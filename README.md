Python 3 project development tools. Looks like a turtle, tastes like chicken.

Chicken Turtle Project (CTP) provides CLI tools for developing Python 3 projects.
It makes it easier to make quality commits and releases, through automating
what can be automated and by verifying manual work against quality requirements. 

Chicken Turtle Project is pre-alpha. None of the interface is stable, meaning
it may change in the future.

## Usage

### Getting started

For a new project, run `ct-project`. You'll be asked to name your project and the
project structure will be generated. For details on which files are created and/or
managed by `ct-project`, see `ct-project --help`.

`ct-project` can also be used on an existing project. The details on which
files are created and/or managed by `ct-project` should allow you to
restructure your project to match the structure expected by `ct-project`. 

### Project info

Instead of managing `setup.py` directly, you specify your project info in
`project.py` in a format that resembles setuptools.setup. When `project.py`
does not exist, `ct-mkproject` will create a template of it for you which
includes documentation of the options.

### Project invariants

Having run `ct-project` once, you should never have to call it again. It will
have installed a git pre-commit hook (unless you already had one) that ensures
the project state is up to date and valid at each commit.

This ensures that for all of your (future) commits:
- there is a requirements.txt with pinned versions for which all tests succeed in a virtual env
- there are no errors in the documentation (i.e. sphinx-build encounters no errors or warnings)
- there is a LICENSE.txt, a readme file, ...
- the version is up to date across the project

### Managing dependencies

Required dependencies should be listed in `requirements.in`, optional
dependencies should be listed in `${name}_requirements.in`. A `requirements.txt` file
will be generated from these files using `pip-compile`
([pip-tools](https://github.com/nvie/pip-tools)), containing both required and
optional dependencies. Required dependencies will appear in setuptools'
`install_requires`. Optional dependencies will appear in `extras_require` with
`$name` as key, e.g. `test_requirements.in` corresponds to
`extras_require['test']`.

If one of your dependencies fails to list its dependencies correctly, e.g. `pip
install scikit-learn` fails when scipy is not installed, you can add its
dependencies to `requirements.in` before the misbehaving dependency. When `X`
appears before `Y` in `requirements.in` it will be installed before `Y` (unless
`Y` is a dependency of `X`).

### Package data

Package data can be provided by placing a directory named `data` in the package
you want to add data to. The `data` directory should not have a `__init__.py`
(as direct descendant) as that would make it a package instead of a data
directory.

You can then access this data (regardless of whether and how the project is
installed) using `pkg_resources <https://pythonhosted.org/setuptools/pkg_resources.html#basic-resource-access>`_.

### Testing

Tests must be placed in `$project_name.test` or a sub-package thereof. Tests are
run from within the venv with `py.test`. To enter the venv, run `. venv/bin/activate`.

To get a coverage report, run: `py.test --cov=$your_project_name --testmon-off`.
If you forgot to add `--testmon-off`, run `rm .testmondata` to fix testmon.

### Documenting

Sphinx is used to generate documentation. `ct-mkproject` generates a `doc_src`
directory containing the source of the documentation of the project. API doc is
generated in `doc_src/api`. `index.rst` by default includes the API. The compiled
html documentation is placed in `doc/`. 

### Releasing to Python indices

To release your project to a Python index (e.g. PyPI, devpi), use `ct-release`.
This ensures releases are made correctly. Simply call `ct-release
--project-version VERSION` with the version you want to release.
`ct-release` will first validate the project before trying to release it.
Then it sets the version in the relevant files, adds a commit, tags it with the
version, releases the project to a test index and a production and finally
pushes all commits in the working directory.

Versions should adhere to [PEP-0440](https://www.python.org/dev/peps/pep-0440/)
and use [semantic versioning](https://python-packaging-user-guide.readthedocs.org/en/latest/distributing/#semantic-versioning-preferred).
Versions are only set on release commits made by `ct-release`. At any other
time, setup.py's version is 0.0.0. If you need to refer to a specific
unreleased commit, use the commit's id.

### Deployment

Chicken Turtle Project does not enforce a particular methodology for deployments, but
we recommend shell scripts for simple deployments as they don't have dependencies
(assuming you only deploy to unix-like machines). If you need to do more
complex work such as migrating data to a new database structure, include a
Python script and call it from the shell script after having made the venv.

## Developer guide

### Project decisions

Git stashing is not user-friendly and should not be relied upon. Stashing only
certain files or hunks can be done with `git stash -p` but that doesn't work
for new files. `git add` and `git add -i` are much friendlier. Other unfinished
changes can be left behind on a separate branch. (See also: 
[stack overflow thread](http://stackoverflow.com/questions/3040833/stash-only-one-file-out-of-multiple-files-that-have-changed-with-git)
and this [blog post](https://codingkilledthecat.wordpress.com/2012/04/27/git-stash-pop-considered-harmful/))

By consequence we must allow committing only part of the working directory. We
can still require a clean directory before release however.

Warn on a poorly formatted project name (underscores, upper case) instead of
raising an error. The project may already have been submitted and the index 
may not allow renaming the package (although PyPI allows it through a support
ticket).

SIP based packages are not installable from PyPI and the SIP team hasn't fixed
this.  Writing a setuptools package for SIP is non-trivial. This means we must
use their build process (configure, make, make install). Eggs and wheels don't
allow installing files in system directories. SIP based packages stick close
enough to non-system directories in a venv. We could make a setup.py with
`zip_safe=False` and put all files installed by `make install` in
`package_data`, then use `bdist_wheel` on it to create a binary
platform-dependent wheel. This is a bit more error-prone (e.g. a .so file
appearing in an unexpected place would break things) without much benefit as
these wheels probably can't be shared across machines. In order to support SIP
based packages, we install them without pip and reuse the dev venv in
pre-commits as to not incur the performance hit of waiting for a SIP package to
compile.

pytest-testmon is not compatible with pytest-xdist, --maxfail, --ff, --lf and
--cov to name a few. It sometimes misses changes that do cause test failures.
For these reasons, we default to using xdist instead of testmon. We may revisit
testmon once it supports xdist. You can still install and use --testmon
yourself, you probably shouldn't add --testmon to setup.cfg though as that would
allow for commits with failing tests.

## See also

Python packaging recommendations:

- https://packaging.python.org/en/latest/distributing.html
- https://github.com/pypa/sampleproject

