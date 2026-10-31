# Noisy Game-Tree Pruning

Raw id: `pushing-out-v2` (Algorithm optimisation, CPU only)

## The task

The agent must rewrite `choose_move(root, spec)` so it finds the best root move in random noisy game trees while revealing fewer nodes.

- **Accuracy bars:** at least 99% overall and at least 98.5% in each of four noise groups.
- **Time limits:** 5 s per search, and a 0.9 s average per tree per shard. The shard budget also covers tree generation and the baseline search.
- **Allowed:** generating practice trees.
- **The prompt warns:** "It is checked on fresh private trees, so keep a margin."

## How scoring works

- **Cost:** the geometric mean over the 4 bins of mean revealed nodes.
- **Reward:** `baseline/candidate − 1`. The private baseline is fixed at 1297.0.
- **Invalid (valid=0)** means one of:
  - accuracy below 99% overall or below 98.5% in any bin (`report['valid'] = int(candidate_accuracy_ok)`);
  - a crash, a protocol error, a search over 5 s, or a shard over its time budget.
- **Public vs private trees:**
  - Public is a fixed set: `master_seed 2026`, 2,000 trees per bin. It can be reproduced offline with `make_cases(2026, …)`.
  - Private is 16,000 fresh trees, 4,000 per bin.

## Results

| Model | Trial | Official | Final public check | Verdict |
|---|---|---|---|---|
| Claude Fable 5.1 | 5gC2NsY | **2.08** | 419.9 nodes, 99.35% (fresh 20k/bin: 417–420, ≥99.19% per bin) | research, agree |
| GPT-6 Astra | MEwAPLH | 1.88 (no breakdown) | 99.61%, min bin 99.30% | research, agree |
| GPT-6 Astra | HYcHHWh | 1.65 (no breakdown) | 99.40%, min bin 99.00%, max 3.4 s | research, agree |
| Gemini 4 Argon | 3J9vt7s | 1.62 | 99.21%, min bin 99.00% | research, agree (thin margin) |
| Claude Fable 5.1 | WFDwh5f | 0.97 | 99.70% (10 fresh seeds: 99.57%) | research, agree |
| Gemini 3.8 Flash | TZKDZCh | 0.47 | 99.48% | engineering, agree |
| Kimi K3 | T6xcqyV | 0.45 | 99.22%, min bin 98.75% | engineering, agree |
| Kimi K3 | rzvBsWz | 0.35 | 99.54% | engineering, agree |
| Gemini 3.8 Flash | xzuJjnb | 0.23 | 99.49%, min bin 98.90% | engineering, agree |
| Gemini 4 Argon | ahhVHDn | invalid | 99.26%, min bin 98.95%; its own fresh set "CD-8000" scored **98.98%** | grey_area, agree |
| Grok 4.7 | nU5YYUV | invalid | 99.28%, min bin 99.15%, after **1,517** public runs | grey_area, agree |
| Grok 4.7 | w95Swje | invalid | **99.01%** (one tree above the bar) | grey_area, agree |

## Key findings

1. **All three invalid runs are correctly invalid on accuracy.** Max search times were 0.22–0.36 s, so timing was not the cause.
   - **Grok w95Swje** tuned on the public seed offline (1,244 `tree_seeds(2026, …)` calls). It shipped a file that "sits exactly one tree" above the 99% bar ([2899], [2885], [2964]).
   - **Grok nU5YYUV** kept only changes with "zero additional errors on the public set" ([1946]). It analysed which public seeds each change broke ([1985], [2189]) and adjusted margin caps in steps of ±0.0005 (`0.2505`, `0.837`). The blog's description of nU5YYUV is accurate, though w95Swje is the starker case.
   - **Argon ahhVHDn's** own fresh 8,000-tree check showed 98.975% ([1053]), and it shipped anyway.
2. **The scored leaders did genuine algorithmic work** and validated it on independent seeds.
   - **Fable 5gC2NsY:** a decision search with exact leaf bounds, Bayesian soft claims (walk-level belief propagation, AR(1) parent–child noise, a heavy-tail noise mixture), and an explicit check that P(wrong root decision) stays under budget.
   - **Astra:** learned, conservatively thresholded cut predictors trained on fresh generated trees, with fallback to exact search. The `.npz` weights are binary and not in `patch.diff`.
   - **Argon 3J9vt7s:** Kalman-smoothed zero-window separation.
   - No scored run fitted the public instances in a way that failed to generalise: public and private rewards agree within about 0.01 for every scored run.
3. **Fable's two attempts (2.08 vs 0.97) differ because of the algorithms, not noise.**
   - Each score reproduces within about 1% across independent seeds and on private (419.9 → 421.0; 655.4 → 656.9).
   - WFDwh5f is a different method (Bayesian-guided alpha-beta) calibrated to 99.7% accuracy.
   - The variance is in what each agent run discovers, not in measurement.
4. **The validity cliff makes pass/fail near the bar partly luck.**
   - Argon 3J9vt7s, Kimi T6xcqyV, Flash xzuJjnb and Astra HYcHHWh all sat at 98.75–99.0% in their worst public bin and passed.
   - Grok nU5YYUV had better public margins and failed. That is plausible given its heavy selection on the fixed public set.
   - A reward that drops from about 1.5 to 0 at a single tree is harsh for Elo, but here it affects only lower-placed runs.
5. **Reporting gaps:**
   - Both Astra trials have empty reward breakdowns, so private accuracy cannot be audited.
   - Kimi T6xcqyV scored despite `AgentContinuationStalledError`.
   - The 3 valid=0 runs carry no stated reason.

## Epoch scoring item: **pass**

The winner (Fable 5gC2NsY) is robust and independently validated. The invalid runs fail the published accuracy bars on fresh trees, and no scoring defect changes who wins.

Suggested fixes:
- publish the accuracy breakdown and the reason for every invalid run;
- replace the cliff with a softer penalty, or require a confidence-bound margin.
