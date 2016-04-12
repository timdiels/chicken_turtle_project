'''
ct-mkvenv tests
'''

from chicken_turtle_project.tests.common import (
    create_project, reset_logging, project1
)
from chicken_turtle_project.mkvenv import main as _mkvenv
from click.testing import CliRunner
from textwrap import dedent
from pathlib import Path
import plumbum as pb
import pytest

# TODO this is copy paste from `release`
def mkvenv(*args, **invoke_kwargs):
    '''
    Call mkvenv, suppress all exceptions
    '''
    result = CliRunner().invoke(_mkvenv, args, **invoke_kwargs)
    reset_logging()
    assert (result.exit_code == 0) == (result.exception is None or (isinstance(result.exception, SystemExit) and result.exception.code == 0))
    return result 

@pytest.mark.long  # Note: takes a while to run due to compiling PyQt5
def test_sip_install(tmpcwd):
    '''
    When SIP dependencies, install them correctly
    '''
    project = project1.copy()
    project.project_py['entry_points'] = {
        'console_scripts': [
            'mycli = operation.mittens.main:main',
        ],
    }
    project.files[Path('requirements.in')] = 'pytest\nsip==4.17\nPyQt5==5.5.1\n'
    project.files[Path('operation/mittens/main.py')] = dedent('''\
        import pytest
        import PyQt5
        
        def main():
            print('meow')
        ''')
    create_project(project)
    
    pb.local['ct-mkproject']()
    
    # When mkvenv, all good
    result = mkvenv()
    assert result.exit_code == 0, result.output
    
    # When call mycli, all good
    stdout = pb.local['venv/bin/mycli']()
    assert 'meow' in stdout
    