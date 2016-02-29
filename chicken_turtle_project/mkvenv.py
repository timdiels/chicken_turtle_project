from chicken_turtle_project.common import configure_logging
from pathlib import Path
import logging
import plumbum as pb

logger = logging.getLogger(__name__)
    
def main(): #TODO click to show help message and version; also on mksetup and other tools. Also include the output from -h in the readme automatically, i.e. compile the readme (or maybe reST can? or maybe we should use Sphinx instead?).
    '''
    Create Python virtual environment in $project_root/venv and install project in the venv
    '''
    configure_logging()
    
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
            python('-m', 'venv', 'venv')
        pip_install = pb.local['venv/bin/pip']['install']
        pip_install('--upgrade', 'pip', 'setuptools')
        pip_install('-r', 'requirements.txt')
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