from chicken_turtle_util.exceptions import UserException
from chicken_turtle_project.common import get_project, graceful_main, get_repo, init_logging, parse_requirements_file, get_dependency_name, get_pkg_root
from setuptools import find_packages  # Always prefer setuptools over distutils
from collections import defaultdict
from pathlib import Path
from glob import glob
from configparser import ConfigParser
from chicken_turtle_project import __version__
from chicken_turtle_util import cli
import plumbum as pb
import pypandoc
import click
import pprint
import os
import re
from glob import glob
from more_itertools import first

import logging
logger = logging.getLogger(__name__)

git_ = pb.local['git']

_dummy_version = '0.0.0'

def main(args=None):
    _main(args, help_option_names=['-h', '--help'])

#TODO mv to CTU.ordering
'''
This module represents totally ordered sets (tosets) as `setlist`s. E.g. a toset
`a < b < c` is represented as `setlist([a, b, c])`.
'''

from collections_extended import setlist
from chicken_turtle_util.itertools import window 
import networkx as nx
    
def toset_from_tosets(*tosets):
    '''
    Create totally ordered set (toset) from tosets.
    
    These tosets, when merged, form a partially ordered set. The linear
    extension of this poset, a toset, is returned.
    
    Parameters
    ----------
    tosets : iterable of setlist
        tosets to merge
        
    Raises
    ------
    ValueError
        if the tosets (derived from the lists) contradict each other. E.g. `[a, b]` and `[b, c, a]` contradict each other.
        
    Returns
    -------
    setlist
        Totally ordered set
    '''
    # Construct directed graph with: a <-- b iff a < b and adjacent in a list
    graph = nx.DiGraph()
    for toset in tosets:
        graph.add_nodes_from(toset)
        graph.add_edges_from(window(reversed(toset)))
    
    # No cycles allowed
    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError('Given tosets contradict each other')  # each cycle is a contradiction, e.g. a > b > c > a
    
    # Topological sort
    return setlist(nx.topological_sort(graph, reverse=True))    

@click.command()
@cli.option(
    '--pre-commit/--no-pre-commit',
    default=False, is_flag=True,
    help='Internal option, do not use.'
)
@cli.option(
    '--project-version',
    default=_dummy_version,
    envvar='CT_PROJECT_VERSION',
    help='Internal option, do not use.'
)
@click.version_option(version=__version__)
def _main(pre_commit, project_version):
    '''
    Create, update and validate project, enforcing Chicken Turtle Project
    development methodology.
    
    ct-mkproject must be run from the root of the project (where setup.py should be).
    
    The project must be in a git repository. 
    
    The following files are created if missing:
    - project.py
    - $project_name package
    - $project_name/test package
    - $project_name/test/conftest.py
    - requirements.in
    - test_requirements.in
    
    The following files may be created or updated by merging in changes:
    - $project_name/__init__.py
    - .gitignore
    - setup.cfg
    
    The following files will be created or overwritten if they exist:
    - requirements.txt
    - setup.py
    
    Warnings are emitted if these files are missing:
    - LICENSE.txt
    - readme file pointed to by readme_file
    
    ct-mkproject ensures certain patterns are part of .gitignore, but does not erase any patterns you added.
    
    py.test will be configured to run test in $project_name.test and subpackages.
    
    All dependencies should be listed in a requirements.in. If you want to
    install dependencies as editable, prefix them with -e and provide a path to
    the package.
    
    A git pre-commit hook will be installed (if none exists). It updates project
    files and ensures the tests succeed before committing.
    
    Any file modified by ct-mkproject, is automatically staged (git). Some files
    will be dirty after the commit (e.g. setup.py) due to implementation
    limitations, as these files are managed by ct-mkproject, there should be no
    need to `git reset --hard` them.
    '''
    init_logging()
    with graceful_main(logger):
        project_root = Path.cwd()
        repo = get_repo(project_root)
        
        _ensure_project_exists(project_root)
        
        project = get_project(project_root)
        pkg_root = get_pkg_root(project_root, project['name'])
        project['version'] = project_version
        
        _ensure_root_package_exists(pkg_root)
        _update_root_package(pkg_root, project['version'])
        
        test_root = pkg_root / 'test'
        _ensure_test_package_exists(test_root)
        _ensure_conftest_exists(test_root)
        
        _ensure_requirements_in_exists(project_root)
        _ensure_test_requirements_in_exists(project_root)
        
        setup_cfg_path = project_root / 'setup.cfg'
        _ensure_setup_cfg_exists(setup_cfg_path)
        _update_setup_cfg(setup_cfg_path, project, project_root)
        
        gitignore_path = project_root / '.gitignore'
        _ensure_gitignore_exists(gitignore_path)
        _update_gitignore(gitignore_path)
        
        _ensure_precommit_hook_exists(repo)
        
        _raise_if_missing_file(project)
        
        # TODO check that source files have correct copyright header
        # TODO ensure the readme_file is mentioned in MANIFEST.in
        
        _update_requirements_txt(project_root)
        _update_setup_py(project, project_root, pkg_root)
            
