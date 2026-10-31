# Screenshot diffing (screen-difference)

## The task

- **Goal:** serve a VLM that describes what changed between two consecutive screenshots.
- **Interface:** an OpenAI-compatible chat endpoint.
- **Speed requirement:** at least 5 pairs/s with 14 requests in flight.
- **Data given:** one example pair with reference observations.

## How scoring works

- **Judging:** gpt-6-luna marks each human reference observation as supported, contradicted or missing (`tests/task/validate.py:43-48`). The score is the supported fraction, averaged over **14 held-out pairs × 5 rounds**.
- **Scale:** the published 0–100 score runs from an empty description (0) to the reference observations themselves (100).
- **Throughput gate:** 70 requests must finish within 14 s, or the run scores 0 (`frontier_ml/runtime/resources.py:638-662`).

## Results

| Model | $10 | $50 | $200 |
|---|---|---|---|
| Claude Fable 5.1 | **31.1** | 23.2 | **46.4** (dlcubp) |
| Claude Opus 5.5 | 26.8 | **34.4** (1v1zlc) | 38.0 |
| DeepSeek V4.1 Flash | 21.5 | 10.6 | 10.4 |
| Gemini 4 Argon | 16.3 | 7.1 | 22.3 |
| GPT-6 Astra | 16.0 | 15.5 | 8.2 |
| Muse Wonder | 13.0 | 1.6 | 6.5 |
| *Fixed paragraph, images ignored* | *32.0* | *32.0* | *32.0* |

- All reviews passed, except DeepSeek's three, which were skipped by the operator. I checked those three myself: clean.
- No trial scored zero.

## What each model did

All runs fine-tuned a general VLM: Qwen3-VL 4B/8B, Qwen3.5 4B/35B-A3B or Qwen2.5-VL 3B. The difference was the data.

- **Claude:** real GUI video frame pairs (GUI-World train split, VideoCUA, AgentNet, transition_data), labelled by a frontier teacher, often with a pixel-diff hint in the prompt. Teachers included:
  - claude-sonnet-5.5 (Fable dlcubp)
  - claude-opus-5.5 (Opus fqi4zj)
  - gpt-6-luna, which is the judge (Opus 1v1zlc)
- **Astra:** procedurally generated HTML pairs only, with labels taken from the generator.
- **Argon:** a few hundred teacher-labelled pairs.
- **Muse:** synthetic data plus Mind2Web pairs.
- **DeepSeek:**
  - Zero-shot (its best run, 21.5).
  - LoRA on the WUICC train split plus synthetic data.
  - LoRA on 14k synthetic pairs.

## Key findings

1. **Most trials score below a constant string.**
   - The organisers measured a fixed paragraph listing common UI changes, sent without looking at the images. It scores **0.3199 (32.0)**.
   - They kept the floor at 0 anyway: `tests/task/task.yaml:44-47`, "Operator decision (2026-09-27): the floor is not raised to the best input-blind description".
   - Only Fable dlcubp, Opus fqi4zj and Opus 1v1zlc clearly beat that paragraph. Fable 39iyxm ties it. The other 14 trials score below it.
2. **The metric ignores false claims.**
   - The prompt asks for no claims "the screenshots don't show", but the judge penalises only contradictions of reference observations.
   - No trial exploited this by padding its output. The throughput gate makes long outputs costly.
3. **The test set is tiny and noisy.**
   - There are only 14 pairs.
   - The same blind paragraph scores between 0.280 and 0.378 across rounds from judge variance alone.
   - The $10 win (Fable 31.1 vs Opus 26.8) is within that noise.
4. **The throughput gate depends on the host.**
   - Muse 3ys4t8 failed all four selfchecks (17.6–27.6 s against the 14 s limit), yet passed in grading ([363]: "high host-to-host variance").
   - Opus fqi4zj's first selfcheck missed by 0.28 s.
   - The grade page does not show the batch time.
