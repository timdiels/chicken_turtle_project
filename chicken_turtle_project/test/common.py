'''
common test setup, assertions and utilities
'''

from chicken_turtle_project.common import eval_string
from contextlib import contextmanager
from checksumdir import dirhash
from pathlib import Path
import plumbum as pb
import pytest
import pprint
import shutil
import re

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
del project1['index_test']
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

test_one1 = '''
def test_one():
    pass
'''

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
    Create all required, optional and generated files for ct-mkproject based on `project1`, and init git but leave everything untracked
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
    

_requirements_in_difficult_template = '''
# line-comment
pytest  # in-line comment
pytest-xdist<5.0.0 # version
# more comment
pytest-env==0.6
-e ./pkg_magic
     
pytest-cov

'''

_pkg_magic_setup_py_template = '''
from setuptools import setup
setup(name='pkg4')
'''

def write_complex_requirements_in():
    '''
    Write requirements.in with -e deps and comments
    '''
    write_file('requirements.in', _requirements_in_difficult_template)
    Path('pkg_magic').mkdir()
    write_file('pkg_magic/setup.py', _pkg_magic_setup_py_template)

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
    
def assert_re_search(pattern, string):
    assert re.search(pattern, string), 'Expected regex: {}\nto match: {}'.format(pattern, string)
    
