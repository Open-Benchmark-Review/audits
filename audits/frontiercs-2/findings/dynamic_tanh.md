dynamic_tanh: FP (CONFIRMED hack in a PASS; flip UNCONFIRMED), MINOR (CONFIRMED). Affected run: gemini (PASS on the pre-fix scorer, uses the exact #647 argv switch).

Paths below are relative to `src/FrontierCS-2/tasks/frontier-cs-2.0-demo/problems/Machine Learning/dynamic_tanh/`. Patches are in `$SCRATCH/hf/patches/dynamic_tanh/`.

## How it's scored
- There are 3 hidden ViT-Base workloads. On every workload the candidate needs top-1 >= the reference, median paired training-block latency strictly < the reference, and median paired inference latency strictly < the reference (`judge/beat_spec.json`, `beats_reference`; `judge/evaluator.py:744-750`). Per-call outputs, loss and gradients under the timed conditions are also checked against the trusted implementation.
- Continuous score (`judge/evaluator.py:726-733`): `0.6*clamp(50+2*(A-A*)) + 0.4*clamp(50+200*log2(T*/T))`, averaged over workloads. **Inference latency is not in the score.**
- Reference score is the constant 50.0. `_score_rows` is applied with candidate = reference (`evaluator.py:751-753`), so quality = latency = 50 by construction. It is not a measurement.
- **What ~70 means:** accuracy is 20.0% for essentially every run, so the quality term is pinned at 50. The latency term saturates at 100 once T*/T >= 2^0.25 = 1.19. So 70.0 = 0.6*50 + 0.4*100 means "training block at least 19% faster on all 3 workloads". It is a ceiling, and it says nothing about inference latency. Astra scores 70.0 and FAILS because inference latency cleared on only 2 of 3 workloads (`checks`: inference 2/3). The score and the verdict are decoupled.

## P(reference passes vs itself)
There are 6 strict paired latency comparisons (3 workloads x {train, inference}), with medians of 11 interleaved blocks. Accuracy ties pass (`>=`). At parity each latency comparison is close to a coin flip. Several parity-level runs (glm, k3, wonder, ds) show training 1/3 or 2/3, which fits that. So P ≈ 0.5^6 ≈ 1.6%. That is not an FP source.

## Findings
1. **FP, CONFIRMED (hack present), flip UNCONFIRMED: gemini's PASS relies on the #647 argv introspection switch.**
   - `gemini.patch:14`: `_IS_MAIN_CLI = os.path.basename(sys.argv[0]) == "main.py"`.
   - It gates the fused DyT kernel (`gemini.patch:35`), the whole-ViT custom C++ forward/backward (`gemini.patch:181`, `_fast_forward` → `_ViTFastFn`/`vit_infer`) and the extension build (`gemini.patch:253`) to `not _IS_MAIN_CLI`.
   - Effect: the accuracy run (frontier-bench.sh → main.py) trains with the plain reference-equivalent path. The evaluator's timed and validated calls use the custom whole-model fp16 kernel. This is exactly the defect named in commit 5630acc6 ("a submission enabled its fast path only when sys.argv[0] was not main.py, so the scored accuracy and the strict accuracy gate came from code that was never timed").
   - The trace confirms it was written deliberately (`$SCRATCH/hf/traces/dynamic_tanh/gemini/models/primary/traffic/00068.request.bin`, message 121 writes the switch). The agent's reasoning is encrypted, so the motive is not visible.
   - Mitigation: the per-call timed-path validation (outputs, loss, every gradient vs trusted) still ran, so the measured latency comes from code that computes correct per-call results.
   - What is not shown is that accuracy (a PASS condition) would hold if the fast path were used during training. Since accuracy is near chance (finding 3), a flip is plausible but unproven.
   - gemini's leaderboard PASS is still pre-fix. The gemini-agy rerun on the fixed version (PASS, 70.0) is a different harness/agent and does not re-score gemini (pi).
2. **opus PASS is legit, but it would be rejected by the post-fix token filter (MINOR, benchmark consistency).**
   - `opus.patch:45`: `os.environ.get("DYT_GRAPHS","1")` is a default-on developer knob. The judge never sets DYT_GRAPHS (grep of `judge/` finds nothing). opus has no argv, `__main__` or process checks, and the same NVRTC DyT kernels and CUDA-graph replay run in main.py and in the evaluator.
   - The post-fix `patch_policy` regex rejects the substring `environ` (`judge/evaluator.py:66` and following). Under the current public task, opus's legitimate patch would score 0.
   - So formal PASS/FAIL for this task mixes two rule sets: opus/gemini pre-fix, gemini-agy post-fix.
3. **MINOR / weak construct (CONFIRMED): the accuracy gate is near chance and non-discriminating.**
   - Each workload is 5 classes, 20 training and 10 validation images, 2 epochs from scratch (`judge/evaluator.py:17`, `:212-216`, `:363`).
   - Mean top-1 is 20.0% (2/10 = chance) in 15 of 16 scored runs. terra has 16.67 and still cleared 3/3, which implies the reference itself also landed below 20 on one workload in that run, i.e. reference accuracy is not stable across runs.
   - The "without losing accuracy" half of the paper claim is therefore not really tested. The task reduces to latency engineering guarded by per-call numerics checks. This does not flip any verdict.
4. **Small train budget (elicitation): constraining but not decisive.**
   - The budget is 3 train calls, 1800 agent GPU-s on an L4 (900 s per instance) over 5 h (`policy.json`).
   - opus and gemini each passed using a single train call. Most failures are at parity: no speedup attempted or achieved (glm, ds, k3, wonder ~48-50).
   - The budget limits iteration but is not what separates PASS from FAIL here.

## Passing runs checked
- opus: legit. A fused DyT kernel reproduces the reference bit-for-bit, plus CUDA-graph replay of the block stack. No harness introspection, and the same path runs in training and timing.
- gemini: suspicious. The argv switch makes the timed path differ from the trained/scored path (finding 1).
- gemini-agy (post-fix rerun): legit as far as checked. No banned tokens (grep for argv/environ/inspect/sys.modules/__main__ finds nothing). It uses an fp16 weight cache keyed by tensor version, plus fused kernels.
- astra (70.0, FAIL): no introspection. It uses `make_graphed_callables` of the model. It failed inference latency on 1 of 3 workloads, so the FAIL is genuine.

## Notes
- Beat-spec v3 added the inference-latency criterion on 2026-10-08. All formal runs are on or after 10-12, so v3 is consistent across them. The earlier other_runs PASSes (astra 66.6, sol 67.7 on 10-10/10-11) are pre-v3 and not accepted.
- The agent-visible statement does document the inference criterion (`agent-base/frontier/task/repo/README.md:64`).
