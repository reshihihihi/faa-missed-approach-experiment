# Data Deprecation Path

Tracks artifacts being retired as the proxy-ground-truth pipeline is rebuilt
inside this repository (Issue #4).

## `data/v2604_100/pairs_100.json` — deprecated as of 2026-04-24

Produced by an external private pipeline (README references `e:/hangtu3`, not in
this repo). Contains only 7 fields per leg: `seq_no`, `rt_type`, `wpt_ident`,
`trans_ident`, `altitude1/2 + alt_desc`, `speed_lmt`. Drops
`turn_direction`, `RNP`, `waypoint_desc`, `mag_course`, `theta/rho`,
`distance` / `hold_time`, `vertical_angle`, `center_fix`, `rec_navaid`, etc.

**Replaced by**:

- `scripts/extract_missed_approach.py` reads raw `FAACIFP18`
- produces extraction-schema `data/v2604_100/missed_approach_extracted/{chart_id}.json`
  (full ARINC 424 field set per leg, plus `raw_record` for evidence)
- `scripts/project_canonical.py` projects to canonical-schema
  `data/v2604_100/missed_approach/{chart_id}.json`

Will be removed once Issues #4 and #14 stabilize. Kept as read-only reference
until then.

## `data/v2604_100/sample_manifest_100.json` — deprecated

Contains stale `ma_leg_count` / `holding_required` / `ma_holding_legs` fields
that are wrong for **35 of 100 procedures** (those whose MAP fix is not
`RW*` — typical of LOC, VOR, and RNAV circle-to-land approaches). Root cause:
old `scripts/run_O.py`'s `get_main_transition()` heuristic.

**Replaced by**: `data/v2604_100/sample_manifest.json` — built by
`scripts/build_manifest.py` per A7 release convention (chart_id primary key,
paths, SHA256, `shares_pdf_with` for multi-procedure PDFs, schema pointer).

Will be removed after v1.0 dataset release.

## `results/v2604_100/O/*.json` — flat-schema baseline output

Produced by the old `scripts/run_O.py` which outputs a 9-field flat JSON:
`{climb_altitude, waypoints, turn_direction, holding_required, holding_fix,
initial_track, turn_trigger, holding_details, raw_instruction}`. Returns
`"unknown"` for the 35 procedures hit by the `RW*` heuristic bug.

**Replaced by**: `data/v2604_100/missed_approach/*.json` (canonical leg-level).

`run_O.py` itself will be rewritten in a future PR to output canonical JSON.
For now the column-slicing bugs in the CIFP reader have been fixed
(`proc_ident` cols 14-19 instead of 14-18; `rt_type` cols 48-49 instead of
48-50); the flat schema is unchanged to avoid breaking legacy consumers.

## Not deprecated (still in use)

- `data/v2604_100/candidate_pool.json` — procedure selection record, kept for
  traceability
- `data/v2604_100/selection_100.json` — stratified quota log, kept for
  traceability
