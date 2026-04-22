"""
Build the historical 10-sample pilot dataset from a legacy local source tree.

This script is kept only for pilot-history traceability. It is not part of the
formal 100-sample reproduction flow described in README/REPRODUCE.

Expected legacy layout under `FAA_LEGACY_DATA_ROOT`:
- pairs/pilot.json
- cifp/FAACIFP18
- chart files referenced by `image_path` in `pilot.json`

Outputs are written to:
- data/pilot_10/charts/
- data/pilot_10/cifp/
- data/pilot_10/sample_manifest.json
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from scripts.repo_paths import REPO_ROOT


LEGACY_DATA_ROOT = Path(os.getenv("FAA_LEGACY_DATA_ROOT", REPO_ROOT / "data" / "preparation" / "legacy_pilot"))
PAIRS_FILE = LEGACY_DATA_ROOT / "pairs" / "pilot.json"
CIFP_SRC = LEGACY_DATA_ROOT / "cifp" / "FAACIFP18"
BASE_DIR = LEGACY_DATA_ROOT
OUT_DIR = REPO_ROOT / "data" / "pilot_10"
CHARTS_DIR = OUT_DIR / "charts"
CIFP_DIR = OUT_DIR / "cifp"

HOLDING_LEG_TYPES = {"HM", "HF", "HA"}
EXPLICIT_HOLDING_TYPES = {"HF", "HA"}


def main() -> None:
    with open(PAIRS_FILE, encoding="utf-8") as handle:
        pairs = json.load(handle)
    print(f"Loaded pilot pairs: {len(pairs)}")

    with_holding = []
    without_holding = []

    for pair in pairs:
        legs = pair["cifp"]["legs"]
        has_holding = any(leg["rt_type"].strip() in EXPLICIT_HOLDING_TYPES for leg in legs)
        pair["holding_required"] = has_holding
        if has_holding:
            with_holding.append(pair)
        else:
            without_holding.append(pair)

    print(f"Pilot pairs with explicit hold: {len(with_holding)}")
    print(f"Pilot pairs without explicit hold: {len(without_holding)}")

    selected = without_holding[:6] + with_holding[:4]
    if len(selected) != 10:
        raise ValueError(f"Expected 10 pilot samples, got {len(selected)}")

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    CIFP_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(CIFP_SRC, CIFP_DIR / "FAACIFP18")
    print(f"Copied CIFP to {CIFP_DIR / 'FAACIFP18'}")

    manifest = []
    print("\nSelected pilot samples:")
    print(f"{'No.':>3}  {'Hold':>5}  {'ID':<20}  {'Image'}")
    print("-" * 60)

    for index, pair in enumerate(selected, 1):
        img_src = BASE_DIR / pair["image_path"].replace("data\\", "").replace("data/", "")
        img_dst = CHARTS_DIR / img_src.name
        shutil.copy2(img_src, img_dst)

        flag = "YES" if pair["holding_required"] else "NO"
        print(f"{index:>3}  {flag:>5}  {pair['id']:<20}  {img_src.name}")

        ma_legs = [
            leg for leg in pair["cifp"]["legs"]
            if leg["rt_type"].strip() in HOLDING_LEG_TYPES or leg["trans_ident"].strip().startswith("M")
        ]

        manifest.append(
            {
                "id": pair["id"],
                "image": img_src.name,
                "airport": pair["cifp"]["airport"],
                "proc_ident": pair["cifp"]["proc_ident"],
                "holding_required": pair["holding_required"],
                "total_legs": len(pair["cifp"]["legs"]),
                "ma_holding_legs": [
                    {"rt_type": leg["rt_type"].strip(), "wpt_ident": leg["wpt_ident"].strip()}
                    for leg in ma_legs
                ],
            }
        )

    manifest_path = OUT_DIR / "sample_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)

    print(f"\nPilot dataset completed: {len(manifest)} samples")
    print(f"Without explicit hold: {sum(1 for item in manifest if not item['holding_required'])}")
    print(f"With explicit hold: {sum(1 for item in manifest if item['holding_required'])}")
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
