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
from functools import partial
from pathlib import Path
import plumbum as pb
from plumbum.commands import ProcessExecutionError
import logging
import versio.version
import versio.version_scheme
import click

logger = logging.getLogger(__name__)
git_ = pb.local['git']
Version = partial(versio.version.Version, scheme=versio.version_scheme.Pep440VersionScheme)
Version.__name__ = 'Version'

def main(args=None):
    _main(args, help_option_names=['-h', '--help'])
    
@click.command()
@cli.option(
    '--project-version',
    type=Version,
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
        version_tag = 'v{}'.format(project_version)
        
        # Working directory must be clean (no untracked/modified files)
        if repo.is_dirty(untracked_files=True):
            raise UserException('Git repo is not clean, please stash or commit all untracked files and changes')
        
        # Disallow reuse of previous versions
        for tag in repo.tags:
            try:
                if _version_from_tag(tag) == project_version:
                    raise UserException('This version has been released before')
            except ValueError:
                pass
        
        # Get newest ancestor version
        ancestors = list(repo.commit().iter_parents())
        versions = []
        for tag in repo.tags:
            if tag.commit in ancestors:
                try:
                    versions.append(_version_from_tag(tag))
                except AttributeError:
                    pass
        newest_ancestor_version = max(versions, default=Version('0.0.0'))
                
        # If version is less than that of an ancestor commit, ask to continue
        if project_version < newest_ancestor_version and not click.confirm('Given version is less than that of an ancestor commit ({}). Do you want to release anyway?'.format(newest_ancestor_version)):
            raise UserException('Cancelled')
        
        # Check origin is configured correctly
        logger.info('Validating git remote')
        try:
            git_('ls-remote', 'origin')
        except ProcessExecutionError as ex:
            raise UserException('Cannot access remote: origin') from ex 
        
        # Validation done, release
        with pb.local.env(CT_PROJECT_VERSION=str(project_version)):
            released = False  # whether we have released anything of current version yet
            committed = False
            tag_created = False
            
            try:
                # Prepare release
                logger.info('Preparing to commit versioned project')
                pb.local['ct-mkproject'] & pb.FG  # While pre-commit hook will also call ct-mkproject, we need to call it here first to dirty the repo as git commit would throw otherwise
                
                logger.info('Committing')
                git_['commit', '-m', 'Release {}'.format(version_tag)] & pb.FG
                committed = True
                
                logger.info('Tagging commit as "{}"'.format(version_tag))
                git_('tag', version_tag)
                tag_created = True

                # Release                     
                try:
                    # to test index (if any)
                    if 'index_test' in project:
                        _release(project['index_test'])
                        released=True
                
                    # to production index
                    _release(project['index_production'])
                    released=True
                except ReleaseError as ex:
                    if ex.partial:
                        released=True
                    raise
            
                # Push
                try:
                    logger.info('Pushing commits to remote')
                    git_('push')
                     
                    logger.info('Pushing tag to remote')
                    git_('push', 'origin', version_tag)
                except:
                    logger.error('Failed to push. Run the following once the issue is resolved to complete the release: git push && git push origin v{}'.format(project_version))
                    raise
            except:
                if not released:
                    logger.warning('Something went wrong, but nothing was released, rolling back')
                    if committed:
                        git_('reset', '--hard', 'HEAD^')
                    if tag_created:
                        git_('tag', '-d', version_tag)
                raise
    
def _version_from_tag(tag):
    '''
    Get version from version tag
    
    Returns
    -------
    str
        The version the version tag represents 
    
    Raises
    ------
    ValueError
        If tag name is not of format v{version}, i.e. not a version tag
    '''
    name = Path(tag.name).name
    if name[0] != 'v':
        raise ValueError('{} is not a version tag'.format(tag))
    return name[1:]
    

# Note: this function is mocked in a unit test, none of the code
# that actually releases to an index should leave this function's
# dynamic scope!
def _release(index_name):
    '''
    Returns False if not at all released, True if partial or fully released
    '''
    logger.info('Releasing to {}'.format(index_name))
    
    try:
        setup('register', '-r', index_name)
    except ProcessExecutionError as ex:
        raise ReleaseError(partial=False, index_name=index_name) from ex
    
    try:
        setup('sdist', 'upload', '-r', index_name)
    except ProcessExecutionError as ex:
        raise ReleaseError(partial=True, index_name=index_name) from ex
    
    logger.info('Released to {}'.format(index_name))
    
_setup = pb.local['python']['setup.py']
def setup(*args):
    code, out, err = _setup.run(args)  # always has exit code 0
    if 'Server response (200): OK' not in (out + err):
        raise ProcessExecutionError(args, code, out, err)
    
class ReleaseError(Exception):
    
    '''Release failed'''
    
    def __init__(self, partial, index_name):
        '''
        Parameters
        ----------
        partial : bool
            Whether the release failed completely or partially
        index_name : str
            Index to which we were releasing
        '''
        partial_msg = ', but did release partially!' if partial else ''
        super().__init__('Failed to release to {}{}'.format(index_name, partial_msg))
        self.partial = partial
        self.index_name = index_name
    