"""
Validate normalized bbox objects used by B1/B3 artifacts.

Issue #7 requires bbox values to use 0-1 normalized coordinates:
  {x_center, y_center, width, height}

This validator scans JSON files recursively and reports any bbox object with
missing keys, nonnumeric values, or values outside [0, 1].
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


BBOX_KEYS = {"x_center", "y_center", "width", "height"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_bboxes(value: Any, path: str = "") -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    if isinstance(value, dict):
        if "bbox" in value:
            bbox_path = f"{path}.bbox" if path else "bbox"
            bbox = value["bbox"]
            if isinstance(bbox, dict):
                found.append((bbox_path, bbox))
            elif bbox is not None:
                found.append((bbox_path, {"__invalid_bbox__": bbox}))
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            found.extend(find_bboxes(child, child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            found.extend(find_bboxes(child, f"{path}[{idx}]"))
    return found


def validate_bbox(bbox: dict[str, Any]) -> list[str]:
    errors = []
    if set(bbox.keys()) != BBOX_KEYS:
        errors.append(f"bbox keys must be exactly {sorted(BBOX_KEYS)}, got {sorted(bbox.keys())}")
        return errors
    for key in sorted(BBOX_KEYS):
        value = bbox[key]
        if not isinstance(value, int | float):
            errors.append(f"{key} is not numeric: {value!r}")
            continue
        if value < 0 or value > 1:
            errors.append(f"{key}={value!r} outside [0, 1]")
    return errors


def iter_json_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for item in paths:
        path = Path(item)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.json")))
        else:
            files.append(path)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate normalized bbox objects in JSON artifacts.")
    parser.add_argument("paths", nargs="+", help="JSON files or directories")
    args = parser.parse_args()

    failed = False
    total = 0
    for path in iter_json_files(args.paths):
        data = read_json(path)
        file_errors = []
        for bbox_path, bbox in find_bboxes(data):
            total += 1
            errors = validate_bbox(bbox)
            file_errors.extend(f"{bbox_path}: {error}" for error in errors)
        if file_errors:
            failed = True
            print(f"FAIL {path}")
            for error in file_errors:
                print(f"  - {error}")
        else:
            print(f"PASS {path}")
    print(f"Checked {total} bbox objects.")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
