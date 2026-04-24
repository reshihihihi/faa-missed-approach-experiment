"""
Build the v2 sample manifest per A7 spec (Issue #15 refinement comment).

Reads:
- data/v2604_100/sample_manifest_100.json (legacy; for pdf_source_name + chart_name)
- data/v2604_100/missed_approach/*.json (canonical proxy GT)
- data/v2604_100/cifp_raw_per_procedure/*.txt (raw CIFP slices)
- local asset files for SHA256 (where present; null otherwise)

Writes:
- data/v2604_100/sample_manifest.json (new, canonical source of truth)

Notes:
- PDF SHA256 is null when PDF not materialized locally (charts/pdfs/ is gitignored).
- CIFP raw SHA256 is computed from the committed per-procedure slice file.
- extraction_script_version uses `git log -1 --pretty=%H -- <script>`; falls back to
  "unknown" if git unavailable.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DATASET = REPO / "data" / "v2604_100"
OLD_MANIFEST = DATASET / "sample_manifest_100.json"
OUT_FILE = DATASET / "sample_manifest.json"

CIFP_CYCLE = "2604"
CIFP_EFFECTIVE = "2026-04-16"
EXTRACTION_SCRIPT = "scripts/extract_missed_approach.py"
SCHEMA_FILE = "schemas/missed_approach_leg.schema.json"


def sha256_of_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def last_commit_sha(path_rel: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), "log", "-1", "--pretty=%H", "--", path_rel],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip() or "uncommitted"
    except Exception:
        return "unknown"


def pdf_name_from_image(image_name: str) -> str:
    stem = Path(image_name).stem
    if stem.endswith("_p0"):
        return f"{stem[:-3].upper()}.PDF"
    return f"{stem.upper()}.PDF"


def main() -> None:
    old = json.loads(OLD_MANIFEST.read_text(encoding="utf-8"))

    # Group samples by their source PDF to populate shares_pdf_with
    samples_by_pdf = defaultdict(list)
    for e in old:
        pdf_name = pdf_name_from_image(e["image"])
        samples_by_pdf[pdf_name].append(e["id"])

    samples = []
    for e in old:
        chart_id = e["id"]
        pdf_name = pdf_name_from_image(e["image"])
        pdf_url = f"https://aeronav.faa.gov/d-tpp/{CIFP_CYCLE}/{pdf_name}"
        shares = sorted(x for x in samples_by_pdf[pdf_name] if x != chart_id)

        samples.append({
            "chart_id": chart_id,
            "airport": e["airport"],
            "approach_ident": e["proc_ident"],
            "chart_name": e["chart_name"],
            "pdf_source_name": pdf_name,
            "pdf_url": pdf_url,
            "pdf_sha256": sha256_of_file(DATASET / "charts" / "pdfs" / pdf_name),
            "shares_pdf_with": shares,
            "cifp_raw_sha256": sha256_of_file(DATASET / "cifp_raw_per_procedure" / f"{chart_id}.txt"),
            "canonical_sha256": sha256_of_file(DATASET / "missed_approach" / f"{chart_id}.json"),
            "paths": {
                "missed_approach_gt": f"missed_approach/{chart_id}.json",
                "cifp_raw": f"cifp_raw_per_procedure/{chart_id}.txt",
                "chart_pdf_local": f"charts/pdfs/{pdf_name}",
                "chart_image_local": f"charts/images/{chart_id}.png",
            },
        })

    manifest = {
        "dataset": f"faa-missed-approach-v{CIFP_CYCLE}-{len(samples)}",
        "cifp_cycle": CIFP_CYCLE,
        "cifp_effective": CIFP_EFFECTIVE,
        "extraction_script_version": f"{EXTRACTION_SCRIPT}@{last_commit_sha(EXTRACTION_SCRIPT)}",
        "schema_version": "canonical_leg_v1",
        "schema_file": SCHEMA_FILE,
        "sample_count": len(samples),
        "samples": samples,
    }

    OUT_FILE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_FILE.relative_to(REPO)} with {len(samples)} samples.")


if __name__ == "__main__":
    main()
