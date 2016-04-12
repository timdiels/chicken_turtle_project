# http://stackoverflow.com/a/30091579/1031434
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL) # Ignore SIGPIPE

from pathlib import Path
import os
import pytest

# TODO is CTU.test.temp_dir_cwd
@pytest.yield_fixture()
def tmpcwd(tmpdir):
    '''
    Create temp dir make it the current working directory
    '''
    original_cwd = Path.cwd()
    os.chdir(str(tmpdir))
    yield tmpdir
    os.chdir(str(original_cwd))
    