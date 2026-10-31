# nano_world_model

**Verdict:** `nano_world_model: MINOR; FN (UNCONFIRMED)`. Affected runs: none confirmed. Possibly the 15 runs that beat the reference's continuous score but failed the per-clip conjunction (glm, astra, sol, ds, k3, muse, k27, wonder, qwen, gemini, step, ds1017, gemini-agy, terra, k31).

## How it's scored
- `judge/evaluator.py:363-376`: on each of 6 graded clips (3 predicted frames each), the candidate needs PSNR `>`, SSIM `>` and LPIPS `<` the reference. That is 18 strict comparisons with no tolerance.
- The continuous score uses only the 2 original clips (`_score`, `evaluator.py:280-292`).
- The reference is measured in the same verification via the non-isolated path (`_reference_rows`, `evaluator.py:295-311`).

## P(reference passes vs itself)
**About 0.**
- The reference score is 79.07574 or 79.07583 across all 17 runs (stdev 4e-5), so the pipeline is nearly deterministic.
- A reference copy either ties, failing the strict `>`, or differs at noise level. At noise level it would need 18 coin flips to land the same way, about 4e-6.

## Findings
1. **Strict 18-way per-clip conjunction with no noise calibration (FN, UNCONFIRMED).**
   - 15/17 completed formal runs beat the reference's continuous score (by +0.02 to +2.3), but only 1/17 passed. Most failures are 1–3 LPIPS clips; e.g. ds1017 passed 6/6 LPIPS and 6/6 PSNR but 5/6 SSIM.
   - The beat_spec says no tolerance exists because "genuine GPU evaluation and tolerance calibration were deferred" and "Not GPU-validated: no A10G run of the four- and six-clip suites exists" (`judge/beat_spec.json` comments).
   - Per-clip outcomes depend on the sampled trajectory realisation. A sampler that is better on average can lose a clip by chance.
   - No per-clip rows are available, so the probability cannot be computed. The rule itself is clearly stated to the agent (README, "Feedback and grading").
2. **The scorer changed before the formal runs (consistency note, CONFIRMED).**
   - Beat spec v3 (2-clip to 6-clip suites) and the 2026-10-11 timeout refresh are documented in `beat_spec.json` comments and `evaluator.py:31-35`.
   - Five earlier non-accepted runs (other_runs: glm Oct 6, astra/sol/ds/k3 Oct 10) PASSED under v2. All 17 formal runs are Oct 11 or later, so they were scored consistently.
3. **Extremely tight agent budget (MINOR, CONFIRMED).**
   - `max_train_calls` = 3 (`policy.json` quota).
   - The agent's own A10G is limited to 1,800 GPU-seconds (README, Resources). One development verification has been recorded at 147–646 s.
   - The pass/fail signal is very coarse: 4 dev clips, aggregate counts only. 9/17 runs used all 3 calls.
4. **Statement inconsistency (MINOR, CONFIRMED).** README Validity says "Each native program invocation has a 1,650-second timeout", while Resources and the evaluator say 4,950 s (`evaluator.py:35`).
5. **Reward-hack surfaces (checked, none found).**
   - `_policy_check` (`evaluator.py:60-118`) forbids file and env access and `judge_data` tokens.
   - The sampler runs isolated and receives only the context latent and actions.
   - The reference sampler is not otherwise recoverable, and reproducing it would only tie.

## Passing runs checked
- **opus (PASS): legit.**
  - `SAMPLER_OPTIONS` (opus.patch:25-36): `num_samples=16`, `combine="mean"`, 50 steps, `refine_level=100`, `refine_steps=10`.
  - So it averages a 16-sample ensemble (a posterior-mean estimate) and then runs a short refinement pass.
  - This is a known PSNR/SSIM-favouring technique that uses about 3–4x the reference's 250 NFEs. No compute or latency metric is gated, and the README sets no compute bound, so it is legitimate. It is also an easier lever than "a better DFoT schedule" (a construct observation, not egregious).

## Notes
- Several failing runs also use ensembles (astra, ds, sol, glm, k3; grep `num_samples`).
- No infrastructure failures: all 17 runs COMPLETED.
