# FrontierCS 2 (48 public tasks): benchmark audit

| | |
| --- | --- |
| **Reviewed** | 2026-10-27 |
| **Benchmark creators** | FrontierCS Team (Q. Mang, W. Chai et al.; UC Berkeley, Princeton and others) |
| **Version under review** | The leaderboard on frontier-cs.org and Kaggle as of 2026-10-26. The 816 formal runs in HF `FrontierCS2/FrontierCS-2-runs` @ `a3f6c3e2` (`formal-results.json` sha256 `35b1a7eb…`). Tasks and judges at GitHub `FrontierCS/FrontierCS-2` @ `57b97dcb`; pre-fix files were taken from that history. The paper is arXiv 2610.29932v1. |
| **Verdict** | **Flawed** |
| **Rubric** | [Epoch Rubric v1 plus our extensions](../../methodology/rubric.md) |
| **Review depth** | All 48 tasks assessed, the sampling rule for benchmarks with 50 or fewer tasks. The private set of more than 100 tasks was not reviewed. |

## Summary

**What the benchmark measures.** FrontierCS 2 deletes the key contribution of
a published paper from its authors' repository and gives an agent 5 hours to
rebuild it, with no network access. A run **passes** only if its final patch
beats the deleted code (the "human reference") on every metric and every
held-out workload. The headline number is pass rate over 48 tasks, one run
per (task, model). The leaderboard is led by Claude Opus 5.5 in Claude Code
(58.3%), then Gemini 4 Argon in Antigravity (54.2%) and GPT-6 Astra in Codex
(43.8%).

**Reviewability is excellent.** Every task, evaluator, beat rule, reference
patch, final patch and full agent trace is public. That made this audit
possible.

**But the scoring has defects that cross the threshold.**

- **23 of 48 tasks (47.9%) have a confirmed defect that can flip PASS/FAIL.** The Flawed threshold is 20%.
- **14 tasks are false negatives or practically impossible.** Most of them combine "strictly better on every workload, no tolerance" with stochastic or near-floor measurements that the authors never calibrated, and on several the reference itself would fail its own bar.
- **9 tasks are false positives:** reward-hackable scorers (5 of them fixed by the developers after the runs), or bars that the reference meets or that a trivial change to the reference beats.
- **The leaderboard mixes task versions.** On 5 tasks it combines runs scored before and after those scorer fixes, without a version bump.
- **Two leaderboard passes use the hacks directly.** Gemini 4 Argon (Pi) passed `dynamic_tanh` with the exact argv-introspection hack the developers later patched, and passed `detok_latent_denoising` by optimizing the latents against the image being scored.

