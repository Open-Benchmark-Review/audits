# FrontierML (Induction Labs): benchmark audit

| | |
| --- | --- |
| **Reviewed** | 2026-10-27 |
| **Benchmark creators** | Induction Labs |
| **Version under review** | Repo [`induction-labs/frontier-ml`](https://github.com/induction-labs/frontier-ml) at `31837e0` ("Initial benchmark release", 2026-10-13). Tasks dataset [`inductionlabs/frontier-ml-tasks`](https://huggingface.co/datasets/inductionlabs/frontier-ml-tasks) at `925401fb`. Leaderboard at [frontierml.org](https://www.frontierml.org/data/) as fetched 2026-10-27 (19 models, 21 tasks, 3 wallets, 1,197 trials). |
| **Verdict** | **Flawed** |
| **Rubric** | [Epoch Rubric v1 + extensions](../../methodology/rubric.md) |
| **Review depth** | Full for 21 tasks (prompt, contract, grader, anchors, judge, held-out data, self-check) and for every trajectory and grade page of six models (378 trials). The other 13 models were used only for leaderboard-wide statistics. |

Rendered page in Epoch's review format: [review.html](review.html). The full write-up with every finding is
[findings.md](findings.md).

## Summary

FrontierML is an agentic benchmark of 21 ML tasks: training, distillation, quantisation, serving, vision, audio, Lean
and games.

- Each model gets 12 hours in its developer's own agent harness, with internet access, and a compute wallet of $10,
  $50 or $200. Each (model, task, wallet) cell is run once.
- A per-task metric on held-out data is scaled linearly between a floor and a ceiling, to 0–100.
- A reviewer (Claude Opus 5.5) can zero a trial for breaking the task's rules.
- The leaderboard reports the mean score per wallet.

FrontierML is unusually inspectable. The grading code, review rubrics, scoring anchors, every trajectory and every
grade page are public. That openness is also its biggest problem:

- **The held-out data is public.** For all 21 tasks it sits in a public, ungated Hugging Face dataset, and agents
  have internet access and a Hugging Face token.
- **7 of 21 tasks (33%) have confirmed scoring defects:**
  - rule-breaking trials scored as valid
  - a scorer a blind constant beats
  - a deciding rule that is undefined
  - floors that contradict the graded request or sit inside the noise
  - a task that rewards recognising its source benchmark
- **The review that enforces the rules was skipped for 21 of DeepSeek's trials**, and those scores still count.

We therefore designate the benchmark as **Flawed**.

The model ranking survives every correction we tried: Opus 5.5 first, then GPT-6 Astra, Fable 5.1, Gemini 4 Argon,
then DeepSeek V4.1 Flash and Muse Wonder. Opus is #1 in 100% of task-bootstrap replicates. What the defects undermine
is the score levels, and what several tasks measure.

## Methodology

For each of the 21 tasks we read the following in the repository and the dataset, and compared them with the
observed scores:

- the prompt the agent receives, and the task contract
- the grader, scoring anchors and judge
- the held-out data, gates and self-check
- the reference solution

For six models (Opus 5.5, Fable 5.1, GPT-6 Astra, Gemini 4 Argon, Muse Wonder and DeepSeek V4.1 Flash), reviewers
read every trajectory and grade page, 378 trials in all, following [REVIEW_PROTOCOL.md](REVIEW_PROTOCOL.md). Each
trial was classified as research, engineering, grey area, reward hack or no gain, and its official outcome was
checked against the task rules. Leaderboard-wide statistics, such as review fail rates and zero rates, use all 1,197
trials.

The published per-wallet means reproduce exactly from the trial table. The ranking sensitivity is in
[`data/sensitivity.md`](data/sensitivity.md).

The lead auditor re-checked every confirmed false positive and every call that affects a winner. Reviewer overrides
and the mapping of task-design findings onto the rubric are recorded in
[`data/adjudication.json`](data/adjudication.json). The central claims were re-verified against primary sources on
2026-10-28:

- the dataset's visibility (HF API: `private: false`, `gated: false`, created 2026-09-24, `<task>/private/` for all 21
  tasks)
- `harbor_plugin.py:521-526`, which injects the operator's token
- `grading.py:67`, the review skip
- `review_trajectory.py:154`, which tells the reviewer the model name

A task counts toward the threshold only if a defect is confirmed in code, data or trial evidence and it can change a
score. Unconfirmed concerns are logged in [task-log.csv](task-log.csv) but not counted.

