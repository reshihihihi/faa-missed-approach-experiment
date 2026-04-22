"""
Classify major error types for paths A/B/C/D against path O.

Outputs:
1. error_analysis_report.md
2. error_analysis.json
"""

import json
from collections import defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path("e:/experiment/scripts")))
from dataset_config import MANIFEST_PATH, RESULTS_DIR

MANIFEST = MANIFEST_PATH
RESULTS = RESULTS_DIR
PATHS = ["A", "B", "C", "D", "E"]
REPORT = RESULTS / "error_analysis_report.md"
JSON_OUT = RESULTS / "error_analysis.json"

CORE_FIELDS = [
    "climb_altitude",
    "turn_direction",
    "holding_required",
    "holding_fix",
]


def load_json_safe(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def normalize_altitude(value):
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped.lower() == "unknown":
            return "unknown"
        try:
            return int(stripped)
        except ValueError:
            return "unknown"
    return "unknown"


def normalize_turn(value):
    if value is None:
        return "unknown"
    text = str(value).strip().upper()
    return text if text in {"LEFT", "RIGHT", "NONE", "UNKNOWN"} else "unknown"


def normalize_holding(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "yes", "1"}:
            return True
        if text in {"false", "no", "0"}:
            return False
        if text == "unknown":
            return "unknown"
    return "unknown"


def normalize_fix(value):
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return "unknown"
        low = text.lower()
        if low in {"null", "none"}:
            return None
        if low == "unknown":
            return "unknown"
        return text.upper()
    return "unknown"


def normalize_waypoints(value):
    if not isinstance(value, list):
        return set()
    return {str(item).strip().upper() for item in value if str(item).strip()}


def normalize_record(record):
    record = record or {}
    return {
        "climb_altitude": normalize_altitude(record.get("climb_altitude")),
        "turn_direction": normalize_turn(record.get("turn_direction")),
        "holding_required": normalize_holding(record.get("holding_required")),
        "holding_fix": normalize_fix(record.get("holding_fix")),
        "waypoints": normalize_waypoints(record.get("waypoints")),
    }


def is_applicable(field, ref_value, ref_record):
    if field == "holding_fix":
        return ref_record["holding_required"] is True and ref_value not in (None, "unknown")
    return ref_value != "unknown"


def is_predicted(field, pred_value, pred_record):
    if field == "holding_fix":
        return pred_record["holding_required"] is True and pred_value not in (None, "unknown")
    return pred_value != "unknown"


def scalar_error_label(field, pred_record, ref_record):
    pred_value = pred_record[field]
    ref_value = ref_record[field]
    applicable = is_applicable(field, ref_value, ref_record)
    predicted = is_predicted(field, pred_value, pred_record)

    if not applicable and not predicted:
        return None
    if not applicable and predicted:
        return f"{field}:spurious_prediction"
    if applicable and not predicted:
        return f"{field}:missing_prediction"
    if pred_value == ref_value:
        return None

    if field == "holding_required":
        if ref_value is True and pred_value is False:
            return "holding_required:missed_hold"
        if ref_value is False and pred_value is True:
            return "holding_required:false_hold"
        return "holding_required:wrong_value"

    if field == "turn_direction":
        if pred_value == "NONE" and ref_value in {"LEFT", "RIGHT"}:
            return "turn_direction:missed_turn"
        if pred_value in {"LEFT", "RIGHT"} and ref_value == "NONE":
            return "turn_direction:hallucinated_turn"
        return "turn_direction:wrong_direction"

    if field == "climb_altitude":
        return "climb_altitude:wrong_value"

    if field == "holding_fix":
        return "holding_fix:wrong_fix"

    return f"{field}:wrong_value"


def waypoint_error_labels(pred_record, ref_record):
    pred = pred_record["waypoints"]
    ref = ref_record["waypoints"]
    tp = len(pred & ref)
    fp = len(pred - ref)
    fn = len(ref - pred)

    if not ref and not pred:
        return []
    if not ref and pred:
        return ["waypoints:spurious_only"]
    if ref and not pred:
        return ["waypoints:missed_all"]
    if tp and not fp and not fn:
        return []
    if tp == 0 and fp > 0 and fn > 0:
        return ["waypoints:noisy_mismatch"]
    labels = []
    if fp > 0 and fn == 0:
        labels.append("waypoints:extra_points")
    if fn > 0 and fp == 0:
        labels.append("waypoints:missing_points")
    if fp > 0 and fn > 0:
        labels.append("waypoints:mixed_missing_and_extra")
    return labels


def fmt_percent(count, total):
    if not total:
        return "0.0%"
    return f"{count / total:.1%}"


def top_examples(example_map, key, limit=5):
    return example_map.get(key, [])[:limit]


with open(MANIFEST, encoding="utf-8") as f:
    manifest = json.load(f)

sample_ids = [entry["id"] for entry in manifest]
refs_raw = {sid: load_json_safe(RESULTS / "O" / f"{sid}.json") for sid in sample_ids}
refs = {sid: normalize_record(refs_raw[sid]) for sid in sample_ids}

all_results = {}

for path in PATHS:
    counts = defaultdict(int)
    examples = defaultdict(list)
    field_counts = {field: defaultdict(int) for field in CORE_FIELDS + ["waypoints"]}
    field_examples = {field: defaultdict(list) for field in CORE_FIELDS + ["waypoints"]}
    sample_signatures = defaultdict(int)
    sample_signature_examples = defaultdict(list)

    for sid in sample_ids:
        pred_raw = load_json_safe(RESULTS / path / f"{sid}.json")
        pred = normalize_record(pred_raw)
        ref = refs[sid]

        sample_labels = []

        if pred_raw is None:
            counts["sample:no_output"] += 1
            examples["sample:no_output"].append(sid)
            sample_labels.append("sample:no_output")

        for field in CORE_FIELDS:
            label = scalar_error_label(field, pred, ref)
            if label is None:
                continue
            counts[label] += 1
            examples[label].append(sid)
            field_counts[field][label] += 1
            field_examples[field][label].append(sid)
            sample_labels.append(label)

        for label in waypoint_error_labels(pred, ref):
            counts[label] += 1
            examples[label].append(sid)
            field_counts["waypoints"][label] += 1
            field_examples["waypoints"][label].append(sid)
            sample_labels.append(label)

        if sample_labels:
            signature = " | ".join(sorted(sample_labels))
            sample_signatures[signature] += 1
            sample_signature_examples[signature].append(sid)

    all_results[path] = {
        "counts": dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))),
        "examples": {k: v[:10] for k, v in examples.items()},
        "field_counts": {
            field: dict(sorted(field_counts[field].items(), key=lambda item: (-item[1], item[0])))
            for field in field_counts
        },
        "field_examples": {
            field: {k: v[:10] for k, v in field_examples[field].items()}
            for field in field_examples
        },
        "sample_signatures": dict(
            sorted(sample_signatures.items(), key=lambda item: (-item[1], item[0]))
        ),
        "sample_signature_examples": {
            k: v[:10] for k, v in sample_signature_examples.items()
        },
    }

