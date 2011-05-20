#! /usr/bin/env python
# Encoding: UTF-8

import random
from functools import partial
from fractions import Fraction

from regeneration.battle import messages
from regeneration.battle.effect import Effect, EffectSubject
from regeneration.battle.battler import Battler
from regeneration.battle.command import CommandRequest, MoveCommand
from regeneration.battle.moveeffect import MoveEffect
from regeneration.battle.trainer import Trainer
from regeneration.battle.helper_effects import default_effect_classes

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class MessageSender(object):
    def __init__(self, field, messages):
        self.field = field
        self.messages = messages

    def __getattr__(self, attr):
        return partial(self.send, getattr(self.messages, attr))

    def send(self, cls, **kwargs):
        self.field.send_message(cls(field=self.field, **kwargs))

class Side(EffectSubject):
    def __init__(self, field, number, trainers):
        EffectSubject.__init__(self, field)
        self.number = number
        self.field = field
        try:
            trainers = iter(trainers)
        except TypeError:
            # We only got one trainer, make a lonely team for her
            trainers = [trainers]
        self.spots = [Spot(self, i, t) for i, t in enumerate(trainers)]

    def __str__(self):
        return "<Side %s>" % self.number

    def message_values(self, public=False):
        return dict(id=id(self), name='Side %s' % self.number)

class Spot(object):
    def __init__(self, side, number, trainer):
        self.number = number
        self.side = side
        self.trainer = trainer
        self.battler = None
        self.field = self.side.field

    def message_values(self, trainer):
        return dict(
                trainer=self.trainer.message_values(trainer),
                side=self.side.message_values(trainer),
            )