def _ensure_project_exists(project_root):
    project_path = project_root / 'project.py'
    if not project_path.exists():
        logger.info('project.py not found, will create from template')
        project_name = click.prompt('Please pick a name for your project')
        assert project_name and project_name.strip()
        with project_path.open('w') as f:
            logger.info('Creating project.py')
            f.write(project_template.format(name=project_name, pkg_name=get_pkg_root(project_root, project_name).name))
            git_('add', str(project_path))

def _ensure_root_package_exists(pkg_root):
    # Create package dir if missing
    if not pkg_root.exists():
        logger.info('Creating {}'.format(pkg_root))
        pkg_root.mkdir()
    
    # Ensure package root __init__.py exists
    pkg_root_init = pkg_root / '__init__.py'
    if not pkg_root_init.exists():
        logger.info('Creating {}'.format(pkg_root_init))
        pkg_root_init.touch()
        
def _update_root_package(pkg_root, version):
    '''
    Set __version__ in package root __init__.py
    '''
    pkg_root_init = pkg_root / '__init__.py'
    version_line = version_template.format(version)
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
    git_('add', pkg_root_init)
    
def _ensure_test_package_exists(test_root):
    if not test_root.exists():
        logger.info('Creating {}'.format(test_root))
        test_root.mkdir()
    
    test_root_init = test_root / '__init__.py'
    if not test_root_init.exists():
        logger.info('Creating {}'.format(test_root_init))
        test_root_init.touch()
        git_('add', test_root_init)
        
def _ensure_conftest_exists(test_root):
    conftest_py_path = test_root / 'conftest.py'
    if not conftest_py_path.exists():
        logger.info('Creating test/conftest.py')
        with conftest_py_path.open('w') as f:
            f.write(conftest_py_template)
        git_('add', conftest_py_path)
        
def _ensure_requirements_in_exists(project_root):
    requirements_in_path = project_root / 'requirements.in'
    if not requirements_in_path.exists():
        logger.info('Creating requirements.in')
        requirements_in_path.touch()

def _ensure_test_requirements_in_exists(project_root):
    requirements_in_path = project_root / 'test_requirements.in'
    if not requirements_in_path.exists():
        logger.info('Creating test_requirements.in')
        with requirements_in_path.open('w') as f:
            f.write(test_requirements_in_template)
        
def _ensure_setup_cfg_exists(setup_cfg_path):
    if not setup_cfg_path.exists():
        logger.info('Creating setup.cfg')
        setup_cfg_path.touch()
        git_('add', setup_cfg_path)
        
