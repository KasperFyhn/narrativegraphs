import sys
from typing import Literal

CONFIGS = {
    "lotr": {
        "COMMUNITIES_CACHE_PATH": "output/lotr/communities.pkl",
        "DOCS_PATH": "input/lotr_docs.jsonl",
        # Model
        "COREF": None,
        "N_CPU": 1,
        # Community detection
        "MIN_NODE_FREQUENCY": 2,
        "MIN_WEIGHT": 2.5,
        "K_CLIQUE_K": 4,
        "LOUVAIN_RESOLUTION": 35,
    },
    "lotr_coref": {
        "COMMUNITIES_CACHE_PATH": "output/lotr/communities.pkl",
        "DOCS_PATH": "input/lotr_docs.jsonl",
        # Model
        "COREF": "fastcoref",
        "N_CPU": 1,
        # Community detection
        "MIN_NODE_FREQUENCY": 2,
        "MIN_WEIGHT": 3.5,
        "K_CLIQUE_K": 4,
        "LOUVAIN_RESOLUTION": 35,
    },
    "chatgpt_reddit": {
        "COMMUNITIES_CACHE_PATH": "output/chatgpt_reddit/communities.pkl",
        "DOCS_PATH": "input/chatgpt_reddit_docs.jsonl",
        # Data preparation
        "INPUT_GLOB": "input/chatgpt-reddit-comments.jsonl",
        "SECTION_SPLIT_PATTERN": None,
        # Model
        "N_CPU": -1,
        # Community detection
        "MIN_NODE_FREQUENCY": 2,
        "MIN_WEIGHT": 2.5,
        "K_CLIQUE_K": 4,
        "LOUVAIN_RESOLUTION": 35,
    },
}


def _parse_config_name() -> str:
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--config" and i + 2 < len(sys.argv):
            return sys.argv[i + 2]
        if arg.startswith("--config="):
            return arg.split("=", 1)[1]
    raise ValueError("invalid config name")


name = _parse_config_name()
_cfg = CONFIGS[name]

OUTPUT_DIR: str = f"output/{name}"
DB_PATH: str = OUTPUT_DIR + f"/{name}.db"
COMMUNITIES_CACHE_PATH: str = OUTPUT_DIR + "/communities.pkl"
DOCS_PATH: str = _cfg["DOCS_PATH"]
COREF: Literal["fastcoref"] | None = _cfg["COREF"]
N_CPU: int = _cfg["N_CPU"]
MIN_NODE_FREQUENCY: int = _cfg["MIN_NODE_FREQUENCY"]
MIN_WEIGHT: float = _cfg["MIN_WEIGHT"]
K_CLIQUE_K: int = _cfg["K_CLIQUE_K"]
LOUVAIN_RESOLUTION: int = _cfg["LOUVAIN_RESOLUTION"]
