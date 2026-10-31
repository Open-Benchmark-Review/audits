# representation_frechet_loss

**Verdict:** `representation_frechet_loss: FN (CONFIRMED); IMPOSSIBLE-adjacent / unqualified task (CONFIRMED); FP (not met, ~2%)`. Affected runs: all 17. The beat signal is dominated by training nondeterminism.

## How it's scored
- Final runs 3 workloads (`judge/judge_deps/workloads.json`: final-0 ema/128 updates, final-1 online/512, final-2 ema/512).
- Each workload post-trains pMF-B with FD-loss using the candidate's `FeatureQueue`, then evaluates FDr in 6 representation spaces on 4,096 held-out images.
- The candidate must be strictly lower than the reference on all 6 × 3 = 18 comparisons (`judge/evaluator.py:139-145`).
- Score = 100 / (1 + mean FDr6).

## P(reference passes vs itself)
**About 2% (range 1–6%); below the 10% FP threshold.**
- Seeds are fixed, yet the in-run reference score ranges 2.83–4.29 across 17 runs (stdev 0.42). That is reference FDr6 from 22.3 to 34.3, a CV of 12.9% on the 3-workload mean.
- Training is therefore nondeterministic despite fixed seeds.
- Model: each workload has a shared latent factor with correlation ρ across the 6 metrics. The observed within-run variance of per-metric pass counts (mean 0.33 over 17 runs) fits ρ ≈ 0.8. Monte Carlo at ρ=0.8 gives P(all 18) = 0.020; at ρ=0.95, 0.058; fully correlated, 0.12.
- Script: inline in this audit session; numbers reproducible from `analysis/per_task/representation_frechet_loss.json`.

## Findings
1. **Noise swamps any plausible improvement (FN, CONFIRMED by computation).**
   - Reference self-noise on the 3-workload mean is about 13% CV, and larger per workload.
   - Under the same model (σ_workload ≈ 0.22 in log FDr, difference σ ≈ 0.31), a genuine 5% FDr improvement passes with probability ≈ 3–4%. A 20% improvement passes about 15–20% of the time.
   - The design space is a population mean/covariance estimator (`judge/reference.patch`: snapshot, online accumulator and EMA). Correct implementations are numerically near-equivalent to the reference, so outcomes are mostly noise.
   - Run data fit a coin flip: opus scored 7.16 vs the reference's 3.61 (about 2x lower FDr6 on average) yet passed only 2/3 workloads on most metrics. terra scored 3.11 vs 4.03 (0–1/3).
2. **The task self-declares as unqualified (IMPOSSIBLE/validity, CONFIRMED).** The agent-visible README opens with:
   > "**Source revision awaiting runtime qualification.** ... The resulting verifier image and complete scientific workloads still require validation before this revision can be used as a solver benchmark."

   It also says "No admissible non-reference baseline has reached quality scoring" (README, Calibration status), `workloads.json` has `"status": "proposed_uncalibrated"`, and the beat_spec says "the author must calibrate noise", which was never done. No witness patch is known to clear the bar.
3. **Tight agent budget (MINOR, CONFIRMED).** `max_train_calls` = 3, each up to 7,200 s. Development has only 2 workloads, and feedback is aggregate means plus pass counts. With about 13% run-to-run noise, 3 calls give almost no usable signal.
4. **Reward-hack surfaces (checked, none found).**
   - The training spine is sha-locked (`evaluator.py:24`, `:110-112`), the queue runs in an isolated process, and validity guards apply (`evaluator.py:87-98`).
   - The reference queue is small and standard; reconstructing it would only tie in distribution.

## Passing runs checked
None passed.

Consistency: many non-accepted reruns on Oct 10 (other_runs) have verdict None or score 0. This suggests infrastructure churn on Oct 10 before the formal runs; the formal runs are all COMPLETED.

## Notes
- The gemini run made 0 train submissions and was still scored, which is fine.
- Reference-score drift across runs has no time trend (2.83 on Oct 14, 4.29 on Oct 25), so it reflects nondeterminism rather than a scorer change.
