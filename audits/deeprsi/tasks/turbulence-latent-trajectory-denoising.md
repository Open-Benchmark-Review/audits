# Turbulence Latent Trajectory Denoising

**Epoch scoring item: pass.** 12 engineering, 0 false positives, 0 false negatives.

## Spec
The agent denoises 16-frame sequences of 128×128 ReBlurNet latent maps corrupted by Gaussian noise. The grid covers 4 turbulence conditions × 3 noise factors (0.5/1/2 × latent_std). The restorer runs on CPU only, within 1200 s and a 1 GiB folder. Fitting may use only `train.npz` (512 sequences) or the supplied generator; `dev.npz` may be used only for aggregate model selection. Stored answers and noise-seed exploits are forbidden.

## How scoring works
- **Metric:** per-cell MSE / σ², combined by geometric mean over the 12 cells. Reward = baseline / candidate − 1.
- **Inputs:** `restore.py` receives `noisy`, `condition_id` and the true `sigma`, so this is non-blind denoising.
- **Private run:** 192 unseen sequences with fresh noise. The frozen baseline is re-run on the same draw, so the baseline varies only 0.13% across trials.

## What each model did (private reward; dev reward in brackets)
| model / trial | reward | decisive change |
|---|---|---|
| Fable 78SNWcr | 2.747 (2.671) | Rank-2048 PCA AR(1) Kalman prior + 2 (2+1)D U-Net residual denoisers trained on generator data |
| Fable hnWjajq | 2.733 (2.653) | Pooled-eigenbasis Gaussian smoother + 2 residual U-Nets on a period-8 pixel-unshuffled grid |
| GPT CgZXFaG | 2.660 (~2.583, no breakdown) | 1536-direction population PCA prior + phase-aware CNN refiners, cascade and calibration |
| GPT m5NsTAX | 2.588 (2.510) | PCA prior + neural experts stacked by blend coefficients fitted on fresh generator data |
| Argon CpnFVQM | 2.559 (2.486) | Pooled Wiener filter + block-phase polynomial refiners + NAFNet ensemble |
| Argon 3XGKFg3 | 2.515 (2.439) | Pooled Wiener filter + 5-layer nonlinear block-regressor cascade |
| Gemini Flash 3q8vdhv | 2.306 (2.232) | Rank-3072 diagonal AR(1) Kalman smoother + 7-layer dilated CNN |
| Kimi WPX7E42 | 2.208 (2.149) | Rank-4096 Toeplitz-temporal Wiener filter (0.02235) + cross-mode MLP refiner |
| Grok bbUmbse | 2.195 (2.135) | PCA + Fourier AR(1) priors + coefficient and spatial correctors |
| Grok DENHGGE | 2.158 (2.088) | PCA Wiener + Fourier residual prior + 3-D conv corrector, halved in the top 32 modes |
| Kimi yZXCrFP | 2.142 (2.079) | High-rank PCA + temporal GP + summed 4-CNN residuals + time-reversal TTA |
| Gemini Flash 4LuQaZs | 2.040 (1.987, no breakdown) | Pure linear empirical-Bayes spatio-temporal Wiener filter, rank 3800 |

## Key findings
1. **Most of the gain is generic.** The starter truncates to a rank-64 PCA basis. Using a high-rank Gaussian/Wiener prior instead gives ~0.0223 NMSE (reward ~2.0) for everyone.
   - Kimi WPX7E42 measured the linear-only result at 0.02235, which it described as near Bayes-optimal among linear estimators.
   - Gemini Flash 4LuQaZs ships only such a Wiener filter and scores 2.04, about 74% of the best reward.
   - The remaining 0.2–0.75 comes from nonlinear residual refiners trained on unlimited generator data.
2. **The insight that separates the top four is task-specific but uses known techniques.** The frozen encoder imprints a periodic (period-4/8) phase pattern. Pixel-unshuffled, phase-aware CNNs (Fable hnWjajq, Fable 78SNWcr, GPT CgZXFaG, GPT m5NsTAX) therefore see stationary statistics.
3. **No fitting to public data and no seed exploitation.**
   - Fable rebuilt the dev noise from the stored `noise_seed`, but only for tracking and checkpoint or ensemble-weight selection on aggregate scores. That is allowed, and Fable re-checked with other noise seeds (0.0182) and generator holdouts (0.0183).
   - The Argon trials explicitly kept dev out of fitting and used self-generated validation sets. Argon's fitting scripts are not shipped in the submission, which hurts reproducibility but breaks no rule.
4. **Two trials have rewards but no breakdown.** GPT CgZXFaG has `rewards={}` with no exception; Gemini Flash 4LuQaZs has ArtifactCollectionError. Both rewards equal their dev result plus the common +0.06–0.08 private offset, so they look genuine.
5. **Noise is very low.** Dev and private orderings are identical and the baseline drifts only 0.13%. The narrow 2.0–2.75 band reflects real differences in nonlinear refinement, not noise. The only within-noise pair is Fable's two runs.
6. **Science vs gaming.** This is competent applied denoising with no gaming. The task mostly measures how much capacity and generated data an agent stacks on the same linear core.
