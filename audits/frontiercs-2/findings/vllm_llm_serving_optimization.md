# vllm_llm_serving_optimization

**Verdict:** `vllm_llm_serving_optimization: FN (CONFIRMED; near-IMPOSSIBLE for the reference itself)`. 0/17 PASS. Affected runs: all of them, most consequentially **astra** (19/20 comparisons passed) and **gemini** (17/20, paired timing 4/4).

## How it's scored
- Candidate-only evaluation against **fixed** targets from 3 calibration captures of the reference and vanilla vLLM (Oct 18, run_01M568…, run_01M56NV8…, run_01M571D9…; `verifier/fixed-targets.json`).
- 4 groups (swe/public N=48, swe/hidden 48, bfcl/public 155, bfcl/hidden 155) × 5 comparisons = 20, all must clear (`judge/beat_spec.json`):
  - paired geomean log-ratio > 0 against the **per-instance minimum** of the 3 reference captures;
  - p90, p95 and p99 strictly below the **minimum** of the 3 captures' group percentiles;
  - correct count ≥ median(ref) − max(1, ceil(0.05N)).
- Margin 0 (`fixed_targets_policy`, `judge/beat_spec.json`). The rule is disclosed in the agent README (`agent-base/frontier/task/README.md:130-139`), so it isn't hidden, but it is structurally biased.

## P(reference passes vs itself) ≈ 0 (computed from `verifier/fixed-targets.json`, script `tools/vllm_ft.py`)
- Per-case latency variation across captures: median CV 19% (swe/public), 16.5% (swe/hidden), 4.1% (BFCL).
- A reference capture's paired log-ratio against the min-of-3 target, i.e. the speedup the reference itself would need:
  - swe/public: ×1.23, ×1.48, ×1.69
  - swe/hidden: ×1.62, ×1.24, ×1.34
  - bfcl/public: ×1.12, ×1.10, ×1.02
  - bfcl/hidden: ×1.05, ×1.12, ×1.06
- Leave-one-out (capture j vs min of the other two, which is easier than min-of-3): only 2 of 12 capture×group cells clear paired timing.
- Tail targets: a fresh exchangeable capture beats the min of 3 with probability about 1/4 per percentile. There are 12 tail checks.
- So an unmodified reference re-run fails almost surely. A candidate must beat the reference by more than its own run-to-run noise: roughly 1.2–1.7x on SWE, plus winning 12 tail draws.

## Findings
1. **Best-of-3 fixed targets with zero margin (FN, CONFIRMED).** Computed above. The noise is also larger than the effect being measured. The reference's own speedup over vanilla per capture is 1.45–1.57x on swe/public, 0.89–1.13x on swe/hidden (one capture slower than vanilla), and 0.99–1.06x on both BFCL groups. On BFCL the reference is not distinguishable from vanilla, yet candidates must beat its per-case best-of-3.
2. **Fixed targets measured on other hosts and runs (FN amplifier, CONFIRMED as design).** The captures are Oct 18 runs, and candidates were evaluated Oct 19–26 on separately provisioned Modal H100s (4-GPU verifier). Any host or day drift lands entirely on the candidate side. No in-run reference re-measurement exists (`reference_score` is null in every run record).
3. **Did runs get valid evaluations? Yes, 15/17.** Every COMPLETED run has correctness 4/4 and full timing coverage (`analysis/per_task/vllm_llm_serving_optimization.json`). The two non-evaluations: k3 `agent_exited_without_final_submission` (agent side) and ds1017 `agent_job_failed` (BackoffLimitExceeded, exit 2, possibly infra). Infra failures do **not** dominate. The 0/17 comes from the timing rule.
4. **Near-misses that a fair rule could flip (UNCONFIRMED whether they'd pass).** astra cleared all 12 tail checks and 3/4 paired-timing groups, failing only one paired log-ratio. gemini cleared 4/4 paired timing (beating per-case best-of-3 on every group, which is strong evidence of a real speedup) but missed 1 p90, 2 p95 and 2 p99. Against a fresh, in-run reference (an exchangeable draw), both would have a substantial chance of passing.
5. **Budget plausibility.** 5 h agent time, 25 train calls on tiny public subsets (SWE N=5, BFCL N=8) and an 1800-min final. Evaluation is feasible: 15 finals completed. Train feedback on N=5/8 can't reveal tail behaviour at N=48/155.

## Passing runs checked
- None passed. Patches weren't inspected for hacks because no run passed. Correctness was 4/4 everywhere.

## Notes
- The reference is Continuum's KV-cache-TTL job-aware scheduler (arXiv 2511.02230), an appropriate paper method. Not CONSTRUCT.
