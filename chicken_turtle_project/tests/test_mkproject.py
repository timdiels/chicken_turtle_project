'''
ct-mkproject tests
'''

from chicken_turtle_project.tests.common import (
    create_project, mkproject, project_defaults, write_file, git_, project1,
    assert_directory_contents, assert_process_fails, assert_file_access,
    read_file, get_setup_args, extra_files, add_complex_requirements_in
)
from contextlib import ExitStack
from chicken_turtle_project.common import eval_file, parse_requirements_file, get_dependency_name, remove_file
from chicken_turtle_project import specification as spec
from pathlib import Path
from configparser import ConfigParser
from enum import IntEnum
from textwrap import dedent
import plumbum as pb
import itertools
import pytest
import re

## Project file requirements ############################################
Permission = IntEnum('Permission', 'none create update overwrite')

class ProjectFileRequirement(object):
    '''
    Interface
    
    Attributes
    ----------
    permission : Permission
        Max permission. I.e. lower permissions are included.
    
    Methods
    -------
    verify_default_content(file_content :: str, format_variables :: {str : any}) -> None
        raises if the file content after being created from scratch or overwritten
        is invalid. Only called if has 'create' permission.
    verify_updated_content(updated_content :: str, original_content :: str, format_variables :: {str : any}) -> None
        raises if the file content after being updated is invalid, e.g. if original
        content is dropped entirely. Only called if has 'update' permission.
        
    Notes
    -----
    No need to inherit from this due to duck typing.
    '''

class _IniFileRequirement(object):
    
    '''
    Require ini-like file to provide defaults and/or fix options at certain values
    '''
    
    permission = Permission.update
    
    def __init__(self, defaults, overwrite):
        self._defaults = defaults
        self._overwritten = overwrite
    
    def _config(self, content):
        config = ConfigParser()
        config.read_string(content)
        return config
    
    def verify_default_content(self, content, format_kwargs):
        config = self._config(content)
        
        # defaults are included and have correct value
        for section in self._defaults:
            for option, value in self._defaults[section].items():
                assert config.has_option(section, option)
                assert config[section][option] == value.format(**format_kwargs)
        
        self._verify(content, format_kwargs)
        
    def verify_updated_content(self, updated_content, original_content, format_kwargs):
        updated_config = self._config(updated_content)
        original_config = self._config(original_content)
        
        # add missing required options
        for section in self._defaults:
            for option, value in self._defaults[section].items():
                if not original_config.has_option(section, option):
                    assert updated_config.has_option(section, option) 
                    assert updated_config[section][option] == value.format(**format_kwargs)
        
        # carry over everything else from the original
        for section in original_config:
            for option in original_config[section]:
                # allow overwrite in some
                if section in self._overwritten and option in self._overwritten[section]:
                    continue
                
                # but not these
                assert updated_config.has_option(section, option)
                assert updated_config[section][option] == original_config[section][option]
        
        self._verify(updated_content, format_kwargs)
        
    def _verify(self, content, format_kwargs):
        config = self._config(content)
        
        # options to overwrite if their value differs from what it should be
        for section in self._overwritten:
            for option, value in self._overwritten[section].items():
                assert config.has_option(section, option)
                assert config[section][option] == value.format(**format_kwargs)
                
class _SnippetsRequirement(object):
    
    '''
    Require file to contain given snippets, in any order, allowing overlap
    '''
    
    def __init__(self, permission, snippets, format_snippets=True):
        self.permission = permission
        self._snippets = snippets
        self._format = format_snippets
    
    def verify_default_content(self, content, format_kwargs):
        self._verify(content, format_kwargs)
        
    def verify_updated_content(self, updated_content, original_content, format_kwargs):
        assert self.permission >= Permission.update
        assert original_content in updated_content
        self._verify(updated_content, format_kwargs)
    
    def _verify(self, content, format_kwargs):
        if self._format:
            snippets = (snippet.format(**format_kwargs) for snippet in self._snippets)
        else:
            snippets = self._snippets
        for snippet in snippets:
            assert snippet in content
            
class _NoRequirement(object):
    
    '''
    Don't impose any additional requirements
    '''
    
    def __init__(self, permission = Permission.none):
        self.permission = permission
        
    def verify_default_content(self, content, format_variables):
        pass
        
    def verify_updated_content(self, updated_content, original_content, format_variables):
        pass

