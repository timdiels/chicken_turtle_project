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
from chicken_turtle_project.common import graceful_main, get_repo, get_newest_version, get_current_version, get_project
from pathlib import Path
import plumbum as pb
import logging
import click

logger = logging.getLogger(__name__)

def main():
    '''
    Open a Python interpreter in the venv of the current project.
    
    Should be run in the project root. Runs venv/bin/python and 'sources'
    `interpreter.py` if it exists.
    '''
    graceful_main(_main, logger)
    
def _main():
    # Note: The pre-commit hook already does most of the project validation
    project_root = Path.cwd()
    project = get_project(project_root)
    
    # Working directory must be clean (no untracked/modified files)
    repo = get_repo(project_root)
    if repo.is_dirty:
        raise UserException('Please first commit or stash your changes')
    
    # Current commit must have version tag
    version = get_current_version(repo)
    if not version:
        raise UserException('Please assign a version with `git tag v{{version}}, newest version is {}`'.format(str(get_newest_version())))
    
    assert False
    # Release to test index (if any)
    index_name = project['index_test']
    if index_name:
        _release(index_name)
    
    # Release to production index
    _release(project['index_production'])
    logger.info('Released')
    
def _release(index_name): #TODO don't forget to mock this in tests, do not want to actually release
    logger.info('Releasing to production index')
    setup = pb.local['python']['setup.py']
    setup('register', '-r', index_name)
    setup('sdist', 'upload', '-r', index_name)
    
    
    