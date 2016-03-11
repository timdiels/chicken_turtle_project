Python 3 project development tools. Looks like a turtle, tastes like chicken.

Chicken Turtle Project provides tools (CLI) for developing Python 3 projects.

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
the project state is updated and valid.

This ensures that all your (future) commits have a requirements.txt with pinned
versions, that are guaranteed to pass your tests when installed in a fresh
virtual env. It also guarantees a number of other things such as the presence
of a LICENSE.txt and a readme file, or an up-to-date __version__ field in your
root package.

### Managing dependencies

Dependencies should be listed in `requirements.in`, which is an input file to
`pip-compile` ([pip-tools](https://github.com/nvie/pip-tools)).
There is no separate requirements file for test dependencies, install and test
dependencies should simply be lumped together; though you can separate install and
test dependencies in blocks with comment headers for example.

Some dependencies don't list their dependencies correctly, `pip install
scikit-learn` fails with when scipy is not installed instead of simply
installing scipy first.  install without scipy installed. To get around such
issues, add its dependencies to `requirements.in` before the misbehaving
dependency. When `X` appears before `Y` in `requirements.in` it will be
installed before `Y` (unless `Y` is a dependency of `X`).

### Testing

Tests must be placed in `$project_name.test` or a sub-package thereof. By
default, tests are run with py.test from the project root from within a `venv`.
To change this behaviour, edit `./deploy_local`. To run the tests, call
`./deploy_local`.

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

### Package data

Package data can be provided by placing a directory named `data` in the package
you want to add data to. The `data` directory should not have a `__init__.py`
(as direct descendant) as that would make it a package instead of a data
directory.

### Deployment

Chicken Turtle Project does not enforce a particular methodology for deployments, but
we recommend shell scripts for simple deployments as they don't have dependencies
(assuming you only deploy to unix-like machines). If you need to do more
complex work such as migrating data to a new database structure, include a
Python script and call it from the shell script after having made the venv.

## Project decisions

Git stashing is not user-friendly and should not be relied upon. Stashing only
certain files or hunks can be done with `git stash -p` but that doesn't work
for new files. `git add` and `git add -i` are much friendlier. Other unfinished
changes can be left behind on a separate branch. (See also: 
[stack overflow thread](http://stackoverflow.com/questions/3040833/stash-only-one-file-out-of-multiple-files-that-have-changed-with-git)
and this [blog post](https://codingkilledthecat.wordpress.com/2012/04/27/git-stash-pop-considered-harmful/))

By consequence we must allow committing only part of the working directory. We
can still require a clean directory before release however.

## See also

Python packaging recommendations:

- https://packaging.python.org/en/latest/distributing.html
- https://github.com/pypa/sampleproject