#: Requirements of project files.
#: 
#: Each file should exist after a successful run of ct-mkproject. Not all have to
#: be created by the user.
project_file_requirements = {
    Path('operation/mittens/__init__.py') : _SnippetsRequirement(Permission.update, {spec.version_line}),
    Path('operation/mittens/tests/__init__.py') : _NoRequirement(Permission.create),
    Path('operation/mittens/tests/conftest.py') : _SnippetsRequirement(Permission.update, {spec.conftest_py}),
    Path('docs/conf.py') : _SnippetsRequirement(Permission.create, {spec.docs_conf_py}),
    Path('docs/Makefile') : _SnippetsRequirement(Permission.create, {spec.docs_makefile}, format_snippets=False),
    Path('docs/index.rst') : _SnippetsRequirement(Permission.create, {spec.docs_index_rst}),
    Path('requirements.in') : _SnippetsRequirement(Permission.update, {spec.requirements_in_header}),
    Path('dev_requirements.in') : _SnippetsRequirement(Permission.update, spec.dev_requirements_in),
    Path('test_requirements.in') : _SnippetsRequirement(Permission.update, spec.test_requirements_in),
    Path('requirements.txt') : _NoRequirement(Permission.overwrite), # tested elsewhere
    Path('.gitignore') : _SnippetsRequirement(Permission.update, spec.gitignore_patterns),
    Path('.coveragerc') : _IniFileRequirement(spec.coveragerc_defaults, spec.coveragerc_overwrite),
    Path('setup.cfg') : _IniFileRequirement(spec.setup_cfg_defaults, spec.setup_cfg_overwrite),
    Path('setup.py') : _SnippetsRequirement(Permission.overwrite, {spec.setup_py_header}),
    Path('MANIFEST.in') : _SnippetsRequirement(Permission.update, spec.manifest_in),
    Path('LICENSE.txt') : _NoRequirement(),
    Path('README.md') : _NoRequirement(),
    # project.py is tested elsewhere as it requires stdin to be created
}

## setup, asserts, util #######################################

def add_docstring(project, docstring):
    for path in (Path('docs/index.rst'), Path('docs/conf.py'), Path('docs/Makefile')):
        del project.files[path]
    project.files[Path('operation/mittens/meow.py')] = dedent('''\
        def meow_meow():
            '{}'
        '''.format(docstring)
    )

def is_subsequence(left, right): #TODO to CTU
    '''
    Get whether left is a subsequence of right, in the mathematical sense
    
    Subsequence definition: https://en.wikipedia.org/wiki/Subsequence
    '''
    right = right[:]
    for i in reversed(range(len(right))):
        if right[i] not in left:
            del right[i]
    return left == right 
    
## tests ############################################

class TestFileRequirements(object):
    
    '''Drive tests specified by `project_file_requirements`'''
    
    @pytest.mark.parametrize('missing_path, missing_requirements', project_file_requirements.items())
    def test_missing_file(self, tmpcwd, missing_path, missing_requirements):
        '''
        Test handling of missing files:
        
        - When files are missing, create them if allowed, error otherwise
        - When files are present and may not be updated, they are left untouched
        '''
        create_project()
        remove_file(missing_path)
        if missing_requirements.permission == Permission.none:
            # When can't create, must raise error
            with assert_process_fails(stderr_matches=missing_path.name):
                mkproject()
        else:
            # When can create, create
            with ExitStack() as contexts:
                for file, requirements in project_file_requirements.items():
                    if missing_path != file and missing_path not in file.parents and requirements.permission <= Permission.create:
                        contexts.enter_context(assert_file_access(file, written=False, contents_changed=False))
                mkproject & pb.FG
            assert missing_path.exists()
            content = read_file(missing_path)
            missing_requirements.verify_default_content(content, project1.format_kwargs)
        
    def test_update_file(self, tmpcwd):
        '''
        Test updates to files:
        
        - file is updated to match requirements
        - file also still contains original contents
        
        Specifically:
        
        - $project_name/__init__.py: leaves all intact, just inserts/overwrites __version__
        - .gitignore: leaves previous patterns intact, does insert the new patterns
        - setup.cfg: leaves previous intact, except for some lines designated to be overwritten
        - ...
        '''
        create_project(project1) # Note this template is such that each of the files will require an update
        updated_files = [path for path, requirements in project_file_requirements.items() if requirements.permission == Permission.update]
        with assert_file_access(*updated_files, written=True, contents_changed=True):
            mkproject & pb.FG
        
        for path in updated_files:
            requirements = project_file_requirements[path]
            content = read_file(path)
            requirements.verify_updated_content(content, project1.files[path], project1.format_kwargs)
            
    def test_overwrite_file(self, tmpcwd):
        '''
        Test file overwrites
        '''
        create_project(project1) # Note this template is such that each of the files that be overwritten will require an overwrite
        overwritten_files = [path for path, requirements in project_file_requirements.items() if requirements.permission == Permission.overwrite]
        with assert_file_access(*overwritten_files, written=True, contents_changed=True):
            mkproject & pb.FG
        
        for path in overwritten_files:
            requirements = project_file_requirements[path]
            content = read_file(path)
            requirements.verify_default_content(content, project1.format_kwargs)
    
