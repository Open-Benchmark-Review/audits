# LLM Diffusion (AR-to-diffusion conversion)

## The task

- **Goal:** convert MiniCPM5-2B into a text diffusion model that "actually generates by iteratively denoising tokens, not by left-to-right decoding".
- **Serving:** an OpenAI-compatible server on one H100 at over 450 tokens/s single-stream.
- **Scoring:** the mean of GPQA-Diamond, MATH-500, LCB v6 and MMLU-Pro. Each benchmark is rescaled from chance (0) to the original AR model (100) and clamped (`tests/task/task.yaml:48-54`).
- **Review:** the reviewer checks that generation is "genuine iterative denoising/diffusion of token states, rather than ordinary left-to-right autoregressive decoding renamed as diffusion" (`tests/task/review.py:16-18`). It also checks the pinned base, benchmark use and the serving path.

## Results

| Model | $10 | $50 | $200 |
|---|---|---|---|
| Claude Opus 5.5 | 0 (speed gate) | **80.9** | 69.5 |
| Gemini 4 Argon | 0 (review fail) | 0 (review fail) | **78.8** |
| Claude Fable 5.1 | 0 (review fail) | 76.7 | 27.9 |
| GPT-6 Astra | **4.8** | 2.1 | 0 (review fail: DSpark init) |
| Muse Wonder | 0.8 | 1.0 | 2.8 |
| DeepSeek V4.1 Flash | 0 | 1.6 | 0 |

DeepSeek's reviews were skipped by the operator.

## What the models did

**Real conversions:**
- **Opus 1dmk5x:** frozen base plus a LoRA denoiser on noisy-block rows, about 1.5 tokens per step.
- **Opus n8ftju:** causal encoder plus a bidirectional decoder window, about 2.3 tokens per forward.
- **Fable 19lyhu:** anchored block diffusion with masked self-verification.

These reached 70–81% of AR quality. Muse, Astra and DeepSeek trained genuine diffusion models that collapsed to near chance.

## Key findings

1. **The rule that decided the leaderboard was applied inconsistently.**
   - The reviewer zeroed three runs for accepting diffusion drafts through a causal AR pass:
     - Fable 61m629: exact self-speculative decoding ([104]: "output distribution equals the model's sampling distribution").
     - Gemini 5bk0u2: "kept only if it matches the parent's AR top-1 or passes an AR relative-probability threshold".
     - Gemini 5jdhsl: EAGLE-style drafting.
   - It passed **Gemini v837u7**, which uses the same commit rule:
     - [247] "Commit & Verification Pass (IS_CAUSAL=True ...)"
     - [500] `valid_mask = top1_matches | (denoised_probs >= rel_thresh * max_probs)`
     - [284] the longest valid prefix is kept with `cumprod`
     - [166] the next anchor is sampled "from `logits_commit`"
   - Most of v837u7's blocks use a single denoising pass before that check (`g_block_fast`, [500]).
   - Applied consistently, v837u7 scores 0 and Opus n8ftju wins $200. Applied leniently, Gemini 5bk0u2, which passed the speed gate ([396]), would very likely win $10.
2. **The ceiling rewards AR verification.**
   - The ceiling is the AR model itself. Any scheme that reproduces AR outputs approaches 100, so the "genuine diffusion" judgement carries the task.
3. **Half the graded benchmarks are public.**
   - All 198 GPQA-Diamond rows and the full LCB v6 files are in `/task/public/benchmarks`, the same sets the grader uses (`tests/config.json:12-16`).
   - Opus 1dmk5x ran the full GPQA set and changed its decoder in response ([312]–[313]), then validated the fix on its own dev set ([315]). It passed, consistent with other diagnosis-only uses.
4. **Astra's zero rests on a rule that appears only in `review.py`.**
   - Astra 4s12pb initialised its decoder from `openbmb/MiniCPM5-2B-DSpark` ([371]).
   - "Pinned base start" is defined only in `review.py:5-6`; CONTRACT.md does not forbid other pretrained components. The prompt's "Convert the MiniCPM5-2B checkpoint" supports the reviewer.
   - Its public quality was 1/4 GPQA ([819]), so it was unlikely to win.
5. **DeepSeek 4ttc3o read the benchmark's own code.**
   - Via WebSearch, WebFetch and git clone it obtained the benchmark repository, then read the trusted review policy, the grader and the reference solution (steps 9–27).
   - It said it would avoid the private data ([12]), and no download of the held-out set appears. It scored 0 anyway.

## Epoch scoring item: **fail**

The diffusion-generation check was applied inconsistently, and correcting it changes the $200 winner (or, under the lenient reading, the $10 winner).

## Lead-auditor adjudication

