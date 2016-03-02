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
from common import graceful_main, get_repo, get_newest_version, get_current_version, version_from_tag
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
    project_root = Path.cwd()
    
    # Ensure project is up to date and valid
    pb.local['ct-mkproject']()
    
    # Working directory must be clean (no untracked/modified files)
    repo = get_repo(project_root)
    if repo.is_dirty:
        raise UserException('Please first commit or stash your changes')
    
    # Current commit must have version tag
    version = get_current_version(repo)
    if not version:
        raise UserException('Please assign a version with `git tag v{{version}}, newest version is {}`'.format(str(get_newest_version())))

    # Warn if current version is less than that of any ancestor commit
    ancestors = list(repo.commit().iter_parents())
    versions = []
    for tag in repo.tags:
        if tag.commit in ancestors:
            try:
                versions.append(version_from_tag(tag))
            except AttributeError:
                pass
    newest_ancestor_version = max(versions)
    if version < newest_ancestor_version:
        logger.warning('Current version ({}) is older than ancestor commit version ({})'.format(version, newest_ancestor_version))
        if not click.confirm('Do you want to release anyway?'):
            logger.info('Release cancelled')
            return
    
    return
    # Release to test index (if any)
    logger.info('Releasing to test index')
#     python setup.py register -r pypitest
#     python setup.py sdist upload -r pypitest
    
    # Release to production index
    logger.info('Releasing to production index')
#     python setup.py register -r pypi
#     python setup.py sdist upload -r pypi
    
    logger.info('Released')
    