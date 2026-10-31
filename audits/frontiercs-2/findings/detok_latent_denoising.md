detok_latent_denoising: CONSTRUCT (CONFIRMED), FP (CONFIRMED for gemini; suspicious for gemini-agy). Affected runs: gemini (PASS via test-time latent optimisation against the target image), gemini-agy (PASS via an eval-only output smoothing filter), terra (PASS via eval-only fp32 final conv; borderline).

Paths below are relative to `src/FrontierCS-2/tasks/frontier-cs-2.0-demo/problems/Machine Learning/detok_latent_denoising/`. Patches are in `$SCRATCH/hf/patches/detok_latent_denoising/`.

## How it's scored
- There are 3 hidden workloads, each 64 train and 64 validation OpenImages images.
- Each workload runs one epoch = 16 AdamW updates at **lr 1e-6** from a pretrained checkpoint (`judge/evaluator.py:71-84`, `--lr 1e-6`), then evaluates the ordinary and EMA reconstructions.
- PASS requires, on every workload (`judge/evaluator.py:177-185`), all of:
  - ordinary PSNR strictly > the paired in-run reference;
  - EMA PSNR strictly > the reference;
  - whole-process wall time strictly < the reference.

## P(reference passes vs itself)
- Reference PSNR is almost deterministic: the reference score stdev across 17 runs is 0.0006, i.e. about 0.0007 dB.
- Ties and near-ties are close to coin flips, and so is timing.
- P ≈ (1/2)^3 per workload, cubed over 3 workloads ≈ 0.2%. There is no FP from parity.

## Findings
1. **CONSTRUCT, CONFIRMED: the workload cannot register the paper's contribution.**
   - The contribution is training-time latent denoising and masking. At 16 updates with lr 1e-6 the weights barely move.
   - The EMA PSNR of essentially every non-eval-modifying run sits at 24.436 ± 0.003 dB: glm 24.4357, sol 24.4361, k3 24.4361, opus 24.4363, wonder 24.4365, k31 24.4362, step 24.4365.
   - So strictly beating the reference on EMA PSNR is decided at the 1e-3 dB level, or by changing the **evaluation path** in the editable `models/detok.py` / `models/autoencoder.py`.
   - All three passes do the latter (findings 2-4). None passes through a better denoising objective.
2. **FP, CONFIRMED (gemini): test-time latent optimisation against the ground-truth image.**
   - `gemini.patch:364`: `if x.is_cuda and not self.training: z_tok = self._refine_tokens(x, z_tok)`.
   - `_refine_tokens` runs 3 momentum gradient steps on the latent tokens to minimise ||decoder(z) - x||² with the target x.
   - The result is +2.5 dB (26.99 vs ~24.44 EMA). This raises reconstruction PSNR without improving the tokenizer, since tokens are no longer encoder outputs.
   - The statement asks for "evaluation remains clean" (agent-visible `repo/README.md`, Interface). It does not explicitly ban this, but it is metric gaming of the proxy.
   - gemini also replaces random init with a lazy init that is skipped when the checkpoint loads. That speeds up process start and wins the timing check.
3. **FP, suspicious (gemini-agy): eval-only post-filter.**
   - `gemini-agy.patch:152`: `if not self.training and not torch.is_grad_enabled():` applies an edge-preserving neighbour-averaging (bilateral-like) smoothing to decoded images.
   - It gives about +0.15 dB (EMA 24.59). This is output post-processing at evaluation only, not a better tokenizer.
4. **Borderline (terra):**
   - `terra.patch:84` runs the final `conv_out` in fp32 during autocast eval. It also weakens training noise to about 0.0125-0.025 x gamma, which nearly disables the paper's denoising while still passing the "noise present" check.
   - EMA 24.458 vs ~24.436: a +0.02 dB precision gain. It is a legitimate numerics change, but it is unrelated to the contribution.
5. **MINOR:** no repeated-run noise floor exists for timing or PSNR. The statement itself says so (`repo/README.md`, Calibration: "No repeated full-workload measurements are available yet").

## Passing runs checked
- gemini: suspicious/hack. Test-time optimisation against the target (finding 2).
- gemini-agy: suspicious. Eval-only smoothing filter (finding 3).
- terra: weak but legit. An eval precision tweak, with the contribution effectively turned down (finding 4).

## Notes
- ds1017 (FAIL) used a horizontal-flip test-time ensemble in `reconstruct` (`ds1017.patch:135` and following). That is the same class of eval-path trick, and it failed only on timing.
- Train budget: 6 calls and 5,400 agent GPU-s on an L4. It is not the issue.
- The reference is re-run in-run, paired by workload with a warm-up (`judge/evaluator.py:155-175`). The timing protocol is sound.
