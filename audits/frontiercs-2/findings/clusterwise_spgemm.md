# clusterwise_spgemm

**Verdict:** `clusterwise_spgemm: OK; MINOR (CONFIRMED) benchmark-consistency issue (scores rescored, one run on an older task version); verdicts unaffected`. Affected runs: none. glmf is the only formal run on the pre-g2 task version.

## How it's scored
- 8 final matrices, 7 alternating fresh-process pairs each. The parent clock times the whole process: load, reorder, build the clustered representation, multiply, output (`judge/evaluator.py:160-186`).
- Pass needs every product to be correct and `C < 0.85*R` on each workload. The throughput metric is the reciprocal of the same test (`evaluator.py:175-178`; `judge/runtime-config.json:15`).
- A reference noise gate rejects the evaluation when MAD or drift exceeds 5% (`evaluator.py:88-97`).
- Score: logistic of the mean log speedup, with the reference fixed at 50 (`evaluator.py:71-85,195`).

## P(reference passes vs itself)
About 0. It needs a 15% win on 8 workloads, and a reference replay is gated at `|c/r-1| <= 5%` (`evaluator.py:171-173`).

## Findings
1. **What "recomputed under the revised scoring policy" changed: only the continuous score, not verdicts. CONFIRMED.**
   - For the 10 notes runs, the record field `margin` keeps the old value while `key_metrics.margin` = score − 50.
   - The old margins fit `old_score = min(100, 50 + 50*(S−1))`, where S = exp(mean log speedup). For example k27 has S=1.470 → 73.5 (record margin 23.5), glm has S=1.665 → 83.25 (33.23), and opus has S=2.018 → 100, capped (margin 50.0).
   - The new score is `100*S/(1+S)` (`evaluator.py:71-85`).
   - `beats_reference` is the per-workload `C<0.85R` conjunction computed from the same saved measurements ("no extra evaluation run"). It doesn't depend on the score formula, so PASS/FAIL is unchanged. This also explains the earlier other_runs scores of 84-100.
2. **Version consistency, MINOR.**
   - The "SEPARATE KERNEL BUILD (2026-10-15)" change (`judge/beat_spec.json` comments) compiles main and kernel as separate translation units with a link guard, so kernel code can't override loading, reordering or output.
   - 15 formal runs are dated Oct 15 or later (g2). glmf's formal run is dated Oct 13 (pre-g2) and scored 0.0 (gate failure, margin −50).
   - Earlier evaluations (other_runs, Oct 6-14) ran on the older build, so the leaderboard mixes versions for glmf only. Its re-evaluations on g2 (Oct 15 and 16) have no verdict (None).
3. **Attempted memoization, neutralized.**
   - k31, k3, wonder and ds1017 add function-static product caches keyed on the A/B pointers. For example `hf/patches/clusterwise_spgemm/k31.patch:223-229` has `if (cached_a == &A && cached_b == &B) { C.share_from(*cache); return; }`.
   - These target the agent-visible program's warmup plus `ITERS 10` loop (`sample/ReorderedFlengthClusterSpGEMM_kernel.cpp:49-63`; `sample_common.hpp:41`).
   - The judge rewrites the entrypoint to `warmups = 0` and `ITERS 1` (`judge/trusted_runner.py:140-145`), so there is exactly one multiply per fresh process and the cache never hits.
   - The k31 and ds1017 passes therefore rest on their real kernels.
4. **Allocator replacement, MINOR/UNCONFIRMED.**
   - opus replaces global `operator new/delete` with 2 MiB THP mmaps and a span cache (`opus.patch:151-220`). gemini-agy and astra add `madvise(MADV_HUGEPAGE)` hints.
   - The link guard explicitly permits replacing the allocation functions, and the change also speeds up allocations in the locked main TU (loading, CSR construction), outside the paper's kernel.
   - This doesn't decide any verdict: non-allocator patches such as sol, terra and k31 also pass, with geomean speedups of 1.6-1.8x against the 1.176x bar.
5. **Only 3 train calls**, but 13/17 pass, so feedback scarcity didn't block anyone. glmf (1 call) and step (3 calls) scored 0 on the gate.

## Passing runs checked (13)
glm, muse, k27, gemini, astra, sol, ds, opus, wonder, ds1017, gemini-agy, terra, k31.
- I grepped all of them for allocators, constructors, getenv, file I/O, static caches and threads, and read the k31 and opus internals.
- All are real clustered hash/SPA SpGEMM kernels, so **legit**.
- The caches noted above are inert under the judge. The getenv calls in glm and glmf are test knobs; the variables are unset in the judge.

## Notes
- Full-process timing with only the kernel editable still gives 1.5-2x gains, so the multiply dominates. That keeps the construct reasonable.
