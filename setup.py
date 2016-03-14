# Auto generated by ct-mksetup
# Do not edit this file, edit ./project.py instead

from setuptools import setup
setup(
    **{   'author': 'Tim Diels',
    'author_email': 'timdiels.m@gmail.com',
    'classifiers': [   'Natural Language :: English',
                       'Intended Audience :: Developers',
                       'Development Status :: 2 - Pre-Alpha',
                       'Topic :: Software Development',
                       'Operating System :: POSIX',
                       'Operating System :: POSIX :: AIX',
                       'Operating System :: POSIX :: BSD',
                       'Operating System :: POSIX :: BSD :: BSD/OS',
                       'Operating System :: POSIX :: BSD :: FreeBSD',
                       'Operating System :: POSIX :: BSD :: NetBSD',
                       'Operating System :: POSIX :: BSD :: OpenBSD',
                       'Operating System :: POSIX :: GNU Hurd',
                       'Operating System :: POSIX :: HP-UX',
                       'Operating System :: POSIX :: IRIX',
                       'Operating System :: POSIX :: Linux',
                       'Operating System :: POSIX :: Other',
                       'Operating System :: POSIX :: SCO',
                       'Operating System :: POSIX :: SunOS/Solaris',
                       'Operating System :: Unix',
                       'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
                       'Programming Language :: Python',
                       'Programming Language :: Python :: 3',
                       'Programming Language :: Python :: 3 :: Only',
                       'Programming Language :: Python :: 3.2',
                       'Programming Language :: Python :: 3.3',
                       'Programming Language :: Python :: 3.4',
                       'Programming Language :: Python :: 3.5',
                       'Programming Language :: Python :: Implementation',
                       'Programming Language :: Python :: Implementation :: CPython',
                       'Programming Language :: Python :: Implementation :: Stackless'],
    'description': 'Python 3 project development tools',
    'entry_points': {   'console_scripts': [   'ct-mkproject = chicken_turtle_project.mkproject:main',
                                               'ct-mkvenv = chicken_turtle_project.mkvenv:main',
                                               'ct-release = chicken_turtle_project.release:main',
                                               'ct-interpreter = chicken_turtle_project.interpreter:main']},
    'install_requires': [   'chicken_turtle_util==1.0.0',
                            'click',
                            'plumbum',
                            'pypandoc',
                            'GitPython',
                            'pip-tools',
                            'checksumdir',
                            'versio',
                            'pytest',
                            'pytest-xdist',
                            'pytest-env',
                            'pytest-mock'],
    'keywords': 'development release setuptools tools',
    'license': 'LGPL3',
    'long_description': 'Python 3 project development tools. Looks like a turtle, tastes like\n'
                        'chicken.\n'
                        '\n'
                        'Chicken Turtle Project (CTP) provides CLI tools for developing Python 3\n'
                        'projects. It makes it easier to make quality commits and releases,\n'
                        'through automating what can be automated and by verifying manual work\n'
                        'against quality requirements.\n'
                        '\n'
                        'Chicken Turtle Project is pre-alpha. None of the interface is stable,\n'
                        'meaning it may change in the future.\n'
                        '\n'
                        'Usage\n'
                        '-----\n'
                        '\n'
                        'Getting started\n'
                        '~~~~~~~~~~~~~~~\n'
                        '\n'
                        "For a new project, run ``ct-project``. You'll be asked to name your\n"
                        'project and the project structure will be generated. For details on\n'
                        'which files are created and/or managed by ``ct-project``, see\n'
                        '``ct-project --help``.\n'
                        '\n'
                        '``ct-project`` can also be used on an existing project. The details on\n'
                        'which files are created and/or managed by ``ct-project`` should allow\n'
                        'you to restructure your project to match the structure expected by\n'
                        '``ct-project``.\n'
                        '\n'
                        'Project info\n'
                        '~~~~~~~~~~~~\n'
                        '\n'
                        'Instead of managing ``setup.py`` directly, you specify your project info\n'
                        'in ``project.py`` in a format that resembles setuptools.setup. When\n'
                        '``project.py`` does not exist, ``ct-mkproject`` will create a template\n'
                        'of it for you which includes documentation of the options.\n'
                        '\n'
                        'Project invariants\n'
                        '~~~~~~~~~~~~~~~~~~\n'
                        '\n'
                        'Having run ``ct-project`` once, you should never have to call it again.\n'
                        'It will have installed a git pre-commit hook (unless you already had\n'
                        'one) that ensures the project state is updated and valid.\n'
                        '\n'
                        'This ensures that all your (future) commits have a requirements.txt with\n'
                        'pinned versions, that are guaranteed to pass your tests when installed\n'
                        'in a fresh virtual env. It also guarantees a number of other things such\n'
                        'as the presence of a LICENSE.txt and a readme file, or an up-to-date\n'
                        '**version** field in your root package.\n'
                        '\n'
                        'Managing dependencies\n'
                        '~~~~~~~~~~~~~~~~~~~~~\n'
                        '\n'
                        'Dependencies should be listed in ``requirements.in``, which is an input\n'
                        'file to ``pip-compile``\n'
                        '(`pip-tools <https://github.com/nvie/pip-tools>`__). There is no\n'
                        'separate requirements file for test dependencies, install and test\n'
                        'dependencies should simply be lumped together; though you can separate\n'
                        'install and test dependencies in blocks with comment headers for\n'
                        'example.\n'
                        '\n'
                        "Some dependencies don't list their dependencies correctly,\n"
                        '``pip install scikit-learn`` fails with when scipy is not installed\n'
                        'instead of simply installing scipy first. install without scipy\n'
                        'installed. To get around such issues, add its dependencies to\n'
                        '``requirements.in`` before the misbehaving dependency. When ``X``\n'
                        'appears before ``Y`` in ``requirements.in`` it will be installed before\n'
                        '``Y`` (unless ``Y`` is a dependency of ``X``).\n'
                        '\n'
                        'Testing\n'
                        '~~~~~~~\n'
                        '\n'
                        'Tests must be placed in ``$project_name.test`` or a sub-package thereof.\n'
                        'By default, tests are run with py.test from the project root from within\n'
                        'a ``venv``. To change this behaviour, edit ``./deploy_local``. To run\n'
                        'the tests, call ``./deploy_local``.\n'
                        '\n'
                        'Releasing to Python indices\n'
                        '~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
                        '\n'
                        'To release your project to a Python index (e.g. PyPI, devpi), use\n'
                        '``ct-release``. This ensures releases are made correctly. Simply call\n'
                        '``ct-release --project-version VERSION`` with the version you want to\n'
                        'release. ``ct-release`` will first validate the project before trying to\n'
                        'release it. Then it sets the version in the relevant files, adds a\n'
                        'commit, tags it with the version, releases the project to a test index\n'
                        'and a production and finally pushes all commits in the working\n'
                        'directory.\n'
                        '\n'
                        'Versions should adhere to\n'
                        '`PEP-0440 <https://www.python.org/dev/peps/pep-0440/>`__ and use\n'
                        '`semantic\n'
                        'versioning '
                        '<https://python-packaging-user-guide.readthedocs.org/en/latest/distributing/#semantic-versioning-preferred>`__.\n'
                        'Versions are only set on release commits made by ``ct-release``. At any\n'
                        "other time, setup.py's version is 0.0.0. If you need to refer to a\n"
                        "specific unreleased commit, use the commit's id.\n"
                        '\n'
                        'Package data\n'
                        '~~~~~~~~~~~~\n'
                        '\n'
                        'Package data can be provided by placing a directory named ``data`` in\n'
                        'the package you want to add data to. The ``data`` directory should not\n'
                        'have a ``__init__.py`` (as direct descendant) as that would make it a\n'
                        'package instead of a data directory.\n'
                        '\n'
                        'Deployment\n'
                        '~~~~~~~~~~\n'
                        '\n'
                        'Chicken Turtle Project does not enforce a particular methodology for\n'
                        'deployments, but we recommend shell scripts for simple deployments as\n'
                        "they don't have dependencies (assuming you only deploy to unix-like\n"
                        'machines). If you need to do more complex work such as migrating data to\n'
                        'a new database structure, include a Python script and call it from the\n'
                        'shell script after having made the venv.\n'
                        '\n'
                        'Project decisions\n'
                        '-----------------\n'
                        '\n'
                        'Git stashing is not user-friendly and should not be relied upon.\n'
                        'Stashing only certain files or hunks can be done with ``git stash -p``\n'
                        "but that doesn't work for new files. ``git add`` and ``git add -i`` are\n"
                        'much friendlier. Other unfinished changes can be left behind on a\n'
                        'separate branch. (See also: `stack overflow\n'
                        'thread '
                        '<http://stackoverflow.com/questions/3040833/stash-only-one-file-out-of-multiple-files-that-have-changed-with-git>`__\n'
                        'and this `blog\n'
                        'post '
                        '<https://codingkilledthecat.wordpress.com/2012/04/27/git-stash-pop-considered-harmful/>`__)\n'
                        '\n'
                        'By consequence we must allow committing only part of the working\n'
                        'directory. We can still require a clean directory before release\n'
                        'however.\n'
                        '\n'
                        'See also\n'
                        '--------\n'
                        '\n'
                        'Python packaging recommendations:\n'
                        '\n'
                        '-  https://packaging.python.org/en/latest/distributing.html\n'
                        '-  https://github.com/pypa/sampleproject\n',
    'name': 'chicken-turtle-project',
    'package_data': {},
    'packages': ['chicken_turtle_project', 'chicken_turtle_project.test'],
    'url': 'https://github.com/timdiels/chicken_turtle_project',
    'version': '0.0.0'}
)
