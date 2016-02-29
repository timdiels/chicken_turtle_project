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

## ct-mkvenv

See `ct-mkvenv --help`

## ct-interpreter

See `ct-interpreter --help`

## Deployment API

There's a single function that helps with very simple deployments.

## Methodology

Tests must be placed in $project_name.test or subpackages. Tests are run with
py.test from the project root.

Package data can be provided by placing a directory named `data` in the package
with the data files, but no `__init__.py` as that would turn the data directory
into a package.

Simply include test dependencies in install_requires.

`ct-mksetup` should be run before any commit and deployment. For the latter, call
`ct-mksetup` in your deploy scripts.

Chicken Turtle Project does not enforce a particular methodology for deployments, but
we recommend shell scripts for simple deployments as they don't have dependencies
(assuming you only deploy to unix-like machines). If you need to do more
complex work such as migrating data to a new database structure, include a
Python script and call it from the shell script after having made the venv.

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

## See also

Python packaging recommendations:

- https://packaging.python.org/en/latest/distributing.html
- https://github.com/pypa/sampleproject