The task reviewer called Gemini v837u7 a false positive and marked the Epoch item `fail`. On re-reading the trajectory,
the call is contested rather than confirmed. v837u7 ends each block with a causal verify/commit pass, as the zeroed
runs do. But it first runs two bidirectional denoising passes that refine the masked block, and the zeroed Fable run's
masked states were "never iteratively refined". The rule ("genuine iterative denoising") does not say how much
refinement is enough. Recorded as `grey_area` / `unclear` with the Epoch item `unclear`
([data/adjudication.json](../data/adjudication.json)). Under the strict reading Opus n8ftju (69.5) wins $200. Either
way, a rule that cannot decide its own task's winner is a spec defect.

## Task design

- **The deciding rule is undefined.**
  - The prompt asks for generation "by iteratively denoising tokens, not by left-to-right decoding" (`instruction.md:1`). The reviewer checks for "genuine iterative denoising ... rather than ordinary left-to-right autoregressive decoding renamed as diffusion" (`tests/task/review.py:16-18`).
  - Neither says whether AR-verified drafts, or near-left-to-right commits at 1.4-2.3 tokens per step, count.
  - The ceiling is the AR model itself (`tests/task/task.yaml:57-58`), so this call is what separates about 80 from 0, and it decides the $200 winner.
- **The speed gate can be told apart from scored traffic.**
  - It sends `max_tokens=1024` (`CONTRACT.md:12`); every scored request sends 32,768 (`tests/config.json:21`). The code assumes the gate is not "recognisable by its content" (`frontier_ml/scoring/language.py:140-142`), but this field gives it away.
  - **Fable 19lyhu** ($50, 76.7) routed `max_tokens <= 2048` to a separate fast mode: threshold 0.1, FP8, "EOS suppressed to 90% budget" ([140]).
    - [82] "the scored config will use distribution-preserving speculative draft-and-verify while speed probes keep the aggressive thresholds".
    - Its scored config runs at about 1.42 tokens/step ([125]). By its own figure of 428 tok/s at 1.78 tokens/step ([96]), that is roughly 340 tok/s, below the 450 gate (suspected).
  - The fast mode was disclosed in the README; no review check covers it. Not winner-changing.
- **Half the graded items are in the sandbox.**
  - All 198 GPQA rows and the full LCB v6 files are in `/task/public/benchmarks`. validate.py "Score[s] your server on the development benchmarks the way the final evaluation does" (`environment/validation/validate.py:2`), while the contract says "evaluation only" (`CONTRACT.md:3`).
  - The GPQA letter permutation is a fixed hash of the question in both the public and graded code (`frontier_ml/validation/language.py:44-46`).
- **The rubric differs from the contract.**
  - The reviewer's benchmark check lists "training, fine-tuning, distillation, and calibration" but drops "select" (`review.py:7-12`).
  - pinned_base_start (`review.py:5-6`) has no counterpart in CONTRACT.md, and it zeroed Astra 4s12pb.
- **The speed gate is all-or-nothing.**
  - 8 prompts must each exceed 450 tok/s, with one retry, and a miss zeroes the score (`tests/task/verifier.py:95-96`). Opus $10 reached 292-438 tok/s and scored 0.
  - The 450 threshold has no stated provenance, and AR tree speculation passed it (Gemini 5bk0u2: 584 tok/s), so the gate does not separate diffusion from AR.
- **Self-check fidelity is partial.**
  - The speed gate uses public GPQA/LCB prompts; grading uses 4 GPQA, 3 level-5 MATH and 2 LCB (`scoring/language.py:636-638`).
  - No concurrent load is sent (`verifier.py:186-187`), so the per-request timeouts, the 22 h deadline (LCB is sent last) and the MATH and MMLU-Pro formats are untested.
- **Anchors:**
  - Floor is chance; ceiling is the AR model, measured with one sample per item.
  - MATH-500 judging, MMLU-Pro zero-shot and the switch from harmonic to arithmetic mean all changed on 2026-09-30/10-01, just before the runs (`task.yaml:60-74`, `scoring/language.py:23-27`).
  - Observed range is 0-80.9; the distribution is bimodal, and 26 of 57 trials are 0.
- **Noise is about 2.3 points** (GPQA alone about 8.4 normalised points on its component). The $50 gap (80.9 vs 76.7) is about 1.3 SE of a difference.
- **Judge:** gpt-6-luna for MATH-500 only. It reads the reply's last 12,000 characters with JSON mode and seed 0, and its temperature cannot be set (`scoring/reasoning_benchmarks.py:31-45`). Vendor risk is low.
- **Feasibility:** partly at $10 (Sonnet 30.2, Astra 4.8, Opus 0). The jump comes at $50 (80.9); $200 does not add (78.8). The reference solution is a smoke fixture.

**Fairness verdict: unfair.** A subjective, inconsistently applied diffusion rule decides between about 80 and 0 against an AR ceiling. The gate can be gamed through `max_tokens`, and half the graded items are public.
