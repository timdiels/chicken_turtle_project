project = dict(
    readme_file='README.rst',
    
    # overridden
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    # Note: you must add ancestors of any applicable classifier too
    classifiers='''
        Natural Language :: English
        Intended Audience :: Developers
        Development Status :: 3 - Alpha
        Topic :: Software Development
        Operating System :: POSIX
        Operating System :: POSIX :: AIX
        Operating System :: POSIX :: BSD
        Operating System :: POSIX :: BSD :: BSD/OS
        Operating System :: POSIX :: BSD :: FreeBSD
        Operating System :: POSIX :: BSD :: NetBSD
        Operating System :: POSIX :: BSD :: OpenBSD
        Operating System :: POSIX :: GNU Hurd
        Operating System :: POSIX :: HP-UX
        Operating System :: POSIX :: IRIX
        Operating System :: POSIX :: Linux
        Operating System :: POSIX :: Other
        Operating System :: POSIX :: SCO
        Operating System :: POSIX :: SunOS/Solaris
        Operating System :: Unix
        License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)
        Programming Language :: Python
        Programming Language :: Python :: 3
        Programming Language :: Python :: 3 :: Only
        Programming Language :: Python :: 3.2
        Programming Language :: Python :: 3.3
        Programming Language :: Python :: 3.4
        Programming Language :: Python :: 3.5
        Programming Language :: Python :: Implementation
        Programming Language :: Python :: Implementation :: CPython
        Programming Language :: Python :: Implementation :: Stackless
    ''',
    
    # standard
    name='chicken_turtle_project',
    package_name='chicken_turtle_project',
    human_friendly_name='Chicken Turtle Project',
    python_version=(3,4),
    description="Python 3 project development tools",
    author='Tim Diels',
    author_email='timdiels.m@gmail.com',
    license='LGPL3',
    url='https://github.com/timdiels/chicken_turtle_project', # project homepage
    download_url='https://github.com/timdiels/chicken_turtle_project/releases/v{version}.tar.gz',
    index_test='pypitest',
    index_production='pypi',
     
    # What does your project relate to?
    keywords='development release setuptools tools',
    
    # Auto generate entry points
    entry_points={
        'console_scripts': [
            'ct-mkproject = chicken_turtle_project.mkproject:main',
            'ct-mkvenv = chicken_turtle_project.mkvenv:main',
            'ct-release = chicken_turtle_project.release:main',
            'ct-mkdoc = chicken_turtle_project.mkdoc:main',
            'ct-pre-commit-hook = chicken_turtle_project.pre_commit_hook:main',
        ],
    },
)
