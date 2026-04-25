"""
Extended B1/B3/B3V2/B3V3 evaluation for the pilot dataset.

This script keeps the original transparent indexed-leg scorer intact and adds
the evaluation dimensions needed for the stricter experiment report:

- exact precision/recall/F1 on GT-aligned Q fields
- false positive / false negative / wrong-value breakdown
- relation labels: supported, partial, not_observable, contradicted
- over-assertion / under-assertion rates
- chart-level bootstrap confidence intervals

The alignment remains leg_index based, matching the current experiment design:
visual-to-leg alignment is itself a research issue, so the scorer does not
silently re-order predicted legs.
"""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.getenv("FAA_B1_B3_ROOT", REPO_ROOT)).expanduser().resolve()
GT_DIR = ROOT / "targets/canonical_proxy_gt_10"
OUT_DIR = ROOT / "outputs/evaluation"
METHODS = {
    "B1": ROOT / "outputs/B1_ocr_llm/method_outputs",
    "B3": ROOT / "outputs/B3_region_ocr_llm/method_outputs",
    "B3V2": ROOT / "outputs/B3_region_ocr_llm_v2/method_outputs",
    "B3V3": ROOT / "outputs/B3_region_ocr_llm_v3/method_outputs",
}
Q_FIELDS = [
    "Q_terminator",
    "Q1_fix_ident",
    "Q2_altitude_constraint",
    "Q3_turn",
    "Q4_course_or_radial",
    "Q5_hold_params",
]
NON_PRESENT_STATUSES = {"not_applicable", "not_observable", "unknown"}
BOOTSTRAP_SEED = 4242
BOOTSTRAP_ROUNDS = 5000


