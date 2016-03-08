from chicken_turtle_project.common import eval_file, eval_string
from contextlib import contextmanager, ExitStack
from checksumdir import dirhash
from pathlib import Path
from configparser import ConfigParser
import plumbum as pb
import itertools
import pytest
import pprint
import shutil
import git
import re
import os

mkproject = pb.local['ct-mkproject']
git_ = pb.local['git']

project_defaults = dict(
    name='operation_mittens',
    description='Short description',
    author='your name',
    author_email='your_email@example.com',
    readme_file='README.md',
    url='https://example.com/project/home',
    download_url='https://example.com/repo/{version}',
    license='LGPL3',
    keywords='keyword1 key-word2',
    index_test = 'pypitest',
    index_production = 'pypi',
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
    entry_points={
        'console_scripts': [
            'mycli = operation_mittens.main:main',
        ],
    },
)

file_permissions = {
    Path('operation_mittens/__init__.py') : 'update',
    Path('operation_mittens/test/__init__.py') : 'create',
    Path('operation_mittens/test/conftest.py') : 'create',
    Path('requirements.in') : 'create',
    Path('requirements.txt') : 'overwrite',
    Path('deploy_local') : 'create',
    Path('.gitignore') : 'update',
    Path('setup.cfg') : 'update',
    Path('setup.py') : 'overwrite',
    Path('LICENSE.txt') : 'none',
    Path('README.md') : 'none',
}
'''
Maps regular files to their write permission.

All files should exist after running ct-mkproject.

Permissions (each permission level includes all the above, e.g. overwrite may also update and create):

- none
- create
- update
- overwrite 
'''

# non-default minimal project description
project1 = project_defaults.copy()
del project1['entry_points']
project1.update(
    author='mittens',
    author_email='mittens@test.com',
    url='https://test.com/project/home',
    download_url='https://test.com/repo/{version}',
    classifiers='  Development Status :: 2 - Pre-Alpha\nProgramming Language :: Python :: Implementation :: Stackless\n\n'
)

# file templates
gitignore1 = 'pattern1\npattern2'
pkg_init1 = '# pkg init'
test_init1 = '# test init'
requirements_in1 = 'checksumdir'
deploy_local1 = '#!/bin/sh\necho "deploy"'
license_txt1 = 'license'
readme1 = 'readme'
setup_cfg1 = '''
[pytest]
addopts = --basetemp=last_test_runs --maxfail=2
testpaths = bork

[metadata]
description-file = bork

[other]
mittens_says = meow
'''

conftest_py1 = '''
# ours
'''

@pytest.fixture(scope='function')
def tmpcwd(request, tmpdir):
    '''
    Create temp dir make it the current working directory
    '''
    original_cwd = Path.cwd()
    os.chdir(str(tmpdir))
    request.addfinalizer(lambda: os.chdir(str(original_cwd)))
    return tmpdir

## util ######################

# Reusable outside testing too

def write_file(path, contents):
    with Path(path).open('w') as f:
        f.write(contents)
        
def read_file(path):
    with Path(path).open('r') as f:
        return f.read()
        
import hashlib
def file_hash(path):
    '''
    Get SHA512 checksum of file
    
    Parameters
    ----------
    path : pathlib.Path
    
    Returns
    -------
    hash object
        hash of file contents
        
    See also
    --------
    checksumdir.dirhash (TODO or change interface such that it allows directories too, derring to dirhash)
    '''
    with path.open('rb') as f:
        hash_ = hashlib.sha512()
        while True:
            buffer = f.read(65536)
            hash_.update(buffer)
            if not buffer:
                return hash_.digest()
            
def remove_file(path):
    '''
    Remove file or directory (recursively)
    
    Parameters
    ----------
    path : Path
    '''
    if path.is_dir():
        shutil.rmtree(str(path))
    else:
        path.unlink()

## setup util ###########################################

def create_project():
    '''
    Create all required, optional and generated files for ct-mkproject based on `project1`, and init git
    '''
    write_project(project1)
    path = Path('operation_mittens')
    path.mkdir()
    write_file(path / '__init__.py', pkg_init1)
    path /= 'test'
    path.mkdir()
    write_file(path / '__init__.py', test_init1)
    write_file(path / 'conftest.py', conftest_py1)
    write_file('requirements.in', requirements_in1)
    write_file('deploy_local', deploy_local1)
    write_file('.gitignore', gitignore1)
    write_file('LICENSE.txt', license_txt1)
    write_file('setup.cfg', setup_cfg1)
    write_file('setup.py', 'bork')
    write_file('README.md', readme1)
    git_('init')
    
