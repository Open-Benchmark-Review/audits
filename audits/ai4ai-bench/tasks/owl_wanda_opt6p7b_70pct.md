# OWL/Wanda pruning, OPT-6.7B at 70% sparsity

Task id: `owl_wanda_opt6p7b_70pct` (Einsia/AI4AI-Bench @ `5ced1e2`). Structured review: [`../data/task_reviews/owl_wanda_opt6p7b_70pct.json`](../data/task_reviews/owl_wanda_opt6p7b_70pct.json).

**Rubric code: `FN`.** Confirmed, but not counted toward the threshold at task level. The task design is sound. The score-affecting defects are run-level and hit 2 of 29 cells, about 3% of the task's sigma. We recommend counting them per cell.

## The task

- Produce a loadable OPT-6.7B whose decoder linear weights are 70% zero. The only inputs are the fixed dense model and a C4 shard.
- **Score:** WikiText-2 raw test perplexity over 140 blocks of 2,048 tokens. Lower is better.
- **Proxy:** WikiText-2 validation, 122 blocks.
- **Paper anchors:**
  - baseline 53.4 (the shipped 3-seed mean, 53.359)
  - optimum perplexity 1
  - phi = -log x
- The shipped recipe does no training. Agents may change the pruning method, may train on C4 (`instruction.md:27`), and are told "OWL/Wanda is the shipped implementation rather than an enforced family" (`instruction.md:53`). The paper's "no training" describes only the shipped recipe.

## What we checked

- **Hidden data holds.**
  - Test text is mounted only in the score phase (`declaration.py:162`, `assets.lock.yaml:154`).
  - Exploration mounts validation only (`declaration.py:70-77`).
  - Formal replay mounts no WikiText at all (`declaration.py:104-111`).
  - Validation and test are disjoint. Retrain and score run with `--network=none` (`orchestrator/container.py:216-230`).
  - WikiText-2 is public and OPT's pretraining corpus included Wikipedia, but that affects every candidate equally. No case page found test text in any trajectory or patch.
- **The exact-sparsity gate is real.**
  - `SPARSITY_WINDOW = (0.699, 0.701)` is computed from the scored tensors (`harness/grade.py:34, 72-83`).
  - A violation invalidates the trial with no reward (`harness/final_eval.py:209-240`).
  - The gate covers decoder `nn.Linear` weights only. Embeddings, LayerNorm and biases may be trained densely, and at least 10 cells did (for example opus-5/max and xhigh, sonnet-5/high, sol/max and medium, terra/max and xhigh, kimi). That is consistent with `task.toml:59` and the Wanda/SparseGPT convention.
  - Unconfirmed: config and tokenizer are taken from the checkpoint (`grade.py:106-115`), and only the 140-block count constrains them.
- **SparseGPT is in scope.** 23 of 28 scored cells use SparseGPT/OBS. The shipped `/workspace/owl` tree already holds an upstream, LLaMA-only SparseGPT route, which agents ported to OPT.
- **The 12-16 perplexity results come from C4 fine-tuning.** 18 cells fine-tune or distill from the dense teacher, which is allowed. This is known technique (sparse recovery, KD), classified as engineering.

## Results

| Tier | Cells | Official best (perplexity) | sigma |
|---|---|---|---|
| SparseGPT + long KD/fine-tune | opus-5 x5, gpt-5.6-sol high/xhigh | 12.96-13.85 | 0.40-0.42 |
| SparseGPT/Wanda + fine-tune | sonnet max, kimi, sol low/max/medium, terra high/max/xhigh, luna xhigh | 14.26-17.41 | 0.35-0.40 |
| SparseGPT, no or short training | sonnet high/medium/xhigh, luna max/medium, sol none, terra low/medium | 19.67-24.31 | 0.28-0.33 |
| OWL/Wanda tuning, short SGD | luna high, luna none | 29.24, 42.90 | 0.24, 0.15 |
| Unchanged recipe | luna low (seed luck), sonnet low (platform failure) | 51.00, 54.00 | 0.110, 0.100 |
| No candidate | terra none | - | 0 |

## Findings

1. **False negative: `claude-sonnet-5/low`.**
   - A storage `OSError: [Errno 70]` at the first trained save left only the untrained pruning fallback. It scored 53.997, which is the shipped seed-0 result.
   - The exploration validation perplexity of the lost method was 17.5.
   - About 0.25-0.3 sigma was lost to a platform failure. The page's benchmark-side qualification is "Confirmed".
2. **False negative: `gpt-5.6-luna/medium`.**
   - Artifacts 108 and 109 scored 23.686 and 22.389 but were dropped for missing `.complete` receipts.
   - The public selection code reads only `summary.json` (`orchestrator/final_score.py:109-143`). `.complete` matters only for elapsed time (`:42`), so the code would have chosen 22.389.
   - Loss: 0.019 sigma.
3. **Site data errors on the same luna/medium page.**
   - Perplexities are shown as -23.686, -22.389 and -24.310, because `final_eval.py:168` writes reward = -perplexity.
   - "Beats it by 35.171/77.669" is wrong: the correct figure versus the shipped recipe is 29.05.
   - The excluded 108/109 are labelled "Retained".
   - Our `scripts/score.py` takes magnitudes and uses 22.389.
4. **Small false positive: `gpt-5.6-luna/low`.**
   - The shipped recipe is unchanged across seeds 1-3. Seeds 1 and 2 reproduce the references, and seed 3 gives 50.996.
   - That is below the paper's 3-seed-mean baseline, so sigma is 0.110 from seed luck alone (+0.010).
5. **Anchors.**
   - Perplexity 1 is unreachable. Even dense quality (10.86) maps to sigma 0.46, so the realistic ceiling is about 0.45.
   - Ordering within the task is fine, but OWL's sigma range is roughly 3x Soup's, which shapes cross-task weighting.
   - The case pages' "fixed start" (10.86, dense) is gate-ineligible.
6. **Noise and best-of-3.**
   - Calibration-seed spread is about 1-3% of perplexity, roughly 0.007 sigma. The top 7 configurations (12.96-13.85) are not separable with one run per cell.
   - In 13 of 28 scored cells the official checkpoint is not the last, but the mean gain is only +0.0018 sigma and no outcome flips.
7. **Minor issues.**
   - `instruction.md:63` says to score `/out/probe-name/pruned`; `solution/run.sh:20` writes `.../work/pruned`.
   - On two pages (sonnet-5/max, terra/medium) the structured "Protocol exposure: Confirmed" contradicts the page's own prose.