def configure_paths(root: Path) -> None:
    global ROOT, GT_DIR, OUT_DIR, METHODS
    ROOT = root.expanduser().resolve()
    GT_DIR = ROOT / "targets/canonical_proxy_gt_10"
    OUT_DIR = ROOT / "outputs/evaluation"
    METHODS = {
        "B1": ROOT / "outputs/B1_ocr_llm/method_outputs",
        "B3": ROOT / "outputs/B3_region_ocr_llm/method_outputs",
        "B3V2": ROOT / "outputs/B3_region_ocr_llm_v2/method_outputs",
        "B3V3": ROOT / "outputs/B3_region_ocr_llm_v3/method_outputs",
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm_number(value: Any) -> Any:
    if isinstance(value, int):
        return float(value)
    if isinstance(value, float):
        return value
    return value


def values_equal(a: Any, b: Any) -> bool:
    a = norm_number(a)
    b = norm_number(b)
    if isinstance(a, float) and isinstance(b, float):
        return abs(a - b) <= 0.51
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(values_equal(a[key], b[key]) for key in a.keys())
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(values_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().upper() == b.strip().upper()
    return a == b


def answer_equal(pred: dict[str, Any] | None, gt: dict[str, Any] | None) -> bool:
    if not isinstance(pred, dict) or not isinstance(gt, dict):
        return False
    if pred.get("status") != gt.get("status"):
        return False
    return values_equal(pred.get("value"), gt.get("value"))


def leg_map(doc: dict[str, Any]) -> dict[int, dict[str, Any]]:
    result = {}
    for leg in doc.get("missed_approach", {}).get("legs", []):
        if isinstance(leg, dict) and isinstance(leg.get("leg_index"), int):
            result[leg["leg_index"]] = leg
    return result


def is_present(answer: dict[str, Any] | None) -> bool:
    return isinstance(answer, dict) and answer.get("status") == "present"


def partial_value_score(pred_value: Any, gt_value: Any) -> float:
    """Return a loose overlap score used only for error taxonomy, not accuracy."""
    if values_equal(pred_value, gt_value):
        return 1.0
    if isinstance(pred_value, dict) and isinstance(gt_value, dict):
        common = sorted(set(pred_value.keys()) & set(gt_value.keys()))
        if not common:
            return 0.0
        matches = sum(1 for key in common if values_equal(pred_value.get(key), gt_value.get(key)))
        return matches / len(set(pred_value.keys()) | set(gt_value.keys()))
    if isinstance(pred_value, str) and isinstance(gt_value, str):
        pred_norm = pred_value.strip().upper()
        gt_norm = gt_value.strip().upper()
        if pred_norm and gt_norm and (pred_norm in gt_norm or gt_norm in pred_norm):
            return 0.5
    return 0.0


def relation_label(pred: dict[str, Any] | None, gt: dict[str, Any] | None) -> str:
    if answer_equal(pred, gt):
        return "supported"
    if not isinstance(pred, dict):
        return "not_observable"
    if pred.get("status") in {"not_observable", "unknown"} and is_present(gt):
        return "not_observable"
    if isinstance(gt, dict) and pred.get("status") in NON_PRESENT_STATUSES and gt.get("status") in NON_PRESENT_STATUSES:
        return "partial"
    if is_present(pred) and is_present(gt) and partial_value_score(pred.get("value"), gt.get("value")) > 0:
        return "partial"
    return "contradicted"


def classify_field(pred: dict[str, Any] | None, gt: dict[str, Any]) -> str:
    if answer_equal(pred, gt):
        return "exact_match"
    pred_present = is_present(pred)
    gt_present = is_present(gt)
    if pred_present and gt_present:
        return "wrong_value"
    if pred_present and not gt_present:
        return "false_positive"
    if not pred_present and gt_present:
        return "false_negative"
    return "nonpresent_status_mismatch"


def safe_div(num: float, den: float) -> float | None:
    return num / den if den else None


def summarize_counts(counts: dict[str, int]) -> dict[str, float | int | None]:
    tp = counts["exact_present_match"]
    fp = counts["false_positive"]
    fn = counts["false_negative"]
    wrong = counts["wrong_value"]
    total = counts["field_total"]
    precision = safe_div(tp, tp + fp + wrong)
    recall = safe_div(tp, tp + fn + wrong)
    if precision is None or recall is None or precision + recall == 0:
        f1 = None
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "exact_precision": precision,
        "exact_recall": recall,
        "exact_f1": f1,
        "false_positive_rate": safe_div(fp, total),
        "false_negative_rate": safe_div(fn, total),
        "wrong_value_rate": safe_div(wrong, total),
        "over_assertion_rate": safe_div(fp, total),
        "under_assertion_rate": safe_div(fn, total),
    }


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = (len(ordered) - 1) * pct
    lower = int(idx)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return ordered[lower]
    weight = idx - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def bootstrap_ci(samples: list[dict[str, Any]], key_num: str, key_den: str) -> dict[str, float | None]:
    usable = [sample for sample in samples if sample[key_den] > 0]
    if not usable:
        return {"mean": None, "ci95_low": None, "ci95_high": None}
    rng = random.Random(BOOTSTRAP_SEED)
    estimates = []
    for _ in range(BOOTSTRAP_ROUNDS):
        draw = [rng.choice(usable) for _ in range(len(usable))]
        num = sum(sample[key_num] for sample in draw)
        den = sum(sample[key_den] for sample in draw)
        estimates.append(num / den if den else 0.0)
    observed = sum(sample[key_num] for sample in usable) / sum(sample[key_den] for sample in usable)
    return {
        "mean": observed,
        "ci95_low": percentile(estimates, 0.025),
        "ci95_high": percentile(estimates, 0.975),
    }


def score_method(method: str, method_dir: Path) -> dict[str, Any]:
    gt_files = sorted(GT_DIR.glob("*.json"))
    counts = {
        "charts": 0,
        "outputs": 0,
        "field_total": 0,
        "exact_field_match": 0,
        "exact_present_match": 0,
        "true_negative": 0,
        "false_positive": 0,
        "false_negative": 0,
        "wrong_value": 0,
        "nonpresent_status_mismatch": 0,
        "leg_count_exact": 0,
        "chart_exact": 0,
        "extra_pred_legs": 0,
        "missing_pred_legs": 0,
    }
    per_q = {
        field: {
            "total": 0,
            "exact_match": 0,
            "exact_present_match": 0,
            "false_positive": 0,
            "false_negative": 0,
            "wrong_value": 0,
            "nonpresent_status_mismatch": 0,
        }
        for field in Q_FIELDS
    }
    relation_counts = {
        "supported": 0,
        "partial": 0,
        "not_observable": 0,
        "contradicted": 0,
    }
    per_sample = {}
    detailed_errors = []

    for gt_file in gt_files:
        gt = read_json(gt_file)
        chart_id = gt["chart_id"]
        pred_file = method_dir / f"{chart_id}.json"
        pred = read_json(pred_file) if pred_file.exists() else None
        counts["charts"] += 1
        if pred is not None:
            counts["outputs"] += 1

        sample = {
            "chart_id": chart_id,
            "has_output": pred is not None,
            "q_total": 0,
            "q_exact_match": 0,
            "leg_count_total": 1,
            "leg_count_match": 0,
            "chart_exact_match": 0,
            "false_positive": 0,
            "false_negative": 0,
            "wrong_value": 0,
            "relation_counts": {key: 0 for key in relation_counts},
        }

        if pred is None:
            per_sample[chart_id] = sample
            detailed_errors.append({"chart_id": chart_id, "type": "missing_output"})
            continue

        gt_leg_count = gt["missed_approach"]["leg_count"]
        pred_leg_count = pred["missed_approach"]["leg_count"]
        leg_count_exact = answer_equal(pred_leg_count, gt_leg_count)
        if leg_count_exact:
            counts["leg_count_exact"] += 1
            sample["leg_count_match"] = 1

        gt_legs = leg_map(gt)
        pred_legs = leg_map(pred)
        extra = max(0, len(pred_legs) - len(gt_legs))
        missing = max(0, len(gt_legs) - len(pred_legs))
        counts["extra_pred_legs"] += extra
        counts["missing_pred_legs"] += missing

        chart_exact = leg_count_exact and extra == 0 and missing == 0
        for leg_index in sorted(gt_legs.keys()):
            gt_answers = gt_legs[leg_index].get("answers", {})
            pred_answers = pred_legs.get(leg_index, {}).get("answers", {})
            for field in Q_FIELDS:
                gt_answer = gt_answers[field]
                pred_answer = pred_answers.get(field)
                class_name = classify_field(pred_answer, gt_answer)
                relation = relation_label(pred_answer, gt_answer)

                counts["field_total"] += 1
                per_q[field]["total"] += 1
                relation_counts[relation] += 1
                sample["relation_counts"][relation] += 1
                sample["q_total"] += 1

                if class_name == "exact_match":
                    counts["exact_field_match"] += 1
                    per_q[field]["exact_match"] += 1
                    sample["q_exact_match"] += 1
                    if is_present(gt_answer):
                        counts["exact_present_match"] += 1
                        per_q[field]["exact_present_match"] += 1
                    else:
                        counts["true_negative"] += 1
                else:
                    chart_exact = False
                    if class_name in counts:
                        counts[class_name] += 1
                    if class_name in per_q[field]:
                        per_q[field][class_name] += 1
                    if class_name in {"false_positive", "false_negative", "wrong_value"}:
                        sample[class_name] += 1
                    detailed_errors.append(
                        {
                            "chart_id": chart_id,
                            "leg_index": leg_index,
                            "field": field,
                            "error_type": class_name,
                            "relation": relation,
                            "pred": pred_answer,
                            "gt": gt_answer,
                        }
                    )

        if chart_exact:
            counts["chart_exact"] += 1
            sample["chart_exact_match"] = 1
        if extra:
            detailed_errors.append(
                {
                    "chart_id": chart_id,
                    "type": "extra_pred_legs",
                    "pred_leg_count": len(pred_legs),
                    "gt_leg_count": len(gt_legs),
                }
            )
        if missing:
            detailed_errors.append(
                {
                    "chart_id": chart_id,
                    "type": "missing_pred_legs",
                    "pred_leg_count": len(pred_legs),
                    "gt_leg_count": len(gt_legs),
                }
            )

        per_sample[chart_id] = sample

    samples = list(per_sample.values())
    summary = {
        "output_coverage": safe_div(counts["outputs"], counts["charts"]),
        "leg_count_accuracy": safe_div(counts["leg_count_exact"], counts["charts"]),
        "q_field_accuracy": safe_div(counts["exact_field_match"], counts["field_total"]),
        "chart_exact_rate": safe_div(counts["chart_exact"], counts["charts"]),
        **summarize_counts(counts),
        "relation_rates": {
            key: safe_div(value, counts["field_total"]) for key, value in relation_counts.items()
        },
        "per_q": {
            field: {
                "exact_accuracy": safe_div(stats["exact_match"], stats["total"]),
                "exact_present_precision": safe_div(
                    stats["exact_present_match"],
                    stats["exact_present_match"] + stats["false_positive"] + stats["wrong_value"],
                ),
                "exact_present_recall": safe_div(
                    stats["exact_present_match"],
                    stats["exact_present_match"] + stats["false_negative"] + stats["wrong_value"],
                ),
                "false_positive_rate": safe_div(stats["false_positive"], stats["total"]),
                "false_negative_rate": safe_div(stats["false_negative"], stats["total"]),
                "wrong_value_rate": safe_div(stats["wrong_value"], stats["total"]),
            }
            for field, stats in per_q.items()
        },
        "bootstrap_ci": {
            "q_field_accuracy": bootstrap_ci(samples, "q_exact_match", "q_total"),
            "leg_count_accuracy": bootstrap_ci(samples, "leg_count_match", "leg_count_total"),
            "chart_exact_rate": bootstrap_ci(samples, "chart_exact_match", "leg_count_total"),
        },
    }

    return {
        "method": method,
        "counts": counts,
        "relation_counts": relation_counts,
        "per_q_counts": per_q,
        "summary": summary,
        "per_sample": per_sample,
        "detailed_errors": detailed_errors,
    }


def fmt(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def fmt_ci(ci: dict[str, float | None]) -> str:
    if ci["mean"] is None:
        return "N/A"
    return f"{fmt(ci['mean'])} [{fmt(ci['ci95_low'])}, {fmt(ci['ci95_high'])}]"


def write_report(results: dict[str, Any]) -> None:
    lines = ["# B1/B3 Extended Pilot Evaluation", ""]
    lines.append("Reference target: `targets/canonical_proxy_gt_10`.")
    lines.append("")
    lines.append("The scorer uses indexed-leg alignment and the PR #28 canonical Q-field schema.")
    lines.append("")
    lines.append("## Exact Extraction Metrics")
    lines.append("")
    lines.append("| Method | Coverage | QFieldAcc | Precision | Recall | F1 | ChartExact | ExtraLegs | MissingLegs |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for method, data in results.items():
        summary = data["summary"]
        counts = data["counts"]
        lines.append(
            f"| {method} | {fmt(summary['output_coverage'])} | {fmt(summary['q_field_accuracy'])} | "
            f"{fmt(summary['exact_precision'])} | {fmt(summary['exact_recall'])} | {fmt(summary['exact_f1'])} | "
            f"{fmt(summary['chart_exact_rate'])} | {counts['extra_pred_legs']} | {counts['missing_pred_legs']} |"
        )

    lines.append("")
    lines.append("## Error Breakdown")
    lines.append("")
    lines.append("| Method | WrongValue | FalsePositive | FalseNegative | NonPresentStatusMismatch | OverRate | UnderRate |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for method, data in results.items():
        counts = data["counts"]
        summary = data["summary"]
        lines.append(
            f"| {method} | {counts['wrong_value']} | {counts['false_positive']} | {counts['false_negative']} | "
            f"{counts['nonpresent_status_mismatch']} | {fmt(summary['over_assertion_rate'])} | "
            f"{fmt(summary['under_assertion_rate'])} |"
        )

    lines.append("")
    lines.append("## Relation Labels")
    lines.append("")
    lines.append("| Method | Supported | Partial | NotObservable | Contradicted |")
    lines.append("|---|---:|---:|---:|---:|")
    for method, data in results.items():
        rates = data["summary"]["relation_rates"]
        lines.append(
            f"| {method} | {fmt(rates['supported'])} | {fmt(rates['partial'])} | "
            f"{fmt(rates['not_observable'])} | {fmt(rates['contradicted'])} |"
        )

    lines.append("")
    lines.append("## Bootstrap 95% CI")
    lines.append("")
    lines.append("| Method | QFieldAcc CI | LegCountAcc CI | ChartExact CI |")
    lines.append("|---|---:|---:|---:|")
    for method, data in results.items():
        ci = data["summary"]["bootstrap_ci"]
        lines.append(
            f"| {method} | {fmt_ci(ci['q_field_accuracy'])} | "
            f"{fmt_ci(ci['leg_count_accuracy'])} | {fmt_ci(ci['chart_exact_rate'])} |"
        )

    lines.append("")
    lines.append("## Weakest Fields By Method")
    for method, data in results.items():
        lines.append("")
        lines.append(f"### {method}")
        per_q = data["summary"]["per_q"]
        ordered = sorted(per_q.items(), key=lambda item: (item[1]["exact_accuracy"] or 0))
        lines.append("")
        lines.append("| Q Field | ExactAcc | Precision | Recall | FP | FN | WrongValue |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for field, stats in ordered:
            counts = data["per_q_counts"][field]
            lines.append(
                f"| {field} | {fmt(stats['exact_accuracy'])} | {fmt(stats['exact_present_precision'])} | "
                f"{fmt(stats['exact_present_recall'])} | {counts['false_positive']} | "
                f"{counts['false_negative']} | {counts['wrong_value']} |"
            )

    path = OUT_DIR / "b1_b3_extended_evaluation.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run extended scoring for B1/B3/B3V2/B3V3 pilot outputs.")
    parser.add_argument("--root", default=str(ROOT), help="B1-B3 working root.")
    args = parser.parse_args()
    configure_paths(Path(args.root))

    results = {method: score_method(method, path) for method, path in METHODS.items()}
    write_json(OUT_DIR / "b1_b3_extended_metrics.json", results)
    write_json(
        OUT_DIR / "b1_b3_extended_errors.json",
        {method: data["detailed_errors"] for method, data in results.items()},
    )
    write_report(results)
    print((OUT_DIR / "b1_b3_extended_evaluation.md").read_text(encoding="utf-8"))
    print(f"Wrote {OUT_DIR / 'b1_b3_extended_metrics.json'}")
    print(f"Wrote {OUT_DIR / 'b1_b3_extended_errors.json'}")


if __name__ == "__main__":
    main()
