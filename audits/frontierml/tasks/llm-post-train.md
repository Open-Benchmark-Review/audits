# LLM Post-Training (Qwen3-4B-Base)

## The task

- **Goal:** post-train Qwen3-4B-Base into a reasoning chat model and serve it behind an OpenAI-compatible endpoint.
- **Constraints:** a 250 s timeout per request at 32 concurrent, and 16,384 tokens at temperature 0.7.
- **Scoring:** the mean of GPQA-Diamond, MATH-500, LCB v6 and MMLU-Pro. Each is rescaled from the base model (0) to Qwen3-4B-Instruct-2507 (100) and clamped (`tests/task/task.yaml:53-59`).
- **Review:** `review.py:27` forbids "checkpoint or prompt selection" on any benchmark test split. The supplied `/task/public/benchmarks` files are "evaluation-only".

## Results

| Model | $10 | $50 | $200 |
|---|---|---|---|
| Claude Opus 5.5 | **57.6** | 43.3 | **67.4** |
| GPT-6 Astra | 51.6 | 48.3 | 67.2 |
| Gemini 4 Argon | 0 (stalled, no weights) | **55.2** | 58.1 |
| Muse Wonder | 0 (review fail) | 34.8 | 48.8 |
| Claude Fable 5.1 | 26.0 | 46.2 | 0 (review fail) |
| DeepSeek V4.1 Flash | 20.9 | 35.5 | 15.2 |

DeepSeek's reviews were skipped by the operator.

## What the models did

- Every run did distillation SFT on public R1/QwQ-style reasoning traces.
- Most also built serving-side length control: budget forcing, answer reserves, deadlines, n-gram speculative decoding, FP8.
- Opus 562x1w chose between its two training stages on a private dev set from the training sources ([193]). It reported public scores without tuning on them ([201]).

## Key findings

1. **The public GPQA and LCB files are the graded sets, and "selection" was judged inconsistently.**
   - Failed:
     - **Fable 67hhap:** checkpoints and the reasoning budget were compared on GPQA/LCB; [187] "sticking with 13k".
     - **Muse 2wj08u:** a chat template was picked on GPQA, 4/24 → 8/24 ([203], [213]–[214]).
   - Passed for the same kind of tuning:
     - **Fable 2ikiw0:** [136] "Budget forcing improved accuracy significantly—GPQA rose from 20% to 42% and LCB from 15% to 22.5%". The reviewer called this "evaluation".
     - **Gemini s6ff3k:** [354] budget caps set while "measuring speed and pass@1 accuracy" on 32 GPQA and 32 LCB items; [362] "gpqa_diamond score leapt to 0.50".
   - In the skipped reviews, **DeepSeek 671pbq** picked its final training phase partly on a 16-item GPQA probe ([377] "5/16 correct vs 2/16").
   - None of these three trials wins its wallet.
2. **Opus used the graded set for diagnosis only.**
   - Opus 5w16aj ran all 198 GPQA items, found that 95 replies had no answer, trained a format-fix stage, and re-ran GPQA to confirm it ([143]–[186]).
   - It made no score-based choice between variants, which is the reviewer's line. The case is still close to Muse's failed trial.
3. **Gemini $10 never submitted.**
   - The trajectory stops at step 200, 62 minutes into the session, after 34 Gemini API 429 quota errors. The grade page says it "ran out of its 12 hours".
   - It was the only Gemini trial here that was not re-run.
   - This is a suspected infrastructure zero. It would need more than 57.6 to change the winner, above what Gemini scored at $50 or $200.
4. **The $200 result is a tie.**
   - Opus 67.4 vs Astra 67.2 is well within sampling noise: GPQA alone has about ±10 normalised points of SE.

## Epoch scoring item: **pass**

The grading errors found (false positives on Fable 2ikiw0, Gemini s6ff3k and DeepSeek 671pbq) and the suspected infrastructure zero do not change a winner. The selection rule needs a stated threshold, and the graded GPQA and LCB sets should not ship to the agents.

## Task design

- **The graded GPQA/LCB files ship as development data.**
  - The public benchmarks hold all 198 GPQA rows and the full LCB v6 (`frontier_ml/scoring/language.py:712`), the sets the grader reads (`tests/config.json:7-12`).
  - validate.py scores them "the way the final evaluation does" (`environment/validation/validate.py:2`), while the contract says "evaluation only" (`CONTRACT.md:3`).
- **The selection rule has no threshold.**
  - `review.py:25-31` bans "checkpoint or prompt selection" on test splits but draws no line between diagnosis and selection.
  - Fable 67hhap and Muse 2wj08u failed; Fable 2ikiw0 and Gemini s6ff3k passed for similar budget and template tuning.
- **16,384 tokens cannot be reached in 250 s at 32 concurrent.**
  - The settings are `tests/config.json:16-18`. Agents measured about 1,400 tok/s aggregate on one H100, so a full reply "would take ~370s" (Opus 562x1w [59]). For Opus 3hexms, the time limit "cut off about a third of GPQA requests early" ([113]).
  - The anchors were measured at an 1,800 s timeout on two data-parallel H100s (`tests/task/task.yaml:62-64`), and the non-thinking ceiling model never came near the limit.
  - Every competitive run had to build wall-clock length control.
- **Weight provenance against the ceiling model rests on the reviewer alone.**
  - The audit checks only tensor names and shapes, which Instruct-2507 shares.
  - The weight-update comparison was "dropped ... on 2026-10-01 as brittle" (`tests/task/checkpoint_audit.py:8-14`; `review.py:18-20`).
  - Copying the ceiling weights would score about 100 if the reviewer missed it. Not observed.
- **Anchors are measured under the task's settings (2026-10-01, `task.yaml:56-74`).**
  - Floor: the untouched base, with GPQA set to chance because the base scored below it.
  - Ceiling: Qwen3-4B-Instruct-2507. It is not binding: the best trial is 67.4 (52/83/58/78 per component).
  - Some floor points are buyable by format fixes alone, which the review explicitly allows (`review.py:14-16`).
- **The self-check matches grading's gates.** It runs the same checkpoint audit and one wave of 32 concurrent public requests at 16,384 tokens and 250 s (`scoring/language.py:879-981`). It does not run MATH-500, MMLU-Pro or the review.
- **Noise is about 3.2 points** (GPQA alone about 10 on its component; about 4.5 for a difference of two runs).
  - The $200 tie (67.4 vs 67.2) is real.
  - $10 (57.6 vs 51.6) is about 1.3 SE.
- **Feasibility:** yes at $10 (Opus 57.6, Astra 51.6). Gains from more budget are weak and mostly within noise.
- **Judge:** gpt-6-luna for MATH-500 equivalence (`scoring/reasoning_benchmarks.py:31-45`), reference-based, with low vendor risk.
- **Other points:**
  - The Gemini $10 zero (API 429s, no re-run) is a harness-side infrastructure zero.
  - The reference solution is a smoke fixture that fails the checkpoint audit.

**Fairness verdict: minor issues.** The scoring is sound and the self-check is faithful. But the graded sets are public with an unthresholded selection ban, the token and time limits conflict, and anti-copy provenance relies on the reviewer alone.
