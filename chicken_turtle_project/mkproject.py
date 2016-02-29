def main():
    '''Create or update existing project to match the latest Chicken Turtle project structure.
    
    The following files are created if missing:
    - project.py
    - $project_name package
    - $project_name/version.py
    - $project_name/test package
    - requirements.in
    - .gitignore
    
    mkproject ensures certain patterns are part of .gitignore, but does not erase any patterns you added.
    
    Warnings are emitted if these files are missing:
    - LICENSE.txt
    - README.*
    '''
    # Determine whether existing or new
    