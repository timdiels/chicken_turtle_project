'''
- simple: simple project, nothing funky going on
- missing_dep: project with a dep that omits a dep, but project fixes it by including the missing dep in its own dependencies
- sip_dep: project with a dependency that uses sip, e.g. PyQt5

for each, check that:
- venv/bin/testproject runs and can import relevant dependencies
'''