class TestProjectPy(object):
    
    'Test project.py content (some of it is already covered by TestFileRequirements)'
    
    def test_new(self, tmpcwd):
        '''
        When project.py missing, ask for a name and generate template
        '''
        # When project.py is missing and git repo exists but has no commits
        create_project()
        remove_file(Path('project.py'))
        (mkproject << '{name}\n{pkg_name}\n{human_friendly_name}\n'.format(**project1.format_kwargs))()
        
        # Then project.py is created and contains the defaults we want
        project_py_path = Path('project.py')
        assert project_py_path.exists()
        assert read_file(project_py_path) == spec.project_py.format(**project1.format_kwargs)
        assert eval_file(project_py_path)['project'] == project_defaults  # double-check
            
    def test_undefined(self, tmpcwd):
        '''
        When project.py does not define `project`, abort
        '''
        create_project()
        write_file('project.py', '')
        with assert_process_fails(stderr_matches='must export a `project` variable'):
            mkproject()
            
    @pytest.mark.parametrize('required_attr', project1.project_py.keys())
    def test_missing_required_attr(self, tmpcwd, required_attr):
        '''
        When `project` lacks a required attribute, abort
        '''
        project = project1.copy()
        del project.project_py[required_attr]
        create_project(project)
        with assert_process_fails(stderr_matches='Missing.+{}'.format(required_attr)):
            mkproject()
            
    @pytest.mark.parametrize('unknown_attr', 'version package_data packages long_description extras_require install_requires unknown'.split())
    def test_has_unknown_attr(self, tmpcwd, unknown_attr):
        '''
        When `project` contains an unknown attribute, abort
        '''
        project = project1.copy()
        project.project_py[unknown_attr] = 'value'
        create_project(project)
        with assert_process_fails(stderr_matches=unknown_attr):
            mkproject()
            
    _parameters = set(itertools.product(project1.project_py.keys(), ('', None, ' ', '\t'))) # most attributes may not be empty or None
    _parameters.add(('name', 'white space'))
    _parameters.add(('pre_commit_no_ignore', ('sneaky/../../*',)))  # must stay below project_root
    _parameters.add(('pre_commit_no_ignore', ('/not/so/sneaky',)))  # must be relative path, even if the abs happens to point to project_root or lower
    
    @pytest.mark.parametrize('attr,value', _parameters)
    def test_attr_has_invalid_value(self, tmpcwd, attr, value):
        '''
        When '\s*' or None as attr values, abort
        
        When dashes or whitespace in name, abort
        '''
        project = project1.copy()
        project.project_py[attr] = value
        create_project(project)
        with assert_process_fails(stderr_matches=attr):
            mkproject()

