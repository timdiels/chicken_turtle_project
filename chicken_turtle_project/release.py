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
from chicken_turtle_project.common import graceful_main, get_repo, get_project, init_logging
from chicken_turtle_project import __version__
from chicken_turtle_util import cli
from pathlib import Path
import click
import plumbum as pb
import logging

logger = logging.getLogger(__name__)
git_ = pb.local['git']

def main(args=None):
    _main(args, help_option_names=['-h', '--help'])
    
@click.command()
@cli.option(
    '--project-version',
    help='Version of the project release, e.g. "1.0.0-dev2". Versions must adhere to PEP-0440 and preferably make use of semantic versioning.'
)
@click.version_option(version=__version__)
def _main(project_version):
    '''
    Release the project to your configured test (optional) and production index
    
    Must be run in the project root.
    '''
    init_logging()
    with graceful_main(logger):
        # Note: The pre-commit hook already does most of the project validation
        project_root = Path.cwd()
        repo = get_repo(project_root)
        project = get_project(project_root)
        
        # Working directory must be clean (no untracked/modified files)
        if repo.is_dirty(untracked_files=True):
            raise UserException('Git repo is not clean, please stash or commit all untracked files and changes')
        
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
        
        with pb.local.env(CT_PROJECT_VERSION=project_version):
            # Prepare release
            logger.info('Preparing to commit versioned project')
            pb.local['ct-mkproject'] & pb.FG  # Update with version
            
            logger.info('Committing')
            git_('commit', '-m', 'Release v{}'.format(project_version))
            
            logger.info('Tagging commit as "v{}"'.format(project_version))
            git_('tag', 'v{}'.format(project_version))
             
            # Release to test index (if any)
            if 'index_test' in project:
                _release(project['index_test'])
            
            # Release to production index
            _release(project['index_production'])
            logger.info('Released')
            
            # Pushing
            logger.info('Pushing commits to remote')
            git_('push')
            
            logger.info('Pushing tag to remote')
            git_('push', 'origin', 'v{}'.format(project_version))
    
# Note: this function is mocked in a unit test, none of the code
# that actually releases to an index should leave this function's
# dynamic scope!
def _release(index_name):
    assert False, 'Not mocked!'
    logger.info('Releasing to production index')
    setup = pb.local['python']['setup.py']
    setup('register', '-r', index_name)
    setup('sdist', 'upload', '-r', index_name)  
    