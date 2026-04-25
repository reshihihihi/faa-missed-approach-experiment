"""
Build a static review viewer for comparing B1 and B3 box results.

The viewer is a human-review artifact only. It copies original unboxed chart
images into the annotation platform public folder and writes a manifest with
OCR/annotation boxes. It does not create method inputs for LLM/scoring.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.getenv("FAA_B1_B3_ROOT", REPO_ROOT)).expanduser().resolve()
PUBLIC_ROOT = Path(os.getenv("FAA_B1_B3_REVIEW_PUBLIC", ROOT / "review_only/b1b3_review_public")).expanduser().resolve()
IMAGES_DIR = PUBLIC_ROOT / "images"
DATA_DIR = PUBLIC_ROOT / "data"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clean_text(text: Any, max_len: int = 80) -> str:
    if text is None:
        return ""
    value = str(text).replace("\n", " ").strip()
    return value[:max_len]


def token_to_box(token: dict[str, Any], *, kind: str, color_group: str) -> dict[str, Any] | None:
    bbox = token.get("bbox")
    if not bbox:
        return None
    return {
        "id": token.get("token_id", ""),
        "kind": kind,
        "color_group": color_group,
        "bbox": bbox,
        "label": clean_text(token.get("text")),
        "text": clean_text(token.get("text"), 200),
        "confidence": token.get("confidence"),
        "source_region": token.get("source_region", ""),
        "source_region_type": token.get("source_region_type", ""),
    }


def region_to_box(item: dict[str, Any], *, kind: str, color_group: str) -> dict[str, Any] | None:
    bbox = item.get("bbox")
    if not bbox:
        return None
    label = clean_text(item.get("ocr_text") or item.get("text") or item.get("visual_label") or item.get("source_region_type"))
    return {
        "id": item.get("region_id", ""),
        "kind": kind,
        "color_group": color_group,
        "bbox": bbox,
        "label": label,
        "text": clean_text(item.get("ocr_text") or item.get("text"), 200),
        "confidence": item.get("confidence"),
        "candidate_type": item.get("candidate_type", ""),
        "source_region": item.get("source_region", ""),
        "source_region_type": item.get("source_region_type", ""),
    }


def load_b1_boxes(sample_id: str) -> list[dict[str, Any]]:
    path = ROOT / "outputs/B1_ocr_llm/prompt_inputs" / f"{sample_id}__prompt_input.json"
    data = read_json(path)
    boxes = []
    for token in data.get("input_evidence", {}).get("ocr_tokens", []):
        box = token_to_box(token, kind="B1_FULL_PAGE_OCR_TOKEN", color_group="b1_ocr")
        if box:
            boxes.append(box)
    return boxes


def load_b3_boxes(sample_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    path = ROOT / "outputs/B3_region_ocr_llm/prompt_inputs" / f"{sample_id}__prompt_input.json"
    data = read_json(path)
    evidence = data.get("input_evidence", {})
    region_boxes: list[dict[str, Any]] = []
    element_boxes: list[dict[str, Any]] = []
    ocr_boxes: list[dict[str, Any]] = []

    for item in evidence.get("regions", []):
        box = region_to_box(item, kind="B3_ANNOTATION_REGION", color_group="b3_region")
        if box:
            region_boxes.append(box)
        for token in item.get("ocr_tokens", []):
            token_box = token_to_box(token, kind="B3_REGION_OCR_TOKEN", color_group="b3_ocr")
            if token_box:
                ocr_boxes.append(token_box)

    for item in evidence.get("elements", []):
        box = region_to_box(item, kind="B3_ANNOTATION_ELEMENT", color_group="b3_element")
        if box:
            element_boxes.append(box)
        for token in item.get("ocr_tokens", []):
            token_box = token_to_box(token, kind="B3_ELEMENT_OCR_TOKEN", color_group="b3_ocr")
            if token_box:
                ocr_boxes.append(token_box)

    return region_boxes, element_boxes, ocr_boxes


def build_manifest() -> dict[str, Any]:
    samples = read_json(ROOT / "data/pilot10/sample_map_private.json")
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_samples = []
    for sample in samples:
        sample_id = sample["sample_id"]
        image_src = Path(sample["b1_original_chart"])
        image_name = f"{sample_id}__original{image_src.suffix.lower()}"
        image_dst = IMAGES_DIR / image_name
        shutil.copy2(image_src, image_dst)

        b1_boxes = load_b1_boxes(sample_id)
        b3_regions, b3_elements, b3_ocr = load_b3_boxes(sample_id)

        output_samples.append(
            {
                "sample_id": sample_id,
                "chart_id": sample.get("chart_id", ""),
                "chart_name": sample.get("chart_name", ""),
                "image": f"images/{image_name}",
                "counts": {
                    "b1_ocr_boxes": len(b1_boxes),
                    "b3_region_boxes": len(b3_regions),
                    "b3_element_boxes": len(b3_elements),
                    "b3_ocr_boxes": len(b3_ocr),
                },
                "b1": {
                    "description": "B1 full-page OCR token boxes. B1 does not use dataset annotation boxes.",
                    "boxes": b1_boxes,
                },
                "b3": {
                    "description": "B3 uses prior annotation/prelabel regions and elements, then OCRs those regions from the original chart.",
                    "region_boxes": b3_regions,
                    "element_boxes": b3_elements,
                    "ocr_boxes": b3_ocr,
                },
            }
        )

    return {
        "title": "B1/B3 Box Review",
        "warning": "Human-review artifact only. Do not use this viewer or boxed screenshots as OCR/LLM/scoring input.",
        "samples": output_samples,
    }


def main() -> None:
    manifest = build_manifest()
    write_json(DATA_DIR / "manifest.json", manifest)
    print(f"Wrote viewer manifest: {DATA_DIR / 'manifest.json'}")
    print(f"Copied {len(manifest['samples'])} images to: {IMAGES_DIR}")


if __name__ == "__main__":
    main()
