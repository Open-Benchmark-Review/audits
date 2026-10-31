# Screenshot generation (screenshot-generation)

## The task

The agent serves a generator that takes a screen description and text lines with boxes, and returns a realistic 1280×720 PNG. Every text line must be rendered exactly inside its box.

**Limits:**
- Open-weights models only, and no specialised screenshot generator.
- p95 latency of 30 s or less.

## How scoring works

- **Per image** (`tests/task/screenshot_generation.py:5-6, 324-335`):
  - score = (geomean(T, L, F) + R) / 2
  - T = OCR text accuracy and L = OCR layout. F (faithfulness) and R (realism) are rated by gpt-6-luna.
  - Each run scores 200 of 500 held-out pages.
- **Rescaling** (`tests/task/task.yaml:46-52`):
  - 0 = 0.537: the white page with the text drawn in its boxes. It already gets T 0.987 and L 0.961.
  - 100 = 0.954: the real screenshots.
  - Scores are clamped, so the published score mostly measures the judge's F and R ratings.
- **Failure rule:** more than 5% failed requests scores 0.

## Results

| Model | $10 | $50 | $200 |
|---|---|---|---|
| Claude Opus 5.5 | **74.2** | **63.0** | **78.9** |
| GPT-6 Astra | 47.3 | 59.3 | 50.6 |
| Claude Fable 5.1 | 44.6 | 0 (3yw6ax) | 35.0 |
| DeepSeek V4.1 Flash | 31.7 | 38.6 | 37.6 |
| Muse Wonder | 32.5 | 22.4 | 18.6 |
| Gemini 4 Argon | 15.9 | 18.9 | 0 (5xgpaj) |

- All reviews passed, except DeepSeek's three, which were skipped by the operator. I checked those three myself: procedural renderers, clean.

## What each model did

- **Opus:** general diffusion models with exact text compositing.
  - Z-Image-Turbo plus a union ControlNet on a procedural scaffold (5q5wft).
  - FLUX.2-klein-9B editing a PIL mock-up (3wkr2c, q6eopv; q6eopv adds Qwen3.5-9B best-of-N selection).
  - OCR is used to erase stray generated text.
- **Astra and Fable:** an LLM writes a drawing program or HTML, which is rendered. Astra adds SDXL-Turbo or Z-Image photo regions, or bundled Unsplash photos.
- **Muse:** Z-Image img2img over a PIL canvas, or a pure Pillow renderer.
- **Argon:** small LoRA scene planners with SVG renderers.
- **DeepSeek:** pure procedural renderers, tuned sample by sample against gpt-6-luna.

## Key findings

1. **GPT-6 Astra did not use its harness's `imagegen` skill or any image generation outside the wallet.**
   - In all three trials, `imagegen` appears only in the system preamble. No trial read its SKILL.md or called an image tool.
   - Tool calls were `exec_command`, `apply_patch`, `view_image` (to inspect its own renders), `web__run` (HF/vLLM doc searches) and `clock`. No sub-agents were spawned.
   - Its OpenRouter calls were text models only: qwen3-coder, qwen3.5/3.6, and gpt-6-luna as judge and case writer.
   - Image models were open weights run on Spin GPUs: SDXL-Turbo, Z-Image-Turbo, and FLUX.2-klein experiments.
   - 5dab48 ships real Unsplash stock photos. These are not generated.
2. **Fable 3yw6ax's zero is unexplained.**
   - The final selfcheck passed on the frozen submission ([252]).
   - Its own scoring on the 25 public examples gave 0.756 (T 0.987) at [245].
   - Grading gave a raw 0.2143 with 0 invalid images, which is below the 0.537 floor. By the formula, that means near-zero text quality on most images: the Chromium renderer likely drew little readable text on the grading machine.
   - Selfcheck runs no OCR, so the agent could not have caught this.
   - Marked infra suspected, grader agreement unclear. Its sibling runs scored 35–45, so it would not have beaten Opus's 63.0 at $50.
3. **Argon 5xgpaj's zero is the agent's own bug.**
   - "11 of 200 requests failed ... ValueError: y1 must be greater than or equal to y0"
