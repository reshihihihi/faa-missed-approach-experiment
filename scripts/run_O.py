"""
Path O: CIFP baseline extraction.

Build a reference JSON for each sample from the structured legs in pilot.json,
using the raw FAACIFP18 record only for DF-leg turn direction lookup.
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from dataset_config import CIFP_PATH, MANIFEST_PATH, PAIRS_PATH, RESULTS_DIR

MANIFEST = MANIFEST_PATH
PAIRS_FILE = PAIRS_PATH
CIFP_FILE = CIFP_PATH
OUT_DIR = RESULTS_DIR / "O"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HOLDING_TYPES = {"HM", "HF", "HA"}


def parse_app_record(line):
    """Parse a primary ARINC 424 approach record."""
    if not line.startswith("SUSAP"):
        return None
    if len(line) < 50:
        return None
    if line[12] != "F":
        return None

    cont_num = line[38] if len(line) > 38 else "0"
    if cont_num not in ("0", "1"):
        return None

    # ARINC 424.18 PF record column layout (1-indexed, inclusive).
    # Bug fixes 2026-04-24:
    #   proc_ident was cols 14-18 (5 chars) -> now cols 14-19 (6 chars per spec 5.9+5.10).
    #   rt_type was cols 48-50 (3 chars, overran into col 50 turn_dir_valid) -> cols 48-49 (2 chars per spec 5.21).
    return {
        "airport": line[6:10].strip(),
        "proc_ident": line[13:19].rstrip(),
        "trans_ident": line[19:25].strip(),
        "seq_no": line[26:29].strip(),
        "turn_dir": line[43].strip() if len(line) > 43 else "",
        "rt_type": line[47:49].strip() if len(line) > 49 else "",
    }


def parse_altitude(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def get_main_transition(legs):
    for leg in legs:
        if leg["wpt_ident"].strip().startswith("RW"):
            return leg["trans_ident"].strip()

    trans_ids = {leg["trans_ident"].strip() for leg in legs}
    for candidate in ("R", "I"):
        if candidate in trans_ids:
            return candidate
    return None


def get_missed_approach_legs(legs, main_trans):
    if not main_trans:
        return []

    main_legs = [leg for leg in legs if leg["trans_ident"].strip() == main_trans]
    rw_idx = next(
        (i for i, leg in enumerate(main_legs) if leg["wpt_ident"].strip().startswith("RW")),
        None,
    )
    if rw_idx is None:
        return []
    return main_legs[rw_idx + 1 :]


def build_raw_instruction(ma_legs):
    parts = []
    for leg in ma_legs:
        rt = leg["rt_type"].strip()
        wpt = leg["wpt_ident"].strip()
        alt = parse_altitude(leg.get("altitude1"))
        alt_desc = leg.get("alt_desc", "").strip()

        piece = rt
        if wpt:
            piece += f" {wpt}"
        if alt is not None:
            suffix = "+" if alt_desc == "+" else "-" if alt_desc == "-" else ""
            piece += f" {alt}{suffix}ft"
        parts.append(piece)
    return " -> ".join(parts) if parts else "unknown"


def extract_climb_altitude(ma_legs):
    after_ca = False
    for leg in ma_legs:
        rt = leg["rt_type"].strip()
        if rt == "CA":
            after_ca = True
            continue
        if after_ca:
            alt = parse_altitude(leg.get("altitude1"))
            if alt is not None:
                return alt

    altitudes = [parse_altitude(leg.get("altitude1")) for leg in ma_legs]
    altitudes = [alt for alt in altitudes if alt is not None]
    return max(altitudes) if altitudes else "unknown"


def extract_waypoints(ma_legs):
    after_ca = False
    waypoints = []
    for leg in ma_legs:
        rt = leg["rt_type"].strip()
        if rt == "CA":
            after_ca = True
            continue
        if after_ca:
            wpt = leg["wpt_ident"].strip()
            if wpt and wpt not in waypoints:
                waypoints.append(wpt)
    return waypoints


def extract_turn_direction(ma_legs, cifp_index, airport, proc_id, main_trans):
    for leg in ma_legs:
        if leg["rt_type"].strip() != "DF":
            continue
        key = (airport, proc_id, main_trans, leg["seq_no"].strip())
        raw_td = cifp_index.get(key, "")
        if raw_td == "L":
            return "LEFT"
        if raw_td == "R":
            return "RIGHT"
        return "NONE"
    return "NONE"


def extract_holding(ma_legs):
    for leg in ma_legs:
        if leg["rt_type"].strip() in HOLDING_TYPES:
            return True, (leg["wpt_ident"].strip() or "unknown")
    return False, None


def extract_turn_trigger(ma_legs):
    for leg in ma_legs:
        if leg["rt_type"].strip() == "DF":
            wpt = leg["wpt_ident"].strip()
            if wpt:
                return wpt
            alt = parse_altitude(leg.get("altitude1"))
            if alt is not None:
                return str(alt)
    return None


with open(MANIFEST, encoding="utf-8") as f:
    manifest = json.load(f)

with open(PAIRS_FILE, encoding="utf-8") as f:
    all_pairs = json.load(f)

pairs_by_id = {pair["id"]: pair for pair in all_pairs}

print("Building CIFP raw record index...")
cifp_index = {}
with open(CIFP_FILE, "r", encoding="latin-1") as f:
    for line in f:
        record = parse_app_record(line)
        if record is None:
            continue
        key = (
            record["airport"],
            record["proc_ident"],
            record["trans_ident"],
            record["seq_no"],
        )
        cifp_index.setdefault(key, record["turn_dir"])
print(f"Indexed {len(cifp_index)} CIFP records.")

results = []

for entry in manifest:
    sid = entry["id"]
    airport = entry["airport"]
    proc_id = entry["proc_ident"]

    pair = pairs_by_id[sid]
    legs = pair["cifp"]["legs"]
    main_trans = get_main_transition(legs)
    ma_legs = get_missed_approach_legs(legs, main_trans)

    holding_required, holding_fix = extract_holding(ma_legs)

    out = {
        "raw_instruction": build_raw_instruction(ma_legs),
        "climb_altitude": extract_climb_altitude(ma_legs),
        "waypoints": extract_waypoints(ma_legs),
        "turn_direction": extract_turn_direction(ma_legs, cifp_index, airport, proc_id, main_trans),
        "holding_required": holding_required,
        "holding_fix": holding_fix,
        "initial_track": None,
        "turn_trigger": extract_turn_trigger(ma_legs),
        "holding_details": None,
    }

    out_path = OUT_DIR / f"{sid}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(
        f"  {sid}: climb={out['climb_altitude']}, wpts={out['waypoints']}, "
        f"turn={out['turn_direction']}, holding={out['holding_required']}, "
        f"fix={out['holding_fix']}"
    )
    results.append({"id": sid, "result": out})

print(f"\nPath O completed: {len(results)} samples -> {OUT_DIR}")
