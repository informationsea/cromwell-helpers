#!/bin/bash

set -e

python3 -m venv dev
source dev/bin/activate
pip3 install -e .
pip3 install pyinstaller mypy flake8 pytest tox types-requests

echo "Run next command to enter development environment"
echo "source dev/bin/activate"
