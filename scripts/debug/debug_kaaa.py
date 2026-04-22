"""Analyze KAAA/R03 record positions precisely."""
from pathlib import Path

CIFP_FILE = Path("e:/experiment/data/cifp/FAACIFP18")

print("KAAA / FR03 records:\n")
with open(CIFP_FILE, "r", encoding="latin-1") as f:
    for line in f:
        if not line.startswith("SUSAP"):
            continue
        airport = line[6:10].strip()
        if airport != "KAAA":
            continue
        subsec = line[12] if len(line) > 12 else ""
        if subsec != "F":
            continue
        proc13 = line[13:18]
        if proc13.strip() != "R03":
            continue

        # Analyze each field position
        trans19 = line[19:25]
        trans20 = line[20:26]
        seq26 = line[26:29]
        seq27 = line[27:30]
        cont38 = line[38] if len(line) > 38 else "?"
        turn43 = line[43] if len(line) > 43 else "?"
        rt47 = line[47:50] if len(line) > 50 else "?"
        wpt29 = line[29:34]

        print(f"  subsec={subsec!r} proc13:18={proc13!r} trans19:25={trans19!r} trans20:26={trans20!r} seq26:29={seq26!r} seq27:30={seq27!r}")
        print(f"  cont[38]={cont38!r} turn[43]={turn43!r} rt[47:50]={rt47!r} wpt[29:34]={wpt29!r}")
        print(f"  raw[:70]={line[:70]!r}")
        print()
