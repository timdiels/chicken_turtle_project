from chicken_turtle_project.common import remove_file, init_logging, graceful_main
from chicken_turtle_project import __version__
from chicken_turtle_util import cli
from pathlib import Path
import plumbum as pb
import click
from tempfile import mkdtemp

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
            env_context = pb.local.env(
                GIT_DIR=str(_get_abs_path_from_env('GIT_DIR')),
                GIT_INDEX_FILE=str(_get_abs_path_from_env('GIT_INDEX_FILE')),
            ) 
            with env_context, pb.local.cwd(str(temp_dir)):
                # Reuse dev venv, if any
                venv_dir = project_root / 'venv'
                if venv_dir.exists():
                    Path(venv_dir.name).symlink_to(venv_dir, target_is_directory=True)
                    
                # Reuse pytest-testmon data
                testmondata_path = project_root / '.testmondata'
                if testmondata_path.exists():
                    Path(testmondata_path.name).symlink_to(testmondata_path)
                    
                # Update project
                pb.local['ct-mkproject']['--pre-commit'] & pb.FG
                
                # Forget about Git and Chicken Turtle environment
                bad_env_vars = [k for k in pb.local.env.keys() if k.startswith('GIT_') or k.startswith('CT_')]
                for name in bad_env_vars:
                    del pb.local.env[name]
                
                # Run tests
                pb.local['ct-mkvenv'] & pb.FG
                pb.local['venv/bin/py.test'] & pb.FG(retcode=(0,5))
            
        finally:
            remove_file(temp_dir)
            
def _get_abs_path_from_env(name):
    return Path(pb.local.env.get(name, '.')).absolute()