## Representative errors

- **Held-out answers readable from the web.** Every task's verifier downloads its held-out data from `<task>/private/`
  in a public, ungated dataset created before any audited run. Agents have internet access, and by default they get
  the operator's own HF token. In six more tasks the held-out set is drawn from a public benchmark's test split. In
  three LLM tasks, the full graded GPQA-Diamond and LiveCodeBench v6 sets are handed to the agent as "development
  examples".
  - The only control is the reviewer. Only 10 of 21 rubrics forbid using the dataset, and the "searching up answers"
    check the methodology post describes is in no rubric.
  - DeepSeek `4ttc3o` (llm-diffusion) cloned the benchmark repository and read the grader, the reference solution and
    the location of the private split. It downloaded nothing and scored 0, and its review had been skipped.
- **Selecting on the graded benchmark, scored as valid.** The prompt bans training, fine-tuning, calibrating "or
  selecting" on any public benchmark's validation or test split.
  - In ternary-ptq, the rubric omits "select" (`tests/task/review.py:14-23`). It therefore passed three Fable trials
    and one Argon trial that picked serving settings or checkpoints by GPQA accuracy. One example is Fable `27dhfi`
    [136]: "GPQA-Diamond first 40 questions: 4/40 (thinking…)", after which it sets the shipped defaults to match.
  - In llm-post-train, the same behaviour was zeroed twice (Fable `67hhap`, Muse `2wj08u`) and passed once (Fable
    `2ikiw0`).
- **A scorer a blind constant beats.** In screen-difference, the floor is an empty output. An input-blind fixed
  paragraph scores 32.0, above 14 of the 18 audited trials. The judge scores recall only, although the prompt forbids
  unsupported claims (`tests/task/task.yaml:45-47`, `instruction.md:5`).
- **A rule that cannot decide its own winner.** In llm-diffusion, the review separates about 80 points from 0 on
  "genuine iterative denoising" without saying whether AR-verified diffusion qualifies.
  - The $200 winner, Argon `v837u7`, ends each block with the causal verify pass the reviewer cited when zeroing
    three other trials. Strictly applied, Opus `n8ftju` wins instead.
  - The speed gate can also be told apart from scored traffic by `max_tokens`. Fable `19lyhu` served the gate a
    separate fast decoder (a probable false positive).
- **Floors that contradict the request or sit in the noise.**
  - maple-vlm's floor is measured with 8,192 sampled thinking tokens and a grammar, while graded requests send
    `max_tokens: 256` at temperature 0. The floor was also raised mid-evaluation. 54 of 57 trials score 0.
  - pokemon-random-battle's 50% floor is against an opponent with about the candidate's compute. 41 of 57 trials
    score 0, and every wallet winner is within 1–2 paired standard errors.
- **Rewarding recognition of the source.** In ai-text-detection, the held-out set is DetectRL-X's public test rows,
  and the in-distribution train split is allowed. The 9 trials that found and trained on it average 92.0, against
  65.3 for the rest.

Outside scoring:

- **Review skipped.** `FML_REVIEW_SKIP` turns off review for a whole run (`grading.py:67`). 21 of DeepSeek's 63 trials
  were graded that way, and 17 of MiniMax's, and they count on the leaderboard.
- **Re-runs.** 62 of 63 Gemini 4 Argon trials are re-runs, and the originals are unpublished. Argon also hit 332
  `RESOURCE_EXHAUSTED` quota errors in 38 trials and averaged 3.4 of 12 hours.
- **Reviewer told the model name.** The reviewer is Claude Opus 5.5 and is told which model it is reviewing. Claude
  models fail review 2.0% of the time against 6.1% for the rest (p = 0.004). The per-trial audit found no
  self-preference: 0 missed violations in Opus trials, and the reviewer's misses favoured Fable and Argon.

## Errors

