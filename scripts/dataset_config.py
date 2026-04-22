from pathlib import Path

DATASET_NAME = "v2604_100"
DATASET_DIR = Path(f"e:/experiment/data/{DATASET_NAME}")
RESULTS_DIR = Path(f"e:/experiment/results/{DATASET_NAME}")

MANIFEST_PATH = DATASET_DIR / "sample_manifest_100.json"
PAIRS_PATH = DATASET_DIR / "pairs_100.json"
CHARTS_DIR = DATASET_DIR / "charts"
CIFP_PATH = DATASET_DIR / "cifp" / "FAACIFP18"
PROMPTS_DIR = Path("e:/experiment/prompts")
