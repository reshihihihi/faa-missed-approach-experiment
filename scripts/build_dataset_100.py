"""
Materialize the public assets required by the formal 100-sample experiment.

This script is intentionally deterministic. It does not resample the dataset;
instead it recreates the raw public inputs needed to rerun the committed
100-sample experiment:

1. download the official FAA CIFP zip for cycle 2604
2. extract `FAACIFP18` under `data/v2604_100/cifp/`
3. download the official d-TPP metafile for traceability
4. download the 100 chart PDFs referenced by `sample_manifest_100.json`
5. render page 1 of each chart PDF to the expected PNG filename

The committed `sample_manifest_100.json` and `pairs_100.json` remain the source
of truth for the fixed experiment split and structured CIFP pairing metadata.
"""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

import fitz
import requests

from repo_paths import DATASET_NAME, get_dataset_dir


CYCLE = "2604"
DATASET_DIR = get_dataset_dir(DATASET_NAME)
SOURCES_DIR = DATASET_DIR / "sources"
CIFP_DIR = DATASET_DIR / "cifp"
PDF_DIR = DATASET_DIR / "pdfs"
CHARTS_DIR = DATASET_DIR / "charts"
MANIFEST_PATH = DATASET_DIR / "sample_manifest_100.json"
PAIRS_PATH = DATASET_DIR / "pairs_100.json"
REPORT_PATH = DATASET_DIR / "materialization_report.json"

CIFP_ZIP_URL = "https://aeronav.faa.gov/Upload_313-d/cifp/CIFP_260416.zip"
DTPP_XML_URL = f"https://aeronav.faa.gov/d-tpp/{CYCLE}/xml_data/d-TPP_Metafile.xml"
DTPP_PDF_BASE = f"https://aeronav.faa.gov/d-tpp/{CYCLE}/"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and render the public inputs for the formal 100-sample dataset.")
    parser.add_argument("--skip-downloads", action="store_true", help="Do not download missing PDFs or source archives.")
    parser.add_argument("--skip-render", action="store_true", help="Do not render PNG charts from PDFs.")
    parser.add_argument("--force-render", action="store_true", help="Re-render PNG charts even if they already exist.")
    return parser.parse_args()


def ensure_dirs() -> None:
    for path in [DATASET_DIR, SOURCES_DIR, CIFP_DIR, PDF_DIR, CHARTS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def load_manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Missing manifest: {MANIFEST_PATH}. The committed manifest is required for deterministic reproduction."
        )
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if len(manifest) != 100:
        raise ValueError(f"Expected 100 manifest entries, got {len(manifest)}")
    return manifest


def verify_pairs_file() -> None:
    if not PAIRS_PATH.exists():
        raise FileNotFoundError(
            f"Missing pairing metadata: {PAIRS_PATH}. This repository expects the committed pairs file to stay in Git."
        )


def download_file(url: str, dest: Path, skip_downloads: bool = False) -> Path:
    if dest.exists():
        return dest
    if skip_downloads:
        raise FileNotFoundError(f"Required file is missing and downloads are disabled: {dest}")

    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with open(dest, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    return dest


def prepare_official_sources(skip_downloads: bool = False) -> Path:
    zip_path = download_file(CIFP_ZIP_URL, SOURCES_DIR / Path(CIFP_ZIP_URL).name, skip_downloads=skip_downloads)
    download_file(DTPP_XML_URL, SOURCES_DIR / "d-TPP_Metafile.xml", skip_downloads=skip_downloads)

    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(CIFP_DIR)

    cifp_candidates = (
        list(CIFP_DIR.glob("CIFP"))
        + list(CIFP_DIR.glob("FAACIFP*"))
        + list(CIFP_DIR.glob("*.dat"))
        + list(CIFP_DIR.glob("CIFP*"))
    )
    if not cifp_candidates:
        raise FileNotFoundError("No CIFP data file found after extracting the FAA archive.")

    cifp_file = max(cifp_candidates, key=lambda path: path.stat().st_size)
    canonical = CIFP_DIR / "FAACIFP18"
    if cifp_file != canonical:
        shutil.copy2(cifp_file, canonical)
    return canonical


def pdf_name_from_image_name(image_name: str) -> str:
    stem = Path(image_name).stem
    if not stem.endswith("_p0"):
        raise ValueError(f"Unexpected chart image naming convention: {image_name}")
    return f"{stem[:-3].upper()}.PDF"


def chart_image_path(entry: dict) -> Path:
    return CHARTS_DIR / entry["image"]


def pdf_path_for_entry(entry: dict) -> Path:
    return PDF_DIR / pdf_name_from_image_name(entry["image"])


def download_selected_pdfs(manifest: list[dict], skip_downloads: bool = False) -> list[Path]:
    downloaded = []
    for entry in manifest:
        pdf_name = pdf_name_from_image_name(entry["image"])
        pdf_path = PDF_DIR / pdf_name
        pdf_url = DTPP_PDF_BASE + pdf_name
        download_file(pdf_url, pdf_path, skip_downloads=skip_downloads)
        downloaded.append(pdf_path)
    return downloaded


def render_first_page(pdf_path: Path, image_path: Path, force_render: bool = False) -> None:
    if image_path.exists() and not force_render:
        return

    with fitz.open(pdf_path) as document:
        if document.page_count == 0:
            raise ValueError(f"PDF has no pages: {pdf_path}")
        page = document.load_page(0)
        pix = page.get_pixmap(dpi=150, alpha=False)
        pix.save(image_path)


def render_charts(manifest: list[dict], force_render: bool = False) -> None:
    for entry in manifest:
        render_first_page(pdf_path_for_entry(entry), chart_image_path(entry), force_render=force_render)


def write_report(manifest: list[dict], cifp_file: Path) -> None:
    report = {
        "dataset": DATASET_NAME,
        "cycle": CYCLE,
        "manifest_entries": len(manifest),
        "pdf_count": len(list(PDF_DIR.glob("*.PDF"))),
        "chart_count": len(list(CHARTS_DIR.glob("*.png"))),
        "cifp_file": str(cifp_file.relative_to(DATASET_DIR)),
        "notes": [
            "This script reconstructs the public raw inputs for the committed 100-sample experiment.",
            "It does not rerun candidate-pool generation or reselection.",
            "The committed sample manifest and pairs metadata define the formal split.",
        ],
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    ensure_dirs()
    verify_pairs_file()
    manifest = load_manifest()

    print(f"Preparing dataset assets for {DATASET_NAME}...")
    cifp_file = prepare_official_sources(skip_downloads=args.skip_downloads)
    print(f"Prepared CIFP file: {cifp_file}")

    if not args.skip_downloads:
        download_selected_pdfs(manifest, skip_downloads=False)
        print(f"PDFs ready under: {PDF_DIR}")
    else:
        download_selected_pdfs(manifest, skip_downloads=True)
        print("Verified that all required PDFs are already present.")

    if not args.skip_render:
        render_charts(manifest, force_render=args.force_render)
        print(f"Rendered PNG charts under: {CHARTS_DIR}")
    else:
        print("Skipping chart rendering as requested.")

    write_report(manifest, cifp_file)
    print(f"Wrote materialization report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
