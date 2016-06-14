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

from chicken_turtle_project.common import remove_file, graceful_main, get_project, debug_option
from chicken_turtle_project import __version__
from pathlib import Path
import plumbum as pb
import click
from tempfile import mkdtemp
from glob import glob
from contextlib import suppress

import logging
logger = logging.getLogger(__name__)

git_ = pb.local['git']
tar = pb.local['tar']

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@debug_option()
@click.version_option(version=__version__)
def main(debug):
    '''
    Internal, do not use
    '''
    with graceful_main(logger, app_name='pre-commit-hook', debug=debug):
        temp_dir = Path(mkdtemp())
        try:
            # Export last commit + staged changes
            if pb.local.env.get('CT_RELEASE'): # Are we releasing? (ct-release)
                # Make clean copy of working dir without staged changes
                (git_['archive', 'HEAD'] | tar['-x', '-C', str(temp_dir)])()
            else:
                # Make clean copy of working dir with staged changes
                git_('checkout-index', '-a', '-f', '--prefix', str(temp_dir) + '/')
            
            project_root = _get_abs_path_from_env('GIT_WORKING_TREE')
            project = get_project(project_root)
            for pattern in project['pre_commit_no_ignore']:
                for file in glob(pattern):
                    pb.path.utils.copy(file, str(temp_dir / file))
            venv_dir = Path(pb.local.env.get('CT_VENV_DIR', str(project_root / 'venv'))).absolute()
            env_context = pb.local.env(
                GIT_DIR=str(_get_abs_path_from_env('GIT_DIR')),
                GIT_INDEX_FILE=str(_get_abs_path_from_env('GIT_INDEX_FILE')),
                CT_VENV_DIR=str(venv_dir),
            ) 
            try:
                with env_context, pb.local.cwd(str(temp_dir)):
                    # Check documentation for errors (which also updates the venv, which we rely on)
                    pb.local['ct-mkdoc'] & pb.FG
                    
                    # Forget about Git and Chicken Turtle environment before running tests
                    bad_env_vars = [k for k in pb.local.env.keys() if k.startswith('GIT_') or k.startswith('CT_')]
                    for name in bad_env_vars:
                        del pb.local.env[name]
    
                    # Run tests
                    pb.local['sh']['-c', '. {} && py.test'.format(venv_dir / 'bin/activate')] & pb.FG(retcode=(0,5))
            finally:
                # Restore venv dir
                with pb.local.cwd(str(project_root)):
                    with suppress(pb.commands.ProcessExecutionError): # if restoring fails, commit should still continue
                        pb.local['ct-mkvenv']()
        finally:
            remove_file(temp_dir)
            
def _get_abs_path_from_env(name):
    return Path(pb.local.env.get(name, '.')).absolute()