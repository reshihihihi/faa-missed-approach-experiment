import argparse
import json
import re
from pathlib import Path


DISALLOWED_KEYS = {
    "chart_id",
    "airport",
    "proc_ident",
    "approach_ident",
    "procedure",
    "candidate_mappings",
    "expected_value",
    "expected_answer",
    "canonical_leg_index",
    "candidate_leg_id",
    "leg_type",
    "field_name",
    "canonical_proxy_gt_file",
    "source_seq_no",
    "source_trans_ident",
    "raw_record",
    "target_fields",
}

STRICT_DISALLOWED_KEYS = {
    "prelabel_text",
    "visual_label",
    "label",
    "candidate_mappings_source",
    "manual_answer",
    "human_corrected_value",
}

DISALLOWED_CANDIDATE_TYPES = {
    "Q_terminator",
    "Q1_fix_ident",
    "Q2_altitude_constraint",
    "Q3_turn",
    "Q4_course_or_radial",
    "Q5_hold_params",
}

CHART_ID_RE = re.compile(r"\bK[A-Z0-9]{3}_[A-Z0-9\-]+\b")
CIFP_PATH_RE = re.compile(r"(canonical_proxy_gt|pilot_canonical|FAACIFP|\\cifp\\|/cifp/)", re.IGNORECASE)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def walk(value, path, errors, *, strict_prompt=False):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key in DISALLOWED_KEYS:
                errors.append(f"{child_path}: disallowed key '{key}'")
            if strict_prompt and key in STRICT_DISALLOWED_KEYS:
                errors.append(f"{child_path}: strict prompt disallows key '{key}'")
            if key == "candidate_type" and child in DISALLOWED_CANDIDATE_TYPES:
                errors.append(f"{child_path}: disallowed Q-field candidate_type '{child}'")
            walk(child, child_path, errors, strict_prompt=strict_prompt)
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            walk(child, f"{path}[{idx}]", errors, strict_prompt=strict_prompt)
    elif isinstance(value, str):
        if CIFP_PATH_RE.search(value):
            errors.append(f"{path}: disallowed CIFP/canonical target path fragment in string value")
        # OCR may legitimately contain airport/city names from the chart, but true
        # dataset ids such as KCOE_L06 should never be prompt-visible.
        if CHART_ID_RE.search(value):
            errors.append(f"{path}: disallowed chart_id-like string value {CHART_ID_RE.search(value).group(0)!r}")


def validate_file(path, *, strict_prompt=False):
    errors = []
    data = read_json(path)
    walk(data, "", errors, strict_prompt=strict_prompt)
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="JSON files or directories to validate")
    parser.add_argument(
        "--strict-prompt",
        action="store_true",
        help="Also reject prompt-visible prelabel/manual text fields.",
    )
    args = parser.parse_args()

    files = []
    for item in args.paths:
        path = Path(item)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.json")))
        else:
            files.append(path)

    failed = False
    for path in files:
        errors = validate_file(path, strict_prompt=args.strict_prompt)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {path}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
