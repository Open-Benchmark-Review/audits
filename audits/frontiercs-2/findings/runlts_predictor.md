# runlts_predictor

**Verdict:** `runlts_predictor: FN / near-IMPOSSIBLE (CONFIRMED by the task's own measurement; no observed run affected, since every candidate is worse than the reference on average)`. Affected runs: none flip. 0/17 pass, and every candidate's continuous score (30.89-31.27) is below the reference's (31.488).

## How it's scored
- CBP2025 simulator, one deterministic run of the candidate predictor per trace over all 105 training traces, measured on the latter-half "50 Perc" epochs.
- Pass needs, on **every one of the 105 traces**, strictly lower BrMisPKI **and** strictly lower CycWpPKI than the exact original RUNLTS, compared by exact integer cross-products with no tolerance. Storage must be ≤ 1,572,864 bits (`judge/beat_spec.json` metrics and `beats_reference`).
- The edit surface is only the register-value (sR) component, inside 9 byte-regions of `my_cond_branch_predictor.cc` (`repo/README.md:7,21-23`).
- The reference counts are fixed recorded values (`repo/README.md:116`).

## P(reference passes vs itself)
0. The simulator is deterministic, so a self-comparison ties and equality fails.

## Findings
1. **FN / near-IMPOSSIBLE, CONFIRMED.**
   - The agent-visible statement says (`agent-base/frontier/task/repo/README.md:91`): "shifting by one call the shared random stream that the retained predictor uses moves a single trace's mispredictions by about 1% (standard deviation; up to 6.6%) and its wrong-path cycles by about 0.7%".
   - So per-trace outcomes behave chaotically at about 1% sd, while the editable sR component is a small statistical-corrector input. The no-sR naive baseline scores 31.35 on dev (`README.md:86`), against the reference's 31.49 on the final suite (different suites, but the whole component is a sub-percent effect on the score).
   - Winning all 105 traces × 2 metrics strictly needs a per-trace gain well above the 1% chaotic sd everywhere, including on traces where sR has no leverage, and the reference itself almost certainly doesn't achieve that against a no-sR baseline.
   - Estimate: a uniform true 2% gain with difference-sd ≈ 1.4% gives P(win one trace, one metric) ≈ Φ(1.43) ≈ 0.92, so 0.92^105 ≈ 2e-4 per metric, before the 6.6% tails.
   - Observed best: sol 53/105 BrMis and 54/105 CycWP. That is roughly coin-flip level, consistent with near-equal predictors on a chaotic metric.
   - Even a genuinely better sR design would almost surely FAIL.
2. **Edit-surface strictness, MINOR, disclosed.** There is a heavy lexical and semantic audit: forbidden words such as `new`, `read`, `write`, `vector` and `function`, no raw arrays, and the edits must fit within 9 byte-ranges (`README.md:7-23,98-113`). There are only 1,974 bits of storage slack over the reference (1,572,864 vs 1,570,890). These are all stated to the agent, so this is not a hidden requirement. Every completed run produced a valid, scored submission.
3. **Consistency.** reference_score is identical (31.4878) in all 16 completed runs, which is consistent with fixed recorded reference counts. k27 hit the 5 h agent deadline with no submission.

## Passing runs checked
None passed. I did not inspect FAIL patches for hacks. The scores cluster tightly below the reference, so there are no anomalous jumps.

## Notes
- The beat_spec comments say "No full105 measurement or sR ablation was established" at authoring time. Nobody showed the bar is reachable, and no reachability witness exists, unlike the other tasks.
- For the leaderboard this task is a fixed 0 for every model. It can't change rankings, but it deflates absolute pass rates.
