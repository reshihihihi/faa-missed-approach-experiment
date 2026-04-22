"""Analyze actual byte positions in CIFP records for KAAT approach (BACHS24)."""
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from repo_paths import get_dataset_dir

CIFP_FILE = get_dataset_dir("v2604_100") / "cifp" / "FAACIFP18"

lines_found = []
with open(CIFP_FILE, "r", encoding="latin-1") as f:
    for line in f:
        if line.startswith("SUSAP") and "KAAT" in line[6:10] and "BACHS" in line[10:20]:
            lines_found.append(line.rstrip())

print(f"Found {len(lines_found)} KAAT/BACHS approach records\n")
for line in lines_found[:10]:
    print(f"Line: {repr(line[:90])}")
    print(f"  [0:5]={repr(line[0:5])} [5]={repr(line[5])} [6:10]={repr(line[6:10])} [10:12]={repr(line[10:12])} [12]={repr(line[12])}")
    print(f"  [13:18]={repr(line[13:18])} [18:20]={repr(line[18:20])} [20:25]={repr(line[20:25])} [25:26]={repr(line[25:26])} [26:29]={repr(line[26:29])}")
    print(f"  [29:34]={repr(line[29:34])} [38]={repr(line[38]) if len(line)>38 else '?'} [43]={repr(line[43]) if len(line)>43 else '?'} [47:50]={repr(line[47:50]) if len(line)>50 else '?'}")
    print()

# Now find records with proc_ident R31 at various offsets
print("\n--- Searching for R31 approach at KAAT ---")
with open(CIFP_FILE, "r", encoding="latin-1") as f:
    for line in f:
        if not line.startswith("SUSAP"):
            continue
        airport = line[6:10]
        if airport != "KAAT":
            continue
        # Try different proc_ident offsets
        subsec = line[12]  # D = approach
        if subsec == "D":
            proc13 = line[13:18].strip()
            print(f"subsec=D proc[13:18]={proc13!r:10s} trans[20:25]={line[20:25].strip()!r:8s} seq[26:29]={line[26:29].strip()!r:5s} line[:50]={line[:50]!r}")
