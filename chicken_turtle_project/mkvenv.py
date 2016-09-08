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
    graceful_main, get_dependency_file_paths, 
    parse_requirements_file, is_sip_dependency, get_dependency_name,
    sip_packages, remove_file, get_project, debug_option
)
from chicken_turtle_project import __version__
import click
from pathlib import Path
from collections import namedtuple
import logging
import plumbum as pb
import pkg_resources

logger = logging.getLogger(__name__)

_SIPDependency = namedtuple('SIPDependency', 'name version')
    
class SIPDependency(_SIPDependency):
    def __eq__(self, other):
        if isinstance(other, SIPDependency):
            return self.name == other.name
        else:
            return self.name == str(other).lower()
    
def get_venv(venv_dir):
    return pkg_resources.WorkingSet([str(next(venv_dir.glob('lib/python*/site-packages')))])
    
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@debug_option()
@click.version_option(version=__version__)
def main(debug):
    '''
    Create Python virtual environment in `./venv` and install project in it.
    
    First calls `ct-mkproject` to ensure project files are up to date, unless
    CT_NO_MKPROJECT is set. In the latter case requirements.txt,
    *requirements.in files and setup.py should already be present.
    '''
    with graceful_main(logger, app_name='mkvenv', debug=debug):
        _main()
    
def _main():
    pb.local['ct-mkproject']()  # Ensure requirements.in files, ... are up to date
    
    project_root = Path.cwd()
    project = get_project(project_root)
    venv_dir = Path(pb.local.env.get('CT_VENV_DIR', 'venv')).absolute()
    
    # Create venv if missing
    if not venv_dir.exists():
        # Find the desired Python
        desired_python = 'python{}.{}'.format(*project['python_version'])
        python = pb.local.get(desired_python, 'python{}'.format(project['python_version'][0]), 'python')
        if python.executable.name != desired_python:
            logger.warning('{} not found, falling back to {}'.format(desired_python, python.executable))
        
        # Create venv    
        logger.info('Creating venv')
        python('-m', 'venv', str(venv_dir))
        
    python = pb.local[str(venv_dir / 'bin/python')]
    pip = python[str(venv_dir / 'bin/pip')]  # Note: setuptools sometimes creates shebangs that are longer than the max allowed, so we call pip with python directly, avoiding the shebang
        
    # These are always (implicitly) desired
    base_dependencies = {'pip' : '', 'setuptools' : '', 'wheel' : ''}
    for editable, dependency, version_spec, _ in parse_requirements_file(Path('requirements.txt')):
        if dependency in base_dependencies:
            base_dependencies[dependency] = version_spec
    
    logger.info('Upgrading {}'.format(', '.join(sorted(base_dependencies))))
    pip('install', '--upgrade', *(dependency + version_spec for dependency, version_spec in base_dependencies.items()))
    
    # Get desired dependencies from requirements.txt (note: requirements.txt contains no SIP deps)
    desired_dependencies = set(base_dependencies.keys())
    for editable, dependency, version_spec, _ in parse_requirements_file(Path('requirements.txt')):
        if dependency:
            desired_dependencies.add(get_dependency_name(editable, dependency))
    
    # Get installed dependencies
    venv = get_venv(venv_dir)
    installed_dependencies = {distribution.project_name.lower() for distribution in venv}
            
    # Remove installed packages not listed in requirements.txt
    extra_dependencies = installed_dependencies - desired_dependencies
    extra_dependencies.discard('chicken-turtle-project')  # never uninstall chicken-turtle-project
    logger.debug('Installed packages: ' + ' '.join(installed_dependencies))
    logger.debug('Desired packages: ' + ' '.join(desired_dependencies))
    if extra_dependencies:
        if extra_dependencies != {project['name']}:
            logger.info('Removing packages not listed as dependencies: ' + ', '.join(extra_dependencies))
        pip('uninstall', '-y', *extra_dependencies)
    
    # Install desired dependencies
    logger.info('Installing requirements.txt')
    pip('install', '-r', 'requirements.txt')
    
    # Get desired SIP dependencies
    desired_sip_dependencies = {}  # {(name :: str) : (version :: str)}
    input_file_paths = get_dependency_file_paths(project_root)
    for input_path in input_file_paths:
        for editable, dependency, version_spec, _ in parse_requirements_file(input_path):
            if not dependency:
                continue
            name = get_dependency_name(editable, dependency)
            if is_sip_dependency(name):
                assert version_spec.startswith('==')
                desired_sip_dependencies[name.lower()] = version_spec[2:]
                
    # Get installed SIP dependencies
    installed_sip_dependencies = set()
    for name, package in sip_packages.items():
        if python['-c', 'import {}'.format(package)] & pb.TF:
            installed_sip_dependencies.add(name)
    
    # Install SIP dependencies
    missing_sip_dependencies = desired_sip_dependencies.keys() - installed_sip_dependencies
    if missing_sip_dependencies:
        # Note: http://stackoverflow.com/a/1962076/1031434
        logger.info('Installing SIP dependencies')
        wget = pb.local['wget']
        tar = pb.local['tar']
        sh = pb.local['sh']
        for name in ['sip'] + list(missing_sip_dependencies - {'sip'}):
            logger.info('- installing ' + name)
            if name == 'sip':
                url = 'https://sourceforge.net/projects/pyqt/files/sip/sip-{version}/sip-{version}.tar.gz'
                unpack_path = 'sip-{version}'
            elif name == 'pyqt5':
                url = 'https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-{version}/PyQt-gpl-{version}.tar.gz'
                unpack_path = 'PyQt-gpl-{version}'
            else:
                assert False
            
            version = desired_sip_dependencies[name]
            unpack_path = Path(unpack_path.format(version=version))
            tar_path = unpack_path.with_name(unpack_path.name + '.tar.gz')
            try:
                wget(url.format(version=version)) #XXX use CTU http.download_file instead
                tar('zxvf', str(tar_path))
                with pb.local.cwd(str(unpack_path)):
                    cmd = sh['-c', '. {} && python configure.py && make && make install'.format(str(venv_dir / 'bin/activate'))]
                    if name == 'pyqt5':
                        # say yes to license and ignore exit code as this script always fails (but still install correctly)
                        (cmd << 'yes\n')(retcode=None)
                    else:
                        cmd & pb.FG
            finally:
                if unpack_path.exists():
                    remove_file(unpack_path)
                if tar_path.exists():
                    remove_file(tar_path)
        
    # Install project package
    logger.info('Installing project package')
    pip('install', '-e', '.')
    
