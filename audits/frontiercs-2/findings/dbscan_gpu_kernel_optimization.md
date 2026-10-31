# dbscan_gpu_kernel_optimization

**Verdict:** `dbscan_gpu_kernel_optimization: MINOR (FN surface UNCONFIRMED), OK otherwise`. 5/17 PASS (astra, sol, opus, step, terra), all legitimate. No run flips on a confirmed defect.

## How it's scored
- Final has 6 workloads (w0–w3 original, plus w4 200K pts and w5 min_samples=20 with noise, both strict-only). Each implementation gets 2 warmups and 3 timed fresh inputs, measured in the same verifier on the same H100, in the order naive → reference → candidate, one subprocess per workload (`judge/evaluator.py:308-350`, `judge/worker.py:41-70`).
- PASS needs, on every workload: median latency strictly `<` the in-run reference, min ARI `>=` reference and `>= 0.99`, and max noise-mismatch `<=` reference, both measured against the frozen naive labels (`judge/evaluator.py:262-267`).
- All formal runs are dated Oct 11 or later, so they all ran on beat-spec v3 (2026-10-08). The task has no post-run fix commit.

## P(reference passes vs itself)
- The reference labels are deterministic, so the quality metrics tie and pass (`>=`/`<=`). Latency is strict on 6 workloads, so P ≈ 0.5^6 ≈ **1.6%**. Not FP.

## Findings
1. **FN surface, zero-tolerance noise/ARI gate vs. a non-zero-error reference (UNCONFIRMED, MINOR).** On w4/w5 the reference already has noise mismatch 5e-5 to 1.4e-4 and ARI about 0.9998 against the naive (`judge/beat_spec.json` comments). The candidate must match or beat these with no band. An exact DBSCAN that uses a different but equally valid distance formula (direct difference instead of ‖a‖²+‖b‖²−2ab) can flip ε-boundary points differently from the naive, and can fail even though it is a correct implementation. The rule is stated in the agent README, so it is not hidden. Three runs had latency 6/6 but failed ARI and noise on exactly one workload: gemini (72.12 vs ref 64.12), qwen (69.49 vs 64.39) and k31 (66.10 vs 64.04). Their eval `result.json` (traces downloaded) gives only aggregate counts. The patches show approximation: k31 uses `input_precision="tf32"` (`k31.patch:198`) and gemini caps stored neighbours at `K = 320/512` (`gemini.patch:672`). So these failures are most likely genuine quality losses, not boundary noise. Not counted against the benchmark.
2. **Latency strictness with no deadband (UNCONFIRMED, MINOR).** There is no margin and the comparison is a median of 3. Near-parity candidates split the latency checks about evenly: glm scored 64.34 vs ref 63.87 and got 3/6, consistent with a coin flip. Across runs the reference score has stdev 0.68 (61.7–64.4), which is a ±20% swing in ref/naive speedup (about 41x–64x). Most of that is naive and host variation, and it doesn't enter the candidate-vs-reference comparison directly. A candidate only a few % faster than the reference would often fail. The 5 passes all have clear margins (score +2.3 to +9).
3. **Reference identity (context).** `reference.patch` vendors FlashLib's `flash_dbscan` (bounded top-K=32 kNN in fp32, then GPU union-find; `judge/reference.patch:898-1190`). The "paper" is the FlashLib blog (https://flashml-org.github.io/; `tasks/metadata/dbscan_gpu_kernel_optimization.yaml`), not a peer-reviewed method. The reference is FlashLib's own released code at its default `max_neighbors=32`. Nothing suggests it is crippled. Not CONSTRUCT.
4. **No leak found.** The agent image holds only the naive starter (`agent-gpu/Dockerfile`). `flashlib`/`cuml`/`cupy` imports are regex-blocked (`judge/evaluator.py:34-37`). Fresh data is generated per round (`worker.py:52`).

## Passing runs checked (all 5 patches downloaded to `hf/patches/dbscan_gpu_kernel_optimization/`)
- astra: legit. Triton tiled bf16/IEEE dot distance kernels plus label propagation, no caching.
- sol: legit. Spatial-key ordering, block bounds and a hierarchical radius search. Dispatch on `count > 65536 or min_samples >= 16` (`sol.patch:554`) branches on generic parameters, not workload recognition.
- opus: legit. CUDA-graph replay keyed on (N, D, eps, minpts). Each call copies fresh `x` into the static buffer and replays the full pipeline (`opus.patch:1063-1094`). It's a launch-overhead optimization, not output caching.
- step: legit. Exact tiled kernels with IEEE/tf32x3 dot choices and exact border rule.
- terra: legit. Tiled exact kernel, `allow_tf32=False`.

## Notes
- k27 and glmf scored 0 (invalid or failed candidates). The verifier itself ran in every formal run, and there are no infra failures among the formal runs.
