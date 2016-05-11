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
from datetime import date
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
    '--project-version',
    default=_dummy_version,
    envvar='CT_PROJECT_VERSION',
    help='Internal option, do not use.'
)
@click.version_option(version=__version__)
def _main(project_version):
    '''
    Create, update and validate project, enforcing Chicken Turtle Project
    development methodology.
    
    ct-mkproject must be run from the root of the project (where setup.py should be).
    
    The project must be in a git repository. 
    
    The following files are created if missing:
    
    - project.py
    - docs/conf.py
    - docs/index.rst
    - docs/Makefile
    
    The following files may be created or updated by merging in changes:
    
    - $project_name/__init__.py
    - $project_name/tests/conftest.py
    - .gitignore
    - .coveragerc
    - setup.cfg
    - requirements.in
    - dev_requirements.in
    - test_requirements.in
    - MANIFEST.in
    
    The following files will be created or overwritten if they exist:
    
    - requirements.txt
    - setup.py
    
    Warnings are emitted if these files are missing:
    
    - LICENSE.txt
    - readme file pointed to by readme_file
    
    py.test will be configured to run tests in $project_name.tests and subpackages.
    
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
        pkg_root = get_pkg_root(project_root, project['package_name'])
        project['version'] = project_version
        
        format_kwargs = {
            'name': project['name'],
            'human_friendly_name': project['human_friendly_name'],
            'author': project['author'],
            'readme_file': project['readme_file'],
            'pkg_root': str(pkg_root.relative_to(project_root)),
            'pkg_root_root': str(project['package_name'].split('.')[0]),
            'pkg_name': project['package_name'],
            'version': project_version,
            'year': date.today().year,
        }
        
        path = pkg_root
        while path != project_root:
            _ensure_exists(path / '__init__.py')
            path = path.parent
        _update_root_package(pkg_root, format_kwargs)
        
        test_root = pkg_root / 'tests'
        _ensure_exists(test_root / '__init__.py')
        
        conftest_py_path = test_root / 'conftest.py'
        _ensure_exists(conftest_py_path)
        _ensure_contains_snippets(conftest_py_path, {spec.conftest_py}, format_kwargs)
        
        manifest_in = project_root / 'MANIFEST.in'
        _ensure_exists(manifest_in)
        _ensure_contains_snippets(manifest_in, spec.manifest_in, format_kwargs)
        
        requirements_in_path = project_root / 'requirements.in'
        _ensure_exists(requirements_in_path)
        _ensure_contains_snippets(requirements_in_path, {spec.requirements_in_header}, format_kwargs)

        dev_requirements_in_path = project_root / 'dev_requirements.in'
        _ensure_exists(dev_requirements_in_path)
        _ensure_contains_snippets(dev_requirements_in_path, spec.dev_requirements_in, format_kwargs)
        
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
        
        doc_root = project_root / 'docs' 
        _ensure_exists(doc_root / 'conf.py', spec.docs_conf_py, format_kwargs)
        _ensure_exists(doc_root / 'Makefile', spec.docs_makefile, raw=True)
        _ensure_exists(doc_root / 'index.rst', spec.docs_index_rst, format_kwargs)
            
def _ensure_project_exists(project_root):
    project_path = project_root / 'project.py'
    if not project_path.exists():
        logger.info('project.py not found, will create from template')
        name = click.prompt('Please pick a name to register your project (later) with at an index (like PyPI)')
        pkg_name = name.replace('-', '_')
        pkg_name = click.prompt('What is the name of the root package? (e.g. {pkg_name} or {pkg_name}.subproject)'.format(pkg_name=pkg_name))
        human_friendly_name = click.prompt('Please pick a human friendly name for your project')
        assert name and name.strip()
        assert human_friendly_name and human_friendly_name.strip()
        with project_path.open('w') as f:
            logger.info('Creating project.py')
            f.write(spec.project_py.format(name=name, human_friendly_name=human_friendly_name, pkg_name=pkg_name))
            git_('add', str(project_path))
        
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
    
def _ensure_dir_exists(path):
    if not path.exists():
        path.mkdir()
        
def _ensure_exists(path, content='', format_kwargs={}, raw=False, git_add=True):
    '''
    Ensure file exists
    '''
    os.makedirs(str(path.parent), exist_ok=True)
    if not path.exists():
        logger.info('Creating {}'.format(path))
        with path.open('w') as f:
            if not raw:
                content = content.format(**format_kwargs)
            f.write(content)
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
    requirements_txt_lines = {get_dependency_name(line[0], line[1]) : line[-1] for line in parse_requirements_file(requirements_txt_path) if line[1]}
    all_dependencies = []
    for input_path in input_file_paths:
        dependency_names = [get_dependency_name(line[0], line[1]) for line in parse_requirements_file(input_path) if line[1]]
        dependency_names = [name for name in dependency_names if not is_sip_dependency(name)]
        all_dependencies.append(setlist(dependency_names))

    all_dependencies = toset_from_tosets(*all_dependencies)
    with requirements_txt_path.open('w') as f:
        for name in all_dependencies:  # write ordered
            f.write(requirements_txt_lines[name] + '\n')
        for name, line in sorted(requirements_txt_lines.items()):  # write left-overs, sorted to avoid unnecessary diffs in git
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
    project['package_data'] = _get_package_data(project_root, project['packages'])
    
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
    del project['human_friendly_name']
    del project['pre_commit_no_ignore']
    del project['package_name']
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
        for editable, dependency_url, version_spec, _ in parse_requirements_file(path):
            if not dependency_url:
                continue
            name = get_dependency_name(editable, dependency_url)
            if is_sip_dependency(name):
                continue
            dependencies.append(name + (version_spec or ''))
        if path.name == 'requirements.in':
            install_requires = dependencies
        else:
            name = re.fullmatch('(.*)_requirements.in', path.name).group(1)
            extra_requires[name] = dependencies
    return dict(install_requires=install_requires, extras_require=extra_requires)
    
def _get_package_data(project_root, packages):
    package_data = defaultdict(list) 
    for package in packages:
        package_dir = project_root / package.replace('.', '/')
        data_dir = package_dir / 'data'
        if data_dir.exists() and not (data_dir / '__init__.py').exists():
            # Found a data dir
            for parent, _, files in os.walk(str(data_dir)):
                package_data[package].extend(str((data_dir / parent / file).relative_to(package_dir)) for file in files)
    return {k: sorted(v) for k,v in package_data.items()}  # sort to avoid unnecessary git diffs
        
setup_py_template = spec.setup_py_header + '''\

from setuptools import setup
setup(
    **{}
)
'''
