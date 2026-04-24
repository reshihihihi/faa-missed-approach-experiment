"""
Extract leg-level missed-approach segments from FAACIFP18.

Trial extraction per the charter agreed on 2026-04-24:

Slicing
  1. Filter: line[0:5] in {SUSAP, SUSAH}, line[12]='F', line[38]='0'
  2. Group key: (airport, approach_ident, transition_ident) from cols 7-10 / 14-19 / 21-25
  3. Within each group, sort by sequence number (cols 27-29)
  4. MAP = leg where Waypoint Description Code char 4 (col 43) == 'M'
  5. Missed-approach legs = legs with seq > MAP.seq in the group that contains MAP
  6. Groups without a MAP are discarded (feeder transitions etc.)

Per-line parsing follows the column table verified against KABE_I06 records.

Scope of this trial
  - No commit, no PR. Evidence-only output under data/v2604_100/missed_approach_extracted/.
  - Covers only the 100 procedures in pairs_100.json.
  - Includes raw record text per leg for traceability.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DATASET = REPO / "data" / "v2604_100"
CIFP_FILE = DATASET / "cifp" / "FAACIFP18"
PAIRS_FILE = DATASET / "pairs_100.json"
OUT_DIR = DATASET / "missed_approach_extracted"
SUMMARY_FILE = OUT_DIR / "_summary.json"


ALT_DESC_MAP = {
    "": "AT",
    "@": "AT",
    "+": "AT_OR_ABOVE",
    "-": "AT_OR_BELOW",
    "V": "AT_OR_BELOW",
    "B": "BETWEEN",
    "G": "AT",
    "H": "AT",
    "I": "AT",
    "J": "AT",
    "X": "AT",
    "Y": "AT",
    "C": "AT",
}

MISSED_PERMISSIBLE_TERMINATORS = {
    "CA", "CF", "CI", "CR", "DF", "FA", "FM",
    "HA", "HF", "HM", "IF", "RF", "TF",
    "VA", "VD", "VI", "VM", "VR", "AF", "CD",
}


def col(line: str, a: int, b: int | None = None) -> str:
    if b is None:
        b = a
    return line[a - 1 : b]


def parse_altitude_ft(s: str):
    s = s.strip()
    if not s:
        return None
    if s.startswith("FL"):
        try:
            return int(s[2:]) * 100
        except ValueError:
            return None
    try:
        return int(s)
    except ValueError:
        return None


def parse_scaled(s: str, divisor: float):
    s = s.strip()
    if not s:
        return None
    try:
        return int(s) / divisor
    except ValueError:
        return None


def parse_mag_course_deg(s: str):
    s = s.strip()
    if not s:
        return None, False
    true_flag = s.endswith("T")
    if true_flag:
        s = s[:-1]
    try:
        return int(s) / 10.0, true_flag
    except ValueError:
        return None, true_flag


def parse_distance_or_hold(s: str, path_term: str):
    s = s.strip()
    if not s:
        return None, None
    if s.startswith("T") and path_term in ("HA", "HF", "HM"):
        try:
            return None, int(s[1:]) / 10.0
        except ValueError:
            return None, None
    try:
        return int(s) / 10.0, None
    except ValueError:
        return None, None


def parse_rnp_nm(s: str):
    """Mantissa+negative-exponent: 3 chars. e.g. '105' -> 1.0, '010' -> 0.10, '012' -> 0.01."""
    s = s.strip()
    if not s or len(s) != 3:
        return None
    try:
        mant = int(s[0:2])
        exp = int(s[2])
        return mant * (10 ** (-exp))
    except ValueError:
        return None


def parse_vertical_angle_deg(s: str):
    s = s.strip()
    if not s:
        return None
    try:
        return int(s) / 100.0
    except ValueError:
        return None


def parse_leg_line(line: str) -> dict:
    path_term = col(line, 48, 49).strip()
    mag_course, mag_course_is_true = parse_mag_course_deg(col(line, 71, 74))
    dist_nm, hold_time = parse_distance_or_hold(col(line, 75, 78), path_term)
    alt_desc_raw = col(line, 83).strip()
    speed_limit_raw = col(line, 100, 102).strip()
    speed_desc_raw = col(line, 118).strip()

    return {
        "seq_no": col(line, 27, 29).strip(),
        "transition_ident": col(line, 21, 25).rstrip(),
        "approach_ident": col(line, 14, 19).rstrip(),
        "airport": col(line, 7, 10).strip(),
        "path_terminator": path_term,
        "fix_ident": col(line, 30, 34).rstrip() or None,
        "waypoint_desc": col(line, 40, 43),
        "turn_direction": {"L": "LEFT", "R": "RIGHT"}.get(col(line, 44).strip()),
        "rnp_nm": parse_rnp_nm(col(line, 45, 47)),
        "alt_desc_raw": alt_desc_raw,
        "alt_desc": ALT_DESC_MAP.get(alt_desc_raw, "AT"),
        "altitude_1_ft": parse_altitude_ft(col(line, 85, 89)),
        "altitude_2_ft": parse_altitude_ft(col(line, 90, 94)),
        "mag_course_deg": mag_course,
        "mag_course_is_true": mag_course_is_true,
        "theta_deg": parse_scaled(col(line, 63, 66), 10.0),
        "rho_nm": parse_scaled(col(line, 67, 70), 10.0),
        "distance_nm": dist_nm,
        "hold_time_min": hold_time,
        "rec_navaid": col(line, 51, 54).rstrip() or None,
        "center_fix": col(line, 107, 111).rstrip() or None,
        "arc_radius_nm": parse_scaled(col(line, 57, 62), 10.0),
        "vertical_angle_deg": parse_vertical_angle_deg(col(line, 103, 106)),
        "speed_limit_kt": int(speed_limit_raw) if speed_limit_raw.isdigit() else None,
        "speed_limit_desc": speed_desc_raw or None,
        "raw_record": line,
    }


def passes_filter(line: str) -> bool:
    if len(line) < 132:
        return False
    if line[0:5] not in ("SUSAP", "SUSAH"):
        return False
    if line[12] != "F":
        return False
    if line[38] != "0":
        return False
    return True


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pairs = json.loads(PAIRS_FILE.read_text(encoding="utf-8"))
    wanted = {(p["cifp"]["airport"], p["cifp"]["proc_ident"]): p["id"] for p in pairs}

    all_groups: dict[tuple, list[dict]] = {}
    total_lines = primary_legs = matched_legs = 0

    with CIFP_FILE.open("r", encoding="latin-1") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip("\r")
            total_lines += 1
            if not passes_filter(line):
                continue
            primary_legs += 1
            apt = line[6:10].strip()
            ident = line[13:19].rstrip()
            if (apt, ident) not in wanted:
                continue
            matched_legs += 1
            leg = parse_leg_line(line)
            key = (apt, ident, leg["transition_ident"])
            all_groups.setdefault(key, []).append(leg)

    for legs in all_groups.values():
        legs.sort(key=lambda x: x["seq_no"])

    extracted: dict[str, dict] = {}
    warnings: list[str] = []

    for p in pairs:
        apt = p["cifp"]["airport"]
        pid = p["cifp"]["proc_ident"]
        chart_id = p["id"]

        proc_groups = {k: v for k, v in all_groups.items() if k[0] == apt and k[1] == pid}

        if not proc_groups:
            warnings.append(f"{chart_id}: no PF records matched")
            extracted[chart_id] = {
                "chart_id": chart_id,
                "airport": apt,
                "approach_ident": pid,
                "error": "no_records",
                "missed_approach_legs": [],
            }
            continue

        map_matches = []
        for key, legs in proc_groups.items():
            for i, leg in enumerate(legs):
                wd = leg["waypoint_desc"]
                if len(wd) >= 4 and wd[3] == "M":
                    map_matches.append((key, i, leg))

        if not map_matches:
            warnings.append(
                f"{chart_id}: no MAP found; transition groups seen = "
                f"{[k[2] or '(blank)' for k in proc_groups]}"
            )
            extracted[chart_id] = {
                "chart_id": chart_id,
                "airport": apt,
                "approach_ident": pid,
                "error": "no_map",
                "transition_groups": [k[2] or "" for k in proc_groups],
                "missed_approach_legs": [],
            }
            continue

        if len(map_matches) > 1:
            warnings.append(
                f"{chart_id}: multiple MAP candidates across transitions "
                f"{[k[2] or '(blank)' for k, _, _ in map_matches]}; taking first"
            )
        map_key, map_idx, map_leg = map_matches[0]
        missed_legs = proc_groups[map_key][map_idx + 1 :]

        extracted[chart_id] = {
            "chart_id": chart_id,
            "airport": apt,
            "approach_ident": pid,
            "main_transition_ident": map_key[2],
            "map_fix": map_leg["fix_ident"],
            "map_seq_no": map_leg["seq_no"],
            "missed_approach_legs": [
                {"leg_index": i, **leg}
                for i, leg in enumerate(missed_legs, start=1)
            ],
        }

    for chart_id, data in extracted.items():
        (OUT_DIR / f"{chart_id}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    succeeded = [d for d in extracted.values() if "error" not in d]
    failed = [d for d in extracted.values() if "error" in d]

    pt_counter: Counter[str] = Counter()
    leg_counts: dict[str, int] = {}
    unexpected_terms: Counter[str] = Counter()
    for d in succeeded:
        leg_counts[d["chart_id"]] = len(d["missed_approach_legs"])
        for leg in d["missed_approach_legs"]:
            pt = leg["path_terminator"]
            pt_counter[pt] += 1
            if pt not in MISSED_PERMISSIBLE_TERMINATORS:
                unexpected_terms[pt] += 1

    summary = {
        "cifp_file": str(CIFP_FILE.relative_to(REPO).as_posix()),
        "total_pairs": len(pairs),
        "procedures_extracted": len(succeeded),
        "procedures_failed": [
            {"chart_id": d["chart_id"], "error": d["error"]} for d in failed
        ],
        "cifp_scan": {
            "total_lines": total_lines,
            "approach_primary_legs": primary_legs,
            "matched_to_100": matched_legs,
        },
        "leg_count_distribution": dict(Counter(leg_counts.values()).most_common()),
        "path_terminator_distribution": dict(pt_counter.most_common()),
        "unexpected_path_terminators": dict(unexpected_terms),
        "warnings": warnings,
    }
    SUMMARY_FILE.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Scanned {total_lines:,} lines; {primary_legs:,} approach primary legs; "
          f"{matched_legs:,} matched to 100 procedures.")
    print(f"Extracted OK: {len(succeeded)} / {len(pairs)}")
    if failed:
        print(f"Failures ({len(failed)}):")
        for d in failed:
            print(f"  {d['chart_id']}: {d['error']}")
    print("\nPath terminator distribution (missed-approach legs):")
    for pt, n in summary["path_terminator_distribution"].items():
        flag = " !" if pt in unexpected_terms else ""
        print(f"  {pt}: {n}{flag}")
    print("\nLeg count distribution (#legs -> #procedures):")
    for n_legs, n_procs in sorted(summary["leg_count_distribution"].items()):
        print(f"  {n_legs} legs: {n_procs} procedures")
    if warnings:
        print(f"\n{len(warnings)} warnings (first 10):")
        for w in warnings[:10]:
            print(f"  {w}")
    print(f"\nPer-procedure JSON under: {OUT_DIR.relative_to(REPO).as_posix()}")
    print(f"Summary: {SUMMARY_FILE.relative_to(REPO).as_posix()}")


if __name__ == "__main__":
    main()
