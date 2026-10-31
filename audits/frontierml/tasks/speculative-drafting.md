# Speculative Drafting

Raw id: `speculative-drafting` (Efficiency; source: Google)

## The task

Train a draft model for greedy, non-thinking Qwen3-8B. A `POST /draft` endpoint returns up to 16 token ids.

- **Size cap:** the whole submission must be at most 1,000,000,000 bytes.
- **Base model:** any open-weights model that is not a specialised drafter. EAGLE, Medusa and similar heads are forbidden (`tests/task/review.py:29-45`).
- **Public data:** 40 conversations with the target's continuations. Training and selection on them are allowed.
- **Held-out set:** 200 new conversations in the same eight categories. The verifier replays greedy speculative decoding against the stored target continuations.

## How scoring works

- **Metric:** tau = continuation tokens / verification steps.
- **Rescaling:** score = (tau − 4.6) / 2.4, clamped (`tests/task/task.yaml:51-61`).
  - The floor of 4.6 is untouched Qwen3-1.7B with 4-bit linears.
  - The ceiling of 7 is an owner-set target, not a measured model.
- **Noise:** the replay is deterministic, so grading noise is negligible. 0.1 of tau is 4.2 points.

## Results

| Wallet | Model | Trial | Score | tau | Verdict |
|---|---|---|---|---|---|
| $10 | **Opus** | 58i7sa | **21.2** | 5.108 | engineering, agree |
| $10 | Astra | 1fhd62 | 16.8 | 5.002 | engineering, agree |
| $10 | Fable | 2ot571 | 15.6 | 4.974 | engineering, agree |
| $10 | Argon | 3oklat | 12.9 | 4.909 | engineering, agree |
| $10 | Muse | mugqi9 | 9.5 | 4.827 | engineering, agree |
| $10 | DeepSeek | 696vw4 | 2.4 | 4.658 | engineering, agree |
| $50 | **Opus** | 1qhhnj | **37.0** | 5.488 | engineering, agree |
| $50 | Fable | 4g3uws | 26.8 | 5.242 | engineering, agree |
| $50 | Astra | 5b038w | 16.5 | 4.995 | engineering, agree |
| $50 | Muse | 2j2fr1 | 13.1 | 4.915 | engineering, agree |
| $50 | Argon | 4a9bxl | 10.4 | 4.851 | engineering, agree |
| $50 | DeepSeek | 2k0m92 | 6.6 | 4.759 | engineering, agree |
| $200 | **Opus** | 8r9f65 | **41.8** | 5.604 | engineering, agree |
| $200 | Fable | 3avp9w | 29.5 | 5.309 | engineering, agree |
| $200 | Astra | fd7qp3 | 25.8 | 5.220 | engineering, agree |
| $200 | Argon | 1n9j8t | 16.9 | 5.006 | engineering, agree |
| $200 | Muse | 3f2w0h | 5.2 | 4.725 | engineering, agree (spent $35 of $200) |
| $200 | DeepSeek | 582llj | 0 | 4.306 | no_gain, agree (public 5.03, held-out 4.31) |

## What the models did

- **Every trial took the same route.** Start from Qwen3-1.7B, distil it on Qwen3-8B greedy continuations of prompts, then quantize to about 4 to 5 bits to fit 1 GB.
  - Prompts came from train-split public corpora or were LLM-generated.
  - The quantization is GPTQ, NF4 or QAT-packed int4.
- **Opus** won every wallet by matching the prompt distribution and compressing carefully:
  - 177k LLM-generated, category-matched synthetic prompts (1qhhnj).
  - Online KL distillation against the target's logits.
  - Sensitivity-guided mixed 4/5-bit packing. 8r9f65 [93]: "Layer 2's down_proj turns out to be the single critical tensor—keeping just it in bf16 recovers most of the 4-bit loss".
  - Each Opus trial selected checkpoints on its own held-out generated split.
- **Opus 1qhhnj also tried a larger model:** "Qwen3-4B ... squeezed to about 2 bits per weight to fit 1 GB it fell to 3.3".

## Key findings

