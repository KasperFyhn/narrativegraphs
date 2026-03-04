#!/bin/bash
set -e
cd "$(dirname "$0")"

python 01_build_graph.py
python 02_entity_distribution.py
python 03_pmi_analysis.py
python 04_community_detection.py
python 05_community_comparison.py
python 06_typology_analysis.py
python 07_explore_communities.py
