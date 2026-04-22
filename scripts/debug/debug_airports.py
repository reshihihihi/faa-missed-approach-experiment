"""Check all SUSAP subsections present for KABE and other sample airports."""
from pathlib import Path

CIFP_FILE = Path("e:/experiment/data/cifp/FAACIFP18")

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
