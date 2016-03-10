'''
ct-release tests
'''

from chicken_turtle_util.exceptions import UserException
from chicken_turtle_project.test.common import (
    create_project, assert_re_search, git_, mkproject, project1, write_project, 
    test_one1, write_file, get_setup_args, write_complex_requirements_in
)
from chicken_turtle_project.release import main as release_
from pathlib import Path
import plumbum as pb
import pytest
from click.testing import CliRunner
import logging

def reset_logging():
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
    
def release(*args, **invoke_kwargs):
    '''
    Call release, suppress all exceptions
    '''
    result = CliRunner().invoke(release_, args, **invoke_kwargs)
    reset_logging()
    assert (result.exit_code == 0) == (result.exception is None or (isinstance(result.exception, SystemExit) and result.exception.code == 0))
    return result
        
## fixtures ##########################

@pytest.fixture(autouse=True, scope='function')
def mocked_release(mocker):
    stub = mocker.patch('chicken_turtle_project.release._release')
    return stub


## util ##########################
 
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
    result = release('--project-version', '1.0.0')
    assert result.exit_code != 0
    assert_re_search('(?i)error.+(dirty|clean)', result.output)

def test_happy_days(tmpcwd, mocked_release):
    '''
    When valid project with clean working dir and valid version, release
    '''
    create_release_project()
    result = release('--project-version', '1.0.0')
    assert result.exit_code == 0
    assert mocked_release.call_args_list == [(('pypitest',),), (('pypi',),)]
    assert git_('tag').strip() == 'v1.0.0'
    setup_args = get_setup_args()
    assert '1.0.0' in setup_args['download_url']
    assert setup_args['version'] == '1.0.0'

def test_no_test_index(tmpcwd, mocked_release):
    '''
    When no index_test is specified, succeed
    '''
    create_release_project(test_index=False)
    result = release('--project-version', '1.0.0')
    assert result.exit_code == 0
    assert mocked_release.call_args_list == [(('pypi',),)]

def test_no_reuse_versions(tmpcwd, capsys):
    '''
    When previously used version is specified, fail gracefully
    '''
    create_release_project()
    result = release('--project-version', '1.0.0')
    assert result.exit_code == 0
    print(result.output)
    result = release('--project-version', '1.0.0')
    print(result.output)
    assert result.exit_code != 0
    assert 'version has been released before' in result.output
        
def test_older_than_ancestor(tmpcwd):
    '''
    Ask user before releasing with an older version than an ancestor commit 
    '''
    create_release_project()
    git_('tag', 'v2.0.0')
    Path('dummy1').touch()
    git_('add', '.')
    git_('commit', '-m', 'message')
    git_('tag', 'v0.5.0')
    
    result = release('--project-version', '1.0.0', input='y\n')
    assert result.exit_code == 0
    assert '2.0.0' in result.output
    assert 'less than' in result.output
    assert 'Do you want to' in result.output

def test_older_than_other_branch(tmpcwd):
    '''
    Don't ask user before releasing with an older version than a commit in another branch (i.e. not an ancestor) 
    '''
    create_release_project()
    git_('tag', 'v0.5.0')
    
    git_('checkout', '-b', 'other')
    Path('dummy1').touch()
    git_('add', '.')
    git_('commit', '-m', 'message')
    git_('tag', 'v2.0.0')
    
    git_('checkout', 'master')
    Path('dummy2').touch()
    git_('add', '.')
    git_('commit', '-m', 'message')
    git_('tag', 'v0.8.0')
    
    result = release('--project-version', '1.0.0')
    assert result.exit_code == 0
    assert 'v2.0.0' not in result.output
    assert 'less than' not in result.output
    assert 'Do you want to' not in result.output

def test_editable_requirements(tmpcwd, capsys):
    '''
    When requirements.txt contains editable dependencies (-e), error
    '''
    create_release_project()
    write_complex_requirements_in()
    git_('add', '.')
    git_('commit', '-m', 'message')
    result = release('--project-version', '1.0.0')
    assert result.exit_code != 0
    assert 'No editable requirements (-e) allowed for release' in result.output
