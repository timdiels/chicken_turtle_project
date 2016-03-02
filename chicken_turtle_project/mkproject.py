from chicken_turtle_util.exceptions import UserException
from chicken_turtle_project.common import get_project, eval_file, graceful_main, get_repo, get_current_version, get_newest_version, version_from_tag
from setuptools import find_packages  # Always prefer setuptools over distutils
from collections import defaultdict
from pathlib import Path
from glob import glob
from configparser import ConfigParser
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
    Create, update and validate project, enforcing Chicken Turtle Project
    development methodology.
    
    ct-mkproject must be run from the root of the project (where setup.py should be).
    
    The project must be in a git repository. 
    
    The following files are created if missing:
    - project.py
    - $project_name package
    - $project_name/test package
    - requirements.in
    - deploy_local
    
    The following files may be created or updated by merging in changes:
    - $project_name/__init__.py
    - .gitignore
    - setup.cfg
    
    The following files will be created or overwritten if they exist:
    - requirements.txt
    - setup.py
    
    A git pre-commit hook will be installed (if none exists) to call
    $project_root/deploy_local before each commit. deploy_local can be any
    executable, it is auto generated for you if missing but you is left alone
    otherwise so you can provide your own. Its purpose is to call `ct-
    mkproject`, install editably the current project and ensure tests succeed.
    
    ct-mkproject ensures certain patterns are part of .gitignore, but does not erase any patterns you added.
    
    Warnings are emitted if these files are missing:
    - LICENSE.txt
    - README.*
    
    py.test will be configured to run test in $project_name.test and subpackages
    
    All dependencies should be listed in a requirements.in. If you want to
    install dependencies as editable, prefix them with -e and provide a path to
    the package.
    
    ct-mkproject will update the current version in
    $project_name/__init__.py:__version__. This is either the version specified
    by you using `git tag` or the max version in `git tags` with its dev version
    bumped by 1 (E.g. '1.0.0.dev1' becomes '1.0.0.dev2' and
    '1.0.0' becomes '1.0.1.dev1').
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
    
    # Determine current version
    repo = get_repo(project_root)
    version = get_current_version(repo)
    if not version:
        version = get_newest_version(project_root)
        version.bump('dev')
    project['version'] = str(version) #TODO no bump if tag is of last commit
    
    # Set __version__ in package root __init__.py    
    version_line = version_template.format(project['version'])
    with pkg_root_init.open('r') as f:
        lines = f.read().splitlines()
    for i, line in enumerate(lines):
        if line.startswith('__version__ ='):
            lines[i] = version_line
            break
    else:
        lines.append(version_line)
    logger.info('Setting __version__ in {}'.format(pkg_root_init))
    with pkg_root_init.open('w') as f:
        f.write('\n'.join(lines))
    
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
    _update_setup_cfg(project_root, project)
        
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
        with gitignore_path.open('w') as f:
            f.write('\n'.join(list(missing_patterns) + [content]))
    
    # Raise error if missing file
    for file in 'LICENSE.txt README.*'.split():
        if not glob(file):
            raise UserException("Missing file: {}".format(file))
        
    # If version tag, warn if it is less than that of an ancestor commit 
    version = get_current_version()
    if version:
        ancestors = list(repo.commit().iter_parents())
        versions = []
        for tag in repo.tags: #TODO test whether this picks up the tag as I'm not sure whether it's checking the tag uncommitted
            if tag.commit in ancestors:
                try:
                    versions.append(version_from_tag(tag))
                except AttributeError:
                    pass
        newest_ancestor_version = max(versions)
        if version < newest_ancestor_version:
            logger.warning('Current version ({}) is older than ancestor commit version ({})'.format(version, newest_ancestor_version))
            if not click.confirm('Do you want to continue anyway?'):
                raise UserException('Cancelled')
            
    # Install pre-commit hook if none exists
    pre_commit_hook_path = project_root / '.git/hooks/pre-commit'
    if not pre_commit_hook_path.exists():
        with pre_commit_hook_path.open('w') as f:
            f.write(pre_commit_hook_template)
        pre_commit_hook_path.chmod(0o775)
    
    return project

def _update_setup_cfg(project_root, project):
    # Ensure file exists
    setup_cfg_path = project_root / 'setup.cfg'
    if not setup_cfg_path.exists():
        logger.info('Creating setup.cfg')
        setup_cfg_path.touch()
    
    # Ensure sections exist
    config = ConfigParser()
    config.read(str(setup_cfg_path))
    for section_name in ('pytest', 'metadata'):
        if section_name not in config.sections():
            config.add_section(section_name)
            
    # Update options
    if not config.get('pytest', 'addopts'):
        config.set('pytest', 'addopts', '--basetemp=last_test_runs')
    config.set('pytest', 'testpaths', '{}/test'.format(project['name']))
    config.set('metadata', 'description-file', project['readme_file'])
    
    # Write updated
    logger.info('Writing setup.cfg')
    with setup_cfg_path.open('w') as f:
        config.write(f)
            
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
    
    # Add download_url if current commit is version tagged
    repo = get_repo(project_root)
    version = get_current_version(repo)
    if version:
        project['download_url'] = project['download_url'].format(version=str(version))
    else:
        del project['download_url']
    
    # Write setup.py
    del project['readme_file']
    del project['index_test']
    del project['index_production']
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
    download_url='https://example.com/repo/{{version}}', # Template for url to download source archive from. You can refer to the current version with {{version}}. You can get one from github or gitlab for example.
    license='LGPL3',
 
    # What does your project relate to?
    keywords='keyword1 key-word2',
    
    # Package indices to release to using `ct-release`
    # These names refer to those defined in ~/.pypirc.
    # For pypi, see http://peterdowns.com/posts/first-time-with-pypi.html
    # For devpi, see http://doc.devpi.net/latest/userman/devpi_misc.html#using-plain-setup-py-for-uploading
    index_test = 'pypitest'  # Index to use for testing a release, before releasing to `index_production`. `index_test` can be set to None if you have no test index
    index_production = 'pypi'
    
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
 
    # Auto generate entry points
    entry_points={
        'console_scripts': [
            'mycli = project_name.main:main', # just an example, any module will do, this template doesn't care where you put it
        ],
    },
)
""".lstrip()

version_template = """
__version__ = '{}'  # Auto generated by ct-mksetup, do not edit this line, instead use `git tag v{{version}}`, e.g. `git tag v1.0.0-dev1`.
""".strip()

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

pre_commit_hook_template = '''
#!/bin/sh
# Auto generated by ct-mkproject, you may edit this file. When deleted, this file will be recreated.
set -e
./deploy_local
'''.lstrip()
