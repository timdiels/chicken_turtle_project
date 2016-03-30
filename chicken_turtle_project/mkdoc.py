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
    
    See also: `ct-mkproject` for generating and updating files required by ct-mkdoc.
    '''
    init_logging()
    with graceful_main(logger):
        project_root = Path.cwd()
        project = get_project(project_root)
        pkg_root = get_pkg_root(project_root, project['name'])
        
        doc_root = project_root / 'docs'
        remove_file(doc_root / 'api')
        remove_file(doc_root / 'build')
        kwargs = dict(
            doc_root=doc_root,
            pkg_name=pkg_root.name,
            pkg_root=pkg_root
        )
        pb.local['sh']('-c', '. venv/bin/activate && sphinx-apidoc -o {doc_root}/api -T {pkg_name} {pkg_root}/test && cd {doc_root} && make html'.format(**kwargs))
