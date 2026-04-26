# paper-v2 configuration namespace

This directory stores frozen configuration manifests for paper-v2 runs.

Configuration files in this directory should be treated as part of the experiment freeze. If a model version, prompt file, parser policy, or rerun rule changes after evaluation begins, create a new run ID and update the relevant manifest rather than overwriting previous outputs.

## Planned files

- `model_config_manifest.json` — model/provider/version/temperature/top_p/max_tokens/OCR engine details.
- `prompt_manifest.json` — prompt path, prompt hash, allowed inputs, forbidden inputs, and prompt version.
- `parser_repair_policy.md` — fixed parser repair rules for malformed model outputs.
- `d_sft_training_config.json` — D-SFT training configuration, if D-SFT is included.

## Related issues

- PV2-03: #36
- PV2-13: #46
- PV2-14: #47
