# ckks_composable_noise

**Verdict:** `ckks_composable_noise: MINOR (CONFIRMED: stale docs, public judge readme says bands absent); timing-gate FN risk for marginal speedups (UNCONFIRMED, ds1017)`
Affected runs: none confirmed. ds1017 is a possible noise-decided FAIL (28/29 time cells) on a genuinely marginal (≈5–20%) speedup.

## How it's scored
- `judge/beat_spec.json` / `judge/formal_scoring.py:53-64`: 29 LogN12 workloads, 3 interleaved candidate/reference pairs each. Per workload:
  - Accuracy, two cells: (mean |AVG discrepancy|)_cand − (…)_ref ≤ tau_j, inclusive (`formal_scoring.py:59`).
  - Time: candidate estimator clock < reference in **each** of the 3 pairs (`:41-45`), 87 strict pairs in total.
- Bands are frozen in `judge/judge/formal_calibration.json` (q = 5.684; `calibration.py:42` takes the 19th of 19 maxima, i.e. the max). They come from 19 reference-vs-reference single-invocation pairs: tau_j = q · SD_j, e.g. 0.036–0.86 bits. All 17 runs used the same calibration digest (d740f700…).

## P(reference passes vs itself)
- Accuracy: ≈1. The bands are a ~95% simultaneous non-inferiority band for one invocation, applied to 3-invocation means.
- Time: ≈ 0.5^87 ≈ 0 for identical code.
- Overall ≈0, so the time gate is what forces real improvement.

## Findings

### 1. Thresholds (CONFIRMED, by design)
- Accuracy is non-inferiority with generous bands. A candidate can be up to 0.2–0.86 bits *less* accurate per cell and still pass.
- "Beats the paper's estimator" therefore means "about as accurate, strictly faster". The README states this plainly (`agent-base/frontier/task/repo/README.md:7,94`), and the contribution summary in `judge/metadata.json` is "Complete, cheaper precision estimator". Not a defect, but PASS means *speedup at parity accuracy*, not better accuracy.

### 2. Timing gate on marginal speedups (UNCONFIRMED FN)
- From the train evidence (`traces/ckks_composable_noise/*/verifications/*/evidence.tar` → `metrics.json` `operator_evidence`):
  - ds1017 is only 5–20% faster than the reference per workload (e.g. mul_relin_rescale 73.3 vs 77.1 ms; poly_eval 969 vs 1092 ms).
  - astra is 1.4–3× faster.
  - Reference times differ by 2–9% across machines/runs.
- ds1017's final failed exactly 1 of 87 strict time pairs (`estimator_seconds` 28/29) at accuracy parity (score 95.79 vs 95.78). This is a plausible noise loss at a ~5% margin.
- Passing runs have mean estimator time 0.04–0.10 s (astra 0.33 s) against a reference of about 0.4 s, so their margins are large. No passing verdict looks noise-dependent.

### 3. MINOR (CONFIRMED): stale public statement
`judge/readme` ("This release has no frozen accuracy bands… cannot pass") and the `beat_spec.json` tolerance text ("No band exists for this release") contradict `judge/judge/release.json` (`mode: formal`, `formal_calibration` set) and the 11 passes. Documentation only; no effect on verdicts.

### 4. Consistency
- other_runs from 2026-10-12T04:06 scored on a different scale (~73) under an earlier release. All formal runs (Oct 12 16:21 → Oct 26) share one calibration digest, and the reference score is stable at 95.56–96.66 (sd 0.27).
- ds: infrastructure failure (`agent_job_failed`, empty patch).

## Passing runs checked (11 PASS: astra, sol, glm, k3, opus, wonder, qwen, gemini, gemini-agy, terra, k31)
- All 11 patches were grepped for file I/O, env/argv introspection, `exec`, `unsafe`, workload-name detection, hard-coded numeric tables, slot subsampling and extrapolation. **None found.**
- `time.Now()` appears only as an RNG seed.
- The edits are allocation/arith optimizations of the bignum estimator in `element.go`, `operations.go`, `noise.go` and `linear_transformation.go`; some add double-double (`dd.go`).
- stats.go and the experiment mains are a fixed surface, byte-checked by the judge.
- Verdict: **legit** (spot-check depth: grep plus a read of astra's diff head).

## Notes
I didn't run the Go evaluator. The final-verification evidence tarballs are not included in the HF traces (train ones are).
