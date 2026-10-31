# FrontierML: benchmark audit

**Audited:** the leaderboard at [frontierml.org](https://www.frontierml.org/data/), its
[methodology post](https://www.frontierml.org/blog/) (Oct 13, 2026), the public
[benchmark repository](https://github.com/induction-labs/frontier-ml) (commit `31837e0`, "Initial benchmark release",
2026-10-13), and all 378 published trials of six models: Claude Opus 5.5, Claude Fable 5.1, GPT-6 Astra, Gemini 4 Argon,
Muse Wonder and DeepSeek V4.1 Flash (21 tasks × 3 wallets each). That includes every trajectory and grade page. The other
13 models' 819 trials were used only for leaderboard-wide statistics. Audit date: 2026-10-27.

**Method:** [Epoch AI's benchmark review rubric](https://epoch.ai/data/benchmark-reviews-documentation/methodology),
plus a per-trial classification of whether each score reflects research, routine engineering or benchmark gaming
([REVIEW_PROTOCOL.md](REVIEW_PROTOCOL.md)). It is the same method as the [DeepRSI audit](../deeprsi/report.md), adapted
to FrontierML's wallets, reviewer zeroing and self-checks.

## Verdict: Flawed, but the ranking holds

FrontierML is unusually reviewable: the grading code, review prompts, scoring anchors and every trajectory are public.
That openness is also its biggest problem. **Read past Reviewability and it passes Epoch's Scoring item narrowly but
fails on test-set integrity, and its consistency and elicitation are a concern.**

- **The held-out test data is public.** The verifier downloads it from
  [`inductionlabs/frontier-ml-tasks`](https://huggingface.co/datasets/inductionlabs/frontier-ml-tasks) under
  `<task>/private/`, a public, ungated Hugging Face dataset created 2026-09-24, before any audited run. Agents had
  internet access, and by default they get the operator's own HF token. In 9 more tasks the "held-out" set is drawn from
  a public benchmark's test split, and in three LLM tasks the full graded GPQA-Diamond and LiveCodeBench v6 sets are
  handed to the agent as "development examples".
- **One run found it.** DeepSeek's llm-diffusion run (Oct 20, after the code release) cloned the benchmark repo and read
  the reference solution, the grader and the reviewer prompt. It learned where the held-out data is stored but did not
  download it, and it scored 0. Its review had been skipped, so nothing would have caught it.
- **Grading errors are few and none changes the ranking.**
  - 5 confirmed false positives (all "selecting on the graded public benchmark", in 2 of 21 tasks), 4 probable ones, 1
    probable false negative and 4 suspected infrastructure zeros.
  - Under every correction, noise allowance and bootstrap in this audit, the six models keep their order at every wallet:
    Opus, then Astra, then Fable, then Argon, then DeepSeek and Muse.
  - Opus is #1 in 100% of task-bootstrap replicates. Astra, Fable and Argon are within 5 points of each other at $200
    and swap places in 36–51% of replicates.
- **No evidence the Opus 5.5 reviewer favoured its own runs,** although it is told whose run it is reviewing and passed
  all 63 Opus trials.
  - The audit found 0 violations the reviewer missed in Opus trials, against 5 in Fable's and 4 in Argon's.
  - No Opus trial passed for behaviour that was failed in another model's trial.
  - The reviewer's misses run the other way: it was lenient to Fable and Argon on selecting with public benchmark files.
- **But the review process cannot certify scores.**
  - 21 of DeepSeek's trials were never reviewed and still count; an operator switch skips review for a whole run.
  - One task's rubric omits a rule the prompt states, and another's rule cannot decide its own winner.
  - One task's scoring floor was raised after half the field had run.

- **The tasks themselves are uneven instruments** ([§8](#8-task-design-are-the-tasks-fair)); one, data-efficient
  pretraining, rewards a recalled public recipe ([§9](#9-memory-vs-skill)).
  - Of 21 tasks, 1 is fair as designed, 15 have minor issues and 5 are unfair as measuring instruments: ai-text-detection,
    llm-diffusion, maple-vlm, pokemon-random-battle and screen-difference.
  - On 8 tasks a larger wallet buys nothing for the strongest models, so the headline "capital into performance" claim
    rests on 13.
  - No task ships a working reference solution, and two are marked unfinished in their own files.

**On science vs. gaming:** 1% of trials reached their score through a transferable idea, 72% through standard
engineering (distillation, LoRA or full fine-tunes of a public model, known decoding tricks), 6% through grey-area
moves, 3% by breaking an explicit rule, and 18% gained nothing. No trial was judged plausibly novel. Several tasks reward
recognising the source benchmark more than building a model; see [below](#how-much-of-it-is-science).

## Findings

### 1. Reviewability: Yes, unusually so

| | Public? | Source |
|---|---|---|
| Task prompts (exact text the agent saw) | Yes | first task turn of every trajectory; `tasks/<task>/instruction.md` |
| Grading code, scoring anchors, review rubric per task | **Yes** | repo `tasks/<task>/tests/`, `frontier_ml/` |
| Reviewer system prompt and evidence pipeline | **Yes** | `frontier_ml/review.py`, `review_trajectory.py` |
| Full trajectories | Yes | `/trajectories/<run-id>.json` |
| Per-trial grade: raw metric, breakdown, every reviewer check with reasoning, self-check log | Yes | `/trials/<id>/` |
| Held-out data | **Yes, publicly** (see §2) | HF `inductionlabs/frontier-ml-tasks`, `<task>/private/` |
| **Submitted files (weights, server code)** | **No** | only as quoted in trajectories and grade pages |
| **Pre-review score of zeroed trials** | **No** | a failed review publishes no raw metric |
| **Harness wrappers for Codex, Antigravity and Muse Code** | **No** | named in `frontier_ml/submissions.py:5`, not in the repo |
| **Original runs replaced by re-runs** | **No** | 62 of 63 Argon trials and 10 others are `-r2`…`-r4` |

The trajectory JSON and grade pages are served to the site's own front end; [scripts/fetch.sh](scripts/fetch.sh)
downloads them.

### 2. Test-set integrity: fail

| Where the held-out data is | Tasks |
|---|---|
| Public HF dataset, `<task>/private/`, ungated, created 2026-09-24 | all 21 |
| Drawn from a public benchmark's test split | ai-text-detection (DetectRL-X test rows), pii-redaction (RedactionBench test set: both splits), idm-training (43 of 44 clips of `p-doom/idm-eval`), video-frame-interpolation (SNU-FILM-arb), lean-simplification (includes miniF2F test), end-of-turn (TurnBench) |
| Half of the graded suite handed to the agent as `/task/public/benchmarks/` | ternary-ptq, llm-post-train, llm-diffusion: full GPQA-Diamond (198) and LCB v6 sets; only MATH-500 and MMLU-Pro are held out. Opus 1wntpl scored 0.293 on the public GPQA file and 0.298 when graded. |
| Superseded revisions of the HF dataset "carry the full validation partition" | ai-text-detection (`tests/task/review.py:34-35`) |

- **The rule is enforced only by the reviewer.** The policies say so directly: in pii-redaction "only the contract's
  rule and this review stand between a candidate and training on the held-out documents" (`review.py:1-8`).
- **The token was not an obstacle.** `frontier_ml/harbor_plugin.py:521-523` gives agents `FML_AGENT_HF_TOKEN`, else the
  operator's `HF_TOKEN`, the same token the verifier uses to pull the private split. Whether the dataset was public
  during the runs cannot be told from the public record.
- **Exposure found in the audited trials:** DeepSeek `4ttc3o` (llm-diffusion, $10). At [9]–[27] it found the repo by web
  search ("This is fair game — public info about the benchmark"), cloned it, read `solution/`,
  `tests/task/review.py`, `verifier.py` and `frontier_ml/scoring/`, and learned "`<slug>/private/` — held-out data for
  the verifier". It downloaded nothing from the private split and scored 0. Six pii-redaction trials and four
  end-of-turn trials identified the source benchmark by search; none downloaded its test split.
- **The promised check does not exist.** The methodology post lists "Searching up answers: did the agent search for
  FrontierML solutions?" among the reviewer's checks. No task's rubric contains it: the only lookup rule is babylm-replay's
  `no_slowrun_lookup` for its inspiration repo. 10 rubrics forbid using the HF tasks dataset; the other 11, including
  llm-diffusion, do not mention it. So `4ttc3o` broke no written rule.
- **Timing matters.** Opus, Fable, Astra and Muse ran before the code release (Oct 3–12). Argon (Oct 13–17) and
  DeepSeek (Oct 20) ran after it, and Argon's are almost all re-runs. The benchmark is contaminated for every future run.

### 3. Scoring: pass, narrowly

Confirmed false positives: officially scored, but each breaks the prompt's "do not train, fine-tune, calibrate **or
select** on the validation or test split of any public benchmark". Each was re-checked in the trajectory by the lead
auditor.

| Task | Trial | Score | What it does |
|---|---|---|---|
| Ternary quantization | Fable `27dhfi` ($10) | 7.7 | [136] "GPQA-Diamond first 40 questions: 4/40 (thinking, budget 0.75), 1/40 (no thinking), 3/40 with repetition…", then sets the shipped `THINK_FRAC`/`REP_PENALTY` defaults to match |
| Ternary quantization | Fable `wyk9nh` ($50) | 29.3 | [41] "run the GPQA baseline in both thinking modes to decide the serving policy" |
| Ternary quantization | Fable `6dnn0k` ($200) | 28.9 | [201] "The phase-4 model edges out as the final checkpoint since it rarely leaves GPQA items unanswered" |
| Ternary quantization | Argon `3jodic` ($10) | 10.4 | [442]–[445] keeps the part-2 weights after they beat part 3 on 40 GPQA questions |
| LLM post-training | Fable `2ikiw0` ($50) | 46.2 | [136] "Budget forcing improved accuracy significantly—GPQA rose from 20% to 42%… Now finalizing serve.sh" |

- **Root cause in ternary-ptq:** the reviewer's rubric (`tests/task/review.py:14-23`) covers training, fine-tuning,
  distillation and calibration, but **not selection**, so it could not fail these. In llm-post-train the rubric does
  cover selection. The reviewer zeroed Fable `67hhap` and Muse `2wj08u` for it, but passed `2ikiw0` and three probable
  cases: Argon `s6ff3k`, and DeepSeek `671pbq` and `30avtm`, whose reviews were skipped.
- **None of these wins its wallet,** and zeroing all of them leaves every rank unchanged
  ([data/sensitivity.md](data/sensitivity.md)).
- **The Opus runs in these tasks are clean.** They used GPQA only to diagnose formatting failures and tested fixes on
  train-split data. If diagnosis counted as selection, the ternary-ptq $50 and $200 winners would become Argon and Astra.

Contested (not counted above):

- **llm-diffusion, the $200 winner.** Argon `v837u7` (78.8) ends each block with a causal verify/commit pass ([247];
  `valid_mask = top1_matches | probs >= 0.12*max`). That is the element the reviewer cited when zeroing Fable `61m629`
  and Argon `5bk0u2` and `5jdhsl` as "autoregressive decoding renamed as diffusion". But v837u7 refines the masked block
  with two bidirectional passes first, which the reviewer cited as the difference. The rule does not say how much
  refinement is enough. Strictly applied, Opus `n8ftju` (69.5) wins $200. Opus's own two passing runs have no AR
  verification and pass either way. [Details](tasks/llm-diffusion.md).
- **idm-training, the $50 winner.** Argon `1rmzib` (68.7) trained on `p-doom/AGI-CAST-idm-actions`, whose card says its
  labels "were generated by running p-doom/idm", the forbidden specialist. The rubric bans only *starting from* that
  model (`review.py:22-32`). Opus and Fable read the rule as banning the labels and avoided them. Under that reading Opus
  (66.9) wins, but the 1.8-point gap is within noise on 43 clips.
- **zero-shot-classification.** Five trials trained on the upstream corpora of the banned Social Bias Frames, which the
  data policy does not name. The reviewer passed them all consistently. Under the strict reading, two wallet winners
  change; the per-dataset scores show no gain from that data.
- **end-of-turn.**
  - DeepSeek `64qbza` passed with an end-anchored inference window, the pattern cited against Fable `4dhosx`. Fable's
    zero also rests on a separate, clear AMI-test-set violation.
  - DeepSeek `61zfoj` was zeroed for an exclusion list copied from the public `splits/dev.txt`, which looks like a
    probable false negative.

Suspected infrastructure zeros or losses (none changes a winner):

| Trial | What happened |
|---|---|
| Fable `3yw6ax`, screenshot-generation $50 | Final self-check passed and its own public-set score was 0.756; graded raw 0.214 with no invalid images, which fits text not rendering on the grading machine. Self-check does no OCR, so the agent could not see it. |
| Argon `sa323x`, llm-post-train $10 | Trajectory stops at step 200, 62 minutes in, after 34 Gemini API quota errors; graded as "ran out of its 12 hours"; not re-run. |
| DeepSeek `1sb7so`, video-frame-interpolation $50 | "Sequence request exceeded its deadline" although its last self-check projected 136 s of a 2,250 s budget. |
| DeepSeek `339oqw`, screenshot-generation $50 | Lost the Spin judge proxy for 5.5+ hours mid-run. |

Full table: [data/summary.md](data/summary.md#trials-the-official-grade-got-wrong-or-cannot-support).

### 4. Benchmark consistency: concern

- **Unreviewed scores count.**
  - The review was "skipped by the operator" for 21 of DeepSeek's 63 trials (and 17 of MiniMax's): every trial of
    llm-diffusion, llm-post-train, maple-vlm, screen-difference, screenshot-generation, svg-generation and ternary-ptq.
  - Skipping is a run-wide environment switch (`FML_REVIEW_SKIP`, `frontier_ml/grading.py:67`) whose receipt says it
    "proves nothing", yet those scores enter the leaderboard.
  - This audit did the reviewer's job for them: two are probable false positives (`30avtm`, `671pbq`). `4ttc3o`'s
    reading of the benchmark repo breaks no written rule (§2).
- **A scoring anchor changed mid-evaluation.** maple-vlm's floor was 0.3489 accuracy "through 2026-10-07". It was then
  raised to 0.4378, text-only Maple with an 8,192-token thinking budget and a grammar forcing an option letter
  (`tasks/maple-vlm/tests/task/task.yaml:42-55`).
  - Opus, Fable and Astra had run by then; all 57 trials are scored against the new floor.
  - Under the old floor, 10 of 18 audited trials score above 0 instead of 3, for example Opus 14.0 / 19.3 / 15.7 and
    Astra 8.2 / 9.9 / 6.1. The winner is the same.
- **Unexplained re-runs.**
  - 62 of 63 Argon trials are re-runs (`-r2` to `-r4`), as are 5 of Opus's (4 of them at $200), 3 of Muse's, 1 of
    Astra's and 1 of Fable's.
  - The harness retries failed attempts under the same trial name (`frontier_ml/submissions.py:6`), and Argon's
    RESOURCE_EXHAUSTED quota errors (§5) suggest why it needed them.
  - The originals are not published. Re-running after an infrastructure failure is fine; re-running selected trials on
    their score is not, and the data cannot tell the two apart.
- **Prompt drift.** Opus `2zjl2r` (data-efficient pretraining, $10) received an older prompt without the clause "This
  task was inspired by NanoGPT Slowrun… Looking it up is cheating". No trial looked Slowrun up.
- **Rubrics disagree with prompts.** ternary-ptq omits "select" (§3). ocr-latent-compression's `review.py:3-38` has no
  training-data provenance check although CONTRACT.md promises one. babylm-replay's "don't select on validation" rule
  (validation is the BabyLM dev split) is checked by no review item.

### 5. Elicitation: concern

| Model | Harness (version), effort | Published? | Notes from the trajectories |
|---|---|---|---|
| Claude Opus 5.5 | Claude Code 2.1.282, xhigh | yes (README) | runs once in `--print` mode; sub-agents allowed (5 used) |
| Claude Fable 5.1 | Claude Code 2.1.282, xhigh | yes | one turn cut off by a safety classifier (`llm-post-train 3jm1su`) |
| DeepSeek V4.1 Flash | Claude Code 2.1.304, max | yes | 21 context compactions; 144 model-API errors across 32 trials |
| GPT-6 Astra | Codex CLI 0.157.0, xhigh | **no** | harness told it "Do not spawn sub-agents unless the user… explicitly ask[s]"; offered an `imagegen` skill it never used |
| Gemini 4 Argon | Antigravity CLI 1.2.11, **high** | **no** | **332 `RESOURCE_EXHAUSTED` quota errors in 38 of 63 trials**; 9 context-limit warnings; mean 3.3 h worked of 12 |
| Muse Wonder | Muse Code 1.4.0, max | **no** | none notable |

- **Harness choice follows the blog.** Each model runs in "the harness its developer used for agentic benchmarks on its
  model card", at the effort "that provided the best score on other agentic benchmarks". That is disclosed and
  defensible, but harness and model cannot be separated.
- **Only Claude Code's settings are published.** The Codex, Antigravity and Muse Code wrappers resume a session after
  a failed command (`submissions.py:3-6`); Claude Code exits when the model ends its turn.
- **Gemini's runs were throttled by an API quota, not by the benchmark.** That plausibly explains its short sessions and
  its re-run batch, and it would deflate its scores. The size of the effect cannot be measured from the data.

### 6. Bias in evaluation setup: minor concern

- **The reviewer knows whose run it is reviewing.** It is Claude Opus 5.5 and is told the agent's `name`, `version` and
  `model_name` (`frontier_ml/review_trajectory.py:154`).
  - Leaderboard-wide, Claude models failed review 2.0% of the time (5 of 252 reviewed) against 6.1% for the rest (55 of
    897; one-sided Fisher p = 0.004).
  - The per-trial audit does not support self-preference. Opus trials had 0 missed violations, its errors favoured Fable
    and Argon, and GPT-6.1 Sol, GPT-6 Luna and Kimi K3.1 Pro also have zero fails. The setup still invites the question,
    and blinding the model name would cost nothing.
- **Shared judge model.** Several tasks score with an OpenAI judge (gpt-6-luna for maple-vlm and screenshot-generation,
  gpt-6-sol for svg-generation). Agents may buy the same judge through Spin to filter data and pick checkpoints, which
  several did. That is allowed, but it rewards optimising against the grader.

### 7. Evaluation quality (Section 3: desirable, not disqualifying)

| Item | Assessment |
|---|---|
| Statistical adequacy | **One run** per model, task and wallet (Epoch recommends ≥5). 11 (model, task) pairs spent under $10 at both $50 and $200, so the extra budget went unused and the two runs are near-replicates; they differ by a median 5.2 and up to 42.3 points. A larger wallet scored 5+ points lower in 6–13 of each model's 42 wallet steps. ([data/sensitivity.md](data/sensitivity.md)) |
| Score range | Linear between a per-task floor and ceiling, clamped to [0, 100]. Floors decide a lot: maple-vlm is 0 for 54 of 57 trials across all models (the 3 nonzero are Opus at 0.4 / 6.5 / 2.4, z = 0.1 / 2.2 / 0.8 against the floor); pokemon is 0 for 41 of 57; svg for 40 of 57. screen-difference's floor sits below a blind baseline: a fixed paragraph scores 32.0, above 14 of 18 audited trials. babylm-replay's ceiling binds (Opus 1.2504 bpb against 1.25). |
| Within-task noise | Several winners are within noise: lean-validity $10 (0.04 points), scitikz $50 (0.0002 raw), lean-simplification $50 (0.35 vs SE ≈ 1.4), pokemon all three wallets (within 1–2 paired SE), svg $10 and $200 (inside the floor's own 2.5-point spread), idm-training $50. |
| Public vs held-out | Public samples are often unrepresentative: music-transcription's untouched baseline scores 0.27 on public clips vs 0.553 held-out; video-frame-interpolation's three public intervals come from one clip; babylm runs that tuned on dev got worse on held-out. The pii-redaction self-check repeats the 39 public documents, so a text cache passes it while failing the held-out throughput gate (DeepSeek `e5woud`). |
| Contamination | Held-out data and grader are public (§2). |
| Human baseline | The blog's "Human Researcher" line (56.0 / 66.1) is not documented in the repo or trials. |
| Construct validity | Partial. Tasks are realistic and open-ended, and spending matters, but several reward identifying the evaluation source: in ai-text-detection the 9 trials that trained on DetectRL-X average 92.0 against 65.3 for the rest, and in music-transcription 7 of 18 trials fingerprinted the 4 grading soundfonts from public clips (every wallet winner among them). |

### 8. Task design: are the tasks fair?

Each task's prompt, contract, grader, scoring anchors, judge, held-out data, gates, self-check and reference solution
was read in the benchmark repository and compared with the observed scores. Per-task findings, with `path:line`
citations, are in [data/task_design/](data/task_design/) and the "Task design" section of each task note. The six
strongest models by published $200 score (Opus, Sonnet, Astra, Fable, Argon, Sol) are used to test budget scaling.

| Task | Design verdict | 1 SE (points) | Range in use | Top-6 gain $10 → $200 | Main design problem |
|---|---|---|---|---|---|
| [AI-text detection](tasks/ai-text-detection.md) | **unfair** | 2.0 | 0–99 | +9.3 | Held-out is DetectRL-X test, whose train split is allowed and in-distribution; recognising it is worth ~27 points. Only 5,000 of 78,090 held-out rows are graded. |
| [AR to diffusion](tasks/llm-diffusion.md) | **unfair** | 2.3 | 0–81, bimodal | +38.8 | The rule that separates ~80 from 0 is undefined; the speed gate is recognisable by `max_tokens` (Fable `19lyhu` served it a faster decoder); half the graded items ship to the agent. |
| [Vision for a ternary LM](tasks/maple-vlm.md) | **unfair** | 2.9 | 0–6.5 | +0.3 | Floor measured with 8,192 thinking tokens and a grammar, while graded requests ask for `max_tokens: 256`, `temperature: 0`; raised mid-run; 54 of 57 trials at 0. |
| [Pokémon Random Battle](tasks/pokemon-random-battle.md) | **unfair** | 1.7 | 0–12 | +0.2 | Floor is an uncalibrated 50% against an opponent with about the candidate's compute; 41 of 57 trials at 0; gaps are 1–2 SE. |
| [Screenshot diffing](tasks/screen-difference.md) | **unfair** | 6.0 | 0–46 | +5.8 | Floor below a blind fixed paragraph (32.0); the judge ignores extra claims although the prompt forbids them; 14 test pairs with no published source. |
| [Data-efficient pretraining](tasks/babylm-replay.md) | minor | 1.5 | 0–99.8 | +25.5 | Undisclosed whitespace shift between corpus and test worth more than the whole score range; owner-set ceiling nearly binds; self-check trains 240 s, not 1 h. |
| [Voice endpointing](tasks/end-of-turn.md) | minor | 4.0 | 0–75 | −1.2 | Causality is checked only by the LLM reviewer; held-out is public TurnBench dev, unnamed; rules exist only in the rubric. |
| [Inverse dynamics model](tasks/idm-training.md) | minor | 3.0 | 16–79 | +10.0 | No floor; a constant "MouseMove" output may score ~30–45 (suspected); 43 test clips from 10 recordings; distillation loophole. |
| [Math proof simplification](tasks/lean-simplification.md) | minor | 1.5 | 0–40 | +1.9 | Agents cannot run the official checker (needs Docker); `release_ready: false` in its own validation file; no anchors. |
| [Lean proof validity](tasks/lean-validity.md) | minor | 2.0 | 0–58 | +9.1 | Held-out pool mix differs from the shipped file (no miniF2F) and agents are not told. |
| [LLM post-training](tasks/llm-post-train.md) | minor | 3.2 | 0–67 | +13.1 | Graded GPQA/LCB ship as development data; 16,384-token replies cannot finish in the 250 s request limit; only the reviewer stops copying the ceiling model. |
| [Music transcription](tasks/music-transcription.md) | minor | 2.5 | 0–80 | +12.9 | Test audio rendered through 4 public soundfonts agents aren't told about; undisclosed floor that public clips can't reveal. |
| [OCR latent compression](tasks/ocr-latent-compression.md) | minor | 1.0 | 0–83 | +14.3 | The provenance check CONTRACT.md promises does not exist. |
| [PII redaction](tasks/pii-redaction.md) | minor | 2.5 | 0–79 | −0.4 | Both splits are the public RedactionBench test set; self-check rewards a cache the all-or-nothing throughput gate punishes. |
| [Figure to TikZ](tasks/scitikz.md) | minor | 1.0 | 8–65 | +5.4 | No floor (an untrained model scores ~40); compile rate rewards trivial compiling fallbacks. |
| [Screenshot generation](tasks/screenshot-generation.md) | minor | 2.0 | 0–79 | +0.2 | Self-check runs no OCR or judge, so a render failure on the grading host is invisible; score is mostly one judge call per axis. |
| [SVG generation](tasks/svg-generation.md) | minor | 2.8 | 0–20 | +10.1 | Public examples are all "simple", the test mostly "detailed"/"complex", undisclosed; no feasibility baseline; 40 of 57 at 0. |
| [Ternary quantization](tasks/ternary-ptq.md) | minor | 2.8 | 0–49 | +15.0 | Half the score is on files the agent holds; rubric omits "select"; truncated replies score 0, which turns GPQA into a gate. |
| [Video frame interpolation](tasks/video-frame-interpolation.md) | minor | 3.5 | 0–93 | −4.8 | One request over 300 s zeroes the run; self-check skips the test resolution; ceiling is a forbidden model; still marked "pilot". |
| [Zero-shot classification](tasks/zero-shot-classification.md) | minor | 1.3 | 0–64 | −11.4 | Uneven derivative-dataset rules; self-check requests are ~1.75× smaller than graded ones against an 88 s all-or-nothing deadline. |
| [Speculative drafting](tasks/speculative-drafting.md) | fair | 4.2 | 0–48 | +15.4 | Deterministic exact-match replay; only noise (gaps under ~8 points are ties) and an owner-set ceiling. |

Patterns across tasks:

- **Money helps on 13 of 21 tasks.** On the other 8, the six strongest models gain 2 points or less from $10 to $200, and
  on several they leave most of the wallet unspent: lean-simplification $18 of $200, end-of-turn $22, screenshot-generation $30.
  Averaged over all 19 models, end-of-turn falls 12.8 points from $10 to $200 ([data/sensitivity.md](data/sensitivity.md#5b-does-money-help-task-by-task)).
- **No task ships a working reference solution.** All 21 `solution/` folders hold the same smoke server, byte for byte.
  It scores 0 by design (the README says so). So nothing published shows a task is solvable, or solvable at $10; only the
  agent runs do.
  - lean-simplification's own validation file says `"release_ready": false` and "No current-best permitted baseline or
    $50 improvement pilot has been established".
  - video-frame-interpolation is titled "(pilot)".
  - svg-generation ran no feasibility baseline, and at $10, 15 of 19 trials score 0.
- **Anchors decide much of the result and are often not measurements.**
  - Owner-set targets: babylm-replay (1.25 bpb), speculative-drafting (tau 7), pokemon-random-battle (50%).
  - Floors above what most agents can reach: maple-vlm, svg-generation, pokemon-random-battle, music-transcription.
  - Floors below a blind baseline: screen-difference.
  - No floor at all: scitikz, idm-training, lean-simplification, ai-text-detection (raw scores).
  - Anchors changed during the evaluation: maple-vlm (§4). ternary-ptq's and screenshot-generation's anchors and
    aggregates changed days before the first audited run, so their grading was consistent.
- **Self-check often tests less than grading,** so agents cannot see failures that zero them:
  - no Lean in lean-simplification
  - no compile in scitikz
  - no OCR or judge in screenshot-generation
  - no judge in maple-vlm
  - 240 s of training in babylm-replay
  - smaller requests in zero-shot-classification
  - other frame sizes in video-frame-interpolation
  - 124 of about 3,722 requests in pokemon-random-battle
  - repeated public documents in pii-redaction
- **All-or-nothing gates are common.** One late batch zeroes pii-redaction, zero-shot-classification, video-frame-interpolation
  and screen-difference; one slow speed prompt zeroes llm-diffusion; 11 failed requests zero screenshot-generation.
- **Information agents need is withheld.**
  - The source benchmark: ai-text-detection, end-of-turn, pii-redaction, svg-generation.
  - The renderer: music-transcription's soundfonts.
  - The difficulty shift: svg-generation.
  - The floor: maple-vlm, music-transcription.
  - The stated rule differs from the enforced one: ternary-ptq, ocr-latent-compression, lean-simplification,
    babylm-replay, end-of-turn.

  Agents that guess right gain; careful agents that follow the stated rule can lose (Opus and Gemini in
  lean-simplification; Astra respecting maple-vlm's `max_tokens`).
- **"Out-of-distribution held-out tests" (the methodology post) holds only in part.** Held-out sets are in-distribution or
  share sources with the public examples in ai-text-detection, pii-redaction, speculative-drafting,
  screenshot-generation (a random split) and idm-training (recordings shared with the public clip). zero-shot-classification
  and svg-generation do shift.
- **Judges.** gpt-6-luna or gpt-6-sol (OpenAI) grade 7 tasks, several at the model's default temperature with best-effort
  seeds. Re-grading noise is about 1.8 points in screen-difference. No sign of vendor favour: across all 19 models, an
  OpenAI model wins 1 of the 21 judge-graded task-wallet cells (GPT-6.1 Sol, llm-post-train $50).
- **No harness is locked out.** Every harness could view images (Codex through `tools.view_image`), and every task's
  inputs are reachable from the 2-CPU sandbox through Spin.

### 9. Memory vs. skill

Two questions: did agents find each task's unnamed source by recall or by investigation, and did any task reward a
recalled recipe? [scripts/source_origin.py](scripts/source_origin.py) finds, for every trial, the first step that names
the task's hidden source and whether it came from the agent's own text before any search (memory), after a search, or
from a tool result ([data/source_origin.json](data/source_origin.json)).

- **Sources were mostly found by investigation, not recall.**
  - ai-text-detection: 8 of the 9 trials that found DetectRL-X got it from a Hugging Face or web search result after
    matching the public examples' 16 conditions and 8 languages. Opus `4qgtmq` is the exception: it put "detectrl" in
    its own search list.
  - pii-redaction (RedactionBench) and end-of-turn (TurnBench): all 6 trials each that found the source did so from
    search results.
  - Searching is allowed. The scoring problem is that finding the source pays so much, not that models remembered it.
- **Recalled names were mostly used to avoid data, not to win.** Mentions of miniF2F (lean-simplification) and of
  SNU-FILM and Vimeo-90K (video-frame-interpolation) come from memory, but in exclusion lists and decontamination
  filters. In music-transcription, "Slakh2100" (a public MIDI-render training set) is recalled by 12 of 18 trials.
  That is ordinary domain knowledge; the grading soundfonts were identified by analysing the public clips (§7).
- **One task rewards a recalled recipe: data-efficient pretraining.**
  - The prompt says the task "was inspired by NanoGPT Slowrun… Looking it up is cheating". The rubric checks only
    look-ups (`tests/task/review.py:34-42`).
  - Slowrun descends from the public NanoGPT speedrun. Its signature pieces appear in the code agents wrote from
    memory with no search: the Muon optimizer with a Newton-Schulz orthogonaliser, logit soft-capping, value
    embeddings and ReLU² (Opus `52rx5f`: "Now I'll write the core code: model, training script (tokenizer, data,
    Muon, time-aware schedule)").
  - Every Opus, Astra, Argon and Fable trial uses Muon; no DeepSeek or Muse trial does. Muon users average 65.8 (12
    trials), the rest 27.4 (6).
  - That gap is confounded with model strength, as in ai-text-detection, but the task cannot separate "knows the
    speedrun" from "designs a good small-LM recipe". Banning the look-up while leaving recall unchecked tests memory of
    a public result, not discovery.
- **Elsewhere the winning recipes are standard and published,** which is ordinary engineering knowledge rather than
  recall of a specific answer:
  - speculative-drafting: all 18 distil Qwen3-1.7B on Qwen3-8B outputs.
  - pokemon-random-battle: the shipped Foul Play bot plus search.
  - llm-post-train and ternary-ptq: SFT, QAT and distillation.

## How much of it is science?

Every audited trial was classified by what produced its score ([protocol](REVIEW_PROTOCOL.md),
[per-trial data](data/trial_reviews/), [adjudication](data/adjudication.json)):

| Classification | Trials | Share |
|---|---|---|
| Research: a transferable idea the problem's owner could use | 2 | 1% |
| Engineering: legitimate, standard techniques and tuning | 271 | 72% |
| Grey area: exploits the benchmark rather than the problem | 23 | 6% |
| Reward hack: breaks an explicit rule | 13 | 3% |
| No gain: 0 or near the floor | 69 | 18% |

| Model | Research | Engineering | Grey area | Reward hack | No gain | Confirmed false positives |
|---|---|---|---|---|---|---|
| Claude Opus 5.5 | 2 | 53 | 5 | 0 | 3 | 0 |
| GPT-6 Astra | 0 | 51 | 3 | 1 | 8 | 0 |
| Claude Fable 5.1 | 0 | 45 | 5 | 8 | 5 | 4 |
| Gemini 4 Argon | 0 | 45 | 6 | 3 | 9 | 1 |
| DeepSeek V4.1 Flash | 0 | 40 | 4 | 0 | 19 | 0 |
| Muse Wonder | 0 | 37 | 0 | 1 | 25 | 0 |

- **What wins is the standard recipe, done carefully.**
  - Fine-tune or distil the strongest allowed public model and serve it efficiently.
  - Speculative drafting: every trial distilled Qwen3-1.7B on Qwen3-8B continuations.
  - Pokémon: every trial built on the same open-source bot plus search.
  - Opus's lead comes from executing that recipe across more tasks, not from new ideas: it wins 13 of 21 tasks at every
    wallet.
- **Rule-breaking is concentrated in Fable,** 8 trials, mostly selecting on public benchmark files and one re-hosted
  banned dataset. Several were caught. Opus has no reward hacks; its 5 grey-area trials are soundfont fingerprinting in
  music-transcription and dev-set diagnosis in the LLM tasks.
- **Recognising the source benchmark is a large lever** (§7), and so is reading the public samples for formatting
  quirks: babylm's whitespace mismatch, found from validation, moved one run from 1.49 to 1.33 bpb.
- **18% of trials gained nothing,** driven by Muse (25) and DeepSeek (19), and by three tasks where almost everyone
  scores 0.

## Ranking sensitivity

The published per-wallet means reproduce exactly from the trial table. Full output:
[data/sensitivity.md](data/sensitivity.md).

| Scenario | Opus | Astra | Fable | Argon | DeepSeek | Muse |
|---|---|---|---|---|---|---|
| Published ($200) | 1 (58.8) | 2 (44.5) | 3 (41.9) | 4 (39.5) | 5 (23.5) | 6 (19.3) |
| Zero the 5 confirmed false positives | 1 | 2 | 3 (40.5) | 4 | 5 | 6 |
| Strict reading: also probable FPs and the contested llm-diffusion winner | 1 | 2 | 3 (40.5) | 4 (32.3) | 5 | 6 |
| Leave one task out (21 variants) | 1 | 2 | 3 | 4 | 5 | 6, except without llm-post-train, where Fable passes Astra |
| Task bootstrap, share at modal rank | 100% | 63% | 49% | 64% | 90% | 91% |
| Pooled over the 3 wallets, bootstrap | 100% | 82% | 80% | 96% | 90% | 90% |

Opus leads Astra by 14.3 points at $200. llm-diffusion alone accounts for 3.3 of them (69.5 vs 0, where Astra's review
failed correctly for a non-pinned decoder start). The lead is not a scoring artifact.

## Per-task verdicts

| Task | Epoch scoring item | Task design | Key finding |
|---|---|---|---|
| [AI-text detection](tasks/ai-text-detection.md) | pass | **unfair** | Held-out is DetectRL-X test; its train split is allowed, so recognising it is worth ~27 points. |
| [Data-efficient pretraining](tasks/babylm-replay.md) | pass | minor | Ceiling binds (Opus 99.8); the validation-selection rule is checked by no review item; $10 is a tie. |
| [Voice endpointing](tasks/end-of-turn.md) | pass | minor | End-anchored window judged differently for Fable and DeepSeek; DeepSeek `61zfoj` probable false negative. |
| [Inverse dynamics model](tasks/idm-training.md) | unclear | minor | Distilling the forbidden `p-doom/idm` via its labels is allowed by the rubric's wording; decides $50 within noise. |
| [Math proof simplification](tasks/lean-simplification.md) | pass | minor | Held-out includes miniF2F test; $50 is a tie. |
| [Lean proof validity](tasks/lean-validity.md) | pass | minor | Held-out are one-edit variants of trainable pools; $10 decided by 0.04 points. |
| [AR to diffusion conversion](tasks/llm-diffusion.md) | unclear | **unfair** | The "genuine denoising" rule cannot decide the $200 winner; DeepSeek `4ttc3o` read the grader (unreviewed). |
| [LLM post-training](tasks/llm-post-train.md) | pass | minor | Graded GPQA/LCB handed to agents; selection on them zeroed twice, passed once (`2ikiw0`) plus 3 probable. |
| [Vision for a ternary LM](tasks/maple-vlm.md) | pass | **unfair** | Floor raised after half the field ran; 15 of 18 at 0; the gain is reasoning, not vision. |
| [Music transcription](tasks/music-transcription.md) | pass | minor | Held-out rendered with 4 known soundfonts; 7 trials fingerprinted them, including every winner. |
| [OCR latent compression](tasks/ocr-latent-compression.md) | pass | minor | Rubric lacks the provenance check CONTRACT.md promises; Fable `12nqia` selected on public images. |
| [PII redaction](tasks/pii-redaction.md) | pass | minor | Both splits are the public RedactionBench test set; the self-check rewards a text cache the grader punishes. |
| [Pokémon Random Battle](tasks/pokemon-random-battle.md) | pass | **unfair** | Top audited score 7.4; all bots are the same open-source base; every winner within 1–2 SE. |
| [Figure to TikZ](tasks/scitikz.md) | pass | minor | No floor (scores 39.6–65.1); $50 decided by 0.0002 raw. |
| [Screenshot diffing](tasks/screen-difference.md) | pass | **unfair** | A blind fixed paragraph scores 32.0, above 14 of 18 trials. |
| [Screenshot generation](tasks/screenshot-generation.md) | pass | minor | Fable `3yw6ax` probable grading-machine render failure; Astra did not use `imagegen`. |
| [Speculative drafting](tasks/speculative-drafting.md) | pass | fair | Deterministic grading, clear margins; held-out in a readable HF folder, untouched. |
| [SVG generation](tasks/svg-generation.md) | pass | minor | 40 of 57 trials leaderboard-wide at 0; two winners inside the floor's own noise. |
| [Ternary quantization](tasks/ternary-ptq.md) | pass | minor | Rubric omits "select": 4 confirmed and 2 probable false positives; graded GPQA/LCB are the public files. |
| [Video frame interpolation](tasks/video-frame-interpolation.md) | pass | minor | Held-out is public SNU-FILM; DeepSeek `1sb7so` suspected infrastructure timeout. |
| [Zero-shot classification](tasks/zero-shot-classification.md) | unclear | minor | Upstream sources of a banned dataset are not named; strict reading changes two winners within noise. |

## Questions for Induction Labs

1. Was `inductionlabs/frontier-ml-tasks` (including `<task>/private/`) public while the trials ran? Which HF token did
   agents receive (`FML_AGENT_HF_TOKEN` or the operator's)?
2. Why were 21 DeepSeek and 17 MiniMax trials graded with `FML_REVIEW_SKIP=1`, and why do they count on the leaderboard?
3. Why were 62 of 63 Gemini 4 Argon trials, and 4 of Opus's $200 trials, re-run? Were any re-runs triggered by score?
   Can the originals be published?
4. Was the Gemini API quota (332 `RESOURCE_EXHAUSTED` errors) known, and did it affect which Argon trials were re-run?
5. Why does ternary-ptq's rubric omit "select", and why does ocr-latent-compression's omit the promised provenance check?
6. Why was maple-vlm's floor raised on 2026-10-07, after three of the audited models had run?
7. Will the Codex, Antigravity and Muse Code harness wrappers and settings be published?
8. Will future reviews hide the agent's model name from the reviewer?
9. The methodology post says the reviewer checks whether the agent searched for FrontierML solutions. Which rubric
   implements that check?
10. Why does every task's `solution/` hold the same smoke server? Was each task shown to be solvable at $10 before
    release, and why were lean-simplification (`release_ready: false`) and the video-frame-interpolation pilot included?
11. Why is maple-vlm's floor measured with 8,192 thinking tokens when graded requests ask for `max_tokens: 256`?

## Limitations of this audit

- **Six of 19 models.** Leaderboard-wide statistics (review rates, zero rates) use all 1,197 trials; per-trial
  judgements cover only the six audited models.
- **No submitted files.** Reviewers judged from trajectories (tool output truncated to 4,000 characters per step) and
  grade pages. A zeroed trial's pre-review metric is unpublished, so false negatives cannot be restored in the ranking.
- **Model review.** Per-trial classifications were made by model reviewers reading trajectories of up to 5 MB. Every
  confirmed false positive and every winner-relevant call was re-checked by the lead auditor; contested calls are in
  [data/adjudication.json](data/adjudication.json). The research/engineering boundary is a judgement call.
- **Dataset visibility history.** The HF dataset is public now; its visibility during the runs is unknown.

## Reproduce

```bash
sh scripts/fetch.sh /tmp/frontierml-raw                    # ~160 MB: site pages, 1,197 trial records, 378 trajectories
python3 -I scripts/build_workspace.py /tmp/frontierml-raw /tmp/frontierml-ws
python3 -I scripts/sensitivity.py data/all_trials.csv data/trial_reviews data/adjudication.json > data/sensitivity.md
python3 -I scripts/summarize.py data/trial_reviews data/adjudication.json > data/summary.md
```

`data/all_trials.csv` is every trial on the site (1,197 rows); `data/trials.csv` is the 378 audited ones with harness,
effort and run id. Per-trial reviews are in `data/trial_reviews/<task>.json` and per-task notes in `tasks/<task>.md`.