def _update_setup_cfg(setup_cfg_path, project, project_root):
    # Ensure sections exist
    config = ConfigParser()
    config.read(str(setup_cfg_path))
    for section_name in ('pytest', 'metadata'):
        if section_name not in config.sections():
            config.add_section(section_name)
            
    # Update options
    changed = False
    if 'addopts' not in config['pytest']:
        config['pytest']['addopts'] = '--basetemp=last_test_runs --maxfail=1'
        changed = True
        
    if 'env' not in config['pytest']:
        config['pytest']['env'] = 'PYTHONHASHSEED=0'
        changed = True
    
    test_paths = '{}/test'.format(get_pkg_root(project_root, project['name']).name)
    if 'testpaths' not in config['pytest'] or config['pytest']['testpaths'] != test_paths:
        config['pytest']['testpaths'] = test_paths
        changed = True
        
    if 'description-file' not in config['metadata'] or config['metadata']['description-file'] != project['readme_file']:
        config['metadata']['description-file'] = project['readme_file']
        changed = True
    
    # Write updated
    if changed:
        logger.info('Writing setup.cfg')
        with setup_cfg_path.open('w') as f:
            config.write(f)
        git_('add', setup_cfg_path)
        
def _ensure_gitignore_exists(gitignore_path):
    if not gitignore_path.exists():
        logger.info('Creating .gitignore')
        gitignore_path.touch()
        git_('add', gitignore_path)
        
def _update_gitignore(gitignore_path):
    '''
    Ensure the right patterns are present in .gitignore
    '''
    with gitignore_path.open('r') as f:
        content = f.read()
    patterns = set(map(str.strip, content.splitlines()))
    missing_patterns = gitignore_patterns - patterns
    if missing_patterns:
        logger.info('Inserting missing patterns into .gitignore')
        with gitignore_path.open('w') as f:
            f.write('\n'.join(list(missing_patterns) + [content]))
        git_('add', gitignore_path)
        
def _raise_if_missing_file(project):
    for file in ('LICENSE.txt', project['readme_file']):
        if not glob(file):
            raise UserException("Missing file: {}".format(file))
    
def _ensure_precommit_hook_exists(repo):    
    pre_commit_hook_path = Path(repo.git_dir) / 'hooks/pre-commit'
    if not pre_commit_hook_path.exists():
        logger.info('Creating {}'.format(pre_commit_hook_path))
        with pre_commit_hook_path.open('w') as f:
            f.write(pre_commit_hook_template)
        pre_commit_hook_path.chmod(0o775)
        
def _get_dependency_file_paths(project_root):
    paths = [Path(x) for x in glob(str(project_root / '*requirements.in'))]
    assert paths
    return paths

def _update_requirements_txt(project_root):
    logger.info('Writing requirements.txt')
    
    # Compile
    input_file_paths = _get_dependency_file_paths(project_root)
    pb.local['pip-compile'](*(list(map(str, input_file_paths)) + ['-o', 'requirements.txt']))
    
    # Reorder to match ordering in requirements.in
    requirements_txt_path = project_root / 'requirements.txt'
    requirements_txt_lines = {get_dependency_name(line[1]) : line[-1] for line in parse_requirements_file(requirements_txt_path) if line[1]}
    all_dependencies = []
    for input_path in input_file_paths:
        dependency_names = [get_dependency_name(line[1]) for line in parse_requirements_file(input_path) if line[1]]
        all_dependencies.append(setlist(dependency_names))

    all_dependencies = toset_from_tosets(*all_dependencies)
    with requirements_txt_path.open('w') as f:
        for name in all_dependencies:  # write ordered
            f.write(requirements_txt_lines[name] + '\n')
        for name, line in requirements_txt_lines.items():  # write left-overs
            if name not in all_dependencies:
                f.write(line + '\n')

    # Stage it
    git_('add', 'requirements.txt')

