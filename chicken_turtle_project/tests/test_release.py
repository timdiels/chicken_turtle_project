'''
ct-release tests
'''

from chicken_turtle_project.tests.common import (
    create_project, git_, mkproject, project1, get_setup_args, extra_files,
    reset_logging, write_file, add_complex_requirements_in
)
from chicken_turtle_project.release import main as release_
from pathlib import Path
import plumbum as pb
import pytest
from click.testing import CliRunner
    
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

def create_release_project(project=project1, test_index=True):
    '''
    Create valid project for release
    '''
    project = project.copy()
    test_succeed_path = Path('operation/mittens/tests/test_succeed.py')
    project.files[test_succeed_path] = extra_files[test_succeed_path] 
    if test_index:
        project.project_py['index_test'] = 'pypitest'
    create_project(project)
    
    git_('add', '.')
    mkproject()
    git_['commit', '-m', 'Initial commit'] & pb.FG
    
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

def test_ignore_staged(tmpcwd):
    '''
    When working directory is dirty, ignore staged changes
    '''
    create_release_project()
    write_file(Path('project.py'), '')  # Invalid project.py
    git_('add', 'project.py')
    result = release('1.0.0')
    assert result.exit_code == 0, result.output
    
def test_ignore_untracked(tmpcwd):
    '''
    When working directory is dirty, ignore untracked files
    '''
    create_release_project()
    test_fail_path = Path('operation/mittens/tests/test_fail.py')
    write_file(test_fail_path, extra_files[test_fail_path])
    result = release('1.0.0')
    assert result.exit_code == 0, result.output

def test_ignore_unstaged(tmpcwd):
    '''
    When working directory is dirty, ignore unstaged changes
    '''
    create_release_project()
    write_file(Path('project.py'), '')  # Invalid project.py
    result = release('1.0.0')
    assert result.exit_code == 0, result.output

def test_happy_days(tmpcwd, mocked_release):
    '''
    When valid project with clean working dir and valid version, release
    '''
    create_release_project()
    result = release('1.0.0')
    git_('reset', '--hard')
    assert result.exit_code == 0, result.output
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
    result = release('1.0.0')
    assert result.exit_code == 0
    assert mocked_release.call_args_list == [(('pypi',),)]

def test_no_reuse_versions(tmpcwd):
    '''
    When previously used version is specified, fail gracefully
    '''
    create_release_project()
    result = release('1.0.0')
    assert result.exit_code == 0, result.output
    result = release('1.0.0')
    assert result.exit_code != 0, result.output
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
    
    result = release('1.0.0', input='y\n')
    assert result.exit_code == 0, result.output
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
    
    result = release('1.0.0')
    assert result.exit_code == 0, result.output
    assert 'v2.0.0' not in result.output
    assert 'less than' not in result.output
    assert 'Do you want to' not in result.output

def test_editable_requirements(tmpcwd):
    '''
    When requirements.txt contains editable dependencies (-e), error
    '''
    project = project1.copy()
    add_complex_requirements_in(project)
    create_release_project(project)
    git_('add', '.')
    git_('commit', '-m', 'message')
    result = release('1.0.0')
    assert result.exit_code != 0
    assert 'No editable requirements (-e) allowed for release' in result.output
            