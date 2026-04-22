"""
Build a refreshed FAA-aligned 100-sample dataset for the missed-approach experiment.

Outputs are written under:
  e:/experiment/data/v2604_100/

This script:
1. downloads the official FAA CIFP zip and d-TPP metafile for cycle 2604
2. parses candidate IAP procedures from CIFP
3. matches procedures to official chart PDFs
4. selects a stratified 100-sample set
5. downloads selected PDFs, renders chart images, and writes pairs/manifest JSON
"""

from __future__ import annotations

import json
import random
import shutil
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

import requests

ROOT = Path("e:/experiment")
DATASET_DIR = ROOT / "data" / "v2604_100"
SOURCES_DIR = DATASET_DIR / "sources"
CIFP_DIR = DATASET_DIR / "cifp"
PDF_DIR = DATASET_DIR / "pdfs"
IMAGE_DIR = DATASET_DIR / "charts"

CYCLE = "2604"
CIFP_ZIP_URL = "https://aeronav.faa.gov/Upload_313-d/cifp/CIFP_260416.zip"
DTPP_XML_URL = f"https://aeronav.faa.gov/d-tpp/{CYCLE}/xml_data/d-TPP_Metafile.xml"
DTPP_PDF_BASE = f"https://aeronav.faa.gov/d-tpp/{CYCLE}/"

PAIRS_PATH = DATASET_DIR / "pairs_100.json"
MANIFEST_PATH = DATASET_DIR / "sample_manifest_100.json"
SELECTION_PATH = DATASET_DIR / "selection_100.json"
POOL_PATH = DATASET_DIR / "candidate_pool.json"

RANDOM_SEED = 2604
PER_AIRPORT_CAP = 2

# Quotas chosen to preserve some procedure-type diversity while still respecting
# the real distribution of no-hold charts in the current cycle.
QUOTAS = [
    ("RNAV", False, 25),
    ("LOC", False, 13),
    ("ILS", False, 2),
    ("RNAV", True, 35),
    ("LOC", True, 12),
    ("ILS", True, 13),
]

sys.path.insert(0, str(Path("e:/hangtu3")))
from data.cifp_parser import CIFPParser  # noqa: E402
from data.pdf_processor import extract_plan_view_region, extract_text_layer, render_pdf_image  # noqa: E402
from data.precise_pairing import chart_name_matches, parse_proc_ident  # noqa: E402


def ensure_dirs() -> None:
    for path in [DATASET_DIR, SOURCES_DIR, CIFP_DIR, PDF_DIR, IMAGE_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest: Path) -> Path:
    if dest.exists():
        return dest

    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    return dest


def prepare_official_sources() -> tuple[Path, Path]:
    zip_path = download_file(CIFP_ZIP_URL, SOURCES_DIR / Path(CIFP_ZIP_URL).name)
    xml_path = download_file(DTPP_XML_URL, SOURCES_DIR / "d-TPP_Metafile.xml")

    cifp_candidates_before = set(CIFP_DIR.glob("*"))
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(CIFP_DIR)

    cifp_candidates = (
        list(CIFP_DIR.glob("CIFP"))
        + list(CIFP_DIR.glob("FAACIFP*"))
        + list(CIFP_DIR.glob("*.dat"))
        + list(CIFP_DIR.glob("CIFP*"))
    )
    if not cifp_candidates:
        raise FileNotFoundError("No CIFP data file found after extracting official zip.")

    cifp_file = max(cifp_candidates, key=lambda p: p.stat().st_size)
    canonical_cifp = CIFP_DIR / "FAACIFP18"
    if cifp_file != canonical_cifp:
        shutil.copy2(cifp_file, canonical_cifp)
        cifp_file = canonical_cifp

    return cifp_file, xml_path


def load_airport_charts(xml_path: Path) -> dict[str, list[tuple[str, str]]]:
    root = ET.parse(xml_path).getroot()
    airport_charts: dict[str, list[tuple[str, str]]] = {}
    for apt_node in root.iter("airport_name"):
        ident = (apt_node.get("icao_ident", "") or apt_node.get("apt_ident", "")).strip()
        if not ident:
            continue
        charts = []
        for record in apt_node.iter("record"):
            if record.findtext("chart_code", "") != "IAP":
                continue
            chart_name = record.findtext("chart_name", "").strip()
            pdf_name = record.findtext("pdf_name", "").strip()
            if chart_name and pdf_name:
                charts.append((chart_name, pdf_name))
        if charts:
            airport_charts[ident] = charts
    return airport_charts


