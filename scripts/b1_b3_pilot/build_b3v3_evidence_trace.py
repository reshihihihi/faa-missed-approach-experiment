"""
Build sidecar evidence traces for B3V3 method outputs.

The PR #28 output schema intentionally stays compact, so evidence is stored as
sidecar JSON instead of being inserted into method_outputs.  Each present Q
field is linked back to matching B3V3 candidate_legs or semantic_steps q_hints
when possible.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.getenv("FAA_B1_B3_ROOT", REPO_ROOT)).expanduser().resolve()
Q_FIELDS = [
    "Q_terminator",
    "Q1_fix_ident",
    "Q2_altitude_constraint",
    "Q3_turn",
    "Q4_course_or_radial",
    "Q5_hold_params",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().upper()
    if isinstance(value, dict):
        return {key: norm(child) for key, child in value.items()}
    if isinstance(value, list):
        return [norm(child) for child in value]
    return value


def numbers_close(a: Any, b: Any) -> bool:
    if isinstance(a, int | float) and isinstance(b, int | float):
        return abs(float(a) - float(b)) <= 0.51
    return False


def observed_matches_prediction(observed: Any, predicted: Any) -> bool:
    observed = norm(observed)
    predicted = norm(predicted)
    if observed == predicted:
        return True
    if numbers_close(observed, predicted):
        return True
    if isinstance(observed, list):
        return any(observed_matches_prediction(item, predicted) for item in observed)
    if isinstance(observed, dict) and isinstance(predicted, dict):
        return all(
            key in observed and observed_matches_prediction(observed.get(key), value)
            for key, value in predicted.items()
        )
    return False


def compact_cell(cell: dict[str, Any]) -> dict[str, Any]:
    return {
        "cell_id": cell.get("cell_id"),
        "cell_semantic_hint": cell.get("cell_semantic_hint"),
        "bbox": cell.get("bbox"),
        "ocr_texts": cell.get("ocr_texts", []),
        "observed_types": cell.get("observed_types", []),
        "source_element_ids": cell.get("source_element_ids", []),
    }


def cells_by_id(prompt_input: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cells = prompt_input.get("input_evidence", {}).get("visual_cells_ocr_only", [])
    return {
        str(cell.get("cell_id")): compact_cell(cell)
        for cell in cells
        if isinstance(cell, dict) and cell.get("cell_id")
    }


def resolve_cells(refs: list[str], cell_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    resolved = []
    seen = set()
    for ref in refs:
        if ref in seen or ref not in cell_lookup:
            continue
        seen.add(ref)
        resolved.append(cell_lookup[ref])
    return resolved


def matching_hints(
    field: str,
    predicted_value: Any,
    semantic_steps: list[dict[str, Any]],
    candidate_legs: list[dict[str, Any]],
    cell_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    matches = []
    sources = [
        ("candidate_leg", "candidate_ref", candidate_legs),
        ("semantic_step", "semantic_step_id", semantic_steps),
    ]
    for source_type, id_key, items in sources:
        for item in items:
            q_hints = item.get("q_hints", {})
            hint = q_hints.get(field)
            if not isinstance(hint, dict):
                continue
            observed = hint.get("observed_value")
            if observed_matches_prediction(observed, predicted_value):
                refs = hint.get("evidence_refs", item.get("evidence_refs", []))
                matches.append(
                    {
                        "source_type": source_type,
                        "source_id": item.get(id_key),
                        "semantic_step_id": item.get("semantic_step_id"),
                        "candidate_ref": item.get("candidate_ref"),
                        "action_type": item.get("action_type"),
                        "source_snippet": item.get("source_snippet"),
                        "evidence_refs": refs,
                        "resolved_evidence_cells": resolve_cells(refs, cell_lookup),
                        "hint_confidence": hint.get("confidence"),
                        "hint_status": hint.get("status_hint"),
                        "hint_value": observed,
                    }
                )
    return matches


def sample_maps(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    samples = read_json(root / "data/pilot10/sample_map_private.json")
    sample_to_chart = {item["sample_id"]: item["chart_id"] for item in samples}
    chart_to_sample = {item["chart_id"]: item["sample_id"] for item in samples}
    return sample_to_chart, chart_to_sample


def build_trace(root: Path, chart_id: str, sample_id: str) -> dict[str, Any]:
    method_output_path = root / "outputs/B3_region_ocr_llm_v3/method_outputs" / f"{chart_id}.json"
    prompt_input_path = root / "outputs/B3_region_ocr_llm_v3/prompt_inputs" / f"{sample_id}__prompt_input.json"
    semantic_path = root / "outputs/B3_region_ocr_llm_v3/semantic_steps" / f"{sample_id}__semantic_steps.json"
    method_output = read_json(method_output_path)
    prompt_input = read_json(prompt_input_path)
    semantic_steps = read_json(semantic_path)
    candidate_legs = prompt_input.get("input_evidence", {}).get("candidate_legs", [])
    cell_lookup = cells_by_id(prompt_input)

    field_traces = []
    for leg in method_output.get("missed_approach", {}).get("legs", []):
        leg_index = leg.get("leg_index")
        answers = leg.get("answers", {})
        for field in Q_FIELDS:
            answer = answers.get(field, {})
            if answer.get("status") != "present":
                continue
            predicted_value = answer.get("value")
            matches = matching_hints(field, predicted_value, semantic_steps, candidate_legs, cell_lookup)
            field_traces.append(
                {
                    "field_path": f"legs[{leg_index}].answers.{field}",
                    "predicted_value": predicted_value,
                    "trace_status": "matched" if matches else "unmatched",
                    "matching_semantic_hints": matches,
                }
            )

    matched = sum(1 for item in field_traces if item["trace_status"] == "matched")
    return {
        "chart_id": chart_id,
        "sample_id": sample_id,
        "method": "B3V3",
        "trace_policy": "sidecar only; not inserted into PR #28 method_output schema",
        "trace_summary": {
            "present_field_count": len(field_traces),
            "matched_field_count": matched,
            "matched_field_rate": round(matched / len(field_traces), 6) if field_traces else None,
        },
        "field_traces": field_traces,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build B3V3 sidecar evidence traces.")
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()

    root = Path(args.root)
    _, chart_to_sample = sample_maps(root)
    output_dir = root / "outputs/B3_region_ocr_llm_v3/evidence_traces"
    manifest = []
    for method_output_path in sorted((root / "outputs/B3_region_ocr_llm_v3/method_outputs").glob("*.json")):
        chart_id = method_output_path.stem
        sample_id = chart_to_sample[chart_id]
        trace = build_trace(root, chart_id, sample_id)
        trace_path = output_dir / f"{chart_id}__evidence_trace.json"
        write_json(trace_path, trace)
        manifest.append(
            {
                "chart_id": chart_id,
                "sample_id": sample_id,
                "trace": str(trace_path).replace("\\", "/"),
                "present_field_count": trace["trace_summary"]["present_field_count"],
                "matched_field_count": trace["trace_summary"]["matched_field_count"],
                "matched_field_rate": trace["trace_summary"]["matched_field_rate"],
            }
        )
    write_json(root / "outputs/B3_region_ocr_llm_v3/evidence_trace_manifest.json", manifest)
    print(f"Wrote {len(manifest)} B3V3 evidence traces to {output_dir}")


if __name__ == "__main__":
    main()
