# kami_fp64_block_gemm

**Verdict:** `kami_fp64_block_gemm: MINOR (designed 2.4% deadband); CONSTRUCT (UNCONFIRMED: harness regime makes the task memory-load-bound)`. 7/17 PASS (glm, sol, k3, astra, opus, gemini, gemini-agy), all legitimate.

## How it's scored
- 8 final workloads (4 public and 4 hidden M×N×K batch shapes, ≥4,096 CTAs each). Each CTA gets distinct SplitMix64 dyadic A/B/C slices, `NUM_ITER` is forced to 1, and every output element is checked against a CPU oracle (`judge/readme` §Inputs/Timing).
- Candidate and source-locked reference run in isolated CUDA contexts. 6 paired repetitions, 3 candidate-first and 3 reference-first. Per-arm medians are combined by geometric mean.
- PASS per workload: candidate/reference ratio strictly **> 1.024**, all 8 workloads (`judge/beat_spec.json` metrics[0]).

## P(reference passes vs itself) ≈ 0
- The threshold 1.024 is the upward-rounded maximum self-pair deviation 0.0239 from an exact-H100 calibration of all 8 workloads (`judge/beat_spec.json` tolerance text). A self-pair must exceed it on all 8. Not FP.

## Findings
1. **Designed deadband (MINOR).** A real improvement under 2.4% on any one workload fails by construction. That is a deliberate noise guard, not a defect. Five FAILs had score leads but missed one or two workloads: qwen 7/8, wonder 7/8 (21.71 vs 18.98), ds1017 7/8, k31 7/8, terra 6/8. That fits one hard workload more than noise. The in-run reference score is tight (17.65–18.98, stdev 0.38, about ±4% in absolute TFLOPS across hosts). The comparison is in-run and order-balanced, which is good practice. The self-noise envelope came from one calibration on one host. If other Modal hosts are noisier, a 1.024 bound could occasionally let a parity candidate pass, but that would need a ≥2.4% swing on all 8 workloads at once, so it is negligible.
2. **Harness regime vs. KAMI's design point (CONSTRUCT, UNCONFIRMED).** The KAMI reference kernel loads A/B fragments from global memory with scalar strided loads, then runs its communication-avoiding rank-staged MMA loop `NUM_ITER` times (`judge/reference.patch` lines ~45-110; `for (idx_iter < NUM_ITER)` at 107). The upstream benchmark used 1,000 iterations on resident data. The adaptation sets `NUM_ITER=1` with distinct data per CTA. That is a sound fix for the shared-input shortcut, but it makes each CTA a single tiny GEMM. Arithmetic intensity is about 1.2 flop/byte for 16×16×24, which caps it near 4 TFLOPS at 3.35 TB/s, and about 4.6 flop/byte for 128×64×64. The reference reaches G ≈ 4.4 TFLOPS (score 18 ⇒ G = 20·18/82). Passing patches win mainly through memory-path engineering: 16-byte `cp.async`, `__ldg` double2 vector loads, streaming `st.global.cs` (astra, gemini, gemini-agy, k3, opus). So the task largely measures "write a better-coalesced loader than KAMI's research kernel", not "improve KAMI's communication-avoiding schedule". The paper does report batched FP64 TFLOPS (Fig. 12, per beat_spec comments), so batched evaluation is not foreign to the paper. I couldn't verify whether the paper's batched setup also amortizes loads. Flagged, not counted.
3. **Leakage.** None. The agent repo has only the excised `.cu` file plus harness and plots (`agent-base/frontier/task/repo/src/...`). There is no other KAMI kernel variant to copy.
4. **Infra.** step TIMED_OUT (`agent_active_deadline_exceeded`, agent side). The other 16 completed.

## Passing runs checked (7/7 patches downloaded; grepped for timers, asm, dynamic launches and persistence)
- glm, sol, k3, astra, opus, gemini, gemini-agy: device-only FP64 `mma.sync` or FMA kernels with cp.async/vectorized staging. No `%globaltimer`/clock use, no child launches. The trusted host checks all outputs and times one fixed-entry launch, so there's no route around the work. Legit.

## Notes
- No task change visible; all runs ran on the one released version (initial commit Oct 20, runs Oct 9–26). The reference scores are stable across that window.
