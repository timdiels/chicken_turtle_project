'''
mock _release!

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