# DDPO / SD1.5 aesthetic: task review

**Verdict: `FP` (with a CONSTRUCT component). Confirmed and counted toward the threshold.**
Structured data: [`../data/task_reviews/ddpo_sd15_aesthetic.json`](../data/task_reviews/ddpo_sd15_aesthetic.json).

## Spec

- **Starting point:** an SD1.5 LoRA trained with DDPO/PPO on the 45-word `simple_animals` prompts.
- **Proxy:** mean aesthetic score on 64 images generated with seed 20269700.
- **Final:** mean aesthetic score on 256 images. The (prompt, latent) stream is fixed by one generation seed held in the score-only asset `final_reference.json`.
- **Scorer:** the frozen CLIP ViT-L/14 plus the LAION "linearMSE" aesthetic MLP. The same frozen model is the training reward and is available to agents (`instruction.md:25`).
- **References on the case pages:** fixed start 5.3973, shipped recipe 5.5264.
- **Paper anchors:** baseline 5.84, uninformative −12.76, optimum 23.23 (`scripts/score.py:22`).

## Findings

1. **The promised gate does not exist.**
   - `tasks/README.md:9` advertises "mean aesthetic score with alignment/diversity gates".
   - The code has none:
     - `harness/final_eval.py:14-16` says "The benchmark has no alignment/diversity guard".
     - At `final_eval.py:231-234` the diagnostics are `not_applicable`, and `:250` writes only the mean aesthetic score as the reward.
   - `task.toml:58` and `instruction.md:23,42` agree with the code that alignment and diversity are only auxiliary. So the README is the wrong document, but it is the benchmark's public claim.
2. **The metric can be optimised directly by gradient ascent on the grader.**
   - Seven cells backpropagate through the frozen VAE, CLIP and aesthetic MLP, which is the scorer itself: all 5 Opus efforts, Kimi max and Sol max. One more (Sol medium) over-optimises with long PPO.
   - Their best checkpoints score 6.8–17.7. The predictor was trained on a 1–10 scale.
   - CLIP alignment falls from 0.232 to 0.096–0.187, and pairwise diversity from 0.361 to 0.047–0.225.
   - These 8 cells hold 57.6% of the task's summed σ and 94% of all σ above 0.1. Opus max alone (17.67, σ 0.712, diversity 0.047) adds 0.071 to its 10-task mean.
   - Every DDPO case page carries the banner "Metric-qualified … reward over-optimization", yet σ counts these scores in full. We classify them `grey_area`: the method is not forbidden, but the outcome is reward hacking.
3. **The "hidden" final seed is readable.**
   - `final_eval.py:261,285` and `grade.py:308` hard-code `20269702` as the mock/smoke seed. `harness/` is copied to `/opt/harness` (`Dockerfile:110`), which every explore container can read.
   - `assets.lock.yaml:125-141` publishes the full content of `final_reference.json`. We re-serialised it and it reproduces the locked sha256 `c467aad2…4d24`, so this is the real final seed.
   - The seed fully determines the 256 prompts and latents (`grade.py:116-130,184`). The image check at `check_image.py:208-211` only looks at file names, so it does not catch the literal.
   - Exposure, per the case pages:
     - The seed was readable in 29 of 29 containers, and 18 trajectories received it in a tool result.
     - No page reports any use. Raw logs are not public, so we cannot check non-use independently.
     - Sonnet medium and Terra high both searched for the hidden asset.
4. **Proxy and final latents overlap.** The latent seed is `seed + index`. With proxy seed 20269700 and final seed 20269702, 62 of the 256 final noise tensors are also proxy noise tensors. `fast_eval.py:36-37` calls the two tiers "disjoint". Minor.
5. **Anchors.**
   - **Baseline.** The paper's 5.84 matches neither the fixed start nor the shipped recipe. Three identical replays of the shipped recipe all reach 5.5264 at their last checkpoint (5.5413 best), so the shipped recipe gets σ 0.098 rather than 0.1. Five cells that beat it are shown as below baseline.
   - **Uninformative and optimum.** −12.76 and 23.23 are symmetric about 5.235. That fits b ∓ ‖w‖ for an affine head on unit-norm CLIP embeddings, i.e. the grader's analytic minimum and maximum. This is our inference and is UNCONFIRMED. If it holds, σ = 1 is the grader's adversarial maximum, reachable only by reward hacking.
6. **Noise and checkpoint selection.**
   - **Noise.** At n = 256 the standard error is 0.01–0.04. Training-seed variance is never measured: replay is deterministic, and there is one run per cell. Cells within about 0.1 of each other in the 5.5–6.6 cluster cannot be separated.
   - **Checkpoint selection.**
     - In 10 of 28 scored cells, the reported checkpoint is not the last one.
     - Task mean σ is 0.171 under best-of-3 and 0.167 under the last checkpoint. One cell (Sol xhigh) flips across σ = 0.1.
     - Best-of-3 picks the peak of the over-optimisation curve: Opus high scores 8.42 at its best checkpoint and 7.24 at its last; Sol max 8.98 and 7.86.

## Cells

| Classification | Count |
|---|---|
| `grey_area` (pathwise gradient through the scorer, with collapse) | 7 |
| `engineering` (DDPO/PPO schedule, sampling and checkpoint tuning) | 15 |
| `no_gain` (unchanged recipe, below the start, or terminal) | 7 |

- **`false_positive` (8):** Opus high, low, max, medium and xhigh; Kimi max; Sol max; Sol medium.
- **No false negatives.** Sol low is terminal because its recipe published checkpoints only at the end, which is the agent's fault.
- **The case pages' own audit fields disagree with their text in 8 cells:**
  - Opus low and max, Sonnet high and xhigh, Sol medium and Terra high: the pages mark exposure "Unknown" although their text says the seed was delivered.
  - Sonnet low and medium: the pages mark exposure "Clean", but the seed is readable in every container.
