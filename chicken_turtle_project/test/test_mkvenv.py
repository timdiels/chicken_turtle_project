'''
ct-mkvenv tests
'''

from chicken_turtle_project.test.common import (
    create_project, reset_logging, write_file, project1, write_project
)
from chicken_turtle_project.mkvenv import main as _mkvenv
import plumbum as pb
import pytest
from click.testing import CliRunner

# TODO this is copy paste from `release`
def mkvenv(*args, **invoke_kwargs):
    '''
    Call mkvenv, suppress all exceptions
    '''
    result = CliRunner().invoke(_mkvenv, args, **invoke_kwargs)
    reset_logging()
    assert (result.exit_code == 0) == (result.exception is None or (isinstance(result.exception, SystemExit) and result.exception.code == 0))
    return result

main_py_template = '''
import pytest
import PyQt5

def main():
    print('meow')
''' 

@pytest.mark.long  # Note: takes a while to run due to compiling PyQt5
def test_sip_install(tmpcwd):
    '''
    When SIP dependencies, install them correctly
    '''
    create_project()
    
    project = project1.copy()
    project['entry_points'] = {
        'console_scripts': [
            'mycli = operation_mittens.main:main',
        ],
    }
    write_project(project)
    
    write_file('requirements.in', 'pytest\nsip==4.17\nPyQt5==5.5.1\n')
    write_file('operation_mittens/main.py', main_py_template)
    
    pb.local['ct-mkproject']()
    
    # When mkvenv, all good
    result = mkvenv()
    assert result.exit_code == 0, result.output
    
    # When call mycli, all good  
    stdout = pb.local['venv/bin/mycli']()
    assert 'meow' in stdout
    