# OpenR1: `openr1_code_livecodebench`

**Rubric code: `FN`** (confirmed; counted toward the threshold, but the σ impact is small: at most 0.0045 per cell).
The paper's baseline anchor sits above every replay of the shipped recipe. Full data:
[`data/task_reviews/openr1_code_livecodebench.json`](../data/task_reviews/openr1_code_livecodebench.json).

## Task

Qwen2.5-Coder-1.5B-Instruct is fine-tuned on a fixed 8,133-row Python subset of the decontaminated Codeforces-CoTs
data. The final metric is LiveCodeBench v6: all 175 problems, 10 samples each, pass@1 = c/n. The exploration proxy
uses public v4/v5 problems.

## Findings

- **Hidden data holds.**
  - The v6 rows are mounted only in the score phase (`declaration.py:112-118`).
  - Retraining has no LiveCodeBench mount (`declaration.py:52-69`).
  - The evaluator has no fallback to public rows (`final_eval.py:100-120`).
  - `network_mode = no-network` (`task.toml:32`).
  - The proxy (test4/test5) and the final (test6) are different releases, so they are disjoint
    (`assets.lock.yaml:99,108-113`; `final_eval.py:36-41`).
  - Case pages report no v6 content in any trajectory or patch.
  - Training-corpus contamination is **UNCONFIRMED** and the risk is low: the corpus is the upstream decontaminated
    split, and the task runs no overlap check of its own.
- **Anchor (the confirmed defect).** The paper's baseline 0.127 (`scripts/score.py:18`) equals the case pages'
  single-run shipped reference, 0.12743 (223/1750). The task's own file reports six replays of the shipped recipe
  with mean 0.12286, SD 0.00188 and range 0.1200–0.1257 (`instruction.md:36,41`). So the reference fails against
  itself 6 times out of 6.
  - With b = 0.12286, cells below baseline drop from 25 to 14, and 11 cells flip beat/miss.
  - σ changes by only about 0.003–0.0045 per cell (task mean 0.091 to 0.095), because the task's σ range is
    compressed to 0.076–0.112.
  - Of the paper's 4 cells above baseline:
    - opus/high and terra/xhigh tie the reference exactly (0.1274286) and count as wins only because the anchor is
      rounded to 0.127.
    - opus/xhigh's 0.128 comes from its 60-step baseline-style checkpoint.
    - Only opus/low (0.1383, execution-verified self-training) clearly beats the recipe.
- **The scorer's code does not match the published scores.**
  - The instruction describes n = 10 sampled generations (`instruction.md:23`).
  - The pinned harness generates greedily with n = 1 and scores correct/175 (`grade.py:197-244,294-297,333-336`;
    `final_eval.py:187-188`).
  - Published scores have denominator 1,750, so the scorer behind them is not public. The vLLM eval-image README
    claims the harness is unchanged (`README-eval-image.md:20-31`).
  - Agents saw a legacy "greedy first128" final description, and all checkpoints were later rescored under the 175-row
    protocol. The cells are still comparable with each other.
  - The 64-row proxy's rank correlation with the reference ordering is 0.0 (`assets.lock.yaml:119-125`).
- **Noise.** The descriptive per-problem SE is about 0.023. The relevant replay SD is about 0.002–0.003, both from the
  instruction and from the baseline-equivalent 60-step checkpoints inside the cells (0.1206–0.128). Most cells sit in
  0.115–0.127, inside 2–3 replay SDs of the shipped mean.
- **Checkpoint selection.** In 18 of 28 scored cells the best checkpoint is not the last one.
  - Task mean σ is 0.091 under best-of-3 and 0.088 under the last checkpoint.
  - Two cells flip beat/miss against 0.127: opus/high and opus/xhigh.

## Cells

| Classification | Count |
|---|---|
| engineering | 1 (opus/low; a known technique: rejection-sampling fine-tuning) |
| no_gain | 28 (includes sonnet/medium, whose formal run hit OOM, so σ = 0) |

Grader agreement:
- agree: 23
- unclear: 5 (sol/high, sol/max, terra/low, terra/max and terra/medium; all at 0.1263–0.1269, above every published
  shipped replay but below 0.127)
- **false_positive: 1.** opus/xhigh is credited with beating the baseline using its 60-step baseline-style checkpoint
  (0.128). The submitted method's own checkpoints scored 0.1006 and 0.1023.

Benchmark-audit agreement:
- agree: 28
- disagree: 1. luna/high's Protocol exposure field says "Confirmed" but its own narrative says none was found.

**Answer to the lead.** The baseline can be beaten within the budget. The "25 of 29 below baseline" figure is largely
caused by where the anchor sits.
