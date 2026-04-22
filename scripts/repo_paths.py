from __future__ import annotations

import os
from pathlib import Path


def get_repo_root() -> Path:
    env_root = os.getenv("FAA_EXPERIMENT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


REPO_ROOT = get_repo_root()
DATASET_NAME = os.getenv("FAA_EXPERIMENT_DATASET", "v2604_100")


def get_dataset_dir(dataset_name: str | None = None) -> Path:
    return REPO_ROOT / "data" / (dataset_name or DATASET_NAME)


def get_results_dir(dataset_name: str | None = None) -> Path:
    return REPO_ROOT / "results" / (dataset_name or DATASET_NAME)