class Field(EffectSubject):
    in_loop = False
    turn_number = 0
    allow_run = True

    state = 'new'

    def __init__(self, loader, trainers, messages=messages, rand=random):
        """ Make a Battlefield, pitting the given trainers against each other!

        trainers is a list of lists of trainers, grouped by side.
        If there is only one trainer per side, a flat list is OK, as long as
        the trainers themselves aren't iterable.
        Note that a trainer controls more monsters at the same time, the
        single trainer must be repeated: [[blue, blue], [red, green]].
        Otherwise, the lonely trainer could only control one monster.
        """
        EffectSubject.__init__(self, self)
        self.loader = loader
        self.rand = rand
        self.message = MessageSender(self, messages)
        self.sides = [Side(self, i, t) for i, t in enumerate(trainers)]

        self.observers = []

        self.struggle = self.loader.load_struggle()

        self.apply_default_effects()

    # Helpers

    @property
    def spots(self):
        for side in self.sides:
            for spot in side.spots:
                yield spot

    @property
    def battlers(self):
        for spot in self.spots:
            if spot.battler and not spot.battler.fainted:
                yield spot.battler

    @property
    def ended(self):
        return self.state == 'finished'

    @property
    def active_subsubjects(self):
        for side in self.sides:
            yield side
        for battler in self.battlers:
            yield battler

    def assert_state(self, *states):
        if self.state not in states:
            raise AssertionError('Bad battle state %s' % self.state)

    def debug(self, turn_no=None):
        if turn_no is None or turn_no == self.turn_number:
            import pdb; pdb.set_trace()

    # Loaders

    def type_by_name(self, name, names):
        """Helper method to get a type by its name easily.

        Returs a list of types if more names are given.
        """
        return self.loader.load_types(names)

    # Messages

    def add_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    def send_message(self, message):
        for observer in self.observers:
            observer(message)

    def message_values(self, trainer):
        return dict(
                id=id(self),
            )

    # Load/Save

    @classmethod
    def load(cls, dct, loader, trainer_loader=Trainer.load, **kwargs):
        loaded_trainers = {}
        trainers = []
        for trainer_ids in dct['battle_format']:
            side = []
            for trainer_id in trainer_ids:
                try:
                    trainer = loaded_trainers[trainer_id]
                except KeyError:
                    trainer = loaded_trainers[trainer_id] = trainer_loader(
                            dct['trainers'][trainer_id], loader=loader)
                side.append(trainer)
            trainers.append(side)
        if not trainers:
            raise ValueErorr('No trainers')
        if 'seed' in dct:
            kwargs['rand'] = random.Random(dct['seed'])
        return cls(loader, trainers, **kwargs)

    # Main logic

    def run(self):
        self.assert_state('new')

        self.message.BattleStart()

        sendouts = []
        exclude = []
        for side in self.sides:
            for spot in side.spots:
                monster = spot.trainer.get_first_inactive_monster(
                        exclude=exclude)
                sendouts.append((spot, monster))
                self.release_monster(spot, monster)
        self.sort_by_speed(
                sendouts,
                key=lambda x: x[1].stats.speed,
                reverse=True,
            )
        for spot, mon in sendouts:
            self.init_battler(spot.battler)

        self.state = 'waiting'

        self.ask_for_commands()
        self.command_loop()

    def sort_by_speed(self, lst,
            key=lambda x: x.monster.stats.spd,
            reverse=False,
            shuffle=False,
        ):
        if shuffle:
            self.shuffle(lst, "Shuffle before sorting by speed")
        if reverse:
            lst.sort(key=lambda x: -key(x))
        else:
            lst.sort(key=key)

    def ask_for_commands(self):
        self.assert_state('waiting', 'waiting_replacements')

        self.active_requests = {}
        self.commands = {}

        for spot in self.spots:
            battler = spot.battler
            if battler.fainted:
                # Fainted! Has to send out new battler!
                command_request = CommandRequest(battler)
                self.active_requests[battler] = command_request

        if self.active_requests:
            self.state = 'waiting_replacements'
        else:
            for battler in self.battlers:
                # Any command they may like
                command_request = CommandRequest(battler)
                self.active_requests[battler] = command_request

            self.state = 'waiting'

        for battler in self.battlers:
            request = self.active_requests.get(battler)
            if request:
                command = battler.trainer.request_command(request)
                if command is not None:
                    self.commands[battler] = command

        for battler, command in self.commands.items():
            self.command_selected(command, False)

    def command_loop(self):
        while not self.ended and not self.active_requests:
            if self.state == 'waiting_replacements':
                self.process_replacements()
            else:
                self.assert_state('processing')
                self.do_turn()

    def command_selected(self, command, process=True):
        self.assert_state('waiting', 'waiting_replacements')

        try:
            del self.active_requests[command.request.battler]
        except KeyError:
            raise AssertionError("Not waiting for a command for that battler")

        self.commands[command.request.battler] = command

        if not self.active_requests:
            if self.state == 'waiting_replacements':
                self.process_replacements()
            else:
                self.state = 'processing'
                if process:
                    self.doTurn()

    def process_replacements(self):
        """Send out monsters to replace those that have fainted."""
        self.assert_state('waiting_replacements')

        commands = [
                command for command in self.commands.values()
                if command.command == 'switch'
            ]

        for command in commands:
            self.withdraw(command.battler)
        for command in commands:
            self.release_monster(command.spot, command.replacement)
        for command in commands:
            self.init_battler(command.spot.battler)

        self.ask_for_commands()

    def do_turn(self):
        self.turn_number += 1
        self.can_save = False
        self.handle_turn()
        self.can_save = True

    # Mechanics

    def apply_default_effects(self):
        for effect_class in default_effect_classes:
            self.give_effect_self(effect_class())

    def command_allowed(self, command, ignore_pp=False):
        if command.battler.fainted and command.command != 'switch':
            return False
        if command.command == 'move':
            move = command.move
            if move is None:
                # Forced move!
                pass
            else:
                if move.kind == self.struggle:
                    # Struggle: We trust the trainer that there are no usable
                    # moves left
                    return True
                if move.pp <= 0 and not ignore_pp:
                    return False
                if Effect.prevent_move_selection(command):
                    return False
            return True
        elif command.command == 'switch':
            replacement = command.replacement
            if replacement.fainted:
                # Can't send in a fainted monster
                return False
            for battler in self.battlers:
                if command.replacement is battler.monster:
                    # Can't switch to an already active battler
                    return False
                if command in self.commands.values():
                    # Cant switch to a monster being already switched in!
                    # Note that this makes the result of command_allowed()
                    # dependent on commands already issued this turn
                    return False
            battler = command.request.battler
            if not battler or battler.fainted:
                return True
            return not Effect.prevent_switch(command)
        elif command.command == 'run':
            return self.allow_run

        raise NotImplementedError(command)

    def handle_turn(self):
        self.assert_state('processing')

        commands = []
        for battler, command in self.commands.items():
            if command.command == 'move' and command.battler.forced_move:
                move, target = command.battler.forced_move
                command = MoveCommand(command.request, 'move', move, target)
            commands.append(command)

        self.message.TurnStart(turn=self.turn_number)
        Effect.begin_turn(self)

        self.turnCommands = commands = self.sort_commands(commands)

        move_effects = {}

        for command in commands:
            if command.command == 'move':
                command.move_effect = MoveEffect(
                        self,
                        command.move,
                        command.request.battler,
                        command.target)
                command.move_effect.begin_turn()

        for command in commands:
            battler = command.battler

            self.message.SubturnStart(battler=battler, turn=self.turn_number)
            if command.command == 'move':
                command.move_effect.attempt_use()
            elif command.command == 'switch':
                self.switch(command.request.spot, command.replacement)
            else:
                raise NotImplementedError(command)
            self.message.SubturnEnd(battler=battler, turn=self.turn_number)
            if self.check_win():
                return

        self.end_turn_effects()

        self.message.TurnEnd(turn=self.turn_number)

        # That's it for this turn!
        if not self.ended:
            self.state = 'waiting'
            self.ask_for_commands()

    def sort_commands(self, commands):
        self.shuffle(commands, 'Shuffle commands before sorting')
        commands.sort(key=self.command_sort_order)
        return commands

    def command_sort_order(self, command):
        if command.command == 'move':
            trick_factor = Effect.speed_factor(self, 1)
            speed_stat = self.loader.load_stat('speed')
            speed_value = command.request.battler.stats[speed_stat]
            return (
                    1,
                    -command.move.priority,
                    -speed_value * trick_factor,
                )
        elif command.command == 'switch':
            return (
                    0,
                    command.request.spot.side.number,
                    command.request.spot.number,
                )
        else:
            raise NotImplementedError()

    def calculate_damage(self, hit):
        damage_class = hit.damage_class
        user = hit.user
        target = hit.target

        if damage_class.identifier == 'physical':
            attack_stat = self.loader.load_stat('attack')
            defense_stat = self.loader.load_stat('defense')
        else:
            attack_stat = self.loader.load_stat('special-attack')
            defense_stat = self.loader.load_stat('special-defense')

        self.message.effectivity(hit=hit)
        if not hit.effectivity:
            return None

        attack = user.stats[attack_stat]
        defense = target.stats[defense_stat]
        damage = ((user.level * 2 // 5 + 2) *
                hit.power * attack // 50 // defense)

        damage = Effect.modify_move_damage(self, damage, hit)

        if damage < 1:
            damage = 1

        return damage

    def switch(self, spot, replacement):
        self.withdraw(spot)
        self.release_monster(spot, replacement)
        self.init_battler(spot.battler)

    def withdraw(self, spot):
        for effect in self.active_effects:
            effect.withdraw(spot)
        spot.battler.spot = None
        spot.battler = None

    def release_monster(self, spot, monster):
        assert spot.battler is None
        spot.battler = Battler(monster, spot, self.loader)
        self.message.SendOut(battler=spot.battler)

    def init_battler(self, battler):
        for effect in battler.active_effects:
            effect.switchIn()

    def check_win(self):
        # Losing is defined as "having nothing on the field AND nothing
        # to send out". If exactly one side did not lose yet, it wins.
        # If everyone lost, it's a draw.

        survivors = set()
        for side in self.sides:
            for spot in side.spots:
                if (
                        (spot.battler and not spot.battler.fainted) or
                        spot.trainer.get_first_inactive_monster(
                                [spot.battler for spot in self.spots]
                            )
                    ):
                    survivors.add(side)
                    break

        if not survivors:
            # It's a draw!
            self.handle_win(None)
            return True
        elif len(survivors) == 1:
            self.handle_win(survivors.pop())
            return True
        else:
            return False

    def handle_win(self, side):
        self.state = 'finished'
        if side:
            self.message.Victory(side=side)
        else:
            self.message.Draw()

    def end_turn_effects(self):
        pass

    # Random stuff (literally)

    def flip_coin(self, chance, blurb):
        chance = Fraction(chance)
        max = chance.denominator - 1
        return self.randint(0, max, blurb) < chance.numerator

    def randint(self, min, max, blurb):
        return self.rand.randint(min, max)

    def shuffle(self, list, blurb):
        self.rand.shuffle(list)
