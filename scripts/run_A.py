"""
Path A: PaddleOCR 规则提取
使用 PaddleOCR 对图表图像进行 OCR，然后用正则规则提取复飞信息。

运行环境: conda activate ocr_exp
"""

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

try:
    from paddleocr import PaddleOCR
except ImportError as exc:
    print("Missing dependency: paddleocr. Install it in the experiment environment before running Path A.")
    raise SystemExit(1) from exc

sys.path.insert(0, str(Path(__file__).parent))
from dataset_config import CHARTS_DIR as DATA_CHARTS_DIR, MANIFEST_PATH, RESULTS_DIR

MANIFEST   = MANIFEST_PATH
CHARTS_DIR = DATA_CHARTS_DIR
OUT_DIR    = RESULTS_DIR / "A"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── OCR 初始化 ────────────────────────────────────────────────────────────────
ocr = PaddleOCR(use_textline_orientation=True, lang="en")

# ── 正则规则 ──────────────────────────────────────────────────────────────────
# 复飞指令通常形如：
#   CLIMBING LEFT TURN TO 3000 VIA ... HOLD AT ...
#   CLIMB TO 3000 DIRECT BACHS HOLD IN LIEU...
#   CLIMBING TURN RIGHT TO 2700 TO PIMKE THEN HOLD...

RE_MA_LINE = re.compile(
    r"(CLIMB(?:ING)?|MISSED\s+APPROACH)",
    re.IGNORECASE,
)

RE_ALTITUDE = re.compile(
    r"\b(\d{3,5})\b",
)

RE_TURN_LEFT  = re.compile(r"\bLEFT\s*TURN\b|\bTURN\s*LEFT\b", re.IGNORECASE)
RE_TURN_RIGHT = re.compile(r"\bRIGHT\s*TURN\b|\bTURN\s*RIGHT\b", re.IGNORECASE)

RE_HOLD = re.compile(r"\bHOLD(?:ING)?\b", re.IGNORECASE)
RE_FREQ = re.compile(r"\b\d{3}(?:\.\d{1,3})?\b")
RE_MISSED_APCH = re.compile(r"\bMISSED\s+AP(?:PROACH|CH)\b", re.IGNORECASE)
RE_ACTION = re.compile(
    r"\b(CLIMB(?:ING)?|TURN|DIRECT|HEADING|TRACK|COURSE|HOLD(?:ING)?|DME)\b",
    re.IGNORECASE,
)
RE_FIVE_LETTER_FIX = re.compile(r"\b([A-Z]{5})\b")
RE_CONTEXT_FIX = re.compile(
    r"\b(?:DIRECT|TO|OVER|AT)\s+([A-Z]{3,5})(?:/[A-Z]{3,5})?\b",
    re.IGNORECASE,
)

# 5-char uppercase waypoint name (letters only, not common words)
COMMON_WORDS = {
    "CLIMB", "CLIMBING", "DIRECT", "TURN", "LEFT", "RIGHT",
    "HOLD", "HOLDING", "THEN", "CROSS", "UNTIL", "RADAR",
    "CONTACT", "TOWER", "APPROACH", "MISSED", "PROCEDURE",
    "CLIMB", "LEVEL", "IDENT", "VISUAL", "INBOUND", "OUTBOUND",
    "TRACK", "COURSE", "HEADING", "FEET", "KNOTS", "MILES",
    "ABOVE", "BELOW", "MSL", "AGL", "DME", "VOR", "NDB", "ILS",
    "RNAV", "GNSS", "GPS", "LOC", "GLIDE", "SLOPE",
    "FOR", "ALL", "AND", "CATS", "CAT", "INOP", "ALSF", "MALSR",
    "ATIS", "TOWER", "CENTER", "APP", "CON", "CTAF", "UNICOM",
    "NIGHT", "NA", "VIS", "RVR", "SM", "SYSTEMS", "AUTHORIZED",
    "SIMULTANEOUS", "APPROACH", "MISSED", "PROCEDURE", "VISIBILITY",
    "INCREASE", "CONTINUE", "REQUIRED", "ENTRY", "FROM", "BELOW",
    "ABOVE", "CIRCLING", "RWY", "RW", "HELICOPTER", "LOCAL", "USING",
    "ALTIMETER", "SETTING", "RECEIVED", "REDUCTION", "BELOW",
}

