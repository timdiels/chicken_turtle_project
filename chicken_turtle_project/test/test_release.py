'''
ct-release tests
'''

from chicken_turtle_util.exceptions import UserException
from chicken_turtle_project.test.common import create_project, assert_system_exit, git_
from chicken_turtle_project.release import main as release_
import pytest
import re

## fixtures, util ##########################

def release(*args):
    release_(args)
    
# @pytest.fixture(autouse=True, scope='function')
# def mocked_release(mocker):
#     stub = mocker.patch('chicken_turtle_project.release._release')
#     return stub

# def create_release_project():
#     '''
#     Create valid project for release
#     '''
#     create_project()
#     git_('add', '.')
#     mkproject()

## tests ##########################

def test_dirty(tmpcwd, capsys):
    '''
    When working directory is dirty, error
    '''
    create_project()  # leaves behind untracked files
    with assert_system_exit(capsys, stderr_matches='(?i)error.+untracked'):
        release('--project-version', '1.0.0')

'''
call with --version (assume click knows how to do requiredness)
if working dir is dirty, error
release to test if any (try with and without)
release to production if release to test succeeded

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
'''