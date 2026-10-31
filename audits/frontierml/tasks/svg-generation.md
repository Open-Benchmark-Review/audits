# SVG Generation

Raw id: `svg-generation` (LLM post-training; source: QuiverAI)

## The task

Fine-tune `openai/gpt-oss-20b` so it writes an SVG for a drawing instruction. The agent submits bf16 weights only. The grader serves them itself (SGLang, FP8, reasoning effort low, temperature 0.5, at most 16,384 tokens, SVG at most 32 KiB).

- **Data:** 30 public instruction/reference pairs, all in the "simple" stratum. They may be used for anything, including training and selection.
- **Rules:**
  - Don't train on validation or test splits of public datasets, or on "any public text-to-SVG evaluation suite".
  - The weights must descend from the pinned gpt-oss-20b.
  - Distillation from teacher models is allowed (`tests/task/review.py:18`).
- **Held-out set:** 254 items spread over complexity groups, drawn from SVGenius. Only the reviewer is told the source (`review.py:21-24`).

## How scoring works

- **Judging:** gpt-6-sol rates each rendering. An item scores (fidelity−1)/9 × (mean of the other five aspects−1)/9. The raw score is the macro mean over complexity groups.
- **Rescaling:** score = (raw − 0.1885) / (0.7535 − 0.1885), clamped to [0, 1] (`tests/task/task.yaml:93`).
  - The floor is untouched gpt-oss-20b, the mean of two runs (0.1955 and 0.1815, `task.yaml:95-98`).
  - The ceiling is the reference drawings.
- **Noise:** the contract says the same weights can differ by about 0.01 raw between gradings. That is about 1.8 points. The floor's own spread is about 2.5 points.

## Results

| Wallet | Model | Trial | Score | Raw | Verdict |
|---|---|---|---|---|---|
| $10 | **Fable** | 5uus6j | **2.7** | 0.2038 | engineering, agree (within floor noise) |
| $10 | DeepSeek | 3r8r1s | 1.9 | 0.1995 | engineering, agree (review skipped; I checked it) |
| $10 | Opus / Argon / Astra / Muse | i9hng5 / 2hht7i / 29hykn / 32wvxy | 0 | 0.165 / 0.105 / 0.070 / 0.072 | no_gain |
| $50 | **Astra** | 5pavh1 | **8.3** | 0.2356 | engineering, agree |
| $50 | Opus | 6b1uc5 | 5.2 | 0.2177 | engineering, agree |
| $50 | Argon | 5tnbkq | 2.7 | 0.2036 | engineering, agree |
| $50 | Fable | 23ajzb | 2.0 | 0.1996 | engineering, agree |
| $50 | DeepSeek / Muse | kei48h / j6w17x | 0 | 0.096 / 0.145 | no_gain |
| $200 | **Fable** | 4vubq5 | **20.3** | 0.3032 | engineering, agree |
| $200 | Opus | 2y9b1x | 18.0 | 0.2904 | engineering, agree |
| $200 | Astra | 5yr6t0 | 14.0 | 0.2677 | engineering, agree |
| $200 | DeepSeek / Argon / Muse | 24zhyt / 5f60ys / 4nyu6t | 0 | 0.041 / 0.173 / 0.124 | no_gain |

## What the models did

- **Every positive score came from distillation.** A frontier teacher (mostly gpt-6-luna; Opus 2y9b1x used Claude Sonnet 5.5 for instructions) drew SVGs for synthetic instructions across complexity tiers. The agents trained LoRA on attention and per-expert MLPs, merged it, and often averaged checkpoints.
- **Fable 4vubq5** (best at $200) used best-of-2 selection with the grader's own judge model, gpt-6-sol [35]. It kept stage 1 because stage 2 scored lower on the public set [148].
- **Teaching the model to stop** was the main engineering problem, because SVGs over 32 KiB score zero:
  - Fable 23ajzb numbered every top-level element and stated the element count up front [158].
  - Astra 5pavh1 put part labels and a completion marker in SVG comments [236].
- **Public icon corpora hurt.** Trials that SFT'd on svg-stack, svgen-500k, Iconify or MMSVG made the model worse than the base:
  - Argon 2hht7i, Muse 32wvxy, DeepSeek 24zhyt and DeepSeek kei48h all scored below the floor.
  - DeepSeek 3r8r1s measured it directly: "A full SFT on svg-stack SVG targets ... collapses the model". It fell back to self-distillation that only fixes missing viewBox attributes.
- **Opus i9hng5** scaled lm_head by 0.625 to "mimic T=0.8 sampling while reporting as T=0.5" [158]. That is allowed (`review.py:15-17`), and it still scored 0.

## Key findings

1. **No grading errors.**
   - All 15 reviewer passes hold up.
   - I reviewed the three DeepSeek trials whose review was skipped: no use of test or validation splits, eval suites, or other bases.
   - No trial touched the HF tasks dataset, the benchmark repo or frontierml.org.
