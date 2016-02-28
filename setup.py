from pathlib import Path
here = Path(__file__).parent

import sys
sys.path.append(str(here / 'chicken_turtle_project'))

from chicken_turtle.setuptools import setup

# setup
setup(
    # custom attrs
    here=here,
    readme_file='readme.md',
    
    # overridden
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    # Note: you must add ancestors of any applicable classifier too
    classifiers='''
        Natural Language :: English
        Intended Audience :: Developers
        Development Status :: 2 - Pre-Alpha
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
    description="Python 3 project development tools",
    author='Tim Diels',
    author_email='timdiels.m@gmail.com',
 
    url='https://github.com/timdiels/chicken_turtle_project', # project homepage
  
    license='LGPL3',
     
    # What does your project relate to?
    keywords='',
  
    # Required dependencies
    install_requires='pytest chicken_turtle_util'.split(),
  
    # Optional dependencies
    extras_require={
        'dev': ['pypandoc'],
        'test': [],
    },
)