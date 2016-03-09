'''
ct-release tests
'''

from chicken_turtle_util.exceptions import UserException
from chicken_turtle_project.test.common import create_project, assert_system_exit, git_, mkproject, project1, write_project, test_one1, write_file, suppress_system_exit_0, get_setup_args
from chicken_turtle_project.release import main as release_, _main as release__
from pathlib import Path
import plumbum as pb
import pytest
from click.testing import CliRunner

def release(*args):
    with suppress_system_exit_0():
        release_(args)
        
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
    with assert_system_exit(capsys, stderr_matches='(?i)error.+(dirty|clean)'):
        release('--project-version', '1.0.0')
        
def test_happy_days(tmpcwd, mocked_release):
    '''
    When valid project with clean working dir and valid version, release
    '''
    create_release_project()
    release('--project-version', '1.0.0')
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
    release('--project-version', '1.0.0')
    assert mocked_release.call_args_list == [(('pypi',),)]
    
def test_no_reuse_versions(tmpcwd, capsys):
    '''
    When previously used version is specified, fail gracefully
    '''
    create_release_project()
    release('--project-version', '1.0.0')
    with assert_system_exit(capsys, stderr_matches='version has been released before'):
        release('--project-version', '1.0.0')
        
def test_older_than_ancestor(tmpcwd, capsys):
    '''
    Ask user before releasing with an older version than an ancestor commit 
    '''
    create_release_project()
    git_('tag', 'v2.0.0')
    Path('dummy1').touch()
    git_('add', '.')
    git_('commit', '-m', 'message')
    git_('tag', 'v0.5.0')
    
    result = CliRunner().invoke(release__, ['--project-version', '1.0.0'], input='y\n')
    assert not result.exception
    assert '2.0.0' in result.output
    assert 'less than' in result.output
    assert 'Do you want to' in result.output
    
def test_older_than_other_branch(tmpcwd, capsys):
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
    
    result = CliRunner().invoke(release__, ['--project-version', '1.0.0'])
    assert not result.exception
    assert 'v2.0.0' not in result.output
    assert 'less than' not in result.output
    assert 'Do you want to' not in result.output
        
'''
manual check it actually does it correctly on real PyPI (as 1.0.0-dev1 version) 
'''