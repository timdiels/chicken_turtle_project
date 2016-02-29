from chicken_turtle_project.common import configure_logging, get_project
from chicken_turtle_util.exceptions import UserException, log_exception
from pathlib import Path
import sys
import logging
import click
from glob import glob

logger = logging.getLogger(__name__)
    
def main(): #TODO click to show help message and version; also on mksetup and other tools. Also include the output from -h in the readme automatically, i.e. compile the readme (or maybe reST can? or maybe we should use Sphinx instead?).
    '''
    Create or update existing project to match the latest Chicken Turtle project structure.
    
    ct-mkproject must be run from the root of the project. 
    
    The following files are created if missing:
    - project.py
    - $project_name package
    - $project_name/version.py
    - $project_name/test package
    - requirements.in
    - .gitignore
    - setup.cfg
    
    ct-mkproject ensures certain patterns are part of .gitignore, but does not erase any patterns you added.
    
    Warnings are emitted if these files are missing:
    - LICENSE.txt
    - README.*
    
    py.test will be configured to run test in $project_name.test and subpackages
    '''
    try:
        project_root = Path.cwd()
        configure_logging()
        
        # Create project if missing
        project_path = project_root / 'project.py'
        if not project_path.exists():
            logger.info('project.py not found, will create from template')
            project_name = click.prompt('Please pick a name for your project')
            assert project_name and project_name.strip()
            with project_path.open('w') as f:
                f.write(project_template.format(project_name))
        
        # Load project info
        project = get_project()
        project_name = project['name']
        pkg_root = project_root / project_name
        
        # Create package dir if missing
        if not pkg_root.exists():
            pkg_root.mkdir()
        
        # Ensure package root __init__.py exists
        pkg_root_init = pkg_root / '__init__.py'
        if not pkg_root_init.exists():
            pkg_root_init.touch()
        
        # Ensure package root __init__.py imports __version__    
        import_line = 'from {}.version import __version__'.format(project_name)
        with pkg_root_init.open('r') as f:
            contents = f.read()
        if import_line not in map(str.strip, contents.splitlines()): 
            with pkg_root_init.open('w') as f:
                f.write(import_line + "\n" + contents)
            
        # Create version.py if missing    
        version_path = pkg_root / 'version.py'
        if not version_path.exists():
            with version_path.open('w') as f:
                f.write(version_template)
        
        # Create test package if missing
        test_root = pkg_root / 'test'
        if not test_root.exists():
            test_root.mkdir()
        
        test_root_init = test_root / '__init__.py'
        if not test_root_init.exists():
            test_root_init.touch()
            
        # Create requirements.in if missing
        requirements_in_path = project_root / 'requirements.in'
        if not requirements_in_path.exists():
            requirements_in_path.touch()
            
        # Create setup.cfg if missing
        setup_cfg_path = project_root / 'setup.cfg'
        if not setup_cfg_path.exists():
            with setup_cfg_path.open('w') as f:
                f.write(setup_cfg_template)
            
        # Create .gitignore if missing
        gitignore_path = project_root / '.gitignore'
        if not gitignore_path.exists():
            gitignore_path.touch()
        
        # Ensure the right patterns are present in .gitignore
        with gitignore_path.open('r') as f:
            content = f.read()
        patterns = set(map(str.strip, content.readlines()))
        missing_patterns = gitignore_patterns - patterns
        if missing_patterns:
            with gitignore_path.open('r') as f:
                f.write('\n'.join(*missing_patterns, content))
        
        # Emit warnings for missing files
        for file in 'LICENSE.txt README.*':
            if not glob(file):
                logger.warning("Missing file: {}".format(file))
        
        #TODO need be able to enter interpreter for current setup.py derived venv, preferably also first load interpreter.py     
        
    except UserException as ex:
        logger.error(ex.message)
        sys.exit(1)
    except Exception as ex:
        log_exception(logger, ex)
        sys.exit(2)
        
project_template = """
project = dict(
    name='{}',
    description='Short description',
    author='your name',
    author_email='your_email@example.com',
    readme_file='README.md',
    url='https://example.com/project/home', # project homepage
    license='LGPL3',
 
    # What does your project relate to?
    keywords='keyword1 key-word2',
    
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    # Note: you must add ancestors of any applicable classifier too
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
 
    # Required dependencies
    setup_requires='pypandoc'.split(), # required to run setup.py. I'm not aware of any setup tool that uses this though
    install_requires=(
        'pypi-dep-1 pypydep2 '
        'moredeps '
    ),
 
    # Optional dependencies
    extras_require={
        'dev': '',
        'test': 'pytest pytest-benchmark pytest-timeout pytest-xdist freezegun',
    },
 
    # Auto generate entry points
    entry_points={
        'console_scripts': [
            'mycli = project_name.main:main', # just an example, any module will do, this template doesn't care where you put it
        ],
    },
)
"""

version_template = """
# Versions should comply with PEP440.
# https://www.python.org/dev/peps/pep-0440/
# https://python-packaging-user-guide.readthedocs.org/en/latest/distributing/#semantic-versioning-preferred
__version__ = '1.0.0.dev1'
"""

setup_cfg_template = """
[pytest]
addopts = --basetemp=last_test_runs
testpaths={}/test
"""

gitignore_patterns = r'''
*.orig
*.swp
.project
.pydevproject
.cproject
test/last_runs
venv
*.pyc
__pycache__
*.egg-info
'''
gitignore_patterns = {line for line in map(str.strip, gitignore_patterns.splitlines()) if line}
