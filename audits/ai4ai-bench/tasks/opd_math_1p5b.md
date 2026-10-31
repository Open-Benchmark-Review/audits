# OPD math 1.5B (`opd_math_1p5b`)

**Rubric: `MINOR`** (confirmed, not counted toward the threshold).
Structured review: [`data/task_reviews/opd_math_1p5b.json`](../data/task_reviews/opd_math_1p5b.json).

## Task and scoring

The agent must improve DeepSeek-R1-Distill-Qwen-1.5B. The shipped method is sampled-token on-policy distillation
from the teacher JustRL-DeepSeek-1.5B, trained on a DAPO-Math-17k subset that has been decontaminated against AIME.

- **Proxy:** MATH-500, 4 samples per question, rule grader only.
- **Final:** AIME 2024 + 2025 (60 questions), 32 samples per question, T=0.7, 31,744-token cap, rule grader with a
  CompassVerifier-3B fallback (`harness/final_eval.py:102-111,432-469`).
- **Anchors (paper):** baseline 0.436, optimum 1.0. The task's own shipped replay scored 820/1920 = 0.4271
  (`instruction.md:36`).

## Findings

- **The hidden data is intact.**
  - AIME is mounted only in the score phase (`declaration.py:21-43,111-117`). The image carries no AIME data
    (`environment/Dockerfile:91-96`, `environment/check_image.py:132-135`).
  - Training rows are 8-gram-decontaminated against the pinned AIME snapshots
    (`environment/assets.lock.yaml:115-142`).
  - MATH-500 predates AIME 2024/25, so the proxy cannot leak.
  - There is no network.
  - Case pages report zero literal hits of any final problem in any trajectory.
- **Memorisation risk:** AIME 2024 predates the fixed student, and its shipped component is 0.496 vs 0.358 for
  AIME 2025. Every cell starts from the same student and teacher, so this shifts the absolute level rather than
  the comparisons (UNCONFIRMED as a driver).
- **Noise dominates.**
  - The question-clustered SE is about 0.052.
  - Near-identical checkpoints differ by up to 0.016 (Sonnet 5 high, step 1650 vs 1651: 0.411 vs 0.427).
  - All 25 scored cells fall in 0.392–0.449 and none is distinguishable from the shipped 0.427. The best cell is
    +0.022 over the shipped replay. The task's ranking of configurations is noise, plus whether a nonempty patch
    was submitted (σ about 0.1 vs 0).
- **The anchors are inconsistent.**
  - The paper baseline (0.436) is not the documented shipped replay (0.4271). Under 0.436, 5 cells beat the
    baseline; under 0.4271, 14 do.
  - An optimum of 1.0 is unreachable, which compresses OPD σ into 0.09–0.12.
- **The grading does not match its documentation.**
  - `instruction.md:23` and `task.toml:66` promise a verifier fallback for both metrics, but the proxy is rule-only
    (`harness/grade.py:55-63`, `harness/fast_eval.py:223`).
  - The final's CompassVerifier fallback judges about 1,100 of 1,920 rows per checkpoint. It is given `question=""`
    (`final_eval.py:412`), and no agreement rate with ground truth is reported.
- **Best-of-3 selection on the test set:** in 16 of 25 scored cells the reported checkpoint is not the last. This
  flips 4 cells across the 0.436 line (Opus 5 xhigh, Luna medium, Sol low, Terra medium), changing σ by 0.012 or
  less each.

## Cells

- **Classification:** all 29 cells are `no_gain`. 21 made hyperparameter, sampling or data-order changes, or
  forward-KL, top-k KL or task-reward variants, all within noise. 4 submitted empty patches (Luna low, Terra
  high/low/none, σ=0).
- **Grader agreement:** agree for all 29. No false positives or false negatives.
- **Benchmark-audit agreement:** disagree for 2 cells.
  - Kimi K3: "exposure Confirmed" refers only to readable evaluator hashes, which every cell had.
  - Terra low: the structured exposure field says Confirmed, but the page text says no exposure.
