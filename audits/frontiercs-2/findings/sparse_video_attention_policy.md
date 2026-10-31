sparse_video_attention_policy: FN (CONFIRMED), MINOR (CONFIRMED). Affected runs: potentially all 16 scored FAILs; astra and terra are the nearest misses.

Paths below are relative to `src/FrontierCS-2/tasks/frontier-cs-2.0-demo/problems/MLSys/sparse_video_attention_policy/`. Per-workload values come from the verifier evidence in the traces (`$SCRATCH/hf/traces/sparse_video_attention_policy/<model>/verifier/evidence.tar` → `metrics.json` → `paired_workload_metrics`). The script that prints them is `$SCRATCH/tools2/svg_pairs.py`.

## How it's scored
- There are 12 graded clips: 8 Wan2.1-14B and 4 HunyuanVideo, each 81 frames at 720p, 50 steps, one fixed seed.
- Every clip must satisfy all of the following (`judge/beat_spec.json`; `judge/evaluator.py:158-161`):
  - latency <= 0.96 x reference;
  - PSNR >= ref - 0.25 dB;
  - SSIM >= ref - 0.01;
  - LPIPS <= ref + 0.005.
- Fidelity is measured against a fixed dense-attention video.
- The reference values are **frozen, single captures** (`judge/dense_targets/manifest.json`: one reference.mp4 and one latency per clip). The reference is never re-run, so its own run-to-run spread is invisible to the judge.

## P(reference passes vs itself)
- **Latency:** the reference cannot meet <= 0.96 x itself (the threshold was set 1 pp above a 3.01% replay spread), so P ≈ 0 and there is no FP.
- **Fidelity, the FN question:** would a re-run of the reference (or any numerically equivalent implementation) stay inside the bands?
  - The reference k-means is nondeterministic: centroid sums use float `tl.atomic_add` (`agent-base/frontier/task/repo/svg/kmeans_utils.py:322-323`, used by `batch_kmeans_Euclid` → `triton_centroid_update_sorted_euclid`, `:638`). The reference EAR path calls this every step.
  - **Wan, measured:** gemini and muse both submitted Wan EAR processors that compute exactly the inherited SAP path. gemini.patch calls `super().__init__` and inherits `attention_core_logic`. muse.patch re-types the same body (its kmeans_utils edits are not on the Wan path; `svg/models/wan/attention.py:381-563`). The two runs were on different days and GPUs.
    - Their Wan outputs differ by |dPSNR| <= 0.011 dB, |dSSIM| <= 0.0047 and |dLPIPS| <= 0.0056.
    - The LPIPS maximum (wan_graded_2: 0.2465 vs 0.2410) exceeds the 0.005 LPIPS band.
    - One of 8 clips has two-sided |d| > band, so the one-sided fail rate is about 1/16 per clip and P(all 8 Wan clear) ≈ 0.6. The CI is wide (n = 8).
  - **Hunyuan, sensitivity measured:** muse's Hunyuan EAR is the inherited SAP body with one change. Dense layers/steps call `self.flash_attention` (FlashAttention varlen) instead of `self.flashinfer_attention` (FlashInfer varlen) (`muse.patch:129` vs `svg/models/hyvideo/attention.py:448-474`). Both are exact dense varlen attention and differ only in kernel rounding.
    - Hunyuan outputs then move by dPSNR +0.90 / -0.66 / -2.61 / -0.15 dB, dSSIM up to 0.049 and dLPIPS 0.010-0.047.
    - **All 4 Hunyuan clips would fail at least one band from a rounding-level change.** Run-to-run atomics noise on Hunyuan was not measured, but the trajectory is evidently chaotic at that scale.
  - **Estimate:** P(a reference re-run clears all 12 fidelity bands) ≈ 0.6 x (0.05-0.8) ≈ **0.05-0.5**. For any faster implementation that changes numerics at all (new kernels, a different sparsity rule), the Hunyuan evidence implies a per-clip pass chance of about 0.3-0.5 even at equal expected quality, so roughly 1-5% across 4 clips before counting Wan.

## Findings
1. **FN, CONFIRMED: the fidelity bands are far narrower than the trajectory-level spread they are compared against.**
   - The bands were justified as "decoded-video measurement noise" (beat_spec comments; readme Calibration). Fidelity vs dense is itself only 16-28 dB PSNR, i.e. the sparse reference is far from dense, and small numerical differences re-roll the trajectory.
   - Evidence is the identical-code pair (Wan) and the kernel-swap pair (Hunyuan) above.
   - The deltas across all 11 candidate traces are roughly symmetric and large: Wan dPSNR SD ≈ 0.5 dB, Hunyuan ≈ 1-2 dB, LPIPS ≈ 0.02.
   - **astra** is about 20% faster on Wan and about 5.5% faster on Hunyuan. It has much better fidelity on 10 of 12 clips (Hunyuan +1.5..+4.2 dB, wan_graded_4 +7.6 dB). It fails only wan_graded_2 (-1.04 dB, LPIPS +0.040) and wan_graded_5 (SSIM -0.0107, LPIPS +0.017).
   - The bands treat that sort of per-clip draw as a regression.
   - This suggests the conjunction measures luck on 12 chaotic draws more than method quality. A genuinely better method (higher mean fidelity and faster) can still fail, as astra shows.
2. **MINOR (CONFIRMED): suspected lucky reference draw.**
   - On wan_graded_2, all 11 candidates with traces are below the reference in PSNR (-0.13 to -1.09 dB). Most are also below on wan_graded_1 and wan_graded_6.
   - Either the EAR estimator truly helps there, or the frozen single reference capture is a favourable draw. With one capture (no repetitions) this cannot be separated.
3. **MINOR (CONFIRMED): the statement contradicts the budget.**
   - The repo README says "At most 3 development submissions are allowed" (`agent-base/frontier/task/repo/README.md:471-472`; also `judge/readme`).
   - The policy, the task README and the metadata give 25 (`policy.json` quota.max_train_calls = 25; `agent-base/frontier/task/README.md:65`).
   - Agents used up to 11. A cautious agent that believed "3" would under-use its budget.
4. **Consistency (MINOR):**
   - HunyuanVideo clips were added on 2026-10-15 (beat_spec comments). k27's formal run (2026-10-12, TIMED_OUT, 0) predates that, and the other_runs sol PASS (43.18, 2026-10-10) is a pre-extension Wan-only version.
   - The other 16 formal runs are on 10-16 or later, with an identical frozen reference (33.932).
5. **Train budget:** 25 calls and 54,000 agent GPU-s on an H100, but one dev evaluation takes about 1 h of 4xH100. This is not the bottleneck.

## Passing runs checked
There are none (0/16). The near misses (astra, terra, sol) look like genuine method work and no hacks were seen. gemini's patch just aliases EAR to the older SAP processor, i.e. no error estimation, which is a 5-6% speedup.

## Notes
- P(ref vs itself) is ≈ 0 on latency by design. On fidelity it is ≈ 0.05-0.5 (UNCONFIRMED magnitude, CONFIRMED mechanism).
- A fix would be repeated reference captures, comparing against the reference's own spread, or a mean-over-clips non-inferiority test.
