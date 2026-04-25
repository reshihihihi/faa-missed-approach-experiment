"""
Run the previous experiment OCR version for B1/B3 pilot inputs.

Previous OCR stack, inherited from the earlier run_A.py and run_B.py flow:
    conda env: ocr_exp
    PaddleOCR(use_textline_orientation=True, lang="en")

This script only prepares OCR evidence. It does not call an LLM.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

try:
    import paddle
    import paddleocr as paddleocr_module
    from paddleocr import PaddleOCR
except ImportError as exc:
    print(
        "Missing dependency: paddleocr/paddle. Run this with the previous OCR env:\n"
        "  conda run -n ocr_exp python scripts/b1_b3_pilot/run_paddleocr_previous.py",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.getenv("FAA_B1_B3_ROOT", REPO_ROOT)).expanduser().resolve()
MODEL_NAME = "PaddleOCR"
MODEL_INIT = {"use_textline_orientation": True, "lang": "en"}


def as_jsonable(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def norm_path(path: str | Path) -> str:
    return str(Path(path).as_posix())


def bbox_norm_to_abs(bbox: dict[str, float], width: int, height: int, padding: int = 0) -> tuple[int, int, int, int]:
    cx = float(bbox["x_center"]) * width
    cy = float(bbox["y_center"]) * height
    bw = float(bbox["width"]) * width
    bh = float(bbox["height"]) * height
    x1 = max(0, int(round(cx - bw / 2 - padding)))
    y1 = max(0, int(round(cy - bh / 2 - padding)))
    x2 = min(width, int(round(cx + bw / 2 + padding)))
    y2 = min(height, int(round(cy + bh / 2 + padding)))
    if x2 <= x1:
        x2 = min(width, x1 + 1)
    if y2 <= y1:
        y2 = min(height, y1 + 1)
    return x1, y1, x2, y2


def bbox_from_poly(poly: Any) -> tuple[float, float, float, float] | None:
    data = as_jsonable(poly)
    if data is None:
        return None
    if isinstance(data, list) and len(data) == 4 and all(isinstance(v, (int, float)) for v in data):
        x1, y1, x2, y2 = [float(v) for v in data]
        return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
    points: list[tuple[float, float]] = []
    if isinstance(data, list):
        for point in data:
            if isinstance(point, list) and len(point) >= 2:
                try:
                    points.append((float(point[0]), float(point[1])))
                except (TypeError, ValueError):
                    continue
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def normalized_bbox(
    local_bbox: tuple[float, float, float, float] | None,
    page_width: int,
    page_height: int,
    offset_x: int = 0,
    offset_y: int = 0,
) -> tuple[dict[str, float] | None, dict[str, int] | None]:
    if local_bbox is None:
        return None, None
    x1, y1, x2, y2 = local_bbox
    ax1 = max(0.0, min(float(page_width), x1 + offset_x))
    ay1 = max(0.0, min(float(page_height), y1 + offset_y))
    ax2 = max(0.0, min(float(page_width), x2 + offset_x))
    ay2 = max(0.0, min(float(page_height), y2 + offset_y))
    if ax2 < ax1:
        ax1, ax2 = ax2, ax1
    if ay2 < ay1:
        ay1, ay2 = ay2, ay1
    abs_bbox = {
        "x1": int(round(ax1)),
        "y1": int(round(ay1)),
        "x2": int(round(ax2)),
        "y2": int(round(ay2)),
    }
    norm = {
        "x_center": round(((ax1 + ax2) / 2) / page_width, 6),
        "y_center": round(((ay1 + ay2) / 2) / page_height, 6),
        "width": round((ax2 - ax1) / page_width, 6),
        "height": round((ay2 - ay1) / page_height, 6),
    }
    return norm, abs_bbox


def get_page_value(page: Any, key: str, default: Any = None) -> Any:
    if hasattr(page, "get"):
        return page.get(key, default)
    if hasattr(page, key):
        return getattr(page, key)
    return default


def extract_ocr_tokens(
    result: Any,
    *,
    token_prefix: str,
    source_region: str,
    source_region_type: str,
    page_width: int,
    page_height: int,
    offset_x: int = 0,
    offset_y: int = 0,
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    tokens: list[dict[str, Any]] = []
    raw_pages: list[dict[str, Any]] = []
    if not result:
        return tokens, "", raw_pages

    for page_index, page in enumerate(result):
        if page is None:
            continue
        rec_texts = list(get_page_value(page, "rec_texts", []) or [])
        rec_scores = list(get_page_value(page, "rec_scores", []) or [])
        rec_boxes = as_jsonable(get_page_value(page, "rec_boxes", []))
        rec_polys = as_jsonable(get_page_value(page, "rec_polys", []))
        if not rec_polys:
            rec_polys = as_jsonable(get_page_value(page, "dt_polys", []))

        raw_pages.append(
            {
                "page_index": page_index,
                "rec_texts": as_jsonable(rec_texts),
                "rec_scores": as_jsonable(rec_scores),
                "rec_boxes": rec_boxes,
                "rec_polys": rec_polys,
            }
        )

        for idx, text in enumerate(rec_texts):
            if text is None or str(text).strip() == "":
                continue
            score = rec_scores[idx] if idx < len(rec_scores) else None
            local_bbox = None
            if isinstance(rec_boxes, list) and idx < len(rec_boxes):
                local_bbox = bbox_from_poly(rec_boxes[idx])
            if local_bbox is None and isinstance(rec_polys, list) and idx < len(rec_polys):
                local_bbox = bbox_from_poly(rec_polys[idx])

            bbox, abs_bbox = normalized_bbox(local_bbox, page_width, page_height, offset_x, offset_y)
            token = {
                "token_id": f"{token_prefix}__ocr_{len(tokens) + 1:04d}",
                "text": str(text),
                "confidence": round(float(score), 6) if score is not None else None,
                "bbox": bbox,
                "bbox_abs": abs_bbox,
                "source_region": source_region,
                "source_region_type": source_region_type,
                "ocr_model": f"{MODEL_NAME} {getattr(paddleocr_module, '__version__', 'unknown')}",
                "ocr_init": MODEL_INIT,
                "page_width": page_width,
                "page_height": page_height,
            }
            tokens.append(token)

    text = "\n".join(token["text"] for token in tokens)
    return tokens, text, raw_pages


def run_ocr_image(
    ocr: PaddleOCR,
    image_path: Path,
    *,
    token_prefix: str,
    source_region: str,
    source_region_type: str,
    page_width: int,
    page_height: int,
    offset_x: int = 0,
    offset_y: int = 0,
) -> dict[str, Any]:
    result = ocr.predict(str(image_path))
    tokens, text, raw_pages = extract_ocr_tokens(
        result,
        token_prefix=token_prefix,
        source_region=source_region,
        source_region_type=source_region_type,
        page_width=page_width,
        page_height=page_height,
        offset_x=offset_x,
        offset_y=offset_y,
    )
    return {
        "ocr_text": text,
        "ocr_tokens": tokens,
        "raw_pages": raw_pages,
    }


def load_private_samples(root: Path, sample_id: str | None) -> list[dict[str, Any]]:
    samples = read_json(root / "data/pilot10/sample_map_private.json")
    if sample_id:
        samples = [sample for sample in samples if sample["sample_id"] == sample_id]
        if not samples:
            raise SystemExit(f"Unknown sample_id: {sample_id}")
    return samples


def build_b1_prompt(sample_id: str, ocr_text: str, tokens: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "method": "B1",
        "status": "ocr_completed",
        "input_evidence": {
            "ocr_scope": "full_page",
            "ocr_text": ocr_text,
            "ocr_tokens": tokens,
            "note": (
                "Generated by previous OCR stack. No chart_id, airport, procedure metadata, "
                "or CIFP target values are included."
            ),
        },
    }


def run_b1(root: Path, ocr: PaddleOCR, samples: list[dict[str, Any]], force: bool) -> list[dict[str, Any]]:
    output_root = root / "outputs/B1_ocr_llm"
    raw_dir = output_root / "ocr_raw"
    text_dir = output_root / "ocr_text"
    prompt_dir = output_root / "prompt_inputs"
    data_prompt_dir = root / "data/pilot10/prompt_inputs_b1_after_ocr"
    report: list[dict[str, Any]] = []

    for sample in samples:
        sample_id = sample["sample_id"]
        image_path = Path(sample["b1_original_chart"])
        if not image_path.exists():
            raise FileNotFoundError(image_path)
        with Image.open(image_path) as image:
            width, height = image.size

        prompt_path = prompt_dir / f"{sample_id}__prompt_input.json"
        if prompt_path.exists() and not force:
            report.append({"sample_id": sample_id, "method": "B1", "status": "skipped_existing"})
            continue

        print(f"[B1] OCR full page: {sample_id} -> {image_path.name}")
        ocr_result = run_ocr_image(
            ocr,
            image_path,
            token_prefix=f"{sample_id}__full_page",
            source_region="full_page",
            source_region_type="FULL_PAGE",
            page_width=width,
            page_height=height,
        )

        raw = {
            "sample_id": sample_id,
            "method": "B1",
            "image_path": norm_path(image_path),
            "image_size": {"width": width, "height": height},
            "ocr_model": f"{MODEL_NAME} {getattr(paddleocr_module, '__version__', 'unknown')}",
            "paddle_version": getattr(paddle, "__version__", "unknown"),
            "ocr_init": MODEL_INIT,
            "ocr_text": ocr_result["ocr_text"],
            "ocr_tokens": ocr_result["ocr_tokens"],
            "raw_pages": ocr_result["raw_pages"],
        }
        prompt_input = build_b1_prompt(sample_id, ocr_result["ocr_text"], ocr_result["ocr_tokens"])

        write_json(raw_dir / f"{sample_id}__ocr_raw.json", raw)
        text_dir.mkdir(parents=True, exist_ok=True)
        (text_dir / f"{sample_id}__ocr.txt").write_text(ocr_result["ocr_text"], encoding="utf-8")
        write_json(prompt_path, prompt_input)
        write_json(data_prompt_dir / f"{sample_id}__prompt_input.json", prompt_input)

        report.append(
            {
                "sample_id": sample_id,
                "method": "B1",
                "status": "ok",
                "token_count": len(ocr_result["ocr_tokens"]),
                "text_chars": len(ocr_result["ocr_text"]),
            }
        )

    return report


def crop_region(original: Image.Image, bbox: dict[str, float], padding: int) -> tuple[Image.Image, tuple[int, int, int, int]]:
    width, height = original.size
    x1, y1, x2, y2 = bbox_norm_to_abs(bbox, width, height, padding)
    return original.crop((x1, y1, x2, y2)), (x1, y1, x2, y2)


def ocr_b3_items(
    root: Path,
    ocr: PaddleOCR,
    packet: dict[str, Any],
    *,
    sample_id: str,
    original_image_path: Path,
    crop_dir: Path,
    padding: int,
    item_key: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    updated_items: list[dict[str, Any]] = []
    raw_items: list[dict[str, Any]] = []
    with Image.open(original_image_path) as original:
        original = original.convert("RGB")
        width, height = original.size
        for item in packet.get(item_key, []):
            region_id = item["region_id"]
            source_region_type = item.get("source_region_type", item.get("candidate_type", "UNKNOWN"))
            crop_image, (x1, y1, x2, y2) = crop_region(original, item["bbox"], padding)
            crop_path = crop_dir / f"{region_id}.png"
            crop_path.parent.mkdir(parents=True, exist_ok=True)
            crop_image.save(crop_path)

            print(f"[B3] OCR {item_key}: {sample_id} {region_id}")
            ocr_result = run_ocr_image(
                ocr,
                crop_path,
                token_prefix=region_id,
                source_region=region_id,
                source_region_type=source_region_type,
                page_width=width,
                page_height=height,
                offset_x=x1,
                offset_y=y1,
            )

            updated = dict(item)
            updated["ocr_text"] = ocr_result["ocr_text"]
            updated["ocr_tokens"] = ocr_result["ocr_tokens"]
            updated["ocr_crop"] = {
                "path": norm_path(crop_path.relative_to(root)),
                "bbox_abs": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                "padding_px": padding,
            }
            updated_items.append(updated)
            raw_items.append(
                {
                    "region_id": region_id,
                    "item_key": item_key,
                    "source_region_type": source_region_type,
                    "crop_path": norm_path(crop_path),
                    "crop_bbox_abs": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "ocr_text": ocr_result["ocr_text"],
                    "ocr_tokens": ocr_result["ocr_tokens"],
                    "raw_pages": ocr_result["raw_pages"],
                }
            )
    return updated_items, raw_items


def run_b3(root: Path, ocr: PaddleOCR, samples: list[dict[str, Any]], force: bool, padding: int) -> list[dict[str, Any]]:
    output_root = root / "outputs/B3_region_ocr_llm"
    raw_dir = output_root / "ocr_raw"
    prompt_dir = output_root / "prompt_inputs"
    crop_dir = output_root / "crops"
    data_prompt_dir = root / "data/pilot10/prompt_inputs_b3_after_ocr"
    report: list[dict[str, Any]] = []

    for sample in samples:
        sample_id = sample["sample_id"]
        packet_path = Path(sample["b3_evidence_packet"])
        packet = read_json(packet_path)
        original_image_path = Path(packet["input_images"]["original_chart"])
        if not original_image_path.exists():
            raise FileNotFoundError(original_image_path)

        prompt_path = prompt_dir / f"{sample_id}__prompt_input.json"
        if prompt_path.exists() and not force:
            report.append({"sample_id": sample_id, "method": "B3", "status": "skipped_existing"})
            continue

        with Image.open(original_image_path) as image:
            width, height = image.size

        print(f"[B3] OCR evidence regions: {sample_id}")
        updated_regions, raw_regions = ocr_b3_items(
            root,
            ocr,
            packet,
            sample_id=sample_id,
            original_image_path=original_image_path,
            crop_dir=crop_dir / sample_id,
            padding=padding,
            item_key="regions",
        )
        updated_elements, raw_elements = ocr_b3_items(
            root,
            ocr,
            packet,
            sample_id=sample_id,
            original_image_path=original_image_path,
            crop_dir=crop_dir / sample_id,
            padding=padding,
            item_key="elements",
        )

        prompt_input = {
            "sample_id": sample_id,
            "method": "B3",
            "status": "ocr_completed",
            "input_evidence": {
                "regions": updated_regions,
                "elements": updated_elements,
                "note": (
                    "Region-aware evidence generated from the original unboxed chart only. "
                    "Review-only boxed previews are not used."
                ),
            },
            "prompt_policy": packet.get("input_policy")
            or packet.get("prompt_policy")
            or {
                "method": "B3",
                "use_original_chart_only": True,
                "boxed_preview_for_human_review_only": True,
                "no_true_chart_id_in_prompt": True,
                "no_cifp_proxy_answers": True,
            },
        }
        raw = {
            "sample_id": sample_id,
            "method": "B3",
            "image_path": norm_path(original_image_path),
            "image_size": {"width": width, "height": height},
            "ocr_model": f"{MODEL_NAME} {getattr(paddleocr_module, '__version__', 'unknown')}",
            "paddle_version": getattr(paddle, "__version__", "unknown"),
            "ocr_init": MODEL_INIT,
            "crop_padding_px": padding,
            "regions": raw_regions,
            "elements": raw_elements,
        }

        write_json(raw_dir / f"{sample_id}__region_ocr_raw.json", raw)
        write_json(prompt_path, prompt_input)
        write_json(data_prompt_dir / f"{sample_id}__prompt_input.json", prompt_input)

        region_token_count = sum(len(item.get("ocr_tokens", [])) for item in updated_regions)
        element_token_count = sum(len(item.get("ocr_tokens", [])) for item in updated_elements)
        report.append(
            {
                "sample_id": sample_id,
                "method": "B3",
                "status": "ok",
                "region_count": len(updated_regions),
                "element_count": len(updated_elements),
                "region_token_count": region_token_count,
                "element_token_count": element_token_count,
            }
        )

    return report


def write_run_manifest(root: Path, report: list[dict[str, Any]]) -> None:
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": norm_path(Path(__file__)),
        "ocr_environment": {
            "recommended_conda_env": "ocr_exp",
            "paddleocr_version": getattr(paddleocr_module, "__version__", "unknown"),
            "paddle_version": getattr(paddle, "__version__", "unknown"),
            "ocr_init": MODEL_INIT,
            "inherited_from": [
                "E:/experiment/scripts/run_A.py",
                "E:/experiment/scripts/run_B.py",
            ],
        },
        "report": report,
    }
    write_json(root / "outputs/ocr_run_manifest.json", manifest)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run previous PaddleOCR setup for B1/B3 pilot inputs.")
    parser.add_argument("--root", default=str(ROOT), help="B1-B3 root directory.")
    parser.add_argument("--method", choices=["B1", "B3", "all"], default="all")
    parser.add_argument("--sample-id", default=None, help="Optional opaque sample id, e.g. sample_0001.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing OCR prompt outputs.")
    parser.add_argument("--crop-padding", type=int, default=2, help="Padding in pixels for B3 region crops.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    samples = load_private_samples(root, args.sample_id)

    print(
        "Using previous OCR stack: "
        f"PaddleOCR {getattr(paddleocr_module, '__version__', 'unknown')}, "
        f"paddle {getattr(paddle, '__version__', 'unknown')}, init={MODEL_INIT}"
    )
    ocr = PaddleOCR(**MODEL_INIT)

    report: list[dict[str, Any]] = []
    if args.method in {"B1", "all"}:
        report.extend(run_b1(root, ocr, samples, args.force))
    if args.method in {"B3", "all"}:
        report.extend(run_b3(root, ocr, samples, args.force, args.crop_padding))
    write_run_manifest(root, report)
    print(f"Finished OCR preparation. Report: {root / 'outputs/ocr_run_manifest.json'}")


if __name__ == "__main__":
    main()
