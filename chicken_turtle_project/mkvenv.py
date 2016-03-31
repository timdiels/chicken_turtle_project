from chicken_turtle_project.common import (
    graceful_main, init_logging, get_dependency_file_paths, 
    parse_requirements_file, is_sip_dependency, get_dependency_name,
    parse_requirements, sip_packages, remove_file
)
from chicken_turtle_project import __version__
import click
from pathlib import Path
from collections import namedtuple
import logging
import plumbum as pb

logger = logging.getLogger(__name__)

_SIPDependency = namedtuple('SIPDependency', 'name version')
    
class SIPDependency(_SIPDependency):
    def __eq__(self, other):
        if isinstance(other, SIPDependency):
            return self.name == other.name
        else:
            return self.name == str(other).lower()
    
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(version=__version__)
def main():
    '''
    Create Python virtual environment in `./venv` and install project in it.
    
    Note: Calls `ct-mkproject` to ensure project files are up to date.
    '''
    init_logging(debug=False)
    with graceful_main(logger):
        _main()
    
def _main():
    pb.local['ct-mkproject'] & pb.FG  # Ensure requirements.in files, ... are up to date
    
    project_root = Path.cwd()
    venv_dir = Path(pb.local.env.get('CT_VENV_DIR', 'venv')).absolute()
    
    # Create venv if missing
    if not venv_dir.exists():
        # Find the desired Python
        desired_python = 'python3.4'
        python = pb.local.get(desired_python, 'python3', 'python')
        if python.executable.name != desired_python:
            logger.warning('{} not found, falling back to {}'.format(desired_python, python.executable))
        
        # Create venv    
        logger.info('Creating venv')
        python('-m', 'venv', str(venv_dir))
        
    python = pb.local[str(venv_dir / 'bin/python')]
    pip = python[str(venv_dir / 'bin/pip')]  # Note: setuptools sometimes creates shebangs that are longer than the max allowed, so we call pip with python directly, avoiding the shebang
    
    # Install install dependencies    
    base_dependencies = {'pip', 'setuptools', 'wheel'}  # these are always (implicitly) desired
    logger.info('Installing install dependencies')
    pip.bgrun(['install', '--upgrade'] + list(base_dependencies))
    
    # Get desired dependencies from requirements.txt (note: requirements.txt contains no SIP deps)
    desired_dependencies = base_dependencies
    for editable, dependency, version_spec, _ in parse_requirements_file(Path('requirements.txt')):
        if dependency:
            desired_dependencies.add(get_dependency_name(editable, dependency))
    
    # Get installed dependencies
    installed_dependencies = set()
    for editable, dependency, version_spec, _ in parse_requirements(pip('freeze').splitlines()):
        if dependency:
            installed_dependencies.add(get_dependency_name(editable, dependency))
            
    # Remove installed packages not listed in requirements.txt
    extra_dependencies = installed_dependencies - desired_dependencies
    extra_dependencies.discard('chicken-turtle-project')  # never uninstall chicken-turtle-project
    logger.debug('Installed packages: ' + ' '.join(installed_dependencies))
    logger.debug('Desired packages: ' + ' '.join(desired_dependencies))
    logger.debug('Packages too many: ' + ' '.join(extra_dependencies))
    if extra_dependencies:
        logger.info('Removing packages not listed as dependencies')
        pip.bgrun(['uninstall', '-y'] + list(extra_dependencies))
    
    # Install desired dependencies
    logger.info('Installing dependencies')
    for editable, dependency, version_spec, _ in parse_requirements_file(Path('requirements.txt')):  # Note: we can't use pip install -r as we promise to install in order
        if not dependency:
            continue
        if editable:
            args = ['-e']
        else:
            args = []
        if version_spec:
            dependency += version_spec
        args.append(dependency)
        pip('install', *args)
    
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
    
