# egraph_invariant_restoration

**Verdict:** `egraph_invariant_restoration: FN (CONFIRMED), CONSTRUCT (UNCONFIRMED)`. Affected runs: potentially all 16 scored FAILs. The strongest cases are gemini and gemini-agy (congruence 6/6, wall 4/6), then astra, sol, terra and k31.

## How it's scored
- Paired evaluation with 1 warmup and 9 samples per workload. Each sample runs the test process for at least 4 s and at least 3 invocations. Two metrics are computed per workload: process wall-clock, and Runner `Apply+Rebuild` ("congruence").
- PASS requires `cand <= 0.95 * ref` on **both** metrics on **all 6** final workloads: 3 public dev plus 3 hidden. The hidden ones are `integ_part2`, `math_simplify_root` and `math_simplify_factor` (judge/evaluator.py:25-30, 292-311; judge/beat_spec.json).

## P(reference passes vs itself)
About 0. The bar is a 5% material speedup, so a tie fails. No FP from noise.

## Findings
1. **FN (CONFIRMED). The 5% wall-clock gate is close to unreachable on two hidden workloads, because process overhead dominates their wall time.**
   - I built the reference (agent repo plus judge/reference.patch, Rust 1.94.1, release) and timed 30 process invocations per workload with `RAYON_NUM_THREADS=1` and `--test-threads=1`:

     | workload | process wall | Runner total | apply+rebuild | rebuild only | congr/wall |
     |---|---|---|---|---|---|
     | math_simplify_root | 3.64 ms | 0.69 ms | 0.36 ms | 0.05 ms | 9.2% |
     | math_simplify_factor | 3.51 ms | 0.69 ms | 0.39 ms | 0.05 ms | 7.5% |
     | integ_part2 | 5.43 ms | 2.02 ms | 1.33 ms | 0.34 ms | 24% |
     | math_associate_adds (dev) | 5.69 ms | 2.83 ms | 1.97 ms | — | 35% |
     | empty process (`--exact nonexistent`) | 1.73 ms | — | — | — | — |

   - The removed contribution, deferred rebuild, is about 1.4% of wall time on root and factor. Passing the wall gate there needs a cut of about 0.18 ms. If e-matching search (`machine.rs`, not editable) stays the same, that means removing about 50–67% of *all* apply+rebuild time.
   - The best congruence reduction any model achieved in dev was c≈0.76–0.80, by gemini, gemini-agy and terra. Applied to root, that saves only about 2% of wall time.
   - The final data fit this picture. gemini and gemini-agy passed congruence 6/6 but wall only 4/6, with a geomean wall that was 26% faster than the reference (key_metrics 0.01242 vs 0.01688 s). Every run fails at least 2 wall checks.
   - The README notes processes as short as about 5.3 ms. It does not say that the score-bearing work is under 20% of those processes.
   - Which 2 workloads failed per run is withheld (eval evidence has no per-workload rows), so "root and factor are the failing pair" is an inference.
2. **CONSTRUCT (UNCONFIRMED).** The paper measures rebuild and congruence time. Here the deciding gate is test-process wall time, which on the hidden workloads mostly measures process startup and the fixed test harness (rules() parsing, goal checks).
3. **All 17 runs FAIL. No PASS to check.** The rule set is fully disclosed in the agent README, so this is not a hidden requirement. Development feedback covers only the three larger public workloads, so agents could not see the problem.
4. **step (pending re-judgement).** All 5 train calls and the final ended in about 8–13 s with the generic "build, sandbox, deadline, or correctness failure" message (trace verifications). Other runs show the same fast-failure signature for genuine candidate failures (ds 8.2 s, sol 4.6 s), and their later calls in the same run scored normally.
   - step's patch applies cleanly, and I compiled it (without running it) under 1.94.1. A runtime guard failure is the likely cause.
   - step's non-accepted run on 10-16 scored 56.25 FAIL. A re-judgement cannot plausibly yield PASS, because no run clears the wall gate.
5. **Dev evidence (MINOR).** Every candidate gets a 3–4x wall speedup on `diff_power_harder` while its congruence stays about 1.0. That workload's wall time is dominated by explanation checking (`src/test.rs:94-115`), not by rebuild. Nothing was hidden, but it shows that wall time is weakly coupled to the measured contribution.
6. **Consistency.** Beat-spec v2 (adding congruence) is dated 2026-10-07. All formal runs (10-08 onward) used it. glm's 10-06 run is listed in other_runs only. The in-run reference score varies 51.98–55.29 (sd 1.0), which is timing noise. The comparison is paired, so this is benign.

## Passing runs checked
None (0/17).

## Notes
- The forbidden-capability regex (evaluator.py:114) matches nothing in any of the 17 patches.
- The local measurements were taken on a 4-CPU sandbox. Absolute values differ from the verifier, but the ratios are the point.
