flow_opd: FN (CONFIRMED), FP-surface (UNCONFIRMED), CONSTRUCT (UNCONFIRMED). Affected runs: all scored FAILs, notably glm (86.1), step (85.5), astra, ds and k3. Each has a mean OCR far above the reference but fails 1-3 single-image workloads.

Paths below are relative to `src/FrontierCS-2/tasks/frontier-cs-2.0-demo/problems/Machine Learning/flow_opd/`.

## How it's scored
- There are 8 final workloads: 4 prompts x 2 seeds. Each is **one** 512px image generated after an 8-update LoRA distillation run.
- Every workload must satisfy C_w > R_w strictly, or C_w = 1 when R_w = 1 (`judge/beat_spec.json` `beats_reference`).
- The reference is a frozen single run (`judge/judge/reference_cache.json`). Final R = [1.0, 1.0, 0.231, 0.231, 0.824, 0.824, 0.833, 0.0].
- The score is mean OCR x 100. The reference scores 61.77 in every run.

## P(reference passes vs itself)
The evaluation is deterministic (deterministic algorithms; the ema_adapter_reload replay matches bitwise in the traces). A re-run therefore ties on 6 sub-ceiling workloads, and ties fail. P ≈ 0, so there is no FP from parity.

## Findings
1. **FN, CONFIRMED: the strict per-image conjunction is not calibrated, and the developers' own qualification file says so.**
   - `judge/judge/qualification.json`:
     - `"reference_repetitions": 1` (line 26);
     - `"release_ready": false` (line 27);
     - `"formal_guard_gpu_validated": false`;
     - outstanding review "Three genuine reference repetitions, OCR variability and attainable strict per-workload headroom" (line 31).
   - The beat_spec comments say: "No noise magnitude has been measured."
   - One single-image OCR draw per workload decides each comparison, and two workloads require an exact 1.0.
   - From the verifier evidence in the traces (`$SCRATCH/hf/traces/flow_opd/{step,glm,astra}/verifier/evidence.tar`):
     - step has mean OCR 0.854 vs reference 0.618 and fails only final-00-1 (R = 1.0).
     - glm (0.861) and astra fail final-00-1 and final-02-1.
     - All three fail final-00-1, whose reference is a perfect 1.0 on that seed.
   - At realistic per-workload win rates for a clearly better method (around 0.7-0.8), P(8/8) is about 0.06-0.17. Candidates with +40% mean OCR therefore fail.
   - Whether the reference's 1.0 on final-00-1 is reproducible or reachable is unmeasured (no repetitions).
2. **FP surface, UNCONFIRMED (no PASS to exploit it): eval images come from the candidate's own sampler, and private prompts are reachable in-process.**
   - `pipeline_with_logprob` is used for the endpoint images (agent-visible README, "Design space": "The sampler is called during ... endpoint image generation").
   - The guard leaves "the mean/integration/exploration schedule ... free" (`judge/judge/transition_checks.py:38-39`). It checks only self-consistency, plus zero noise at eval (`:42-43`).
   - The README states the trainer process "does not provide confidentiality between the trainer and submitted code" for private rows and seeds.
   - A sampler could therefore paint the target text into the final latent. No downloaded patch does this: grep of 15 patches for ImageDraw/ImageFont/frames/sys.modules finds nothing relevant.
3. **CONSTRUCT, UNCONFIRMED:**
   - With only U = 8 optimizer updates (`judge/judge/profiles/ocr-u8.json`), most of the OCR gain can come from the eval-time ODE integrator rather than from better on-policy distillation trajectory sampling, which is the paper's contribution. For example, glm.patch:95 and :137 add Heun second-order integration on the noise_level = 0 path.
   - This is allowed by the statement, but it means "beat the reference" partly measures inference-sampler tweaks.
4. **Train budget:** 4 train calls and 3,000 agent GPU-s on an H100. Each dev run is about 400 s. This is tight, but agents reached large mean gains. The binding constraint is finding 1, not elicitation.

## Passing runs checked
None (0/17).

## Notes
- Beat spec and reference are constant across all 17 formal runs (ref 61.774 every time).
- k27 and glmf scored 0 on invalid submissions (their own errors).
