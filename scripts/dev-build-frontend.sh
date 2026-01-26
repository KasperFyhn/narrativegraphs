#!/bin/bash
# Quick frontend rebuild for testing the production build locally

set -e

cd visualizer
npm run build
cd ..
cp -r visualizer/build narrativegraphs/server/static
echo "✓ Frontend rebuilt and copied to narrativegraphs/server/static/"