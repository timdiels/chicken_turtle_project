Python 3 project development tools. Looks like a turtle, tastes like chicken.

Chicken Turtle Project (CTP) provides CLI tools for developing Python 3 projects.
It makes it easier to make quality commits and releases, through automating
what can be automated and by verifying manual work against quality requirements. 

Chicken Turtle Project is alpha. The interface may change in the future, but
has gained some stability (far less changes than pre v2.1.0).


Links
=====

- `Documentation <http://pythonhosted.org/chicken_turtle_project/>`_
- `PyPI <https://pypi.python.org/pypi/chicken_turtle_project/>`_
- `GitHub <https://github.com/timdiels/chicken_turtle_project/>`_


Changelist
==========

v2.1.2
------

- Changed: expect tests in ``your_pkg.tests`` instead of ``your_pkg.test``
- Added:

  - `project.py:package_name`: allows package name and PyPI/index name to be different 
  - `project.py:pre_commit_no_ignore`: files not to ignore in precommit checks,
    despite them not being tracked by git. 

v2.0.4
------
No changelist

