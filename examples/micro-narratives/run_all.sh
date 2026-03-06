#!/bin/bash
set -e
set -o xtrace

cd "$(dirname "$0")"

CONFIG=${1}

python 01_build_graph.py         --config "$CONFIG"
python 02_entity_distribution.py --config "$CONFIG"
python 03_pmi_analysis.py        --config "$CONFIG"
python 04_community_detection.py --config "$CONFIG"
python 05_community_comparison.py --config "$CONFIG"
python 06_typology_analysis.py   --config "$CONFIG"
