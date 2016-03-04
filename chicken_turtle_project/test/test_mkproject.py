from chicken_turtle_project.common import eval_file
from contextlib import contextmanager
 
'''
error = UserException usually

When project.py does not define `project`, error

When `project` lacks a required attribute, error
    'name readme_file description author author_email url classifiers keywords download_url index_test index_production'
    
'\s*' and None are invalid attr values, however index_test allows None, should error

When whitespace or dashes in project[name], error 
    
When `project` contains an unknown attribute, error
    'license version package_data packages long_description extras_require install_requires unknown'

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

project1 = project_defaults.copy()
project1.update(
    author='mittens',
    author_email='mittens@test.com',
    url='https://test.com/project/home',
    download_url='https://test.com/repo/{version}',
    entry_points={
        'console_scripts': [
            'meow = operation_mittens.main:main',
        ],
    },
)

def create_project(has_project_py=True, has_src_pkg=True, has_test_pkg=True, has_requirements_in=True, has_deploy_local=True, has_git=True, has_license=True, has_readme=True):
    if has_git:
        git_('init')
    
    if has_license:
        Path('LICENSE.txt').touch()
            
    if has_readme:
        Path(project1['readme_file']).touch()
    
def write_file(path, contents):
    with path.open('w') as f:
        f.write(contents)

@contextmanager
def ensure_file_access(*files, read=None, written=None, stat_changed=None):
    '''
    Ensure particular file access
    
    Parameters
    ----------
    files : iterable of str
    read : bool
        If True, file must have been read (atime, contents or meta read), if False it musn't have been read, else either is fine. 
    written : bool
        If True, file must have been written (mtime, contents changed) to, if False, it musn't have been written to, else either is fine.
    stat_changed : bool
        If True, file must have been changed (ctime, meta info changed, e.g. chmod), if False it musn't have been changed, else either is fine. 
    '''
    assert files
    stats = [Path(file).stat() for file in files]
    yield
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

def is_valid_project():
    pass

def test_project_missing(tmpdir):
    '''
    When project.py missing, ask for a name and generate template
    '''
    with pb.local.cwd(tmpdir):
        # When project.py is missing and git repo exists but has no commits
        create_project(has_project_py=False)
        (mkproject << project_defaults['name'] + '\n')()
        
        # Then project.py is created and contains the defaults we want
        project_py_path = Path('project.py')
        assert project_py_path.exists()
        project = eval_file(project_py_path)['project']
        assert project == project_defaults
        
def test_project_present(tmpdir):
    '''
    When project.py exists, it is left alone
    '''
    create_project()
    with ensure_file_access('project.py', written=False):
        mkproject()
    
# def test_idempotent(tmpdir):
#     '''
#     Running mkproject twice is the same as running it once, in any case
#     '''
#     assert False
    