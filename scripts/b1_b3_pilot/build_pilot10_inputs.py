import json
import os
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
EXP = Path(os.getenv("FAA_B1_B3_ROOT", REPO_ROOT)).expanduser().resolve()
ROOT = EXP.parent
MANIFEST = Path(os.getenv("FAA_B1_B3_PILOT_MANIFEST", EXP / "manifests/pilot_manifest_10.json")).expanduser().resolve()
PRELABEL_DIR = Path(os.getenv("FAA_B1_B3_PRELABEL_DIR", EXP / "prelabels")).expanduser().resolve()

ORIGINAL_DIR = EXP / "assets/charts_original"
BOXED_DIR = EXP / "review_only/boxed_previews"
PILOT_DIR = EXP / "data/pilot10"
B1_INPUT_DIR = PILOT_DIR / "b1_image_inputs"
B3_EVIDENCE_DIR = PILOT_DIR / "b3_evidence_packets"
B1_PROMPT_DIR = PILOT_DIR / "prompt_inputs_b1"
B3_PROMPT_DIR = PILOT_DIR / "prompt_inputs_b3"

PRIVATE_SAMPLE_MAP = PILOT_DIR / "sample_map_private.json"
PUBLIC_SAMPLE_INDEX = PILOT_DIR / "sample_index_public.json"
B1_MANIFEST = PILOT_DIR / "b1_image_input_manifest.json"
B3_MANIFEST = PILOT_DIR / "b3_evidence_manifest.json"

DISALLOWED_MAPPING_KEYS = {
    "candidate_mappings",
    "expected_value",
    "expected_answer",
    "canonical_leg_index",
    "candidate_leg_id",
    "leg_type",
    "field_name",
    "canonical_proxy_gt_file",
    "source_seq_no",
    "source_trans_ident",
    "raw_record",
    "target_fields",
}

REGION_TYPE_MAP = {
    "MISSED_APPROACH_TEXT": "missed_approach_text_box",
    "PLAN_VIEW": "plan_view_missed_context",
    "MISSED_APPROACH_DETAIL_AREA": "profile_missed_strip",
    "ALTITUDE_TEXT": "altitude_text",
    "CLIMB_ARROW": "arrow_symbol",
    "PATH_SEGMENT": "turn_arc",
    "NAVAID_TEXT": "navaid_text",
    "FIX_TEXT": "fix_text",
    "FIX_SYMBOL": "fix_symbol",
    "RADIAL_TEXT": "radial_text",
    "HEADING_TEXT": "heading_text",
    "HOLD_ARC": "hold_arc",
    "DME_TEXT": "distance_text",
}

COARSE_TYPES = {
    "MISSED_APPROACH_TEXT",
    "PLAN_VIEW",
    "MISSED_APPROACH_DETAIL_AREA",
}

