Python 3 project development tools. Looks like a turtle, tastes like chicken.

Chicken Turtle provides tools (CLI) for developing Python 3 projects.

Chicken Turtle is pre-alpha. None of the interface is stable, i.e. it may
change in the future.

## ct-mkproject
See `ct-mkproject --help`

## ct-mksetup

Your project should adhere to the following minimal structure (can be created
with `ct-mkproject`):

    $project_name
      __init__.py
      version.py
    project.py

Your source goes in `$project_name`. Use `project.py` to configure
`ct-mksetup`. Package data can be added by adding a `data` directory without an
`__init__.py` to the package in the `$project_name` tree. 

Run `ct-mksetup` to generate/update `setup.py`.


## Methodology

Tests must be placed in $project_name.test or subpackages. Tests are run with
py.test from the project root.

Package data can be provided by placing a directory named `data` in the package
with the data files, but no `__init__.py` as that would turn the data directory
into a package.

## Old notes (TODO rm)
- venv_create.sh: create a virtual environment corresponding to setup.py. If
  requirements.txt exists, that list of packages will be installed. If
  extra_requirements.txt exists (corresponding to the extra dependencies in
  setup.py), these will also be installed. Then setup.py's deps are installed,
  without upgrading any other packages. 
- interpreter.sh: start an interpreter inside the virtual environment, ensuring
  the project source is in the PYTHONPATH and start an interactive session in
  which interpreter.py is first executed.
- test data should be placed in test/data
- output of last test runs is kept in test/last_runs 
- run_tests.py to run the tests, but you need to run it from withing the venv
  (i.e. `. venv/bin/activate` before running this)
