# AI4AI-Bench (Einsia / Navers Lab): benchmark audit

| | |
| --- | --- |
| **Reviewed** | 2026-10-29 |
| **Benchmark creators** | Yizhe Chi, Wenyi Li, Deyao Hong, Xiaoqiu Wang, Mingju Gao, Kaisen Yang, Bingxiang He, Youjie Zheng, Calvin Xiao, Qinhuai Na (Einsia / Navers Lab, Tsinghua) |
| **Version under review** | arXiv [2608.20318](https://arxiv.org/abs/2608.20318) v1 (2026-08-20). Repo [`Einsia/AI4AI-Bench`](https://github.com/Einsia/AI4AI-Bench) at `5ced1e2` (2026-08-21). The 290 case pages at [lab.einsia.ai/ai4ai/trajectories](https://lab.einsia.ai/ai4ai/trajectories/) as fetched 2026-10-29. |
| **Verdict** | **Flawed** |
| **Rubric** | [Epoch Rubric v1 + extensions](../../methodology/rubric.md) |
| **Review depth** | Full: all 10 tasks (task contract, instruction, phase mounts, proxy and final evaluators) and all 290 cells (case pages) |

Rendered page in Epoch's review format: [review.html](review.html).

## Summary

AI4AI-Bench asks whether a coding agent can improve an existing AI training recipe.

- **Tasks:** ten tasks span diffusion, alignment, reasoning distillation, unlearning, pruning, RL, reward modelling,
  graph diffusion and model merging.
- **Run structure:** the agent explores for 4 hours with a visible proxy evaluator. Only its source patch is replayed
  in a fresh 12-hour Formal run, and up to three checkpoints go to a frozen final evaluator.
- **Scoring:** each cell's best checkpoint is mapped to a scale σ in [0, 1], where 0.1 is the repository's shipped
  recipe and 1 is a declared "optimum".
- **Configurations:** six systems at several reasoning efforts give 29 configurations, one run per cell, 290 cells in
  all.
- **Headline:** the paper reports a mean of 0.166, with Claude Opus 5 the best system at 0.250.

The task code is public and unusually well documented, which made a full review possible. But **4 of the 10 tasks
(40%) have confirmed scoring defects that change scores:**

- **RAGEN Sokoban:** the "held-out" board seed is upstream RAGEN's default validation seed, sitting in code the agent
  edits. Training overlaps most of the final bank, and five cells score a perfect 512/512.
- **DDPO:** the aesthetic scorer has none of the alignment or diversity gates its README promises. Its "score-only"
  seed is hard-coded in readable harness code.
- **NPO:** the paper's optimum (2.08) is above the metric's maximum (1.0).
- **BTRM:** the baseline sits inside seed noise of about 8.5 points.

Across the benchmark, **each cell's checkpoint is chosen on the test metric**, and in 163 of 271 completed cells the
reported checkpoint is not the last one. We therefore designate the benchmark as **Flawed**.

The headline ranking is also fragile:

- **Opus 5's lead depends on aggregation.** It is #1 in 98% of task-bootstrap replicates under the paper's
  aggregation, but #3 when systems are compared at maximum effort.
- **Corrections reorder the middle.** With the confirmed corrections applied, Kimi K3 moves from #3 to #2 and Opus 5's
  lead shrinks from 0.076 to 0.020.
- **No research progress was found.** No cell was judged research. 49% of cells gained nothing over the shipped recipe.

## Methodology

AI4AI-Bench has 10 tasks, so we assessed all of them, as the rubric requires for benchmarks of 50 tasks or fewer. For
each task, reviewers read the following and checked hidden-data integrity, scorer correctness, the paper's anchor
values, noise and checkpoint selection:

- `task.toml` and `instruction.md`
- `declaration.py`, which sets what each phase mounts
- the proxy and final evaluators
- the shipped solution and the orchestrator

For each of the 290 cells, they read the benchmark's own case page. Each page gives:

- the submitted method
- the exploration and replay evidence
- every checkpoint's final score
- the benchmark team's audit fields

Each cell was classified as research, engineering, grey area, reward hack or no gain
([REVIEW_PROTOCOL.md](REVIEW_PROTOCOL.md)).

AI4AI-Bench publishes neither raw agent logs nor patch contents. The paper says it releases "every scored
submission", but we found only patch IDs. So cell-level judgements rest on the case pages, and task-level judgements
rest on the code.

We parsed all 290 case pages ([`scripts/parse_cases.py`](scripts/parse_cases.py)) and recomputed σ from the paper's
anchors ([`scripts/score.py`](scripts/score.py)). The recomputation reproduces the paper's per-configuration means:
0.165 overall against the paper's 0.166, Opus 5 medium 0.287 against 0.288, and GPT-5.6 Luna medium 0.124 against
0.124. We then tested the ranking under alternative selection rules, aggregations and corrections
([`scripts/ranking.py`](scripts/ranking.py)).

Model reviewers made the per-task calls. The lead auditor re-verified every counted defect in the code; reviewer
overrides are in [`data/adjudication.json`](data/adjudication.json). A task counts toward the threshold only for a
confirmed defect that changes scores materially. Defects worth 0.006 σ per cell or less are logged as minor.

## Representative errors

- **A held-out seed that is not hidden (RAGEN Sokoban).**
  - `declaration.py:50` sets `FINAL_ENVIRONMENT_SEED = 123`, with the comment "The final seed stays host-side so
    exploration cannot reconstruct the held-out boards". The grader calls the seed "the entire withheld quantity".
  - Upstream RAGEN at `20daedc4` ships `config/base.yaml` with `seed: val: 123`. That tree is copied into the agent's
    editable `/workspace/ragen` (`environment/Dockerfile:95`).
  - Board generation is deterministic (`es_manager.py:115-117`), so the exact final bank, with solutions, can be
    rebuilt inside the container. No agent was seen doing so.
  - Separately, the 6×6 one-box board space is small enough that formal training on solver demonstrations covered
    243–490 of the 512 final boards in every cell where overlap was measured.
  - The proxy summary hard-codes `proxy_final_overlap_fraction: 0.0` (`fast_eval.py:236`), yet 7 of its boards are in
    the final.
  - Five cells score 512/512 (σ = 1): Opus 5 low, medium and high, and GPT-5.6 Sol high and max. One of them reached
    it with pure supervised imitation of the in-container BFS solver, so σ = 1 does not require the RL the task is
    about.
- **Scorer optimisation scored as success, with a promised gate missing (DDPO).** The task README says the final
  metric is "mean aesthetic score with alignment/diversity gates". The evaluator says "the original DDPO benchmark
  has no alignment/diversity guard" (`harness/final_eval.py:233`).
  - Seven cells back-propagate through the frozen aesthetic scorer, and one more over-trains PPO. Their images
    collapse in prompt alignment and diversity, yet they score 6.8–17.7 against a shipped 5.53 and supply 94% of the
    task's above-baseline σ.
  - Every DDPO case page calls its result "Metric-qualified".
  - The "score-only" final seed (`generation_seed: 20269702`, `assets.lock.yaml:138`) is also hard-coded in the mock
    path of `/opt/harness/final_eval.py:261,285`, which the agent can read. 18 trajectories saw it; none used it.
- **An optimum the metric cannot reach (NPO).** The balanced unlearning score is the harmonic mean of two values
  clipped to [0, 1] (`harness/final_eval.py:192-221`), so it cannot exceed 1.0. The paper anchors the optimum at
  2.08, which caps σ at 0.185. The six cells that reach the true maximum are scored as having covered 7.5% of the
  distance to the optimum, and all 19 improved cells are under-scored about four-fold.
- **A baseline inside the noise (BTRM).**
  - The task calls its own reference "seed-sensitive … a single-run reference" (74.569, `instruction.md:30-37`); the
    paper uses 74.9.
  - Replays of the unchanged recipe score 65.4–73.95, so most of "21 of 29 cells below baseline" is noise.
  - The official score also includes the 512 proxy pairs the agent saw during exploration (`final_eval.py:337-341`).
- **Checkpoint chosen on the test set (all tasks).** `orchestrator/final_score.py:148` reports the best of up to three
  checkpoints on the final metric.
  - In 163 of 271 completed cells, the reported checkpoint is not the last.
  - Several agents published three independent seeds as their three checkpoints, making the result a max-of-3 over
    seeds.
  - Mean σ falls from 0.165 to 0.158 with the last checkpoint, and 21 cells flip between beating and missing the
    baseline.

Outside the counted defects:

- **Anchors that disagree with the tasks.** The paper's baseline differs from the task's own stated reference in 7 of
  10 tasks:
  - DDPO 5.84 vs 5.53
  - DiGress 65.8 vs 69.57
  - DPO 0.424 vs 0.509 stated (and 0.39–0.44 replayed)
  - OPD 0.436 vs 0.427
  - OpenR1 0.127 vs 0.123
  - BTRM 74.9 vs 74.57
  - Model Soup 0.686 vs a start of 0.687

  Several optima are unreachable (perplexity 1, NLL 0, 100% ImageNetV2), which compresses whole tasks into σ bands
  only 0.03 wide.
- **An unvalidated LLM judge.** OPD's final grader sends about 1,100 of each checkpoint's 1,920 samples to
  CompassVerifier-3B, with the question left empty (`final_eval.py:412`).
- **Published OpenR1 numbers cannot be reproduced** from the public scorer, which is greedy with n = 1, scored out of
  175. The published scores use n = 10, out of 1,750.

## Errors

| Task | Error type | Evidence |
| --- | --- | --- |
| `ragen_sokoban_grpo` | FP (+ CONSTRUCT) | Final seed 123 = upstream `seed.val` in `/workspace/ragen`; training covers 243–490/512 final boards; 5 cells at 512/512 |
| `ddpo_sd15_aesthetic` | FP | Promised alignment/diversity gates absent (`final_eval.py:233`); score-only seed in readable source (`final_eval.py:261`) |
| `openunlearning_tofu_npo_llama3p2_1b` | FN | Metric ≤ 1.0 (`final_eval.py:192-221`) vs optimum 2.08; σ capped at 0.185 |
| `ultrafeedback_bt_rm_rewardbench` | FN | Reference "seed-sensitive" (`instruction.md:30`); replays 65.4–73.95 vs anchor 74.9; seen rows scored |
| *(all tasks)* | FP (selection) | Best of 3 checkpoints on the final metric (`final_score.py:148`) |

**Total:** 4 of 10 tasks (40%). The Flawed threshold is 20%.

- The two tasks whose hidden final data is exposed inside the container, RAGEN and DDPO, give 2 of 10 (20%) on their
  own.
- Logged but not counted:
  - DiGress: best-of-3 noise above the baseline
  - OWL: platform losses
  - OpenR1: anchor
  - OPD: noise
  - DPO: declared proxy overlap
  - Model Soup: declared proxy inside the final

### Sensitivity of the ranking

| Aggregation | System order (mean σ) |
| --- | --- |
| Published: mean over all effort levels, best of 3 | Opus 5 (0.249) > Sol (0.190) > Kimi K3 (0.173) > Sonnet 5 (0.145) > Terra (0.135) > Luna (0.116) |
| Last checkpoint instead of best of 3 | Opus 5 (0.240) > Sol (0.184) > Kimi K3 (0.159) > Sonnet 5 (0.142) > Terra (0.127) > Luna (0.110) |
| **Max effort only** (Kimi K3 ran only at max) | **Sol (0.244) > Terra (0.228) > Opus 5 (0.222)** > Kimi K3 (0.173) > Sonnet 5 (0.163) > Luna (0.138) |
| Each system's best configuration | Opus 5 (0.287) > Sol (0.244) > Terra (0.228) > Sonnet 5 (0.216) > Kimi K3 (0.173) > Luna (0.147) |
| Drop RAGEN (contaminated) | Opus 5 (0.203) > **Kimi K3 (0.180) > Sol (0.147)** > Sonnet 5 (0.133) > Luna (0.126) > Terra (0.121) |
| **All confirmed corrections**: NPO optimum 1.0; task-stated BTRM/OpenR1 baselines; DDPO degenerate cells at baseline; RAGEN dropped | Opus 5 (0.257) > **Kimi K3 (0.237) > Sol (0.208)** > Sonnet 5 (0.181) > Luna (0.161) > Terra (0.161) |
| Task bootstrap of the published order (2,000 replicates) | Opus 5 #1 in 98%; Sol #2 in 59%; Kimi K3 #2 in 39% |

Effort curves are non-monotone (Opus 5 scores 0.273, 0.287, 0.277, 0.188 and 0.222 from low to max), and each cell is
one run. So differences of about 0.1 σ between configurations cannot be separated from run-to-run noise. Full output
is in [`data/ranking.md`](data/ranking.md) and [`data/rescoring.md`](data/rescoring.md).

## Rubric

### 1. Reviewability

**Status:** Partial (proceed to 2)

**Public:**

- Every task's contract, instruction, phase mounts, proxy and final evaluator, and orchestrator. The paper says it
  releases "the task suite, the evaluators and every scored submission".
- All 290 case pages, with checkpoint scores and the benchmark's own per-cell audit.

**Not public:**

- Patch contents: only patch IDs, despite the paper's claim.
- Raw agent logs: the case pages are "redacted" summaries written "without reproducing raw shell-event logs".
- The scorer that produced the published OpenR1 numbers.
- Max output tokens and context settings for the harnesses.

### 2. Scoring

| Item | Status | Notes |
| --- | --- | --- |
| Task validity and scorer accuracy | **Flag** | 4/10 tasks (40%) affected, plus best-of-3 test-set selection in every task; see Errors |
| Benchmark consistency | Pass | OpenR1's final protocol changed on 2026-08-20 and all cells were rescored. Claude cells were replayed on a retry-hotfix commit under a documented waiver. One DiGress Formal run was voided for GPU sharing and re-run. |
| Elicitation | Pass | Each system runs in a modern vendor CLI with a fixed 4 h + 12 h budget. Codex runs have no continuation: 18 of the 19 zero-scored cells are GPT-5.6 runs, three of them early exits within 100 s with about 4 h left. Kimi K3 runs in Claude Code, not its own harness. |
| Bias in evaluation setup | **Flag** | Systems are compared by averaging over unequal sets of effort levels. GPT-5.6 includes `none`; Claude starts at `low`; Kimi K3 has only `max`. That choice decides the headline: Opus 5 is #1 under the paper's aggregation but #3 at maximum effort, and Kimi K3's single max-effort configuration is compared against other systems' averages that include deliberately weak settings. |

### 3. Evaluation quality

| Question | Status | Notes |
| --- | --- | --- |
| Elicitation and resource adequacy | Sufficient | 4 h Explore and 12 h Formal on one B300; two tasks do no training |
| Scaffold fairness | Model-specific scaffolds | Codex for GPT-5.6, Claude Code for Claude and Kimi K3 |
| Contamination | Final data are public benchmarks: AIME 24/25, LiveCodeBench v6, IFEval, RewardBench, WikiText-2, QM9, ImageNetV2, TOFU | Mounted only at scoring, with no network. The leaks found are inside the container (RAGEN, DDPO). |
| Human completability | Not established | Shipped recipes give the 0.1 anchor; "optima" are mostly theoretical |
| Score range | Floor 0, ceiling 1 by construction | Unreachable optima confine five tasks to σ bands 0.03–0.05 wide; one task (RAGEN) reaches 1.0 by imitation |
| Statistical adequacy | 1 run per cell | No seed replicates; per-checkpoint SEs are descriptive. Several tasks' gaps sit inside noise: OPD SE 0.052 on 60 questions, BTRM seed spread about 8.5 points. |
| Construct validity | Partially measures stated capabilities | Realistic research-repository tasks, but the score rewards optimising evaluators (DDPO), imitation instead of RL (RAGEN) and seed luck (BTRM, OPD). The paper's own reading agrees: "few changed how the model learns". |

### Extension: research vs. benchmark gaming

Every cell was classified from its case page ([`data/summary.md`](data/summary.md)):

| Classification | Cells | Share |
| --- | --- | --- |
| Research: a transferable idea | 0 | 0% |
| Engineering: legitimate, standard techniques and tuning | 137 | 47% |
| Grey area: exploits the benchmark rather than the problem | 10 | 3% |
| Reward hack: breaks an explicit rule | 0 | 0% |
| No gain over the shipped recipe | 143 | 49% |

| Model | Cells | Engineering | Grey area | No gain | False positives | False negatives |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Opus 5 | 50 | 25 | 7 | 18 | 9 | 5 |
| GPT-5.6 Sol | 60 | 32 | 1 | 27 | 3 | 5 |
| Kimi K3 | 10 | 5 | 1 | 4 | 1 | 1 |
| Claude Sonnet 5 | 50 | 23 | 0 | 27 | 1 | 4 |
| GPT-5.6 Terra | 60 | 26 | 1 | 33 | 5 | 3 |
| GPT-5.6 Luna | 60 | 26 | 0 | 34 | 1 | 3 |

- **Nothing new was found.** No cell was judged research or plausibly novel. The improvements that work are known
  techniques applied well:
  - SparseGPT in place of Wanda
  - solver-imitation SFT before RL
  - pathwise gradients through a differentiable reward
  - LoRA weight soups
  - synthetic constraint data for IFEval
- **Opus 5's grey-area cells are mostly DDPO scorer optimisation.** Five of its seven are DDPO cells that
  back-propagated through the aesthetic scorer; the other two train on synthetic IFEval-style constraints. The eight
  DDPO false positives are five Opus 5 runs, one Kimi K3 run and two Sol runs. Optimising the scorer directly is
  allowed by the instruction, but the images collapse in alignment and diversity.
- **About half of all cells did no better than the shipped recipe.** On OPD all 29 are within noise of it.

### Per-task verdicts

| Task | Scoring | Key finding |
| --- | --- | --- |
| [RAGEN Sokoban GRPO](tasks/ragen_sokoban_grpo.md) | **FP** | Final seed is upstream's default; training covers most final boards; 512/512 by imitation |
| [DDPO SD1.5 aesthetic](tasks/ddpo_sd15_aesthetic.md) | **FP** | No gates; scorer optimisation gives 94% of above-baseline σ; seed in readable source |
| [NPO TOFU unlearning](tasks/openunlearning_tofu_npo_llama3p2_1b.md) | **FN** | Optimum 2.08 above a metric capped at 1.0 |
| [BTRM RewardBench](tasks/ultrafeedback_bt_rm_rewardbench.md) | **FN** | Baseline inside about 8.5-point seed noise; seen rows scored |
| [OpenR1 LiveCodeBench](tasks/openr1_code_livecodebench.md) | minor | Anchor above every shipped replay; public scorer cannot reproduce published numbers |
| [OPD AIME](tasks/opd_math_1p5b.md) | minor | All cells within noise of the baseline; unvalidated LLM-judge fallback |
| [DiGress QM9](tasks/digress_qm9_graph_diffusion.md) | minor | Unchanged recipe beats the anchor by best-of-3; σ confined to 0.094–0.128 |
| [DPO IFEval](tasks/dpo_preference_alignment.md) | minor | Declared 31% proxy overlap; stale shipped reference |
| [OWL/Wanda pruning](tasks/owl_wanda_opt6p7b_70pct.md) | minor | Sound task; two platform losses; site shows negative perplexities |
| [Model Soup ImageNetV2](tasks/model_soup_clip_imagenetv2.md) | minor | Proxy inside the final by design; σ confined to 0.117–0.142 |

## Limitations

- **No raw logs or patches.** Cell-level calls rely on the benchmark's own case pages, which are summaries written by
  the benchmark team. Where a page's claim can be checked against the code, we checked it.
- **The anchor convention for infinite uninformative points** (DiGress, OWL) follows the paper's description. The
  recomputed means match the paper's to within 0.002.
- **The effect of the RAGEN seed exposure on observed scores is unproven.** No agent was seen using the seed, and GPT-5.6
  Sol max's models also solved final boards absent from their training data.
- **Model review.** Per-task calls were made by model reviewers. Every counted defect was re-verified in code by the
  lead auditor, and the line between research and engineering is a judgement call.

## Disclaimer

This is a full review of all 10 tasks and 290 cells. Our open questions:

1. Where are the "scored submissions" (patch contents) the paper says are released?
2. Why is RAGEN's withheld final seed (123) the upstream default validation seed?
3. Why does the DDPO README promise alignment and diversity gates that the evaluator does not implement?
4. How were the Table 2 baselines and optima chosen? NPO's 2.08 exceeds its metric's range, and 7 of 10 baselines
   differ from the tasks' own references.
5. Which scorer produced the published OpenR1 numbers?
6. Why is the reported checkpoint chosen on the final metric rather than pre-committed?

This review uses the format and rubric of Epoch AI's Benchmark Reviews. It is an independent review and is not
produced or endorsed by Epoch AI.

## Notes

1. Paper: <https://arxiv.org/abs/2608.20318> (v1, 2026-08-20). Repository:
   <https://github.com/Einsia/AI4AI-Bench> at `5ced1e2eb1882baf52e6d928f9257006aa71968c`. Case pages:
   <https://lab.einsia.ai/ai4ai/trajectories/>.
2. Upstream RAGEN: <https://github.com/RAGEN-AI/RAGEN> at `20daedc4`, `config/base.yaml` lines 8–10 (`seed: train:
   10000, val: 123`).
3. The reproduction of the paper's Table 3 per-configuration means is in [`data/rescoring.md`](data/rescoring.md). One
   case page (`codex__owl_wanda_opt6p7b_70pct__gpt-5.6-luna__medium`) displays perplexities with a flipped sign; the
   magnitude is used.

## Reproduce

```bash
sh scripts/fetch.sh /tmp/ai4ai                          # repo at the audited commit + 290 case pages; parses and rescores
python3 -I scripts/summarize.py data/task_reviews data/adjudication.json > data/summary.md
```
