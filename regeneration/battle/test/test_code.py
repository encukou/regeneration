#! /usr/bin/python
# Encoding: UTF-8

import re
import os

import pkg_resources

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

def yield_source_files():
    pkg_root = pkg_resources.resource_filename('regeneration.battle', '')
    for root, dirs, files in os.walk(pkg_root):
        for file in files:
            name, ext = os.path.splitext(file)
            if ext == '.py':
                yield name, os.path.join(root, file)

def for_all_files(func):
    def wrapped():
        for name, filename in yield_source_files():
            yield func, name, filename
    wrapped.__name__ = func.__name__
    return wrapped

def_or_class_re = re.compile('(def|class) +([a-z_A-Z0-9]+)(\(?)')
file_prop_re = re.compile('__([a-z]+)__ = (.*)')

@for_all_files
def test_style(name, filename):
    file_props = {}
    empty = True
    for lineno, line in enumerate(open(filename), 1):
        line = line.rstrip('\n')
        if line == 'CHECK@END': return
        if line:
            empty = False
        info = filename, lineno
        assert not line.endswith('\r'), (
                '%s:%s: Use Unix line endings' % info
            )
        assert not line.endswith('\\'), (
                "%s:%s: Don't use line continuations" % info
            )
        assert '\t' not in line, (
                '%s:%s: Use spaces, not tabs' % info
            )
        assert (len(line) - len(line.lstrip())) % 4 == 0, (
                '%s:%s: Use 4 spaces to indent' % info
            )
        def_or_class = def_or_class_re.match(line.strip())
        if def_or_class:
            type, name, paren = def_or_class.groups()
            name = name.strip('_')
            info_with_name = filename, lineno, name
            if type == 'class':
                assert '_' not in name or 'not camelCase' in line, (
                        '%s:%s: %s: Use CamelCase' % info_with_name
                    )
            elif type == 'def' and name not in 'setUp setupClass'.split():
                assert not re.search('[A-Z]', name), (
                        '%s:%s: %s: Use pep8_function_names' % info_with_name
                    )
            # Check that classes are new-style (and no space between name/paren)
            assert paren, (
                    '%s:%s: %s: Missing parenthesis after name' % info_with_name
                )
        file_prop = file_prop_re.match(line.strip())
        if file_prop:
            file_props[file_prop.group(1)] = file_prop.group(2)
    if not empty:
        assert file_props.get('license') == "'MIT'", (
                "%s: Missing/bad MIT license (use 'MIT', with single quotes)" %
                    filename
            )
        assert '2010' not in file_props.get('copyright', '')

bad_word_re = re.compile('pok.{1,2}(mon|dex|ball)|p(arameter|kmn)', re.I)
@for_all_files
def test_terminology(name, filename):
    if name in 'example movetargetting'.split():
        return
    for lineno, line in enumerate(open(filename), 1):
        if line.strip() == 'CHECK@END': return
        assert not bad_word_re.search(line), '%s:%s: Watch your terminology' % (
                filename, lineno
            )
