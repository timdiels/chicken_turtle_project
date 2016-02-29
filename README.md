Python 3 project development tools. Looks like a turtle, tastes like chicken.

Chicken Turtle provides a project template and tools (CLI) for developing
Python 3 projects.

Chicken Turtle is pre-alpha. None of the interface is stable, i.e. it may
change in the future.

## ct-mksetup

Your project should adhere to the following minimal structure:

    $project_name
      __init__.py
      version.py
    project.py

Your source goes in `$project_name`. Use `project.py` to configure
`ct-mksetup`. Package data can be added by adding a `data` directory without an
`__init__.py` to the package in the `$project_name` tree. 

Run `ct-mksetup` to generate/update `setup.py`.

## Project template usage

Instructions for the included project template.

To create a project with Chicken Turtle:

- Copy the template directory to start your project from.
- Replace all occurences of `$project_name` in the template files with your project name.
- Edit `setup.py` with the details of your project.
- Rename gitignore to .gitignore

To use the created project:

- venv_create.sh: create a virtual environment corresponding to setup.py. If requirements.txt exists, that list of packages will be installed. If extra_requirements.txt exists (corresponding to the extra dependencies in setup.py), these will also be installed. Then setup.py's deps are installed, without upgrading any other packages. 
- interpreter.sh: start an interpreter inside the virtual environment, ensuring the project source is in the PYTHONPATH and start an interactive session in which interpreter.py is first executed.
- test data should be placed in test/data
- output of last test runs is kept in test/last_runs 
- run_tests.py to run the tests, but you need to run it from withing the venv (i.e. `. venv/bin/activate` before running this)


## Methodology

Chicken Turtle Project enforces the following methodology:

TODO
