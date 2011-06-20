#! /usr/bin/env python
# Encoding: UTF-8

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class NoTargetError(Exception):
    pass

class MoveTargetting(object):
    needs_selected_target = False
    _id_map = dict()

    @classmethod
    def by_identifier(cls, identifier):
        return cls._id_map[identifier]

    @classmethod
    def choice_list(cls, user):
        """Returns an iterable of targets to choose from.
        If empty, or has only one item, no choosing is needed.
        user is the user of the move.
        combattants is an iterable containing all monsters on the field.
        """
        return []

    @classmethod
    def targets(cls, move_effect, chosen_target):
        """Returns a list of targetted battlers.
        moveEffect is the MoveEffect corresponding to this move's usage.
        chosenTarget is one of the targets from chooseList, if applicable.
        """
        if chosen_target:
            return [chosen_target]
        else:
            return []

    @classmethod
    def affected_areas(cls, move_effect, targets):
        """Returns a list of all affected areas

        Affected areas can be Battlers, Sides, or the Field.
        If a larger area is returned, the ones it contains are not (for
        example, a field-targetting move's affectedAreas are only the field).
        When a larger area is completely covered by tagetted smaller areas,
        these are not joined together.

        moveEffect is the MoveEffect corresponding to this move's usage.
        targets is the list of actual targets, as returned by targets()
        """
        return targets

    @classmethod
    def random_choice(cls, field, targets):
        if not targets:
            return []
        else:
            field.choice(targets, 'Select a random target')

def has_identifier(identifier):
    def decorator(cls):
        MoveTargetting._id_map[identifier] = cls
        return cls
    return decorator

@has_identifier('specific-move')
class TargetMove(MoveTargetting):
    """Target a specific move."""
    single_target = True
    # Should be handled in the move effect

@has_identifier('selected-battler')
class TargetSelectedOpponent(MoveTargetting):
    """Target a specific battler."""
    needs_selected_target = True
    single_target = True

    @classmethod
    def choice_list(cls, user):
        return user.allies + user.opponents

@has_identifier('ally')
class TargetAlly(MoveTargetting):
    """Target an ally."""
    needs_selected_target = True
    single_target = True

    @classmethod
    def choice_list(cls, user):
        return user.allies

@has_identifier('users-field')
class TargetUserSide(MoveTargetting):
    single_target = False
    @classmethod
    def affected_areas(cls, move_effect, targets):
        return [move_effect.user.side]

@has_identifier('user-or-ally')
class TargetUserOrAlly(MoveTargetting):
    single_target = True
    @classmethod
    def choice_list(cls, user):
        return user + [user.allies]

@has_identifier('opponents-field')
class TargetOpponentSide(MoveTargetting):
    single_target = False
    @classmethod
    def choice_list(cls, user):
        return user.opponents

    @classmethod
    def affected_areas(cls, move_effect, targets):
        return [targets[0].side]

@has_identifier('user')
class TargetUser(MoveTargetting):
    single_target = True

    @classmethod
    def targets(cls, move_effect, chosen_target):
        return []

@has_identifier('random-opponent')
class TargetRandomOpponent(MoveTargetting):
    single_target = True

    @classmethod
    def targets(cls, move_effect, chosen_target):
        return [cls.random_choice(move_effect.field, user.opponents)]

@has_identifier('all-others')
class TargetAllOthers(MoveTargetting):
    single_target = False

    @classmethod
    def targets(cls, move_effect, chosen_target):
        return move_effect.user.opponents + move_effect.user.allies

@has_identifier('all-opponents')
class TargetAllOpponents(MoveTargetting):
    single_target = False

    @classmethod
    def targets(cls, move_effect, chosen_target):
        return move_effect.user.opponents

@has_identifier('entire-field')
class TargetField(MoveTargetting):
    single_target = False
    @classmethod
    def affected_areas(cls, move_effect, targets):
        return [move_effect.user.field]
