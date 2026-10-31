# kmeans_gpu_kernel_optimization

**Verdict:** `kmeans_gpu_kernel_optimization: MINOR (FP surface: unchecked first Lloyd step, UNCONFIRMED; FN surface: strict latency, UNCONFIRMED)`. 8/17 PASS (ds, k3, opus, gemini, step, gemini-agy, terra, k31). None of the 8 patches exploit the surface.

## How it's scored
- 6 final workloads (w0–w3 public, w4 1M×64×1024 and w5 300K×256×2048 hidden). The judge-owned loop calls `kmeanslib.step` twice on fresh planted-cluster bf16 data, with 2 warmups and 3 timed rounds per implementation in separate worker processes (`judge/evaluator.py:359-466`).
- PASS per workload: median latency strict `<` in-run reference, final labeled inertia `<= 1.05 × ref`, final label-mismatch `<= ref + 0.002` (`judge/evaluator.py:196-200`, `judge/beat_spec.json`).

## P(reference passes vs itself)
- The quality bands include parity, so quality always passes. Latency is strict on 6 workloads, so P ≈ 0.5^6 ≈ **1.6%**. Not FP.

## Findings
1. **Only the second step's output is checked (FP surface, UNCONFIRMED).** `_run_loop` keeps only the last call's labels, centroids and input centroids (`judge/evaluator.py:372-379`). The inertia is computed on the final (labels, centroids), and the mismatch uses the final labels against the centroids passed to step 2 (`:455-456`). Step 1's labels are never checked, and its centroids are judged only through the 5% inertia band. A stateful `step` (call counter) could run a cheap approximate first step. The README says results "must be deterministic functions of the inputs" and forbids caching, but the judge does not enforce that.
   - Size of the gap: I simulated the generator (`tools/km_sim.py`, numpy) with a blunt version where step 1 returns its input unchanged and only step 2 runs. Final inertia vs. the true 2-step result: w0 +10.3% (fails the 5% band), w1 +4.8% (passes), w3 +0.45% (passes). The blunt hack would fail on w0. A milder approximation (subsampled or low-precision step 1) could likely stay inside 5% on every shape while saving close to half the work. Unexploited and unconfirmed.
2. **Strict latency, no deadband (UNCONFIRMED, MINOR).** The in-run reference score spans 39.6–46.1 (stdev 1.86), which is ref/naive ≈ 4.5x–7.2x across hosts. Near-parity runs split as a coin flip would: astra 45.35 vs 45.27 got latency 2/6, muse 44.70 vs 44.36 got 3/6, k27 43.48 vs 43.40 got 2/6. Several runs with large geomean leads still lost one workload: glm 47.76 vs 40.34, wonder 48.36 vs 40.51 and ds1017 47.44 vs 42.83, all at 5/6. That looks like a workload where the reference is strong (likely w3 D=512 or hidden w5), not noise. Not confirmable from released evidence, since per-workload values are withheld.
3. **Reference identity.** FlashLib K-Means (fused Triton assign/update). The "paper" is the FlashLib blog (`tasks/metadata/kmeans_gpu_kernel_optimization.yaml`). Not CONSTRUCT.

## Passing runs checked (8/8 patches downloaded; grepped for globals, counters, data_ptr caches and graphs)
- ds, gemini, terra: single fused or split assign+update kernels, no state. Legit.
- k3, k31: TMA descriptors and launcher caches keyed on shape and `data_ptr()%16` alignment (`k3.patch:413-453`). They recompute on every call. Legit.
- opus: `_PLANS` keyed on shape and alignment (`opus.patch:445`). `_Plan._launch` runs prep, assign and finalize on the current `x` and `centroids` every call (`opus.patch:360-390`). Legit.
- step: `_fastpath` capability flag and scratch buffers only. Legit.
- gemini-agy: `_WORKSPACE_CACHE` holds scratch only. Legit.
- None of the 8 has a call counter or approximates the first step.

## Notes
- The formal set spans Oct 10–26. The reference scores show no regime jump, and every formal run completed.
