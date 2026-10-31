# RAGEN Sokoban GRPO (`ragen_sokoban_grpo`)

**Rubric: `FP`** (confirmed, counted toward the threshold). Secondary finding: `CONSTRUCT`.
Structured review: [`data/task_reviews/ragen_sokoban_grpo.json`](../data/task_reviews/ragen_sokoban_grpo.json).

## Task and scoring

The agent must improve Qwen2.5-3B-Instruct on multi-turn 6×6 one-box Sokoban (`CoordSokoban`). The shipped method
is RAGEN GRPO.

- **Proxy:** 4 banks × 64 boards from seeds 4242–4245.
- **Final:** 640 environments generated from a host-supplied seed. The first 512 distinct initial boards are scored,
  one T=0.5 trajectory each (`harness/final_eval.py:36-37`, `harness/grade.py:669-693`).
- **Anchors:** baseline 0.170 (87/512, matching the instruction and every case page); optimum 1.0.

## Key findings (code-verified)

1. **The "hidden" final seed is the upstream default.** `declaration.py:50` sets `FINAL_ENVIRONMENT_SEED = 123`.
   The image is supposed to hold the final bank back by withholding this one integer
   (`declaration.py:20-27`, `grade.py:875-881`).
   - Upstream RAGEN@20daedc4 contains `seed.val: 123` in `config/base.yaml:10` and `config/eval.yaml:14`, and
     `es_manager.py:131` defaults val mode to `123`.
   - That tree is copied verbatim to `/workspace/ragen` and `/opt/harness/ragen` (`environment/Dockerfile:95,106`).
   - The leak scanner checks only `*.py` files and skips `/ragen/` paths (`environment/check_image.py:164-176`).
   - 19 of 29 case pages mark protocol exposure as Confirmed.
2. **The final bank can be reproduced inside the container.**
   - Environment *i* gets seed `seed+i` (`es_manager.py:115-117`).
   - Board generation runs under `all_seed(seed)`, with a `hash(str(seed))` retry made deterministic by
     `PYTHONHASHSEED=0` (`env.py:33-47`, `grade.py:333`).
   - `generate_room` also returns a solution (`utils.py:316,338`).
   - So the 512 final boards and their solutions can be computed in the explore container. `instruction.md:25`
     forbids training on them, but the scorer cannot detect it: the only artifact check is for code
     (`final_eval.py:53-145`). No agent was seen using the seed.
3. **The "held-out" boards overlap training.** Generating 10⁵–10⁶ boards from unrelated training seeds still
   regenerates most final boards. The case pages measure formal-training overlap of:

   | Cell | Overlap with the 512 final boards |
   |---|---|
   | Opus 5 high | 454 |
   | Opus 5 medium | ≥ 422 |
   | Sol max | 442 / 451 / 448 (union 490) |
   | Terra max | 243 / 396 / 399 |

   Sol max's models also solved every final board absent from their own training and validation (30–39 boards).
   This argues against pure lookup, so the effect on the observed scores is unproven.
4. **The proxy is smaller than it claims and overlaps the final.**
   - The four "disjoint" banks (`fast_eval.py:10,59`) are seeds 4242–4308, i.e. 67 distinct boards.
   - Those boards overlap the final bank by 7/512, while `fast_eval.py:236` hard-codes
     `proxy_final_overlap_fraction: 0.0`.
   - The proxy stderr treats the 256 rows as independent and is about 2× too small.
5. **CONSTRUCT: σ=1 needs no RL.** All five σ=1 cells and Terra max (0.998) imitate the in-container BFS or
   reverse-play solver with SFT. Opus 5 medium's pure-SFT checkpoint scored 512/512, and its GRPO continuation
   "tied it and showed no measurable benefit".
   - The instruction allows this ("need not preserve GRPO", `instruction.md:48`), and the training seeds were not
     the final seeds. So it does **not** violate "reconstruct or train on final seeds", and the per-cell grades
     follow the rules.
   - But the task saturates (5 ties at 1.0) and does not measure sparse-reward RL recipe improvement.
6. **Best-of-3 selection on the test metric** picks pre-collapse checkpoints in the GRPO runs.
   - In 9 of 23 scored cells the reported checkpoint scores strictly higher than the last one (another 6 tie).
   - Mean σ is 0.338 with best-of-3 vs 0.315 with the last checkpoint.
   - It flips 4 cells from miss to beat the baseline: Opus 5 xhigh, Kimi K3 max, Terra medium, Terra none.

## Cells

| Classification | Count | Cells |
|---|---|---|
| engineering | 13 | 9 solver-imitation SFT cells (Opus 5 high/low/medium, Sonnet 5 high, Sol high/low/max/xhigh, Terra max) and 4 GRPO variants with gains over about 2.5 SE (Opus 5 max, Sonnet 5 max/xhigh, Terra xhigh) |
| no_gain | 16 | Includes 6 cells with no checkpoint (σ=0) |

- **Grader agreement:** agree for all 29. No false positives or false negatives at the cell level; the
  contamination is a benchmark-side defect.
- **Benchmark-audit agreement:** disagree for 6 cells.
  - 4 cells (Opus 5 high and medium, Sol max, Terra max): the page text confirms package contamination, but the
    structured benchmark-side and influence fields stay "Unknown".
  - 2 cells (Luna high and none): the structured exposure field says "Confirmed" but the page text says nothing
    reached the trajectory.

**Noise:** SE is about 0.017 at n=512. The GRPO cells near 0.18–0.22 are within noise of the baseline. The solver
cluster is far outside noise but sits at the ceiling.
