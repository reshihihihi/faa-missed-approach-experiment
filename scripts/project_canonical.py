"""
Project extraction-schema per-leg data to canonical-schema 6-question answer bundles.

Input:  data/v2604_100/missed_approach_extracted/{chart_id}.json
Output: data/v2604_100/missed_approach/{chart_id}.json

Mapping rules follow docs/schemas/missed_approach_leg_v1.md §4.
Also injects procedure.chart_name from the committed sample_manifest_100.json.

Validates each output against schemas/missed_approach_leg.schema.json at the end
(if jsonschema is installed; otherwise skips validation).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DATASET = REPO / "data" / "v2604_100"
EXTRACTED_DIR = DATASET / "missed_approach_extracted"
OUT_DIR = DATASET / "missed_approach"
MANIFEST_OLD = DATASET / "sample_manifest_100.json"
SCHEMA_FILE = REPO / "schemas" / "missed_approach_leg.schema.json"


ALT_DESC_CANONICAL = {"AT", "AT_OR_ABOVE", "AT_OR_BELOW", "BETWEEN"}

TERMINATORS_NO_FIX = {"CA", "VA", "VI", "VM", "VR", "VD", "CD", "CI", "CR", "VC"}
TERMINATORS_FROM_FIX = {"FA", "FC", "FD", "FM"}
TERMINATORS_TO_FIX = {"CF", "DF", "TF", "AF"}
TERMINATORS_HOLD = {"HA", "HF", "HM"}

VALID_TERMINATORS = {
    "CA", "CF", "CI", "CR", "DF", "FA", "FM",
    "HA", "HF", "HM", "IF", "RF", "TF",
    "VA", "VD", "VI", "VM", "VR",
    "AF", "CD", "FC", "FD", "VC", "PI",
}


def present(value):
    return {"status": "present", "value": value}


def not_applicable():
    return {"status": "not_applicable", "value": None}


def unknown():
    return {"status": "unknown", "value": None}


def project_terminator(leg: dict) -> dict:
    term = (leg.get("path_terminator") or "").strip()
    if term in VALID_TERMINATORS:
        return present(term)
    return unknown()


def project_fix_ident(leg: dict) -> dict:
    term = leg.get("path_terminator")
    fix = leg.get("fix_ident")
    if term in TERMINATORS_NO_FIX:
        return not_applicable()
    if term in TERMINATORS_FROM_FIX | TERMINATORS_TO_FIX | TERMINATORS_HOLD | {"IF"}:
        return present(fix) if fix else unknown()
    # RF/PI: fix may or may not be present; follow extraction
    if fix:
        return present(fix)
    return not_applicable()


def project_altitude(leg: dict) -> dict:
    alt_desc = leg.get("alt_desc")
    alt1 = leg.get("altitude_1_ft")
    alt2 = leg.get("altitude_2_ft")
    if alt1 is None and alt2 is None:
        return not_applicable()
    if alt_desc not in ALT_DESC_CANONICAL:
        alt_desc = "AT"
    return present({
        "desc": alt_desc,
        "altitude_ft": alt1,
        "altitude_2_ft": alt2 if alt_desc == "BETWEEN" else None,
    })


def project_turn(leg: dict) -> dict:
    term = leg.get("path_terminator")
    if term in TERMINATORS_HOLD:
        return not_applicable()  # hold turn lives in Q5
    td = leg.get("turn_direction")
    if td in ("LEFT", "RIGHT"):
        return present(td)
    return not_applicable()


def project_course_or_radial(leg: dict) -> dict:
    term = leg.get("path_terminator")
    if term in TERMINATORS_HOLD:
        return not_applicable()
    if term == "DF":
        return present({"type": "direct"})

    rec_navaid = leg.get("rec_navaid")
    theta = leg.get("theta_deg")
    fix_ident = leg.get("fix_ident")
    course = leg.get("mag_course_deg")

    # FA/FC/FD: outbound from rec_navaid (== fix_ident for FA)
    if (term in TERMINATORS_FROM_FIX
            and rec_navaid and rec_navaid == fix_ident
            and course is not None):
        return present({
            "type": "navaid_radial",
            "navaid": rec_navaid,
            "radial_deg": round(course, 1),
            "direction": "outbound",
        })

    # CF/TF: inbound radial — two variants
    if term in ("CF", "TF") and rec_navaid:
        if rec_navaid == fix_ident and course is not None:
            # Inbound to the navaid; radial = reciprocal of aircraft course
            return present({
                "type": "navaid_radial",
                "navaid": rec_navaid,
                "radial_deg": round((course + 180) % 360, 1),
                "direction": "inbound",
            })
        if theta is not None and theta != 0:
            # Inbound on a specific radial toward a fix not at the navaid
            return present({
                "type": "navaid_radial",
                "navaid": rec_navaid,
                "radial_deg": round(theta, 1),
                "direction": "inbound",
            })

    # Default: plain course_deg
    if course is not None:
        return present({"type": "course_deg", "course_deg": round(course, 1)})

    return not_applicable()


def project_hold_params(leg: dict) -> dict:
    term = leg.get("path_terminator")
    if term not in TERMINATORS_HOLD:
        return not_applicable()
    course = leg.get("mag_course_deg")
    return present({
        "inbound_course_deg": round(course, 1) if course is not None else None,
        "leg_time_min": leg.get("hold_time_min"),
        "leg_distance_nm": leg.get("distance_nm"),
        "turn": leg.get("turn_direction"),
    })


def project_leg(leg: dict) -> dict:
    return {
        "leg_index": leg["leg_index"],
        "answers": {
            "Q_terminator": project_terminator(leg),
            "Q1_fix_ident": project_fix_ident(leg),
            "Q2_altitude_constraint": project_altitude(leg),
            "Q3_turn": project_turn(leg),
            "Q4_course_or_radial": project_course_or_radial(leg),
            "Q5_hold_params": project_hold_params(leg),
        },
    }


def project_procedure(extracted: dict, chart_name: str) -> dict:
    legs = extracted.get("missed_approach_legs") or []
    leg_count = len(legs)
    return {
        "chart_id": extracted["chart_id"],
        "procedure": {
            "airport": extracted["airport"],
            "approach_ident": extracted["approach_ident"],
            "chart_name": chart_name,
        },
        "missed_approach": {
            "leg_count": present(leg_count) if leg_count > 0 else unknown(),
            "legs": [project_leg(leg) for leg in legs],
        },
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    chart_name_map: dict[str, str] = {}
    if MANIFEST_OLD.exists():
        old = json.loads(MANIFEST_OLD.read_text(encoding="utf-8"))
        chart_name_map = {e["id"]: e.get("chart_name", "") for e in old}

    sources = sorted(EXTRACTED_DIR.glob("*.json"))
    processed = 0
    for src in sources:
        if src.name.startswith("_"):
            continue
        extracted = json.loads(src.read_text(encoding="utf-8"))
        chart_id = extracted["chart_id"]
        chart_name = chart_name_map.get(chart_id, "")
        canonical = project_procedure(extracted, chart_name)
        (OUT_DIR / f"{chart_id}.json").write_text(
            json.dumps(canonical, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        processed += 1
    print(f"Projected {processed} procedures to canonical form at {OUT_DIR.relative_to(REPO)}/")

    try:
        from jsonschema import Draft202012Validator
        schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        failures = 0
        for p in sorted(OUT_DIR.glob("*.json")):
            instance = json.loads(p.read_text(encoding="utf-8"))
            errors = list(validator.iter_errors(instance))
            if errors:
                failures += 1
                print(f"  SCHEMA FAIL {p.name}: {errors[0].message}", file=sys.stderr)
        if failures == 0:
            print(f"All {processed} canonical JSONs validate against schema.")
        else:
            print(f"{failures}/{processed} canonical JSONs FAILED schema validation.", file=sys.stderr)
            return 1
    except ImportError:
        print("jsonschema not installed; skipping schema validation.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
