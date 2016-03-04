from chicken_turtle_project.common import eval_file
from contextlib import contextmanager
from checksumdir import dirhash
import itertools
import pytest
import pprint
import os
import re
 
'''
The following files are created if missing:
- project.py
- $project_name package (=dir and __init__.py)
- $project_name/test package
- requirements.in
- deploy_local

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

Errors are emitted if these files are missing:
- LICENSE.txt
- README.*

When LICENSE.txt, README.* has wrong case, error.

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

from pathlib import Path
import plumbum as pb

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

# non-default minimal project description
project1 = project_defaults.copy()
del project1['entry_points']
project1.update(
    author='mittens',
    author_email='mittens@test.com',
    url='https://test.com/project/home',
    download_url='https://test.com/repo/{version}',
)

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
                return hash

## setup util ###########################################

def create_project(has_project_py=True, has_src_pkg=True, has_test_pkg=True, has_requirements_in=True, has_deploy_local=True, has_git=True, has_license=True, has_readme=True):
    '''
    Create project
    
    Parameters
    ----------
    has_project_py : bool
        If True, create project.py with project1
    '''
    if has_project_py:
        write_project(project1)
    
    if has_git:
        git_('init')
    
    if has_license:
        Path('LICENSE.txt').touch()
            
    if has_readme:
        Path(project1['readme_file']).touch()

def write_project(project):
    write_file('project.py', 'project = ' + pprint.pformat(project))

## assertion util ##############################

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
        
    yield
    
    # read, written, stat_changed
    new_stats = [Path(file).stat() for file in files]
    for old, new in zip(stats, new_stats):
        if read:
            assert old.st_atime_ns != new.st_atime_ns
        elif read == False:
            assert old.st_atime_ns == new.st_atime_ns
            
        if written:
            assert old.st_mtime_ns != new.st_mtime_ns
        elif written == False:
            assert old.st_mtime_ns == new.st_mtime_ns
            
        if stat_changed:
            assert old.st_ctime_ns != new.st_ctime_ns
        elif stat_changed == False:
            assert old.st_ctime_ns == new.st_ctime_ns
            
    # contents_changed
    if contents_changed is not None:
        new_checksums = [file_hash(Path(file)) for file in files]
        for old, new in zip(checksums, new_checksums):
            if contents_changed:
                assert old != new
            else:
                assert old == new
                
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
    create_project(has_project_py=False)
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
    