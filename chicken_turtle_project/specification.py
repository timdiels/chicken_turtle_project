# Copyright (C) 2016 Tim Diels <timdiels.m@gmail.com>
# 
# This file is part of Chicken Turtle Project.
# 
# Chicken Turtle is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Chicken Turtle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Chicken Turtle.  If not, see <http://www.gnu.org/licenses/>.

'''
Specifies CTP requirements data used by both test and implementation code

Be warned, incorrect changes here will likely go undetected.
'''

from textwrap import dedent
from pkg_resources import resource_string

#: setup.py must begin with this header
setup_py_header = '''\
# Auto generated by ct-mksetup
# Do not edit this file, edit ./project.py instead
'''
        
#: Newly created project.py must match this template
project_py= """
project = dict(
    # Changing these attributes is not supported (you'll have to manually move and edit files)
    name='{name}',  # PyPI (or other index) name.
    package_name='{pkg_name}',  # name of the root package of this project, e.g. 'myproject' or 'myproject.subproject' 
    human_friendly_name='{human_friendly_name}',
    
    #
    description='Short description',
    author='your name',  # will appear in copyright mentioned in documentation: 'year, your name'
    author_email='your_email@example.com',
    python_version=(3,5),  # python (major, minor) version to use to create the venv and to test with. E.g. (3,5) for python 3.5.x. Only being able to pick a single version is a current shortcoming of Chicken Turtle Project.
    readme_file='README.md',
    url='https://example.com/project/home', # project homepage
    download_url='https://example.com/project/downloads', # project downloads page, optional
    license='LGPL3',
 
    # What does your project relate to?
    keywords='keyword1 key-word2',
    
    # Package indices to release to using `ct-release`
    # These names refer to those defined in ~/.pypirc.
    # For pypi, see http://peterdowns.com/posts/first-time-with-pypi.html
    # For devpi, see http://doc.devpi.net/latest/userman/devpi_misc.html#using-plain-setup-py-for-uploading
    index_test = 'pypitest',  # Index to use for testing a release, before releasing to `index_production`. `index_test` can be omitted if you have no test index
    index_production = 'pypi',
    
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
 
    # Auto generate entry points (optional)
    entry_points={{
        'console_scripts': [
            'mycli = {pkg_name}.main:main', # just an example, any module will do, this template doesn't care where you put it
        ],
    }},
    
    # pre_commit_no_ignore (optional):
    #
    # Files not to ignore in pre commit checks, despite them not being tracked by
    # git.
    #
    # Before a commit, project files are updated (ct-mkproject), the venv is
    # updated (ct-mkvenv), tests are run and documentation generation is checked
    # for errors. This process (intentionally) ignores any untracked files.
    # In order to include files needed by this process that you do not wish to
    # have tracked (e.g. files with passwords such as some test configurations),
    # you must add them to `pre_commit_no_ignore`.
    #
    # List of glob patterns relative to this file. You may not refer to files
    # outside the project directory (i.e. no higher than project.py).
    #
    # For supported glob syntax, see Python `glob.glob(recursive=False)`. Note
    # there is no need for ``**`` as no- ignores are recursive.
    pre_commit_no_ignore = [
        'test.conf',
        'secrets/*',
    ]
)
"""

#: Version line in $project/__init__.py must match this format
version_line = "__version__ = '{version}'  # Auto generated by ct-mksetup, do not edit this line. Project version is only set nonzero on release, using `ct-release`."

#: .gitignore must contain these patterns
gitignore_patterns = r'''
*.orig
*.swp
.project
.pydevproject
.cproject
.coverage
.testmondata
.tmontmp
.settings
*.pyc
__pycache__
*.egg-info
.cache
venv
last_test_runs
dist
build
docs/build
'''
gitignore_patterns = {line for line in map(str.strip, gitignore_patterns.splitlines()) if line}

#: pre-commit hook script must contain this
pre_commit_hook = '''\
#!/bin/sh
# Auto generated by ct-mkproject, you may add to this file,
ct-pre-commit-hook # but don't remove this call
'''

#: $project/tests/conftest.py must contain this
conftest_py = '''\
# http://stackoverflow.com/a/30091579/1031434
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL) # Ignore SIGPIPE
'''

#: requirements.in must start with this header
requirements_in_header = '# List of required dependencies'

#: dev_requirements.in must contain these dependencies, in this order
dev_requirements_in = ['Sphinx', 'numpydoc', 'sphinx-rtd-theme']

#: test_requirements.in must contain these dependencies, in this order
test_requirements_in = ['pytest', 'pytest-env', 'pytest-xdist', 'pytest-cov', 'coverage-pth']

#: setup.cfg must set these options to these values iff they're missing
setup_cfg_defaults = {
    'pytest': {
        'addopts': dedent('''
            --basetemp=last_test_runs
            --cov-config=.coveragerc
            -n auto'''),
        'env': 'PYTHONHASHSEED=0'
    }
}

#: setup.cfg must set these options to these values
setup_cfg_overwrite = {
    'pytest': {
        'testpaths': '{pkg_root}/tests',
    },
    'metadata': {
        'description-file': '{readme_file}',
    }
}

#: .coveragerc must set these options to these values iff they're missing
coveragerc_defaults = {}

#: .coveragerc must set these options to these values
coveragerc_overwrite = {'run': {'omit': '{pkg_root}/tests/*'}}

#: MANIFEST.in must contain these lines
manifest_in = '''\
include {readme_file}
recursive-include docs *
recursive-exclude docs/build *
'''.splitlines()

#: docs/_templates/autosummary/module.rst must match this format
docs_templates_autosummary_module_rst = resource_string(__name__, 'data/_templates/autosummary/module.rst').decode('utf-8')

#: docs/conf.py must match this format
docs_conf_py = resource_string(__name__, 'data/conf.py').decode('utf-8')

#: docs/Makefile must match this format
docs_makefile = resource_string(__name__, 'data/Makefile').decode('utf-8')

#: docs/index.rst must match this format
docs_index_rst = resource_string(__name__, 'data/index.rst').decode('utf-8')

#: project.py:project must have these keys
project_py_required_attributes = {'name', 'package_name', 'human_friendly_name', 'python_version', 'readme_file', 'description', 'author', 'author_email', 'url', 'license', 'classifiers', 'keywords', 'index_production'}

#: project.py:project may have these keys
project_py_optional_attributes = {'entry_points', 'index_test', 'pre_commit_no_ignore', 'download_url'}