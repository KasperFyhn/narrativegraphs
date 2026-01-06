#!/bin/bash
# Quick frontend rebuild for testing the production build locally

set -e

cd visualizer
npm run build
cd ..
cp -r visualizer/build narrativegraph/server/static
echo "✓ Frontend rebuilt and copied to narrativegraph/server/static/"