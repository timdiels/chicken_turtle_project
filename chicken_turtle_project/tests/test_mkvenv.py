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
    assert Path('venv/bin/python3.5').exists() # project.py requested python version 3.5
    
    # When call mycli, all good
    stdout = pb.local['venv/bin/mycli']()
    assert 'meow' in stdout
    