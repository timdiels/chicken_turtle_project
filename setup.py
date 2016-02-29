# Manually written setup.py
from setuptools import setup

setup(
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
    install_requires='pytest'.split(),
  
    # Optional dependencies
    extras_require={
        'dev': [],
        'test': [],
    },
    
    # Auto generate entry points
    entry_points={
        'console_scripts': [
            'ct-mksetup = chicken_turtle_project.mksetup:main',
            'ct-mkproject = chicken_turtle_project.mkproject:main',
        ],
    },
)