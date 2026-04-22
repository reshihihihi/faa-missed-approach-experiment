"""
Evaluate paths A/B/C/D against Path O.

This report keeps two complementary views:
1. field-level precision / recall / F1 for the core schema fields
2. sample-level exactness summaries and waypoint set overlap
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from dataset_config import MANIFEST_PATH, RESULTS_DIR

MANIFEST = MANIFEST_PATH
RESULTS = RESULTS_DIR
PATHS = ["A", "B", "C", "D", "E"]
REPORT = RESULTS / "evaluation_report.md"
METRICS_JSON = RESULTS / "all_metrics.json"

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


def field_confusion(field, pred_record, ref_record):
    pred_value = pred_record[field]
    ref_value = ref_record[field]
    applicable = is_applicable(field, ref_value, ref_record)
    predicted = is_predicted(field, pred_value, pred_record)

    if not applicable:
        if predicted:
            return {"tp": 0, "fp": 1, "fn": 0}
        return {"tp": 0, "fp": 0, "fn": 0}

    if not predicted:
        return {"tp": 0, "fp": 0, "fn": 1}

    if pred_value == ref_value:
        return {"tp": 1, "fp": 0, "fn": 0}

    return {"tp": 0, "fp": 1, "fn": 1}


def waypoint_stats(pred_record, ref_record, has_output=True):
    pred = pred_record["waypoints"]
    ref = ref_record["waypoints"]
    if not has_output:
        return {"tp": 0, "fp": 0, "fn": len(ref), "jaccard": 0.0, "exact": False}
    tp = len(pred & ref)
    fp = len(pred - ref)
    fn = len(ref - pred)
    union = pred | ref
    jaccard = 1.0 if not union else len(pred & ref) / len(union)
    exact = pred == ref
    return {"tp": tp, "fp": fp, "fn": fn, "jaccard": jaccard, "exact": exact}


def safe_div(num, den):
    return num / den if den else None


def f1(precision, recall):
    if precision is None or recall is None or precision + recall == 0:
        return None
    return 2 * precision * recall / (precision + recall)


def fmt(value, decimals=3):
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.{decimals}f}"
    return str(value)


with open(MANIFEST, encoding="utf-8") as f:
    manifest = json.load(f)

sample_ids = [entry["id"] for entry in manifest]
refs = {
    sid: normalize_record(load_json_safe(RESULTS / "O" / f"{sid}.json"))
    for sid in sample_ids
}

all_results = {}

for path in PATHS:
    path_dir = RESULTS / path
    per_sample = {}
    aggregate = {
        "fields": {field: {"tp": 0, "fp": 0, "fn": 0} for field in CORE_FIELDS},
        "waypoints": {"tp": 0, "fp": 0, "fn": 0, "jaccard_total": 0.0, "exact_count": 0},
        "samples_with_output": 0,
    }

    for sid in sample_ids:
        pred_raw = load_json_safe(path_dir / f"{sid}.json")
        pred = normalize_record(pred_raw)
        ref = refs[sid]

        has_output = pred_raw is not None
        if has_output:
            aggregate["samples_with_output"] += 1

        sample_metrics = {
            "has_output": has_output,
            "field_matches": {},
        }

        scalar_match_values = []
        for field in CORE_FIELDS:
            confusion = field_confusion(field, pred, ref)
            for key in ("tp", "fp", "fn"):
                aggregate["fields"][field][key] += confusion[key]

            applicable = is_applicable(field, ref[field], ref)
            predicted = is_predicted(field, pred[field], pred)
            matched = applicable and predicted and pred[field] == ref[field]
            sample_metrics["field_matches"][field] = matched if applicable else None
            if applicable:
                scalar_match_values.append(1 if matched else 0)

        wp = waypoint_stats(pred, ref, has_output=has_output)
        aggregate["waypoints"]["tp"] += wp["tp"]
        aggregate["waypoints"]["fp"] += wp["fp"]
        aggregate["waypoints"]["fn"] += wp["fn"]
        aggregate["waypoints"]["jaccard_total"] += wp["jaccard"]
        aggregate["waypoints"]["exact_count"] += 1 if wp["exact"] else 0

        sample_metrics["waypoints_jaccard"] = wp["jaccard"]
        sample_metrics["waypoints_exact"] = wp["exact"]
        sample_metrics["scalar_exact_rate"] = (
            sum(scalar_match_values) / len(scalar_match_values) if scalar_match_values else None
        )
        per_sample[sid] = sample_metrics

    all_results[path] = {
        "per_sample": per_sample,
        "aggregate": aggregate,
    }

lines = []
lines.append("# Experiment Evaluation Report")
lines.append("")
lines.append("Reference baseline: Path O")
lines.append("")
lines.append("## Summary")
lines.append("")
lines.append("| Path | OutputCoverage | ScalarPrecision | ScalarRecall | ScalarF1 | WaypointPrecision | WaypointRecall | WaypointF1 | MeanWaypointJaccard | WaypointExactRate |")
lines.append("|------|----------------|-----------------|--------------|----------|-------------------|----------------|------------|---------------------|-------------------|")

for path in PATHS:
    aggregate = all_results[path]["aggregate"]

    scalar_tp = sum(item["tp"] for item in aggregate["fields"].values())
    scalar_fp = sum(item["fp"] for item in aggregate["fields"].values())
    scalar_fn = sum(item["fn"] for item in aggregate["fields"].values())
    scalar_precision = safe_div(scalar_tp, scalar_tp + scalar_fp)
    scalar_recall = safe_div(scalar_tp, scalar_tp + scalar_fn)
    scalar_f1 = f1(scalar_precision, scalar_recall)

    wp_tp = aggregate["waypoints"]["tp"]
    wp_fp = aggregate["waypoints"]["fp"]
    wp_fn = aggregate["waypoints"]["fn"]
    wp_precision = safe_div(wp_tp, wp_tp + wp_fp)
    wp_recall = safe_div(wp_tp, wp_tp + wp_fn)
    wp_f1 = f1(wp_precision, wp_recall)

    coverage = aggregate["samples_with_output"] / len(sample_ids)
    mean_jaccard = aggregate["waypoints"]["jaccard_total"] / len(sample_ids)
    exact_rate = aggregate["waypoints"]["exact_count"] / len(sample_ids)

    lines.append(
        f"| {path} | {fmt(coverage)} | {fmt(scalar_precision)} | {fmt(scalar_recall)} | "
        f"{fmt(scalar_f1)} | {fmt(wp_precision)} | {fmt(wp_recall)} | {fmt(wp_f1)} | "
        f"{fmt(mean_jaccard)} | {fmt(exact_rate)} |"
    )

lines.append("")
lines.append("## Field Details")

for path in PATHS:
    aggregate = all_results[path]["aggregate"]
    lines.append("")
    lines.append(f"### Path {path}")
    lines.append("")
    lines.append("| Field | TP | FP | FN | Precision | Recall | F1 |")
    lines.append("|-------|----|----|----|-----------|--------|----|")
    for field in CORE_FIELDS:
        stats = aggregate["fields"][field]
        precision = safe_div(stats["tp"], stats["tp"] + stats["fp"])
        recall = safe_div(stats["tp"], stats["tp"] + stats["fn"])
        score = f1(precision, recall)
        lines.append(
            f"| {field} | {stats['tp']} | {stats['fp']} | {stats['fn']} | "
            f"{fmt(precision)} | {fmt(recall)} | {fmt(score)} |"
        )

    wp = aggregate["waypoints"]
    wp_precision = safe_div(wp["tp"], wp["tp"] + wp["fp"])
    wp_recall = safe_div(wp["tp"], wp["tp"] + wp["fn"])
    wp_score = f1(wp_precision, wp_recall)
    lines.append(
        f"| waypoints | {wp['tp']} | {wp['fp']} | {wp['fn']} | "
        f"{fmt(wp_precision)} | {fmt(wp_recall)} | {fmt(wp_score)} |"
    )

lines.append("")
lines.append("## Per-Sample Snapshot")

for path in PATHS:
    lines.append("")
    lines.append(f"### Path {path}")
    lines.append("")
    lines.append("| Sample | Output | ScalarExactRate | WaypointsExact | WaypointsJaccard |")
    lines.append("|--------|--------|-----------------|----------------|------------------|")
    for sid in sample_ids:
        sample = all_results[path]["per_sample"][sid]
        lines.append(
            f"| {sid} | {sample['has_output']} | {fmt(sample['scalar_exact_rate'])} | "
            f"{sample['waypoints_exact']} | {fmt(sample['waypoints_jaccard'])} |"
        )

report_text = "\n".join(lines) + "\n"
REPORT.write_text(report_text, encoding="utf-8")
METRICS_JSON.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")

print(report_text)
print(f"Report written to {REPORT}")
print(f"Detailed metrics written to {METRICS_JSON}")
