# ivf_pq_gpu_kernel_optimization

**Verdict:** `ivf_pq_gpu_kernel_optimization: MINOR (FN surface from strict latency on 8 workloads, UNCONFIRMED)`. 8/17 PASS (astra, sol, glm, k3, opus, wonder, gemini, gemini-agy), all legitimate on inspection.

## How it's scored
- 8 final workloads on SIFT1M (6 original, plus strict-only q10k_np32 and q1k_np128_k1024). The index is built once by the frozen naive builder outside timing. Each call gets `fresh_index()` (cloned tensors) and a fresh permutation of the 10K test queries (`agent-base/frontier/task/repo/benchmark/ivfpq_worker.py:168-231`). 2 warmups and 7 timed calls, each paired with the naive in the same process.
- Reference and candidate run in separate worker passes in the same verifier (`judge/evaluator.py:324-338`). PASS per workload: median latency strict `<`, worst iso-recall `>=` reference, worst nn-recall@k `>=` reference (`judge/evaluator.py:262-264`). Validity also requires iso-recall ≥ 0.99, rtol 1e-6 distance consistency vs an fp32 ADC oracle, and no duplicate IDs.

## P(reference passes vs itself)
- The reference's recall is deterministic, so it ties and passes. Latency is strict on 8 workloads, so P ≈ 0.5^8 ≈ **0.4%**. Not FP.

## Findings
1. **Strict latency, no deadband, 8-way conjunction (UNCONFIRMED, MINOR).** The task's own v2 history shows the conjunction "was decided by near-ties in latency on six bandwidth-bound k=100 workloads" (`judge/beat_spec.json` comments). v3 kept the strict rule. Formal near-parity runs: qwen scored 75.65 vs ref 75.67 and got latency 4/8, ds1017 74.07 vs 72.72 got 5/8, glmf 76.69 vs 76.06 got 7/8. The cross-run in-run reference score has stdev 1.43 (70.9–77.1). At this score level 1 point is about 0.38 in ln(speedup), so the ref/naive ratio swings several-fold between hosts. Wonder's in-run reference score of 70.92 is an outlier, so naive timing is very host-dependent. This doesn't directly enter candidate-vs-ref, but per-workload jitter is unobservable from released evidence. A real improvement of a few % on a bandwidth-bound workload has a substantial chance of losing at least one of the 8 medians.
2. **iso_recall `>=` reference on ADC ties (UNCONFIRMED, MINOR).** Ties at the k-th ADC distance are common with PQ codes, and iso_recall compares ID sets against the naive's tie-break. The reference reaches 0.999999, not 1.0, on the k1024 shape. step (latency 8/8, iso 6/8) and ds (iso 7/8) failed on iso_recall. step builds its LUT with split fp16 tensor-core arithmetic (`step.patch:20-21,99-106`), which is a genuine precision loss, so this is not evidence of a tie-break FN.
3. **Reference identity.** `reference.patch` is FlashLib's IVF-PQ search. The "paper" is the FlashLib blog (`tasks/metadata/ivf_pq_gpu_kernel_optimization.yaml`). The beat_spec cites Jégou et al. for the recall@k metric only. Not CONSTRUCT.
4. **Hack surfaces closed.** The README forbids amortizing preprocessing into warmup ("Do all index layout conversion ... inside that search call"). The index tensors are cloned every call and the queries re-permuted.

## Passing runs checked (8/8 patches downloaded; grepped for module-level caches, data_ptr keys, CUDA graphs and hashing)
- astra, sol, glm, k3, wonder, gemini, gemini-agy: no module-level state except scratch buffers. Per-call Triton coarse-select, LUT and scan kernels. Legit.
- opus: `_LAYOUTS`, `_WS`, `_FA` and `_LAUNCH_CACHE` (`opus.patch:758-816`) hold workspace carving and compiled-launcher handles keyed by shape. Every kernel (prep, coarse GEMM, select, scan, fine MMA, exact refine, rank) is relaunched on the current call's index and queries (`opus.patch:935-995`). Legit.

## Notes
- All formal runs date from Oct 12 or later, so they ran on v3 (2026-10-08). There are no infra failures among the formal runs.
