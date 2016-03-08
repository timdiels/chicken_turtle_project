Python 3 project development tools. Looks like a turtle, tastes like chicken.

Chicken Turtle provides tools (CLI) for developing Python 3 projects.

Chicken Turtle is pre-alpha. None of the interface is stable, i.e. it may
change in the future.

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

When making dependency in requirements.in editable (e.g. -e path/to/setup_dir),
leave the original dependency as a comment so you remember the previous version
constraint when you change it back at release (though you likely need to
require the version with the changes you made)

Versions should adhere to [PEP-0440](https://www.python.org/dev/peps/pep-0440/)
and use [semantic versioning](https://python-packaging-user-guide.readthedocs.org/en/latest/distributing/#semantic-versioning-preferred).
Versions are only set on release, via an argument to `ct-release`. `ct-release`
then adjusts `setup.py` with the new version, commits and tags the commit with
its version (prefixed with 'v'). At all other times, the version in `setup.py`
is set to `0.0.0`, use commit ids instead of versions in this case.

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
