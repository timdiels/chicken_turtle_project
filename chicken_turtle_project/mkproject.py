from chicken_turtle_util.exceptions import UserException
from chicken_turtle_project.common import get_project, eval_file, graceful_main
from setuptools import find_packages  # Always prefer setuptools over distutils
from collections import defaultdict
from pathlib import Path
from glob import glob
import plumbum as pb
import pypandoc
import click
import pprint
import os
import re

import logging
logger = logging.getLogger(__name__)
    
def main(): # XXX click to show help message and version; also on mksetup and other tools. Also include the output from -h in the readme automatically, i.e. compile the readme (or maybe reST can? or maybe we should use Sphinx instead?).
    '''
    Create or update existing project to match the latest Chicken Turtle project structure and create/update setup.py and requirements.txt
    
    ct-mkproject must be run from the root of the project. 
    
    The following files are created if missing:
    - project.py
    - $project_name package
    - $project_name/version.py
    - $project_name/test package
    - requirements.in
    - .gitignore
    - setup.cfg
    
    ct-mkproject ensures certain patterns are part of .gitignore, but does not erase any patterns you added.
    
    Warnings are emitted if these files are missing:
    - LICENSE.txt
    - README.*
    
    py.test will be configured to run test in $project_name.test and subpackages
    
    All dependencies should be listed in a requirements.in. If you want to
    install dependencies as editable, prefix them with -e and provide a path to
    the package.
    '''
    graceful_main(_main, logger)
    
def _main():
    project_root = Path.cwd()
    project = _make_project(project_root)
    _make_setup(project, project_root)
    
def _make_project(project_root):
    # Create project if missing
    project_path = project_root / 'project.py'
    if not project_path.exists():
        logger.info('project.py not found, will create from template')
        project_name = click.prompt('Please pick a name for your project')
        assert project_name and project_name.strip()
        with project_path.open('w') as f:
            f.write(project_template.format(project_name))
    
    # Load project info
    project = get_project()
    project_name = project['name']
    pkg_root = project_root / project_name
    
    # Create package dir if missing
    if not pkg_root.exists():
        logger.info('Creating {}'.format(pkg_root))
        pkg_root.mkdir()
    
    # Ensure package root __init__.py exists
    pkg_root_init = pkg_root / '__init__.py'
    if not pkg_root_init.exists():
        logger.info('Creating {}'.format(pkg_root_init))
        pkg_root_init.touch()
    
    # Ensure package root __init__.py imports __version__    
    import_line = 'from {}.version import __version__'.format(project_name)
    with pkg_root_init.open('r') as f:
        contents = f.read()
    if import_line not in map(str.strip, contents.splitlines()):
        logger.info('Inserting __version__ import in {}'.format(pkg_root_init)) 
        with pkg_root_init.open('w') as f:
            f.write(import_line + "\n" + contents)
        
    # Create version.py if missing    
    version_path = pkg_root / 'version.py'
    if not version_path.exists():
        logger.info('Creating {}'.format(version_path))
        with version_path.open('w') as f:
            f.write(version_template)
    
    # Create test package if missing
    test_root = pkg_root / 'test'
    if not test_root.exists():
        logger.info('Creating {}'.format(test_root))
        test_root.mkdir()
    
    test_root_init = test_root / '__init__.py'
    if not test_root_init.exists():
        logger.info('Creating {}'.format(test_root_init))
        test_root_init.touch()
        
    # Create requirements.in if missing
    requirements_in_path = project_root / 'requirements.in'
    if not requirements_in_path.exists():
        logger.info('Creating requirements.in')
        requirements_in_path.touch()
        
    # Create setup.cfg if missing
    setup_cfg_path = project_root / 'setup.cfg'
    if not setup_cfg_path.exists():
        logger.info('Creating setup.cfg')
        with setup_cfg_path.open('w') as f:
            f.write(setup_cfg_template.format(project_name))
        
    # Create .gitignore if missing
    gitignore_path = project_root / '.gitignore'
    if not gitignore_path.exists():
        logger.info('Creating .gitignore')
        gitignore_path.touch()
    
    # Ensure the right patterns are present in .gitignore
    with gitignore_path.open('r') as f:
        content = f.read()
    patterns = set(map(str.strip, content.splitlines()))
    missing_patterns = gitignore_patterns - patterns
    if missing_patterns:
        logger.info('Inserting missing patterns into .gitignore')
        with gitignore_path.open('r') as f:
            f.write('\n'.join(*missing_patterns, content))
    
    # Raise error if missing file
    for file in 'LICENSE.txt README.*'.split():
        if not glob(file):
            raise UserException("Missing file: {}".format(file))
    
    return project
            
