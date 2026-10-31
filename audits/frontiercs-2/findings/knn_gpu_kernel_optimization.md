# knn_gpu_kernel_optimization

**Verdict:** `knn_gpu_kernel_optimization: CONSTRUCT (CONFIRMED); MINOR strict-latency FN surface (UNCONFIRMED)`. 2/17 PASS (opus, gemini-agy), both legitimate. The construct issue affects how all 17 runs should be read: the bar is a task-author kernel, not the FlashLib method.

## How it's scored
- 8 final workloads (SIFT/GIST, 500K rows, k=10/50/100, plus strict-only full 1M SIFT k=256 and full 1M GIST k=100). Each timed call samples fresh query and database rows. 2 warmups and 7 timed calls, with the in-run reference and candidate in separate workers.
- PASS per workload: median latency strict `<`, worst ball-recall `>=` ref (and ≥ 0.88), worst exact-recall `>=` ref, and an fp64 distance-consistency gate (rtol 1e-6) (`judge/beat_spec.json`).

## P(reference passes vs itself)
- The reference is exact (recall 1.0 everywhere, per beat_spec comments) and deterministic, so quality ties and passes. Latency is strict on 8 workloads, so P ≈ 0.5^8 ≈ **0.4%**. Not FP.

## Findings
1. **The reference is not the paper's (FlashLib's) method (CONSTRUCT, CONFIRMED).** `tasks/metadata/knn_gpu_kernel_optimization.yaml:5-7` cites the FlashLib blog. The `judge/beat_spec.json` comments say: "Reference replaced 2026-10-12 ... the previous reference, a vendored upstream kernel. The reference is now a task-authored exact filter-and-refine kernel in one file (knnlib/knn.py)". The task authors' measurements show the new reference is 1.5–20x faster than the FlashLib kernel: sift_k10 1.46 vs 2.16 ms, gist_k100 1.97 vs 13.79 ms, gist_full 5.36 vs 42.38 ms. `judge/reference.patch` header confirms the task-authored "filter, certify, refine" design. So "beat the human reference" here means beating a benchmark-author kernel written after model runs, not beating FlashLib. This makes the task harder, not easier (no FP), but the label doesn't describe what the score measures.
2. **Benchmark consistency.** The replacement landed between the non-accepted reruns (Oct 10–11 23:12, where astra, sol, k3 and ds frequently PASSED with scores 40–47) and the formal batch (Oct 12 06:27+). Formal in-run reference scores are homogeneous (43.0–45.7, stdev 0.63), so all 17 formal runs used the new reference. Formal results are internally consistent. The 2/17 rate is not comparable to the earlier FlashLib-referenced task, against which several of the same models passed.
3. **Strict latency (UNCONFIRMED, MINOR).** There is no deadband, and the task's own precheck notes the two reference workers on sift_k100 disagreed (1.68 vs 2.77 ms). That kind of jitter can flip a near-tie. In the formal runs, most fails are large (latency 0/8). gemini had latency 8/8 but ball and exact recall 7/8, so it was not exact and its fail is legit. astra 6/8 (46.15 vs 45.67) and sol 7/8 (46.77 vs 44.80) are near-parity fails that noise could flip.
4. **Ball-recall oracle uses the naive's bf16 ranking (MINOR).** This is acknowledged in the comments. Both reference and candidate are compared against the same oracle, so it can't flip an exact candidate.

## Passing runs checked
- opus: legit. Exact int8/bf16 screening plus fp64 refine. `_PLANS` records the Triton launch sequence for a shape and replays it, substituting the current Q/DB/output tensors (`opus.patch:504-545`). Every kernel, including row norms, reruns on the current inputs. No result caching.
- gemini-agy: legit. GEMM-min tile screening plus candidate refine, with a fallback for small or edge shapes (`gemini-agy.patch:476-520`). No module-level state.

## Notes
- No infra failures among the formal runs. `judge/calibrate_reference.py` only measures distance error. Timing uses the in-run reference, not a fixed one.