test_template = '''
def test_one():
    pass
'''
    
def create_precommit_project():
    '''
    Create project tailored to precommit tests, i.e. mostly just required files
    '''
    write_project(project1)
    write_file('requirements.in', requirements_in1)
    write_file('LICENSE.txt', license_txt1)
    write_file('README.md', readme1)
    Path('operation_mittens').mkdir()
    Path('operation_mittens/test').mkdir()
    write_file('operation_mittens/test/test_one.py', test_template)
    git_('init')
    
files_create_project = {Path(file) for file in 'operation_mittens operation_mittens/test operation_mittens/__init__.py operation_mittens/test/__init__.py operation_mittens/test/conftest.py requirements.in deploy_local .gitignore setup.cfg setup.py LICENSE.txt README.md'.split()}
'''files created by create_project'''

def write_project(project):
    write_file('project.py', 'project = ' + pprint.pformat(project))

## assertion util ##############################

def get_setup_args():
    with Path('setup.py').open('r') as f:
        content = f.read()
        content = content[content.find('{') : content.rfind('}')+1]
        return eval_string('args=' + content)['args']

@contextmanager
def assert_file_access(*files, read=None, written=None, stat_changed=None, contents_changed=None):
    '''
    Assert particular file access does (not) occur
    
    `contents_changed` is a more stringent condition than `written` as `written=True` 
    only requires the file to have been written to, not to have actually changed.
    
    Parameters
    ----------
    files : iterable of str or Path
    read : bool
        If True, file must have been read (atime, contents or meta read), if False it musn't have been read, else either is fine. 
    written : bool
        If True, file must have been written (mtime, contents changed) to, if False, it musn't have been written to, else either is fine.
    stat_changed : bool
        If True, file must have been changed (ctime, meta info changed, e.g. chmod), if False it musn't have been changed, else either is fine.
    contents_changed : bool
        If True, file contents must differ from original, if False, they may not differ, else either is fine.
    '''
    assert files
    
    stats = [Path(file).stat() for file in files]
    if contents_changed is not None:
        checksums = [file_hash(Path(file)) for file in files]
    assert file_hash(Path('project.py')) == file_hash(Path('project.py')) #TODO rm this double check
    yield
    
    # read, written, stat_changed
    new_stats = [Path(file).stat() for file in files]
    for file, old, new in zip(files, stats, new_stats):
        if read:
            assert old.st_atime_ns != new.st_atime_ns, file
        elif read == False:
            assert old.st_atime_ns == new.st_atime_ns, file
            
        if written:
            assert old.st_mtime_ns != new.st_mtime_ns, file
        elif written == False:
            assert old.st_mtime_ns == new.st_mtime_ns, file
            
        if stat_changed:
            assert old.st_ctime_ns != new.st_ctime_ns, file
        elif stat_changed == False:
            assert old.st_ctime_ns == new.st_ctime_ns, file
            
    # contents_changed
    if contents_changed is not None:
        new_checksums = [file_hash(Path(file)) for file in files]
        for file, old, new in zip(files, checksums, new_checksums):
            if contents_changed:
                assert old != new, file
            else:
                assert old == new, file
                
@contextmanager
def assert_directory_contents(path, changed=True):
    '''
    Assert directory contents change or remain the same.
    
    Contents are compared deeply, i.e. recursively and file contents are considered as well.
    
    Parameters
    ----------
    path : Path
        Path to directory
    changed : bool
        If True, directory contents must change, else contents must remain the same.
    '''
    old = dirhash(str(path), 'sha512')
    yield
    new = dirhash(str(path), 'sha512')
    if changed:
        assert old != new
    else:
        assert old == new

@contextmanager
def assert_process_fails(stderr_matches):
    '''
    Assert process exits with failure
    
    stderr_matches : str
        Assert stderr matches regex pattern 
    '''
    with pytest.raises(pb.ProcessExecutionError) as ex:
        yield
    assert re.search(stderr_matches, ex.value.stderr), 'Expected regex: {}\nto match: {}'.format(stderr_matches, ex.value.stderr)

## tests ###########################################

def test_project_missing(tmpcwd):
    '''
    When project.py missing, ask for a name and generate template
    '''
    # When project.py is missing and git repo exists but has no commits
    create_project()
    remove_file(Path('project.py'))
    (mkproject << project_defaults['name'] + '\n')()
    
    # Then project.py is created and contains the defaults we want
    project_py_path = Path('project.py')
    assert project_py_path.exists()
    project = eval_file(project_py_path)['project']
    assert project == project_defaults
        
