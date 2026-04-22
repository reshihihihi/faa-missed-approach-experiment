"""Cross-check pilot.json proc_ident vs CIFP proc_ident for all 10 samples."""
import json
import os
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from repo_paths import REPO_ROOT

LEGACY_DATA_ROOT = Path(os.getenv("FAA_LEGACY_DATA_ROOT", REPO_ROOT / "data" / "preparation" / "legacy_pilot"))
MANIFEST = REPO_ROOT / "data" / "pilot_10" / "sample_manifest.json"
PAIRS_FILE = LEGACY_DATA_ROOT / "pairs" / "pilot.json"
CIFP_FILE = REPO_ROOT / "data" / "pilot_10" / "cifp" / "FAACIFP18"

with open(MANIFEST) as f:
    manifest = json.load(f)

with open(PAIRS_FILE) as f:
    all_pairs = json.load(f)

pairs_by_id = {p["id"]: p for p in all_pairs}

print("=== pilot.json proc_ident vs CIFP record fields ===\n")

# Build CIFP approach index with CORRECTED offsets
# Based on actual layout: airport=6:10, proc_ident=13:18, trans=20:25, seq=26:29, turn=43
cifp_by_airport = {}  # airport -> list of (proc_ident, trans, seq, cont, turn, rt, raw)
print("Building corrected CIFP index...")
with open(CIFP_FILE, "r", encoding="latin-1") as f:
    for line in f:
        if not line.startswith("SUSAP"):
            continue
        if len(line) < 50:
            continue
        # Only approach records (subsection 'D')
        subsec = line[12] if len(line) > 12 else ""
        if subsec != "D":
            continue
        airport    = line[6:10].strip()
        proc_ident = line[13:18].strip()
        trans      = line[20:25].strip()
        seq        = line[26:29].strip()
        cont       = line[38] if len(line) > 38 else "0"
        turn       = line[43] if len(line) > 43 else " "
        rt         = line[47:50].strip() if len(line) > 50 else ""

        if airport not in cifp_by_airport:
            cifp_by_airport[airport] = []
        cifp_by_airport[airport].append((proc_ident, trans, seq, cont, turn.strip(), rt))

print(f"Indexed airports: {len(cifp_by_airport)}\n")

for entry in manifest:
    sid = entry["id"]
    airport = entry["airport"]
    proc_id = entry["proc_ident"]  # e.g. "R31"

    pair = pairs_by_id[sid]
    legs = pair["cifp"]["legs"]

    # pilot.json: find DF leg seq in MA segment
    main_trans = None
    for l in legs:
        if l["wpt_ident"].strip().startswith("RW"):
            main_trans = l["trans_ident"].strip()
            break

    main_legs = [l for l in legs if l["trans_ident"].strip() == main_trans]
    rw_idx = next((i for i, l in enumerate(main_legs) if l["wpt_ident"].strip().startswith("RW")), None)
    ma_legs = main_legs[rw_idx+1:] if rw_idx is not None else []

    df_leg = next((l for l in ma_legs if l["rt_type"].strip() == "DF"), None)

    print(f"\n{sid}: airport={airport!r}, proc_ident(manifest)={proc_id!r}")
    print(f"  main_trans={main_trans!r}")
    if df_leg:
        print(f"  DF leg: seq={df_leg['seq_no'].strip()!r}, wpt={df_leg['wpt_ident'].strip()!r}")

    # What CIFP records exist for this airport?
    recs = cifp_by_airport.get(airport, [])
    print(f"  CIFP approach records count: {len(recs)}")
    # Show unique proc_idents
    procs = sorted(set(r[0] for r in recs))
    print(f"  CIFP proc_idents: {procs}")
    # Show records with DF legs
    df_recs = [(p, t, s, c, turn, rt) for (p, t, s, c, turn, rt) in recs if rt == "DF"]
    print(f"  CIFP DF records: {df_recs[:8]}")
