OUTPUT_DIR = "output"

DB_PATH = "output/lotr.db"
INPUT_GLOB = "input/*.txt"
SECTION_SPLIT_PATTERN = r"(?<=\S)\n\n(?=\S)|\n{3}"

# Graph filter
MIN_NODE_FREQUENCY = 2

# PMI threshold for k-clique edge filtering
MIN_WEIGHT = 2.5

# K-clique community detection
K_CLIQUE_K = 4

# Louvain community detection
LOUVAIN_RESOLUTION = 35

# Pickle cache for computed communities (delete to recompute)
COMMUNITIES_CACHE_PATH = "output/communities.pkl"
