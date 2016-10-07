Python 3 project development tools. Looks like a turtle, tastes like chicken.

Chicken Turtle Project (CTP) provides CLI tools for developing Python 3 projects.
It makes it easier to make quality commits and releases, through automating
what can be automated and by verifying manual work against quality requirements. 

Chicken Turtle Project is alpha. The interface may change in the future, but
has gained some stability.


Links
=====

- `Documentation <http://pythonhosted.org/chicken_turtle_project/>`_
- `PyPI <https://pypi.python.org/pypi/chicken_turtle_project/>`_
- `GitHub <https://github.com/timdiels/chicken_turtle_project/>`_


Changelist
==========

v2.3.0
------

- Fixed:

  - `ct-mkvenv` did not upgrade `pip`, `wheel` and `setuptools`
  - git pre-commit hook did not enter venv properly when running tests
  - added missing `numpy` requirement, an optional dependency of `networkx`
  - `requirements.in`: dependencies on extra requires (e.g.
    ``dependency[extra]``) failed

- Optimised:

  - `ct-mkvenv` reruns are faster

- Added or enhanced: 
  
  - when `CT_NO_MKPROJECT` environment variable is set, `ct-mkproject` will
    exit immediately when called.

  - `--debug` option: more detailed messages on stdout. 

  - minimise changes in `setup.py` and `requirements.txt` (by sorting any lists)

- Changed: 

  - Terser and more readable messages on stdout

  - Generate API using `autosummary_generate` instead of `sphinx-apidoc`. 

  - if `pip`, `wheel` or `setuptools` is mentioned in a `requirements.in` file,
    it will also appear in `requirements.txt`, for the rare cases where you need
    to constrain one of them.

  - ct-mkvenv: dependencies no longer installed in the order they are specified
    in requirements.txt

- Removed: 
  
  - ``ct-mkvenv --no-mkproject``: instead, use ``CT_NO_MKPROJECT=y ct-mkvenv``.

v2.2.0
------

- Changed: user friendlier error messages
- Added:

  - `project.py::python_version`\ : allows specifying which Python version to use
    for the venv and testing
  - ``ct-mkvenv --no-mkproject``: run without first calling `ct-mkproject`
  
- Fixed: the project's package was missing from venv after each commit. The
  venv wasn't restored properly after a pre-commit.  


v2.1.2
------

- Changed: expect tests in ``your_pkg.tests`` instead of ``your_pkg.test``
- Added:

  - `project.py::package_name`\ : allows package name and PyPI/index name to be different 
  - `project.py::pre_commit_no_ignore`\ : files not to ignore in precommit checks,
    despite them not being tracked by git. 

v2.0.4
------
No changelist

