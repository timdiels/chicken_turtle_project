from chicken_turtle_util.exceptions import UserException
from chicken_turtle_project.common import (
    get_project, graceful_main, get_repo, init_logging, 
    parse_requirements_file, get_dependency_name, get_pkg_root, 
    is_sip_dependency, get_dependency_file_paths
)
from chicken_turtle_project import specification as spec
from setuptools import find_packages  # Always prefer setuptools over distutils
from collections import defaultdict
from pathlib import Path
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
from tempfile import mkstemp

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
def _main(pre_commit, project_version): #TODO docstring out of sync?
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
    - doc_src
    
    The following files may be created or updated by merging in changes:
    - $project_name/__init__.py
    - .gitignore
    - setup.cfg
    - dev_requirements.in
    - test_requirements.in
    - MANIFEST.in
    
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
        
        format_kwargs = {
            'name': project['name'],
            'readme_file': project['readme_file'],
            'pkg_name': pkg_root.name,
            'version': project_version,
        }
        
        _ensure_root_package_exists(pkg_root)
        _update_root_package(pkg_root, format_kwargs)
        
        test_root = pkg_root / 'test'
        _ensure_test_package_exists(test_root)
        
        conftest_py_path = test_root / 'conftest.py'
        _ensure_exists(conftest_py_path)
        _ensure_contains_snippets(conftest_py_path, {spec.conftest_py}, format_kwargs)
        
        manifest_in = project_root / 'MANIFEST.in'
        _ensure_exists(manifest_in)
        _ensure_contains_snippets(manifest_in, spec.manifest_in, format_kwargs)
        
        requirements_in_path = project_root / 'requirements.in'
        _ensure_exists(requirements_in_path)
        _ensure_contains_snippets(requirements_in_path, {spec.requirements_in_header}, format_kwargs)

        test_requirements_in_path = project_root / 'test_requirements.in'
        _ensure_exists(test_requirements_in_path)
        _ensure_contains_snippets(test_requirements_in_path, spec.test_requirements_in, format_kwargs)
        
        setup_cfg_path = project_root / 'setup.cfg'
        _ensure_exists(setup_cfg_path)
        _update_ini_file(setup_cfg_path, spec.setup_cfg_defaults, spec.setup_cfg_overwrite, format_kwargs)
        
        coveragerc_path = project_root / '.coveragerc'
        _ensure_exists(coveragerc_path)
        _update_ini_file(coveragerc_path, spec.coveragerc_defaults, spec.coveragerc_overwrite, format_kwargs)
        
        gitignore_path = project_root / '.gitignore'
        _ensure_exists(gitignore_path)
        _ensure_contains_snippets(gitignore_path, spec.gitignore_patterns, format_kwargs)
        
        pre_commit_hook = Path(repo.git_dir) / 'hooks/pre-commit'
        _ensure_exists(pre_commit_hook, git_add=False)
        _ensure_contains_snippets(pre_commit_hook, {spec.pre_commit_hook}, format_kwargs, git_add=False)
        pre_commit_hook.chmod(0o775)
        
        _raise_if_missing_file(project)
        
        # TODO check that source files have correct copyright header
        # TODO ensure the readme_file is mentioned in MANIFEST.in
        
        _update_requirements_txt(project_root)
        
        _update_setup_py(project, project_root, pkg_root, format_kwargs)
            
def _ensure_project_exists(project_root):
    project_path = project_root / 'project.py'
    if not project_path.exists():
        logger.info('project.py not found, will create from template')
        project_name = click.prompt('Please pick a name for your project')
        assert project_name and project_name.strip()
        with project_path.open('w') as f:
            logger.info('Creating project.py')
            f.write(spec.project_py.format(name=project_name, pkg_name=get_pkg_root(project_root, project_name).name))
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
        
def _update_root_package(pkg_root, format_kwargs):
    '''
    Set __version__ in package root __init__.py
    '''
    pkg_root_init = pkg_root / '__init__.py'
    version_line = spec.version_line.format(**format_kwargs)
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
        
def _ensure_exists(path, git_add=True):
    '''
    Ensure file exists
    '''
    if not path.exists():
        logger.info('Creating {}'.format(path))
        path.touch()
        if git_add:
            git_('add', str(path))
        