def _make_setup(project, project_root):
    '''Expects to run after _make_project'''
    
    name = project['name']
    pkg_root = Path(name)
    
    # Write requirements.txt
    logger.info('Writing requirements.txt')
    pb.local['pip-compile']('requirements.in')
    
    # List dependencies
    logger.info('Preparing to write setup.py')
    with (project_root / 'requirements.in').open('r') as f:
        # TODO test with file with -e and normal and line and inline comments
        lines = list(map(str.strip, f.readlines()))
        for i, line in enumerate(lines):
            if line.startswith('-e'):
                path = re.match('-e\s+([^#]+)', line).group(1).strip()
                name = pb.local['python'](Path(path) / 'setup.py', '--name').strip()
                lines[i] = name
        project['install_requires'] = '\n'.join(lines) 
    
    # Transform some keys
    project['long_description'] = pypandoc.convert(project['readme_file'], 'rst')
    project['classifiers'] = [line.strip() for line in project['classifiers'].splitlines() if line.strip()] 

    # Version
    try:
        version_path = pkg_root / 'version.py'
        project['version'] = eval_file(version_path)['__version__'] #TODO check format
    except IOError:
        assert False
    except KeyError:
        raise UserException('{} must contain `__version__`'.format(version_path))
        
    # Packages and package data
    # TODO test:
    # - pkg[init]/pkg[init]/data/derr/data -> only pick the top data
    # - pkg[init]/notpkg/data -> don't pick data dir as it's not child of a package
    # be sure to test for correct pkg names too
    project['packages'] = find_packages()
    package_data = defaultdict(list) 
    for parent, dirs, files in os.walk(str(pkg_root), topdown=True): #XXX find_packages already found all packages so you could simply use that and check for children named 'data' that aren't in `packages` themselves
        if '__init__.py' not in files:
            # Don't search in non-package directories
            dirs[:] = []
        elif 'data' in dirs:
            # Is part of a package, is named 'data', could be a data dir or a package
            dir_ = Path(parent) / 'data'
            if not (dir_ / '__init__.py').exists():
                # It's a data dir
                dirs.remove('data') 
                for parent2, _, files2 in os.walk(str(dir_)):
                    package_data[parent.replace('/', '.')].extend(str(Path(parent2) / file) for file in files2)
    project['package_data'] = dict(package_data)
    
    # Write setup.py
    del project['readme_file']
    logger.info('Writing setup.py')
    with (project_root / 'setup.py').open('w') as f:
        f.write(setup_template.format(pprint.pformat(project, indent=4, width=120)))
        
setup_template = '''
# Auto generated by ct-mksetup
# Do not edit this file, edit ./project.py instead

from setuptools import setup
setup(
    **{}
)
'''.lstrip()
        
project_template = """
project = dict(
    name='{}',
    description='Short description',
    author='your name',
    author_email='your_email@example.com',
    readme_file='README.md',
    url='https://example.com/project/home', # project homepage
    license='LGPL3',
 
    # What does your project relate to?
    keywords='keyword1 key-word2',
    
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    # Note: you must add ancestors of any applicable classifier too
    classifiers='''
        Development Status :: 2 - Pre-Alpha
        Intended Audience :: Developers
        License :: OSI Approved
        License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)
        Natural Language :: English
        Operating System :: POSIX
        Operating System :: POSIX :: AIX
        Operating System :: POSIX :: BSD
        Operating System :: POSIX :: BSD :: BSD/OS
        Operating System :: POSIX :: BSD :: FreeBSD
        Operating System :: POSIX :: BSD :: NetBSD
        Operating System :: POSIX :: BSD :: OpenBSD
        Operating System :: POSIX :: GNU Hurd
        Operating System :: POSIX :: HP-UX
        Operating System :: POSIX :: IRIX
        Operating System :: POSIX :: Linux
        Operating System :: POSIX :: Other
        Operating System :: POSIX :: SCO
        Operating System :: POSIX :: SunOS/Solaris
        Operating System :: Unix
        Programming Language :: Python
        Programming Language :: Python :: 3
        Programming Language :: Python :: 3 :: Only
        Programming Language :: Python :: 3.2
        Programming Language :: Python :: 3.3
        Programming Language :: Python :: 3.4
        Programming Language :: Python :: 3.5
        Programming Language :: Python :: Implementation
        Programming Language :: Python :: Implementation :: CPython
        Programming Language :: Python :: Implementation :: Stackless
    ''',
 
    # Required dependencies
    setup_requires='pypandoc'.split(), # required to run setup.py. I'm not aware of any setup tool that uses this though
    install_requires=(
        'pypi-dep-1 pypydep2 '
        'moredeps '
    ),
 
    # Optional dependencies
    extras_require={
        'dev': '',
        'test': 'pytest pytest-benchmark pytest-timeout pytest-xdist freezegun',
    },
 
    # Auto generate entry points
    entry_points={
        'console_scripts': [
            'mycli = project_name.main:main', # just an example, any module will do, this template doesn't care where you put it
        ],
    },
)
""".lstrip()

version_template = """
# Versions should comply with PEP440.
# https://www.python.org/dev/peps/pep-0440/
# https://python-packaging-user-guide.readthedocs.org/en/latest/distributing/#semantic-versioning-preferred
__version__ = '1.0.0.dev1'
""".lstrip()

setup_cfg_template = """
[pytest]
addopts = --basetemp=last_test_runs
testpaths={}/test
""".lstrip()

gitignore_patterns = r'''
*.orig
*.swp
.project
.pydevproject
.cproject
test/last_runs
venv
*.pyc
__pycache__
*.egg-info
.cache
'''
gitignore_patterns = {line for line in map(str.strip, gitignore_patterns.splitlines()) if line}