COLORS = {
    "MISSED_APPROACH_TEXT": (201, 126, 17),
    "PLAN_VIEW": (24, 105, 84),
    "MISSED_APPROACH_DETAIL_AREA": (201, 126, 17),
    "ALTITUDE_TEXT": (229, 69, 69),
    "CLIMB_ARROW": (229, 69, 69),
    "PATH_SEGMENT": (229, 69, 69),
    "NAVAID_TEXT": (229, 69, 69),
    "FIX_TEXT": (229, 69, 69),
    "FIX_SYMBOL": (229, 69, 69),
    "RADIAL_TEXT": (229, 69, 69),
    "HEADING_TEXT": (229, 69, 69),
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalized_to_xyxy(bbox, width, height):
    x = float(bbox["x_center"]) * width
    y = float(bbox["y_center"]) * height
    w = float(bbox["width"]) * width
    h = float(bbox["height"]) * height
    return [x - w / 2, y - h / 2, x + w / 2, y + h / 2]


def clean_label(region):
    label = region.get("label") or region.get("region_type") or ""
    label = str(label).replace("\n", " ").strip()
    return label[:80]


def assert_no_mapping_fields(value, context):
    if isinstance(value, dict):
        bad = sorted(DISALLOWED_MAPPING_KEYS & set(value.keys()))
        if bad:
            raise ValueError(f"{context} contains disallowed keys: {bad}")
        for key, child in value.items():
            assert_no_mapping_fields(child, f"{context}.{key}")
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            assert_no_mapping_fields(child, f"{context}[{idx}]")


def copy_original(item, sample_id):
    src = Path(item["image_path"])
    suffix = src.suffix.lower()
    dst = ORIGINAL_DIR / f"{sample_id}__{item['chart_id']}__{src.stem}{suffix}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def draw_boxed_image(prelabel, original_path, boxed_path):
    image = Image.open(original_path).convert("RGBA")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()

    # Draw coarse boxes first so fine-grained boxes remain visible.
    regions = prelabel.get("regions", [])
    ordered = sorted(regions, key=lambda r: 0 if r.get("region_type") in COARSE_TYPES else 1)
    for region in ordered:
        bbox = region.get("bbox")
        if not bbox:
            continue
        region_type = region.get("region_type", "UNKNOWN")
        color = COLORS.get(region_type, (229, 69, 69))
        xyxy = normalized_to_xyxy(bbox, width, height)
        line_width = 5 if region_type in COARSE_TYPES else 3
        dash = region_type == "MISSED_APPROACH_DETAIL_AREA"
        if dash:
            draw_dashed_rectangle(draw, xyxy, color, line_width)
        else:
            draw.rectangle(xyxy, outline=color + (255,), width=line_width)
        label = region_type
        lx, ly = xyxy[0], max(0, xyxy[1] - 17)
        draw.rectangle([lx, ly, lx + min(260, len(label) * 8 + 8), ly + 16], fill=(255, 255, 255, 220))
        draw.text((lx + 3, ly + 1), label, fill=color + (255,), font=font)

    boxed_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(boxed_path)


def draw_dashed_rectangle(draw, xyxy, color, width):
    x1, y1, x2, y2 = xyxy
    dash_len = 18
    gap = 10
    for x in frange(x1, x2, dash_len + gap):
        draw.line([(x, y1), (min(x + dash_len, x2), y1)], fill=color + (255,), width=width)
        draw.line([(x, y2), (min(x + dash_len, x2), y2)], fill=color + (255,), width=width)
    for y in frange(y1, y2, dash_len + gap):
        draw.line([(x1, y), (x1, min(y + dash_len, y2))], fill=color + (255,), width=width)
        draw.line([(x2, y), (x2, min(y + dash_len, y2))], fill=color + (255,), width=width)


def frange(start, stop, step):
    value = start
    while value < stop:
        yield value
        value += step


def region_to_public(region, sample_id, index):
    region_type = region.get("region_type", "UNKNOWN")
    candidate_type = REGION_TYPE_MAP.get(region_type, region_type.lower())
    public = {
        "region_id": f"{sample_id}__r{index:03d}",
        "source_region": candidate_type if region_type in COARSE_TYPES else "profile_missed_strip",
        "candidate_type": candidate_type,
        "bbox": region.get("bbox"),
        "text": region.get("ocr_text") or infer_text_from_label(region),
        "confidence": region.get("confidence"),
        "extraction_method": "auto_prelabel_no_leakage",
        "source_region_type": region_type,
        "visual_label": clean_label(region),
    }
    assert_no_mapping_fields(public, public["region_id"])
    return public


def infer_text_from_label(region):
    label = str(region.get("label") or "")
    if ":" not in label:
        return ""
    tail = label.split(":", 1)[1].strip()
    if tail.lower() in {"climb arrow", "left turn arc", "path segment"}:
        return ""
    return tail


def build_evidence_packet(item, sample_id, prelabel, original_path, boxed_path):
    width = int(prelabel.get("image_dimensions", {}).get("width") or 0)
    height = int(prelabel.get("image_dimensions", {}).get("height") or 0)
    regions = []
    elements = []
    for idx, region in enumerate(prelabel.get("regions", []), start=1):
        public = region_to_public(region, sample_id, idx)
        if region.get("region_type") in COARSE_TYPES:
            regions.append(public)
        else:
            elements.append(public)

    packet = {
        "sample_id": sample_id,
        "image_size": {"width": width, "height": height},
        "input_images": {
            "original_chart": str(original_path).replace("\\", "/"),
        },
        "review_artifacts": {
            "boxed_preview_human_review_only": str(boxed_path).replace("\\", "/"),
            "warning": "Do not use boxed preview for OCR, LLM, VLM, or scoring. It may occlude chart information.",
        },
        "regions": regions,
        "elements": elements,
        "input_policy": {
            "method": "B3",
            "allowed_for_prompt": True,
            "use_original_chart_only": True,
            "boxed_preview_for_human_review_only": True,
            "no_true_chart_id_in_prompt": True,
            "no_cifp_proxy_answers": True,
            "no_candidate_mappings": True,
            "source": "auto_prelabel_visual_candidates_stripped",
        },
    }
    assert_no_mapping_fields(packet, f"{sample_id}.packet")
    return packet


def build_b1_image_input(sample_id, original_path):
    return {
        "sample_id": sample_id,
        "method": "B1",
        "image_path": str(original_path).replace("\\", "/"),
        "ocr_scope": "full_page",
        "prompt_policy": {
            "do_not_include_true_chart_id": True,
            "do_not_include_cifp_proxy_answers": True,
            "runner_fills_chart_metadata_after_llm": True,
        },
        "ocr_required_outputs": ["text", "confidence", "bbox"],
    }


def build_b1_prompt_placeholder(sample_id):
    return {
        "sample_id": sample_id,
        "method": "B1",
        "status": "awaiting_ocr",
        "input_evidence": {
            "ocr_scope": "full_page",
            "ocr_text": "",
            "ocr_tokens": [],
            "note": "Fill this file after OCR. Do not add chart_id, airport, procedure metadata, or CIFP target values.",
        },
    }


def build_b3_prompt_input(packet):
    return {
        "sample_id": packet["sample_id"],
        "method": "B3",
        "input_evidence": {
            "regions": packet["regions"],
            "elements": packet["elements"],
        },
        "prompt_policy": packet["input_policy"],
    }


def main():
    for path in [ORIGINAL_DIR, BOXED_DIR, B1_INPUT_DIR, B3_EVIDENCE_DIR, B1_PROMPT_DIR, B3_PROMPT_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    manifest = read_json(MANIFEST)
    sample_map = []
    public_index = []
    b1_manifest = []
    b3_manifest = []

    for idx, item in enumerate(manifest, start=1):
        sample_id = f"sample_{idx:04d}"
        chart_id = item["chart_id"]
        original_path = copy_original(item, sample_id)
        prelabel_path = PRELABEL_DIR / f"{chart_id}.json"
        prelabel = read_json(prelabel_path)
        boxed_path = BOXED_DIR / f"{sample_id}__{chart_id}__boxed.png"
        draw_boxed_image(prelabel, original_path, boxed_path)

        evidence = build_evidence_packet(item, sample_id, prelabel, original_path, boxed_path)
        evidence_path = B3_EVIDENCE_DIR / f"{sample_id}__b3_evidence.json"
        write_json(evidence_path, evidence)
        b3_prompt_path = B3_PROMPT_DIR / f"{sample_id}__prompt_input.json"
        write_json(b3_prompt_path, build_b3_prompt_input(evidence))

        b1_input = build_b1_image_input(sample_id, original_path)
        b1_input_path = B1_INPUT_DIR / f"{sample_id}__b1_image_input.json"
        write_json(b1_input_path, b1_input)
        b1_prompt_path = B1_PROMPT_DIR / f"{sample_id}__prompt_input_after_ocr.placeholder.json"
        write_json(b1_prompt_path, build_b1_prompt_placeholder(sample_id))

        sample_map.append({
            "sample_id": sample_id,
            "chart_id": chart_id,
            "airport": item["airport"],
            "approach_ident": item["proc_ident"],
            "chart_name": item["chart_name"],
            "source_image_path": item["image_path"],
            "b1_original_chart": str(original_path).replace("\\", "/"),
            "boxed_preview_human_review_only": str(boxed_path).replace("\\", "/"),
            "b3_evidence_packet": str(evidence_path).replace("\\", "/"),
            "canonical_proxy_gt_file": str((EXP / "targets/canonical_proxy_gt_10" / f"{chart_id}.json")).replace("\\", "/"),
        })
        public_index.append({
            "sample_id": sample_id,
            "method_scope": ["B1", "B3"],
            "b1_image_input": str(b1_input_path).replace("\\", "/"),
            "b3_evidence_packet": str(evidence_path).replace("\\", "/"),
            "boxed_preview_human_review_only": str(boxed_path).replace("\\", "/"),
        })
        b1_manifest.append(b1_input)
        b3_manifest.append({
            "sample_id": sample_id,
            "method": "B3",
            "evidence_packet": str(evidence_path).replace("\\", "/"),
            "prompt_input": str(b3_prompt_path).replace("\\", "/"),
        })

    write_json(PRIVATE_SAMPLE_MAP, sample_map)
    write_json(PUBLIC_SAMPLE_INDEX, public_index)
    write_json(B1_MANIFEST, b1_manifest)
    write_json(B3_MANIFEST, b3_manifest)
    print(f"Prepared {len(manifest)} B1/B3 pilot samples in {PILOT_DIR}")
    print(f"Original charts: {ORIGINAL_DIR}")
    print(f"Boxed previews for human review only: {BOXED_DIR}")


if __name__ == "__main__":
    main()
