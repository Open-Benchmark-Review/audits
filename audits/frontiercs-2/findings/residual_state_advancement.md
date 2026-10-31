residual_state_advancement: OK, MINOR (CONFIRMED: score scale; UNCONFIRMED: agent-environment OOM fragility, unscreened Python file I/O). Affected runs: none flip on the judge side. k3, qwen, gemini and ds1017 scored 0 after agent containers were killed (exit 137).

## How it's scored
- 8 workloads (4 real Favorita fact slices of 1.0–2.1M rows × 2 profiles). Four repetitions, each one fresh reference process and one fresh candidate process, alternating R,C,R,C (judge/evaluator.py:63-70).
- Per workload, all of:
  - candidate median fit time < reference median
  - candidate median `_update_error` time (which includes a trusted full read of the residual column) < reference median
  - RMSE within 1e-3 of the materialized-join oracle on every repetition
- Conjunction over all 8 (beat_spec.json "beats_reference").
- Continuous score: L = log10(B/T) against the fixed per-leaf baseline B, score = 100·L/(2+L) (beat_spec.json comments).

## Why the reference score is 0.26–0.87 (the "weird scale")
- The reference changes only `_update_error`: one `UPDATE … CASE` instead of per-leaf updates (judge/reference.patch). Residual update is only 3–21% of a fit (authors' own measurement in beat_spec.json comments).
- So the reference is just 1.2–4% faster than the baseline over the whole fit. That gives L = 0.005–0.018 and a score of 0.26–0.87. The spread is the reference/baseline timing noise (about ±1.5%).
- Candidates score 3–33 because the editable files (app.py, cjt.py, aggregator.py, joingraph.py) also allow speeding up tree growth: they are 1.16x–10x faster than the baseline overall.
- PASS compares fit and update medians directly, so the scale does not affect verdicts. MINOR: the continuous score mostly rewards non-update optimizations rather than the paper's contribution.

## P(reference passes vs itself)
Small. The authors measured a byte-different copy of the reference clearing 9 and 8 of 16 timing cells, never all 16 (beat_spec.json comments). Under independence that is about 0.5^16 ≈ 2e-5. Correlated drift could make it larger, but it stays well under 10%.

## Findings
1. **Passes are real improvements (CONFIRMED, train evidence).** Last-call ratios of candidate update time to reference update time per workload: glm 0.65–0.93, k31 0.43–0.89 (two workloads at ~1.1–1.3 in some calls), muse 0.42–0.77, sol 0.45–0.86. Worst-workload fit ratios were 0.42–0.74. k27 is the marginal one: worst-workload fit ratio 0.944–1.017 across its train calls; final speedup over the reference was 1.114 overall. It passed with update ratios of 0.45–0.95, so its elapsed-time win is real but small and partly noise-dependent.
2. **Failures are genuine (CONFIRMED).** step's update ratios were 0.92–1.65 (it shifted work into the update), so its 4/8 failure is earned. sol failed update on 1/8 workloads in final, although its train ratios were at most 0.86. That one is plausibly a noise or data-slice effect (UNCONFIRMED).
3. **Agent-environment fragility (UNCONFIRMED as a benchmark defect).** 4/17 runs died at 8–12 minutes with exit 137 and 0 train submissions (summaries: "OOMKilled", "workspace volume limit exceeded"). k3's and qwen's traces show them building local judge-mimicking harnesses: pandas materialized-join oracles on the 2M-row dev slices that ship in the agent image (repo/data/favorita/sales-dev-*.parquet).
   - The statement says the reference itself peaks at about 7.5 GB, inside a 16 GiB container with a 4 GiB workspace that is also TMPDIR/spill space (agent-base/Dockerfile ENV TMPDIR=/workspace).
   - Honest local reproduction is therefore easy to OOM, and a crash records 0 with no fallback.
   - This is mostly agent judgment, but it removes about 24% of runs from contention.
4. **Possible surface (UNCONFIRMED).** The static screen blocks os.listdir, glob, importlib, duckdb and more (evaluator.py:121-139), but not Python `open()`. Cross-process caching would still have to pass the trusted residual read, the RMSE check and the protected `fit`. No patch uses open, pickle or file writes (grep over all 13 patches).

## Passing runs checked (11 PASS)
All 11 patches downloaded; I read k27 and muse in full and grepped the rest:
- k27: legit. Single UPDATE…FROM over only the needed dimensions; drops per-tree partition tables inside the update, which counts against itself.
- muse: legit-ish. UPDATE…FROM join, and partition_target_relation is turned into a no-op because every fact key exists in the dimension tables (documented data property).
- glm, astra, ds, opus, wonder, glmf, gemini-agy, terra, k31: in-fit caches only (`_best_split_cache`, `row_caches`), and no cross-process state.

## Notes
- The paired schedule and data revision are dated Oct 8–11 (beat_spec.json comments). Formal runs date from Oct 11 onward and the repo has only the initial commit. The earlier other_runs (Oct 6–10) may predate those revisions.
