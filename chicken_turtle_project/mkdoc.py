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

from chicken_turtle_project.common import (
    graceful_main, remove_file, get_project, get_pkg_root,
    debug_option
)
from chicken_turtle_project import __version__
import click
from pathlib import Path
import logging
import plumbum as pb

logger = logging.getLogger(__name__)
    
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@debug_option()
@click.version_option(version=__version__)
def main(debug):
    '''
    Generate project documentation
    
    Note: calls `ct-mkvenv` to ensure the venv is up to date
    '''
    with graceful_main(logger, app_name='mkdoc', debug=debug):
        pb.local['ct-mkvenv'] & pb.FG  # ensure venv is up to date
        
        venv_dir = Path(pb.local.env.get('CT_VENV_DIR', 'venv')).absolute()
        project_root = Path.cwd()
        project = get_project(project_root)
        pkg_root = get_pkg_root(project_root, project['package_name'])
        
        doc_root = project_root / 'docs'
        remove_file(doc_root / 'build')
        kwargs = dict(
            venv_activate=venv_dir / 'bin/activate',
            doc_root=doc_root,
            pkg_root=pkg_root,
            pkg_root_root= project_root / project['package_name'].split('.')[0]
        )
        pb.local['sh']['-c', '. {venv_activate} && cd {doc_root} && make html'.format(**kwargs)] & pb.FG
