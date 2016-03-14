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

from signal import signal, SIGPIPE, SIG_DFL
from contextlib import contextmanager
from chicken_turtle_util.exceptions import UserException, log_exception
from urllib.parse import urlparse
from pathlib import Path
import plumbum as pb
import git
import sys
import re

import logging
logger = logging.getLogger(__name__)

def eval_file(path): #TODO move into chicken turtle util
    with path.open() as f:
        return eval_string(f.read(), str(path))

def eval_string(string, name='in_memory_string'):
    code = compile(string, 'in memory string', 'exec')
    locals_ = {}
    exec(code, None, locals_)
    return locals_
    
def get_project(project_root):
    '''
    Get and validate project info from project.py
    
    Returns
    -------
    dict
        project info.
    '''
    # Load 
    try:
        project = eval_file(project_root / 'project.py')['project']
    except IOError:
        raise UserException('Must run from the directory which contains project.py')
    except KeyError:
        raise UserException('project.py must export a `project` variable (with a dict)')
    
    required_attributes = {'name', 'readme_file', 'description', 'author', 'author_email', 'url', 'license', 'classifiers', 'keywords', 'download_url', 'index_production'}
    optional_attributes = {'entry_points', 'index_test'}
    
    # Attributes that must be present    
    for attr in required_attributes:
        if attr not in project:
            raise UserException('Missing required attribute: project["{}"]'.format(attr))
        
    pkg_root = project_root / project['name']

    # Attributes that should not be present
    if 'version' in project:
        raise UserException('Encountered `version` in `project`. Version should be specified in {}/version.py as `__version__=...`, not in project.py'.format(pkg_root))
    elif 'package_data' in project:
        raise UserException('Encountered `package_data` in `project`. This is auto-generated, remove it. If your data directories are named `data`, have no `__init__.py` and are part of a package in {}, they will be included by auto generation.'.format(pkg_root))
    elif 'packages' in project:
        raise UserException('Encountered `packages` in `project`. This is auto-generated by mksetup, remove it.')
    elif 'long_description' in project:
        raise UserException('Encountered `long_description` in `project`. This is auto-generated by mksetup, remove it.')
    elif 'extras_require' in project:
        raise UserException('Encountered `extras_require` in `project`. Not currently supported, remove it.')
    elif 'install_requires' in project:
        raise UserException('Encountered `install_requires` in `project`. Specify these in requirements.in instead.')
    else:
        for unknown_attr in set(project.keys()) - required_attributes - optional_attributes:
            raise UserException('Encountered unknown attribute `{}` in `project`. Please remove it.'.format(unknown_attr))
        
    # Ensure values are non-empty
    for attr in project:
        if not project[attr]:
            raise UserException('Attribute `{}` may not be None'.format(attr))
        if attr != 'entry_points':
            project[attr] = project[attr].strip()
            if not project[attr]:
                raise UserException('Attribute `{}` may not be empty or whitespace'.format(attr))
        
    # Validate project name
    if re.search('[\s_]', project['name']):
        raise UserException('Attribute `name` may not contain whitespace or underscores (use dashes)')
    
    # Validate readme_file
    if not re.fullmatch('(.*/)?README.[a-z0-9]+', project['readme_file']):
        raise UserException('Attribute `readme_file` must be a path with as file name "README.*", case sensitive with a lower case extension')
            
    return project
    
def init_logging(debug=False):
    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level)
    
@contextmanager
def graceful_main(logger):
    signal(SIGPIPE, SIG_DFL)  # Ignore SIGPIPE, http://stackoverflow.com/a/30091579/1031434
    try:
        yield
    except UserException as ex:
        logger.error(ex.message)
        sys.exit(1)
    except Exception as ex:
        logger.exception(ex)
        sys.exit(2)

def get_repo(project_root):
    return git.Repo(pb.local.env.get('GIT_DIR', str(project_root)))

def parse_requirements_file(path):
    '''
    Parse requirements.txt or requirements.in file
    
    Note: requirements-parser 0.1.0 does not support -e lines it seems, hence this ad-hoc parser
    
    Parameters
    ----------
    path : pathlib.Path
        path to requirements file
        
    Returns
    -------
    Generator that yields (editable : bool, dependency_url : str, version_spec : str, raw line : str)
    '''
    # XXX return namedtuple instead
    with path.open('r') as f:
        # Ad-hoc parse each line into a dependency (requirements-parser 0.1.0 does not support -e lines it seems)
        for line in f.readlines():
            match = re.fullmatch('\s*(-e\s)?\s*(([^#\s=<>]+)\s*([=<>]\s*[^\s#]+)?)?\s*(#.*)?', line.rstrip())
            if match:
                yield (bool(match.group(1)), match.group(3), match.group(4), match.group(0))
                
def path_stem_deep(path):
    '''path name without any suffixes'''
    i = path.name.find('.')
    if i>=0:
        return path.name[:i]
    else:
        return path.name
    
def get_url_name(url):
    assert url
    result = urlparse(url)
    return path_stem_deep(Path(result.netloc + '/' + result.path))

def get_dependency_name(url):
    return get_url_name(url).replace('_', '-')

def get_pkg_root(project_root, project_name):
    return project_root / project_name.replace('-', '_')
    
    