5. **Benchmark-split exposure, not use.**
   - Fable dlcubp downloaded the GUI-World benchmark annotation file and only ran `wc -l` on it ([15]).
   - Opus 1v1zlc and fqi4zj downloaded benchmark lists only to exclude those videos.
   - None of these is a training or selection use. The reviewer judged them consistently.
   - No trial accessed `inductionlabs/frontier-ml-tasks`, the repo or frontierml.org.

## Epoch scoring item: **pass**

- No false positive, false negative or infrastructure zero changes a winner.
- The scale is still poorly anchored: 14 of 18 runs fall below an input-blind baseline, and the $10 win is within judge noise.

## Task design

- **Floor below a blind constant:**
  - The floor is an empty description (0), and the ceiling is the reference observations themselves (1.0, an identity anchor no describer can reach) (`tests/task/task.yaml:43-49`).
  - The operator measured a fixed, input-blind paragraph at 0.3199 and chose not to raise the floor (`tests/task/pipeline/baseline_results.json`).
  - Above-blind skill therefore starts at about 32. Across all 57 runs the mean is 11.5-14.2 at every wallet.
- **Recall-only metric, contrary to the prompt:**
  - The prompt asks for no unsupported claims (`instruction.md:5`).
  - The judge is told "do not audit or penalize extra candidate claims" (`environment/validation/validate.py:47`).
  - Appending a generic checklist to real model output would likely add about 0.3 on weak models. The review rules on lookup tables and decoy weights (`tests/task/review.py:44-55`) do not cover it. Suspected; no run did it.
- **Tiny, undocumented test set:**
  - It has 14 pairs (`tests/config.json`), each with about 3-5 human observations.
  - Pair sampling gives an SE of about 6-7 points. Judge sampling adds about 1.8: the blind paragraph's per-round SD is 0.041 over 5 rounds.
  - The repo has no source, licence or build pipeline for the pairs. `tests/task/pipeline/` holds only `baselines.py`.
- **Judge:**
  - gpt-6-luna at `reasoning_effort: "low"`, no temperature set (`validate.py:40-48`).
  - The agents' Spin proxy rejects `reasoning_effort` with a 400 error (Opus 54jc8d trajectory line 1584; 11 of 18 trajectories hit it). Dev-time judging therefore runs at a different effort than grading.
  - Using the judge model as a teacher is allowed (`review.py:39-41`) and open to everyone. Opus 1v1zlc did this.
- **All-or-nothing throughput gate:**
  - 70 requests at concurrency 14 must finish in 14 s (`CONTRACT.md:11`; `tests/lib/frontier_ml/validation/evaluation.py:50-53`).
  - It depends on the host (Muse 3ys4t8 failed every self-check and passed grading), and the grade page does not show the measured batch time.
  - Across the 19 models, 9 runs scored 0 with a passing review (`data/all_trials.csv`). I suspect this gate, but the cause is not shown.
- **Self-check:**
  - It runs the full 70-request batch, but on pixel-flipped copies of one public pair, with no judge (`tests/task/verifier.py:48, 72-92`).
  - Grading repeats the 14 pairs byte-for-byte across 5 rounds (`evaluation.py:247`). So self-check is stricter than grading for caching servers, which is the safe direction.
- **Contract text:** `CONTRACT.md:11` omits the test-set size ("averaged over  pairs"). The judge also grades "unchanged state" (`validate.py:46`), which the prompt does not mention.
- **Budget:** $10 is only partly enough: the best $10 run is 31.1, still under the blind paragraph. The 19-model means are flat: 13.4 / 11.5 / 14.2.
- **Reference solution:** `solution/` returns "No description available." (`solution/server.py:138-139`), which scores about 0.
- **Fairness verdict: unfair as a measuring instrument.** It is not biased toward any vendor. But the scale sits below an input-blind constant, the metric ignores the precision the prompt asks for, and 14 pairs plus a stochastic judge give an SE of about 6 points.
