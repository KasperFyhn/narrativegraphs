#!/bin/bash

set -e

echo "Building React frontend..."
cd visualizer
npm install
npm run build

echo "Copying static files to package..."
cd ..

rm -rf narrativegraph/server/static
cp -r visualizer/build narrativegraph/server/static

echo "Building Python package..."
python -m build

echo "Done! Package ready in dist/"