class TestSetupPyAndRequirementsTxt(object):

    def test_setup_py(self, tmpcwd):
        '''
        Test generated setup.py and requirements.txt
        
        - install_requires: requirements.in transformed into valid dependency list with version specs maintained
        - long_description present and nonempty
        - classifiers: list of str
        - packages: list of str of packages
        - package_data: dict of package -> list of str of data file paths
        - author, author_email, description, entry_points keywords license name, url: exact same as input
        '''
        project = project1.copy()
        project.project_py['entry_points'] = project_defaults['entry_points']
        add_complex_requirements_in(project)
        project.files[Path('my_extra_requirements.in')] = 'checksumdir\npytest-pep8\n'
        del project.files[Path('test_requirements.in')]
        
        # Create package_data in operation/mittens/tests (it actually may be in non-test as well):
        project.files[Path('operation/mittens/tests/data/subdir/file1')] = ''
        project.files[Path('operation/mittens/tests/data/subdir/file2')] = ''
        project.files[Path('operation/mittens/tests/not_data/file')] = ''
        project.files[Path('operation/mittens/tests/not_data/data/file')] = ''
        project.files[Path('operation/mittens/tests/pkg/__init__.py')] = ''
        project.files[Path('operation/mittens/tests/pkg/data/file')] = ''
        
        #
        create_project(project)
        
        # Run
        mkproject & pb.FG
        
        # Assert setup.py args
        setup_args = get_setup_args()
        
        for attr in ('name', 'author', 'author_email', 'description', 'keywords', 'license', 'url'):
            assert setup_args[attr] == project.project_py[attr].strip()
        assert setup_args['entry_points'] == project.project_py['entry_points']
            
        assert setup_args['long_description'].strip()
        assert set(setup_args['classifiers']) == {'Development Status :: 2 - Pre-Alpha', 'Programming Language :: Python :: Implementation :: Stackless'}
        assert set(setup_args['packages']) == {'operation', 'operation.mittens', 'operation.mittens.tests', 'operation.mittens.tests.pkg'}
        assert {k:set(v) for k,v in setup_args['package_data'].items()} == {
            'operation.mittens.tests' : {'data/subdir/file1', 'data/subdir/file2'},
            'operation.mittens.tests.pkg' : {'data/file'},
        }
        assert set(setup_args['install_requires']) == {'pytest', 'pytest-testmon<5.0.0', 'pytest-env==0.6', 'pkg4', 'pytest-cov'}
        assert set(setup_args['extras_require'].keys()) == {'my_extra', 'test', 'dev'}
        assert set(setup_args['extras_require']['my_extra']) == {'checksumdir', 'pytest-pep8'}
        assert set(setup_args['extras_require']['test']) == set(spec.test_requirements_in)
        assert setup_args['version'] == '0.0.0'
        assert 'download_url' not in setup_args
        
        # requirements.txt must contain relevant packages, including optional dependencies
        requirements_txt_content = read_file('requirements.txt')
        for name in {'pytest', 'pytest-testmon', 'pytest-env', 'pkg_magic', 'pytest-cov', 'checksumdir', 'pytest-pep8'} | set(spec.test_requirements_in) | set(spec.dev_requirements_in):
            assert name in requirements_txt_content
             
        # Ordering of *requirements.in files must be maintained per file (file order may be ignored)
        deps_txt = [get_dependency_name(line[0], line[1]) for line in parse_requirements_file(Path('requirements.txt')) if line[1]]
        for path in map(Path, ('requirements.in', 'my_extra_requirements.in', 'test_requirements.in')):
            deps_in = [get_dependency_name(line[0], line[1]) for line in parse_requirements_file(path) if line[1]]
            assert is_subsequence(deps_in, deps_txt)
            
    def test_sip_dependency(self, tmpcwd):
        '''
        When sip based dependency, do not put it in setup.py or requirements.txt
        '''
        project = project1.copy()
        project.files[Path('requirements.in')] = 'pytest\nsip==4.17\nPyQt5==5.5.1\n'
        create_project(project)
        
        mkproject & pb.FG
        
        setup_args = get_setup_args()
        assert setup_args['install_requires'] == ['pytest']
        
        requirements_txt = read_file('requirements.txt')
        assert 'sip' not in requirements_txt
        assert not re.match('(?i)pyqt5', requirements_txt)
        
    def test_unpinned_sip_dependency(self, tmpcwd):
        '''
        When sip based dependency is not pinned, error
        '''
        project = project1.copy()
        project.files[Path('requirements.in')] = 'pytest\nPyQt5\n'
        create_project(project)
        
        with assert_process_fails(stderr_matches=r"(?i)'PyQt5' .* pin"):
            mkproject()
    