RE_WAYPOINT = re.compile(r"\b([A-Z]{2,6})\b")


def clean_line(text):
    text = text.replace("\u00b0", " ").replace("\u00c5", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def looks_like_non_ma_line(text):
    upper = text.upper()
    if not upper:
        return True
    if RE_FREQ.search(upper) and not RE_ACTION.search(upper):
        return True
    stop_markers = {
        "ATIS", "TOWER", "GROUND", "GND CON", "UNICOM", "CENTER",
        "APP CON", "APPROACH CON", "CTAF", "DEPARTURE", "CLEARANCE",
    }
    return any(marker in upper for marker in stop_markers)


def extract_waypoints(text):
    text = text.upper()
    candidates = []

    for match in RE_CONTEXT_FIX.finditer(text):
        candidates.append(match.group(1))

    for match in RE_FIVE_LETTER_FIX.finditer(text):
        candidates.append(match.group(1))

    for match in RE_WAYPOINT.finditer(text):
        candidates.append(match.group(1))

    seen = set()
    result = []
    for w in candidates:
        if w in COMMON_WORDS or w in seen or len(w) < 3:
            continue
        if len(w) == 3 and not RE_CONTEXT_FIX.search(text):
            continue
        if len(w) not in {3, 5}:
            continue
        if not w.isalpha():
            continue
        if len(w) == 3 and w not in {"ALS"} and not re.search(
            rf"\b(?:DIRECT|TO|AT|OVER|HOLD(?:ING)?(?:\s+AT)?)\s+{w}\b", text
        ):
            continue
        if len(w) == 5 and re.search(rf"\b{w}\b", text):
            seen.add(w)
            result.append(w)
    return result


def extract_ma_text(ocr_lines):
    """Collect the local OCR window around the MISSED APPROACH anchor."""
    cleaned = [clean_line(line) for line in ocr_lines]
    anchors = [idx for idx, line in enumerate(cleaned) if RE_MISSED_APCH.search(line)]

    if not anchors:
        # Fallback to the old broad heuristic if the heading was OCR'd poorly.
        for idx, line in enumerate(cleaned):
            if RE_MA_LINE.search(line):
                anchors = [idx]
                break

    best_text = ""
    best_score = -1

    for idx in anchors:
        start = max(0, idx - 2)
        window = cleaned[start:min(len(cleaned), idx + 10)]
        selected = []
        for pos, line in enumerate(window):
            upper = line.upper()
            if not upper:
                continue
            if looks_like_non_ma_line(upper):
                continue
            absolute_idx = start + pos
            if absolute_idx == idx or RE_MISSED_APCH.search(upper):
                selected.append(line)
                continue
            if absolute_idx < idx:
                if RE_ACTION.search(upper):
                    selected.append(line)
                continue
            if RE_ACTION.search(upper) or RE_FIVE_LETTER_FIX.search(upper):
                selected.append(line)

        candidate = " ".join(selected)
        candidate = re.split(
            r"\b(?:ATIS|TOWER|GROUND|GND CON|UNICOM|CENTER|APP CON|APPROACH CON|CTAF)\b",
            candidate,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        score = 0
        if RE_MISSED_APCH.search(candidate):
            score += 3
        score += len(RE_ACTION.findall(candidate))
        score += 2 * len(RE_FIVE_LETTER_FIX.findall(candidate))

        if score > best_score:
            best_text = candidate
            best_score = score

    return best_text


def process_image(image_path):
    result = ocr.predict(str(image_path))
    if not result:
        return [], ""

    lines = []
    for page in result:
        if page is None:
            continue
        texts = page.get("rec_texts", []) if hasattr(page, "get") else []
        lines.extend(text for text in texts if text)

    full_text = "\n".join(lines)
    ma_text = extract_ma_text(lines)

    return lines, full_text, ma_text


def extract_info(ma_text, all_lines_text):
    """Extract fields from MA text using regex rules."""

    raw_instruction = ma_text.strip() if ma_text.strip() else "unknown"

    # climb_altitude: largest altitude-like number in MA text
    # (prefers 4-5 digit numbers, i.e. thousands of feet)
    altitudes = [int(m) for m in RE_ALTITUDE.findall(ma_text) if 500 <= int(m) <= 99000]
    if altitudes:
        # The climb-to altitude is typically the largest mentioned
        climb_altitude = max(altitudes)
    else:
        climb_altitude = "unknown"

    # turn direction
    if RE_TURN_LEFT.search(ma_text):
        turn_direction = "LEFT"
    elif RE_TURN_RIGHT.search(ma_text):
        turn_direction = "RIGHT"
    else:
        turn_direction = "NONE"

    # holding
    holding_required = bool(RE_HOLD.search(ma_text) or "CLIMB-IN-HOLD" in ma_text.upper())

    # waypoints (prefer contextual tokens and 5-letter fixes)
    waypoints = extract_waypoints(ma_text)

    # holding fix: focus on the fix named in direct-to-hold or hold-at phrases
    holding_fix = None
    if holding_required:
        patterns = [
            r"\bDIRECT\s+([A-Z]{3,5})\s+AND\s+HOLD\b",
            r"\bDIRECT\s+([A-Z]{3,5})\s+(?:VORTAC|VOR/DME|VOR|NDB)\s+AND\s+HOLD\b",
            r"\bTO\s+([A-Z]{3,5})(?:/[A-Z]{3,5})?\s+\d+\s*DME\s+AND\s+HOLD\b",
            r"\bTO\s+([A-Z]{3,5})\s+AND\s+HOLD\b",
            r"\bHOLD(?:ING)?\s+(?:AT|OVER|IN\s+LIEU\s+OF)\s+([A-Z]{3,5})\b",
        ]
        upper_text = ma_text.upper()
        for pattern in patterns:
            m = re.search(pattern, upper_text)
            if m:
                candidate = m.group(1)
                if candidate not in COMMON_WORDS:
                    holding_fix = candidate
                    break

        if not holding_fix:
            for candidate in waypoints:
                if candidate not in COMMON_WORDS:
                    holding_fix = candidate
                    break

    initial_track = None
    turn_trigger  = None
    holding_details = None

    return {
        "raw_instruction": raw_instruction,
        "climb_altitude": climb_altitude,
        "waypoints": waypoints,
        "turn_direction": turn_direction,
        "holding_required": holding_required,
        "holding_fix": holding_fix,
        "initial_track": initial_track,
        "turn_trigger": turn_trigger,
        "holding_details": holding_details,
    }


# ── Main ──────────────────────────────────────────────────────────────────────
with open(MANIFEST, encoding="utf-8") as f:
    manifest = json.load(f)

for entry in manifest:
    sid        = entry["id"]
    image_file = CHARTS_DIR / entry["image"]

    print(f"Processing {sid} ({image_file.name})...")
    lines, full_text, ma_text = process_image(image_file)

    info = extract_info(ma_text, full_text)

    # Save raw OCR text alongside result
    (OUT_DIR / f"{sid}_ocr.txt").write_text(full_text, encoding="utf-8")

    out_path = OUT_DIR / f"{sid}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    print(f"  MA text: {ma_text[:120]!r}")
    print(f"  -> climb={info['climb_altitude']}, turn={info['turn_direction']}, "
          f"holding={info['holding_required']}, fix={info['holding_fix']}, "
          f"wpts={info['waypoints']}")

print(f"\nPath A 完成: {len(manifest)} 个样本 -> {OUT_DIR}")