def _ensure_contains_snippets(path, snippets, format_kwargs, git_add=True):
    '''
    Ensure snippets are present in file
    '''
    with path.open('r') as f:
        content = f.read()
    snippets = (snippet.format(**format_kwargs) for snippet in snippets)
    missing_snippets = [snippet for snippet in snippets if snippet not in content]
    if missing_snippets:
        logger.info('Inserting missing snippets into {}'.format(path))
        with path.open('w') as f:
            f.write('\n'.join(missing_snippets + [content]))
        if git_add:
            git_('add', path)
        
def _update_ini_file(path, defaults, overwrite, format_kwargs, git_add=True):
    '''
    Ensure defaults are applied to missing options and some options are 
    overwritten to a fixed value
    '''
    config = ConfigParser()
    config.read(str(path))
    changed = False
    
    # Ensure sections exist
    for section in defaults.keys() | overwrite.keys():
        if section not in config.sections():
            changed = True
            config.add_section(section)
    
    # Set missing options to their default if any
    for section in defaults:
        for option, value in defaults[section].items():
            if not config.has_option(section, option):
                config[section][option] = value.format(**format_kwargs)
                changed = True
    
    # Overwrite forced options
    for section in overwrite:
        for option, value in overwrite[section].items():
            value = value.format(**format_kwargs)
            if config.get(section, option, fallback=None) != value:
                config[section][option] = value
                changed = True
    
    # Write updated
    if changed:
        logger.info('Writing {}'.format(path))
        with path.open('w') as f:
            config.write(f)
        if git_add:
            git_('add', path)
        
def _raise_if_missing_file(project):
    for file in ('LICENSE.txt', project['readme_file']):
        if not glob(file):
            raise UserException("Missing file: {}".format(file))

def _update_requirements_txt(project_root):
    logger.info('Writing requirements.txt')
    
    input_file_paths = get_dependency_file_paths(project_root)
    regular_dependencies_fd, regular_dependencies_path = mkstemp()
    try:
        regular_dependencies_path = Path(regular_dependencies_path)
        
        # Filter out sip dependencies
        with os.fdopen(regular_dependencies_fd, 'w') as f:
            for input_path in input_file_paths:
                for _, dependency, version_spec, line in parse_requirements_file(input_path):
                    if not dependency:
                        continue
                    if not is_sip_dependency(dependency):
                        f.write(line + '\n')
                    elif not version_spec or not version_spec.startswith('=='):
                        raise UserException("{!r} must be pinned (i.e. must have a '==version' suffix) as it's a sip dependency".format(dependency))

        # Compile requirements
        pb.local['pip-compile'](str(regular_dependencies_path), '-o', 'requirements.txt')  # Note: this eats up most of the time
    finally:
        regular_dependencies_path.unlink()
    
    # Reorder to match ordering in requirements.in
    requirements_txt_path = project_root / 'requirements.txt'
    requirements_txt_lines = {get_dependency_name(line[1]) : line[-1] for line in parse_requirements_file(requirements_txt_path) if line[1]}
    all_dependencies = []
    for input_path in input_file_paths:
        dependency_names = [get_dependency_name(line[1]) for line in parse_requirements_file(input_path) if line[1]]
        dependency_names = [name for name in dependency_names if not is_sip_dependency(name)]
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

def _update_setup_py(project, project_root, pkg_root, format_kwargs):
    logger.debug('Preparing to write setup.py')
    project.update(_get_dependencies(project_root))
    project['long_description'] = pypandoc.convert(project['readme_file'], 'rst')
    project['classifiers'] = [line.strip() for line in project['classifiers'].splitlines() if line.strip()] 
    project['packages'] = find_packages()
    project['package_data'] = _get_package_data(project_root, pkg_root)
    
    # Add download_url if current commit is version tagged
    if project['version'] != _dummy_version:
        project['download_url'] = project['download_url'].format(**format_kwargs)
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
        f.write(setup_py_template.format(pprint.pformat(project, indent=4, width=120)))
    git_('add', setup_py_path)
  
def _get_dependencies(project_root):
    '''
    Returns
    -------
    {'install_requires': ..., 'extras_require': ...}
    '''
    paths = get_dependency_file_paths(project_root)
    extra_requires = {}
    for path in paths: 
        dependencies = []
        for editable, dependency, version_spec, _ in parse_requirements_file(path):
            if not dependency or is_sip_dependency(dependency):
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
        
setup_py_template = spec.setup_py_header + '''\

from setuptools import setup
setup(
    **{}
)
'''.lstrip()
