"""
Run B1/B3/B3V2/B3V3 LLM extraction after OCR preparation.

Inputs:
  B1: outputs/B1_ocr_llm/prompt_inputs/*.json
  B3: outputs/B3_region_ocr_llm/prompt_inputs/*.json
  B3V2: outputs/B3_region_ocr_llm_v2/prompt_inputs/*.json
  B3V3: outputs/B3_region_ocr_llm_v3/prompt_inputs/*.json

Outputs:
  outputs/{method}/llm_raw/*.txt
  outputs/{method}/llm_json/*.json
  outputs/{method}/method_outputs/*.json

The prompt intentionally uses only opaque sample_id and evidence. Real chart
metadata is filled only after the LLM response from sample_map_private.json.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anthropic
from openai import OpenAI

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.getenv("FAA_B1_B3_ROOT", REPO_ROOT)).expanduser().resolve()
STATUS = {"present", "not_applicable", "not_observable", "unknown"}
Q_FIELDS = [
    "Q_terminator",
    "Q1_fix_ident",
    "Q2_altitude_constraint",
    "Q3_turn",
    "Q4_course_or_radial",
    "Q5_hold_params",
]

SYSTEM_PROMPT = """You extract FAA approach-chart missed-approach procedure information from OCR text or region evidence.

Use only the provided evidence. Do not use airport name, chart id, procedure name, CIFP, or outside knowledge. If evidence is insufficient, use status "unknown" or "not_observable" rather than guessing.

Output JSON only. No markdown. No explanation.
"""

USER_INSTRUCTIONS = """Task: extract the missed approach into the PR #28 canonical leg-level JSON fragment.

Return exactly this shape:
{
  "sample_id": "<opaque sample id>",
  "missed_approach": {
    "leg_count": {"status": "present|unknown", "value": <integer|null>},
    "legs": [
      {
        "leg_index": 1,
        "answers": {
          "Q_terminator": {"status": "present|not_applicable|not_observable|unknown", "value": null},
          "Q1_fix_ident": {"status": "present|not_applicable|not_observable|unknown", "value": null},
          "Q2_altitude_constraint": {"status": "present|not_applicable|not_observable|unknown", "value": null},
          "Q3_turn": {"status": "present|not_applicable|not_observable|unknown", "value": null},
          "Q4_course_or_radial": {"status": "present|not_applicable|not_observable|unknown", "value": null},
          "Q5_hold_params": {"status": "present|not_applicable|not_observable|unknown", "value": null}
        }
      }
    ]
  }
}

Field value rules:
- Q_terminator.value, when present, must be one of: CA, CF, CI, CR, DF, FA, FM, HA, HF, HM, IF, RF, TF, VA, VD, VI, VM, VR, AF, CD, FC, FD, VC, PI, unknown.
- Q1_fix_ident.value is the fix/navaid/waypoint ident for the leg, e.g. MUDRE, ALS, EVVIS, ZEXEL. Use null for not_applicable/unknown/not_observable.
- Q2_altitude_constraint.value, when present, must be {"desc":"AT|AT_OR_ABOVE|AT_OR_BELOW|BETWEEN","altitude_ft":integer|null,"altitude_2_ft":integer|null}.
- Q3_turn.value, when present, must be "LEFT" or "RIGHT".
- Q4_course_or_radial.value, when present, must be one of:
  {"type":"course_deg","course_deg":number}
  {"type":"navaid_radial","navaid":"ABC","radial_deg":number,"direction":"outbound|inbound"}
  {"type":"direct"}
- Q5_hold_params.value, when present, must be {"inbound_course_deg":number|null,"leg_time_min":number|null,"leg_distance_nm":number|null,"turn":"LEFT|RIGHT|null"}.

