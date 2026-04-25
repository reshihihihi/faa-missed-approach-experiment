"""
Score B1/B3/B3V2/B3V3 method outputs against CIFP-derived canonical proxy GT.

This is a pilot scorer for the PR #28 canonical schema. It reports:
  - leg_count exact accuracy
  - Q-field indexed-leg accuracy
  - per-sample mismatch details

The scorer is intentionally simple and transparent. It aligns legs by
leg_index, because Issue #25/#26 still treat visual-to-leg mapping as an
explicit research subtask rather than an already-solved alignment problem.
"""

from __future__ import annotations

import argparse
import json
import os
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


def score_method(method: str, method_dir: Path) -> dict[str, Any]:
    gt_files = sorted(GT_DIR.glob("*.json"))
    aggregate = {
        "charts": 0,
        "outputs": 0,
        "leg_count_exact": 0,
        "chart_exact": 0,
        "q_total": 0,
        "q_match": 0,
        "extra_pred_legs": 0,
        "missing_pred_legs": 0,
        "per_q": {field: {"total": 0, "match": 0} for field in Q_FIELDS},
    }
    per_sample = {}
    mismatches = []

    for gt_file in gt_files:
        gt = read_json(gt_file)
        chart_id = gt["chart_id"]
        pred_file = method_dir / f"{chart_id}.json"
        pred = read_json(pred_file) if pred_file.exists() else None
        aggregate["charts"] += 1
        if pred is not None:
            aggregate["outputs"] += 1

        sample = {
            "chart_id": chart_id,
            "has_output": pred is not None,
            "leg_count_exact": False,
            "q_total": 0,
            "q_match": 0,
            "q_accuracy": None,
            "field_matches": {},
        }

        if pred is None:
            per_sample[chart_id] = sample
            mismatches.append({"chart_id": chart_id, "type": "missing_output"})
            continue

        gt_leg_count = gt["missed_approach"]["leg_count"]
        pred_leg_count = pred["missed_approach"]["leg_count"]
        leg_count_exact = answer_equal(pred_leg_count, gt_leg_count)
        sample["leg_count_exact"] = leg_count_exact
        if leg_count_exact:
            aggregate["leg_count_exact"] += 1
        else:
            mismatches.append(
                {
                    "chart_id": chart_id,
                    "type": "leg_count",
                    "pred": pred_leg_count,
                    "gt": gt_leg_count,
                }
            )

        gt_legs = leg_map(gt)
        pred_legs = leg_map(pred)
        extra = max(0, len(pred_legs) - len(gt_legs))
        missing = max(0, len(gt_legs) - len(pred_legs))
        aggregate["extra_pred_legs"] += extra
        aggregate["missing_pred_legs"] += missing

        all_fields_match = leg_count_exact
        for leg_index in sorted(gt_legs.keys()):
            gt_answers = gt_legs[leg_index].get("answers", {})
            pred_answers = pred_legs.get(leg_index, {}).get("answers", {})
            for field in Q_FIELDS:
                sample["q_total"] += 1
                aggregate["q_total"] += 1
                aggregate["per_q"][field]["total"] += 1
                matched = answer_equal(pred_answers.get(field), gt_answers.get(field))
                sample["field_matches"][f"leg{leg_index}.{field}"] = matched
                if matched:
                    sample["q_match"] += 1
                    aggregate["q_match"] += 1
                    aggregate["per_q"][field]["match"] += 1
                else:
                    all_fields_match = False
                    mismatches.append(
                        {
                            "chart_id": chart_id,
                            "leg_index": leg_index,
                            "field": field,
                            "pred": pred_answers.get(field),
                            "gt": gt_answers.get(field),
                        }
                    )

        if extra:
            all_fields_match = False
            mismatches.append(
                {
                    "chart_id": chart_id,
                    "type": "extra_pred_legs",
                    "pred_leg_count": len(pred_legs),
                    "gt_leg_count": len(gt_legs),
                }
            )
        if missing:
            all_fields_match = False

        sample["q_accuracy"] = sample["q_match"] / sample["q_total"] if sample["q_total"] else None
        if all_fields_match:
            aggregate["chart_exact"] += 1
        per_sample[chart_id] = sample

    metrics = {
        "method": method,
        "aggregate": aggregate,
        "summary": {
            "output_coverage": aggregate["outputs"] / aggregate["charts"] if aggregate["charts"] else None,
            "leg_count_accuracy": aggregate["leg_count_exact"] / aggregate["charts"] if aggregate["charts"] else None,
            "q_field_accuracy": aggregate["q_match"] / aggregate["q_total"] if aggregate["q_total"] else None,
            "chart_exact_rate": aggregate["chart_exact"] / aggregate["charts"] if aggregate["charts"] else None,
            "per_q_accuracy": {
                field: (
                    stats["match"] / stats["total"] if stats["total"] else None
                )
                for field, stats in aggregate["per_q"].items()
            },
        },
        "per_sample": per_sample,
        "mismatches": mismatches,
    }
    return metrics


