from chicken_turtle_project.common import eval_file
from contextlib import contextmanager, ExitStack
from checksumdir import dirhash
from pathlib import Path
import plumbum as pb
import itertools
import pytest
import pprint
import shutil
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
)

# file templates
gitignore1 = 'pattern1\npattern2'
pkg_init1 = '# init'
test_init1 = '# init'
requirements_in1 = 'checksumdir'
deploy_local1 = '#!/bin/sh\necho "deploy"'
license_txt1 = 'license'
readme1 = 'readme'
setup_cfg1 = '''
[pytest]
addopts = --basetemp=last_test_runs --maxfail=1
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
    
files_create_project = {Path(file) for file in 'operation_mittens operation_mittens/test operation_mittens/__init__.py operation_mittens/test/__init__.py operation_mittens/test/conftest.py requirements.in deploy_local .gitignore setup.cfg setup.py LICENSE.txt README.md'.split()}
'''files created by create_project'''

def write_project(project):
    write_file('project.py', 'project = ' + pprint.pformat(project))

## assertion util ##############################

@contextmanager
def assert_file_access(file, read=None, written=None, stat_changed=None, contents_changed=None):
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
    files = [file]
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
        
# For the next tests we assume that none of the created files are messed with if we have no higher than create permission
'''
When README.* has wrong case, error.

The following files may be created or updated by merging in changes:
- $project_name/__init__.py: leaves all intact, just inserts/overwrites __version__
- .gitignore: leaves previous patterns intact, does insert the new patterns
- setup.cfg: leaves previous intact, except for some lines designated to be overwritten
    no setup.cfg
    empty setup.cfg
    setup.cfg with unrelated section
    setup.cfg with unrelated and related sections with all the options and some extra options
    
    Expect: pytest.addopts create if not exist; pytest.testpaths (projName/test), metadata.description-file (project readme file path) always overwrite

The following files will be created or overwritten if they exist:
- requirements.txt: check it was created, we trust piptools does it right
- setup.py:
    install_requires:
        requirements.in with version things
        requirements.in with -e
        -> should all be thrown in as valid setup.py stuff with version spec maintained
        
    long_description present and nonempty
    classifiers: list of str
    packages: list of str of packages
    package_data: dict of package -> list of str of data file paths
        # - pkg[init]/pkg[init]/data/derr/data -> only pick the top data
        # - pkg[init]/notpkg/data -> don't pick data dir as it's not child of a package
        # be sure to test for correct pkg names too    
    download_url: must be present if was tagged version, must be url. May not be present otherwise
    author, author_email, description, entry_points keywords license name, url: exact same as input
    version: must match what the version tests expect (e.g. tagged version vs other tag vs no tag)
    no other attribs may be present
    
    a few sanity checks with: python setup.py

ct-mkproject ensures certain patterns are part of .gitignore, but does not erase any patterns you added.

py.test will be configured to run test in $project_name.test and subpackages and nowhere else

Must be in a git repo, else error

Versions:
- if tagged version, use that one
- else max of git tags with dev bump
- if no tags at all, 0.0.0-dev1
__version__ in __init__.py must match this version

If tagged version, warn if it is less than that of an ancestor commit:
- case where it should warn
- trivial where it shouldn't (e.g. we are the only commit)
- multi-branch where it shouldn't (it's fine by current branch, but there are newer commits in another branch)

pre-commit:
- it should be created and call ./deploy_local
- tagged version picked up correctly in a repo of 1 commit and ready to commit a second?
- when any project related file changes during pre-commit, it should be part of the commit. Any other unstaged changes should remain unstaged however!
- invalid project cancels the commit

When source file lacks copyright header or header is incorrect, error (and point to all wrong files)

TODO ensure the readme_file is mentioned in MANIFEST.in 
'''