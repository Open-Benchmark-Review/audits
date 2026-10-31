# Music Transcription

Task: `music-transcription` (Kyutai; audio)

## The task

Agents transcribe 30-second multi-instrument clips into notes: onset, offset, MIDI pitch and one of nine instrument classes.

- **Limits:** at least 50x real time, a submission of at most 1 GB, and 10 labelled public clips.
- **Allowed:** pretrained transcription checkpoints, and using the public clips for anything.

## How scoring works

- **Metric:** macro onset F1 over the 9 classes (50 ms tolerance), summed over 271 held-out clips.
- **Scale:** 0 is the untouched YourMT3+ checkpoint (0.553). 100 is a perfect transcription (`tests/task/task.yaml:55-64`).
- **How the held-out audio is made:** FluidSynth renders a niche MIDI catalog with four General MIDI soundfonts: FluidR3_GM, MuseScore_General, GeneralUser-GS and TimGM6mb (`tests/task/pipeline/amt_render.py:26-36`).
- **The review policy allows training on those same soundfonts.** It names all four as fine (`tests/task/review.py`, training_provenance).

## Results

| Wallet | Opus 5.5 | Astra | Fable | Argon | Muse | DeepSeek |
|---|---|---|---|---|---|---|
| $10 | **61.9** (1au9v7) | 49.4 | 28.8 | 12.6 | 4.6 | 0 |
| $50 | 61.0 | **73.4** (1bd14o) | 47.2 | 0 | 0 | 0 |
| $200 | 64.3 | **76.7** (my6vry) | 28.1 | 38.3 | 13.3 | 0 |

- All 18 reviews passed.
- The five zeros are ordinary models below the floor:
  - DeepSeek: 0.09, 0.43 and 0.36.
  - Argon 2co5hq: 0.542.
  - Muse u96smp: 0.289.
- No trial touched `inductionlabs/frontier-ml-tasks`, the repo or frontierml.org.
- Every use of Slakh2100 is its train split.

## What the models did

- **Opus:** fine-tuned YourMT3+, either the full autoregressive model or its encoder with a new frame head. Training data was Slakh2100 train MIDI rendered with the soundfonts it had matched in the public clips.
  - 1au9v7 [75], [100]: "render the Slakh2100 train-split MIDI weighted toward these three".
  - 42qktd [64]: "organ-only clip aligns with FluidR3_GM/MuseScore accordion (0.98 correlation)".
- **Astra:** compact CNN onset/frame models trained from scratch on procedurally generated random compositions rendered through GM banks, plus the 10 public clips.
  - The 1bd14o ensemble adds MT3/YourMT3-encoder networks.
  - It matched soundfonts in 1ytf2u [31], 1bd14o [113] and my6vry [27].
- **Fable:** from-scratch CRNN or Transformer models on Slakh train plus Lakh renders. Only the $50 run matched soundfonts ([52]), and it is 19 points above Fable's other two runs.
- **Argon:** ensembles of frozen or fine-tuned YourMT3+ and MuScriptor with learned heads.
- **Muse and DeepSeek:** small from-scratch CRNN, U-Net or Onsets-and-Frames models, mostly below the floor.

## Key findings

1. **The top scores come largely from matching the synthetic test renderer. I rate these trials grey_area.**
   - 7 of 18 trials fingerprinted the test soundfonts from the public clips and trained on renders through them: all three Opus runs, all three Astra runs and Fable 3zcox2.
   - That includes the winner at every wallet.
   - This is explicitly permitted, so it is not a grading error. But the held-out score then measures fit to four GM soundfonts more than real-world transcription.
   - Astra's from-scratch synthetic-only CNNs beat every YourMT3 fine-tune.
2. **The public clips do not represent the held-out set well.**
   - Untouched YourMT3+ scores 0.265-0.271 on the 10 public clips (Opus 42qktd [60], pegy8h [35]) but 0.553 on held-out.
   - Agents' local scores therefore understate held-out scores. For example, Fable 1926qx scored 0.525 public vs 0.679 held-out.
3. **The real transferable lesson is about timbre.** Opus pegy8h [38]: "Timing isn't the issue ... The errors are timbral" — pretrained AMT fails on a timbre domain gap, and fine-tuning on matched timbres fixes most of it.

## Epoch scoring item: **pass**

- There are no false positives, false negatives or infrastructure zeros.
- The winners lead by about 12 points at each wallet.
- The renderer matching is allowed and was done by every winner.

## Task design

- **The metric is correct and deterministic.** It is a mir_eval-style onset match (same class and pitch, ≤50 ms, maximum bipartite matching), pooled per class over clips and macro-averaged (`tests/task/amt_notes.py:83-113,143-158`). It averages over classes present in the reference, where CONTRACT.md:11 says "the nine class F1s"; the two are equal if all nine occur. One malformed note fails the whole clip (`amt_notes.py:33-34`).
- **The test set is a synthetic renderer, and the contract obscures it.** All held-out clips are FluidSynth renders through four public GM soundfonts, and "Both splits now contain all four soundfonts" (`tests/task/pipeline/README.md:39-46,78`). CONTRACT.md:3 only says "a range of instrument sounds". The trusted review lists the same banks as fine to train on (`tests/task/review.py:26-29`). Fingerprinting them from the public clips is allowed, and every wallet winner did it.
- **The floor is high and undisclosed.** It is untouched YourMT3+ (0.553, `task.yaml:58-64`), measured by direct batched inference with "HTTP serving and the byte cap not exercised". The same model scores about 0.27 on the public clips, so local scores cannot show whether a model clears the floor. Across all 19 models, 33 of 57 trials are 0.
- **Noise is moderate.** There are 271 clips from 200 catalog selections (`pipeline/README.md:5-6`), and sparse classes weigh 1/9 each. The estimated SE is about 2.5 points (2-3.5), from a clip bootstrap that was not run. The ~12-point winner leads are real; gaps under 5 points are not.
- **An old revision exposes some held-out clips.** 44 current held-out clips were public in an earlier dataset revision (`pipeline/README.md:11-13`). This is a contamination path beyond `private/`; no trial used it.
- **Self-check is faithful for the gates.** It runs the size gate and a 271-request pass (public clips cycled) at concurrency 16 against grading's 162.6 s formula, with 2x patience to measure the factor (`tests/task/verifier.py:141-206`). It has no review and no representative score. The 50x gate is all-or-nothing (CONTRACT.md:11), but it zeroed no audited trial.
- **Feasible at $10, but money matters less than method.** Sonnet scored 73.8 and Opus 61.9 at $10. Astra scales (49.4 -> 73.4 -> 76.7), Opus is flat, and Fable follows whether it matched soundfonts.
- **There is no reference model.** `solution/` is the smoke fixture (no notes, 0). The YourMT3+ floor script (`pipeline/amt_yourmt3.py`) is the only organizer model.
- **Verdict: minor_issues.** It is fair across models and harnesses, but validity is limited: the score largely measures fit to four GM soundfonts, and the undisclosed off-the-shelf floor zeros most trials.