def _update_setup_py(project, project_root, pkg_root):
    logger.debug('Preparing to write setup.py')
    project.update(_get_dependencies(project_root))
    project['long_description'] = pypandoc.convert(project['readme_file'], 'rst')
    project['classifiers'] = [line.strip() for line in project['classifiers'].splitlines() if line.strip()] 
    project['packages'] = find_packages()
    project['package_data'] = _get_package_data(project_root, pkg_root)
    
    # Add download_url if current commit is version tagged
    if project['version'] != _dummy_version:
        project['download_url'] = project['download_url'].format(version=project['version'])
    else:
        del project['download_url']
    
    # Write setup.py
    del project['readme_file']
    if 'index_test' in project:
        del project['index_test']
    del project['index_production']
    logger.info('Writing setup.py')
    setup_py_path = project_root / 'setup.py'
    with setup_py_path.open('w') as f:
        f.write(setup_template.format(pprint.pformat(project, indent=4, width=120)))
    git_('add', setup_py_path)
  
def _get_dependencies(project_root):
    '''
    Returns
    -------
    {'install_requires': ..., 'extras_require': ...}
    '''
    paths = _get_dependency_file_paths(project_root)
    extra_requires = {}
    for path in paths: 
        dependencies = []
        for editable, dependency, version_spec, _ in parse_requirements_file(path):
            if not dependency:
                continue
            if editable:
                # transform editable dependency into its package name
                dependency = pb.local['python'](Path(dependency) / 'setup.py', '--name').strip()
            dependencies.append(dependency + (version_spec or ''))
        if path.name == 'requirements.in':
            install_requires = dependencies
        else:
            name = re.fullmatch('(.*)_requirements.in', path.name).group(1)
            extra_requires[name] = dependencies
    return dict(install_requires=install_requires, extras_require=extra_requires)
    
def _get_package_data(project_root, pkg_root):
    pkg_root = pkg_root.relative_to(project_root)
    package_data = defaultdict(list) 
    for parent, dirs, files in os.walk(str(pkg_root), topdown=True): #XXX find_packages already found all packages so you could simply use that and check for children named 'data' that aren't in `packages` themselves
        # Note: `parent` is path str relative to what we're walking
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
    return dict(package_data)
        
        
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
    name='{name}',
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
    index_test = 'pypitest',  # Index to use for testing a release, before releasing to `index_production`. `index_test` can be set to None if you have no test index
    index_production = 'pypi',
    
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
    entry_points={{
        'console_scripts': [
            'mycli = {pkg_name}.main:main', # just an example, any module will do, this template doesn't care where you put it
        ],
    }},
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
venv
*.pyc
__pycache__
*.egg-info
.cache
last_test_runs
dist
'''
gitignore_patterns = {line for line in map(str.strip, gitignore_patterns.splitlines()) if line}

pre_commit_hook_template = '''
#!/bin/sh
# Auto generated by ct-mkproject, you may edit this file. When deleted, this file will be recreated.
set -e

cleanup() {
    set +e
    rm -rf "$temp_dir"
}

# Export last commit + staged changes
trap cleanup EXIT
temp_dir=`mktemp -d`

if [ -n "$CT_RELEASE" ]
then
    # Make clean copy of working dir without staged changes
    git archive HEAD | tar -x -C "$temp_dir"
else
    # Make clean copy of working dir with staged changes
    git checkout-index -a -f --prefix="$temp_dir/"
fi

(
    export GIT_DIR=`realpath $GIT_DIR`
    export GIT_INDEX_FILE=`realpath $GIT_INDEX_FILE`
    unset GIT_WORKING_TREE
    pushd "$temp_dir" &> /dev/null
    ct-mkproject --pre-commit  # Update project
    
    # Run tests
    unset `env | cut -d'=' -f1 | grep -e '^GIT_'`  # Forget about git environment while testing
    unset `env | cut -d'=' -f1 | grep -e '^CT_'`  # Forget about Chicken Turtle environment while testing
    ct-mkvenv
    venv/bin/py.test
    
    popd &> /dev/null
)
'''.lstrip()

conftest_py_template = '''
# http://stackoverflow.com/a/30091579/1031434
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL) # Ignore SIGPIPE
'''.lstrip()

test_requirements_in_template = '''
pytest
pytest-xdist
pytest-env
'''.lstrip()
