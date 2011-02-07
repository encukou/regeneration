#! /usr/bin/python
# Encoding: UTF-8

from setuptools import setup, find_packages

__copyright__ = "Copyright 2009-2010, Petr Viktorin"
__license__ = "MIT"
__version__ = '0.1'
__author__ = 'Petr "En-Cu-Kou" Viktorin'
__email__ = 'encukou@gmail.com'

setup(
    name='regeneration-battle',
    version=__version__,
    description=u'A pocket monster battle engine',
    author=__author__,
    author_email=__email__,
    install_requires=[
            "pokedex>=0.1",
            "pyyaml>=3.0",
        ],
    setup_requires=[],
    packages = find_packages(),
    namespace_packages = ['regeneration'],

    include_package_data=True,
    package_data={},
)