lines = []
lines.append("# Error Type Analysis")
lines.append("")
lines.append("Reference baseline: Path O")
lines.append("")
lines.append("Error taxonomy:")
lines.append("- scalar field errors: missing, wrong value, or spurious prediction")
lines.append("- waypoint errors: missed all, missing points, extra points, mixed missing+extra, or spurious only")
lines.append("- sample-level signatures: the most common combinations of errors on the same sample")

for path in PATHS:
    result = all_results[path]
    counts = result["counts"]
    lines.append("")
    lines.append(f"## Path {path}")
    lines.append("")

    top_items = list(counts.items())[:12]
    lines.append("### Major Error Types")
    lines.append("")
    lines.append("| ErrorType | Count | Coverage | ExampleSamples |")
    lines.append("|-----------|-------|----------|----------------|")
    for label, count in top_items:
        example_text = ", ".join(top_examples(result["examples"], label))
        lines.append(
            f"| {label} | {count} | {fmt_percent(count, len(sample_ids))} | {example_text} |"
        )

    lines.append("")
    lines.append("### By Field")
    for field in CORE_FIELDS + ["waypoints"]:
        field_items = list(result["field_counts"][field].items())[:5]
        if not field_items:
            continue
        lines.append("")
        lines.append(f"#### {field}")
        lines.append("")
        lines.append("| ErrorType | Count | ExampleSamples |")
        lines.append("|-----------|-------|----------------|")
        for label, count in field_items:
            example_text = ", ".join(top_examples(result["field_examples"][field], label))
            lines.append(f"| {label} | {count} | {example_text} |")

    lines.append("")
    lines.append("### Common Sample-Level Error Patterns")
    lines.append("")
    lines.append("| Pattern | Count | ExampleSamples |")
    lines.append("|---------|-------|----------------|")
    for signature, count in list(result["sample_signatures"].items())[:8]:
        example_text = ", ".join(top_examples(result["sample_signature_examples"], signature))
        lines.append(f"| {signature} | {count} | {example_text} |")

report_text = "\n".join(lines) + "\n"
REPORT.write_text(report_text, encoding="utf-8")
JSON_OUT.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")

print(report_text)
print(f"Report written to {REPORT}")
print(f"JSON written to {JSON_OUT}")