**What survives the audit.** The model ordering is fairly robust to the
defects (see Sensitivity). The *magnitude* claims ("agents beat
published human work on X% of tasks") and close rank comparisons are not.

## Methodology

**What we inspected.** All 48 public tasks, read against Rubric v1 Section 2:

- the agent-visible statement and repo
- `policy.json`
- the judge (`evaluator.py`, `beat_spec.json`, reference patch)
- git history

**How we used the run data.**

- We used the run records of all 816 formal runs and 612 non-accepted runs.
- For every task with 6 or fewer passes, we downloaded and read all passing final patches; for the rest, we spot-checked them.
- To answer specific questions, we extracted verifier evidence and raw model traffic from about 200 traces.

**What we computed or reproduced.**

- For each task, the probability that the unchanged reference passes against itself, and how much measurement noise sits inside the pass margin. These come from the beat rules, the in-run reference spread and the developers' own calibration notes.
- Locally, only the egg reference (egraph task) was built and timed. Numeric emulations were run for polar_express and kmeans.
- We did not run any candidate code.

**How we counted.** A task counts toward the threshold only if a defect is
CONFIRMED (code, rule, computation or run evidence) and can change PASS/FAIL.
Unconfirmed suspicions are logged in [`task-log.csv`](task-log.csv) but not
counted. Per-task write-ups are in [`findings/`](findings/), and the setup
audit is in [`setup.md`](setup.md). The analysis scripts are in
[`scripts/`](scripts/); they need the HF dataset and the GitHub repo locally.

## Representative errors

**1. Reward-hackable scorers, fixed only after the leaderboard runs (FP).**
On 2026-10-25/26, the developers patched five tasks whose scorers could be
gamed. 72 of the 85 leaderboard records on these tasks were created before
the corresponding public fix commit and are not marked as re-runs on the
revised task, so they were scored on the vulnerable versions.

- `parallel_dbscan`: in-process memoization across timing rounds; DeepSeek V4.1 Flash 1017 passed this way. Commit `282b1edd`.
- `batch_local_counting`: output caching across rounds; the developers measured 83 vs a reference of 17. Commit `b11a73b8`.
- `dynamic_tanh`: argv introspection, so the timed code path differs from the accuracy-scored one. Commit `5630acc6`.
- `evm_state_checkpoints`: cost moved into untimed post-restore work. Commit `9ea965c7`.
- `progent_privilege_control`: injection security judged on *requested* rather than *executed* calls. Commit `655bfd01`.

Only the runs that tripped a fix were re-run (DeepSeek 1017, and Gemini
Antigravity on two tasks). In `dynamic_tanh`, **Gemini 4 Argon (Pi)'s
counted PASS uses the exact hack**:
`_IS_MAIN_CLI = basename(sys.argv[0]) == "main.py"` gates the fast kernels
off during the accuracy run (`patches/dynamic_tanh/gemini.patch:14,35,181,253`).

**2. Scorers the reference itself cannot pass (FN / IMPOSSIBLE).**

- `vllm_llm_serving_optimization` compares candidates against the **per-instance minimum of three reference captures**, with zero margin and a strict `<` (`judge/beat_spec.json:116-123`, `verifier/fixed-targets.json`). A fresh reference capture would itself need a 1.02–1.69x speedup to clear this bar, and 0/17 runs pass. GPT-6 Astra cleared 19 of 20 comparisons.
- `fast_kv_compaction`: the reference clears its own accuracy gate only 13–17% of the time, and the full uncompressed cache misses the bar on one article.
- `ragen_multi_turn_rl` scores rollouts of a frozen policy taken before any optimizer step, and requires strictly more successes than a 0%-success deterministic reference on every group.
- `representation_frechet_loss` ships with the agent-visible note *"Source revision awaiting runtime qualification"* (`repo/README.md:3`) and `"status": "proposed_uncalibrated"` (`judge/judge_deps/workloads.json:2`).
- `flow_opd` ships with `release_ready: false` and `reference_repetitions: 1` (`judge/metadata.json:27`, `judge/judge/qualification.json`).

**3. Strict "win every cell" rules on near-floor or noisy measurements (FN).**

- `join_tree_rewriting` needs a strictly lower median on all 39 queries (`judge/query_measurements.py:128`). Across 638 train calls in 16 traces, no submission cleared all 20 dev queries.
- `runlts_predictor` needs strict wins on all 105 traces. Its own README (`repo/README.md:91`) says a trivial RNG shift moves a trace by about 1% (up to 6.6%).
- `parallel_radix_sort` keeps a strict one-pair `c<r` on 12 workloads, although its authors measured 0.5–4% reference-vs-reference noise (outliers 15%). Runs 7–8% faster in geomean fail, while a run 5% faster passes.
- `edlib_exact_alignment` times a reconstruction the reference does in about 0.1 ms, with a CV of 14–31%; sometimes that time is measured at ≤0.
- `sparse_video_attention_policy` sets fidelity bands narrower than the spread between two runs of identical code (LPIPS 0.0056 vs a band of 0.005).
- The same pattern appears in `diffusion_policy_cpu` (P(4/4) ≈ 6% for any faster sampler), `egraph_invariant_restoration`, and `binary_fuse_filter` (runs 21–26% faster fail on 1 of 144 cells).

**4. Bars that pass without a research advance (FP / CONSTRUCT).**

- `metaopt_combined_te_gap_search` accepts ties against a deterministic reference (`"candidate >= reference"`), so the unchanged reference passes.
- `polygon` times a value that the candidate's own editable `Environment.check` reports; the judge only checks `0 ≤ t ≤ budget` (`frontier_runner.py:84-93`, `judge/evaluator.py:722-728`). A fixed 0.29 s offset, whether a candidate includes the parser's one-time grammar build or not, decides most verdicts.
- `polar_express`'s bar is the paper's bf16 method. Re-running the reference code without its bf16 safety margins beats the bar in every simulated seed, and 14/17 runs pass.
- In `detok_latent_denoising`, the editable files control the eval path. Gemini (Pi) passes by optimizing the latents against the image being scored (`gemini.patch`, `reconstruct() → _refine_tokens`); Gemini (Antigravity) passes with an eval-only smoothing filter.

**Setup findings outside scoring.** These are covered in the rubric below and
in [`setup.md`](setup.md):

- one run per task
- a 14.6-point harness effect for the same model
- the Kaggle #2 entry's settings absent from the repo and paper
- one Opus 5.5 run that finished on Opus 4.8 after a refusal
- non-uniform reasoning effort across entries

## Errors

| Task | Error type | Evidence |
| --- | --- | --- |
| `batch_local_counting` | FP (pre-fix scorer) | commit `b11a73b8`; old `evaluator.py:215-221` |
| `dynamic_tanh` | FP (exploited by a counted PASS) | commit `5630acc6`; `patches/dynamic_tanh/gemini.patch:14` |
| `evm_state_checkpoints` | FP (pre-fix scorer); consistency | commit `9ea965c7`; reference ~61 → ~75 |
| `parallel_dbscan` | FP (pre-fix scorer; exploited, re-run) | commit `282b1edd`; `other_runs` ds1017 |
| `progent_privilege_control` | FP surface + FN | commit `655bfd01`; `gemini-agy.patch:~940`; replay: opus, ds, qwen → PASS under the fixed rule |
| `detok_latent_denoising` | FP; CONSTRUCT | `patches/detok_latent_denoising/gemini.patch` |
| `polar_express` | FP / CONSTRUCT | [findings/polar_express.md](findings/polar_express.md) |
| `metaopt_combined_te_gap_search` | FP (reference passes itself) | `judge/beat_spec.json` "exact ties accepted" |
| `polygon` | FN; FP surface | `frontier_runner.py:84-93`; `judge/evaluator.py:722-728` |
| `vllm_llm_serving_optimization` | FN (reference fails its own bar) | `judge/beat_spec.json:116-123`; `verifier/fixed-targets.json` |
| `fast_kv_compaction` | FN | [findings/fast_kv_compaction.md](findings/fast_kv_compaction.md) |
| `ragen_multi_turn_rl` | IMPOSSIBLE (practical) | `judge/beat_spec.json:9,21` |
| `representation_frechet_loss` | FN; unqualified task | `repo/README.md:3`; `workloads.json:2` |
| `flow_opd` | FN; unqualified task | `judge/metadata.json:27`; `qualification.json` |
| `sparse_video_attention_policy` | FN | [findings/sparse_video_attention_policy.md](findings/sparse_video_attention_policy.md) |
| `diffusion_policy_cpu` | FN | [findings/diffusion_policy_cpu.md](findings/diffusion_policy_cpu.md) |
| `join_tree_rewriting` | FN | `judge/query_measurements.py:128` |
| `runlts_predictor` | FN / near-IMPOSSIBLE | `repo/README.md:91` |
| `parallel_radix_sort` | FN | `judge/beat_spec.json` comments; `evaluator.py:109-127` |
| `edlib_exact_alignment` | FN | `judge/beat_spec.json` "0 < T_C(w) < T_R(w)" |
| `egraph_invariant_restoration` | FN | [findings/egraph_invariant_restoration.md](findings/egraph_invariant_restoration.md) |
| `binary_fuse_filter` | FN | [findings/binary_fuse_filter.md](findings/binary_fuse_filter.md) |
| `lwe_structured_recovery` | IMPOSSIBLE | [findings/lwe_structured_recovery.md](findings/lwe_structured_recovery.md) |

**Total:** 23 of 48 tasks (47.9%). The threshold is 20%. The verdict is robust to how the count is made:

- **Against the current public repo only** (the five developer-fixed tasks excluded): 18/48 = 37.5%.
- **Counting only the 8 tasks that are unpassable or unqualified by the developers' own files or by direct computation, plus the 5 developer-acknowledged fixes:** 13/48 = 27%. The 8 are `vllm_llm_serving_optimization`, `fast_kv_compaction`, `ragen_multi_turn_rl`, `representation_frechet_loss`, `flow_opd`, `sparse_video_attention_policy`, `runlts_predictor` and `lwe_structured_recovery`.

Uncounted caveats are in `task-log.csv`, including:

- `knn` (its reference was replaced by a task-authored kernel 1.5–20x faster than the paper's)
- `shockwave` (passes brute-force an 8-job toy instance)
- strict-latency false-negative risk on several GPU kernel tasks

### Sensitivity of the leaderboard

From `scripts/sensitivity.py`:

| Entry | Published pass rate | With targeted corrections¹ | Pass rate on the 25 tasks without a counted defect |
| --- | --- | --- | --- |
| Claude Opus 5.5 | 28/48 (58.3%) | 29/48 (60.4%) | 21/25 (84%) |
| Gemini 4 Argon (Antigravity) | 26/48 (54.2%) | 26/48 (54.2%) | 19/25 (76%) |
| GPT-6 Astra | 21/48 (43.8%) | 21/48 (43.8%) | 16/25 (64%) |
| Gemini 4 Argon (Pi) | 19/48 (39.6%) | 17/48 (35.4%) | 15/25 (60%) |
| GPT-6.1 Terra | 19/48 (39.6%) | 19/48 (39.6%) | 13/25 (52%) |
| GPT-6.1 Sol | 17/48 (35.4%) | 17/48 (35.4%) | 13/25 (52%) |
| GLM 5.3 | 12/48 (25.0%) | 12/48 (25.0%) | 9/25 (36%) |
| Kimi K3.1 Pro | 12/48 (25.0%) | 12/48 (25.0%) | 9/25 (36%) |
| Kimi K3 | 10/48 (20.8%) | 10/48 (20.8%) | 9/25 (36%) |
| Muse Wonder 1.0 | 10/48 (20.8%) | 10/48 (20.8%) | 9/25 (36%) |
| DeepSeek V4.1 Flash 1017 | 8/48 (16.7%) | 8/48 (16.7%) | 6/25 (24%) |
| DeepSeek V4.1 Flash | 7/48 (14.6%) | 8/48 (16.7%) | 6/25 (24%) |
| Muse Spark 1.3 | 6/48 (12.5%) | 6/48 (12.5%) | 5/25 (20%) |
| GLM 5.3 Flash | 6/48 (12.5%) | 6/48 (12.5%) | 5/25 (20%) |
| Qwen 3.8 Max | 6/48 (12.5%) | 7/48 (14.6%) | 5/25 (20%) |
| Step 5 Preview | 4/48 (8.3%) | 4/48 (8.3%) | 3/25 (12%) |

¹ The targeted corrections remove Gemini (Pi)'s two hack-based passes
(`dynamic_tanh`, `detok_latent_denoising`). They also apply the developers' own
post-fix Progent rule to the recorded final traffic, which turns Opus,
DeepSeek and Qwen from FAIL to PASS; this rests on our trace reconstruction,
[findings/progent_privilege_control.md](findings/progent_privilege_control.md).

The ordering is largely stable. The level is not: on the defect-free half of
the benchmark the top model passes 84%, which says "the median task is about
as hard as the strongest agent" (paper §5.2) is driven by the defective tasks.

## Rubric

### 1. Reviewability

**Status:** Full

All tasks, evaluators, beat specifications, reference patches, workloads
(some as LFS objects), final patches and full traces are public. Harness
settings are disclosed for 13 of the 17 entries in `config/candidates.json`
and paper Table 4.

Four entries were added after the paper, and their harness recipe and
settings are not in the repo: Gemini 4 Argon (Antigravity), which is Kaggle's
#2, GPT-6.1 Terra, Kimi K3.1 Pro and DeepSeek V4.1 Flash 1017. Their settings
are recoverable from the raw request bodies in the released traces: for
Antigravity, effort `high` and `max_tokens` 65,536 on main calls. The
benchmark should publish them directly.

### 2. Scoring

| Item | Status | Notes |
| --- | --- | --- |
| Task validity and scorer accuracy | **Flag** | 23/48 tasks (47.9%) have confirmed outcome-affecting defects. |
| Benchmark consistency | **Flag** | On 5 tasks the leaderboard mixes runs scored before and after scorer fixes, with no version bump (the repo is still `frontier-cs-2.0-demo`, Kaggle says "v1", and per-run task versions are redacted). On `evm_state_checkpoints`, 14 runs used a 3-workload scorer (reference ≈61) and 3 used a redefined 6-workload scorer (reference ≈75). On `dynamic_tanh`, Opus's legitimate pre-fix PASS would be rejected by the post-fix filter (`os.environ` token), while Gemini (Antigravity) was re-run under it. 612 non-accepted runs show that tasks were revised mid-campaign and earlier models re-run in batches; this was handled consistently except for the post-release fixes. |
| Elicitation | Pass | 5 h with modern vendor harnesses and no network. Non-voluntary termination is low for ranked entries, except Gemini on Pi (10/48 runs ended by provider refusals, per the site; it is not a ranked Kaggle row). Train-call budgets of 3–8 on several GPU tasks, with aggregate-only feedback, are tight. The reviewers judged them not decisive. |
| Bias in evaluation setup | Pass | No material model-specific advantage was confirmed. The caveats: each model uses its own harness; reasoning effort is `high` for Gemini, Kimi K3, Muse Spark, Qwen and Step but `max`/`xhigh` for the others, and it is not shown that `high` is the maximum for those models; refusal handling differs (Pi stops, Antigravity retries, Claude Code falls back to Opus 4.8); and fixes and re-runs were applied only to the runs that tripped them. |

Because Section 2 is flagged, the verdict is **Flawed**.

### 3. Evaluation quality

| Question | Status | Notes |
| --- | --- | --- |
| Elicitation and resource adequacy | Sufficient / Constraining on some GPU tasks | Tight train-call budgets on DyT, RAGEN, Fréchet, Nano World Model and MuJoCo (3 each). |
| Scaffold fairness | Model-specific scaffolds | The harness effect is large: Gemini 4 Argon passes 26/48 in Antigravity vs 19/48 in Pi (8 vs 1 discordant tasks, exact McNemar p = 0.039). This is bigger than the gap between ranks 2 and 5. |
| Contamination | 100% of the 48 tasks public (since 2026-10-20); the reference implementations come from public upstream repos | The reference code predates most models' training cutoffs, but reproducing it only ties and does not pass. The private set (more than 100 tasks) is not reviewed. |
| Human completability | Not established | No human baseline. The "human reference" cannot pass against itself by design, and on at least 9 tasks no realistic correct improvement could reliably pass. |
| Score range | Floor 0%, ceiling well below 100% | 14 tasks have 0/17 passes; the paper reports 16 over its 12 agents. 11 of these 14 are counted defects above. |
| Statistical adequacy | **1 run/model** (at least 5 recommended) | Where the dataset has more than one scored run of the same (task, model), 74/236 (31%) disagree on PASS/FAIL. The paper's own fit gives a run-effect SD of 2.04 logits (20 FCI points). The 95% bootstrap CI over tasks for #1 is 43.8–72.9%. #1 vs #2: 6 vs 4 discordant tasks, p = 0.75. The leaderboard shows no uncertainty. |
| Construct validity | Partially measures stated capabilities | "Beats the paper's code in this harness" frequently means beating a reference that runs outside its design regime (bf16 margins scored in fp32, a memory-bound GEMM regime, toy scheduler instances). Sometimes the bar is not the paper's code at all (`knn`). |

**LLM-judge check (our extension):** not applicable. No score comes from an LLM
judge. Progent and LRR use LLMs as the system under test; we found small,
non-decisive nondeterminism there.

## Limitations

- **Task-review coverage.** Every task was assessed, but most were not executed. Most false-negative probabilities are estimated from the beat rules, the in-run reference spread and the developers' own calibration notes, not from fresh reruns.
- **Progent.** The FAIL→PASS result rests on reconstructing final traffic from the traces; the per-episode verifier evidence is not released.
- **Unconfirmed concerns** (strict-latency false-negative risk on 4 GPU kernel tasks, the kmeans first-step check, kami and glenside construct notes, nano_world_model and mujoco calibration) are logged but not counted.
- **Scope.** We reviewed the published leaderboard version. The public repo already contains the developers' fixes for 5 tasks, so a re-run on the current repo would avoid those defects, though 18/48 tasks would still be counted.
- **Private set.** The private set is outside this review.

## Disclaimer

This is a full review of the 48 public tasks; the private set was not reviewed. This review uses the format
and rubric of Epoch AI's Benchmark Reviews; it is independent and not produced or endorsed by Epoch AI.

## Notes

1. Epoch AI, Benchmark Reviews methodology (Rubric v1): <https://epoch.ai/data/benchmark-reviews-documentation/methodology>
2. FrontierCS 2 paper: <https://arxiv.org/abs/2610.29932>. Repo: <https://github.com/FrontierCS/FrontierCS-2>. Runs: <https://huggingface.co/datasets/FrontierCS2/FrontierCS-2-runs>. Leaderboards: <https://frontier-cs.org>, <https://www.kaggle.com/benchmarks/frontiercs/frontiercs-2>
3. The post-run scorer fixes are FrontierCS-2 commits `b11a73b8`, `282b1edd`, `655bfd01`, `5630acc6` and `9ea965c7` (2026-10-25/26).
4. The cost per full Opus 5.5 evaluation is stated by the authors as about $1,000 in API fees, $300 in GPU and $100 in CPU. The Claude Code runs used subscription authentication, so per-run costs are list-price estimates.
