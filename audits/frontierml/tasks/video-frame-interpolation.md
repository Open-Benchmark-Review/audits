# Video frame interpolation (video-frame-interpolation)

## The task

- **Goal:** serve `POST /interpolate`, which generates the 3, 7 or 15 intermediate frames (4×/8×/16×) between two endpoint images.
- **Rules:**
  - Specialist VFI weights (GIMM-VFI, RIFE, FILM, their components or descendants) are forbidden, including as teachers.
  - General image and video models and standalone optical-flow models are allowed.
  - No validation or test splits of public datasets.
- **Data given:** three public intervals, all from one 384×720 portrait phone clip (sequence-0027).
- **Limits:** ready in 300 s; 2,250 frames in 2,250 s.

## How scoring works

- **Metric:** LPIPS and sequence FloLPIPS at 4×/8×/16×. Each of the six components is the gap closed between two frozen anchors, clipped to [0, 1], and the score is their mean (`task.yaml:64-71`).
  - The 0 anchor is "permitted-standalone-RAFT-deterministic-synthesis".
  - The 1 anchor is **GIMM-VFI-R-P**, the forbidden specialist (`tests/task/calibration.json`).
- **Held-out set:** **SNU-FILM-arb**, 270 intervals, 90 per factor (`tests/task/pipeline/sources.json`, `tests/config.json`). These are the test lists of a public benchmark built from GoPro test and YouTube footage.
  - The agents are not told this.
  - The review rule treats any use of that footage as a test-split violation (`tests/task/review.py:56-58`).
- **Per-request timeout:** grading enforces 300 s per request (`tests/config.json`, `verifier.py:63`, `validate.py:86-87`). The contract calls this ceiling "adjustable debugging limits, not benchmark speed requirements" (`task.yaml:79-80`).

## Results

| Model | $10 | $50 | $200 |
|---|---|---|---|
| Claude Opus 5.5 | **91.1** | 86.7 | **87.8** |
| GPT-6 Astra | 85.3 | **91.2** | 84.6 |
| Claude Fable 5.1 | 78.5 | 81.8 | 58.2 |
| Gemini 4 Argon | 66.9 | 47.1 | 56.5 |
| Muse Wonder | 68.8 | 49.8 | 55.9 |
| DeepSeek V4.1 Flash | 56.8 | 0 (timeout) | 64.2 |

- All 18 reviews passed.
- The one zero is DeepSeek 1sb7so: "TimeoutError: Sequence request exceeded its deadline".

## What each model did

All 17 scored trials used the same structure: a permitted standalone flow model, warping or softmax splatting, and a refinement network trained from scratch.

- **Opus:** RAFT-large, jointly fine-tuned, plus a synthesis U-Net trained on OpenVid-1M (Mixkit + YouTube-VOS train at $200). 91.1 at $10 cost $8.10 of 4090 time.
- **Astra:** larger flow stacks (SEA-RAFT-M, WAFT/DINOv3, GMFlow, Depth Anything V2, LaMa infill) trained on Vimeo-90K, REDS, Adobe240, X4K and GoPro train splits with test IDs excluded. It used $247–276 of model API per trial.
- **Fable, Muse, Gemini, DeepSeek:** RAFT or SEA-RAFT plus a U-Net refiner on Vimeo/REDS/DAVIS-train/UCF101-train/vimeo1080p.
- **DeepSeek 1sb7so:** trained a full flow + synthesis model from scratch.

## Key findings

1. **No rule violations.**
   - No specialist weights or teachers. Astra's pseudo-labels are SEA-RAFT flow between observed frames.
   - No SNU-FILM download in any trajectory. Three trials used the GOPRO_Large *train* split, which is allowed.
   - Fable 1dybjq downloaded a Vimeo test shard only as a network speed test; nothing later reads it. The reviewer caught and correctly cleared this.
