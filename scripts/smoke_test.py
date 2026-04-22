from __future__ import annotations

import json
from pathlib import Path

from repo_paths import DATASET_NAME, REPO_ROOT, get_dataset_dir, get_results_dir


def require(path: Path, message: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{message}: {path}")


def main() -> None:
    dataset_dir = get_dataset_dir(DATASET_NAME)
    results_dir = get_results_dir(DATASET_NAME)
    manifest_path = dataset_dir / "sample_manifest_100.json"
    pairs_path = dataset_dir / "pairs_100.json"

    require(REPO_ROOT / "README.md", "Missing repository README")
    require(REPO_ROOT / "REPRODUCE.md", "Missing reproduction guide")
    require(manifest_path, "Missing formal manifest")
    require(pairs_path, "Missing committed pairs metadata")
    require(REPO_ROOT / "scripts" / "dataset_config.py", "Missing dataset config")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pairs = json.loads(pairs_path.read_text(encoding="utf-8"))
    if len(manifest) != 100:
        raise ValueError(f"Expected 100 manifest entries, got {len(manifest)}")
    if len(pairs) != 100:
        raise ValueError(f"Expected 100 pair entries, got {len(pairs)}")

    path_ids = {entry["id"] for entry in manifest}
    pair_ids = {entry["id"] for entry in pairs}
    if path_ids != pair_ids:
        missing_in_pairs = sorted(path_ids - pair_ids)[:10]
        missing_in_manifest = sorted(pair_ids - path_ids)[:10]
        raise ValueError(
            f"Manifest/pairs mismatch. Missing in pairs: {missing_in_pairs}; missing in manifest: {missing_in_manifest}"
        )

    print(f"Repository root: {REPO_ROOT}")
    print(f"Dataset: {DATASET_NAME}")
    print(f"Manifest entries: {len(manifest)}")
    print(f"Pair entries: {len(pairs)}")
    print(f"Results directory: {results_dir}")
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