def fmt(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_report(results: dict[str, Any]) -> None:
    lines = ["# B1/B3/B3V2/B3V3 Pilot Evaluation", ""]
    lines.append("Reference: CIFP-derived canonical proxy JSON under `targets/canonical_proxy_gt_10`.")
    lines.append("")
    lines.append("Numeric courses/radials are compared with +/-0.51 tolerance to avoid punishing display rounding such as 063 vs 063.3.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Method | Coverage | LegCountAcc | QFieldAcc | ChartExact | ExtraPredLegs | MissingPredLegs |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for method, data in results.items():
        summary = data["summary"]
        agg = data["aggregate"]
        lines.append(
            f"| {method} | {fmt(summary['output_coverage'])} | {fmt(summary['leg_count_accuracy'])} | "
            f"{fmt(summary['q_field_accuracy'])} | {fmt(summary['chart_exact_rate'])} | "
            f"{agg['extra_pred_legs']} | {agg['missing_pred_legs']} |"
        )

    lines.append("")
    lines.append("## Per-Q Accuracy")
    lines.append("")
    lines.append("| Method | Q_terminator | Q1_fix_ident | Q2_altitude_constraint | Q3_turn | Q4_course_or_radial | Q5_hold_params |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for method, data in results.items():
        pq = data["summary"]["per_q_accuracy"]
        lines.append(
            f"| {method} | " + " | ".join(fmt(pq[field]) for field in Q_FIELDS) + " |"
        )

    lines.append("")
    lines.append("## Per-Sample")
    for method, data in results.items():
        lines.append("")
        lines.append(f"### {method}")
        lines.append("")
        lines.append("| Chart | Output | LegCountExact | QMatch | QTotal | QAccuracy |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for chart_id, sample in sorted(data["per_sample"].items()):
            lines.append(
                f"| {chart_id} | {sample['has_output']} | {sample['leg_count_exact']} | "
                f"{sample['q_match']} | {sample['q_total']} | {fmt(sample['q_accuracy'])} |"
            )

    (OUT_DIR / "b1_b3_pilot_evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Score B1/B3/B3V2/B3V3 pilot outputs.")
    parser.add_argument("--root", default=str(ROOT), help="B1-B3 working root.")
    args = parser.parse_args()
    configure_paths(Path(args.root))

    results = {method: score_method(method, path) for method, path in METHODS.items()}
    write_json(OUT_DIR / "b1_b3_pilot_metrics.json", results)
    write_json(
        OUT_DIR / "b1_b3_pilot_mismatches.json",
        {method: data["mismatches"] for method, data in results.items()},
    )
    write_report(results)
    print((OUT_DIR / "b1_b3_pilot_evaluation.md").read_text(encoding="utf-8"))
    print(f"Wrote {OUT_DIR / 'b1_b3_pilot_metrics.json'}")
    print(f"Wrote {OUT_DIR / 'b1_b3_pilot_mismatches.json'}")


if __name__ == "__main__":
    main()
