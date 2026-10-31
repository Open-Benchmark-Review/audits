# Severity-Agnostic Turbulence Mitigation

**Epoch scoring item: pass.** 12 engineering, 0 false positives, 0 false negatives.

## Spec
The agent improves pretrained MambaTM restoration of 16-frame 256×256 clips across seven turbulence strengths (D/r0 = 1.5–10). Clips carry no strength label. Training may use only `data/reds_train.npy` and the supplied P2S simulator. The public test is for checking only, and the restorer must not reuse information across test calls.

## How scoring works (public `run_sweep.py`)
- **Objective S:** the mean over the 7 bins of restored MSE divided by degraded MSE. Reward = S_baseline / S − 1.
- **Gate:** `STRONG_BINS=(6,8,10)`, `STRONG_MARGIN_DB=0.1`, `valid = strong_gate_passed`. Mean PSNR over strengths 6/8/10 may not fall more than 0.1 dB below the starter.
- **Timing:** each shard of up to 48 clips gets 120 s. The public shards have only 20 clips.
- **Private test:** 420 clips with new optics settings, a secret shuffle seed, and a constant baseline (0.4674).

The overview matches this verifier. The prompt says only "strongest turbulence". The task id ("safe on mild turbulence without losing…") describes a trade-off that the gate is supposed to police.

## What each model did (private reward; public strong-bin ΔPSNR)
| model / trial | reward | strong Δ | decisive change |
|---|---|---|---|
| Fable eTezLSD | 0.738 | +1.97 dB | MambaTMx (8 blocks + temporal skip fusion), ~190k simulator iterations, MSE with metric-matched D/r0 weights, 16× TTA with adaptive budget, DC matching |
| Fable xdbSjnL | 0.708 | +1.95 dB | 10-block temporal-fusion model, ~245k iterations, 16× TTA, ×1.025–1.035 output extrapolation tuned on local validation |
| GPT wf7cQhW | 0.619 | +1.91 dB | 16-view backbone ensemble feeding a learned optical-flow-guided temporal fusion refiner |
| GPT 6RCWGpu | 0.502 | +1.46 dB | Net2Net widening to 130M parameters, D4 TTA, phase extrapolation, motion-compensated fusion; 102.4 s per 48 clips |
| Kimi zzQfEQx | 0.484 | +1.48 dB | MSE fine-tune on all 900 optics rows, function-preserving deepening 6→18 blocks, 16× TTA |
| Argon RaMGX2p | 0.460 | +1.34 dB | Staged fine-tunes, two weight-soup "specialists" interleaved across a 16-symmetry ensemble |
| Argon GgbhMfx | 0.390 | +1.21 dB | Mixed objective, pixel-shift supervision, added 3-D refiners, 8× TTA |
| Grok EzQwRFv | 0.360 (no breakdown) | +1.12 dB | Fine-tune with bin weights chosen from the worst public bins, 16× TTA |
| Grok vkezTdK | 0.345 | +1.08 dB | Depth expansion, all optics rows, D4+time multi-scale ensemble |
| Kimi QgmjK36 | 0.335 | +1.04 dB | MSE fine-tune, Net2Net 6→12 blocks, 16× TTA |
| Gemini Flash GqqP35X | 0.321 (no breakdown) | +1.03 dB | 14 fine-tune stages, hard-bin oversampling, all optics rows, 16× TTA |
| Gemini Flash Taw69S6 | 0.237 | +0.80 dB | Single fine-tune + 16× TTA |

## Key findings
1. **The strong-turbulence constraint is genuinely met but never binds.** Every trial raises strong-bin PSNR by +0.8 to +2.0 dB on the public sweep. The high scorers (Fable +1.97 / +1.95 dB) satisfy the gate by a wide margin, and private `valid=1` confirms they passed.
   - The "safety" trade-off the task advertises is therefore never exercised. Fine-tuning on the full simulator range helps every strength, so the task reduces to plain average-error reduction.
2. **The public test's optics are in the simulator's val split.** The `params.csv` val split (rows 600–899) contains exactly the public test's optics rows (Kimi zzQfEQx [11]–[12]).
   - Kimi zzQfEQx, Grok vkezTdK and Gemini Flash GqqP35X trained on all 900 rows. This is allowed ("the supplied simulator").
   - Their private/public reward ratios (1.13–1.20) match those of train-split-only trials (1.15–1.25), so it gave no private advantage.
3. **Public shards are smaller than private shards.** Public shards hold 20 clips, private shards up to 48. Agents had to extrapolate runtime themselves; GPT ran close to the limit (102–108 s per 48 clips). Everyone passed.
4. **Two trials have rewards but no breakdown.** Gemini Flash GqqP35X and Grok EzQwRFv have rewards but `rewards={}` with ArtifactCollectionError.
   - Their rewards equal their public rewards × ~1.2, the ratio common to all trials, so they look genuine.
   - Gate status cannot be verified, but their public margins (+1.03 / +1.12 dB) make a failure implausible.
5. **Noise is negligible.** Inference is deterministic on fixed clips, and the public and private orderings agree. Fable wins clearly on both attempts.
6. **Science vs gaming.** These are solid known techniques: simulator fine-tuning with an MSE-aligned loss, Net2Net growth, self-ensembles, weight soups and flow fusion. There was no test-data training and no cross-call state. The small physics touches (DC matching, extrapolation to counter TTA over-smoothing) are genuine.
