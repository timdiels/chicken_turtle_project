# Auto generated by ct-mksetup
# Do not edit this file, edit ./project.py instead

from setuptools import setup
setup(
    **{   'author': 'Tim Diels',
    'author_email': 'timdiels.m@gmail.com',
    'classifiers': [   'Natural Language :: English',
                       'Intended Audience :: Developers',
                       'Development Status :: 2 - Pre-Alpha',
                       'Topic :: Software Development',
                       'Operating System :: POSIX',
                       'Operating System :: POSIX :: AIX',
                       'Operating System :: POSIX :: BSD',
                       'Operating System :: POSIX :: BSD :: BSD/OS',
                       'Operating System :: POSIX :: BSD :: FreeBSD',
                       'Operating System :: POSIX :: BSD :: NetBSD',
                       'Operating System :: POSIX :: BSD :: OpenBSD',
                       'Operating System :: POSIX :: GNU Hurd',
                       'Operating System :: POSIX :: HP-UX',
                       'Operating System :: POSIX :: IRIX',
                       'Operating System :: POSIX :: Linux',
                       'Operating System :: POSIX :: Other',
                       'Operating System :: POSIX :: SCO',
                       'Operating System :: POSIX :: SunOS/Solaris',
                       'Operating System :: Unix',
                       'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
                       'Programming Language :: Python',
                       'Programming Language :: Python :: 3',
                       'Programming Language :: Python :: 3 :: Only',
                       'Programming Language :: Python :: 3.2',
                       'Programming Language :: Python :: 3.3',
                       'Programming Language :: Python :: 3.4',
                       'Programming Language :: Python :: 3.5',
                       'Programming Language :: Python :: Implementation',
                       'Programming Language :: Python :: Implementation :: CPython',
                       'Programming Language :: Python :: Implementation :: Stackless'],
    'description': 'Python 3 project development tools',
    'entry_points': {   'console_scripts': [   'ct-mkproject = chicken_turtle_project.mkproject:main',
                                               'ct-mkvenv = chicken_turtle_project.mkvenv:main',
                                               'ct-release = chicken_turtle_project.release:main',
                                               'ct-interpreter = chicken_turtle_project.interpreter:main']},
    'install_requires': [   'chicken_turtle_util',
                            'click',
                            'plumbum',
                            'pypandoc',
                            'GitPython',
                            'pip-tools',
                            'checksumdir',
                            'pytest',
                            'pytest-xdist',
                            'pytest-env',
                            'pytest-mock'],
    'keywords': 'development release setuptools tools',
    'license': 'LGPL3',
    'long_description': 'Python 3 project development tools. Looks like a turtle, tastes like\n'
                        'chicken.\n'
                        '\n'
                        'Chicken Turtle provides tools (CLI) for developing Python 3 projects.\n'
                        '\n'
                        'Chicken Turtle is pre-alpha. None of the interface is stable, i.e. it\n'
                        'may change in the future.\n'
                        '\n'
                        'Methodology\n'
                        '-----------\n'
                        '\n'
                        'Tests must be placed in $project\\_name.test or subpackages. Tests are\n'
                        'run with py.test from the project root.\n'
                        '\n'
                        'Package data can be provided by placing a directory named ``data`` in\n'
                        'the package with the data files, but no ``__init__.py`` as that would\n'
                        'turn the data directory into a package.\n'
                        '\n'
                        'Simply include test dependencies in install\\_requires.\n'
                        '\n'
                        '``ct-mksetup`` should be run before any commit and deployment. For the\n'
                        'latter, call ``ct-mksetup`` in your deploy scripts.\n'
                        '\n'
                        'Chicken Turtle Project does not enforce a particular methodology for\n'
                        'deployments, but we recommend shell scripts for simple deployments as\n'
                        "they don't have dependencies (assuming you only deploy to unix-like\n"
                        'machines). If you need to do more complex work such as migrating data to\n'
                        'a new database structure, include a Python script and call it from the\n'
                        'shell script after having made the venv.\n'
                        '\n'
                        'When making dependency in requirements.in editable (e.g. -e\n'
                        'path/to/setup\\_dir), leave the original dependency as a comment so you\n'
                        'remember the previous version constraint when you change it back at\n'
                        'release (though you likely need to require the version with the changes\n'
                        'you made)\n'
                        '\n'
                        'Versions should adhere to\n'
                        '`PEP-0440 <https://www.python.org/dev/peps/pep-0440/>`__ and use\n'
                        '`semantic\n'
                        'versioning '
                        '<https://python-packaging-user-guide.readthedocs.org/en/latest/distributing/#semantic-versioning-preferred>`__.\n'
                        'Versions are only set on release, via an argument to ``ct-release``.\n'
                        '``ct-release`` then adjusts ``setup.py`` with the new version, commits\n'
                        "and tags the commit with its version (prefixed with 'v'). At all other\n"
                        'times, the version in ``setup.py`` is set to ``0.0.0``, use commit ids\n'
                        'instead of versions in this case.\n'
                        '\n'
                        'Old notes (TODO rm)\n'
                        '-------------------\n'
                        '\n'
                        '-  venv\\_create.sh: create a virtual environment corresponding to\n'
                        '   setup.py. If requirements.txt exists, that list of packages will be\n'
                        '   installed. If extra\\_requirements.txt exists (corresponding to the\n'
                        '   extra dependencies in setup.py), these will also be installed. Then\n'
                        "   setup.py's deps are installed, without upgrading any other packages.\n"
                        '-  interpreter.sh: start an interpreter inside the virtual environment,\n'
                        '   ensuring the project source is in the PYTHONPATH and start an\n'
                        '   interactive session in which interpreter.py is first executed.\n'
                        '-  test data should be placed in test/data\n'
                        '-  output of last test runs is kept in test/last\\_runs\n'
                        '-  run\\_tests.py to run the tests, but you need to run it from withing\n'
                        '   the venv (i.e. ``. venv/bin/activate`` before running this)\n'
                        '\n'
                        'See also\n'
                        '--------\n'
                        '\n'
                        'Python packaging recommendations:\n'
                        '\n'
                        '-  https://packaging.python.org/en/latest/distributing.html\n'
                        '-  https://github.com/pypa/sampleproject\n',
    'name': 'chicken_turtle_project',
    'package_data': {},
    'packages': ['chicken_turtle_project', 'chicken_turtle_project.test'],
    'url': 'https://github.com/timdiels/chicken_turtle_project',
    'version': '0.0.0'}
)