Leg splitting guidance:
- Preserve the visible sequence of the missed approach.
- For B3V3, prefer candidate_legs over raw semantic_steps for leg count and leg order. candidate_legs are OCR-only method hypotheses that group cells into likely PR #28/ARINC-style legs.
- Do not create one output leg per semantic_step when candidate_legs already combine those steps into one leg.
- If candidate_legs contain status_hint/value hints, use them as primary evidence but still mark fields unknown/not_observable when the supporting OCR is insufficient.
- If a B3V3 candidate_leg gives a single scalar Q_terminator observed_value, treat it as the preferred path terminator unless another visible candidate field clearly conflicts.
- If a B3V3 candidate_leg provides Q5_hold_params with OCR-derived/defaulted hold values, copy those visible/inferred hold parameters into the hold leg instead of leaving the hold object empty.
- If a candidate_leg note says carry_forward_altitude_ft, that altitude should usually apply to following fix/radial/hold legs, not automatically to the initial heading leg.
- If a radial phrase is "R-xxx to FIX" and no explicit inbound/outbound text is visible, prefer inbound when the candidate says direction_source=inferred_to_fix; use unknown only if evidence conflicts.
- If candidate_legs include a low-confidence terminal hold because OCR appears truncated near a fix/DME, include a hold leg only when the nearby evidence supports the terminal fix/hold interpretation.
- If multiple visible symbols/text cells describe consecutive actions, split them into consecutive legs only when candidate_legs do not already group them.
- A climb arrow with an altitude usually forms an altitude/climb leg.
- A turn arrow plus heading/course/radial usually forms a course/turn leg.
- A named fix/navaid cell usually contributes Q1_fix_ident to the leg that terminates at or references it.
- A hold instruction or holding-pattern symbol usually forms an HA/HF/HM-like hold leg if enough evidence is visible; otherwise use unknown terminator but keep hold parameters if visible.
- If evidence contains candidate_legs, treat them as chart-derived hints, not as guaranteed answers. Use them to decide leg order and field mapping, but keep "unknown" or "not_observable" when evidence is insufficient.
- If the chart evidence clearly implies a standard value, use status "present"; if it is not visible or uncertain, do not force it.

