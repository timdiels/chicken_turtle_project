'''
ct-release tests
'''

from chicken_turtle_util.exceptions import UserException
from chicken_turtle_project.test.common import create_project, assert_system_exit, git_, mkproject, project1, write_project, test_one1, write_file, suppress_system_exit_0
from chicken_turtle_project.release import main as release_
from pathlib import Path
import plumbum as pb
import pytest

## fixtures ##########################

@pytest.fixture(autouse=True, scope='function')
def mocked_release(mocker):
    stub = mocker.patch('chicken_turtle_project.release._release')
    return stub


## util ##########################

def release(*args):
    with suppress_system_exit_0():
        release_(args)
 
def create_release_project(test_index=True):
    '''
    Create valid project for release
    '''
    create_project()
    write_file('operation_mittens/test/test_one.py', test_one1)
    if test_index:
        project = project1.copy()
        project['index_test'] = 'pypitest'
        write_project(project)
    git_('add', '.')
    mkproject()
    git_('commit', '-m', 'Initial commit')
    
    # Create repo and use as remote
    path = Path.cwd() / '.cache'  # some location ignored by .gitignore
    path.mkdir()
    path /= 'other_repo'
    path.mkdir()
    with pb.local.cwd(str(path)):
        git_('init', '--bare')
    git_('remote', 'add', 'origin', path.as_uri())
    git_('push', '--set-upstream', 'origin', 'master')
    git_['status'] & pb.FG

## tests ##########################

def test_dirty(tmpcwd, capsys):
    '''
    When working directory is dirty, error
    '''
    create_project()  # leaves behind untracked files
    with assert_system_exit(capsys, stderr_matches='(?i)error.+(dirty|clean)'):
        release('--project-version', '1.0.0')
        
def test_happy_days(tmpcwd, mocked_release):
    '''
    When valid project with clean working dir and valid version, release
    '''
    create_release_project()
    release('--project-version', '1.0.0')
    assert mocked_release.call_args_list == [(('pypitest',),), (('pypi',),)]
    
def test_no_test_index(tmpcwd, mocked_release):
    '''
    When no index_test is specified, succeed
    '''
    create_release_project(test_index=False)
    release('--project-version', '1.0.0')
    assert mocked_release.call_args_list == [(('pypi',),)]
    
def test_no_reuse_versions(tmpcwd, mocked_release, capsys):
    '''
    When previously used version is specified, fail gracefully
    '''
    create_release_project()
    release('--project-version', '1.0.0')
    with assert_system_exit(capsys, stderr_matches='version has been released before'):
        release('--project-version', '1.0.0')

'''
--version: 
- cannot be a previously used version
- warn if it is less than that of an ancestor commit and ask to confirm:
  - case where it should warn
  - trivial where it shouldn't (e.g. we are the only commit)
  - multi-branch where it shouldn't (it's fine by current branch, but there are newer commits in another branch)
  
Must add git tag for this version on the correct commit before releasing.

setup.py:
- download_url: must be url
- version: what the user specified

manual check it actually does it correctly on real PyPI (as 1.0.0-dev1 version) 
'''