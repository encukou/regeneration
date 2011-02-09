#! /usr/bin/python
# Encoding: UTF-8

import re
import os

import pkg_resources

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

def yieldSourceFiles():
    pkg_root = pkg_resources.resource_filename('regeneration.battle', '')
    for root, dirs, files in os.walk(pkg_root):
        for file in files:
            name, ext = os.path.splitext(file)
            if ext == '.py':
                yield name, os.path.join(root, file)

def forAllFiles(func):
    def wrapped():
        for name, filename in yieldSourceFiles():
            yield func, name, filename
    wrapped.__name__ = func.__name__
    return wrapped

defOrClassRe = re.compile('(def|class) +([a-z_A-Z0-9]+)(\(?)')
filePropRe = re.compile('__([a-z]+)__ = (.*)')
@forAllFiles
def testStyle(name, filename):
    fileProps = {}
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
        defOrClass = defOrClassRe.match(line.strip())
        if defOrClass:
            type, name, paren = defOrClass.groups()
            name = name.strip('_')
            infoWithName = filename, lineno, name
            assert '_' not in name or 'not camelCase' in line, (
                    '%s:%s: %s: Use CamelCase' % infoWithName
                )
            # Check that classes are new-style (and no space between name/paren)
            assert paren, (
                    '%s:%s: %s: Missing parenthesis after name' % infoWithName
                )
        fileProp = filePropRe.match(line.strip())
        if fileProp:
            fileProps[fileProp.group(1)] = fileProp.group(2)
    if not empty:
        assert fileProps.get('license') == "'MIT'", (
                "%s: Missing/bad MIT license (use 'MIT', with single quotes)" %
                    filename
            )
        assert '2010' not in fileProps.get('copyright', '')

badWordRe = re.compile('pok.{1,2}(mon|dex|ball)|p(arameter|kmn)', re.I)
@forAllFiles
def testTerminology(name, filename):
    if name in 'example movetargetting'.split():
        return
    for lineno, line in enumerate(open(filename), 1):
        if line.strip() == 'CHECK@END': return
        assert not badWordRe.search(line), '%s:%s: Watch your terminology' % (
                filename, lineno
            )