def test_project_present(tmpcwd):
    '''
    When project.py exists, it is left alone.
    
    When project lacks optional attributes, succeed.
    '''
    create_project()
    with assert_file_access('project.py', contents_changed=False):
        mkproject & pb.FG
        
def test_project_undefined(tmpcwd):
    '''
    When project.py does not define `project`, abort
    '''
    create_project()
    write_file('project.py', '')
    with assert_process_fails(stderr_matches='must export a `project` variable'):
        mkproject()
        
@pytest.mark.parametrize('required_attr', project1.keys())
def test_project_missing_required_attr(tmpcwd, required_attr):
    '''
    When `project` lacks a required attribute, abort
    '''
    create_project()
    project = project1.copy()
    del project[required_attr]
    write_project(project)
    with assert_process_fails(stderr_matches='Missing.+{}'.format(required_attr)):
        mkproject()
        
@pytest.mark.parametrize('unknown_attr', 'version package_data packages long_description extras_require install_requires unknown'.split())
def test_project_has_unknown_attr(tmpcwd, unknown_attr):
    '''
    When `project` contains an unknown attribute, abort
    '''
    create_project()
    project = project1.copy()
    project[unknown_attr] = 'value'
    write_project(project)
    with assert_process_fails(stderr_matches=unknown_attr):
        mkproject()
        
_parameters = set(itertools.product(project1.keys(), ('', None, ' ', '\t'))) # most attributes may not be empty or None
_parameters.add(('name', 'white space'))
_parameters.add(('name', 'dashed-name'))

@pytest.mark.parametrize('attr,value', _parameters)
def test_project_attr_has_invalid_value(tmpcwd, attr, value):
    '''
    When '\s*' or None as attr values, abort
    
    When dashes or whitespace in name, abort
    '''
    create_project()
    project = project1.copy()
    project[attr] = value
    write_project(project)
    with assert_process_fails(stderr_matches=attr):
        mkproject()
    
def test_idempotent(tmpcwd):
    '''
    Running mkproject twice is the same as running it once, in any case
    '''
    create_project()
    mkproject()
    with assert_directory_contents(Path('.'), changed=False):
        mkproject()

@pytest.mark.parametrize('missing', files_create_project)
def test_missing_files(tmpcwd, missing):
    '''
    When files are missing, create them if allowed, error otherwise

    While files are present and may not be updated, they are left untouched
    '''
    create_project()
    missing_is_dir = missing.is_dir()
    remove_file(missing)
    if not missing_is_dir and file_permissions[missing] == 'none':
        # When can't create, must raise error
        with assert_process_fails(stderr_matches=missing.name):
            mkproject()
    else:
        # When can create, create
        with ExitStack() as contexts:
            for file, permission in file_permissions.items():
                if missing != file and missing not in file.parents and permission not in ('update', 'overwrite'):
                    contexts.enter_context(assert_file_access(file, written=False, contents_changed=False))
            mkproject()
        assert missing.exists()
    # TODO deploy_local is not created, and just py.test until the rest works
    
@pytest.mark.parametrize('name', ('readme.md', 'README.MD', 'REEEADMEE.md'))
def test_wrong_readme_file_name(tmpcwd, name):
    '''
    When files are missing, create them if allowed, error otherwise

    While files are present and may not be updated, they are left untouched
    '''
    create_project()
    project = project1.copy()
    project['readme_file'] = name
    write_project(project)
    Path(name).touch()
    
    with assert_process_fails(stderr_matches='readme_file'):
        mkproject()
    
def test_updates(tmpcwd):
    '''
    When updating a file but not allowed to overwrite, leave the rest of it intact.
    
    - $project_name/__init__.py: leaves all intact, just inserts/overwrites __version__
    - .gitignore: leaves previous patterns intact, does insert the new patterns
    - setup.cfg: leaves previous intact, except for some lines designated to be overwritten
    '''
    create_project() # Note this template is such that each of the files will require an update
    updated_files = ('operation_mittens/__init__.py', '.gitignore', 'setup.cfg')
    with assert_file_access(*updated_files, written=True, contents_changed=True):
        mkproject()
    
    content = read_file('operation_mittens/__init__.py')
    assert pkg_init1 in content
    assert '__version__ =' in content
    
    content = read_file('.gitignore')
    assert gitignore1 in content
    assert '*.egg-info' in content  # check 1 of the patterns is in there, though they should all be in there
    
    config = ConfigParser()
    config.read('setup.cfg')
    assert config['pytest']['addopts'].strip() == '--basetemp=last_test_runs --maxfail=2'  # unchanged
    assert config['pytest']['testpaths'] == 'operation_mittens/test'  # overwritten
    assert config['metadata']['description-file'] == 'README.md'  # overwritten
    assert config['other']['mittens_says'] == 'meow'  # unchanged
        