1. **Clean task, sound reviews.**
   - All 18 reviews pass, and I agree with all 18.
   - Every data source is a train split, a public corpus, or prompts the agent generated. The test-split file names that turn up are repo listings, not downloads (e.g. Fable 2ot571 hendrycks_math).
   - No trial started from a drafter checkpoint. Argon 4a9bxl saw `AngelSlim/Qwen3-1.7B_eagle3` in a search listing [58] and did not use it.
2. **The held-out data is publicly readable, but nobody read it.** The held-out conversations are in a public HF folder (`review.py:19-21`). I searched all 18 trajectories for the tasks dataset, the benchmark repo and frontierml.org and found no access.
3. **DeepSeek 582llj has an unexplained drop.**
   - Its public tau was 5.03, but held-out tau was 4.31, below the floor.
   - Other trials move by 0.03 to 0.23 between public and held-out.
   - The grade page does not show failed or timed-out requests, so overfitting cannot be told apart from serving failures.
   - It is last at $200 either way.
4. **Elicitation.** Muse spent $35 of its $200 wallet (3f2w0h), so its $200 score (5.2) fell below its $50 score (13.1).

## Epoch scoring item: **pass**

- No false positives, false negatives or infrastructure zeros.
- Opus leads by 4.4 points at $10, 10.2 at $50 and 12.3 at $200 under a deterministic grader.

## Task design

- **The metric matches the prompt and is deterministic.** It is an exact-match greedy replay against stored Qwen3-8B continuations: tau = tokens / steps, scored as (tau − 4.6) / 2.4 (`tests/task/specdraft_walk.py:50-57`, `:177-204`). No judge is involved. The final step's phantom bonus token is not counted, so no inflation is possible.
- **The floor is the obvious untrained drafter.** Untouched Qwen3-1.7B with 4-bit linears (vLLM bitsandbytes) scored tau 4.60 on the held-out set (`tests/task/task.yaml:55-61`). Better compression of that same model is worth up to about 16 points (bf16 scores 4.99 but is over the cap), so the score mixes compression and drafting skill. The floor replaced an earlier empty-draft anchor (tau 1).
- **The ceiling is an owner-set target, not a measurement.** Tau 7 sits against a maximum of 17 (`task.yaml:59-60`). The best observed is tau 5.76 (Sonnet $200, 48.4), so the ceiling is not binding.
- **Sampling noise is the main limit.** 200 conversations (25 per category) give a standard error of about 0.10 tau, which is 4.2 points. The author notes that 80 generated prompts were left unused (`tests/task/specdraft_data.py:60`). Gaps under about 8 points, such as Opus 21.2 vs Sonnet 20.8 at $10, are within about two standard errors. Opus's leads at $50 and $200 among the audited six are 10 to 12 points.
- **The held-out set is in-distribution.** Public and held-out prompts come from the same generator (gpt-5.4-mini, `specdraft_data.py:24`) and the same eight categories (`CONTRACT.md:11`), despite the blog's "out-of-distribution" wording. Shifts are 0.03 to 0.23 tau, except DeepSeek 582llj (5.03 → 4.31), which the grade page cannot explain because it does not show held-out request failures.
- **Two gates zero the run.** More than 5% failed requests, or over 10,800 s of serving, scores 0 (`CONTRACT.md:34-35`). The self-check projects serving time "within about 10%" (`tests/task/verifier.py:120-121`) and applies the same size gate. It reports no tau and does not run the review. No trial hit either gate.
- **The spec and the review agree, apart from small wording differences.** The review allows untrained n-gram drafters although the prompt says "train" (`review.py:3-5`). It explicitly fails "serving the target model itself" and "any network access" (`:52-53`), which the 1 GB cap and offline serving already imply. The site title says "speeds up" decoding, but only acceptance length is scored.
- **Feasible at every wallet.** Mean and max by wallet: 6.0/21.2, 11.2/37.0, 14.1/48.4. More money buys more target continuations and longer distillation.
- **Neutral.** The Qwen target and the Qwen base family are inherent to the task. The hidden OpenAI prompt generator did not matter: Opus won with Qwen, gpt-oss, Gemini and DeepSeek generators. The specialist-drafter ban lists named checkpoints (`review.py:29-45`). `solution/` is the shared smoke fixture and would score 0.
- **Fairness verdict: fair.** The grader is deterministic and the rules match the prompt. Treat gaps under about 8 points as ties.
