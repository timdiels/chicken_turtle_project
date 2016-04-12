from chicken_turtle_project.common import (
    graceful_main, init_logging, remove_file, get_project, get_pkg_root
)
from chicken_turtle_project import __version__
import click
from pathlib import Path
import logging
import plumbum as pb

logger = logging.getLogger(__name__)
    
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(version=__version__)
def main():
    '''
    Generate project documentation
    
    Note: calls `ct-mkvenv` to ensure the venv is up to date
    '''
    init_logging()
    with graceful_main(logger):
        pb.local['ct-mkvenv'] & pb.FG  # ensure venv is up to date
        
        venv_dir = Path(pb.local.env.get('CT_VENV_DIR', 'venv')).absolute()
        project_root = Path.cwd()
        project = get_project(project_root)
        pkg_root = get_pkg_root(project_root, project['package_name'])
        
        doc_root = project_root / 'docs'
        remove_file(doc_root / 'api')
        remove_file(doc_root / 'build')
        kwargs = dict(
            venv_activate=venv_dir / 'bin/activate',
            doc_root=doc_root,
            pkg_root=pkg_root,
            pkg_root_root= project_root / project['package_name'].split('.')[0]
        )
        pb.local['sh']['-c', '. {venv_activate} && sphinx-apidoc -o {doc_root}/api -T {pkg_root_root} {pkg_root}/tests && cd {doc_root} && make html'.format(**kwargs)] & pb.FG