| Task | Error type | Evidence |
| --- | --- | --- |
| `ternary-ptq` | FP | Fable `27dhfi`, `wyk9nh`, `6dnn0k`; Argon `3jodic`: selection on graded GPQA; rubric omits "select" (`tests/task/review.py:14-23`) |
| `llm-post-train` | FP | Fable `2ikiw0` [136]: GPQA-guided budget forcing; the same behaviour was zeroed twice |
| `screen-difference` | FP | Blind fixed paragraph scores 32.0, above 14 of 18 trials (`tests/task/task.yaml:45-47`) |
| `llm-diffusion` | IMPOSSIBLE + FP | Undefined "genuine denoising" rule decides 80 vs 0; gate recognisable by `max_tokens` (`CONTRACT.md:12` vs `tests/config.json:21`) |
| `maple-vlm` | FN + CONSTRUCT | Floor recipe contradicts the graded request (`tests/task/task.yaml:42-55`); 54/57 trials at 0 |
| `pokemon-random-battle` | FN | Uncalibrated 50% floor; paired SE 1.66 points; every winner within 1–2 SE |
| `ai-text-detection` | CONSTRUCT | Held-out = public DetectRL-X test; recognising it is worth ~27 points |
| *(all 21 tasks)* | FP risk at scale | Held-out data public on HF; agents have internet and an HF token (`harbor_plugin.py:521-526`) |

**Total:** 7 of 21 tasks (33%). The Flawed threshold is 20%.

- Excluding the two noise and construct calls (pokemon and ai-text-detection), it is 5 of 21 (24%).
- Counting only tasks with a confirmed trial-level false positive, it is 2 of 21 (10%). The verdict then rests on the
  second trigger: held-out answers for every task are readable from the web by agents with internet access, and the
  only control is a review that is incomplete and can be switched off.

### Sensitivity of the leaderboard

| Scenario | Opus | Astra | Fable | Argon | DeepSeek | Muse |
| --- | --- | --- | --- | --- | --- | --- |
| Published ($200 mean) | 1 (58.8) | 2 (44.5) | 3 (41.9) | 4 (39.5) | 5 (23.5) | 6 (19.3) |
| Zero the 5 confirmed false positives | 1 | 2 | 3 (40.5) | 4 | 5 | 6 |
| Strict reading: also probable false positives and the contested llm-diffusion winner | 1 | 2 | 3 (40.5) | 4 (32.3) | 5 | 6 |
| Leave one task out (21 variants) | 1 | 2 | 3 | 4 | 5 | 6 |
| Task bootstrap, share of replicates at this rank | 100% | 63% | 49% | 64% | 90% | 91% |

The one leave-one-task-out exception: without llm-post-train, Fable passes Astra. Astra, Fable and Argon are within 5
points of each other at $200 and swap places in 36–51% of bootstrap replicates. Opus's 14.3-point lead is not a
scoring artifact.

## Rubric

### 1. Reviewability

**Status:** Full (proceed to 2)

Every task's prompt, contract, grader, anchors, review rubric, judge prompt and held-out data is public, and so is
every trajectory and grade page. That includes each reviewer check with its reasoning, and the self-check log.

Gaps:

- Submitted files (weights and server code) are visible only as quoted in trajectories.
- A zeroed trial's pre-review score is unpublished.
- The harness wrappers for Codex, Antigravity and Muse Code are unpublished, although their settings can be read
  from the trajectories.
- The originals of 72 re-run trials are unpublished.

### 2. Scoring

| Item | Status | Notes |
| --- | --- | --- |
| Task validity and scorer accuracy | **Flag** | 7/21 tasks affected (33%), plus held-out data readable from the web for every task; see Errors |
| Benchmark consistency | **Flag** | Reviewed and unreviewed scores are mixed on one leaderboard: 21 DeepSeek and 17 MiniMax trials were graded with the review that zeroes rule violations skipped. Also: maple-vlm's floor was raised after half the field ran (all rescored on the new floor), 72 re-runs have unpublished originals, and one Opus trial received an older prompt. |
| Elicitation | Pass | 12 h in vendor harnesses with internet. Gemini 4 Argon hit 332 quota errors in 38 of 63 trials and averaged 3.4 of 12 hours; the effect on its score cannot be measured. |
| Bias in evaluation setup | Pass | Model-specific harnesses (disclosed). The reviewer is Opus 5.5 and is told the model name; Claude models fail review less often (2.0% vs 6.1%, p = 0.004), but the per-trial audit found no self-preference. Several tasks are judged by OpenAI models that agents may also query. |

### 3. Evaluation quality

