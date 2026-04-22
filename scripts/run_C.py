"""
Path C: multi-question QA over chart images.

This path implements the new "C" method:
image input + multiple single-field QA + final JSON aggregation.

Outputs are written under:
  e:/experiment/results/v2604_100/C
"""

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).parent))
from dataset_config import CHARTS_DIR as DATA_CHARTS_DIR, MANIFEST_PATH, PROMPTS_DIR as DATA_PROMPTS_DIR, RESULTS_DIR

MANIFEST = MANIFEST_PATH
CHARTS_DIR = DATA_CHARTS_DIR
PROMPTS_DIR = DATA_PROMPTS_DIR
OUT_DIR = RESULTS_DIR / "C"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "claude-sonnet-4-6"
TEMPERATURE = 0
MAX_TOKENS_PER_Q = {
    "raw_instruction": 300,
    "climb_altitude": 64,
    "turn_direction": 64,
    "holding_required": 64,
    "holding_fix": 64,
    "waypoints": 128,
}

PROMPT_FILES = {
    "raw_instruction": "path_c_qa_q1_raw_instruction.txt",
    "climb_altitude": "path_c_qa_q2_climb_altitude.txt",
    "turn_direction": "path_c_qa_q3_turn_direction.txt",
    "holding_required": "path_c_qa_q4_holding_required.txt",
    "holding_fix": "path_c_qa_q5_holding_fix.txt",
    "waypoints": "path_c_qa_q6_waypoints.txt",
}

SYSTEM_PROMPT = (PROMPTS_DIR / "path_c_qa_system.txt").read_text(encoding="utf-8").strip()
QUESTION_PROMPTS = {
    key: (PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()
    for key, filename in PROMPT_FILES.items()
}

api_key = os.getenv("ANTHROPIC_API_KEY")
auth_token = os.getenv("ANTHROPIC_AUTH_TOKEN")
base_url = os.getenv("ANTHROPIC_BASE_URL")

if not api_key and not auth_token:
    print("Missing credentials: set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN before running Path C.")
    raise SystemExit(1)

client = anthropic.Anthropic(
    api_key=api_key,
    auth_token=auth_token,
    base_url=base_url,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Run multi-question QA for Path C.")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N samples.")
    parser.add_argument("--skip-existing", action="store_true", help="Skip samples whose final JSON already exists.")
    return parser.parse_args()


def image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def call_llm(image_path, user_text, max_tokens):
    img_b64 = image_to_base64(image_path)
    img_data = {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": img_b64,
        },
    }
    message = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=TEMPERATURE,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    img_data,
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    )
    return message.content[0].text.strip()


def parse_raw_instruction(text):
    text = text.strip()
    if not text:
        return "unknown"
    if text.lower() == "unknown":
        return "unknown"
    text = (
        text.replace("掳", "°")
        .replace("\\u00b0", "°")
        .replace("\u00c5", " ")
    )
    return text


def parse_climb_altitude(text):
    text = text.strip()
    if not text or text.lower() == "unknown":
        return "unknown"
    match = re.search(r"\d{3,5}", text.replace(",", ""))
    if not match:
        return "unknown"
    return int(match.group())


def parse_turn_direction(text):
    text = text.strip().upper()
    return text if text in {"LEFT", "RIGHT", "NONE", "UNKNOWN"} else "unknown"


def parse_holding_required(text):
    text = text.strip().lower()
    if text in {"true", "false", "unknown"}:
        return True if text == "true" else False if text == "false" else "unknown"
    return "unknown"


def parse_holding_fix(text, holding_required):
    text = text.strip()
    low = text.lower()
    if holding_required is False and low in {"null", "unknown", ""}:
        return None
    if low == "null":
        return None
    if low == "unknown" or not text:
        return "unknown"
    match = re.search(r"\b([A-Z]{3,6})\b", text.upper())
    if not match:
        return "unknown"
    return match.group(1)


def parse_waypoints(text):
    text = text.strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            result = []
            for item in parsed:
                item_text = str(item).strip().upper()
                if item_text:
                    result.append(item_text)
            return result
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, list):
                return [str(item).strip().upper() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass

    return []


def build_final_json(parsed_answers):
    holding_required = parsed_answers["holding_required"]
    holding_fix = parsed_answers["holding_fix"]
    if holding_required is False:
        holding_fix = None

    return {
        "raw_instruction": parsed_answers["raw_instruction"],
        "climb_altitude": parsed_answers["climb_altitude"],
        "waypoints": parsed_answers["waypoints"],
        "turn_direction": parsed_answers["turn_direction"],
        "holding_required": holding_required,
        "holding_fix": holding_fix,
        "initial_track": None,
        "turn_trigger": None,
        "holding_details": None,
    }


def run_questions(image_path):
    raw_responses = {}
    parsed_answers = {}

    for field, prompt in QUESTION_PROMPTS.items():
        response_text = call_llm(image_path, prompt, MAX_TOKENS_PER_Q[field])
        raw_responses[field] = {
            "prompt": prompt,
            "response": response_text,
        }

        if field == "raw_instruction":
            parsed_answers[field] = parse_raw_instruction(response_text)
        elif field == "climb_altitude":
            parsed_answers[field] = parse_climb_altitude(response_text)
        elif field == "turn_direction":
            parsed_answers[field] = parse_turn_direction(response_text)
        elif field == "holding_required":
            parsed_answers[field] = parse_holding_required(response_text)
        elif field == "holding_fix":
            parsed_answers[field] = parse_holding_fix(
                response_text,
                parsed_answers.get("holding_required", "unknown"),
            )
        elif field == "waypoints":
            parsed_answers[field] = parse_waypoints(response_text)

    return raw_responses, parsed_answers


args = parse_args()

with open(MANIFEST, encoding="utf-8") as f:
    manifest = json.load(f)

if args.limit is not None:
    manifest = manifest[: args.limit]

for entry in manifest:
    sid = entry["id"]
    image_file = CHARTS_DIR / entry["image"]
    out_path = OUT_DIR / f"{sid}.json"
    qa_path = OUT_DIR / f"{sid}_qa.json"

    if args.skip_existing and out_path.exists() and qa_path.exists():
        print(f"Skipping {sid} (already exists)...")
        continue

    print(f"Processing {sid} ({image_file.name})...")

    raw_responses, parsed_answers = run_questions(image_file)
    final_json = build_final_json(parsed_answers)

    qa_payload = {
        "id": sid,
        "image": entry["image"],
        "model": MODEL,
        "system_prompt": SYSTEM_PROMPT,
        "questions": raw_responses,
        "parsed_answers": parsed_answers,
    }
    qa_path.write_text(json.dumps(qa_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    out_path.write_text(json.dumps(final_json, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"  -> climb={final_json['climb_altitude']}, "
        f"turn={final_json['turn_direction']}, "
        f"holding={final_json['holding_required']}, "
        f"fix={final_json['holding_fix']}, "
        f"wpts={final_json['waypoints']}"
    )

print(f"\nPath C QA staging completed: {len(manifest)} samples -> {OUT_DIR}")
