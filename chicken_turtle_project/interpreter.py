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
from chicken_turtle_project.common import init_logging
import plumbum as pb
from pathlib import Path

def main():
    '''
    Open a Python interpreter in the venv of the current project.
    
    Should be run in the project root. Runs venv/bin/python and 'sources'
    `interpreter.py` if it exists.
    '''
    init_logging()
    with graceful_main(logger):
        python = pb.local['venv/bin/python']
        if Path('interpreter.py').exists():
            python('-i', 'interpreter.py')
        else:
            python()