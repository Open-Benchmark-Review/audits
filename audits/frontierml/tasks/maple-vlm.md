# Vision for a Ternary LM (maple-vlm)

Task: `maple-vlm` (DeepGrove; vision)

## The task

Agents add a vision encoder and a connector to Maple, a 20B-total / 1B-active ternary MoE language model.

- **Rules:** keep the language network ternary, and add no second LM and no image-to-text front end.
- **Serving:** an OpenAI-compatible endpoint answering college-level image questions.
- **Data:** MMMU is banned except for the 129 public examples, which may be used "however you want". Agents are told to "Reply with only the option letter".

## How scoring works

- **Held-out set:** 900 questions drawn from the MMMU dev and validation rows (`review.py`). Every answer is judged by gpt-6-luna.
- **Floor:** 0 = **0.4378**, text-only Maple with its own reasoning (`tests/task/task.yaml:42-58`). That baseline thinks for up to 8,192 sampled tokens and then answers multiple choice with one token restricted by a grammar to the option letters. With Maple's free reply instead, the same pipeline gives 0.329.
- **The floor was raised on 2026-10-07.** It had been 0.3489, thinking off (`task.yaml:53-55`). Opus, Fable and Astra had already run (10-03/05), and every published score uses the new floor.
- **Disclosure:** agents were never told the floor.

## Results (published score / raw accuracy)

| Wallet | Opus 5.5 | Astra | Fable | DeepSeek | Argon | Muse |
|---|---|---|---|---|---|---|
| $10 | **0.4** / 0.440 | 0 / 0.402 | 0 / 0.360 | 0 / 0.329 | 0 / 0.342 | 0 / 0.297 |
| $50 | **6.5** / 0.474 | 0 / 0.413 | 0 / 0.316 | 0 / 0.379 | 0 / 0.324 | 0 / 0.318 |
| $200 | **2.4** / 0.451 | 0 / 0.389 | 0 / 0.350 | 0 / 0.340 | 0 / 0.353 | 0 / 0.343 |

- 15 of 18 trials are 0. All reviews passed or were skipped: DeepSeek was skipped by the operator, and I checked those three trials myself and found no violation.

## Are Opus's nonzero scores real?

**Mostly not.** On 900 questions the binomial standard error is 0.0165 accuracy, about 2.9 points on the published scale. The floor is itself one sampled run, and it moves from 0.422 to 0.439 with the choice of thinking budget and system prompt.

| Opus trial | Questions above the floor | z (floor fixed) | z (two samples) | Verdict |
|---|---|---|---|---|
| 3gpel2 (0.4) | +2 of 900 | 0.1 | 0.1 | noise |
| ev754s (2.4) | +12 | 0.8 | 0.6 | noise |
| 11dhgk (6.5) | +33 | 2.2 | 1.6 | marginal |

On raw accuracy, Opus still leads Astra at every wallet:

| Wallet | Opus | Astra | z |
|---|---|---|---|
| $10 | 0.440 | 0.402 | ≈ 1.6 (could flip) |
| $50 | 0.474 | 0.413 | ≈ 2.6 |
| $200 | 0.451 | 0.389 | ≈ 2.7 |

Under the old floor (0.3489) the scores would be:

- Opus 14.0 / 19.3 / 15.7
- Astra 8.2 / 9.9 / 6.1
- DeepSeek 0 / 4.6 / 0, Fable 1.7 / 0 / 0.2, Argon 0 / 0 / 0.7, Muse 0

The winners would not change, but 10 of 18 trials would be nonzero instead of 3.

## What the models did

- **Opus (all three trials):**
  - A Qwen3-VL / Qwen3.5 vision tower with a connector initialised by a least-squares or ridge map to Qwen's embedding space, trained on LLaVA-OneVision train shards into frozen packed-ternary Maple.
  - What lifts Opus above the floor is how it serves the model: thinking with a budget plus voting. 3gpel2 votes over thinking-prefix variants ([195], [211]). 11dhgk uses a describe-then-reason prefix with 3-sample self-consistency ([160], [163]). ev754s self-distils thinking traces so the connector stops suppressing reasoning ([263]).
