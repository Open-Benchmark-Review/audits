# CLIP model soup on ImageNetV2

Task id: `model_soup_clip_imagenetv2` (Einsia/AI4AI-Bench @ `5ced1e2`). Structured review: [`../data/task_reviews/model_soup_clip_imagenetv2.json`](../data/task_reviews/model_soup_clip_imagenetv2.json).

**Rubric code: `CONSTRUCT`.** Confirmed and counted toward the threshold. The sigma scale cannot tell agents apart. The confirmed score-changing defect is that the proxy sits inside the final.

## The task

- Build an affine weight-space combination of 72 frozen CLIP ViT-B/32 fine-tunes.
- **Score:** ImageNetV2 matched-frequency top-1 on 10,000 rows.
- **Proxy:** 2,000 rows.
- There is no training (`declaration.py:3-6`).
- **Paper anchors:**
  - baseline 0.686 (the shipped uniform soup, 0.6859)
  - optimum 1.0
  - phi = x
- The case pages' "fixed start" is the best single ingredient, model_69, at 0.6874.

## What we checked

- **Proxy rows are 20% of the final.**
  - ImageNetV2 has exactly 10,000 images (1,000 classes x 10).
  - The proxy is offsets 0-1 and the final is offsets 0-9 (`harness/grade.py:60-61`). The evaluator says so directly: "the proxy is now *inside* the final -- 2000 of the 10000 rows are the ones the Agent tuned on" (`harness/final_eval.py:15-18`). The asset lock lists the proxy as `derived_from: data/imagenetv2_final` (`assets.lock.yaml:161-174`).
- **Proxy labels are visible, and the proxy is mounted in formal replay too** (`declaration.py:109-113`). Every recipe therefore tunes coefficients on 20% of the scored rows.
- **The other 8,000 rows are hidden.** They are mounted only at scoring (`assets.lock.yaml:150`), and the case pages found no exposure.
- **Network:** none (`task.toml:32`).
- **Leakage is measurable from the evaluator's split diagnostics.**
  - Best artifacts score 0.001-0.003 higher on the full set than on the unseen 8,000 rows. For the uniform soup the difference is only 0.0005.
  - Net inflation of each cell's gain over the baseline is about 0.0015-0.0026 top-1, typically 20-30% of the gain (terra/medium 31%, sonnet-5/max 17%). In sigma that is about 0.006 per cell.
  - In luna/high and sol/none, best-of-3 between checkpoints is decided entirely by proxy-overlap images.
- **The artifact gate is real.** It solves the affine coefficients against all 72 ingredients with residual/norm at most 1e-6 (`harness/soup_check.py:118-119, 301-306`); a violation invalidates the trial (`final_eval.py:160-183`). Every artifact passed.
- **Documentation mismatch.** `final_eval.py:9-10` says "v1 takes the last checkpoint and has no selection step", but the orchestrator takes the best of 3 on the final (`orchestrator/final_score.py:147-150`).

## Anchors: why sigma means little here

- **Baseline below the start.** The paper baseline is uniform (0.686), which is below model_69 (0.6874). Submitting the shipped `best_single` option scores sigma 0.104, a "win" the task itself calls "a statistical tie" (`instruction.md:42`).
- **Unreachable optimum.** 100% top-1 is out of reach; realistic soups top out around 0.70-0.71. sigma is confined to 0.10-0.15, and the 28 scored cells span 0.117-0.142.
- **The shipped code already has the main method.** It ships `strict_greedy` (`solution/run.sh:29-33`, `solution/soup.py:63`), which gives 0.6936 (sigma 0.122). 10 of 28 cells are within 0.0001 of that, and the median is 0.6939.

## Results

| Score band (top-1) | Cells | sigma |
|---|---|---|
| 0.6972-0.7006 | sol max (0.7006), sonnet max (0.6985), sonnet low (0.6983), sol high (0.6972) | 0.132-0.142 |
| 0.6950-0.6961 | opus low/medium/xhigh, sol medium | 0.126-0.129 |
| 0.6918-0.6943 | 20 other scored cells, mostly greedy or near-greedy soups | 0.117-0.124 |
| none | terra none (early exit, empty patch) | 0 |

- **Classification:** all scored cells are engineering (greedy soups, learned soups, CV/bootstrap selection, i.e. known techniques). Six reproduce or minimally tweak the shipped greedy rule (novelty none). terra/none is no_gain.
- **Grader agreement:** no false positives or false negatives. Every cell for which the page gives an unseen-row score still beats uniform on those 8,000 rows (0.6915-0.6959 against 0.6854). The gains are real, but small and inflated by the overlap.
- **Noise.**
  - Class-clustered SE is about 0.0067; paired SE against the references is about 0.0025.
  - 16 cells sit in 0.6935-0.6942, i.e. within 7 images of each other.
  - All configuration differences are 0.025 sigma or less, at most 0.0025 of a configuration's 10-task mean.
- **Best-of-3.** In 12 of 28 scored cells the official checkpoint is not the last. The mean gain is +0.0025 sigma; the largest are opus/low (+0.014) and opus/medium (+0.0135). No outcome flips.
- **Site and audit consistency.** On five pages (opus/xhigh, luna/high, sol/max, sol/xhigh, terra/high) the structured "Protocol exposure: Confirmed" contradicts the page's own prose ("none found"). luna/medium's artifact 100 lacks a receipt, with no effect on the result.
