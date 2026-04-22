"""Check all SUSAP subsections present for KABE and other sample airports."""
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from repo_paths import get_dataset_dir

CIFP_FILE = get_dataset_dir("v2604_100") / "cifp" / "FAACIFP18"

target_airports = {"KAAT", "KABE", "KABI", "KAAA", "KAAF"}

print("All SUSAP records for sample airports:\n")

with open(CIFP_FILE, "r", encoding="latin-1") as f:
    for line in f:
        if not line.startswith("SUSAP"):
            continue
        airport = line[6:10].strip()
        if airport not in target_airports:
            continue
        print(repr(line[:90]))