def get_main_transition(legs: list[dict]) -> str | None:
    for leg in legs:
        if leg["wpt_ident"].strip().startswith("RW"):
            return leg["trans_ident"].strip()
    trans_ids = {leg["trans_ident"].strip() for leg in legs}
    for candidate in ("R", "I"):
        if candidate in trans_ids:
            return candidate
    return None


def get_ma_legs(legs: list[dict]) -> list[dict]:
    main_trans = get_main_transition(legs)
    if not main_trans:
        return []
    main_legs = [leg for leg in legs if leg["trans_ident"].strip() == main_trans]
    rw_idx = next(
        (i for i, leg in enumerate(main_legs) if leg["wpt_ident"].strip().startswith("RW")),
        None,
    )
    if rw_idx is None:
        return []
    return main_legs[rw_idx + 1 :]


def procedure_kind(proc_ident: str) -> str:
    prefix = proc_ident[0] if proc_ident else "?"
    if prefix == "I":
        return "ILS"
    if prefix == "L":
        return "LOC"
    if prefix == "R":
        return "RNAV"
    return prefix


def build_candidate_pool(cifp_file: Path, xml_path: Path) -> list[dict]:
    parser = CIFPParser(str(cifp_file))
    procedures = parser.parse(proc_types=["ILS", "RNAV", "RNP", "LOC"], max_procedures=1500, require_icao=True)
    airport_charts = load_airport_charts(xml_path)

    candidates: list[dict] = []
    for proc in procedures:
        proc_dict = proc.to_dict()
        parsed = parse_proc_ident(proc.proc_ident)
        best_score = 0.0
        best_chart_name = None
        best_pdf_name = None
        for chart_name, pdf_name in airport_charts.get(proc.airport_ident, []):
            score = chart_name_matches(chart_name, parsed)
            if score > best_score:
                best_score = score
                best_chart_name = chart_name
                best_pdf_name = pdf_name

        if best_score < 0.5 or not best_pdf_name:
            continue

        ma_legs = get_ma_legs(proc_dict["legs"])
        holding_required = any(leg["rt_type"].strip() in {"HM", "HF", "HA"} for leg in ma_legs)
        candidates.append(
            {
                "id": proc.id,
                "airport": proc.airport_ident,
                "proc_ident": proc.proc_ident,
                "kind": procedure_kind(proc.proc_ident),
                "holding_required": holding_required,
                "ma_leg_count": len(ma_legs),
                "chart_name": best_chart_name,
                "pdf_name": best_pdf_name,
                "pdf_url": DTPP_PDF_BASE + best_pdf_name,
                "procedure": proc_dict,
            }
        )

    POOL_PATH.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    return candidates


