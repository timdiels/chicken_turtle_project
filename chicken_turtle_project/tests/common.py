'''
common test setup, assertions and utilities
'''

from chicken_turtle_project import specification
from chicken_turtle_project.common import eval_string
from contextlib import contextmanager
from checksumdir import dirhash
from textwrap import dedent
from datetime import date
from pathlib import Path
import plumbum as pb
import logging
import pytest
import pprint
import re
import os

mkproject = pb.local['ct-mkproject']
git_ = pb.local['git']

# When a project is created from scratch, these should be the project.py defaults
project_defaults = dict(
    name='operation-mittens',
    package_name='operation.mittens',
    human_friendly_name='Operation Mittens',
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
            'mycli = operation.mittens.main:main',
        ],
    },
    pre_commit_no_ignore = [
        'test.conf',
        'secrets/*',
    ]
)

# Project templates
class Project(object):
    
    def __init__(self, project_py, format_kwargs, files):
        self.project_py = project_py
        self.format_kwargs = format_kwargs
        self.files = files  # all files excluding project.py
        
    def copy(self):
        return Project(dict(self.project_py), dict(self.format_kwargs), dict(self.files))

# Project 1
_project_py = project_defaults.copy()
for name in specification.project_py_optional_attributes:
    del _project_py[name]
_project_py.update(
    author='Mittens Glorious',
    author_email='mittens@test.com',
    url='https://test.com/project/home',
    download_url='https://test.com/repo/{version}',
    classifiers='  Development Status :: 2 - Pre-Alpha\nProgramming Language :: Python :: Implementation :: Stackless\n\n'
)

_format_kwargs = {
    'name': 'operation-mittens',
    'human_friendly_name': 'Operation Mittens',
    'author' : 'Mittens Glorious',
    'pkg_name': 'operation.mittens',
    'pkg_root': 'operation/mittens',
    'pkg_root_root': 'operation',
    'version': '0.0.0',
    'readme_file': 'README.md',
    'year': date.today().year,
}

_project_files = {
    Path('.gitignore'): 'pattern1\npattern2',
    Path('.coveragerc'): '# mittens coverage_rc',
    Path('operation/mittens/__init__.py'): '# mittens pkg init',
    Path('operation/mittens/tests/__init__.py'): '# mittens test init',
    Path('operation/mittens/tests/conftest.py'): '# mittens conftest',
    Path('requirements.in'): 'pytest\nchecksumdir',
    Path('dev_requirements.in'): '# mittens dev_requirements',
    Path('test_requirements.in'): 'pytest-pep8',
    Path('requirements.txt'): '# mittens requirements.txt',
    Path('LICENSE.txt'): 'mittens license',
    Path('README.md'): 'mittens readme',
    Path('MANIFEST.in'): '# mittens manifest',
    Path('setup.cfg'): dedent('''\
        [pytest]
        addopts = --basetemp=last_test_runs --maxfail=2
        testpaths = bork
        
        [metadata]
        description-file = bork
        
        [other]
        mittens_says = meow
        '''),
    Path('setup.py'): '# mittens setup.py',
    Path('docs/index.rst'): '.. mittens index.rst',
    Path('docs/conf.py'): '# mittens conf.py',
    Path('docs/Makefile'): dedent('''\
        all:
        \ttrue
        
        html:
        \ttrue
        '''),
} 

#: project with all required, optional, generated files already present.
#:
#: Each updatable file lacks all required content, and has some other content. When
#: the required content is merged in, the project is valid.
project1 = Project(_project_py, _format_kwargs, _project_files) 

# Extra files (handy to include in some tests)
extra_files = {
    Path('operation/mittens/tests/test_succeed.py'): dedent('''\
        def test_succeed():
            pass
        '''),
    Path('operation/mittens/tests/test_fail.py'): dedent('''\
        def test_fail():
            assert False
        ''')
}

## util ######################

# Reusable outside testing too

def write_file(path, contents): # TODO now in CTU: path.write. Consider making our class Path(pathlib.Path)
    with Path(path).open('w') as f:
        f.write(contents)
        
def read_file(path): #TODO use from CTU
    with Path(path).open('r') as f:
        return f.read()
        
import hashlib
def file_hash(path): # TODO use CTU.path.hash, it works on dirs too though
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
    checksumdir.dirhash (TODO or change interface such that it allows directories too, deferring to dirhash)
    '''
    with path.open('rb') as f:
        hash_ = hashlib.sha512()
        while True:
            buffer = f.read(65536)
            hash_.update(buffer)
            if not buffer:
                return hash_.digest()


## setup util ###########################################

def create_project(project=project1):
    '''
    Create project 1 with all required, optional and generated files for ct-mkproject, and init git but leave everything untracked
    '''
    write_file(Path('project.py'), 'project = ' + pprint.pformat(project.project_py))
    for path, content in  project.files.items():
        os.makedirs(str(path.parent), exist_ok=True)
        write_file(path, content)
    git_('init')
    
def add_complex_requirements_in(project):
    project.files[Path('requirements.in')] = dedent('''\
        
        # line-comment
        pytest  # in-line comment
        pytest-testmon<5.0.0 # version
        # more comment
        pytest-env==0.6
        -e ./pkg_magic
             
        pytest-cov

        ''')
    project.files[Path('pkg_magic/setup.py')] = dedent('''\
        from setuptools import setup
        setup(name='pkg4')
        ''')
    
def reset_logging(): # XXX add to CTU, maybe
    '''
    Reset logging to its original state (as if it were freshly imported)
    
    Note: pytest also resets logging between tests it seems, but
    if you need to setup logging twice in the same test, this is
    what you need.
    '''
    root = logging.root
    while root.handlers:
        root.removeHandler(root.handlers[-1])
    while root.filters:
        root.removeFilter(root.filters[-1])

## assertion util ##############################

def get_setup_args():
    with Path('setup.py').open('r') as f:
        content = f.read()
        content = content[content.find('{') : content.rfind('}')+1]
        return eval_string('args=' + content)['args']

# XXX some of these asserts may be good for CTU.test
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
    assert re.search(stderr_matches, ex.value.stderr), 'Expected regex: {}\nto match: {}\nstdout is: {}'.format(stderr_matches, ex.value.stderr, ex.value.stdout)
    
def assert_re_search(pattern, string):
    assert re.search(pattern, string), 'Expected regex: {}\nto match: {}'.format(pattern, string)
    
