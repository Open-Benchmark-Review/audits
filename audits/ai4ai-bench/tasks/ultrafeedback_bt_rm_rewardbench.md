# BTRM: `ultrafeedback_bt_rm_rewardbench`

**Rubric code: `FN`** (confirmed; counted toward the threshold). The beat-the-baseline outcome is decided by noise
and by where the anchor sits. Two biases in the FP direction also apply, listed below. Full data:
[`data/task_reviews/ultrafeedback_bt_rm_rewardbench.json`](../data/task_reviews/ultrafeedback_bt_rm_rewardbench.json).

## Task

A Mistral-7B-Instruct scalar reward model is trained on a fixed set of 8,192 UltraFeedback pairs. The final metric is
the RewardBench v1 score over 2,985 pairs. During exploration the agent sees a proxy: 512 pairs drawn from that same
final set.

## Findings

- **The reported score includes the 512 rows the agent saw.** The paper calls the other 2,473 pairs "held out", but
  the official score and reward are `score_final` over all 2,985 rows (`harness/final_eval.py:337-341,365`). The
  held-out score is only a diagnostic (`final_eval.py:214-245,342-344`). The instruction discloses this
  (`instruction.md:23`). Where case pages report both numbers, the visible rows add at most about +0.3 points:
  - opus/medium: 77.09 full vs 76.95 held-out
  - luna/max: 74.36 full vs 74.05 held-out

  The case pages' own Protocol exposure field marks this Confirmed for only 6 of 29 cells, although it applies to all
  of them.
- **The overlap gate exists and is enforced.** `verify_disjoint` (`final_eval.py:149-211`) runs before scoring
  (`:260`) and raises on any hit. It matches prompts and responses exactly, after NFKC, whitespace and casefold
  normalisation. Every case page reports zero overlap.
  - Near-duplicate or paraphrase contamination between UltraFeedback and RewardBench is **UNCONFIRMED**: the gate
    cannot detect it.
- **The phase mounts and the no-network rule hold.** See `declaration.py:55-151` and `task.toml:32`.
- **Anchor.** The paper's baseline is 74.9 (`scripts/score.py:21`), but the task's own shipped reference is 74.569
  (`instruction.md:37`; every case page). Exact replays of the unchanged shipped recipe score:
  - 73.95 (sol/low, seed 42)
  - 66.31 (sol/low, seed 7)
  - 65.41 (sol/low, seed 1729)
  - 73.84 (sol/xhigh, seed 42)

  So the reference fails against itself. With b = 74.569 the task mean σ rises from 0.097 to 0.102, and sonnet/max
  (74.889) flips to above baseline. The uninformative point (50) and optimum (100) are sensible; σ = 1 cannot be
  reached.
- **Noise.** The published SE (about 0.8) is a descriptive binomial (`grade.py:366-396`). The seed spread of the
  shipped recipe is about 8.5 points, and the instruction itself warns that RewardBench is seed-sensitive
  (`instruction.md:27,31`).
  - 7 of the 8 cells above the anchor clear it by only 0.27–0.94.
  - Only opus/medium (77.09, a 10-member LoRA soup) clears it by more than 2 SE.
  - Seed-42-matched comparisons (75.2–75.8 vs 73.8–73.95) hint that the schedule and truncation changes give real
    but small gains.
- **Checkpoint selection.** In 24 of 29 cells the best checkpoint is not the last one.
  - Task mean σ is 0.097 under best-of-3 and 0.088 under the last checkpoint.
  - Two cells flip beat/miss against 74.9: opus/max and sol/none.
  - Several agents published three independent seeds as their three checkpoints, which turns best-of-3 into
    max-of-3-seeds chosen on the final set.

## Cells

| Classification | Count |
|---|---|
| engineering | 8 |
| no_gain | 21 |

Reward hacks: none.

Grader agreement:
- agree: 28
- unclear: 1 (sonnet/max, 74.889: above the 74.569 shipped reference but below the 74.9 anchor)
- false positives and false negatives: none flagged per cell

We disagree with the case pages' Protocol exposure field in 23 cells, because exposure through the proxy rows applies
to every cell. We agree on the conduct fields.

**Answer to the lead.** The task can be beaten, but the "21 of 29 below baseline" figure mostly reflects where the
anchor sits and seed variance. It is not evidence that agents cannot beat the recipe.
