"""
Build B3V3 prompt inputs:

  original chart -> B3 OCR regions/elements -> OCR-only visual cells
  -> chart-derived semantic step candidates -> LLM -> PR #28 JSON

B3V3 is intentionally stricter than the earlier B3/B3V2 pilot inputs:
- It does not pass prelabel_text, visual_label, chart_id, airport, procedure, CIFP,
  canonical target values, or human-corrected answers to the prompt.
- Text values come from OCR only. Non-text symbols can contribute visual type
  evidence such as CLIMB_ARROW, PATH_SEGMENT, FIX_SYMBOL, or HOLD_ARC.
- Semantic candidates are produced from chart OCR and visual boxes only; they are
  method-side hypotheses, not ground truth.
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
DEFAULT_IN_DIR = ROOT / "outputs/B3_region_ocr_llm/prompt_inputs"
DEFAULT_OUT_DIR = ROOT / "outputs/B3_region_ocr_llm_v3"


TEXTUAL_REGION_TYPES = {
    "ALTITUDE_TEXT",
    "FIX_TEXT",
    "NAVAID_TEXT",
    "RADIAL_TEXT",
    "HEADING_TEXT",
    "DISTANCE_TEXT",
    "HOLD_TEXT",
    "MISSED_APPROACH_TEXT",
    "PLAN_VIEW",
    "MISSED_APPROACH_DETAIL_AREA",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = text.replace("°", "° ")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\bOACH\s*:", "APPROACH:", text, flags=re.IGNORECASE)
    if not re.search(r"\bMISSED\s+APPROACH\s*:", text, re.IGNORECASE):
        text = re.sub(r"\bAPPROACH\s*:", "MISSED APPROACH:", text, flags=re.IGNORECASE)
    text = re.sub(r"\bMISSED\s+MISSED\s+APPROACH", "MISSED APPROACH", text, flags=re.IGNORECASE)
    text = text.replace("climb-in-hold", "climb in hold")
    return text.strip()


def item_ocr_text(item: dict[str, Any]) -> str:
    text = clean_text(str(item.get("ocr_text") or ""))
    if text:
        return text
    tokens = item.get("ocr_tokens", [])
    if isinstance(tokens, list):
        token_text = " ".join(str(token.get("text") or "") for token in tokens if isinstance(token, dict))
        return clean_text(token_text)
    return ""


def compact_token(token: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": token.get("text", ""),
        "confidence": token.get("confidence"),
        "bbox": token.get("bbox"),
        "source_region_type": token.get("source_region_type", ""),
    }


def compact_item_ocr_only(item: dict[str, Any]) -> dict[str, Any]:
    source_region_type = str(item.get("source_region_type") or "")
    ocr_text = item_ocr_text(item)
    result = {
        "region_id": item.get("region_id", ""),
        "candidate_type": item.get("candidate_type", ""),
        "source_region_type": source_region_type,
        "source_region": item.get("source_region", ""),
        "bbox": item.get("bbox"),
        "ocr_text": ocr_text,
        "confidence": item.get("confidence"),
        "ocr_tokens": [
            compact_token(token)
            for token in item.get("ocr_tokens", [])
            if isinstance(token, dict)
        ],
    }
    if source_region_type not in TEXTUAL_REGION_TYPES and not ocr_text:
        result["visual_symbol_present"] = True
    return result


def bbox_edges(bbox: dict[str, Any]) -> tuple[float, float, float, float]:
    cx = float(bbox.get("x_center", 0.0))
    cy = float(bbox.get("y_center", 0.0))
    w = float(bbox.get("width", 0.0))
    h = float(bbox.get("height", 0.0))
    return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2


def union_bbox(items: list[dict[str, Any]]) -> dict[str, float] | None:
    boxes = [item.get("bbox") for item in items if isinstance(item.get("bbox"), dict)]
    if not boxes:
        return None
    edges = [bbox_edges(box) for box in boxes]
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


def item_x(item: dict[str, Any]) -> float:
    bbox = item.get("bbox") if isinstance(item.get("bbox"), dict) else {}
    return float(bbox.get("x_center", 0.0))


def item_y(item: dict[str, Any]) -> float:
    bbox = item.get("bbox") if isinstance(item.get("bbox"), dict) else {}
    return float(bbox.get("y_center", 0.0))


def classify_cell(items: list[dict[str, Any]], texts: list[str]) -> str:
    types = {str(item.get("source_region_type") or item.get("candidate_type") or "") for item in items}
    joined = " ".join(texts).upper()
    if "CLIMB_ARROW" in types and any(re.search(r"\b\d{3,5}\b", text) for text in texts):
        if any("HEADING_TEXT" == t for t in types):
            return "climb_altitude_heading_cell"
        return "climb_altitude_cell"
    if "PATH_SEGMENT" in types or "TURN_ARC" in types:
        if any(re.search(r"\b\d{3,5}\b", text) for text in texts):
            return "turn_or_arc_altitude_cell"
        return "turn_or_arc_symbol_cell"
    if "RADIAL_TEXT" in types or re.search(r"\bR[- ]?\d{3}\b", joined):
        return "navaid_radial_cell"
    if "HEADING_TEXT" in types or re.search(r"\b(?:HDG|TR|TRACK)\s*[0-3]\d{2}\b", joined):
        return "heading_or_track_cell"
    if "FIX_SYMBOL" in types:
        return "fix_symbol_cell"
    if "FIX_TEXT" in types:
        return "fix_text_cell"
    if "NAVAID_TEXT" in types:
        return "navaid_text_cell"
    if "HOLD_ARC" in types or "HOLD_TEXT" in types or "HOLD" in joined:
        return "hold_context_cell"
    if any(re.search(r"\b\d{3,5}\b", text) for text in texts):
        return "numeric_text_cell"
    return "visual_or_text_cell"


def make_visual_cells(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted((compact_item_ocr_only(item) for item in elements), key=lambda item: (item_x(item), item_y(item)))
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
        texts = [item["ocr_text"] for item in group if item.get("ocr_text")]
        cells.append(
            {
                "cell_id": f"cell_{idx:02d}",
                "bbox": union_bbox(group),
                "cell_semantic_hint": classify_cell(group, texts),
                "observed_types": sorted(
                    {str(item.get("source_region_type") or item.get("candidate_type") or "") for item in group}
                ),
                "ocr_texts": texts,
                "source_element_ids": [item.get("region_id") for item in group],
                "source_elements": group,
            }
        )
    return cells


def upper_missed_text(regions: list[dict[str, Any]]) -> str:
    texts = [
        item_ocr_text(region)
        for region in regions
        if region.get("source_region_type") == "MISSED_APPROACH_TEXT"
    ]
    text = clean_text(" ".join(text for text in texts if text))
    match = re.search(r"(MISSED\s+APPROACH\s*:.*)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


def evidence_refs_from_cells(cells: list[dict[str, Any]], pattern: str) -> list[str]:
    regex = re.compile(pattern, re.IGNORECASE)
    refs = []
    for cell in cells:
        haystack = " ".join(cell.get("ocr_texts", []))
        if regex.search(haystack):
            refs.append(cell["cell_id"])
    return refs


def evidence_refs_for_terms(cells: list[dict[str, Any]], terms: list[str]) -> list[str]:
    clean_terms = [term for term in terms if term]
    if not clean_terms:
        return []
    pattern = r"\b(" + "|".join(re.escape(term) for term in clean_terms) + r")\b"
    return evidence_refs_from_cells(cells, pattern)


def hint(value: Any, source: str, confidence: str, snippet: str = "", evidence_refs: list[str] | None = None) -> dict[str, Any]:
    return {
        "observed_value": value,
        "evidence_source": source,
        "source_snippet": snippet,
        "evidence_refs": evidence_refs or [],
        "confidence": confidence,
    }


def step(index: int, action_type: str, snippet: str, q_hints: dict[str, Any], evidence_refs: list[str] | None = None) -> dict[str, Any]:
    return {
        "semantic_step_id": f"semantic_step_{index:02d}",
        "visual_order": index,
        "action_type": action_type,
        "source": "chart_ocr_and_visual_boxes",
        "source_snippet": snippet,
        "evidence_refs": evidence_refs or [],
        "q_hints": q_hints,
        "llm_decision_needed": True,
    }


def answer_hint(
    status: str,
    value: Any,
    source: str,
    confidence: str,
    snippet: str = "",
    evidence_refs: list[str] | None = None,
    note: str = "",
) -> dict[str, Any]:
    result = hint(value, source, confidence, snippet, evidence_refs)
    result["status_hint"] = status
    if note:
        result["note"] = note
    return result


def candidate_leg(
    index: int,
    action_type: str,
    snippet: str,
    q_hints: dict[str, Any],
    evidence_refs: list[str] | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "candidate_ref": f"candidate_leg_{index:02d}",
        "visual_order": index,
        "action_type": action_type,
        "source": "chart_ocr_and_visual_boxes",
        "source_snippet": snippet,
        "evidence_refs": evidence_refs or [],
        "q_hints": q_hints,
        "notes": notes or [],
        "llm_decision_needed": True,
    }


def normalize_fix(raw: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", raw.upper())[:5]


def is_bad_fix(fix: str | None) -> bool:
    return not fix or fix in {
        "AND",
        "APCH",
        "CLIMB",
        "CLIMBING",
        "CONT",
        "CONTINUE",
        "DEL",
        "DME",
        "FIX",
        "GND",
        "HOLD",
        "INT",
        "MISSED",
        "RADAR",
        "THE",
        "THEN",
        "TO",
        "VOR",
        "VORTAC",
        "VORDM",
    }


def is_fix_like(value: str | None) -> bool:
    if not value:
        return False
    value = normalize_fix(value)
    return bool(
        value
        and not is_bad_fix(value)
        and 3 <= len(value) <= 5
        and re.search(r"[A-Z]", value)
        and not value.isdigit()
    )


def parse_heading(text: str) -> int | None:
    match = re.search(r"\b(?:heading|hdg)\s*([0-3]\d{2})\b", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def parse_track_course(text: str) -> int | None:
    match = re.search(r"\b(?:track|tr|ck)\s*([0-3]\d{2})\b", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def find_first_climb(text: str) -> re.Match[str] | None:
    """Find the first climb-to-altitude phrase, tolerating OCR-damaged turn words."""
    patterns = [
        r"\bclimb(?:ing)?\s+to\s+(\d{3,5})\b",
        r"\bclimbing\b.{0,35}?\bto\s+(\d{3,5})\b",
        r"\bclimb\b.{0,35}?\bto\s+(\d{3,5})\b",
    ]
    matches: list[re.Match[str]] = []
    for pattern in patterns:
        matches.extend(re.finditer(pattern, text, re.IGNORECASE))
    if not matches:
        return None
    return min(matches, key=lambda match: match.start())


def terminator_for_initial_climb(heading: int | None) -> str:
    return "VI" if heading is not None else "CA"


def terminator_note(value: str, reason: str) -> str:
    return f"path_terminator_preferred={value}; {reason}"


def reciprocal_course(course: float | int) -> float:
    value = (float(course) + 180.0) % 360.0
    return round(value if value != 0 else 360.0, 1)


def course_pair_inbound(courses: list[int]) -> float | None:
    clean_courses = [course for course in courses if 1 <= course <= 360]
    for idx, first in enumerate(clean_courses):
        for second in clean_courses[idx + 1 :]:
            diff = abs(first - second)
            if abs(diff - 180) <= 3:
                inbound = min(first, second)
                return float(inbound)
    return None


def parse_turn_near(snippet: str, full_text: str) -> str | None:
    window = snippet
    idx = full_text.upper().find(snippet.upper())
    if idx >= 0:
        window = full_text[max(0, idx - 45) : min(len(full_text), idx + len(snippet) + 45)]
    if re.search(r"\bleft\s+(?:turn|rn)\b", window, re.IGNORECASE):
        return "LEFT"
    if re.search(r"\bright\s+(?:turn|rn)\b", window, re.IGNORECASE):
        return "RIGHT"
    return None


def cell_text(cell: dict[str, Any]) -> str:
    return " ".join(str(text) for text in cell.get("ocr_texts", [])).upper()


def combined_evidence_text(text: str, cells: list[dict[str, Any]], regions: list[dict[str, Any]]) -> str:
    parts = [text]
    parts.extend(" ".join(str(value) for value in cell.get("ocr_texts", [])) for cell in cells)
    parts.extend(str(region.get("ocr_text") or "") for region in regions)
    return clean_text(" ".join(part for part in parts if part))


def infer_hold_params(
    text: str,
    cells: list[dict[str, Any]],
    regions: list[dict[str, Any]],
    *,
    last_fix: str | None,
    last_radial: dict[str, Any] | None,
    last_track_course: int | None,
) -> tuple[dict[str, Any], str]:
    evidence = combined_evidence_text(text, cells, regions)
    params: dict[str, Any] = {
        "inbound_course_deg": None,
        "leg_time_min": None,
        "leg_distance_nm": None,
        "turn": None,
    }
    notes: list[str] = []

    distance_value: float | None = None
    for missed_match in re.finditer(r"\bMISSED\s+APCH\s+FIX\b", evidence, re.IGNORECASE):
        window = evidence[missed_match.end() : missed_match.end() + 140]
        # Prefer a one-digit distance immediately after the inset title. This
        # catches OCR like "4qu.." before unrelated ".9 NM to runway" text.
        after_title = evidence[missed_match.end() : missed_match.end() + 35]
        fuzzy_match = re.search(r"\b([1-9])\s*(?:NM|N\b|qu|\.\.)", after_title, re.IGNORECASE)
        if fuzzy_match:
            distance_value = float(fuzzy_match.group(1))
        if distance_value is not None:
            break
        for number_match in re.finditer(r"(?<![.\d])\b([1-9](?:\.\d+)?)\s*NM\b", window, re.IGNORECASE):
            candidate = float(number_match.group(1))
            if candidate <= 10.0:
                distance_value = candidate
                break
        if distance_value is not None:
            break
    if distance_value is not None:
        params["leg_distance_nm"] = distance_value
        notes.append(f"hold_distance_nm_from_missed_fix_inset={distance_value}")

    if last_track_course is not None:
        params["inbound_course_deg"] = float(last_track_course)
        notes.append(f"hold_inbound_course_from_track={last_track_course}")
    elif last_radial:
        radial = int(last_radial["radial"])
        direction_source = str(last_radial.get("direction_source") or "")
        if direction_source == "inferred_to_fix":
            if re.search(r"/DME\s+R[- ]?\d{3}\s+to\b", text, re.IGNORECASE):
                params["inbound_course_deg"] = reciprocal_course(radial)
                notes.append(f"hold_inbound_course_from_reciprocal_radial={radial}")
            else:
                params["inbound_course_deg"] = float(radial)
                notes.append(f"hold_inbound_course_from_radial_to_fix={radial}")
        elif str(last_radial.get("direction")) == "inbound":
            explicit_course = parse_track_course(evidence)
            if explicit_course is not None:
                params["inbound_course_deg"] = float(explicit_course)
                notes.append(f"hold_inbound_course_from_visible_track={explicit_course}")
            else:
                degree_courses = [
                    int(value)
                    for value in re.findall(r"(?<![\d.])\b([0-3]?\d{2})\s*(?:°|掳)", evidence)
                    if 1 <= int(value) <= 360
                ]
                paired_course = course_pair_inbound(degree_courses)
                if paired_course is not None:
                    params["inbound_course_deg"] = paired_course
                    notes.append(f"hold_inbound_course_from_degree_marked_pair={paired_course}")

    if params["inbound_course_deg"] is None and last_fix:
        fix_pattern = re.escape(last_fix)
        around_fix = re.search(rf".{{0,80}}\b{fix_pattern}\b.{{0,80}}", evidence, re.IGNORECASE)
        if around_fix:
            course_matches = [int(value) for value in re.findall(r"\b([0-3]\d{2})\b", around_fix.group(0))]
            if course_matches:
                params["inbound_course_deg"] = float(course_matches[-1])
                notes.append(f"hold_inbound_course_from_fix_context={course_matches[-1]}")

    turn = "LEFT" if re.search(r"\bleft\s+(?:turn|rn)\b", text, re.IGNORECASE) and re.search(r"\binbound\b", text, re.IGNORECASE) else "RIGHT"
    params["turn"] = turn
    notes.append(f"hold_turn_defaulted={turn}")

    if params["leg_distance_nm"] is None:
        params["leg_time_min"] = 1.0
        notes.append("hold_leg_time_defaulted_1_min_when_distance_not_visible")

    return params, "; ".join(notes)


def nearest_navaid_for_radial(radial: int, cells: list[dict[str, Any]]) -> str | None:
    pattern = re.compile(rf"\bR[- ]?{radial:03d}\b", re.IGNORECASE)
    candidates: list[str] = []
    for cell in cells:
        text = cell_text(cell)
        if not pattern.search(text):
            continue
        for token in re.findall(r"\b[A-Z0-9]{2,5}\b", text):
            fix = normalize_fix(token)
            if is_fix_like(fix) and not re.search(r"\d", fix):
                candidates.append(fix)
    return candidates[0] if candidates else None


def find_direct_actions(text: str, cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions = []
    for match in re.finditer(r"\bdirect\b", text, re.IGNORECASE):
        tail = text[match.end() : match.end() + 90]
        chosen = None
        chosen_span = None
        for token_match in re.finditer(r"\b[A-Z0-9]{1,8}\b", tail, re.IGNORECASE):
            token = normalize_fix(token_match.group(0))
            if is_fix_like(token):
                chosen = token
                chosen_span = (match.start(), match.end() + token_match.end())
                break
        if not chosen or not chosen_span:
            continue
        snippet = text[chosen_span[0] : chosen_span[1]]
        actions.append(
            {
                "type": "direct",
                "fix": chosen,
                "start": chosen_span[0],
                "end": chosen_span[1],
                "snippet": snippet,
                "refs": evidence_refs_for_terms(cells, [chosen]),
            }
        )
    return actions


def find_radial_actions(text: str, cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions = []
    radial_pattern = re.compile(
        r"\b(?:(?P<navaid>[A-Z]{2,5})\s*(?:VOR/DME|VORTAC|VOR|DME)?\s*)?"
        r"(?:[A-Z]\s+)?R[- ]?(?P<radial>\d{3})"
        r"(?:\s+(?P<direction>outbound|inbound|outbnd|inbnd))?"
        r"(?:\s+(?:then\s+)?to\s+(?P<fix>[A-Z][A-Z0-9]{2,5}))?",
        re.IGNORECASE,
    )
    for match in radial_pattern.finditer(text):
        radial = int(match.group("radial"))
        raw_navaid = normalize_fix(match.group("navaid") or "")
        navaid = raw_navaid if is_fix_like(raw_navaid) else None
        if navaid is None:
            navaid = nearest_navaid_for_radial(radial, cells)
        raw_direction = (match.group("direction") or "").lower()
        if raw_direction in {"outbnd", "outbound"}:
            direction = "outbound"
            direction_source = "explicit"
        elif raw_direction in {"inbnd", "inbound"}:
            direction = "inbound"
            direction_source = "explicit"
        elif match.group("fix"):
            direction = "inbound"
            direction_source = "inferred_to_fix"
        else:
            direction = "outbound"
            direction_source = "default_no_fix"
        fix = normalize_fix(match.group("fix") or "")
        if not is_fix_like(fix):
            fix = None
        terms = [navaid or "", f"R-{radial:03d}", fix or ""]
        actions.append(
            {
                "type": "radial",
                "navaid": navaid,
                "radial": radial,
                "direction": direction,
                "direction_source": direction_source,
                "fix": fix,
                "start": match.start(),
                "end": match.end(),
                "snippet": match.group(0),
                "refs": evidence_refs_for_terms(cells, terms),
            }
        )
    return actions


def find_track_actions(text: str, cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions = []
    pattern = re.compile(
        r"\b(?:on\s+)?(?:track|tr|ck)\s+([0-3]\d{2})\S*\s+to\s+([A-Z][A-Z0-9]{2,5})\b",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        course = int(match.group(1))
        fix = normalize_fix(match.group(2))
        if not is_fix_like(fix):
            continue
        actions.append(
            {
                "type": "track",
                "course": course,
                "fix": fix,
                "start": match.start(),
                "end": match.end(),
                "snippet": match.group(0),
                "refs": evidence_refs_for_terms(cells, [f"{course:03d}", fix]),
            }
        )
    if actions:
        return actions

    # Recover OCR-split profile cells such as ["to", "284°"] followed by ["TELLE"].
    for idx, cell in enumerate(cells):
        text_cell = cell_text(cell)
        course_match = re.search(r"\b([0-3]\d{2})\b", text_cell)
        if not course_match:
            continue
        if not (
            re.search(r"\b(?:TR|TRACK|CK|TO)\b", text_cell)
            or "TRACK_OR_RADIAL_TEXT" in cell.get("observed_types", [])
        ):
            continue
        course = int(course_match.group(1))
        fix = None
        fix_ref = None
        for next_cell in cells[idx + 1 : idx + 4]:
            next_text = cell_text(next_cell)
            for token in re.findall(r"\b[A-Z][A-Z0-9]{2,5}\b", next_text):
                candidate = normalize_fix(token)
                if is_fix_like(candidate):
                    fix = candidate
                    fix_ref = next_cell.get("cell_id")
                    break
            if fix:
                break
        if not fix:
            continue
        actions.append(
            {
                "type": "track",
                "course": course,
                "fix": fix,
                "start": 10_000 + idx,
                "end": 10_000 + idx + 1,
                "snippet": f"visual cells: tr {course:03d} to {fix}",
                "refs": [ref for ref in [cell.get("cell_id"), fix_ref] if ref],
            }
        )
    return actions


def nearest_climb_alt_before(text: str, position: int) -> tuple[int | None, str]:
    window = text[max(0, position - 90) : position]
    candidates: list[tuple[int, int, str]] = []
    for match in re.finditer(
        r"\bclimb(?:ing)?(?:\s+(?:left|right))?(?:\s+\w{1,8}){0,4}?\s+to\s+(\d{3,5})\b",
        window,
        re.IGNORECASE,
    ):
        candidates.append((match.start(), int(match.group(1)), match.group(0)))
    for match in re.finditer(
        r"\bclimb(?:ing)?(?:\s+(?:left|right))?(?:\s+\w{1,8}){0,4}?\s+to\s+(\d)\s+(\d{3,4})\b",
        window,
        re.IGNORECASE,
    ):
        candidates.append((match.start(), int(match.group(1) + match.group(2)), match.group(0)))
    for match in re.finditer(r"\bclimbing\s+(\d)\s+(\d{3,4})\b", window, re.IGNORECASE):
        candidates.append((match.start(), int(match.group(1) + match.group(2)), match.group(0)))
    if candidates:
        _, altitude, snippet = sorted(candidates, key=lambda item: item[0])[-1]
        return altitude, snippet
    return None, ""


def nearest_turn_before(text: str, position: int) -> str | None:
    window = text[max(0, position - 90) : position]
    matches = list(re.finditer(r"\b(left|right)\s+turn\b", window, re.IGNORECASE))
    if not matches:
        return None
    return matches[-1].group(1).upper()


def has_action_after(actions: list[dict[str, Any]], position: int, action_type: str | None = None) -> bool:
    return any(action["start"] > position and (action_type is None or action["type"] == action_type) for action in actions)


def should_put_initial_altitude_on_first_leg(text: str, first_climb: re.Match[str], heading: int | None, actions: list[dict[str, Any]]) -> bool:
    after = text[first_climb.end() : first_climb.end() + 20]
    if re.search(r"\bthen\b", after, re.IGNORECASE):
        return True
    if heading is not None:
        return False
    if has_action_after(actions, first_climb.end(), "direct"):
        return False
    return True


def add_q_hint(q_hints: dict[str, Any], field: str, status: str, value: Any, source: str, confidence: str, snippet: str, refs: list[str], note: str = "") -> None:
    q_hints[field] = answer_hint(status, value, source, confidence, snippet, refs, note)


def parse_candidate_legs(text: str, cells: list[dict[str, Any]], regions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    text = clean_text(text)
    legs: list[dict[str, Any]] = []
    heading = parse_heading(text)
    first_climb = find_first_climb(text)
    direct_actions = find_direct_actions(text, cells)
    radial_actions = find_radial_actions(text, cells)
    track_actions = find_track_actions(text, cells)
    ordered_actions = sorted(direct_actions + radial_actions + track_actions, key=lambda item: (item["start"], item["end"]))
    first_alt = int(first_climb.group(1)) if first_climb else None
    carry_altitude: int | None = None

    def add_leg(action_type: str, snippet: str, q_hints: dict[str, Any], refs: list[str] | None = None, notes: list[str] | None = None) -> None:
        legs.append(candidate_leg(len(legs) + 1, action_type, snippet, q_hints, refs, notes))

    if first_climb:
        alt = int(first_climb.group(1))
        refs = evidence_refs_from_cells(cells, rf"\b{alt}\b")
        q_hints: dict[str, Any] = {
            "Q_terminator": answer_hint(
                "present",
                terminator_for_initial_climb(heading),
                "initial climb phrase",
                "medium",
                first_climb.group(0),
                refs,
                terminator_note(terminator_for_initial_climb(heading), "heading-present initial climb uses VI; altitude-only climb uses CA"),
            ),
            "Q1_fix_ident": answer_hint("not_applicable", None, "initial climb phrase", "medium", first_climb.group(0), refs),
            "Q3_turn": answer_hint("not_applicable", None, "initial climb phrase", "medium", first_climb.group(0), refs),
            "Q5_hold_params": answer_hint("not_applicable", None, "initial climb phrase", "medium", first_climb.group(0), refs),
        }
        notes = []
        if should_put_initial_altitude_on_first_leg(text, first_climb, heading, ordered_actions):
            add_q_hint(
                q_hints,
                "Q2_altitude_constraint",
                "present",
                {"desc": "AT_OR_ABOVE", "altitude_ft": alt, "altitude_2_ft": None},
                "initial climb phrase",
                "medium",
                first_climb.group(0),
                refs,
            )
        else:
            carry_altitude = alt
            add_q_hint(
                q_hints,
                "Q2_altitude_constraint",
                "not_applicable",
                None,
                "initial climb altitude carried to following fix/hold leg",
                "low",
                first_climb.group(0),
                refs,
                "The visible altitude is preserved as carry_forward_altitude instead of forcing it onto this first leg.",
            )
            notes.append(f"carry_forward_altitude_ft={alt}")
        if heading is not None:
            add_q_hint(
                q_hints,
                "Q4_course_or_radial",
                "present",
                {"type": "course_deg", "course_deg": heading},
                "heading phrase",
                "medium",
                text,
                evidence_refs_from_cells(cells, rf"\b{heading:03d}\b"),
            )
        else:
            add_q_hint(q_hints, "Q4_course_or_radial", "unknown", None, "initial climb phrase", "low", first_climb.group(0), refs)
        add_leg("initial_climb_or_heading", first_climb.group(0), q_hints, refs, notes)

    last_fix: str | None = None
    last_altitude = carry_altitude or first_alt
    last_radial: dict[str, Any] | None = None
    last_track_course: int | None = None
    seen_action_keys: set[tuple[str, int, int]] = set()
    for action in ordered_actions:
        key = (action["type"], action["start"], action["end"])
        if key in seen_action_keys:
            continue
        seen_action_keys.add(key)
        refs = action.get("refs", [])
        snippet = action["snippet"]
        q_hints: dict[str, Any] = {}
        alt, alt_snippet = nearest_climb_alt_before(text, action["start"])
        if alt is not None:
            last_altitude = alt

        if action["type"] == "direct":
            fix = action["fix"]
            last_fix = fix
            add_q_hint(q_hints, "Q_terminator", "present", "DF", "direct-to-fix phrase", "high", snippet, refs, terminator_note("DF", "direct fix phrase"))
            add_q_hint(q_hints, "Q1_fix_ident", "present", fix, "direct-to-fix phrase", "high", snippet, refs)
            if last_altitude is not None and not has_action_after(ordered_actions, action["end"]):
                add_q_hint(
                    q_hints,
                    "Q2_altitude_constraint",
                    "present",
                    {"desc": "AT_OR_ABOVE", "altitude_ft": last_altitude, "altitude_2_ft": None},
                    "carried climb altitude for direct-to-fix leg",
                    "medium",
                    alt_snippet or snippet,
                    evidence_refs_from_cells(cells, rf"\b{last_altitude}\b"),
                )
            else:
                add_q_hint(q_hints, "Q2_altitude_constraint", "not_applicable", None, "direct-to-fix phrase", "medium", snippet, refs)
            turn = parse_turn_near(snippet, text)
            add_q_hint(q_hints, "Q3_turn", "present" if turn else "unknown", turn, "nearby turn phrase", "medium" if turn else "low", snippet, refs)
            add_q_hint(q_hints, "Q4_course_or_radial", "present", {"type": "direct"}, "direct-to-fix phrase", "high", snippet, refs)
            add_q_hint(q_hints, "Q5_hold_params", "not_applicable", None, "direct-to-fix phrase", "medium", snippet, refs)
            add_leg("direct_to_fix", snippet, q_hints, refs)
            continue

        if action["type"] == "track":
            fix = action["fix"]
            last_fix = fix
            last_track_course = int(action["course"])
            add_q_hint(q_hints, "Q_terminator", "present", "TF", "track-to-fix phrase", "high", snippet, refs, terminator_note("TF", "track/course to fix"))
            add_q_hint(q_hints, "Q1_fix_ident", "present", fix, "track-to-fix phrase", "high", snippet, refs)
            if last_altitude is not None:
                add_q_hint(
                    q_hints,
                    "Q2_altitude_constraint",
                    "present",
                    {"desc": "AT_OR_ABOVE", "altitude_ft": last_altitude, "altitude_2_ft": None},
                    "carried climb altitude for track-to-fix leg",
                    "medium",
                    alt_snippet or snippet,
                    evidence_refs_from_cells(cells, rf"\b{last_altitude}\b"),
                )
            else:
                add_q_hint(q_hints, "Q2_altitude_constraint", "unknown", None, "track-to-fix phrase", "low", snippet, refs)
            add_q_hint(q_hints, "Q3_turn", "not_applicable", None, "track-to-fix phrase", "medium", snippet, refs)
            add_q_hint(
                q_hints,
                "Q4_course_or_radial",
                "unknown",
                None,
                "track-to-fix phrase",
                "low",
                snippet,
                refs,
                "TF candidate carries track in path terminator context; PR #28 Q4 is left unknown unless a separate course/radial leg is visible.",
            )
            add_q_hint(q_hints, "Q5_hold_params", "not_applicable", None, "track-to-fix phrase", "medium", snippet, refs)
            add_leg("track_to_fix", snippet, q_hints, refs)
            continue

        if action["type"] == "radial":
            prior_fix = last_fix
            fix = action.get("fix")
            navaid = action.get("navaid")
            last_fix = fix or navaid or last_fix
            last_radial = action
            suppress_radial_q4 = False
            if fix:
                if navaid and prior_fix == navaid and action.get("direction_source") == "inferred_to_fix":
                    terminator = "TF"
                    action_type = "track_from_navaid_to_fix"
                    suppress_radial_q4 = True
                else:
                    terminator = "CF"
                    action_type = "radial_to_fix"
            else:
                terminator = "FA"
                action_type = "radial_outbound_or_course"
            add_q_hint(
                q_hints,
                "Q_terminator",
                "present",
                terminator,
                "navaid radial phrase",
                "medium",
                snippet,
                refs,
                terminator_note(terminator, "radial to named fix uses CF; radial without named fix uses FA"),
            )
            add_q_hint(q_hints, "Q1_fix_ident", "present" if (fix or navaid) else "unknown", fix or navaid, "radial phrase terminal/reference fix", "medium", snippet, refs)
            if last_altitude is not None:
                add_q_hint(
                    q_hints,
                    "Q2_altitude_constraint",
                    "present",
                    {"desc": "AT_OR_ABOVE", "altitude_ft": last_altitude, "altitude_2_ft": None},
                    "carried climb altitude for radial leg",
                    "medium",
                    alt_snippet or snippet,
                    evidence_refs_from_cells(cells, rf"\b{last_altitude}\b"),
                )
            else:
                add_q_hint(q_hints, "Q2_altitude_constraint", "unknown", None, "radial phrase", "low", snippet, refs)
            turn = nearest_turn_before(text, action["start"])
            turn_status = "present" if turn and action.get("direction") == "inbound" else "unknown"
            if suppress_radial_q4 and not turn:
                turn_status = "not_applicable"
            add_q_hint(q_hints, "Q3_turn", turn_status, turn if turn_status == "present" else None, "nearby turn phrase", "medium" if turn else "low", snippet, refs)
            radial_value = {
                "type": "navaid_radial",
                "navaid": navaid or "unknown",
                "radial_deg": action["radial"],
                "direction": action["direction"],
            }
            if suppress_radial_q4:
                add_q_hint(
                    q_hints,
                    "Q4_course_or_radial",
                    "unknown",
                    None,
                    "navaid radial phrase converted to TF after prior direct navaid",
                    "low",
                    snippet,
                    refs,
                    "Radial text is treated as supporting display evidence; canonical Q4 is left unknown for this TF-style leg.",
                )
            else:
                add_q_hint(
                    q_hints,
                    "Q4_course_or_radial",
                    "present",
                    radial_value,
                    f"navaid radial phrase; direction_source={action['direction_source']}",
                    "high" if action["direction_source"] == "explicit" else "medium",
                    snippet,
                    refs,
                )
            add_q_hint(q_hints, "Q5_hold_params", "not_applicable", None, "radial phrase", "medium", snippet, refs)
            add_leg(action_type, snippet, q_hints, refs, [f"radial_direction_source={action['direction_source']}"])

    has_hold = bool(re.search(r"\bhold\b", text, re.IGNORECASE))
    likely_terminal_hold = bool(last_fix and not has_hold and re.search(r"\bDME\b", text, re.IGNORECASE))
    if has_hold or likely_terminal_hold:
        hold_alt_match = re.search(r"\b(?:continue\s+)?(?:climb|limb)\s+in\s+hold(?:\s+\w+){0,3}\s+to\s+(\d{3,5})\b", text, re.IGNORECASE)
        hold_alt = int(hold_alt_match.group(1)) if hold_alt_match else last_altitude
        refs = evidence_refs_for_terms(cells, [last_fix or "", str(hold_alt or "")])
        q_hints = {
            "Q_terminator": answer_hint(
                "present",
                "HM",
                "hold phrase or terminal hold candidate",
                "medium" if has_hold else "low",
                text,
                refs,
                terminator_note("HM", "terminal hold at missed-approach fix"),
            ),
            "Q1_fix_ident": answer_hint("present" if last_fix else "unknown", last_fix, "last visible fix before hold", "medium", text, refs),
            "Q3_turn": answer_hint("not_applicable", None, "hold leg turn belongs in Q5 when visible", "medium", text, refs),
            "Q4_course_or_radial": answer_hint("not_applicable", None, "hold leg", "medium", text, refs),
        }
        if hold_alt is not None:
            add_q_hint(
                q_hints,
                "Q2_altitude_constraint",
                "present",
                {"desc": "AT_OR_ABOVE", "altitude_ft": hold_alt, "altitude_2_ft": None},
                "hold/carry-forward altitude",
                "medium",
                hold_alt_match.group(0) if hold_alt_match else text,
                evidence_refs_from_cells(cells, rf"\b{hold_alt}\b"),
            )
        else:
            add_q_hint(q_hints, "Q2_altitude_constraint", "unknown", None, "hold phrase", "low", text, refs)
        hold_params, hold_note = infer_hold_params(
            text,
            cells,
            regions,
            last_fix=last_fix,
            last_radial=last_radial,
            last_track_course=last_track_course,
        )
        add_q_hint(
            q_hints,
            "Q5_hold_params",
            "present",
            hold_params,
            "hold phrase plus OCR-only hold context inference",
            "medium",
            text,
            refs,
            hold_note,
        )
        add_leg(
            "hold_at_fix",
            "and hold" if has_hold else "terminal fix/DME likely hold; OCR may be truncated",
            q_hints,
            refs,
            ["hold_created_from_visible_hold_text" if has_hold else "low_confidence_terminal_hold_due_truncated_ocr"],
        )

    if not legs and text:
        add_leg(
            "unparsed_missed_approach_text",
            text,
            {"Q_terminator": answer_hint("unknown", "unknown", "unparsed chart OCR", "low", text, [])},
            [],
            ["fallback_unparsed"],
        )
    return legs


def parse_semantic_steps(text: str, cells: list[dict[str, Any]], regions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    text = clean_text(text)
    steps: list[dict[str, Any]] = []
    used_spans: set[tuple[int, int, str]] = set()

    def add(action_type: str, snippet: str, q_hints: dict[str, Any], refs: list[str] | None = None) -> None:
        key = (len(steps) + 1, len(snippet), action_type)
        if key in used_spans:
            return
        used_spans.add(key)
        steps.append(step(len(steps) + 1, action_type, snippet, q_hints, refs))

    heading = parse_heading(text)

    # Initial climb to altitude, optionally with heading/course evidence.
    first_climb = re.search(r"\bclimb(?:ing)?\s+to\s+(\d{3,5})\b", text, re.IGNORECASE)
    if first_climb:
        alt = int(first_climb.group(1))
        snippet = first_climb.group(0)
        refs = evidence_refs_from_cells(cells, rf"\b{alt}\b")
        q_hints = {
            "Q_terminator": hint(["CA", "VA", "VI"], "initial climb phrase", "low", snippet, refs),
            "Q2_altitude_constraint": hint(
                {"desc": "AT_OR_ABOVE", "altitude_ft": alt, "altitude_2_ft": None},
                "initial climb phrase",
                "medium",
                snippet,
                refs,
            ),
        }
        if heading is not None:
            q_hints["Q4_course_or_radial"] = hint(
                {"type": "course_deg", "course_deg": heading},
                "heading phrase",
                "medium",
                text,
                evidence_refs_from_cells(cells, rf"\b{heading:03d}\b"),
            )
        add("initial_climb_to_altitude", snippet, q_hints, refs)

    # Later plain "then climbing to 3200" phrases without an explicit turn.
    for match in re.finditer(r"\bthen\s+climbing\s+to\s+(\d{3,5})\b", text, re.IGNORECASE):
        alt = int(match.group(1))
        if first_climb and alt == int(first_climb.group(1)):
            continue
        snippet = match.group(0)
        refs = evidence_refs_from_cells(cells, rf"\b{alt}\b")
        add(
            "continued_climb_to_altitude",
            snippet,
            {
                "Q_terminator": hint(["CA", "VA"], "continued climb phrase", "low", snippet, refs),
                "Q2_altitude_constraint": hint(
                    {"desc": "AT_OR_ABOVE", "altitude_ft": alt, "altitude_2_ft": None},
                    "continued climb phrase",
                    "medium",
                    snippet,
                    refs,
                ),
            },
            refs,
        )

    # Climbing turns to altitude.
    for match in re.finditer(r"\bclimbing\s+(left|right)\s+turn\s+to\s+(\d{3,5})\b", text, re.IGNORECASE):
        turn = match.group(1).upper()
        alt = int(match.group(2))
        snippet = match.group(0)
        refs = evidence_refs_from_cells(cells, rf"\b{alt}\b")
        add(
            "climbing_turn_to_altitude",
            snippet,
            {
                "Q_terminator": hint(["CA", "VA", "DF", "CF"], "climbing turn phrase", "low", snippet, refs),
                "Q2_altitude_constraint": hint(
                    {"desc": "AT_OR_ABOVE", "altitude_ft": alt, "altitude_2_ft": None},
                    "climbing turn phrase",
                    "medium",
                    snippet,
                    refs,
                ),
                "Q3_turn": hint(turn, "climbing turn phrase", "high", snippet, refs),
            },
            refs,
        )

    # Direct-to-fix actions.
    direct_fixes: list[str] = []
    ordered_fixes: list[str] = []
    for match in re.finditer(r"\bdirect\s+([A-Z][A-Z0-9]{2,5})\b", text, re.IGNORECASE):
        fix = normalize_fix(match.group(1))
        if is_bad_fix(fix):
            continue
        direct_fixes.append(fix)
        ordered_fixes.append(fix)
        snippet = match.group(0)
        refs = evidence_refs_for_terms(cells, [fix])
        q_hints = {
            "Q_terminator": hint(["DF", "TF"], "direct-to-fix phrase", "medium", snippet, refs),
            "Q1_fix_ident": hint(fix, "direct-to-fix phrase", "high", snippet, refs),
            "Q4_course_or_radial": hint({"type": "direct"}, "direct-to-fix phrase", "high", snippet, refs),
        }
        turn = parse_turn_near(snippet, text)
        if turn:
            q_hints["Q3_turn"] = hint(turn, "nearby turn phrase", "medium", snippet, refs)
        add("direct_to_fix", snippet, q_hints, refs)

    # Track/course to fix actions.
    for match in re.finditer(r"\b(?:on\s+)?(?:track|tr|ck)\s+([0-3]\d{2})\s*(?:°\s*)?to\s+([A-Z][A-Z0-9]{2,5})\b", text, re.IGNORECASE):
        course = int(match.group(1))
        fix = normalize_fix(match.group(2))
        if is_bad_fix(fix):
            continue
        ordered_fixes.append(fix)
        snippet = match.group(0)
        refs = evidence_refs_for_terms(cells, [f"{course:03d}", fix])
        add(
            "track_to_fix",
            snippet,
            {
                "Q_terminator": hint(["TF", "CF"], "track-to-fix phrase", "medium", snippet, refs),
                "Q1_fix_ident": hint(fix, "track-to-fix phrase", "high", snippet, refs),
                "Q4_course_or_radial": hint(
                    {"type": "course_deg", "course_deg": course},
                    "track-to-fix phrase",
                    "high",
                    snippet,
                    refs,
                ),
            },
            refs,
        )

    # Navaid radial actions, optionally terminating at a fix.
    radial_pattern = re.compile(
        r"\b(?:on\s+)?([A-Z]{2,5})\s*(?:VOR/DME|VORTAC)?\s*(?:[A-Z]\s+)?R[- ]?(\d{3})"
        r"(?:\s+(outbound|inbound))?"
        r"(?:\s+(?:then\s+)?to\s+([A-Z][A-Z0-9]{2,5}))?",
        re.IGNORECASE,
    )
    radial_fixes: list[str] = []
    for match in radial_pattern.finditer(text):
        navaid = normalize_fix(match.group(1))
        radial = int(match.group(2))
        direction = (match.group(3) or "outbound").lower()
        fix = normalize_fix(match.group(4)) if match.group(4) else None
        if is_bad_fix(fix):
            fix = None
        if fix:
            radial_fixes.append(fix)
            ordered_fixes.append(fix)
        snippet = match.group(0)
        refs = evidence_refs_for_terms(cells, [navaid, f"R-{radial:03d}", fix or ""])
        q_hints = {
            "Q_terminator": hint(["CR", "CF", "FA", "TF"], "navaid radial phrase", "low", snippet, refs),
            "Q4_course_or_radial": hint(
                {
                    "type": "navaid_radial",
                    "navaid": navaid,
                    "radial_deg": radial,
                    "direction": direction,
                },
                "navaid radial phrase",
                "high",
                snippet,
                refs,
            ),
        }
        if fix:
            q_hints["Q1_fix_ident"] = hint(fix, "radial-to-fix phrase", "medium", snippet, refs)
        turn = parse_turn_near(snippet, text)
        if turn:
            q_hints["Q3_turn"] = hint(turn, "nearby turn phrase", "medium", snippet, refs)
        add("radial_or_course_to_fix", snippet, q_hints, refs)

    last_fix = None
    if ordered_fixes:
        last_fix = ordered_fixes[-1]

    # Holding action. Keep hold parameters as unknown unless chart OCR visibly
    # exposes them; this avoids over-asserting values not present in evidence.
    if re.search(r"\bhold\b", text, re.IGNORECASE):
        snippet = "and hold"
        refs = evidence_refs_from_cells(cells, rf"\b{re.escape(last_fix or '')}\b") if last_fix else []
        q_hints = {
            "Q_terminator": hint(["HM", "HF", "HA"], "hold phrase", "low", text, refs),
            "Q5_hold_params": hint(
                {
                    "inbound_course_deg": None,
                    "leg_time_min": None,
                    "leg_distance_nm": None,
                    "turn": None,
                },
                "hold phrase; parameters not fully visible in OCR",
                "low",
                text,
                refs,
            ),
        }
        if last_fix:
            q_hints["Q1_fix_ident"] = hint(last_fix, "last visible fix before hold", "medium", text, refs)
        hold_alt_match = re.search(r"\bcontinue\s+climb\s+in\s+hold\s+to\s+(\d{3,5})\b", text, re.IGNORECASE)
        if hold_alt_match:
            alt = int(hold_alt_match.group(1))
            q_hints["Q2_altitude_constraint"] = hint(
                {"desc": "AT_OR_ABOVE", "altitude_ft": alt, "altitude_2_ft": None},
                "continue climb in hold phrase",
                "medium",
                hold_alt_match.group(0),
                evidence_refs_from_cells(cells, rf"\b{alt}\b"),
            )
        add("hold_at_fix", snippet, q_hints, refs)

    if not steps and text:
        add(
            "unparsed_missed_approach_text",
            text,
            {"Q_terminator": hint("unknown", "unparsed chart OCR", "low", text)},
            [],
        )
    return steps


def build_prompt_input(path: Path) -> dict[str, Any]:
    prompt_input = read_json(path)
    evidence = prompt_input.get("input_evidence", {})
    regions = evidence.get("regions", [])
    elements = evidence.get("elements", [])
    strict_regions = [compact_item_ocr_only(region) for region in regions]
    cells = make_visual_cells(elements)
    upper_text = upper_missed_text(regions)
    semantic_steps = parse_semantic_steps(upper_text, cells, strict_regions)
    candidate_legs = parse_candidate_legs(upper_text, cells, strict_regions)
    return {
        "sample_id": prompt_input["sample_id"],
        "method": "B3V3",
        "status": "semantic_candidates_prepared",
        "input_evidence": {
            "input_condition": (
                "Strict OCR-only B3 semantic layer. It uses OCR text, OCR bboxes, "
                "and non-text visual candidate types only; prelabel/manual text and CIFP targets are excluded."
            ),
            "upper_missed_approach_text": {
                "ocr_text_cleaned": upper_text,
                "source": "MISSED_APPROACH_TEXT OCR crop",
            },
            "visual_cells_ocr_only": cells,
            "semantic_steps": semantic_steps,
            "candidate_legs": candidate_legs,
            "raw_regions_ocr_only": strict_regions,
            "prompt_contract": {
                "no_true_chart_id": True,
                "no_airport_or_procedure_metadata": True,
                "no_cifp_or_canonical_target": True,
                "no_prelabel_text": True,
                "semantic_steps_are_chart_derived_hypotheses": True,
                "candidate_legs_are_chart_derived_hypotheses": True,
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build B3V3 OCR-only semantic candidate prompt inputs.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--in-dir", default=None)
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    root = Path(args.root)
    in_dir = Path(args.in_dir) if args.in_dir else root / "outputs/B3_region_ocr_llm/prompt_inputs"
    out_dir = Path(args.out_dir) if args.out_dir else root / "outputs/B3_region_ocr_llm_v3"
    prompt_dir = out_dir / "prompt_inputs"
    semantic_dir = out_dir / "semantic_steps"
    candidate_dir = out_dir / "candidate_legs"

    files = sorted(in_dir.glob("*.json"))
    if not files:
        raise SystemExit(f"No B3 OCR prompt inputs found under {in_dir}")

    manifest = []
    for path in files:
        output = build_prompt_input(path)
        sample_id = output["sample_id"]
        prompt_path = prompt_dir / f"{sample_id}__prompt_input.json"
        semantic_path = semantic_dir / f"{sample_id}__semantic_steps.json"
        candidate_path = candidate_dir / f"{sample_id}__candidate_legs.json"
        write_json(prompt_path, output)
        write_json(semantic_path, output["input_evidence"]["semantic_steps"])
        write_json(candidate_path, output["input_evidence"]["candidate_legs"])
        manifest.append(
            {
                "sample_id": sample_id,
                "prompt_input": str(prompt_path).replace("\\", "/"),
                "semantic_steps": str(semantic_path).replace("\\", "/"),
                "candidate_legs": str(candidate_path).replace("\\", "/"),
                "semantic_step_count": len(output["input_evidence"]["semantic_steps"]),
                "candidate_leg_count": len(output["input_evidence"]["candidate_legs"]),
                "visual_cell_count": len(output["input_evidence"]["visual_cells_ocr_only"]),
            }
        )

    write_json(out_dir / "semantic_candidate_manifest.json", manifest)
    print(f"Wrote {len(manifest)} B3V3 prompt inputs to {prompt_dir}")
    print(f"Wrote manifest to {out_dir / 'semantic_candidate_manifest.json'}")


if __name__ == "__main__":
    main()