requirements_in_difficult_template = '''
# line-comment
pytest  # in-line comment
pytest-xdist<5.0.0 # version
# more comment
pytest-env==0.6
-e ./pkg_magic
     
pytest-cov

'''

pkg_magic_setup_py_template = '''
from setuptools import setup
setup(name='pkg4')
'''

def test_setup_py(tmpcwd):
    '''
    - install_requires: requirements.in transformed into valid dependency list with version specs maintained
    - long_description present and nonempty
    - classifiers: list of str
    - packages: list of str of packages
    - package_data: dict of package -> list of str of data file paths
    - author, author_email, description, entry_points keywords license name, url: exact same as input
    '''
    create_project()
    project = project1.copy()
    project['entry_points'] = project_defaults['entry_points']
    write_project(project)
    
    # requirements.in
    write_file('requirements.in', requirements_in_difficult_template)
    Path('pkg_magic').mkdir()
    write_file('pkg_magic/setup.py', pkg_magic_setup_py_template)
    
    # Create package_data in operation_mittens/test (it actually may be in non-test as well):
    Path('operation_mittens/test/data').mkdir()
    Path('operation_mittens/test/data/subdir').mkdir()
    Path('operation_mittens/test/data/subdir/file1').touch()
    Path('operation_mittens/test/data/subdir/file2').touch()
    Path('operation_mittens/test/not_data').mkdir()
    Path('operation_mittens/test/not_data/file').touch()
    Path('operation_mittens/test/not_data/data').mkdir()
    Path('operation_mittens/test/not_data/data/file').touch()
    Path('operation_mittens/test/pkg').mkdir()
    Path('operation_mittens/test/pkg/__init__.py').touch()
    Path('operation_mittens/test/pkg/data').mkdir()
    Path('operation_mittens/test/pkg/data/file').touch()
    
    # Run
    mkproject()
    
    # Assert all the things
    setup_args = get_setup_args()
    
    for attr in ('name', 'author', 'author_email', 'description', 'keywords', 'license', 'url'):
        assert setup_args[attr] == project[attr].strip()
    assert setup_args['entry_points'] == project['entry_points']
        
    assert setup_args['long_description'].strip()
    assert set(setup_args['classifiers']) == {'Development Status :: 2 - Pre-Alpha', 'Programming Language :: Python :: Implementation :: Stackless'}
    assert setup_args['packages'] == ['operation_mittens', 'operation_mittens.test', 'operation_mittens.test.pkg']
    assert {k:set(v) for k,v in setup_args['package_data'].items()} == {
        'operation_mittens.test' : {'operation_mittens/test/data/subdir/file1', 'operation_mittens/test/data/subdir/file2'},
        'operation_mittens.test.pkg' : {'operation_mittens/test/pkg/data/file'},
    }
    assert set(setup_args['install_requires']) == {'pytest', 'pytest-xdist<5.0.0', 'pytest-env==0.6', 'pkg4', 'pytest-cov'}
    assert setup_args['version'] == '0.0.0'
    assert 'download_url' not in setup_args
    
def test_precommit_invalid(tmpcwd):
    '''
    Invalid project cancels the commit
    '''
    create_precommit_project()
    mkproject()  # install pre-commit hook
    remove_file(Path('README.md'))
    git_('add', '.')
    with assert_process_fails(stderr_matches='(?i)error'):
        git_('commit', '-m', 'message')  # runs the hook
     
def test_precommit_include_changes(tmpcwd):
    '''
    Changes made by mkproject must be staged, especially during precommit
    '''
    create_precommit_project()
    mkproject()  # install pre-commit hook
    write_file('requirements.in', 'pytest')
    git_('add', '.')
    git_('commit', '-m', 'message')  # runs the hook, which calls ct-mkproject, which changes setup.py in this case
    
    # Expected change happened
    assert get_setup_args()['install_requires'] == ['pytest']
    
    # And all has been committed
    repo = git.Repo('.')
    assert not repo.is_dirty(untracked_files=True)
            
'''
TODO  

When source file lacks copyright header or header is incorrect, error (and point to all wrong files)

Ensure the readme_file is mentioned in MANIFEST.in 
'''
    