def choose_samples(candidates: list[dict]) -> list[dict]:
    rng = random.Random(RANDOM_SEED)
    pool = defaultdict(list)
    for item in candidates:
        key = (item["kind"], item["holding_required"])
        pool[key].append(item)

    for key in pool:
        rng.shuffle(pool[key])
        pool[key].sort(key=lambda x: (x["airport"], x["proc_ident"], x["id"]))
        rng.shuffle(pool[key])

    selected: list[dict] = []
    airport_counts: Counter[str] = Counter()
    used_pdf_names: set[str] = set()

    def pick_from_group(group: list[dict], count: int) -> list[dict]:
        chosen = []
        for item in group:
            if len(chosen) >= count:
                break
            if item["pdf_name"] in used_pdf_names:
                continue
            if airport_counts[item["airport"]] < PER_AIRPORT_CAP:
                chosen.append(item)
                airport_counts[item["airport"]] += 1
                used_pdf_names.add(item["pdf_name"])
        if len(chosen) < count:
            for item in group:
                if item in chosen:
                    continue
                if item["pdf_name"] in used_pdf_names:
                    continue
                if len(chosen) >= count:
                    break
                chosen.append(item)
                airport_counts[item["airport"]] += 1
                used_pdf_names.add(item["pdf_name"])
        return chosen

    for kind, holding_required, quota in QUOTAS:
        group = pool[(kind, holding_required)]
        if len(group) < quota:
            raise ValueError(f"Not enough candidates for {(kind, holding_required)}: need {quota}, have {len(group)}")
        chosen = pick_from_group(group, quota)
        selected.extend(chosen)

    if len(selected) < 100:
        remaining = []
        for group_items in pool.values():
            remaining.extend(group_items)
        for item in remaining:
            if len(selected) >= 100:
                break
            if item["pdf_name"] in used_pdf_names:
                continue
            if airport_counts[item["airport"]] >= PER_AIRPORT_CAP:
                continue
            selected.append(item)
            airport_counts[item["airport"]] += 1
            used_pdf_names.add(item["pdf_name"])

    if len(selected) < 100:
        remaining = []
        for group_items in pool.values():
            remaining.extend(group_items)
        for item in remaining:
            if len(selected) >= 100:
                break
            if item["pdf_name"] in used_pdf_names:
                continue
            selected.append(item)
            airport_counts[item["airport"]] += 1
            used_pdf_names.add(item["pdf_name"])

    if len(selected) != 100:
        raise ValueError(f"Expected 100 selected samples, got {len(selected)}")

    selected.sort(key=lambda x: (x["kind"], x["holding_required"], x["airport"], x["proc_ident"]))
    selection_summary = {
        "cycle": CYCLE,
        "seed": RANDOM_SEED,
        "per_airport_cap": PER_AIRPORT_CAP,
        "quotas": [{"kind": kind, "holding_required": holding, "count": count} for kind, holding, count in QUOTAS],
        "selected_counts": [
            {"kind": kind, "holding_required": holding, "count": count}
            for (kind, holding), count in sorted(Counter((x["kind"], x["holding_required"]) for x in selected).items())
        ],
        "airport_counts_top20": Counter(x["airport"] for x in selected).most_common(20),
        "selected_ids": [x["id"] for x in selected],
    }
    SELECTION_PATH.write_text(json.dumps(selection_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return selected


def download_selected_pdfs(samples: Iterable[dict]) -> None:
    for item in samples:
        pdf_path = PDF_DIR / item["pdf_name"]
        download_file(item["pdf_url"], pdf_path)


def build_pairs_and_manifest(samples: list[dict]) -> None:
    pairs = []
    manifest = []

    for item in samples:
        pdf_path = PDF_DIR / item["pdf_name"]
        image_path = Path(render_pdf_image(str(pdf_path), page_idx=0, dpi=150))
        if image_path.parent != IMAGE_DIR:
            IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            target_image_path = IMAGE_DIR / image_path.name
            if image_path != target_image_path:
                shutil.copy2(image_path, target_image_path)
                image_path = target_image_path

        blocks = extract_text_layer(str(pdf_path), page_idx=0)
        plan_blocks = extract_plan_view_region(blocks)
        proc = item["procedure"]
        ma_legs = get_ma_legs(proc["legs"])
        ma_holding_legs = [
            {"rt_type": leg["rt_type"].strip(), "wpt_ident": leg["wpt_ident"].strip()}
            for leg in ma_legs
            if leg["rt_type"].strip() in {"HM", "HF", "HA"}
        ]

        pairs.append(
            {
                "id": item["id"],
                "cifp": proc,
                "pdf_path": str(pdf_path),
                "image_path": str(image_path),
                "chart_name": item["chart_name"],
                "ocr": [{"text": b.text, "bbox_norm": list(b.bbox_norm)} for b in plan_blocks],
                "ocr_raw_count": len(blocks),
                "ocr_plan_count": len(plan_blocks),
            }
        )

        manifest.append(
            {
                "id": item["id"],
                "image": image_path.name,
                "airport": proc["airport"],
                "proc_ident": proc["proc_ident"],
                "chart_name": item["chart_name"],
                "holding_required": item["holding_required"],
                "total_legs": len(proc["legs"]),
                "ma_leg_count": len(ma_legs),
                "ma_holding_legs": ma_holding_legs,
            }
        )

    PAIRS_PATH.write_text(json.dumps(pairs, ensure_ascii=False, indent=2), encoding="utf-8")
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    cifp_file, xml_path = prepare_official_sources()
    print(f"Prepared official CIFP: {cifp_file}")
    print(f"Prepared official d-TPP metafile: {xml_path}")

    candidates = build_candidate_pool(cifp_file, xml_path)
    print(f"Candidate pool size: {len(candidates)}")
    print(f"Candidate distribution: {Counter((x['kind'], x['holding_required']) for x in candidates)}")

    selected = choose_samples(candidates)
    print(f"Selected {len(selected)} samples.")
    print(f"Selection distribution: {Counter((x['kind'], x['holding_required']) for x in selected)}")

    download_selected_pdfs(selected)
    build_pairs_and_manifest(selected)

    print(f"Pairs written to {PAIRS_PATH}")
    print(f"Manifest written to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
