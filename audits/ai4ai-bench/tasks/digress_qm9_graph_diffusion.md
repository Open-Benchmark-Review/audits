# DiGress (QM9 graph diffusion): `digress_qm9_graph_diffusion`

**Rubric code: `FP`** (confirmed; not counted toward threshold, because the σ at stake is ≤ 0.006 per cell).
Structured review: [`../data/task_reviews/digress_qm9_graph_diffusion.json`](../data/task_reviews/digress_qm9_graph_diffusion.json).

## Main finding: noise plus best-of-3 test selection lets a null patch beat the baseline

gpt-5.6-terra/low changed only `SAVE_INTERVAL`, so its formal run was effectively the shipped recipe. It reached a
best-of-3 test NLL of **65.35** (checkpoints 66.37 / 66.72 / 65.35). That is below the paper baseline of 65.8, so the
cell gets σ 0.106. It is also 4.2 NLL better than the task's declared shipped reference of 69.57
(`instruction.md:36`).

Consequences:

- Six more cells are credited above baseline while doing no better than this null replay.
- Of the 12 cells credited above baseline, 6 flip below it if the last checkpoint is scored instead of the best.
  Selection is made on test NLL itself (`orchestrator/final_score.py:143-148`).

## Leads checked

- **Proxy ≠ final (refuted).** The fast headline is validity × uniqueness × novelty, but fast eval also reports
  validation NLL as its ranking metric (`harness/fast_eval.py:119-122`, `instruction.md:25`).
- **Test split mounted only at scoring (confirmed).** Explore and retrain see a train/validation asset whose test
  tensor is a byte-alias of validation, with no raw files (`assets.lock.yaml:107-134`; `declaration.py:20-21, 99`).
  There is no network.
- **Gaming NLL through T or bound terms (refuted as a hack).** The scorer runs the frozen tree, but keeps upstream's
  `cfg = model.cfg` (`final_eval.py:228-237`), so the checkpoint chooses T, the noise schedule and the transition.
  The frozen code still computes a consistent variational bound for whatever configuration it is given. In
  practice T barely moved NLL (T = 50–1000 "nearly flat"; T = 1000 gave 66.17). The best cell, sol/xhigh at 63.72,
  used a uniform transition, which is a legitimate model change.
- **Latent forgery path (not observed).** The scorer unpickles candidate checkpoints with `weights_only` off on
  torch 2.0.1 (`final_eval.py:192`), then takes NLL from the last `(Test|Val) NLL` line of stdout (`grade.py:83`).
  A crafted pickle could print a fake score. All 25 observed NLLs (63.7–69.9) are plausible.
- **σ with an infinite uninformative point.** The paper's formula reduces to ∞/∞ below baseline. `score.py:54-55`
  uses the paper convention 0.1·b/x instead, so being worse than baseline is barely penalised (69.88 → 0.094).

## Anchor issues

- **Optimum.** An NLL of 0 is unreachable, so all 25 scored cells fall between σ 0.094 and 0.128, a band about as
  wide as the noise. The task mean (0.089) is driven by the 4 cells with no score.
- **Baseline vs shipped reference.** The paper baseline (65.8) disagrees with the shipped reference on the case pages
  (69.57). Formal replay of the unchanged recipe sides with 65.8, so the case pages' "beats 69.57" claims are
  overstated.
- **"17 of 29 below baseline".** These are 13 scored cells above 65.8 plus the 4 empty or failed cells (σ 0). The
  count is roughly right relative to a null replay.

## Environment caveat

Thirteen case pages report an `sm_103` "L20D" GPU that the image's PyTorch build does not support. luna/high and
luna/xhigh fell back to CPU training. This is a possible false negative, but it cannot be adjudicated from public
data.

## Cells (29)

| Classification | Cells |
|---|---|
| no_gain | 24 (within the null-replay band, worse than it, or no score) |
| engineering | 5 (opus/max, kimi/max, luna/max, sol/xhigh, terra/medium) |

| Grader agreement | Cells | Which |
|---|---|---|
| false_positive | 7 | terra/low (high confidence); opus/high, opus/low, opus/xhigh, sonnet/medium, sol/medium, terra/xhigh (low–medium) |
| unclear | 4 | kimi/max, luna/max (inside noise); luna/high, luna/xhigh (CPU environment artefact) |
| agree | 18 | |

No reward hacks were found.
