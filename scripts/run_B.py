"""
Path B: PaddleOCR + LLM
先用 PaddleOCR 提取文本，再用 claude-sonnet-4-6 从文本提取 JSON。

运行环境: conda activate ocr_exp
"""

import json
import os
import re
import sys
from pathlib import Path

import anthropic
try:
    from paddleocr import PaddleOCR
except ImportError as exc:
    print("Missing dependency: paddleocr. Install it in the experiment environment before running Path B.")
    raise SystemExit(1) from exc

sys.path.insert(0, str(Path(__file__).parent))
from dataset_config import CHARTS_DIR as DATA_CHARTS_DIR, MANIFEST_PATH, PROMPTS_DIR as DATA_PROMPTS_DIR, RESULTS_DIR

MANIFEST    = MANIFEST_PATH
CHARTS_DIR  = DATA_CHARTS_DIR
PROMPTS_DIR = DATA_PROMPTS_DIR
OUT_DIR     = RESULTS_DIR / "B"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL       = "claude-sonnet-4-6"
TEMPERATURE = 0

# ── Load prompts ──────────────────────────────────────────────────────────────
system_prompt = (PROMPTS_DIR / "path_b_system.txt").read_text(encoding="utf-8").strip()
user_template = (PROMPTS_DIR / "path_b_user.txt").read_text(encoding="utf-8").strip()

# ── OCR 初始化 ────────────────────────────────────────────────────────────────
ocr = PaddleOCR(use_textline_orientation=True, lang="en")

api_key = os.getenv("ANTHROPIC_API_KEY")
auth_token = os.getenv("ANTHROPIC_AUTH_TOKEN")
base_url = os.getenv("ANTHROPIC_BASE_URL")

if not api_key and not auth_token:
    print("Missing credentials: set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN before running Path B.")
    raise SystemExit(1)

# ── Anthropic client ──────────────────────────────────────────────────────────
client = anthropic.Anthropic(
    api_key=api_key,
    auth_token=auth_token,
    base_url=base_url,
)


def run_ocr(image_path):
    result = ocr.predict(str(image_path))
    lines = []
    if result:
        for page in result:
            if page is None:
                continue
            texts = page.get("rec_texts", []) if hasattr(page, "get") else []
            lines.extend(text for text in texts if text)
    return "\n".join(lines)


def parse_json_from_response(text):
    """Extract the first JSON object from LLM response text."""
    # Try to find JSON block
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def call_llm(ocr_text):
    user_content = user_template.replace("{ocr_text}", ocr_text)
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        temperature=TEMPERATURE,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    response_text = message.content[0].text
    return response_text


# ── Main ──────────────────────────────────────────────────────────────────────
with open(MANIFEST, encoding="utf-8") as f:
    manifest = json.load(f)

for entry in manifest:
    sid        = entry["id"]
    image_file = CHARTS_DIR / entry["image"]

    print(f"Processing {sid}...")

    # Step 1: OCR
    ocr_text = run_ocr(image_file)
    (OUT_DIR / f"{sid}_ocr.txt").write_text(ocr_text, encoding="utf-8")
    print(f"  OCR: {len(ocr_text)} chars")

    # Step 2: LLM
    response_text = call_llm(ocr_text)
    (OUT_DIR / f"{sid}_response.txt").write_text(response_text, encoding="utf-8")

    parsed = parse_json_from_response(response_text)
    if parsed is None:
        print(f"  WARNING: Could not parse JSON from response for {sid}")
        parsed = {"error": "parse_failed", "raw_response": response_text}

    out_path = OUT_DIR / f"{sid}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)

    print(f"  -> climb={parsed.get('climb_altitude')}, "
          f"turn={parsed.get('turn_direction')}, "
          f"holding={parsed.get('holding_required')}, "
          f"fix={parsed.get('holding_fix')}")

print(f"\nPath B 完成: {len(manifest)} 个样本 -> {OUT_DIR}")