2. **One infrastructure-suspected zero.**
   - DeepSeek 1sb7so's last selfcheck, on the folder it submitted ([596]-[598]), projected 136 s of the 2,250 s budget at 0.06–0.13 s per frame.
   - Grading then failed with a request deadline. The trigger is min(300 s, remaining pass time) per request.
   - At the measured speed neither limit is plausible, and the grade page does not say which request failed. I rate this unclear, infrastructure suspected.
   - It cannot change the $50 winner: DeepSeek's other runs score 56.8 and 64.2.
3. **The public samples mislead selection.**
   - Fable 5xwyxm chose its TTA and hierarchical settings on the three public intervals. It scored LPIPS 0.0185/0.0300/0.0599 there ([148]), at or below the target anchor.
   - On held-out it scored 58.2, against 81.8 for its $50 run.
4. **The top two flip by wallet.**
   - Opus vs Astra margins are 5.8, 4.5 and 3.2 points.
   - Similar recipes swing 20+ points (Fable).
   - Clipping at the GIMM-VFI target compresses the top, and no per-factor breakdown is published.

## Epoch scoring item: **pass**

There are no missed violations. The only defect is a suspected infrastructure zero in a trial that could not have won its wallet, so the winners stand: Opus at $10 and $200, Astra at $50.

## Task design

- **Anchors.** Both anchors were measured on the same 270 intervals. 0 is permitted RAFT-large plus uniform splatting with no training (`tests/task/calibration.json:31`). 1 is GIMM-VFI-R-P, a forbidden specialist (`calibration.json:48`). When the anchors were frozen, no permitted system had been shown to reach the ceiling (`pipeline/anchor_calibration_results.json:29-30`), yet trials reach 91-93. Per-component clipping (`vfi_scoring.py:75-79`) compresses the top.
- **Anchor history.** The scale changed once: GIMM "scored exactly 0 on that historical scale; it scores 1 on the current scale" (`pipeline/BASELINE.md:35`). The floor system's own code (baseline.py, server.py) is listed by hash in `flow_baseline_results.json` but is not in the repo.
- **One late request zeroes the run.** Grading enforces min(300 s, remaining) per request (`tests/config.json:19`, `validate.py:73-87`) with no retries (`CONTRACT.md:32-33`). Yet the contract calls 300 s an "adjustable debugging limit, not a benchmark speed requirement" (`task.yaml:80-81`). DeepSeek $50's zero is exactly this error.
- **Self-check skips the graded frame size.** It adds frame sizes by rotating and enlarging the one public 384x720 clip, giving 720x384 and 1081x577 (`verifier.py:155-163`). The SNU-FILM held-out footage is mostly 1280x720, so per-shape setup and memory at the graded size go untested.
- **Held-out set.** 90 of the 309 available intervals per factor, kept for speed (`BASELINE.md:80-88`). The intervals overlap within a few recordings, and the public and held-out splits share recordings (`BASELINE.md:279-282`), contrary to the group split described in `pipeline/README.md:98-99`. My estimated SE is about 3.5 points (paired against the anchors, not measured). That is comparable to the Opus/Astra margins of 3.2-5.8.
- **Held-out source hidden.** The set is SNU-FILM-arb, the GIMM-VFI paper's own protocol, and agents are not told. The review forbids its GoPro/YouTube test footage "under another name" (`review.py:56-58`), which an agent can only honour by guessing the benchmark.
- **Pilot status.** The task was graded while still marked "(pilot)" with an "admission pilot pending" (`task.yaml:2, 117`). Release checks were still open (`BASELINE.md:8-9`), and media rights are "Unresolved ... redistribution_cleared: false" (`pipeline/sources.json:30-31`).
- **Scorer is deterministic.** It runs in FP32 with TF32 off and deterministic cuDNN (`vfi_metrics.py:264-268`) and needs no judge.
- **Feasible at $10, no scaling.** Opus scored 91.1 for $8.10 of 4090 time. With the ceiling nearly reached, more money adds variance, not score.
- **Reference solution.** `solution/` returns blank or nearest frames and would score 0.
- **Fairness verdict: minor issues.** The metric and anchors are sound and match the prompt. The all-or-nothing request cap, the size gap in the self-check, the small correlated held-out set and the pilot status make close results unreliable.
