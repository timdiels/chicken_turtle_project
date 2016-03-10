'''
ct-mkproject tests
'''

from chicken_turtle_project.test.common import (
    create_project, remove_file, mkproject, project_defaults, write_project, write_file, 
    git_, requirements_in1, license_txt1, readme1, test_one1, project1,
    assert_directory_contents, assert_process_fails, assert_file_access,
    read_file, gitignore1, get_setup_args, files_create_project,
    pkg_init1, write_complex_requirements_in
)
from contextlib import ExitStack
from chicken_turtle_project.common import eval_file
from pathlib import Path
from configparser import ConfigParser
import plumbum as pb
import itertools
import pytest
import git

## setup, asserts, util #######################################

file_permissions = {
    Path('operation_mittens/__init__.py') : 'update',
    Path('operation_mittens/test/__init__.py') : 'create',
    Path('operation_mittens/test/conftest.py') : 'create',
    Path('requirements.in') : 'create',
    Path('requirements.txt') : 'overwrite',
    Path('deploy_local') : 'create',
    Path('.gitignore') : 'update',
    Path('setup.cfg') : 'update',
    Path('setup.py') : 'overwrite',
    Path('LICENSE.txt') : 'none',
    Path('README.md') : 'none'
}
'''
Maps regular files to their write permission.

All files should exist after running ct-mkproject.

Permissions (each permission level includes all the above, e.g. overwrite may also update and create):

- none
- create
- update
- overwrite 
'''
    
def create_precommit_project():
    '''
    Create project tailored to precommit tests, i.e. mostly just required files
    '''
    write_project(project1)
    write_file('requirements.in', requirements_in1)
    write_file('LICENSE.txt', license_txt1)
    write_file('README.md', readme1)
    Path('operation_mittens').mkdir()
    Path('operation_mittens/test').mkdir()
    write_file('operation_mittens/test/test_one.py', test_one1)
    git_('init')
    
    
## tests ############################################


def test_project_missing(tmpcwd):
    '''
    When project.py missing, ask for a name and generate template
    '''
    # When project.py is missing and git repo exists but has no commits
    create_project()
    remove_file(Path('project.py'))
    (mkproject << project_defaults['name'] + '\n')()
    
    # Then project.py is created and contains the defaults we want
    project_py_path = Path('project.py')
    assert project_py_path.exists()
    project = eval_file(project_py_path)['project']
    assert project == project_defaults
        
def test_project_present(tmpcwd):
    '''
    When project.py exists, it is left alone.
    
    When project lacks optional attributes, succeed.
    '''
    create_project()
    with assert_file_access('project.py', contents_changed=False):
        mkproject & pb.FG
        
def test_project_undefined(tmpcwd):
    '''
    When project.py does not define `project`, abort
    '''
    create_project()
    write_file('project.py', '')
    with assert_process_fails(stderr_matches='must export a `project` variable'):
        mkproject()
        
@pytest.mark.parametrize('required_attr', project1.keys())
def test_project_missing_required_attr(tmpcwd, required_attr):
    '''
    When `project` lacks a required attribute, abort
    '''
    create_project()
    project = project1.copy()
    del project[required_attr]
    write_project(project)
    with assert_process_fails(stderr_matches='Missing.+{}'.format(required_attr)):
        mkproject()
        
@pytest.mark.parametrize('unknown_attr', 'version package_data packages long_description extras_require install_requires unknown'.split())
def test_project_has_unknown_attr(tmpcwd, unknown_attr):
    '''
    When `project` contains an unknown attribute, abort
    '''
    create_project()
    project = project1.copy()
    project[unknown_attr] = 'value'
    write_project(project)
    with assert_process_fails(stderr_matches=unknown_attr):
        mkproject()
        
_parameters = set(itertools.product(project1.keys(), ('', None, ' ', '\t'))) # most attributes may not be empty or None
_parameters.add(('name', 'white space'))
_parameters.add(('name', 'dashed-name'))

@pytest.mark.parametrize('attr,value', _parameters)
def test_project_attr_has_invalid_value(tmpcwd, attr, value):
    '''
    When '\s*' or None as attr values, abort
    
    When dashes or whitespace in name, abort
    '''
    create_project()
    project = project1.copy()
    project[attr] = value
    write_project(project)
    with assert_process_fails(stderr_matches=attr):
        mkproject()
    
def test_idempotent(tmpcwd):
    '''
    Running mkproject twice is the same as running it once, in any case
    '''
    create_project()
    mkproject()
    with assert_directory_contents(Path('.'), changed=False):
        mkproject()

@pytest.mark.parametrize('missing', files_create_project)
def test_missing_files(tmpcwd, missing):
    '''
    When files are missing, create them if allowed, error otherwise

    While files are present and may not be updated, they are left untouched
    '''
    create_project()
    missing_is_dir = missing.is_dir()
    remove_file(missing)
    if not missing_is_dir and file_permissions[missing] == 'none':
        # When can't create, must raise error
        with assert_process_fails(stderr_matches=missing.name):
            mkproject()
    else:
        # When can create, create
        with ExitStack() as contexts:
            for file, permission in file_permissions.items():
                if missing != file and missing not in file.parents and permission not in ('update', 'overwrite'):
                    contexts.enter_context(assert_file_access(file, written=False, contents_changed=False))
            mkproject()
        assert missing.exists()
    # TODO deploy_local is not created, and just py.test until the rest works
    