class TestPrecommit(object): #XXX mv to separate file, it tests the pre-commit hook -> test_pre_commit_hook
    
    @property
    def project(self):
        project = project1.copy()
        test_succeed_path = Path('operation/mittens/tests/test_succeed.py')
        project.files = {
            Path('requirements.in'): project.files[Path('requirements.in')],  
            Path('LICENSE.txt'): project.files[Path('LICENSE.txt')],
            Path('README.md'): project.files[Path('README.md')],
            test_succeed_path: extra_files[test_succeed_path],
        }
        return project
        
    def create_project(self):
        create_project(self.project)
    
    def test_invalid_project(self, tmpcwd):
        '''
        Invalid project cancels the commit
        '''
        self.create_project()
        mkproject & pb.FG  # install pre-commit hook
        remove_file(Path('README.md'))
        git_('add', '.')
        with assert_process_fails(stderr_matches='(?i)error'):
            git_('commit', '-m', 'message')  # runs the hook
        
    def test_ignore_unstaged(self, tmpcwd):
        '''
        Pre-commit must ignore unstaged changes
        '''
        self.create_project()
        git_('add', '.')
        mkproject & pb.FG  # install pre-commit hook
        remove_file(Path('README.md'))
        git_('commit', '-m', 'message')  # This fails if unstaged change is included
        
    def test_ignore_untracked(self, tmpcwd):
        '''
        Pre-commit must ignore untracked changes
        '''
        self.create_project()
        git_('add', '.')
        mkproject & pb.FG  # install pre-commit hook
        test_fail_path = Path('operation/mittens/tests/test_fail.py')
        write_file(test_fail_path, extra_files[test_fail_path])
        git_('commit', '-m', 'message')  # This fails if the untracked test is included
         
    def test_include_changes(self, tmpcwd):
        '''
        Changes made by mkproject must be staged, especially during precommit
        '''
        self.create_project()
        mkproject & pb.FG  # install pre-commit hook
        write_file('requirements.in', 'pytest')
        git_('add', '.')
        git_('commit', '-m', 'message')  # runs the hook, which calls ct-mkproject, which changes setup.py in this case
        
        # Expected change happened and is part of the commit
        git_('reset', '--hard')
        assert get_setup_args()['install_requires'] == ['pytest']
            
    def test_no_ignore(self, tmpcwd):
        '''
        When well-behaved pre_commit_no_ignore, copy matched files to pre-commit
        tmp dir
        '''
        project = self.project
        project.project_py['pre_commit_no_ignore'] = ['operation/mittens/test/mah_*']
        project.files[Path('operation/mittens/test/mah_file')] = 'content'
        project.files[Path('operation/mittens/test/mah_dir/some_file')] = 'some file content'
        project.files[Path('operation/mittens/test/test_it.py')] = dedent('''\
            from pathlib import Path
            def test_it():
                # file is there
                dir = Path(__file__).parent
                with (dir / 'mah_file').open('r') as f:
                    assert f.read() == 'content'
                    
                # recursively copied directory is there
                with (dir / 'mah_dir/some_file').open('r') as f:
                    assert f.read() == 'some file content'
            ''')
        create_project(project)
        mkproject() # install pre commit hook
        git_('add', '.')
        git_('reset', 'operation/mittens/test/mah_file')
        git_('reset', 'operation/mittens/test/mah_dir')
        git_('commit', '-m', 'message') # run pre-commit
            
    def test_invalid_documentation(self, tmpcwd):
        '''When a docstring contains an error, mkdoc exits non-zero and pre-commit aborts'''
        project = project1.copy()
        add_docstring(project, '.. derpistan:: nope')
        create_project(project)
        mkproject()
        git_('add', '.')
        
        with assert_process_fails(stderr_matches='derpistan'):
            git_('commit', '-m', 'message')  # runs the hook
        
def test_idempotent(tmpcwd):
    '''
    Running ct-mkproject twice is the same as running it once, in any case
    '''
    create_project()
    mkproject & pb.FG
    with assert_directory_contents(Path('.'), changed=False):
        mkproject()

@pytest.mark.parametrize('name', ('readme.md', 'README.MD', 'REEEADMEE.md'))
def test_wrong_readme_file_name(tmpcwd, name):
    project = project1.copy()
    project.project_py['readme_file'] = name
    create_project(project)
    Path(name).touch()
    
    with assert_process_fails(stderr_matches='readme_file'):
        mkproject()
        
def test_mkdoc(tmpcwd):
    '''When happy days and a file with proper docstring, generate ./doc'''
    # Setup
    project = project1.copy()
    description = 'Meow meow n meow meow meow'
    add_docstring(project, description)
    create_project(project)
    
    # Run
    mkproject()
    pb.local['ct-mkdoc']()
    
    # Assert
    content = read_file('docs/build/html/index.html')
    assert '0.0.0' in content  # correct version
    assert project.project_py['human_friendly_name'] in content  # human friendly project name
    assert 'operation package' in content
    
    content = read_file('docs/build/html/api/operation.mittens.html')
    assert description in content  # the docstring of the project

'''
TODO

use https://pypi.python.org/pypi/pytest-devpi-server/ to speed up testing and allow better coverage of ct-release which can then release to a temp devpi. Be sure to scope it as wide as the whole test session perhaps (but don't want previous versions to get in the way. I guess it depends, for test_mkproject you want it module wide, for test_release you want it per test
http://doc.devpi.net/latest/quickstart-pypimirror.html

fix: after each commit, package is left uninstalled in the venv. Perhaps only when it has had test failures

When source file lacks copyright header or header is incorrect, error (and point to all wrong files)
'''
