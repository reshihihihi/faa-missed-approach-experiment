## Summary

Describe the change in 2-5 sentences.

## Affected Areas

- [ ] dataset materialization
- [ ] sample selection
- [ ] extraction path A or B
- [ ] extraction path C, D, or E
- [ ] baseline path O
- [ ] evaluation
- [ ] error analysis
- [ ] prompts
- [ ] docs only

## Reproducibility Impact

- [ ] no impact on the formal `v2604_100` split
- [ ] changes generated outputs but not the committed split
- [ ] changes the committed split or pairing data
- [ ] changes published metrics or reports

Explain the expected reproducibility impact:

## Validation

- [ ] `python scripts/smoke_test.py`
- [ ] `python scripts/build_dataset_100.py`
- [ ] path-level run script(s)
- [ ] `python evaluate.py`
- [ ] `python error_analysis.py`
- [ ] not run

List the exact commands you ran:

## Data And Results Changes

- [ ] changed files under `data/v2604_100/`
- [ ] changed files under `results/v2604_100/`
- [ ] changed prompt files under `prompts/`
- [ ] no committed data or result files changed

If data, prompts, metrics, or reports changed, explain why:

## Reviewer Notes

Call out anything risky, intentionally deferred, or especially important to verify.

## Codex

After repository-level Codex review is enabled, you can trigger review by:

`@codex review`

You can also narrow the request, for example:

`@codex review for reproducibility regressions`
