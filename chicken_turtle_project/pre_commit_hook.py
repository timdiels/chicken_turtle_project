from chicken_turtle_project.common import remove_file, init_logging, graceful_main, get_project
from chicken_turtle_project import __version__
from pathlib import Path
import plumbum as pb
import click
from tempfile import mkdtemp
import shutil
from glob import glob

import logging
logger = logging.getLogger(__name__)

git_ = pb.local['git']
tar = pb.local['tar']

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(version=__version__)
def main():
    '''
    Internal, do not use
    '''
    init_logging()
    with graceful_main(logger):
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
            with env_context, pb.local.cwd(str(temp_dir)):
                # Check documentation for errors (which also updates the venv, which we rely on)
                pb.local['ct-mkdoc'] & pb.FG
                
                # Forget about Git and Chicken Turtle environment before running tests
                bad_env_vars = [k for k in pb.local.env.keys() if k.startswith('GIT_') or k.startswith('CT_')]
                for name in bad_env_vars:
                    del pb.local.env[name]

                # Run tests
                pb.local[str(venv_dir / 'bin/py.test')] & pb.FG(retcode=(0,5))
            
        finally:
            remove_file(temp_dir)
            
def _get_abs_path_from_env(name):
    return Path(pb.local.env.get(name, '.')).absolute()