| Question | Status | Notes |
| --- | --- | --- |
| Elicitation and resource adequacy | Sufficient | Constraining for Gemini 4 Argon (provider quota) |
| Scaffold fairness | Model-specific scaffolds | Only Claude Code's settings are published |
| Contamination | 100% of held-out data public (HF, since 2026-09-24); grader and reference repo public since 2026-10-13 | The benchmark is contaminated for every future run |
| Human completability | Not established | No task ships a working reference solution (all 21 `solution/` folders hold the same smoke server); the blog's "Human Researcher" line is undocumented |
| Score range | Floor and ceiling per task, clamped to [0, 100] | Floors decide much: maple-vlm 54/57 at 0, pokemon 41/57, svg 40/57; screen-difference's floor sits below a blind baseline; babylm's ceiling binds |
| Statistical adequacy | 1 run per model, task and wallet | Below the recommended 5. Near-replicate pairs differ by a median 5.2 points; several wallet winners are within noise. |
| Construct validity | Partially measures stated capabilities | Realistic open-ended tasks, but several reward identifying the evaluation source, and on 8 of 21 tasks a larger wallet buys the strongest models nothing |

### Extension: research vs. benchmark gaming

Every audited trial was classified by what produced its score ([`data/summary.md`](data/summary.md)):

| Classification | Trials | Share |
| --- | --- | --- |
| Research: a transferable idea | 2 | 1% |
| Engineering: legitimate, standard techniques and tuning | 271 | 72% |
| Grey area: exploits the benchmark rather than the problem | 23 | 6% |
| Reward hack: breaks an explicit rule | 13 | 3% |
| No gain | 69 | 18% |

| Model | Research | Engineering | Grey area | Reward hack | No gain | Confirmed false positives |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Opus 5.5 | 2 | 53 | 5 | 0 | 3 | 0 |
| GPT-6 Astra | 0 | 51 | 3 | 1 | 8 | 0 |
| Claude Fable 5.1 | 0 | 45 | 5 | 8 | 5 | 4 |
| Gemini 4 Argon | 0 | 45 | 6 | 3 | 9 | 1 |
| DeepSeek V4.1 Flash | 0 | 40 | 4 | 0 | 19 | 0 |
| Muse Wonder | 0 | 37 | 0 | 1 | 25 | 0 |

- **No trial was judged plausibly novel.** What wins is the standard recipe done carefully: fine-tune or distil the
  strongest allowed public model and serve it efficiently. Opus wins 13 of 21 tasks at every wallet by executing that
  recipe across more tasks.
- **Rule-breaking is concentrated in Fable:** 8 trials, mostly selecting on public benchmark files. Opus has none.
- **Memory vs. skill.** Sources were mostly found by investigation, not recall
  ([`data/source_origin.json`](data/source_origin.json)). One task, data-efficient pretraining, rewards a recalled
  public recipe: every trial that used the Muon optimizer, written from memory, averages 65.8, against 27.4 for the
  rest. The "no Slowrun lookup" rule cannot check that.

### Per-task verdicts

| Task | Scoring (task log) | Design | Key finding |
| --- | --- | --- | --- |
| [AI-text detection](tasks/ai-text-detection.md) | **CONSTRUCT** | unfair | Recognising DetectRL-X is worth ~27 points |
| [Data-efficient pretraining](tasks/babylm-replay.md) | minor | minor | Ceiling binds; rewards a recalled recipe |
| [Voice endpointing](tasks/end-of-turn.md) | minor | minor | Same window judged differently; DeepSeek `61zfoj` probable false negative |
| [Inverse dynamics model](tasks/idm-training.md) | minor (unconfirmed) | minor | Label-distillation loophole decides $50 within noise |
| [Math proof simplification](tasks/lean-simplification.md) | minor | minor | `release_ready: false`; agents cannot run the checker |
| [Lean proof validity](tasks/lean-validity.md) | minor | minor | Undisclosed held-out shift; $10 decided by 0.04 points |
| [AR to diffusion](tasks/llm-diffusion.md) | **IMPOSSIBLE + FP** | unfair | Undefined deciding rule; recognisable speed gate |
| [LLM post-training](tasks/llm-post-train.md) | **FP** | minor | Selection on graded GPQA zeroed twice, passed once |
| [Vision for a ternary LM](tasks/maple-vlm.md) | **FN + CONSTRUCT** | unfair | Floor contradicts the request; raised mid-run |
| [Music transcription](tasks/music-transcription.md) | minor | minor | Undisclosed soundfonts; every winner fingerprinted them |
| [OCR latent compression](tasks/ocr-latent-compression.md) | minor | minor | Promised provenance check missing |
| [PII redaction](tasks/pii-redaction.md) | minor | minor | Both splits are a public test set |
| [Pokémon Random Battle](tasks/pokemon-random-battle.md) | **FN** | unfair | Uncalibrated floor; winners within noise |
| [Figure to TikZ](tasks/scitikz.md) | minor | minor | No floor; $50 decided by 0.0002 raw |
| [Screenshot diffing](tasks/screen-difference.md) | **FP** | unfair | A blind paragraph beats 14 of 18 trials |
| [Screenshot generation](tasks/screenshot-generation.md) | minor | minor | Probable render failure on the grading host |
| [Speculative drafting](tasks/speculative-drafting.md) | OK | fair | Deterministic grading, clear margins |
| [SVG generation](tasks/svg-generation.md) | minor | minor | Undisclosed difficulty shift; 40/57 at 0 |
| [Ternary quantization](tasks/ternary-ptq.md) | **FP** | minor | Rubric omits "select": 4 confirmed false positives |
| [Video frame interpolation](tasks/video-frame-interpolation.md) | minor | minor | Pilot task; probable infrastructure timeout |
| [Zero-shot classification](tasks/zero-shot-classification.md) | minor (unconfirmed) | minor | Upstream sources of a banned dataset not named |

