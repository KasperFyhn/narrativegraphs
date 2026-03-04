import sys

CONFIGS = {
    "lotr": {
        "OUTPUT_DIR": "output/lotr",
        "DB_PATH": "output/lotr/lotr.db",
        "COMMUNITIES_CACHE_PATH": "output/lotr/communities.pkl",
        "DOCS_PATH": "input/lotr_docs.jsonl",
        # Data preparation
        "INPUT_GLOB": "input/*.txt",
        "SECTION_SPLIT_PATTERN": r"(?<=\S)\n\n(?=\S)|\n{3}",
        # Model
        "N_CPU": 1,
        # Community detection
        "MIN_NODE_FREQUENCY": 2,
        "MIN_WEIGHT": 2.5,
        "K_CLIQUE_K": 4,
        "LOUVAIN_RESOLUTION": 35,
    },
    "chatgpt_reddit": {
        "OUTPUT_DIR": "output/chatgpt_reddit",
        "DB_PATH": "output/chatgpt_reddit/chatgpt_reddit.db",
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
    return "lotr"


_cfg = CONFIGS[_parse_config_name()]

OUTPUT_DIR: str = _cfg["OUTPUT_DIR"]
DB_PATH: str = _cfg["DB_PATH"]
COMMUNITIES_CACHE_PATH: str = _cfg["COMMUNITIES_CACHE_PATH"]
DOCS_PATH: str = _cfg["DOCS_PATH"]
INPUT_GLOB: str = _cfg["INPUT_GLOB"]
SECTION_SPLIT_PATTERN: str | None = _cfg["SECTION_SPLIT_PATTERN"]
N_CPU: int = _cfg["N_CPU"]
MIN_NODE_FREQUENCY: int = _cfg["MIN_NODE_FREQUENCY"]
MIN_WEIGHT: float = _cfg["MIN_WEIGHT"]
K_CLIQUE_K: int = _cfg["K_CLIQUE_K"]
LOUVAIN_RESOLUTION: int = _cfg["LOUVAIN_RESOLUTION"]
