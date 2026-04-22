from repo_paths import DATASET_NAME, REPO_ROOT, get_dataset_dir, get_results_dir

DATASET_DIR = get_dataset_dir(DATASET_NAME)
RESULTS_DIR = get_results_dir(DATASET_NAME)

MANIFEST_PATH = DATASET_DIR / "sample_manifest_100.json"
PAIRS_PATH = DATASET_DIR / "pairs_100.json"
CHARTS_DIR = DATASET_DIR / "charts"
CIFP_PATH = DATASET_DIR / "cifp" / "FAACIFP18"
PROMPTS_DIR = REPO_ROOT / "prompts"
