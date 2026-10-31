# NPO (TOFU unlearning, Llama-3.2-1B): `openunlearning_tofu_npo_llama3p2_1b`

**Rubric code: `FN`** (confirmed, counted toward threshold). Structured review:
[`../data/task_reviews/openunlearning_tofu_npo_llama3p2_1b.json`](../data/task_reviews/openunlearning_tofu_npo_llama3p2_1b.json).

## Main finding: the optimum anchor is unreachable

The headline `balanced_unlearning_score` combines two terms by harmonic mean:

- forgetting progress, clip₀₁((ES_start − ES_cand)/(ES_start − ES_retain90))
- utility retention, clip₀₁(MU_cand/MU_start)

Sources: `harness/final_eval.py:192-221`, and the formula string at `:470-472`. Because both terms are clipped, the score
can never exceed **1.0**.

The paper's anchors are baseline 0.887, uninformative 0 and optimum **2.08** (`scripts/score.py:24`). Under these
anchors the highest σ any cell can reach is 0.1 + 0.9·(1 − 0.887)/(2.08 − 0.887) = **0.185**.

- Six cells reach the composite's true ceiling of 1.0 (claude-opus-5 high/max/medium/xhigh, gpt-5.6-sol xhigh) and
  get σ = 0.185.
- With optimum 1.0, a 0.95 cell would get σ ≈ 0.60 instead of 0.148, so every clearly improved cell is under-scored
  by about 4×.

## Other checks

- **Baseline.** 0.887 is the composite computed from the shipped components in `instruction.md:35-36`. The case pages
  give no scalar start or shipped value.
- **Noise lets a null patch pass.** gpt-5.6-terra/xhigh's only hunk was skipped, so its formal run replayed the
  shipped recipe. It scored **0.9228** (σ 0.127 > 0.1). Running the same recipe twice moves the composite by about
  0.036.
- **Saturation.** Forgetting below retain90's Extraction earns nothing, and neither does MU above the start model's.
  The top of the table is tied at 1.0.
- **Gaming.** Destroying the model scores 0 (MU → 0). A refusal format on forget questions is a legitimate unlearning
  strategy. One latent surface: the candidate's tokenizer and chat template are loaded unhashed by the scorer
  (`final_eval.py:284-285, 377-380`). No cell used it.
- **Proxy.** `tasks/README.md:20-22` and `instruction.md:25` call the visible metric a "training diagnostic". It
  rewards forget-NLL growth without bound, on 24 train rows (`fast_eval.py:137-138`), while the final caps
  forgetting. Most agents built their own Extraction/ROUGE proxies instead.
- **Hidden data.** The retain90 anchor and final data are mounted only in the score phase (`declaration.py:52-78`),
  and there is no network. Overlap between the forget/retain rows and the training data is inherent to TOFU.
- **Checkpoint selection.** In 17 of 28 scored cells the reported checkpoint is not the last. This adds +0.006 σ to
  the task mean and flips one cell (terra/medium).

## Cells (29)

| Classification | Cells |
|---|---|
| engineering | 22 |
| no_gain | 7 |

| Grader agreement | Cells | Which |
|---|---|---|
| false_negative | 19 | Above-baseline cells clearly beyond replay noise, under-scored by the 2.08 anchor |
| false_positive | 2 | terra/xhigh (null replay, 0.9228); terra/medium (0.9045, below the null replay) |
| unclear | 3 | sonnet/max, luna/max, luna/none (inside noise) |
| agree | 5 | |

No reward hacks were found.
