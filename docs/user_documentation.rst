User documentation
==================

Getting started
---------------

For a new project, run ``ct-mkproject``. You'll be prompted for information and the
project structure will be generated. For details on which files are created and/or
managed by `ct-mkproject`, see ``ct-mkproject --help``.

`ct-mkproject` can also be used on an existing project, though you may want to
restructure your project structure according to the one expected by
`ct-mkproject` (see ``ct-mkproject --help``)


Project info
------------

Instead of managing `setup.py` directly, you specify your project info in
`project.py` in a format that resembles `setuptools.setup`. When `project.py`
does not exist, `ct-mkproject` will create a template of it for you, which
includes documentation of the options.


Project invariants
------------------

Having run `ct-mkproject` once, you will never have to call it again. It will
have installed a git pre-commit hook that ensures the project state is up to
date and valid at each commit.

This ensures that for all of your (future) commits:

- there are no errors in the documentation (i.e. sphinx-build encounters no
  errors or warnings)
- there is a `LICENSE.txt`, a README file, ...
- the version is up to date across the project

Further, it is guaranteed that any release commit can be checked out and having
run `ct-mkvenv`, all tests will succeed. This also holds for non-release commits
with no editable requirements.  (editable requirements cannot be pinned in
`requirements.txt`, so when you later revisit such a commit, the editable
requirement may have changed (e.g. an amended commit)).


Managing dependencies
---------------------

Required dependencies should be listed in `requirements.in`, optional
dependencies should be listed in ``${name}_requirements.in``. A `requirements.txt` file
will be generated from these files using `pip-compile`
(`pip-tools <https://github.com/nvie/pip-tools>`_), containing both required and
optional dependencies. Required dependencies will appear in `setup.py`\ 's
`install_requires`. Optional dependencies will appear in `extras_require` with
``$name`` as key, e.g. `test_requirements.in` corresponds to
``extras_require['test']``.


Package data
------------

Package data can be provided by placing a directory named `data` in the package
you want to add data to. The `data` directory should not have a `__init__.py`
(as direct descendant) as that would make it a package instead of a data
directory.

You can then access this data (regardless of whether and how the project is
installed) using `pkg_resources <https://pythonhosted.org/setuptools/pkg_resources.html#basic-resource-access>`_.


Testing
-------

Tests must be placed in ``$package_name.tests`` or a sub-package thereof. Tests are
run from within the venv using `py.test`. To enter the venv, run ``. venv/bin/activate``.

To get a coverage report, run: ``py.test --cov=$your_project_name``.


Documenting
-----------

Sphinx is used to generate documentation. `ct-mkproject` generates a `docs`
directory containing the source of the documentation of the project.  Running
``ct-mkdoc`` compiles the documentation to html, which can be viewed at
`docs/build/html`.


Releasing to Python indices
---------------------------

To release your project to a Python index (e.g. PyPI, devpi), use `ct-release`.
This ensures releases are made correctly. Simply call ``ct-release
VERSION`` with the version you want to release.
`ct-release` will first validate the project and build the documentation before
trying to release it.  Then it sets the version in the relevant files, adds a
commit, tags it with the version, releases the project to a test index and
finally it releases to the production index and pushes all commits in the
working directory.

Versions should adhere to `PEP-0440 <https://www.python.org/dev/peps/pep-0440/>`_
and use `semantic versioning <https://python-packaging-user-guide.readthedocs.org/en/latest/distributing/#semantic-versioning-preferred>`_.
Versions are only set on release commits made by `ct-release`. At any other
time, `setup.py`\ 's version is ``0.0.0``. If you need to refer to a specific
unreleased commit, use the commit's id instead.


Deployment
----------

Chicken Turtle Project does not enforce a particular methodology for deployments, but
we recommend shell scripts for simple deployments as they don't have dependencies
(assuming you only deploy to unix-like machines). If you need to do more
complex work such as migrating data to a new database structure, include a
Python script and call it from the shell script after having made the venv.


See also
--------

Python packaging recommendations:

- https://packaging.python.org/en/latest/distributing.html
- https://github.com/pypa/sampleproject

