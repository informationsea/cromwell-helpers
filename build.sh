#!/bin/bash

set -ex

if [ -d build ]; then
    rm -rf build
fi

python3 -m venv build/dist-env
source build/dist-env/bin/activate
pip3 install -e .
pip3 install pyinstaller mypy flake8 tox types-requests

# check
mypy -p cromwellhelper
#flake8 cromwellhelper
tox

pushd build
pyinstaller --distpath cromwellhelper --name cromwell-cli ../cromwellhelper/cromwell_cli/__main__.py
pyinstaller --distpath cromwellhelper --name docker ../cromwellhelper/fakedocker.py
pyinstaller --distpath cromwellhelper --name grid ../cromwellhelper/grid.py
cp ../README.md cromwellhelper
zip -r cromwellhelper.zip cromwellhelper
popd
