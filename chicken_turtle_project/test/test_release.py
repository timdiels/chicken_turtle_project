'''
ct-release tests
'''

from chicken_turtle_project.test.common import create_project, assert_process_fails, git_, mkproject
import plumbum as pb

release = pb.local['ct-release']['--dry-run']

# def create_release_project():
#     '''
#     Create valid project for release
#     '''
#     create_project()
#     git_('add', '.')
#     mkproject()
    

## tests ##########################

def test_dirty(tmpcwd):
    '''
    When working directory is dirty, error
    '''
    create_project()  # leaves behind untracked files
    with assert_process_fails(stderr_matches=r'(?i)error.+untracked'):
        release('--version', '1.0.0')
    
'''
-n --dry-run

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