2. **8 of 18 trials score exactly 0.** All of them are below the untouched base model, a genuine regression rather than infrastructure.
   - The clamp hides how bad some are (raw 0.041 against a floor of 0.188).
   - Four more trials (1.9 to 2.7 points) are indistinguishable from the floor's own noise.
3. **The public examples are a poor guide to the held-out set.** All 30 are simple icons, while the held-out set is macro-averaged over complexity groups. Agents that tuned only on them, or did no quantitative judging at all (Muse), regressed.
4. **The judge can be called by the agents.** gpt-6-sol is available through Spin OpenRouter, and several trials filtered data or chose checkpoints with it (Fable 4vubq5, Opus 2y9b1x and 6b1uc5, DeepSeek kei48h). Nothing forbids this, but it means optimising directly against the grader.
5. **Infrastructure.**
   - A Spin OpenRouter outage on 2026-10-21 ("All models return 409", DeepSeek kei48h [537]) stopped both DeepSeek trials from judging their final models. It did not change the scores.
   - Argon 5f60ys has a context compaction and a "server restart" notice [1634], but it submitted normally at [1057]. Its steps are out of time order.

## Epoch scoring item: **pass**

- No scoring defect changes a winner.
- The $10 winner (Fable 2.7 vs DeepSeek 1.9) is within the scorer's noise.
- The $200 winner (Fable 20.3 vs Opus 18.0) is about one noise unit ahead.
- Only the $50 result (Astra 8.3 vs Opus 5.2) and the gap between the $200 top three and the rest are robust.

## Task design

- **Floor and noise make most of the scale unreadable.** The floor is untouched gpt-oss-20b, the mean of two held-out runs (0.1955 and 0.1815, `tests/task/task.yaml:93-98`). Those two runs alone differ by 2.5 points. One standard error is about 2.8 points: a macro mean over 67/92/95 items, plus about 0.01 raw between regradings (`CONTRACT.md:11`). 40 of the 57 trials across all models score exactly 0, and the best is 20.3.
- **The held-out mix is not stated.** All 30 public examples are "simple" (`tests/task/svg_data.py:153`). The held-out set is 67 simple, 92 detailed and 95 complex, averaged equally per group (`pipeline/README.md:19`). The CONTRACT says only "mean over complexity groups". Agents see the shift only in the self-check note (`svg_selfcheck.py:306-308`).
- **The public SCHEMA.md is stale.** It still describes the v4 metric ("subject correctness times the mean of explicit attribute, relation and style correctness", `pipeline/SCHEMA.md:5`). It also says an over-budget SVG "counts toward the one-in-twenty limit" (`:9`). `validate.py:71-74` and the CONTRACT say it scores 0 without counting.
- **The ceiling favours the reference.** Each reference is judged against an identical copy of itself ("reference shown as both images", `task.yaml:98`), while candidates are always judged against a different drawing. 100 is probably out of reach. This is not binding at the observed 0-20.
- **The judge is gpt-6-sol, non-deterministic, and open to agents.** It runs with no temperature or seed at `reasoning_effort=low` (`validate.py:170-171`). One malformed verdict aborts the whole grade with no score imputed (`:122`). It passed preregistered controls: reference 0.78, constant circle 0.002, text injection 0 (`pipeline/judge_calibration_v5_results.json`). Agents can call the same model through Spin, which several used for selection.
- **Possible parser stall.** The graded fence regex (`svg_render.py:46`) can backtrack for hours on an unclosed ``` answer with long blank runs, and no deadline interrupts it (`svg_selfcheck.py:40-42`). The self-check screens public answers for this, but grading does not. Not observed.
- **The self-check gives no quality signal.** It runs the audit, the trusted server and the schema check, but judges nothing. It projects the 10,800 s batch from 16 resampled simple icons (`svg_selfcheck.py:58-65`), so the projection is optimistic for complex held-out items.
- **Feasibility at $10 was not established.** No trained-model baseline was run before release (`pipeline/README.md:77`). At $10, 15 of 19 trials score 0 and the rest score 1.9-5.3. The top $10 trial (gemini-3-8-flash d5q92y, 5.3) used $0.05 of compute, which suggests near-base noise. Mean and max by wallet: 0.7/5.3, 2.3/10.0, 4.1/20.3.
- **Neutrality looks fine.** The judge and the most common teacher are both OpenAI models, so a same-vendor preference is possible but unmeasured. Claude agents lead and OpenAI agents do not. The base model, serving setup and hidden SVGenius source are the same for everyone.
- **`solution/` is the shared smoke fixture.** It writes the serve.sh this task forbids and has no `model/` (`solution/README.md:1`), so it would score 0 and shows nothing about solvability.
- **Fairness verdict: minor issues.** The grader is correct and neutral, but low resolution, an undisclosed difficulty shift and a stale SCHEMA mean only the $200 top three and the $50 Astra lead are meaningful.
