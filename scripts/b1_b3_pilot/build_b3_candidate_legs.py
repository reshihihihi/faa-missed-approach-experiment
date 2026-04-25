"""
Build B3-v2 candidate-leg prompt inputs.

B3-v1 gives the LLM a flat list of region/element OCR candidates.  This script
adds the missing middle layer requested by the experiment design:

    boxes/OCR tokens -> visual cells -> candidate_legs -> LLM -> PR #28 JSON

The script intentionally reads only B3 prompt evidence produced from chart
images.  It does not read CIFP, chart_id, airport, procedure metadata, or any
canonical answers.  Output files keep opaque sample_id only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.getenv("FAA_B1_B3_ROOT", REPO_ROOT)).expanduser().resolve()
IN_DIR = ROOT / "outputs/B3_region_ocr_llm/prompt_inputs"
OUT_ROOT = ROOT / "outputs/B3_region_ocr_llm_v2"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_text(text: str) -> str:
    replacements = {
        "掳": "°",
        "Ёу": "°",
        "鈭?": "-",
        "−": "-",
        "–": "-",
        "—": "-",
        "／": "/",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text).strip()
    # Upper missed-approach crops sometimes include the communications row.
    text = re.split(r"\b(?:GND CON|CLNC DEL|UNICOM|D-ATIS|ASOS)\b", text, maxsplit=1)[0].strip()
    return text


def bbox_to_edges(bbox: dict[str, Any]) -> tuple[float, float, float, float]:
    xc = float(bbox.get("x_center", 0.0))
    yc = float(bbox.get("y_center", 0.0))
    w = float(bbox.get("width", 0.0))
    h = float(bbox.get("height", 0.0))
    return xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2


def union_bbox(items: list[dict[str, Any]]) -> dict[str, float] | None:
    boxes = [item.get("bbox") for item in items if isinstance(item.get("bbox"), dict)]
    if not boxes:
        return None
    edges = [bbox_to_edges(box) for box in boxes]
    x1 = min(edge[0] for edge in edges)
    y1 = min(edge[1] for edge in edges)
    x2 = max(edge[2] for edge in edges)
    y2 = max(edge[3] for edge in edges)
    return {
        "x_center": round((x1 + x2) / 2, 6),
        "y_center": round((y1 + y2) / 2, 6),
        "width": round(x2 - x1, 6),
        "height": round(y2 - y1, 6),
    }


def observed_text(item: dict[str, Any]) -> str:
    text = str(item.get("text") or "").strip()
    ocr = clean_text(str(item.get("ocr_text") or ""))
    if text and not text.lower().endswith("fix symbol"):
        return text
    return ocr


def compact_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "region_id": item.get("region_id"),
        "candidate_type": item.get("candidate_type"),
        "source_region_type": item.get("source_region_type"),
        "bbox": item.get("bbox"),
        "observed_text": observed_text(item),
        "ocr_text": clean_text(str(item.get("ocr_text") or "")),
        "prelabel_text": item.get("text", ""),
        "confidence": item.get("confidence"),
    }


def item_x(item: dict[str, Any]) -> float:
    bbox = item.get("bbox") if isinstance(item.get("bbox"), dict) else {}
    return float(bbox.get("x_center", 0.0))


def item_y(item: dict[str, Any]) -> float:
    bbox = item.get("bbox") if isinstance(item.get("bbox"), dict) else {}
    return float(bbox.get("y_center", 0.0))


def make_visual_cells(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(elements, key=lambda item: (item_x(item), item_y(item)))
    groups: list[list[dict[str, Any]]] = []
    threshold = 0.036
    for item in ordered:
        if not groups:
            groups.append([item])
            continue
        current = groups[-1]
        current_x = sum(item_x(member) for member in current) / len(current)
        if abs(item_x(item) - current_x) <= threshold:
            current.append(item)
        else:
            groups.append([item])

    cells = []
    for idx, group in enumerate(groups, start=1):
        types = sorted({str(item.get("source_region_type") or item.get("candidate_type") or "") for item in group})
        texts = [observed_text(item) for item in group if observed_text(item)]
        semantic = classify_cell(types, texts)
        cells.append(
            {
                "cell_id": f"cell_{idx:02d}",
                "bbox": union_bbox(group),
                "cell_semantic_hint": semantic,
                "observed_types": types,
                "observed_texts": texts,
                "source_element_ids": [item.get("region_id") for item in group],
                "source_elements": [compact_item(item) for item in group],
            }
        )
    return cells


def classify_cell(types: list[str], texts: list[str]) -> str:
    type_set = set(types)
    text = " ".join(texts).upper()
    if {"ALTITUDE_TEXT", "CLIMB_ARROW", "HEADING_TEXT"} & type_set == {
        "ALTITUDE_TEXT",
        "CLIMB_ARROW",
        "HEADING_TEXT",
    }:
        return "climb_altitude_heading_cell"
    if "ALTITUDE_TEXT" in type_set and "CLIMB_ARROW" in type_set:
        return "climb_altitude_cell"
    if "ALTITUDE_TEXT" in type_set and "PATH_SEGMENT" in type_set:
        return "turn_or_arc_altitude_cell"
    if "TRACK_OR_RADIAL_TEXT" in type_set:
        return "track_or_course_cell"
    if "RADIAL_TEXT" in type_set or re.search(r"\bR[- ]?\d{3}\b", text):
        return "navaid_radial_cell"
    if "FIX_SYMBOL" in type_set and ("FIX_TEXT" in type_set or "NAVAID_TEXT" in type_set):
        return "fix_or_navaid_symbol_cell"
    if "FIX_TEXT" in type_set:
        return "fix_text_cell"
    return "other_visible_cell"


def numbers_from_text(text: str) -> list[int]:
    return [int(match) for match in re.findall(r"\b\d{3,5}\b", text)]


def first_altitude(cell: dict[str, Any]) -> int | None:
    for element in cell.get("source_elements", []):
        if element.get("source_region_type") == "ALTITUDE_TEXT":
            nums = numbers_from_text(str(element.get("observed_text") or element.get("ocr_text") or ""))
            if nums:
                return nums[0]
    nums = numbers_from_text(" ".join(cell.get("observed_texts", [])))
    return nums[0] if nums else None


def course_from_text(text: str) -> int | None:
    match = re.search(r"\b(?:hdg|heading|tr|track)\s*([0-3]\d{2})\b", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"\b([0-3]\d{2})\s*°", text)
    if match:
        return int(match.group(1))
    return None


def heading_from_cell(cell: dict[str, Any]) -> int | None:
    for element in cell.get("source_elements", []):
        if element.get("source_region_type") in {"HEADING_TEXT", "TRACK_OR_RADIAL_TEXT"}:
            value = course_from_text(str(element.get("observed_text") or element.get("ocr_text") or ""))
            if value is not None:
                return value
    return course_from_text(" ".join(cell.get("observed_texts", [])))


def fix_from_cell(cell: dict[str, Any]) -> str | None:
    ignored = {"INT", "RADAR", "DME", "VORTAC", "VOR", "LOC", "LOCALIZER"}
    candidates = []
    for element in cell.get("source_elements", []):
        if element.get("source_region_type") in {"FIX_TEXT", "NAVAID_TEXT"}:
            for token in re.findall(r"\b[A-Z]{3,6}\b", str(element.get("observed_text") or element.get("ocr_text") or "").upper()):
                if token not in ignored:
                    candidates.append(token)
    return candidates[0] if candidates else None


def navaid_radial_from_cell(cell: dict[str, Any]) -> dict[str, Any] | None:
    text = " ".join(cell.get("observed_texts", [])).upper()
    navaid = None
    radial = None
    direction = None
    for element in cell.get("source_elements", []):
        etype = element.get("source_region_type")
        etext = str(element.get("observed_text") or element.get("ocr_text") or "").upper()
        if etype == "NAVAID_TEXT":
            token = re.search(r"\b[A-Z]{3,5}\b", etext)
            if token:
                navaid = token.group(0)
        if etype == "RADIAL_TEXT":
            match = re.search(r"\b(?:([A-Z]{2,5})\s*)?R[- ]?(\d{3})\b", etext)
            if match:
                if match.group(1):
                    navaid = match.group(1)
                radial = int(match.group(2))
        if etype == "OUTBOUND_INBOUND_MARK":
            if "OUT" in etext:
                direction = "outbound"
            if "IN" in etext:
                direction = "inbound"
    if direction is None:
        if "OUTB" in text:
            direction = "outbound"
        elif "INB" in text:
            direction = "inbound"
    if radial is None:
        match = re.search(r"\b(?:([A-Z]{2,5})\s*)?R[- ]?(\d{3})\b", text)
        if match:
            if match.group(1):
                navaid = match.group(1)
            radial = int(match.group(2))
    if navaid or radial is not None:
        return {"navaid": navaid, "radial_deg": radial, "direction": direction}
    return None


def text_fixes(text: str) -> list[str]:
    ignored = {
        "MISSED",
        "APPROACH",
        "CLIMB",
        "CLIMBING",
        "THEN",
        "LEFT",
        "RIGHT",
        "TURN",
        "DIRECT",
        "VORTAC",
        "VOR",
        "DME",
        "RADAR",
        "HOLD",
        "CONTINUE",
        "IN",
        "ON",
        "TO",
        "AND",
        "TRACK",
        "HEADING",
        "INT",
    }
    candidates: list[str] = []
    for token in re.findall(r"\b[A-Z]{3,6}\b", text.upper()):
        if token not in ignored and token not in candidates:
            candidates.append(token)
    return candidates


def turn_direction(text: str) -> str | None:
    match = re.search(r"\b(left|right)\s+turn\b", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


def turn_direction_from_cell(cell: dict[str, Any]) -> str | None:
    text = " ".join(
        str(element.get("observed_text") or element.get("ocr_text") or element.get("prelabel_text") or "")
        for element in cell.get("source_elements", [])
    )
    return turn_direction(text)


def has_hold(text: str, regions: list[dict[str, Any]]) -> bool:
    combined = text.upper()
    if "HOLD" in combined:
        return True
    # The missed-approach-fix inset is visual evidence that the terminal fix is
    # a holding fix, even when OCR clips "and hold" from the upper text crop.
    plan_text = " ".join(clean_text(str(region.get("ocr_text") or "")).upper() for region in regions)
    return "MISSED APCH FIX" in plan_text or "MISSED APPROACH FIX" in plan_text


def make_answer_hint(value: Any, source: str, confidence: str = "medium") -> dict[str, Any]:
    return {
        "observed_value": value,
        "evidence_source": source,
        "confidence": confidence,
    }


def cell_ref(cell: dict[str, Any]) -> dict[str, Any]:
    return {
        "cell_id": cell["cell_id"],
        "cell_semantic_hint": cell["cell_semantic_hint"],
        "bbox": cell.get("bbox"),
        "observed_texts": cell.get("observed_texts", []),
        "source_element_ids": cell.get("source_element_ids", []),
    }


def make_step(
    index: int,
    hint: str,
    cells: list[dict[str, Any]],
    reason: str,
    field_hints: dict[str, Any],
    confidence: str = "medium",
) -> dict[str, Any]:
    return {
        "step_id": f"step_{index:02d}",
        "visual_order": index,
        "step_type_hint": hint,
        "reason": reason,
        "bbox": union_bbox([{"bbox": cell.get("bbox")} for cell in cells if cell.get("bbox")]),
        "source_cells": [cell_ref(cell) for cell in cells],
        "field_hints": field_hints,
        "confidence": confidence,
        "llm_decision_needed": True,
    }


def nearest_right_cell(cells: list[dict[str, Any]], start_idx: int, wanted: set[str]) -> int | None:
    for idx in range(start_idx + 1, len(cells)):
        if cells[idx].get("cell_semantic_hint") in wanted:
            return idx
    return None


def make_candidate_steps(cells: list[dict[str, Any]], upper_text: str, regions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    consumed: set[int] = set()
    global_turn = turn_direction(upper_text)
    direct_fixes = set(re.findall(r"\bdirect\s+([A-Z]{3,6})\b", upper_text.upper()))
    fixes_in_text = text_fixes(upper_text)

    idx = 0
    while idx < len(cells):
        if idx in consumed:
            idx += 1
            continue
        cell = cells[idx]
        semantic = cell["cell_semantic_hint"]
        altitude = first_altitude(cell)
        heading = heading_from_cell(cell)

        if semantic == "climb_altitude_heading_cell":
            field_hints = {
                "Q_terminator": make_answer_hint(["VI", "VA", "CA"], "heading/climb cell", "low"),
            }
            if altitude is not None:
                field_hints["Q2_altitude_constraint"] = make_answer_hint(
                    {"desc": "AT_OR_ABOVE", "altitude_ft": altitude, "altitude_2_ft": None},
                    cell["cell_id"],
                )
            if heading is not None:
                field_hints["Q4_course_or_radial"] = make_answer_hint(
                    {"type": "course_deg", "course_deg": heading},
                    cell["cell_id"],
                )
            steps.append(
                make_step(
                    len(steps) + 1,
                    "initial_climb_on_heading_or_course",
                    [cell],
                    "A climb arrow, altitude, and heading/course text appear in the same lower missed-approach cell.",
                    field_hints,
                )
            )
            consumed.add(idx)

        elif semantic == "climb_altitude_cell":
            radial = navaid_radial_from_cell(cell)
            next_fix_idx = nearest_right_cell(cells, idx, {"fix_or_navaid_symbol_cell", "fix_text_cell"})
            next_fix = fix_from_cell(cells[next_fix_idx]) if next_fix_idx is not None else None
            if radial and next_fix:
                field_hints = {
                    "Q_terminator": make_answer_hint(["CF", "FA", "TF", "CA"], "climb cell with radial text", "low"),
                    "Q1_fix_ident": make_answer_hint(next_fix, cells[next_fix_idx]["cell_id"]),
                    "Q4_course_or_radial": make_answer_hint(
                        {
                            "type": "navaid_radial",
                            "navaid": radial.get("navaid"),
                            "radial_deg": radial.get("radial_deg"),
                            "direction": radial.get("direction"),
                        },
                        cell["cell_id"],
                    ),
                }
                if altitude is not None:
                    field_hints["Q2_altitude_constraint"] = make_answer_hint(
                        {"desc": "AT_OR_ABOVE", "altitude_ft": altitude, "altitude_2_ft": None},
                        cell["cell_id"],
                    )
                steps.append(
                    make_step(
                        len(steps) + 1,
                        "climb_on_navaid_radial_to_fix",
                        [cell, cells[next_fix_idx]],
                        "A climb altitude cell also contains navaid/radial text and is followed by a terminal fix cell.",
                        field_hints,
                    )
                )
                consumed.update({idx, next_fix_idx})
            elif next_fix and next_fix in direct_fixes and "DIRECT" in upper_text.upper():
                field_hints = {
                    "Q_terminator": make_answer_hint(["DF", "CA"], "direct fix text plus climb cell", "low"),
                    "Q1_fix_ident": make_answer_hint(next_fix, cells[next_fix_idx]["cell_id"]),
                    "Q4_course_or_radial": make_answer_hint({"type": "direct"}, upper_text),
                }
                if altitude is not None:
                    field_hints["Q2_altitude_constraint"] = make_answer_hint(
                        {"desc": "AT_OR_ABOVE", "altitude_ft": altitude, "altitude_2_ft": None},
                        cell["cell_id"],
                    )
                steps.append(
                    make_step(
                        len(steps) + 1,
                        "climb_direct_to_fix",
                        [cell, cells[next_fix_idx]],
                        "The lower detail cells show a climb altitude followed by a named fix; upper text says direct to that fix.",
                        field_hints,
                    )
                )
                consumed.update({idx, next_fix_idx})
            else:
                field_hints = {"Q_terminator": make_answer_hint(["CA", "VA"], "climb cell", "low")}
                if altitude is not None:
                    field_hints["Q2_altitude_constraint"] = make_answer_hint(
                        {"desc": "AT_OR_ABOVE", "altitude_ft": altitude, "altitude_2_ft": None},
                        cell["cell_id"],
                    )
                steps.append(
                    make_step(
                        len(steps) + 1,
                        "initial_climb_to_altitude",
                        [cell],
                        "A climb arrow and altitude appear in the same lower missed-approach cell.",
                        field_hints,
                    )
                )
                consumed.add(idx)

        elif semantic == "turn_or_arc_altitude_cell":
            next_radial_idx = nearest_right_cell(cells, idx, {"navaid_radial_cell"})
            next_fix_idx = nearest_right_cell(cells, idx, {"fix_or_navaid_symbol_cell", "fix_text_cell"})
            chosen_cells = [cell]
            field_hints = {
                "Q_terminator": make_answer_hint(["DF", "CF", "FA", "TF"], "turn/arc cell", "low"),
            }
            if altitude is not None:
                field_hints["Q2_altitude_constraint"] = make_answer_hint(
                    {"desc": "AT_OR_ABOVE", "altitude_ft": altitude, "altitude_2_ft": None},
                    cell["cell_id"],
                )
            local_turn = turn_direction_from_cell(cell)
            if local_turn or global_turn:
                field_hints["Q3_turn"] = make_answer_hint(local_turn or global_turn, cell["cell_id"] if local_turn else upper_text, "medium")

            if next_radial_idx is not None and (next_fix_idx is None or next_radial_idx < next_fix_idx):
                radial = navaid_radial_from_cell(cells[next_radial_idx])
                chosen_cells.append(cells[next_radial_idx])
                consumed.add(next_radial_idx)
                if radial:
                    field_hints["Q4_course_or_radial"] = make_answer_hint(
                        {
                            "type": "navaid_radial",
                            "navaid": radial.get("navaid"),
                            "radial_deg": radial.get("radial_deg"),
                            "direction": radial.get("direction"),
                        },
                        cells[next_radial_idx]["cell_id"],
                    )
                    if radial.get("navaid"):
                        field_hints["Q1_fix_ident"] = make_answer_hint(radial.get("navaid"), cells[next_radial_idx]["cell_id"], "low")
                hint = "climbing_turn_to_navaid_radial"
                reason = "A turn/arc altitude cell is immediately followed by a navaid/radial cell."
            elif next_fix_idx is not None:
                chosen_cells.append(cells[next_fix_idx])
                consumed.add(next_fix_idx)
                next_fix = fix_from_cell(cells[next_fix_idx])
                if next_fix:
                    field_hints["Q1_fix_ident"] = make_answer_hint(next_fix, cells[next_fix_idx]["cell_id"])
                    if next_fix in direct_fixes or "DIRECT" in upper_text.upper():
                        field_hints["Q4_course_or_radial"] = make_answer_hint({"type": "direct"}, upper_text)
                hint = "climbing_turn_direct_or_to_fix"
                reason = "A turn/arc altitude cell is immediately followed by a named fix/symbol cell."
            else:
                hint = "climbing_turn_or_arc_to_altitude"
                reason = "A turn/arc symbol and altitude appear in the same lower missed-approach cell."

            steps.append(make_step(len(steps) + 1, hint, chosen_cells, reason, field_hints))
            consumed.add(idx)

        elif semantic == "navaid_radial_cell":
            radial = navaid_radial_from_cell(cell)
            next_fix_idx = nearest_right_cell(cells, idx, {"fix_or_navaid_symbol_cell", "fix_text_cell"})
            chosen_cells = [cell]
            field_hints = {
                "Q_terminator": make_answer_hint(["CF", "FA", "TF"], "navaid/radial cell", "low"),
            }
            if radial:
                field_hints["Q4_course_or_radial"] = make_answer_hint(
                    {
                        "type": "navaid_radial",
                        "navaid": radial.get("navaid"),
                        "radial_deg": radial.get("radial_deg"),
                        "direction": radial.get("direction"),
                    },
                    cell["cell_id"],
                )
            if next_fix_idx is not None:
                chosen_cells.append(cells[next_fix_idx])
                consumed.add(next_fix_idx)
                next_fix = fix_from_cell(cells[next_fix_idx])
                if next_fix:
                    field_hints["Q1_fix_ident"] = make_answer_hint(next_fix, cells[next_fix_idx]["cell_id"])
            steps.append(
                make_step(
                    len(steps) + 1,
                    "course_or_radial_to_fix",
                    chosen_cells,
                    "A navaid/radial cell defines the course/radial, optionally terminating at the next visible fix cell.",
                    field_hints,
                )
            )
            consumed.add(idx)

        elif semantic == "track_or_course_cell":
            next_fix_idx = nearest_right_cell(cells, idx, {"fix_or_navaid_symbol_cell", "fix_text_cell"})
            chosen_cells = [cell]
            field_hints = {
                "Q_terminator": make_answer_hint(["TF", "CF"], "track/course cell", "low"),
            }
            course = heading_from_cell(cell)
            if course is not None:
                field_hints["Q4_course_or_radial"] = make_answer_hint({"type": "course_deg", "course_deg": course}, cell["cell_id"])
            if next_fix_idx is not None:
                chosen_cells.append(cells[next_fix_idx])
                consumed.add(next_fix_idx)
                next_fix = fix_from_cell(cells[next_fix_idx])
                if next_fix:
                    field_hints["Q1_fix_ident"] = make_answer_hint(next_fix, cells[next_fix_idx]["cell_id"])
            steps.append(
                make_step(
                    len(steps) + 1,
                    "track_or_course_to_fix",
                    chosen_cells,
                    "A track/course cell is followed by a named fix/symbol cell.",
                    field_hints,
                )
            )
            consumed.add(idx)

        elif semantic in {"fix_or_navaid_symbol_cell", "fix_text_cell"}:
            fix = fix_from_cell(cell)
            field_hints = {
                "Q_terminator": make_answer_hint(["DF", "HM"], "visible fix cell", "low"),
            }
            if fix:
                field_hints["Q1_fix_ident"] = make_answer_hint(fix, cell["cell_id"])
            if fix and (fix in direct_fixes or "DIRECT" in upper_text.upper()):
                field_hints["Q4_course_or_radial"] = make_answer_hint({"type": "direct"}, upper_text)
            steps.append(
                make_step(
                    len(steps) + 1,
                    "direct_or_terminal_fix",
                    [cell],
                    "A named fix/symbol cell appears as a standalone lower missed-approach cell.",
                    field_hints,
                )
            )
            consumed.add(idx)

        idx += 1

    if has_hold(upper_text, regions):
        last_fix = None
        for step in reversed(steps):
            hint = step.get("field_hints", {}).get("Q1_fix_ident")
            if isinstance(hint, dict) and hint.get("observed_value"):
                last_fix = hint["observed_value"]
                break
        if not last_fix and fixes_in_text:
            last_fix = fixes_in_text[-1]
        hold_altitudes = re.findall(r"(?:hold|climb-in-hold)\s+to\s+(\d{3,5})", upper_text, re.IGNORECASE)
        altitude = int(hold_altitudes[-1]) if hold_altitudes else None
        if altitude is None:
            for step in reversed(steps):
                q2 = step.get("field_hints", {}).get("Q2_altitude_constraint", {})
                value = q2.get("observed_value") if isinstance(q2, dict) else None
                if isinstance(value, dict) and value.get("altitude_ft") is not None:
                    altitude = value["altitude_ft"]
                    break
        field_hints = {
            "Q_terminator": make_answer_hint(["HM", "HA", "HF"], "hold instruction or missed-approach-fix inset", "medium"),
            "Q5_hold_params": make_answer_hint(
                {
                    "inbound_course_deg": None,
                    "leg_time_min": None,
                    "leg_distance_nm": None,
                    "turn": None,
                },
                "hold instruction visible but exact hold parameters may require plan-view inset",
                "low",
            ),
        }
        if last_fix:
            field_hints["Q1_fix_ident"] = make_answer_hint(last_fix, "last visible fix before hold")
        if altitude is not None:
            field_hints["Q2_altitude_constraint"] = make_answer_hint(
                {"desc": "AT_OR_ABOVE", "altitude_ft": altitude, "altitude_2_ft": None},
                "hold/climb text or preceding altitude",
                "low",
            )
        steps.append(
            make_step(
                len(steps) + 1,
                "terminal_hold_at_fix",
                [],
                "The upper text or missed-approach-fix inset indicates a hold at the terminal missed-approach fix.",
                field_hints,
                "low",
            )
        )

    return steps


def extract_regions(prompt_input: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    evidence = prompt_input.get("input_evidence", {})
    regions = evidence.get("regions", [])
    elements = evidence.get("elements", [])
    upper_texts = [
        clean_text(str(region.get("ocr_text") or ""))
        for region in regions
        if region.get("source_region_type") == "MISSED_APPROACH_TEXT"
    ]
    upper_text = " ".join(text for text in upper_texts if text)
    # Remove OCR fragments before "MISSED APPROACH" when possible, but keep the
    # rest if the crop begins mid-word (e.g. "APPROACH:" / "OACH:").
    match = re.search(r"(MISSED\s+APPROACH\s*:.*)", upper_text, re.IGNORECASE)
    if match:
        upper_text = match.group(1)
    return regions, elements, upper_text


def build_prompt_input(path: Path) -> dict[str, Any]:
    prompt_input = read_json(path)
    regions, elements, upper_text = extract_regions(prompt_input)
    cells = make_visual_cells(elements)
    steps = make_candidate_steps(cells, upper_text, regions)
    return {
        "sample_id": prompt_input["sample_id"],
        "method": "B3V2",
        "status": "candidate_legs_prepared",
        "input_evidence": {
            "input_condition": (
                "B3-v2 region-aware OCR with an added chart-derived visual-cell and candidate-leg layer. "
                "No CIFP, chart metadata, or canonical answers are included."
            ),
            "upper_missed_approach_text": {
                "ocr_text_cleaned": upper_text,
                "note": "Visible OCR from the chart's upper MISSED APPROACH text crop.",
            },
            "visual_cells": cells,
            "candidate_legs": steps,
            "raw_regions_compact": [compact_item(region) for region in regions],
            "raw_elements_compact": [compact_item(element) for element in elements],
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build B3-v2 candidate-leg prompt inputs.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--sample-id", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    in_dir = root / "outputs/B3_region_ocr_llm/prompt_inputs"
    out_root = root / "outputs/B3_region_ocr_llm_v2"
    files = sorted(in_dir.glob("*.json"))
    if args.sample_id:
        files = [path for path in files if path.name.startswith(f"{args.sample_id}__")]
    if not files:
        raise SystemExit(f"No B3 prompt inputs found under {in_dir}")

    manifest = []
    for path in files:
        output = build_prompt_input(path)
        sid = output["sample_id"]
        candidate_path = out_root / "candidate_legs" / f"{sid}__candidate_legs.json"
        prompt_path = out_root / "prompt_inputs" / f"{sid}__prompt_input.json"
        write_json(candidate_path, output["input_evidence"]["candidate_legs"])
        write_json(prompt_path, output)
        manifest.append(
            {
                "sample_id": sid,
                "visual_cell_count": len(output["input_evidence"]["visual_cells"]),
                "candidate_leg_count": len(output["input_evidence"]["candidate_legs"]),
                "prompt_input": str(prompt_path),
                "candidate_legs": str(candidate_path),
            }
        )

    write_json(out_root / "candidate_leg_manifest.json", manifest)
    print(f"Wrote {len(manifest)} B3-v2 prompt inputs to {out_root / 'prompt_inputs'}")
    print(f"Wrote manifest to {out_root / 'candidate_leg_manifest.json'}")


if __name__ == "__main__":
    main()
