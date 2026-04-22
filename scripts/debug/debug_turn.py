"""Debug turn_direction lookup for KAAT_R31."""
import json
from pathlib import Path

PAIRS_FILE = Path("e:/hangtu3/data/pairs/pilot.json")
CIFP_FILE  = Path("e:/experiment/data/pilot_10/cifp/FAACIFP18")
MANIFEST   = Path("e:/experiment/data/pilot_10/sample_manifest.json")

with open(PAIRS_FILE) as f:
    all_pairs = json.load(f)

with open(MANIFEST) as f:
    manifest = json.load(f)

# Build manifest lookup
manifest_by_id = {e["id"]: e for e in manifest}

# Check KAAT_R31 DF leg details
sid = "KAAT_R31"
for p in all_pairs:
    if p["id"] == sid:
        legs = p["cifp"]["legs"]
        print(f"All legs for {sid}:")
        for l in legs:
            print(f"  trans={l['trans_ident'].strip()!r:10s} seq={l['seq_no'].strip()!r:5s} rt={l['rt_type'].strip()!r:4s} wpt={l['wpt_ident'].strip()!r}")

        # Find main trans (has RW## leg)
        main_trans = None
        for l in legs:
            if l["wpt_ident"].strip().startswith("RW"):
                main_trans = l["trans_ident"].strip()
                break
        print(f"\nmain_trans={main_trans!r}")

        # Find DF leg in MA segment
        main_legs = [l for l in legs if l["trans_ident"].strip() == main_trans]
        rw_idx = None
        for i, l in enumerate(main_legs):
            if l["wpt_ident"].strip().startswith("RW"):
                rw_idx = i
                break
        ma_legs = main_legs[rw_idx+1:] if rw_idx is not None else []
        print(f"MA legs:")
        for l in ma_legs:
            print(f"  trans={l['trans_ident'].strip()!r:10s} seq={l['seq_no'].strip()!r:5s} rt={l['rt_type'].strip()!r:4s} wpt={l['wpt_ident'].strip()!r}")

        # DF leg
        for l in ma_legs:
            if l["rt_type"].strip() == "DF":
                airport = manifest_by_id[sid]["airport"]
                proc_id = manifest_by_id[sid]["proc_ident"]
                seq = l["seq_no"].strip()
                key = (airport, proc_id, main_trans, seq)
                print(f"\nLookup key: {key}")
                break
        break

# Now scan raw CIFP for KAAT lines with proc_ident=R31
print("\nRaw CIFP records for KAAT / R31:")
with open(CIFP_FILE, "r", encoding="latin-1") as f:
    for line in f:
        if not line.startswith("SUSAP"):
            continue
        airport = line[6:10].strip()
        proc_id = line[14:19].strip()
        if airport == "KAAT" and proc_id == "R31":
            trans = line[20:26].strip()
            seq = line[27:30].strip()
            cont = line[38] if len(line) > 38 else "?"
            turn = line[43] if len(line) > 43 else "?"
            rt = line[47:50].strip() if len(line) > 50 else "?"
            wpt = line[30:35].strip() if len(line) > 35 else "?"
            print(f"  trans={trans!r:10s} seq={seq!r:5s} cont={cont!r} turn={turn!r} rt={rt!r:4s} wpt={wpt!r}")
