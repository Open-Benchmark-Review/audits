# bounded_evm_path_prediction: OK (MINOR notes). Affected runs: none

## How it's scored
- The replay is deterministic.
- For each of 6 final workloads (complex/normal x epochs 200/400/600):
  - the sum of printed branch-accuracy hundredths must exceed the reference by at least 1 tick;
  - the sum of transaction-path hundredths must be >= the reference;
  - the observation count must be equal (`judge/beat_spec.json`).
- The continuous score uses epoch 400 only.

## P(reference passes vs itself)
- The replay is deterministic (the in-run reference score is 80.44 in all 17 runs, sd 0) and ties fail. P = 0.

## Findings
1. **No noise-driven FN.** The metric is deterministic. Many runs score above the reference (81.1–81.2) yet fail one category-epoch, which is the stated rule (no averaging across epochs).
2. **MINOR: side channel through `observationCount`.**
   - The surrounding sweeper deletes branches whose `observationCount/lifecycle < threshold` (`repo/core/vm/var_table.go:314-318`).
   - The reference caps `observationCount` at 10 (`judge/reference.patch`), so recurring branches are eventually swept.
   - Several patches inflate the field to exempt branches from sweeping: opus `retained = 1<<40` (`opus.patch`), gemini-agy 100000, sol 65536, gemini 100.
   - The README says the field is "read directly" by surrounding code but not what it controls. This is a disclosed interface lever that changes predictor retention, not the measurement. Legit.
3. **MINOR:** `uncertain` falls back to the pre-execution value (`core/vm/pre_instructions.go:613-619`), so abstaining is not free. No abstention hack is possible.
4. The removed predictor is not present in the agent image. I checked `agent-base/frontier/task/repo` for identifiers from `judge/upstream_predictor.go` (`OBSERVER_MODE_THRESHOLD`, `uncertainNum`) and found nothing.

## Passing runs checked (4)
- k3: perceptron plus confidence EMA. Legit.
- opus: per-branch "stable over >= 2 distinct blocks" predictor. It uses package-level globals to infer block boundaries from the query/observe call pattern and inflates `observationCount`. Legit (package-local state is allowed).
- gemini: taken/notTaken counts with an `observationCount` tweak. Legit.
- gemini-agy: first-direction-until-mixed predictor. Legit.

## Notes
- Beat spec v3 (2026-10-07) added the 600-block, 3-epoch grading after v2 was cleared 8/8. All formal runs (10-10 onward) are on v3. The 10-06 glm run in other_runs predates it.
- The verifier memory was raised to 8 GiB for the 600-block replay (beat_spec comments).
