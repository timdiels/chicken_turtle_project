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
# @cli.option(
#     '-e', '--editable',
#     type=bool, is_flag=True, default=False,
#     help='Install project in editable mode (i.e. `pip install -e`)'
# )
@click.version_option(version=__version__)
def main():
    '''
    Create Python virtual environment in `./venv` and install project in it.
    
    The following input files are required:
    
    - `./*requirements.in`
    - `./setup.py`
    - `./requirements.txt`
    
    See also: `ct-mkproject` for generating/updating the above files.
    '''
    init_logging()
    with graceful_main(logger):
        _main()
    
def _main():
    project_root = Path.cwd()
    
    # Create venv if missing
    if not Path('venv').exists():
        # Find the desired Python
        desired_python = 'python3.4'
        python = pb.local.get(desired_python, 'python3', 'python')
        if python.executable.name != desired_python:
            logger.warning('{} not found, falling back to {}'.format(desired_python, python.executable))
        
        # Create venv    
        logger.info('Creating venv')
        python('-m', 'venv', 'venv')
        
    python = pb.local['venv/bin/python']
    
    # Install install dependencies    
    base_dependencies = {'pip', 'setuptools', 'wheel'}  # these are always (implicitly) desired
    logger.info('Installing install dependencies')
    python('venv/bin/pip', 'install', '--upgrade', *base_dependencies) # Note: setuptools sometimes creates shebangs that are longer than the max allowed, so we call pip with python directly, avoiding the shebang
    
    # Get desired dependencies from requirements.txt (note: requirements.txt contains no SIP deps)
    desired_dependencies = base_dependencies
    for _, dependency, version_spec, _ in parse_requirements_file(Path('requirements.txt')):
        if dependency:
            desired_dependencies.add(get_dependency_name(dependency))
    
    # Get installed dependencies
    installed_dependencies = set()
    for _, dependency, version_spec, _ in parse_requirements(python('venv/bin/pip', 'freeze').splitlines()):
        if dependency:
            installed_dependencies.add(get_dependency_name(dependency))
            
    # Remove installed packages not listed in requirements.txt
    extra_dependencies = installed_dependencies - desired_dependencies
    if extra_dependencies:
        logger.info('Removing packages not listed as dependencies: ' + ' '.join(extra_dependencies))
        python('venv/bin/pip', 'uninstall', '-y', *extra_dependencies)
    
    # Install desired dependencies
    logger.info('Installing dependencies')
    python('venv/bin/pip', 'install', '-r', 'requirements.txt')  # Note: first uninstalls pkg if different version is installed
    
    # Get desired SIP dependencies
    desired_sip_dependencies = {}  # {(name :: str) : (version :: str)}
    input_file_paths = get_dependency_file_paths(project_root)
    for input_path in input_file_paths:
        for _, dependency, version_spec, _ in parse_requirements_file(input_path):
            if not dependency:
                continue
            name = get_dependency_name(dependency)
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
                    cmd = sh['-c', '. ../venv/bin/activate && python configure.py && make && make install']
                    if name == 'pyqt5':
                        # say yes to license and ignore exit code as this script always fails (but still install correctly)
                        (cmd << 'yes\n')(retcode=None)
                    else:
                        cmd()
            finally:
                if unpack_path.exists():
                    remove_file(unpack_path)
                if tar_path.exists():
                    remove_file(tar_path)
        
    # Install project package
    logger.info('Installing project package')
    python('venv/bin/pip', 'install', '-e', '.')
    
