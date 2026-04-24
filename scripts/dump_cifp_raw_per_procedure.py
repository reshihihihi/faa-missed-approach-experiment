"""
Emit per-procedure raw CIFP records as evidence / provenance.

For every procedure in pairs_100.json (or sample_manifest_100.json), writes all
primary PF records (all transitions, not just missed-approach slice) plus a column
ruler header to data/v2604_100/cifp_raw_per_procedure/{chart_id}.txt.

These files are committed as part of the dataset release per A7 spec
(Issue #15 refinement comment).
"""

from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DATASET = REPO / "data" / "v2604_100"
CIFP_FILE = DATASET / "cifp" / "FAACIFP18"
PAIRS_FILE = DATASET / "pairs_100.json"
OUT_DIR = DATASET / "cifp_raw_per_procedure"


def passes_filter(line: str) -> bool:
    if len(line) < 132:
        return False
    if line[0:5] not in ("SUSAP", "SUSAH"):
        return False
    if line[12] != "F":
        return False
    return True  # keep both primary and continuation for full evidence


def ruler_lines() -> list[str]:
    rows = []
    rows.append("# Column ruler (1-indexed, 132 chars):")
    rows.append("#" + "".join(
        [str((i + 1) // 100) if (i + 1) % 10 == 0 else " " for i in range(131)]
    ))
    rows.append("#" + "".join(
        [str(((i + 1) // 10) % 10) if (i + 1) % 10 == 0 else " " for i in range(131)]
    ))
    rows.append("#" + "".join([str((i + 1) % 10) for i in range(131)]))
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pairs = json.loads(PAIRS_FILE.read_text(encoding="utf-8"))
    wanted = {(p["cifp"]["airport"], p["cifp"]["proc_ident"]): p["id"] for p in pairs}

    buckets: dict[str, list[str]] = {cid: [] for cid in wanted.values()}

    with CIFP_FILE.open("r", encoding="latin-1") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip("\r")
            if not passes_filter(line):
                continue
            apt = line[6:10].strip()
            ident = line[13:19].rstrip()
            key = (apt, ident)
            if key not in wanted:
                continue
            buckets[wanted[key]].append(line)

    header_lines = ruler_lines()
    written = 0
    for chart_id, records in buckets.items():
        records.sort()  # deterministic order by full record bytes
        header = [
            f"# Raw ARINC 424.18 PF records for {chart_id}",
            f"# Source: FAACIFP18 cycle 2604 (effective 16 APR 2026)",
            f"# Includes all transitions for this procedure (primary + continuation records)",
            f"# Total records: {len(records)}",
            "#",
        ] + header_lines + [""]
        content = "\n".join(header + records) + "\n"
        (OUT_DIR / f"{chart_id}.txt").write_text(content, encoding="utf-8")
        written += 1

    print(f"Wrote {written} per-procedure raw CIFP slices to {OUT_DIR.relative_to(REPO)}/")


if __name__ == "__main__":
    main()
