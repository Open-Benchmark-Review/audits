# Figure to TikZ (scitikz)

## The task

- **Goal:** serve a vision-language model that turns an image of a scientific figure into a complete TikZ/LaTeX document, through an OpenAI-style chat endpoint.
- **Data given:** 50 example figures with reference code from SciTikZ-230K. These may be used for training and selection (SCHEMA.md; `tests/task/review.py:29-35`).
- **Rules:**
  - Training on the rest of SciTikZ-230K is allowed. SciTikZ-Bench is forbidden.
  - Starting from a specialist TikZ checkpoint is forbidden.
  - No embedded raster, tracing, OCR or answer lookup.
- **Limits:** ready within 300 s; 611 figures within 2 h at concurrency 16.

## How scoring works

- **Score:** compilation rate × geometric mean of SigLIP, CLIP, exp(−LPIPS/0.5), SSIM, 1−DreamSim, exp(−TED/0.4) and CrystalBLEU. The result is ×100, with no floor or rescaling.
- **Held-out set:** 611 SciTikZ-Bench figures.
- **Score range:** zero-shot Qwen3-VL already scores about 0.2–0.4 on the dev set ([64] in Opus 1rlvur: 0.407), so all 18 trials land between 39.6 and 65.1.
- **Contamination check:** overlap between SciTikZ-230K and the benchmark was checked only for the 50 dev rows, and only for exact matches (`scitikz_data.py:95-96`: "Exact overlap only, not semantic/template deduplication").

## Results

| Model | $10 | $50 | $200 |
|---|---|---|---|
| Claude Opus 5.5 | **56.4** | 57.01 | **65.1** |
| GPT-6 Astra | 52.9 | **57.03** | 59.1 |
| Claude Fable 5.1 | 54.5 | 54.0 | 56.5 |
| Gemini 4 Argon | 51.4 | 53.9 | 52.9 |
| Muse Wonder | 41.4 | 44.4 | 43.0 |
| DeepSeek V4.1 Flash | 40.7 | 39.6 | 51.1 |

- All 18 reviews passed. I agree with every one.
- No trial scored zero.
- No trial touched SciTikZ-Bench, the frontier-ml repo, the HF tasks dataset or frontierml.org.

## What each model did

Every trial fine-tuned a general Qwen VLM on SciTikZ-230K. The differences:

- **Base:** Qwen3-VL-8B in most runs. Opus used Qwen3-VL-4B at $10 and Qwen3.5-9B at $200. Muse $200 used Qwen3-VL-4B; DeepSeek and Muse $50 used Qwen2.5-VL 3B/7B.
- **Amount of data:** from 6.6k rows (Gemini 5zheb6) to the full 230k (Opus 3mquyr, Astra 3dkpma, DeepSeek 48h210).
- **Serve-time tricks:**
  - Compile-in-the-loop servers with bundled TeX Live or Tectonic: Fable, Astra and DeepSeek 55e3nh.
  - Best-of-N with n-gram MBR (Opus 15ip8u, 1rlvur).
  - Render-and-compare reranking: SigLIP in Fable 4pf2v7, SSIM/L1 in Fable 4mfvjr.
- **Muse** shipped plain vLLM servers with no compile check. Its compile rates of 77–83% explain most of its gap to the others.

## Key findings

1. **No scoring defects.**
   - Data provenance was clean in every trial.
   - The reviewer's approach summaries match the trajectories.
2. **The $50 winner is a statistical tie.**
   - Astra 3sl4he scored 0.57026 raw and Opus 1rlvur 0.57009.
   - Opus 3mquyr measured one checkpoint four times on the 50 dev figures, greedy, and got 0.629, 0.656, 0.655 and 0.617 ([226]).
   - Only the $200 Opus win (65.1 vs 59.1) is clearly real.
3. **The biggest gain came from the base model and data, not a new idea.**
   - Opus 3mquyr did full-parameter SFT of Qwen3.5-9B on all 230k rows on 8×H100, plus a weight soup ([188] "1 epoch over 230K samples in 102 min").
   - It used greedy decoding with no reranking, and its compile rate was only 94%.
4. **Grader-aware selection is permitted.**
   - The review rule allows "Model-driven rendering, refinement and selection" (`tests/task/review.py:41-42`), but the prompt does not mention it.
   - Fable 4pf2v7 reranks candidates with SigLIP SO400M, one of the seven scoring metrics. It reached a 99.8% compile rate, but its score is only mid-pack.
5. **Possible template overlap is unmeasured.**
   - SciTikZ-230K and SciTikZ-Bench come from the same pipeline.
   - Near-duplicate templates would favour training on more of the corpus.
   - This cannot be checked from public data.

## Epoch scoring item: **pass**

No false positive, false negative or infrastructure zero. The $50 result is within noise, but no scoring defect changes a winner.

## Task design

- **No floor.** `task.yaml` has no `score_normalization`, so the reward is the raw metric. Base Qwen3-VL-8B already scored 0.407 on the dev figures (Opus 1rlvur [2190]), and the review requires task-time training (`tests/task/review.py:9-10`). About 40 of the 100 points therefore carry no signal, and all 56 non-zero trials sit between 7.8 and 65.1.
- **Compile rate dominates.** The score is linear in compile rate, but the visual components are averaged only over figures that compiled (`scitikz_metric.py:35, 47`). Any compiling fallback raises the score. With dev-like component means, turning the last 15% of failures into one-line stubs moves 0.433 to 0.480. Compile-in-the-loop servers are the legitimate form of this.
- **Code-text components.** TED and CrystalBLEU (`scitikz_metric.py:84-94`) compare against the reference TikZ text. They reward imitating SciTikZ-230K style and keep any score well below 1 (dev components around 0.29 and 0.22).
- **Wheel rule not enforced.** The contract allows only "unmodified PyPI or PyTorch wheels" for compiled dependencies (`CONTRACT.md:17`). The shared reviewer treats other native files as "not a blocker" (`frontier_ml/review.py:230-231`). Fable shipped a portable TeX Live and passed; Astra hunted down a wheel-packaged Tectonic to comply.
- **Corpus overlap unmeasured.** The SciTikZ-230K vs SciTikZ-Bench overlap was screened only for the 50 sampled dev rows (`scitikz_data.py:48`, `:96` "Exact overlap only"). The rest of the 230K that agents may train on was never counted against the benchmark.
- **Self-check is weaker than grading.** It never compiles or scores ("Nothing was compiled", `verifier.py:217-218`), and it times dev figures although "held-out figures differ and may need longer answers" (`verifier.py:206-207`). The 7,200 s deadline is all-or-nothing (`CONTRACT.md:11`).
- **Scorer is reproducible.** Metric models are pinned by revision and hash (`scitikz_models.py:243-247, 306-313`). LPIPS runs under fp16 autocast and DreamSim in bf16, so only last-digit drift is expected.
- **Noise.** About 1 point SE, from 611 figures plus run-to-run decode variance (Opus 3mquyr dev replicates 0.617-0.656 on 50 figures). This is enough to make the $50 tie (0.57026 vs 0.57009) meaningless.
- **Feasible at $10, weak scaling.** Opus scored 56.4 at $10. Only Opus $200 (full SFT of a 9B model on all 230K rows) clearly buys more.
- **Reference solution.** `solution/` is the empty smoke fixture and would score 0.
- **Fairness verdict: minor issues.** The metric matches the prompt and is deterministic. The missing floor, the compile-rate lever and the unenforced dependency rule are design weaknesses, not winner-changing defects.