4. **DeepSeek 339oqw lost its judge during development.**
   - The Spin OpenRouter proxy returned 409 for more than 5.5 h ([2640], [2670]), so the agent had no realism feedback late in the run.
   - Probably little effect on the score.
5. **No leakage risk from the agents' own dev sets.**
   - The held-out pages come from internal screen recordings and crawls (`tests/task/pipeline/internal/source.json`).
   - So the dev sets agents built from OS-Atlas (Opus q6eopv) and wave-ui-25k (Opus 3wkr2c) train splits cannot overlap them.
   - No trial touched the benchmark repo, the HF tasks dataset or frontierml.org.

## Epoch scoring item: **pass**

- Opus wins every wallet. The closest margin is 3.7 points over Astra at $50.
- Neither zero can change a winner.

## Task design

- **Anchors are sensible:**
  - 0 is the organiser compositor, text pasted on a white page: 0.537 raw, with T 0.987 and L 0.961.
  - 100 is the real screenshots at 0.954 raw (`tests/task/task.yaml:46-52`; `pipeline/baselines/methods.py:76-88`).
  - Because exact text compositing saturates T and L, the usable scale is almost entirely gpt-6-luna's F and R ratings. Observed scores run 0-78.9, so the ceiling does not bind.
- **The judge is stochastic:**
  - Each image gets one call per axis, answered with a single digit 0-9.
  - Only the default temperature is accepted, and `seed: 0` gives best-effort determinism only (`environment/validation/screenshot_generation.py:66-68, 80`).
  - Each anchor was measured once (`task.yaml:52`).
  - 200 shared pages (`tests/task/verifier.py:52-77`) give an SE of about 2 points. The $50 Opus–Astra gap (3.7) is within about 2 SE.
- **Dev judge matches grading:**
  - The rubric prompts and the request are shipped in the validator.
  - The request deliberately leaves out fields the Spin proxy rejects (`screenshot_generation.py:68-72`).
  - Tuning against the judge is therefore legitimate and equally available to everyone.
- **Self-check cannot see content:**
  - It runs no OCR or judge (`tests/task/verifier.py:22-23`). It checks only 20 public requests for latency, failures and PNG validity.
  - A renderer that draws no text on the grading host passes self-check and is clamped to 0.
  - This is the likely story of Fable 3yw6ax: graded raw 0.214 with 0 invalid images, against 0.756 on the public set. Its sibling 3uz0o0 found Chromium crashing in the grading sandbox.
- **Failure-limit cliff:** with 10 of 200 failed requests, only those images score 0; with 11, the whole run is 0 (`CONTRACT.md:11`). This is disclosed, and it decided Argon 5xgpaj.
- **Metric changed before the anchors were fixed:** it moved from a harmonic to an arithmetic mean on 2026-10-01 (`screenshot_generation.py:5-6`), and the anchors were re-measured on 2026-10-07. Published runs are consistent.
- **Test set:**
  - Public (25) and held-out (500) are a seeded random, video-disjoint split of one internal pool (`tests/task/pipeline/internal/source.json:7`). There is no distribution shift, despite the blog.
  - Descriptions were drafted by Qwen3.6-27B (`source.json:6`).
  - PII is not filtered and human review is pending (`source.json:5, 8`). `pipeline/README.md:29` says this data is "local only, never upload", yet it is in the public tasks dataset (`source.json:9`).
- **Possible harness advantage (suspected, not exercised):** an image-generation tool built into a harness (Codex `imagegen`) would sit outside the wallet, and the rules do not mention it.
- **Budget:** $10 is enough (Opus 74.2 for $8.55). Money does not help on average: the 19-model means are 29.7 / 26.2 / 32.4.
- **Reference solution:** `solution/` returns a blank PNG (`solution/server.py:100-101`), which scores 0.
- **Fairness verdict: minor issues.** The spec is clear, the anchors are sound, and the 200 held-out pages are shared by all runs. But the score is a noisy single-digit judge rating, and self-check cannot catch a renderer that fails on the grading host.
