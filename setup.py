# Auto generated by ct-mksetup
# Do not edit this file, edit ./project.py instead

from setuptools import setup
setup(
    **{   'author': 'Tim Diels',
    'author_email': 'timdiels.m@gmail.com',
    'classifiers': [   'Development Status :: 3 - Alpha',
                       'Intended Audience :: Developers',
                       'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
                       'Natural Language :: English',
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
                       'Programming Language :: Python',
                       'Programming Language :: Python :: 3',
                       'Programming Language :: Python :: 3 :: Only',
                       'Programming Language :: Python :: 3.2',
                       'Programming Language :: Python :: 3.3',
                       'Programming Language :: Python :: 3.4',
                       'Programming Language :: Python :: 3.5',
                       'Programming Language :: Python :: Implementation',
                       'Programming Language :: Python :: Implementation :: CPython',
                       'Programming Language :: Python :: Implementation :: Stackless',
                       'Topic :: Software Development'],
    'description': 'Python 3 project development tools',
    'download_url': 'https://github.com/timdiels/chicken_turtle_project/releases/v2.3.0.tar.gz',
    'entry_points': {   'console_scripts': [   'ct-mkdoc = chicken_turtle_project.mkdoc:main',
                                               'ct-mkproject = chicken_turtle_project.mkproject:main',
                                               'ct-mkvenv = chicken_turtle_project.mkvenv:main',
                                               'ct-pre-commit-hook = chicken_turtle_project.pre_commit_hook:main',
                                               'ct-release = chicken_turtle_project.release:main']},
    'extras_require': {   'dev': ['numpydoc', 'sphinx', 'sphinx-rtd-theme'],
                          'test': [   'coverage-pth',
                                      'pytest',
                                      'pytest-cov',
                                      'pytest-env',
                                      'pytest-mock',
                                      'pytest-xdist']},
    'install_requires': [   'checksumdir',
                            'chicken-turtle-util==1.0.0',
                            'click',
                            'collections-extended',
                            'gitpython',
                            'more-itertools',
                            'numpy',
                            'pip-tools<1.7',
                            'pip<8.1.2',
                            'plumbum',
                            'pypandoc',
                            'versio'],
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
                        'Chicken Turtle Project is alpha. The interface may change in the future,\n'
                        'but has gained some stability.\n'
                        '\n'
                        'Links\n'
                        '=====\n'
                        '\n'
                        '-  `Documentation <http://pythonhosted.org/chicken_turtle_project/>`__\n'
                        '-  `PyPI <https://pypi.python.org/pypi/chicken_turtle_project/>`__\n'
                        '-  `GitHub <https://github.com/timdiels/chicken_turtle_project/>`__\n'
                        '\n'
                        'Changelist\n'
                        '==========\n'
                        '\n'
                        'v2.3.0\n'
                        '------\n'
                        '\n'
                        '-  Fixed:\n'
                        '\n'
                        '   -  ct-mkvenv did not upgrade pip, wheel and setuptools\n'
                        '   -  git pre-commit hook did not enter venv properly when running tests\n'
                        '   -  added missing numpy requirement, an optional dependency of\n'
                        '      networkx\n'
                        '   -  \\`requirements.in\\`: dependencies on extra requires (e.g.\n'
                        '      ``dependency[extra]``) failed\n'
                        '\n'
                        '-  Optimised:\n'
                        '\n'
                        '   -  ct-mkvenv reruns are faster\n'
                        '\n'
                        '-  Added or enhanced:\n'
                        '\n'
                        '   -  when CT\\_NO\\_MKPROJECT environment variable is set, ct-mkproject\n'
                        '      will exit immediately when called.\n'
                        '   -  --debug option: more detailed messages on stdout.\n'
                        '   -  minimise changes in setup.py and requirements.txt (by sorting any\n'
                        '      lists)\n'
                        '\n'
                        '-  Changed:\n'
                        '\n'
                        '   -  Terser and more readable messages on stdout\n'
                        '   -  Generate API using autosummary\\_generate instead of sphinx-apidoc.\n'
                        '   -  if pip, wheel or setuptools is mentioned in a requirements.in\n'
                        '      file, it will also appear in requirements.txt, for the rare cases\n'
                        '      where you need to constrain one of them.\n'
                        '   -  ct-mkvenv: dependencies no longer installed in the order they are\n'
                        '      specified in requirements.txt\n'
                        '\n'
                        '-  Removed:\n'
                        '\n'
                        '   -  ``ct-mkvenv --no-mkproject``: instead, use\n'
                        '      ``CT_NO_MKPROJECT=y ct-mkvenv``.\n'
                        '\n'
                        'v2.2.0\n'
                        '------\n'
                        '\n'
                        '-  Changed: user friendlier error messages\n'
                        '-  Added:\n'
                        '\n'
                        '   -  project.py::python\\_version: allows specifying which Python\n'
                        '      version to use for the venv and testing\n'
                        '   -  ``ct-mkvenv --no-mkproject``: run without first calling\n'
                        '      ct-mkproject\n'
                        '\n'
                        "-  Fixed: the project's package was missing from venv after each commit.\n"
                        "   The venv wasn't restored properly after a pre-commit.\n"
                        '\n'
                        'v2.1.2\n'
                        '------\n'
                        '\n'
                        '-  Changed: expect tests in ``your_pkg.tests`` instead of\n'
                        '   ``your_pkg.test``\n'
                        '-  Added:\n'
                        '\n'
                        '   -  project.py::package\\_name: allows package name and PyPI/index name\n'
                        '      to be different\n'
                        '   -  project.py::pre\\_commit\\_no\\_ignore: files not to ignore in\n'
                        '      precommit checks, despite them not being tracked by git.\n'
                        '\n'
                        'v2.0.4\n'
                        '------\n'
                        '\n'
                        'No changelist\n',
    'name': 'chicken_turtle_project',
    'package_data': {   'chicken_turtle_project': [   'data/Makefile',
                                                      'data/_templates/autosummary/module.rst',
                                                      'data/conf.py',
                                                      'data/index.rst']},
    'packages': ['chicken_turtle_project', 'chicken_turtle_project.tests'],
    'url': 'https://github.com/timdiels/chicken_turtle_project',
    'version': '2.3.0'}
)
