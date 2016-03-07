from chicken_turtle_project.common import graceful_main, init_logging
from pathlib import Path
import logging
import plumbum as pb

logger = logging.getLogger(__name__)
    
def main():
    '''
    Create Python virtual environment in $project_root/venv and install project in the venv
    '''
    init_logging()
    with graceful_main(logger):
        _main()
    
def _main():
    # Find the desired Python
    desired_python = 'python3.4'
    python = pb.local.get(desired_python, 'python3', 'python')
    if python.executable.name != desired_python:
        logger.warning('{} not found, falling back to {}'.format(desired_python, python.executable))
        
    # Create or update venv
    
    project_root = Path.cwd()
    with pb.local.cwd(project_root):
        # TODO first rm venv if --clean is supplied
        if not Path('venv').exists():
            logger.info('Creating venv')
            python('-m', 'venv', 'venv')
        logger.info('Installing dependencies')
        pip_install = pb.local['venv/bin/pip']['install']
        pip_install('--upgrade', 'pip', 'setuptools')
        pip_install('-r', 'requirements.txt')
        logger.info('Installing project package')
        pip_install('-e', '.') #TODO only when -e --editable is supplied to us
    
    # TODO support sip dependencies
#     # sip-based install like this
#     # or: http://stackoverflow.com/a/1962076/1031434
#     install_sip() {
#         python -c 'import sip' && return
#         version=4.17
#         wget http://sourceforge.net/projects/pyqt/files/sip/sip-$version/sip-$version.tar.gz
#         tar zxvf sip-$version.tar.gz
#         pushd sip-$version
#         python configure.py
#         make
#         make install
#         popd
#         rm -rf sip-$version{,.tar.gz}
#     }
#     
#     install_pyqt() {
#         python -c 'import PyQt5' && return
#         version=5.5.1
#         wget http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-$version/PyQt-gpl-$version.tar.gz
#         tar zxvf PyQt-gpl-$version.tar.gz
#         pushd PyQt-gpl-$version
#         python configure.py
#         make
#         make install
#         popd
#         rm -rf PyQt-gpl-$version{,.tar.gz}
#     }