Evidence JSON:
"""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def extract_json_text(text: str) -> str:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in LLM output")
    return text[start : end + 1]


def compact_token(token: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": token.get("text", ""),
        "confidence": token.get("confidence"),
        "bbox": token.get("bbox"),
        "source_region_type": token.get("source_region_type", ""),
    }


def compact_b1_evidence(prompt_input: dict[str, Any]) -> dict[str, Any]:
    evidence = prompt_input["input_evidence"]
    return {
        "sample_id": prompt_input["sample_id"],
        "method": "B1",
        "ocr_scope": "full_page",
        "ocr_text": evidence.get("ocr_text", ""),
        "note": "Full-page OCR baseline. OCR token bboxes are saved in raw files but omitted here to keep the prompt compact.",
    }


def compact_b3_item(item: dict[str, Any]) -> dict[str, Any]:
    tokens = item.get("ocr_tokens", [])
    return {
        "region_id": item.get("region_id", ""),
        "candidate_type": item.get("candidate_type", ""),
        "source_region_type": item.get("source_region_type", ""),
        "source_region": item.get("source_region", ""),
        "bbox": item.get("bbox"),
        "ocr_text": item.get("ocr_text", ""),
        "ocr_tokens": [compact_token(token) for token in tokens],
    }


def compact_b3_evidence(prompt_input: dict[str, Any]) -> dict[str, Any]:
    evidence = prompt_input["input_evidence"]
    return {
        "sample_id": prompt_input["sample_id"],
        "method": "B3",
        "input_condition": "Region-aware OCR candidates from prior annotation/prelabel boxes. Original unboxed chart was used for OCR crops.",
        "regions": [compact_b3_item(item) for item in evidence.get("regions", [])],
        "elements": [compact_b3_item(item) for item in evidence.get("elements", [])],
    }


def compact_b3v2_evidence(prompt_input: dict[str, Any]) -> dict[str, Any]:
    evidence = prompt_input["input_evidence"]
    return {
        "sample_id": prompt_input["sample_id"],
        "method": "B3V2",
        "input_condition": evidence.get("input_condition", ""),
        "upper_missed_approach_text": evidence.get("upper_missed_approach_text", {}),
        "visual_cells": evidence.get("visual_cells", []),
        "candidate_legs": evidence.get("candidate_legs", []),
        "raw_elements_compact": evidence.get("raw_elements_compact", []),
    }


def compact_b3v3_evidence(prompt_input: dict[str, Any]) -> dict[str, Any]:
    evidence = prompt_input["input_evidence"]
    return {
        "sample_id": prompt_input["sample_id"],
        "method": "B3V3",
        "input_condition": evidence.get("input_condition", ""),
        "upper_missed_approach_text": evidence.get("upper_missed_approach_text", {}),
        "visual_cells_ocr_only": evidence.get("visual_cells_ocr_only", []),
        "candidate_legs": evidence.get("candidate_legs", []),
        "semantic_steps": evidence.get("semantic_steps", []),
        "prompt_contract": evidence.get("prompt_contract", {}),
    }


def build_user_prompt(method: str, prompt_input: dict[str, Any]) -> str:
    if method == "B1":
        evidence = compact_b1_evidence(prompt_input)
    elif method == "B3V3":
        evidence = compact_b3v3_evidence(prompt_input)
    elif method == "B3V2":
        evidence = compact_b3v2_evidence(prompt_input)
    else:
        evidence = compact_b3_evidence(prompt_input)
    return USER_INSTRUCTIONS + json.dumps(evidence, ensure_ascii=False, indent=2)


def answer(status: str = "unknown", value: Any = None) -> dict[str, Any]:
    if status not in STATUS:
        status = "unknown"
    if status != "present":
        value = None
    return {"status": status, "value": value}


def normalize_answer(field: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return answer()
    status = value.get("status", "unknown")
    if status not in STATUS:
        status = "unknown"
    raw_value = value.get("value")
    if status != "present":
        return answer(status, None)

    if field == "Q3_turn" and isinstance(raw_value, str):
        upper = raw_value.upper()
        if upper in {"LEFT", "RIGHT"}:
            raw_value = upper
        else:
            return answer("unknown", None)
    if field == "Q_terminator" and isinstance(raw_value, str):
        raw_value = raw_value.upper()
    return answer("present", raw_value)


def normalize_llm_payload(payload: dict[str, Any], sample: dict[str, Any]) -> dict[str, Any]:
    ma = payload.get("missed_approach", payload if "legs" in payload else {})
    if not isinstance(ma, dict):
        ma = {}
    legs_in = ma.get("legs", [])
    if not isinstance(legs_in, list):
        legs_in = []

    legs = []
    for idx, leg in enumerate(legs_in, start=1):
        if not isinstance(leg, dict):
            leg = {}
        answers_in = leg.get("answers", {})
        if not isinstance(answers_in, dict):
            answers_in = {}
        legs.append(
            {
                "leg_index": idx,
                "answers": {
                    field: normalize_answer(field, answers_in.get(field))
                    for field in Q_FIELDS
                },
            }
        )

    leg_count = ma.get("leg_count")
    if isinstance(leg_count, dict) and leg_count.get("status") == "unknown" and not legs:
        normalized_leg_count = answer("unknown", None)
    else:
        normalized_leg_count = answer("present", len(legs))

    return {
        "chart_id": sample["chart_id"],
        "procedure": {
            "airport": sample["airport"],
            "approach_ident": sample["approach_ident"],
            "chart_name": sample["chart_name"],
        },
        "missed_approach": {
            "leg_count": normalized_leg_count,
            "legs": legs,
        },
    }


def empty_leg(index: int) -> dict[str, Any]:
    return {
        "leg_index": index,
        "answers": {field: answer("unknown", None) for field in Q_FIELDS},
    }


def candidate_q_hint(candidate: dict[str, Any], field: str) -> dict[str, Any] | None:
    hints = candidate.get("q_hints", {})
    if not isinstance(hints, dict):
        return None
    hint = hints.get(field)
    return hint if isinstance(hint, dict) else None


def hint_answer(field: str, hint: dict[str, Any]) -> dict[str, Any] | None:
    status = hint.get("status_hint")
    if status not in STATUS:
        return None
    return normalize_answer(field, {"status": status, "value": hint.get("observed_value")})


def has_hold_value(value: Any) -> bool:
    return isinstance(value, dict) and any(item is not None for item in value.values())


def apply_b3v3_candidate_postprocess(method_output: dict[str, Any], prompt_input: dict[str, Any]) -> dict[str, Any]:
    evidence = prompt_input.get("input_evidence", {})
    candidates = evidence.get("candidate_legs", [])
    if not isinstance(candidates, list) or not candidates:
        return method_output

    ma = method_output.get("missed_approach", {})
    legs = ma.get("legs", [])
    if not isinstance(legs, list):
        legs = []

    # B3V3 candidate_legs are the OCR-only leg-order hypotheses. Align the
    # normalized output to that sequence so the LLM cannot accidentally split
    # one cell/action into extra canonical legs.
    aligned_legs: list[dict[str, Any]] = []
    for idx, candidate in enumerate(candidates, start=1):
        source_leg = legs[idx - 1] if idx - 1 < len(legs) and isinstance(legs[idx - 1], dict) else empty_leg(idx)
        answers = source_leg.get("answers", {})
        if not isinstance(answers, dict):
            answers = {}
        merged = {
            "leg_index": idx,
            "answers": {
                field: answers.get(field, answer("unknown", None))
                if isinstance(answers.get(field), dict)
                else answer("unknown", None)
                for field in Q_FIELDS
            },
        }

        for field in Q_FIELDS:
            field_hint = candidate_q_hint(candidate, field)
            if not field_hint:
                continue
            if field == "Q5_hold_params" and field_hint.get("status_hint") == "present" and not has_hold_value(field_hint.get("observed_value")):
                continue
            field_answer = hint_answer(field, field_hint)
            if field_answer:
                merged["answers"][field] = field_answer

        aligned_legs.append(merged)

    method_output["missed_approach"]["legs"] = aligned_legs
    method_output["missed_approach"]["leg_count"] = answer("present", len(aligned_legs))
    return method_output


@dataclass
class LLMConfig:
    provider: str
    model: str
    temperature: float
    max_tokens: int


class LLMClient:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        if config.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            auth_token = os.getenv("ANTHROPIC_AUTH_TOKEN")
            base_url = os.getenv("ANTHROPIC_BASE_URL")
            if not api_key and not auth_token:
                raise SystemExit("Missing ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN")
            self.client = anthropic.Anthropic(api_key=api_key, auth_token=auth_token, base_url=base_url)
        elif config.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")
            if not api_key:
                raise SystemExit("Missing OPENAI_API_KEY")
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            raise SystemExit(f"Unsupported provider: {config.provider}")

    def call(self, user_prompt: str) -> str:
        if self.config.provider == "anthropic":
            message = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return "".join(block.text for block in message.content if getattr(block, "type", None) == "text")

        response = self.client.chat.completions.create(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""


def sample_map(root: Path) -> dict[str, dict[str, Any]]:
    samples = read_json(root / "data/pilot10/sample_map_private.json")
    return {item["sample_id"]: item for item in samples}


def input_dir(root: Path, method: str) -> Path:
    if method == "B1":
        return root / "outputs/B1_ocr_llm/prompt_inputs"
    if method == "B3V3":
        return root / "outputs/B3_region_ocr_llm_v3/prompt_inputs"
    if method == "B3V2":
        return root / "outputs/B3_region_ocr_llm_v2/prompt_inputs"
    return root / "outputs/B3_region_ocr_llm/prompt_inputs"


def output_root(root: Path, method: str) -> Path:
    if method == "B1":
        return root / "outputs/B1_ocr_llm"
    if method == "B3V3":
        return root / "outputs/B3_region_ocr_llm_v3"
    if method == "B3V2":
        return root / "outputs/B3_region_ocr_llm_v2"
    return root / "outputs/B3_region_ocr_llm"


def run_method(root: Path, method: str, client: LLMClient, sample_id: str | None, force: bool) -> list[dict[str, Any]]:
    samples = sample_map(root)
    files = sorted(input_dir(root, method).glob("*.json"))
    if sample_id:
        files = [path for path in files if path.name.startswith(f"{sample_id}__")]
        if not files:
            raise SystemExit(f"No prompt input found for {method} {sample_id}")

    out_root = output_root(root, method)
    report = []
    for prompt_path in files:
        prompt_input = read_json(prompt_path)
        sid = prompt_input["sample_id"]
        sample = samples[sid]
        method_output_path = out_root / "method_outputs" / f"{sample['chart_id']}.json"
        if method_output_path.exists() and not force:
            report.append({"sample_id": sid, "method": method, "status": "skipped_existing"})
            continue

        print(f"[{method}] LLM extraction: {sid}")
        user_prompt = build_user_prompt(method, prompt_input)
        write_text(out_root / "llm_prompts" / f"{sid}__prompt.txt", f"{SYSTEM_PROMPT}\n\n{user_prompt}")

        raw_text = client.call(user_prompt)
        write_text(out_root / "llm_raw" / f"{sid}__raw.txt", raw_text)

        try:
            payload = json.loads(extract_json_text(raw_text))
            write_json(out_root / "llm_json" / f"{sid}__llm_fragment.json", payload)
            method_output = normalize_llm_payload(payload, sample)
            if method == "B3V3":
                method_output = apply_b3v3_candidate_postprocess(method_output, prompt_input)
            write_json(method_output_path, method_output)
            report.append(
                {
                    "sample_id": sid,
                    "chart_id": sample["chart_id"],
                    "method": method,
                    "status": "ok",
                    "leg_count": method_output["missed_approach"]["leg_count"]["value"],
                }
            )
        except Exception as exc:  # Keep raw output for manual repair.
            report.append(
                {
                    "sample_id": sid,
                    "chart_id": sample["chart_id"],
                    "method": method,
                    "status": "parse_failed",
                    "error": str(exc),
                }
            )
            print(f"  WARNING: parse failed for {sid}: {exc}")

    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run B1/B3/B3V2/B3V3 LLM extraction.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--method", choices=["B1", "B3", "B3V2", "B3V3", "all"], default="all")
    parser.add_argument("--sample-id", default=None)
    parser.add_argument("--provider", choices=["anthropic", "openai"], default=os.getenv("B1B3_LLM_PROVIDER", "anthropic"))
    parser.add_argument("--model", default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    model = args.model
    if not model:
        model = os.getenv("B1B3_LLM_MODEL")
    if not model:
        model = "claude-sonnet-4-6" if args.provider == "anthropic" else "gpt-4.1"

    client = LLMClient(
        LLMConfig(
            provider=args.provider,
            model=model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
    )

    report: list[dict[str, Any]] = []
    if args.method in {"B1", "all"}:
        report.extend(run_method(root, "B1", client, args.sample_id, args.force))
    if args.method in {"B3", "all"}:
        report.extend(run_method(root, "B3", client, args.sample_id, args.force))
    if args.method in {"B3V2", "all"}:
        report.extend(run_method(root, "B3V2", client, args.sample_id, args.force))
    if args.method in {"B3V3", "all"}:
        report.extend(run_method(root, "B3V3", client, args.sample_id, args.force))

    write_json(
        root / "outputs/llm_extraction_manifest.json",
        {
            "provider": args.provider,
            "model": model,
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
            "report": report,
        },
    )
    print(f"Wrote {root / 'outputs/llm_extraction_manifest.json'}")


if __name__ == "__main__":
    main()
