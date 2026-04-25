import argparse
import json
from pathlib import Path


STATUS = {"present", "not_applicable", "not_observable", "unknown"}
TERMINATORS = {
    "CA", "CF", "CI", "CR", "DF", "FA", "FM", "HA", "HF", "HM", "IF", "RF",
    "TF", "VA", "VD", "VI", "VM", "VR", "AF", "CD", "FC", "FD", "VC", "PI", "unknown",
}
Q_FIELDS = [
    "Q_terminator",
    "Q1_fix_ident",
    "Q2_altitude_constraint",
    "Q3_turn",
    "Q4_course_or_radial",
    "Q5_hold_params",
]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def require(condition, errors, message):
    if not condition:
        errors.append(message)


def validate_answer(field, answer, errors, prefix):
    require(isinstance(answer, dict), errors, f"{prefix}.{field}: answer must be object")
    if not isinstance(answer, dict):
        return
    require(set(answer.keys()) == {"status", "value"}, errors, f"{prefix}.{field}: answer keys must be status/value")
    status = answer.get("status")
    value = answer.get("value")
    require(status in STATUS, errors, f"{prefix}.{field}: invalid status {status!r}")
    if status in {"not_applicable", "not_observable", "unknown"}:
        require(value is None, errors, f"{prefix}.{field}: value must be null when status={status}")
    if field == "Q_terminator" and status == "present":
        require(value in TERMINATORS, errors, f"{prefix}.{field}: invalid terminator {value!r}")
    if field == "Q3_turn" and status == "present":
        require(value in {"LEFT", "RIGHT"}, errors, f"{prefix}.{field}: invalid turn {value!r}")
    if field == "Q2_altitude_constraint" and status == "present":
        require(isinstance(value, dict), errors, f"{prefix}.{field}: value must be object")
        if isinstance(value, dict):
            require(set(value.keys()) == {"desc", "altitude_ft", "altitude_2_ft"}, errors, f"{prefix}.{field}: invalid altitude keys")
            require(value.get("desc") in {"AT", "AT_OR_ABOVE", "AT_OR_BELOW", "BETWEEN"}, errors, f"{prefix}.{field}: invalid desc")
            require(value.get("altitude_ft") is None or isinstance(value.get("altitude_ft"), int), errors, f"{prefix}.{field}: altitude_ft must be int/null")
    if field == "Q4_course_or_radial" and status == "present":
        require(isinstance(value, dict), errors, f"{prefix}.{field}: value must be object")
        if isinstance(value, dict):
            require(value.get("type") in {"course_deg", "navaid_radial", "direct"}, errors, f"{prefix}.{field}: invalid type")
    if field == "Q5_hold_params" and status == "present":
        require(isinstance(value, dict), errors, f"{prefix}.{field}: value must be object")
        if isinstance(value, dict):
            require(set(value.keys()) == {"inbound_course_deg", "leg_time_min", "leg_distance_nm", "turn"}, errors, f"{prefix}.{field}: invalid hold keys")
            require(value.get("turn") in {None, "LEFT", "RIGHT"}, errors, f"{prefix}.{field}: invalid hold turn")


def validate_file(path):
    data = read_json(path)
    errors = []
    require(set(data.keys()) == {"chart_id", "procedure", "missed_approach"}, errors, "top-level keys must be chart_id/procedure/missed_approach")
    require(isinstance(data.get("chart_id"), str), errors, "chart_id must be string")
    procedure = data.get("procedure")
    require(isinstance(procedure, dict), errors, "procedure must be object")
    if isinstance(procedure, dict):
        require(set(procedure.keys()) == {"airport", "approach_ident", "chart_name"}, errors, "procedure keys must be airport/approach_ident/chart_name")
        for key in ["airport", "approach_ident", "chart_name"]:
            require(isinstance(procedure.get(key), str) and procedure.get(key), errors, f"procedure.{key} must be non-empty string")
    ma = data.get("missed_approach")
    require(isinstance(ma, dict), errors, "missed_approach must be object")
    if not isinstance(ma, dict):
        return errors
    require(set(ma.keys()) == {"leg_count", "legs"}, errors, "missed_approach keys must be leg_count/legs")
    leg_count = ma.get("leg_count")
    validate_answer("leg_count", leg_count, errors, "missed_approach")
    legs = ma.get("legs")
    require(isinstance(legs, list), errors, "missed_approach.legs must be array")
    if isinstance(leg_count, dict) and leg_count.get("status") == "present" and isinstance(legs, list):
        require(leg_count.get("value") == len(legs), errors, "leg_count.value must equal len(legs)")
    if isinstance(legs, list):
        for idx, leg in enumerate(legs, start=1):
            prefix = f"legs[{idx}]"
            require(isinstance(leg, dict), errors, f"{prefix}: leg must be object")
            if not isinstance(leg, dict):
                continue
            require(set(leg.keys()) == {"leg_index", "answers"}, errors, f"{prefix}: keys must be leg_index/answers")
            require(leg.get("leg_index") == idx, errors, f"{prefix}: leg_index must be {idx}")
            answers = leg.get("answers")
            require(isinstance(answers, dict), errors, f"{prefix}.answers must be object")
            if isinstance(answers, dict):
                require(set(answers.keys()) == set(Q_FIELDS), errors, f"{prefix}.answers must contain exactly Q fields")
                for field in Q_FIELDS:
                    validate_answer(field, answers.get(field), errors, prefix)
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="Method output JSON files or directories")
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
        errors = validate_file(path)
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
