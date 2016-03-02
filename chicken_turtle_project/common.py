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

from pathlib import Path
from chicken_turtle_util.exceptions import UserException, log_exception
from versio.version import Version
from versio.version_scheme import Pep440VersionScheme
from functools import partial
import git
import sys

import logging
logger = logging.getLogger(__name__)

Version = partial(Version(scheme=Pep440VersionScheme))

def eval_file(path):
    with path.open() as f:
        code = compile(f.read(), str(path), 'exec')
        locals_ = {}
        exec(code, None, locals_)
        return locals_
    
def get_project():
    '''
    Get and validate project.py
    
    Returns
    -------
    dict
        project info
        
    Raises
    ------
    UserException
        On validation errors
    '''
    project_root = Path.cwd()
    
    # Load project info
    try:
        project = eval_file(project_root / 'project.py')['project']
    except IOError:
        raise UserException('Must run from the directory which contains project.py')
    except KeyError:
        raise UserException('project.py must export a `project` variable (with a dict)')
    
    # Attributes that must be present
    for attr in 'name readme_file description author author_email url license classifiers keywords download_url index_test index_production'.split():
        if attr not in project:
            raise UserException('Missing required attribute: project["{}"]'.format(attr))
    
    #
    name = project['name']

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
    
    #TODO ensure the readme_file is mentioned in MANIFEST.in
    
    return project
    
def graceful_main(main, logger, debug=False):
    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level)
    try:
        main()
    except UserException as ex:
        logger.error(ex.message)
        sys.exit(1)
    except Exception as ex:
        logger.exception(ex)
        sys.exit(2)

def get_repo(project_root):
    return git.Repo(str(project_root))

def version_from_tag(tag):
    '''
    Returns versio.version.Version, raises AttributeError if not a version tag
    '''
    name = Path(tag.name).name
    if name[0] != 'v':
        raise AttributeError('{} is not a version tag'.format(tag))
    return Version(name[1:])

def get_current_version(repo):
    '''
    Get current version by git tag of current commit
    
    Returns None if no version
    '''
    current_commit = repo.commit()  # the checked out commit
    version = None
    for tag in repo.tags:
        if tag.commit == current_commit:
            try:
                version_ = version_from_tag(tag)
                if version:
                    raise UserException('Checked out commit has multiple version tags, there can be only one')
                version = version_
            except AttributeError:
                pass
    return version
    
def get_newest_version(repo):
    '''
    Get newest version in git tags, returns a default version if no version tags found
    '''
    versions = []
    for tag in repo.tags:
        try:
            versions.append(version_from_tag(tag))
        except AttributeError as e:
            logger.warning(str(e)) # XXX replace with a pass once we know this works
    version = max(versions, default=Version('0.0.0'))
    return version
    
    