## Limitations

- **Six of 19 models audited per trial.** Leaderboard-wide statistics use all 1,197 trials.
- **No submitted files.** Judgements come from trajectories (tool output truncated to 4,000 characters per step) and
  grade pages. A zeroed trial's pre-review score is unpublished, so false negatives cannot be restored in the ranking.
- **Model review.** Per-trial classifications were made by model reviewers. Every confirmed false positive and every
  winner-relevant call was re-checked by the lead auditor, and the line between research and engineering is a
  judgement call.
- **Dataset visibility history.** The Hugging Face dataset is public now; its visibility during the runs is unknown.
- **Rubric mapping.** The task-design findings were made by the task reviewers and re-mapped onto the rubric's 2a
  codes for the threshold count. The verdict is Flawed under either the original or the re-mapped reading.

## Disclaimer

This is a full review of all 21 tasks and of six models' 378 trials. Our open questions are listed in
[findings.md](findings.md#questions-for-induction-labs). The most important:

1. Was the `<task>/private/` data public while the trials ran, and which HF token did agents receive?
2. Why do 38 trials graded with the review skipped count on the leaderboard?
3. Why were 62 of 63 Gemini 4 Argon trials re-run, and were any re-runs triggered by score?
4. Why does ternary-ptq's rubric omit "select"?
5. Why was maple-vlm's floor raised mid-evaluation, and why is it measured under different request settings than
   those graded?

This review uses the format and rubric of Epoch AI's Benchmark Reviews. It is an independent review and is not
produced or endorsed by Epoch AI.

## Notes

1. Leaderboard: <https://www.frontierml.org/data/>. Methodology post: <https://www.frontierml.org/blog/>
   (2026-10-13).
2. Repository: <https://github.com/induction-labs/frontier-ml> at `31837e0`. Tasks dataset:
   <https://huggingface.co/datasets/inductionlabs/frontier-ml-tasks> at `925401fb` (`private: false`,
   `gated: false`, created 2026-09-24, last modified 2026-10-13; 7,660 files under `<task>/private/` for all 21
   tasks).
3. Code citations: `frontier_ml/harbor_plugin.py:521-526` (`agent_hf_token`: `FML_AGENT_HF_TOKEN`, else `HF_TOKEN`);
   `frontier_ml/grading.py:67` (`review_skip_enabled`); `frontier_ml/review_trajectory.py:154` (the reviewer's
   evidence includes the agent's `name`, `version` and `model_name`).
4. Run dates: Opus, Fable and Astra Oct 3–5; Muse Oct 12; Argon Oct 13 (code release day); DeepSeek Oct 20.

## Reproduce

```bash
sh scripts/fetch.sh /tmp/frontierml-raw                    # ~160 MB: site pages, 1,197 trial records, 378 trajectories
python3 -I scripts/build_workspace.py /tmp/frontierml-raw /tmp/frontierml-ws
python3 -I scripts/sensitivity.py data/all_trials.csv data/trial_reviews data/adjudication.json > data/sensitivity.md
python3 -I scripts/summarize.py data/trial_reviews data/adjudication.json > data/summary.md
```