@pytest.mark.parametrize('name', ('readme.md', 'README.MD', 'REEEADMEE.md'))
def test_wrong_readme_file_name(tmpcwd, name):
    '''
    When files are missing, create them if allowed, error otherwise

    While files are present and may not be updated, they are left untouched
    '''
    create_project()
    project = project1.copy()
    project['readme_file'] = name
    write_project(project)
    Path(name).touch()
    
    with assert_process_fails(stderr_matches='readme_file'):
        mkproject()
    
def test_updates(tmpcwd):
    '''
    When updating a file but not allowed to overwrite, leave the rest of it intact.
    
    - $project_name/__init__.py: leaves all intact, just inserts/overwrites __version__
    - .gitignore: leaves previous patterns intact, does insert the new patterns
    - setup.cfg: leaves previous intact, except for some lines designated to be overwritten
    '''
    create_project() # Note this template is such that each of the files will require an update
    updated_files = ('operation_mittens/__init__.py', '.gitignore', 'setup.cfg')
    with assert_file_access(*updated_files, written=True, contents_changed=True):
        mkproject()
    
    content = read_file('operation_mittens/__init__.py')
    assert pkg_init1 in content
    assert '__version__ =' in content
    
    content = read_file('.gitignore')
    assert gitignore1 in content
    assert '*.egg-info' in content  # check 1 of the patterns is in there, though they should all be in there
    
    config = ConfigParser()
    config.read('setup.cfg')
    assert config['pytest']['addopts'].strip() == '--basetemp=last_test_runs --maxfail=2'  # unchanged
    assert config['pytest']['testpaths'] == 'operation_mittens/test'  # overwritten
    assert config['metadata']['description-file'] == 'README.md'  # overwritten
    assert config['other']['mittens_says'] == 'meow'  # unchanged

def test_setup_py(tmpcwd):
    '''
    - install_requires: requirements.in transformed into valid dependency list with version specs maintained
    - long_description present and nonempty
    - classifiers: list of str
    - packages: list of str of packages
    - package_data: dict of package -> list of str of data file paths
    - author, author_email, description, entry_points keywords license name, url: exact same as input
    '''
    create_project()
    project = project1.copy()
    project['entry_points'] = project_defaults['entry_points']
    write_project(project)
    write_complex_requirements_in()
    
    # Create package_data in operation_mittens/test (it actually may be in non-test as well):
    Path('operation_mittens/test/data').mkdir()
    Path('operation_mittens/test/data/subdir').mkdir()
    Path('operation_mittens/test/data/subdir/file1').touch()
    Path('operation_mittens/test/data/subdir/file2').touch()
    Path('operation_mittens/test/not_data').mkdir()
    Path('operation_mittens/test/not_data/file').touch()
    Path('operation_mittens/test/not_data/data').mkdir()
    Path('operation_mittens/test/not_data/data/file').touch()
    Path('operation_mittens/test/pkg').mkdir()
    Path('operation_mittens/test/pkg/__init__.py').touch()
    Path('operation_mittens/test/pkg/data').mkdir()
    Path('operation_mittens/test/pkg/data/file').touch()
    
    # Run
    mkproject()
    
    # Assert all the things
    setup_args = get_setup_args()
    
    for attr in ('name', 'author', 'author_email', 'description', 'keywords', 'license', 'url'):
        assert setup_args[attr] == project[attr].strip()
    assert setup_args['entry_points'] == project['entry_points']
        
    assert setup_args['long_description'].strip()
    assert set(setup_args['classifiers']) == {'Development Status :: 2 - Pre-Alpha', 'Programming Language :: Python :: Implementation :: Stackless'}
    assert setup_args['packages'] == ['operation_mittens', 'operation_mittens.test', 'operation_mittens.test.pkg']
    assert {k:set(v) for k,v in setup_args['package_data'].items()} == {
        'operation_mittens.test' : {'operation_mittens/test/data/subdir/file1', 'operation_mittens/test/data/subdir/file2'},
        'operation_mittens.test.pkg' : {'operation_mittens/test/pkg/data/file'},
    }
    assert set(setup_args['install_requires']) == {'pytest', 'pytest-xdist<5.0.0', 'pytest-env==0.6', 'pkg4', 'pytest-cov'}
    assert setup_args['version'] == '0.0.0'
    assert 'download_url' not in setup_args
    
def test_precommit_invalid(tmpcwd):
    '''
    Invalid project cancels the commit
    '''
    create_precommit_project()
    mkproject()  # install pre-commit hook
    remove_file(Path('README.md'))
    git_('add', '.')
    with assert_process_fails(stderr_matches='(?i)error'):
        git_('commit', '-m', 'message')  # runs the hook
     
def test_precommit_include_changes(tmpcwd):
    '''
    Changes made by mkproject must be staged, especially during precommit
    '''
    create_precommit_project()
    mkproject()  # install pre-commit hook
    write_file('requirements.in', 'pytest')
    git_('add', '.')
    git_('commit', '-m', 'message')  # runs the hook, which calls ct-mkproject, which changes setup.py in this case
    
    # Expected change happened
    assert get_setup_args()['install_requires'] == ['pytest']
    
    # And all has been committed
    repo = git.Repo('.')
    assert not repo.is_dirty(untracked_files=True)
            
'''
TODO

When source file lacks copyright header or header is incorrect, error (and point to all wrong files)

Ensure the readme_file is mentioned in MANIFEST.in 
'''
    