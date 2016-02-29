#!/bin/sh
set -e

ct-mksetup
ct-mkvenv -e
venv/bin/py.test