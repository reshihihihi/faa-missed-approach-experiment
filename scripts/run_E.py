"""
Path D: 约束多模态 LLM（问卷 + JSON）
将图表图像传给 claude-sonnet-4-6，先回答 6 道字段确认问卷，再提取 JSON。

运行环境: conda activate ocr_exp
"""

import json
import base64
import os
import re
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).parent))
from dataset_config import CHARTS_DIR as DATA_CHARTS_DIR, MANIFEST_PATH, PROMPTS_DIR as DATA_PROMPTS_DIR, RESULTS_DIR

MANIFEST    = MANIFEST_PATH
CHARTS_DIR  = DATA_CHARTS_DIR
PROMPTS_DIR = DATA_PROMPTS_DIR
OUT_DIR     = RESULTS_DIR / "E"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL       = "claude-sonnet-4-6"
TEMPERATURE = 0

# ── Load prompts ──────────────────────────────────────────────────────────────
system_prompt = (PROMPTS_DIR / "path_e_system.txt").read_text(encoding="utf-8").strip()
user_text     = (PROMPTS_DIR / "path_e_user.txt").read_text(encoding="utf-8").strip()

api_key = os.getenv("ANTHROPIC_API_KEY")
auth_token = os.getenv("ANTHROPIC_AUTH_TOKEN")
base_url = os.getenv("ANTHROPIC_BASE_URL")

if not api_key and not auth_token:
    print("Missing credentials: set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN before running Path E.")
    raise SystemExit(1)

# ── Anthropic client ──────────────────────────────────────────────────────────
client = anthropic.Anthropic(
    api_key=api_key,
    auth_token=auth_token,
    base_url=base_url,
)


def image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def parse_questionnaire(text):
    """Parse QUESTIONNAIRE_ANSWERS block."""
    answers = {}
    for q in range(1, 7):
        m = re.search(rf"Q{q}:\s*(yes|no|uncertain)", text, re.IGNORECASE)
        if m:
            answers[f"Q{q}"] = m.group(1).lower()
        else:
            answers[f"Q{q}"] = "not_found"
    return answers


def parse_json_from_response(text):
    """Extract JSON block that follows 'JSON:' in Path D output."""
    # Try to find after JSON: marker
    json_section = re.split(r"^JSON:\s*$", text, flags=re.MULTILINE)
    if len(json_section) > 1:
        candidate = json_section[-1].strip()
    else:
        candidate = text

    match = re.search(r"\{[\s\S]*\}", candidate)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def call_llm(image_path):
    img_b64  = image_to_base64(image_path)
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
        max_tokens=1500,
        temperature=TEMPERATURE,
        system=system_prompt,
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
    return message.content[0].text


# ── Main ──────────────────────────────────────────────────────────────────────
with open(MANIFEST, encoding="utf-8") as f:
    manifest = json.load(f)

for entry in manifest:
    sid        = entry["id"]
    image_file = CHARTS_DIR / entry["image"]

    print(f"Processing {sid} ({image_file.name})...")

    response_text = call_llm(image_file)
    (OUT_DIR / f"{sid}_response.txt").write_text(response_text, encoding="utf-8")

    # Parse questionnaire
    qa = parse_questionnaire(response_text)
    print(f"  Questionnaire: {qa}")

    # Parse JSON
    parsed = parse_json_from_response(response_text)
    if parsed is None:
        print(f"  WARNING: Could not parse JSON from response for {sid}")
        parsed = {"error": "parse_failed", "raw_response": response_text}

    # Attach questionnaire answers to output for analysis
    parsed["_questionnaire"] = qa

    out_path = OUT_DIR / f"{sid}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)

    print(f"  -> climb={parsed.get('climb_altitude')}, "
          f"turn={parsed.get('turn_direction')}, "
          f"holding={parsed.get('holding_required')}, "
          f"fix={parsed.get('holding_fix')}")

print(f"\nPath E completed: {len(manifest)} samples -> {OUT_DIR}")
