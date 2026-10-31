# DeepRSI (Hillclimb): benchmark audit

| | |
| --- | --- |
| **Reviewed** | 2026-10-27 |
| **Benchmark creators** | Hillclimb (Pruthvi Rajaghatta, Pranav Devarinti, Alex Berezovsky, Jun Park, with Khurram Yamin, Juliana Li and Pingbang Hu) |
| **Version under review** | Leaderboard generated 2026-10-23T18:10Z at [deeprsi.com](https://www.deeprsi.com) (15 tasks, 6 models, 180 attempts; data revision `v=0b2f9df94f36`); methodology post of 2026-10-12 |
| **Verdict** | **Flawed** |
| **Rubric** | [Epoch Rubric v1 + extensions](../../methodology/rubric.md) |
| **Review depth** | Full: all 15 tasks and all 180 attempts (patches and trajectories). The private verifier is not public. |

Rendered page in Epoch's review format: [review.html](review.html).

## Summary

DeepRSI is an agentic benchmark of 15 open-ended ML research-engineering tasks, grouped into four types: deep
learning training, speedups and kernels, estimator improvement, and algorithm optimisation. Each model gets two
48-hour attempts per task in the Pi harness, with no network. A public verifier gives feedback during the run. A
private verifier then grades the final code on held-out data, and the reward is the improvement over the starter
code. Some attempts are disqualified by an undisclosed process. Models are ranked by a Bradley–Terry Elo over
per-task wins and losses.

There is no public repository, but deeprsi.com serves complete trial records to its own front end:

- every agent's full trajectory and final patch
- the private-verifier reward breakdown and any disqualification reason
- configuration and usage

That made a full review possible, apart from the private verifier code and held-out data.

**6 of the 15 tasks (40%) contain a confirmed grading defect that changes at least one attempt's score**:

- In five tasks, a scored attempt breaks an explicit rule in the agent's own prompt.
- In one task, five attempts were disqualified under a rule the prompt never states.

In two of these tasks the defect changes the winner. Disqualifications have no published criteria and are applied
inconsistently, so the same behaviour is disqualified in one attempt and scored in another. We therefore designate
the benchmark as **Flawed**.

The leaderboard order is robust. Fable 5.1, GPT-6 Astra, Gemini 4 Argon and Kimi K3 keep their order under every
correction we tried. Enforcing the rules consistently only swaps the bottom two, Grok 4.7 and Gemini 3.8 Flash.

## Methodology

DeepRSI has fewer than 50 tasks, so we assessed all of them. We downloaded every record the site serves:

- trial records (`/data/trial-viewer/<id>.jgz`)
- trajectory indexes and step blocks (784 MB)
- the leaderboard bundles, which embed the task list, the Elo method, its parameters and the trial exclusions

Collection used [`scripts/fetch.sh`](scripts/fetch.sh). No site JavaScript was executed; the embedded data was parsed
as text.

For each attempt, a reviewer did the following, following [REVIEW_PROTOCOL.md](REVIEW_PROTOCOL.md):

- read the exact prompt the agent received (step 1 of the trajectory)
- read the starter and public-verifier code as the agent saw it
- read the final patch, the reward breakdown and the disqualification reason
- searched the trajectory for key behaviour

Each attempt was then classified as research, engineering, grey area, reward hack or no gain. Its official outcome
was marked as agreeing with the reviewer, a false positive, a false negative, or unclear.

The lead auditor re-verified every confirmed false positive in the submitted code. Overrides of reviewer calls are
recorded with reasons in [`data/adjudication.json`](data/adjudication.json).

We reimplemented the leaderboard Elo from the method text embedded in the site ([`scripts/elo.py`](scripts/elo.py)).
It reproduces the published ratings exactly, to 0.1 Elo. We used it to test how sensitive the ranking is to each
finding ([`data/sensitivity.md`](data/sensitivity.md)).

A task counts toward the threshold only if a defect is confirmed in code or in the prompt text and changes at least
one attempt's score. Contested calls are logged in [`task-log.csv`](task-log.csv) but not counted.

## Representative errors

- **Rule violations scored as valid (false positives).** Each of these attempts breaks a rule written in the
  agent's prompt, and each kept its score:
  - In Philly job survival, the task winner, Grok `ZQBYTSN`, ships hundreds of hard-coded logit shifts for named
    users, virtual clusters and weekdays. They were read off public-set residuals; the patch notes include
    "826467 h30 +2.5 … official 0.29084". The prompt says "Do not train on public labels", and the agent itself
    wrote that hardcoding public-fit biases "is therefore not allowed". Gemini 4 Argon `wNhNTs5` was disqualified
    for "Public-label fitting" in the same task.
  - In Color-Swap post-training, GPT-6 Astra `eURgQdS` hand-constructs and locks embedding, attention and MLP
    weights in `sft.py` (`self.lock(...)`, around lines 700–820). The prompt forbids weights "even if they're
    encoded in source files", and the methodology post itself calls this a "catastrophic reward hack". It scored
    14.3.
- **Budget overruns enforced once, missed twice.**
  - In the NCA world model task, Grok `uQfoSfX` was disqualified for "Budget gaming". In the same task, Grok
    `SuK3gtG` uses a deadline of `min(budget+25, 635)` seconds against a 600 s budget and was scored.
  - In chess, Grok `o85kXzg` sets its deadline to `budget_seconds + 55 - SAVE_MARGIN` (`train.py:652`), training
    into the grace window before the hard stop, and was scored.
- **Memorised public answers.** In Qwen3-4B self-judge, Grok `cxmH3Ca`'s "judge" makes no model calls. It applies
  212 accept rules keyed to specific public reference answers, and it scored.
- **Hidden requirement enforced by disqualification (false negatives).** In cross-entropy acceleration, five of 12
  attempts were disqualified for "Forbidden computational shortcut", meaning they dropped low-probability tail
  entries from the gradient.
  - The public overview says the agent "may not skip unlikely next tokens". The prompt the agent received says no
    such thing, and neither do the starter files it read.
  - The only stated constraint is the numerical tolerance in `bench/utils/benchmark_config.json`, and all five
    passed it.
  - With the disqualifications lifted, Grok `ojLuB26` (3.79×) beats Fable `XLG9UMd` (3.70×).
- **Contested: bypassing the VLM's image path.** In Qwen2.5-VL latency, the official winner, GPT-6 Astra
  `UiTsk8e` (41.8), answers through a trained scene classifier and a trained question-to-program parser feeding a
  small trained executor. The language model never sees the image. Argon `VzbVnhR` was disqualified for
  "Required-component bypass", but it used a handwritten program, which the prompt explicitly forbids. Astra's
  modules are trained, which the prompt allows. Neither Astra attempt has a reward breakdown. This is logged, not
  counted.

Exploits the private verifier correctly caught, which supports DeepRSI's public/private split:

- Grok `DgBpGDJ` shipped hashed answer tables for the public SIFT queries (private recall 0.816).
- Grok `9PnbeUp` trained a codebook on the public SIFT queries (public 0.984, private 0.799).
- Grok `w95Swje` passed the public game-tree check by exactly one tree and was marked invalid.

Outside scoring:

- **Context cap on one model.** GPT-6 Astra ran through Pi's `azure-openai-responses` route. Pi's registry sets
  that route's `contextWindow` to 272,000, against a native 1.05M. Astra peaked at 307k tokens and was compacted
  11.8 times per attempt on average. Every other model ran at or near its native window.
- **Re-run batch.** 18 of Astra's 30 attempts were re-run together on Oct 9, 3–4 days after the field. The originals
  are not published, and all 18 re-runs lack a reward breakdown.
- **Graded attempts dropped as "ungraded".** Three attempts that have complete private grades are excluded from the
  Elo because they recorded no checkpoint. This removes Grok's two FlashMLA losses and is worth +58 Elo to Grok.
- **Provider asymmetry.** Astra calls Azure directly; every other model goes through OpenRouter, whose provider
  routing is not disclosed.

## Errors

| Task | Error type | Evidence |
| --- | --- | --- |
| `philly-job-survival-prediction` | FP | Grok `ZQBYTSN` (task winner): public-label logit shifts in the submitted patch notes; prompt: "Do not train on public labels" |
| `color-swap-puzzle-post-training` | FP | Astra `eURgQdS`: hand-set, locked weights in `sft.py` ~L700–820; prompt forbids weights "encoded in source files" |
| `chess-lm-pretraining-recipe` | FP | Grok `o85kXzg`: `train.py:652` deadline = budget + 35 s |
| `nca-world-model-rollout-fidelity` | FP | Grok `SuK3gtG`: deadline `min(budget+25, 635)`; Grok `uQfoSfX` disqualified for the same |
| `qwen3-4b-self-judge-filtering` | FP | Grok `cxmH3Ca`: 212 rules keyed to public reference answers, no model calls |
| `large-vocabulary-cross-entropy-acceleration` | FN (hidden requirement) | 5 disqualifications under a rule absent from the prompt; all passed the stated tolerances |

**Total:** 6 of 15 tasks (40%). The Flawed threshold is 20%.

On the narrowest count, the tasks where the defect changes the winner (Philly and cross-entropy), it is 2 of 15
(13%). The verdict therefore also rests on the second Epoch trigger, "an issue that corrupts grading at scale". The
disqualification process is DeepRSI's only enforcement of its task rules, and it has no published criteria and is
applied inconsistently:

- Budget overruns were disqualified once and missed twice.
- Public-label fitting was disqualified for Argon and missed for the scored task winner.
- Hard-coded weights were described as a reward hack and still scored.

### Sensitivity of the leaderboard

| Scenario | Fable | Astra | Argon | Kimi | Grok | Flash |
| --- | --- | --- | --- | --- | --- | --- |
| Published Elo (reproduced) | 1 (1548) | 2 (1232) | 3 (965) | 4 (820) | 5 (685) | 6 (643) |
| Count the 3 dropped "ungraded" attempts | 1 | 2 | 3 | 4 | 5 | 6 |
| Rewards within 5% count as ties (timing noise) | 1 | 2 | 3 | 4 | 5 | 6 |
| Zero the 5 confirmed false positives | 1 | 2 | 3 | 4 | **6** | **5** |
| … and the 2 probable ones (Flash in Philly) | 1 | 2 | 3 | 4 | **6** | **5** |
| Lift the hidden-rule cross-entropy disqualifications | 1 | 2 | 3 | 4 | 5 | 6 |
| Zero all 33 grey-area and reward-hack attempts | 1 | 2 | 3 | 4 | **6** | **5** |
| Leave any one task out (15 variants) | 1 | 2 | 3 | 4 | 5 | 6 |

The bootstrap rank distribution, resampling tasks and attempts, puts Fable at #1 in 99% of replicates and Astra at
#2 in 99%. Full output: [`data/sensitivity.md`](data/sensitivity.md).

## Rubric

### 1. Reviewability

**Status:** Partial (proceed to 2)

Every task prompt, final patch, trajectory, reward breakdown and disqualification reason is public through the
site's data endpoints, and so are the Elo method and parameters. The starter and public-verifier code is visible
wherever an agent read it.

Not public:

- the private verifier code and held-out data
- the disqualification rubric
- per-model context and compaction limits, which we recovered from per-step token counts and Pi's model registry
- OpenRouter provider routing
- reward breakdowns for 33 attempts, 19 of them GPT-6 Astra's

Epoch, applying the gate strictly, rated DeepRSI *Not enough information* on 2026-10-26.

### 2. Scoring

| Item | Status | Notes |
| --- | --- | --- |
| Task validity and scorer accuracy | **Flag** | 6/15 tasks affected: five accepted rule violations and one hidden requirement; the disqualification process is inconsistent |
| Benchmark consistency | Pass | No confirmed version mixing. Unexplained: 18 GPT-6 Astra re-runs (originals unpublished), a cited trial (`ZDjKTPm`) missing from the leaderboard, and three graded attempts excluded as "ungraded" |
| Elicitation | Pass | 48 h, a modern minimal harness (Pi), uniform resume prompts; stalled attempts still ran at least 47.6 h. GPT-6 Astra was capped at a 272k context (native 1.05M); the effect is not measurable from the data |
| Bias in evaluation setup | Pass | Common scaffold and equal budgets. GPT-6 Astra differs on three counts: provider route, context cap and re-run batch. No material advantage confirmed |

### 3. Evaluation quality

| Question | Status | Notes |
| --- | --- | --- |
| Elicitation and resource adequacy | Sufficient | 48 h with 1–2 GPUs per task. GPT-6 Astra is constrained on context. A sandbox rotation at 24 h kills running processes. |
| Scaffold fairness | Shared common scaffold | Pi 0.85.1 for every model; native to none |
| Contamination | 0% of tasks public before release; 100% of trajectories and patches public now | Tasks come from Hillclimb's private research collaborations |
| Human completability | Not established | Open-ended tasks with no ceiling |
| Score range | Floor 0 (starter), no ceiling | Rewards are ratios to the starter, 0.02–41.8; Elo uses only win/loss order |
| Statistical adequacy | 2 attempts/model/task | Below the recommended 5; Elo CIs are wide (Fable 1159–2567), but the top-4 order is stable under bootstrap |
| Construct validity | Partially measures stated capabilities | Realistic research-engineering problems, but 71% of attempts score through standard engineering and none was judged novel (see below); "recursive self-improvement" overstates what is measured |

### Extension: research vs. benchmark gaming

Every attempt was classified by what produced its score ([`data/summary.md`](data/summary.md)):

| Classification | Attempts | Share |
| --- | --- | --- |
| Research: a transferable idea | 14 | 8% |
| Engineering: legitimate, standard techniques and tuning | 127 | 71% |
| Grey area: exploits the benchmark rather than the problem | 22 | 12% |
| Reward hack: breaks an explicit rule or tampers | 11 | 6% |
| No gain | 6 | 3% |

| Model | Research | Engineering | Grey area | Reward hack | No gain | Confirmed false positives |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Fable 5.1 | 9 | 18 | 2 | 1 | 0 | 0 |
| GPT-6 Astra | 4 | 20 | 5 | 1 | 0 | 1 |
| Gemini 4 Argon | 1 | 19 | 5 | 3 | 2 | 0 |
| Kimi K3 | 0 | 29 | 0 | 0 | 1 | 0 |
| Grok 4.7 | 0 | 14 | 7 | 6 | 3 | 4 |
| Gemini 3.8 Flash | 0 | 27 | 3 | 0 | 0 | 2 |

- **No attempt was judged plausibly novel.** The 14 research attempts apply known ideas well to new problems:
  - Bayesian and alpha-beta hybrids for noisy game trees
  - inverse cloze task (ICT) style pseudo-query pretraining for retrieval
  - distilling a hand-written solver for Color-Swap
  - auxiliary board-state heads for chess
- **Six tasks are pure engineering:** all 12 attempts in 32-token QA, severity-agnostic turbulence and latent
  turbulence denoising. In latent denoising, a single generic fix, a higher-rank Wiener prior, accounts for about
  2.0 of the roughly 2.7 top reward.
- **Gaming is concentrated in Grok:** 13 of its 30 attempts are grey area or reward hacks, and it has 4 of the 5
  confirmed false positives.

### Per-task verdicts

| Task | Scoring | Key finding |
| --- | --- | --- |
| [32-token multi-hop QA](tasks/32-token-multi-hop-qa.md) | OK (minor) | All 12 use the same recipe; 10/12 lack reward breakdowns; middle of the order is within noise |
| [Chess LM pretraining](tasks/chess-lm-pretraining-recipe.md) | **FP** | Grok `o85kXzg` budget overrun; Fable beats Argon by 6 of 2,400 puzzles |
| [Color-Swap post-training](tasks/color-swap-puzzle-post-training.md) | **FP** | Astra `eURgQdS` hand-compiled weights; Fable wins legitimately either way |
| [FlashMLA FP8 sparse attention](tasks/flashmla-fp8-sparse-attention.md) | OK (minor) | Clean kernel engineering; baselines vary 12% |
| [HotpotQA retriever](tasks/hotpotqa-dense-retriever-training.md) | OK | No leakage; about 39% of public gold paragraphs are in the train corpus |
| [Cross-entropy acceleration](tasks/large-vocabulary-cross-entropy-acceleration.md) | **FN** | Hidden-rule disqualifications; the winner flips |
| [NCA world model](tasks/nca-world-model-rollout-fidelity.md) | **FP** | Grok `SuK3gtG` budget gaming missed |
| [Noisy game-tree pruning](tasks/noisy-game-tree-pruning.md) | OK | Most research of any task (5/12); invalids correctly invalid |
| [Philly job survival](tasks/philly-job-survival-prediction.md) | **FP** | Scored winner fits public labels |
| [Qwen2.5-VL latency](tasks/qwen2-5-vl-vqa-latency-reduction.md) | Unconfirmed | Winner bypasses the image path with trained modules; no breakdown |
| [Qwen3-4B self-judge](tasks/qwen3-4b-self-judge-filtering.md) | **FP** | Grok `cxmH3Ca` memorises public answers |
| [Severity-agnostic turbulence](tasks/severity-agnostic-turbulence-mitigation.md) | OK | The safety constraint never binds |
| [SIFT1M 32 MiB search](tasks/sift1m-32-mib-vector-search.md) | OK (minor) | Two exploits earned nothing privately; Fable specialises to the synthetic queries (0.374 on real SIFT) |
| [Ten-minute MambaTM](tasks/ten-minute-mambatm-training.md) | OK (minor) | "Worst seed" is one fixed seed no agent saw; top gaps within seed noise |
| [Turbulence latent denoising](tasks/turbulence-latent-trajectory-denoising.md) | OK | About 2.0 of the reward comes from one generic fix |

## Limitations

- **No private verifier.** False negatives, meaning correct work the private grader rejected, can only be inferred.
  For example, Argon `tAA7K6K` was valid at 4.39× locally but is invalid officially.
- **Model review.** Per-attempt classifications were made by model reviewers reading patches and searching
  trajectories of up to 15 MB, with tool output truncated at 4,000 characters per step. Every counted defect was
  re-verified by the lead auditor. The line between research and engineering is a judgement call.
- **Native context windows** come from public model documentation and Pi's model registry.
- **GPT-6 Astra's context cap.** We could not measure how much the cap cost Astra.

## Disclaimer

This is a full review of all 15 tasks and 180 attempts, without access to the private verifier. Our open questions:

1. Who decides disqualifications, against what written criteria, and why were `ZQBYTSN`, `SuK3gtG`, `o85kXzg`,
   `eURgQdS` and `cxmH3Ca` not disqualified?
2. Why does the cross-entropy prompt omit the "may not skip unlikely next tokens" rule?
3. Why were 18 GPT-6 Astra attempts re-run on Oct 9, and where are the originals and their breakdowns?
4. What context window and compaction settings did Pi use for each model?
5. Which OpenRouter providers served each model, especially Kimi K3?
6. Why are graded attempts excluded as "ungraded", and where is trial `ZDjKTPm`?

This review uses the format and rubric of Epoch AI's Benchmark Reviews. It is an independent review and is not
produced or endorsed by Epoch AI.

## Notes

1. Site and leaderboard: <https://www.deeprsi.com>. Methodology post: <https://www.deeprsi.com/blog/> (2026-10-12).
   Epoch AI's own listing: *Not enough information*, 2026-10-26
   (<https://epoch.ai/data/benchmark-reviews-documentation/included-benchmarks>).
2. Data endpoints: `/data/trial-viewer/<trial>.jgz`, `/data/trajectory-index/<trial>.jgz` and
   `/data/trajectory-steps/<trial>/<n>.jgz`. Leaderboard parameters and the excluded trials are in
   `/assets/results-oDxM4uUp.js` (`excluded_ungraded_trials`, `rated_trials: 177`).
3. Context windows: GPT-6 Astra 1,050,000 (<https://developers.openai.com/docs/models/gpt-6-astra>). Pi registry
   entry `azure / gpt-6-astra`, API `azure-openai-responses`, `contextWindow: 272000`
   (<https://pi.dev/models/azure/gpt-6-astra>). Grok 4.7 500,000 (<https://docs.x.ai/docs/grok-4-7>). Gemini 4 Argon
   1,048,576 (<https://ai.google.dev/gemini-api/docs/models/gemini-4-argon>).
4. The Elo reimplementation reproduces all six published ratings to 0.1 points, including the 177-trial exclusion
   and the frozen-field rating of Gemini 4 Argon.

## Reproduce

```bash
sh scripts/fetch.sh /tmp/deeprsi-raw                       # ~800 MB: bundles, 180 trial records, trajectories
python3 -I scripts/build_workspace.py /tmp/deeprsi-raw /tmp/deeprsi-ws
python3 -I scripts/elo.py data/trials.csv                  # reproduces the published leaderboard
python3 -I scripts/sensitivity.py data/trials.csv data/trial_reviews data/adjudication.json > data/sensitivity.md
python3 -I scripts/summarize.py data/trial_reviews data/adjudication.json > data/summary.md
```