- **Others:** Qwen2.5-VL / Qwen3-VL / SigLIP2 towers with MLP connectors, some with ternary-STE QAT on attention (Argon, Astra). Most answered directly or with short thinking, which caps them near the thinking-off anchor (about 0.35).

## Key findings

1. **The task barely measures vision.**
   - Opus 11dhgk's own ablation: "The text-only ablation scores 43.3% on MC, nearly matching the image-included results" ([141]).
   - DeepSeek 1af6us found that images made its model worse: "40% with no images vs 35% with them" ([307]).
   - The only above-floor gains come from inference-time reasoning and voting.
2. **The floor is high, undisclosed and was changed after the runs.**
   - It uses an 8,192-token thinking budget and a letter grammar that no agent was told about.
   - Agents who read "Reply with only the option letter" literally and turned thinking off (Fable 5c4mu5 [49]) were capped below 0.
3. **No rule violations were found.**
   - No MMMU or MMMU-Pro downloads, and no access to `inductionlabs/frontier-ml-tasks`, the repo or frontierml.org.
   - Training on the public examples (Astra 1e2lgl, Muse 2nzodg and 2204mx) is explicitly allowed.

## Epoch scoring item: **pass** (with a measurement caveat)

- No false positive, false negative or infrastructure zero changes a winner. Opus leads on raw accuracy at every wallet.
- The caveat: the published nonzero scores are mostly noise around a floor that was moved after the runs, so the task separates models only on raw accuracy, which is not what it publishes.

## Task design

- **The floor recipe contradicts the graded request.** The client sends `max_tokens: 256, temperature: 0` and "Return only the correct option letter" (`environment/validation/validate.py:34,41-42`; CONTRACT.md:7). The floor samples 8,192 thinking tokens at temperature 0.6, then forces a letter with a grammar (`tests/task/task.yaml:48-50`). Agents who honoured the request (Astra 2xzouq clipped at `min(max_tokens, 256)`; Fable 5c4mu5 thinking off) were capped near 0.35, below the floor.
- **The floor was moved after the runs and never disclosed.** It went from 0.3489 to 0.4378 on 2026-10-07 (`task.yaml:51,55-57`). Its tools live in `work/maple-floor/thinking-20261007/` (`task.yaml:57-58`), which is not in the repo. The shipped `pipeline/text_only_floor.py:8-9` still builds the old thinking-off anchor. The floor was measured with llama.cpp Q8_0 "on H100s" (`task.yaml:45-47`), not through the graded 1 h / 16-concurrency pass.
- **Noise is larger than the signal.** n = 900, p ~ 0.44 gives SE 0.0165 = 2.9 points on the 0.562-wide scale. The floor is one sampled run with similar noise, so a difference from the floor carries about 4 points of SE. The published nonzero scores are 0.4 / 2.4 / 6.5.
- **Usable range is almost nil.** Across all 19 models, 54 of 57 trials score 0, and only Opus is nonzero. The ceiling (all 900 correct, `task.yaml:59`) is far out of reach for a 1B-active ternary LM, so even 0.55 raw would be only ~20 points.
- **It barely tests vision.** The floor is text-only, and agents' ablations show images add little or hurt (Opus 11dhgk [141]; DeepSeek 1af6us [307]). The gains over the floor come from inference-time reasoning and voting.
- **The judge is reasonable but not strictly deterministic.** gpt-6-luna decides every question (`tests/task/answers.py:1-13,39-47`) at its default temperature with seed 0 (`answers.py:24-29`). Its rules accept a reasoned reply that ends in one answer (rule 1), which is looser than the interface's "only the option letter". Judge faults raise an error rather than marking the answer wrong.
- **Self-check cannot warn about the floor.** It checks reply shape and projects the deadline from 150 of 900 public questions, with "no review, no judge and no score" (`tests/task/verifier.py:3-4`). A submission can pass every check and publish 0.
- **The spec is otherwise consistent.** The MMMU ban, the public-example exception and the held-out source agree across CONTRACT.md:3, `task.yaml:11-14` and `review.py:17-32`. The held-out set is essentially MMMU dev+validation. `solution/` is the smoke fixture ("No description available.", 0).
- **Verdict: unfair.** The published 0-100 score is dominated by an undisclosed, post-hoc floor whose recipe contradicts the request, and it sits within noise of that floor. Only raw accuracy separates models.
