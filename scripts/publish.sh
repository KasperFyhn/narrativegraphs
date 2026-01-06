#!/bin/bash

set -e

rm dist/*

./scripts/build.sh

python3 -m twine upload --repository testpypi dist/*