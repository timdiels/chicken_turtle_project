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

from chicken_turtle_util.exceptions import UserException, log_exception
from chicken_turtle_project.common import graceful_main, get_repo, get_project, init_logging, raise_if_repo_dirty
from pathlib import Path
import plumbum as pb
import logging

logger = logging.getLogger(__name__)

#TODO
# def get_newest_version(repo):
#     '''
#     Get newest version in git tags, returns
#     
#     Parameters
#     ----------
#     repo : git.Repo
#     
#     Returns
#     -------
#     versio.version.Version
#         A default version if no version tags found, newest version otherwise
#     '''
#     versions = []
#     for tag in repo.tags:
#         try:
#             versions.append(version_from_tag(tag))
#         except AttributeError as e:
#             logger.warning(str(e)) # XXX replace with a pass once we know this works
#     return versions

def main():
    '''
    Open a Python interpreter in the venv of the current project.
    
    Should be run in the project root. Runs venv/bin/python and 'sources'
    `interpreter.py` if it exists.
    '''
    init_logging()
    with graceful_main(logger):
        _main()
    
def _main():
    # Note: The pre-commit hook already does most of the project validation
    project_root = Path.cwd()
    repo = get_repo(project_root)
    project = get_project(project_root)
    
    # Working directory must be clean (no untracked/modified files)
    raise_if_repo_dirty(repo)
    #pb.local['ct-mkproject'] & pb.FG
    
    # Current commit must have version tag
#     version = get_current_version(repo)
#     if not version:
#         raise UserException('Please assign a version with `git tag v{{version}}, newest version is {}`'.format(str(get_newest_version())))
    
    assert False
    
    #TODO use:
    # If version tag, warn if it is less than that of an ancestor commit 
#     version = get_current_version(repo) #TODO
#     if version:
#         ancestors = list(repo.commit().iter_parents())
#         versions = []
#         for tag in repo.tags:
#             if tag.commit in ancestors:
#                 try:
#                     versions.append(version_from_tag(tag))
#                 except AttributeError:
#                     pass
#         newest_ancestor_version = max(versions)
#         if version < newest_ancestor_version:
#             logger.warning('Current version ({}) is older than ancestor commit version ({})'.format(version, newest_ancestor_version))
#             if not click.confirm('Do you want to continue anyway?'):
#                 raise UserException('Cancelled')
            
    # Release to test index (if any)
    if 'index_test' in project:
        _release(project['index_test'])
    
    # Release to production index
    _release(project['index_production'])
    logger.info('Released')
    
def _release(index_name):
    logger.info('Releasing to production index')
    setup = pb.local['python']['setup.py']
    setup('register', '-r', index_name)
    setup('sdist', 'upload', '-r', index_name)
    
    
    