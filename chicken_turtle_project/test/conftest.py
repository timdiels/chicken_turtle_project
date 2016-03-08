from signal import signal, SIGPIPE, SIG_DFL
from pathlib import Path
import os
import pytest

# http://stackoverflow.com/a/30091579/1031434
signal(SIGPIPE, SIG_DFL) # Ignore SIGPIPE

#
@pytest.fixture(scope='function')
def tmpcwd(request, tmpdir):
    '''
    Create temp dir make it the current working directory
    '''
    original_cwd = Path.cwd()
    os.chdir(str(tmpdir))
    request.addfinalizer(lambda: os.chdir(str(original_cwd)))
    return tmpdir