# OCR Latent Compression

Task: `ocr-latent-compression` (Induction Labs; vision / efficiency)

## The task

Agents train a discrete visual tokenizer. `POST /encode` turns a page image (1275x1650 document or 1920x1080 screenshot) into integer codes of at most 16,384 bits (2 KB). `POST /decode` gets only those codes and must return the page text.

- **Encoder:** must be neural. It may use FSQ, VQ or similar quantizers, and it must not transcribe the page.
- **Decoder:** must be neural and use only the codes.
- **Speed:** at least 1 image/s on each endpoint.
- **Starting point:** DeepSeek-OCR weights are supplied. Every scored trial built on them.
- **Rule:** "Do not train, fine-tune, calibrate or select on the validation or test split of any public dataset or benchmark".

## How scoring works

- **Metric:** mean word-level edit similarity on 400 held-out pages.
- **Scale:** 0 is empty text. 100 is unmodified DeepSeek-OCR reading the full image (0.8931), clamped (`tests/task/task.yaml:49-56`).
- **Public images:** the 100 public images are about as hard as the held-out ones (0.8978 with the same pipeline). Agents' local scores match their graded raw metric to within about 0.01-0.03.
- **Review** (`tests/task/review.py:3-38`): three architecture checks plus the global harness-credentials check. **There is no training-data provenance check.**

## Results

| Wallet | Opus 5.5 | Fable 5.1 | Astra | Argon | Muse | DeepSeek |
|---|---|---|---|---|---|---|
| $10 | 26.9 (7sh96e) | **56.1** (3p5edt) | 36.4 | 50.6 | 15.3 | 4.4 |
| $50 | 54.4 (lbs8ib) | **67.9** (1fvw9l) | 57.5 | 43.2 | 3.3 | 2.2 |
| $200 | **82.6** (2pu2n0) | 67.8 (12nqia) | 64.1 | 36.0 | 1.9 | 15.2 |

- All 18 reviews passed. No trial was zeroed.
- No trial touched `inductionlabs/frontier-ml-tasks`, the benchmark repo or frontierml.org.

## What the models did

- **Opus 2pu2n0 (task winner):**
  - DeepEncoder at non-square grids and an 8-level FSQ.
  - Adaptive nested-dimension bit allocation ([98]-[99]): a blank-cell bitmap, with the remaining bits spread over inked tokens, so dense pages get about twice the bits per inked token.
  - About 560k self-rendered pages, then an 8-checkpoint average selected on its own dev split.
  - It kept the task's validation set "untouched for evaluation only" ([60]).
- **Opus 7sh96e ($10):**
  - On an A100, end-to-end FSQ, TiTok and Q-Former bottlenecks all failed ([176]-[244]).
  - It then shipped a PCA + Lloyd-Max transform coder over the inked cells, and found that coverage matters more than per-cell fidelity ([262]-[269]).
- **Fable:** FSQ or binary-FSQ bottlenecks on DeepEncoder features with a fine-tuned DeepSeek decoder. It was the strongest at $10 and $50.
- **Astra:** learned product-VQ / FSQ transformer codecs with vLLM decoders, each exactly 2,048 bytes. It froze its weights before running public validation.
- **Argon:** fitted KLT/PCA, Lloyd-Max and VQ codebooks over SAM features. This worked better at $10 than its learned encoders did at $50 and $200.
- **Muse and DeepSeek:** mostly bottlenecks that were too thin, or from-scratch decoders that never learned to read. Five of their six runs scored 4.4 or below; DeepSeek 3vvlac reached 15.2.

## Key findings

1. **The data rule is not checked for this task.**
   - CONTRACT.md promises a training-data provenance check, but `review.py` has none.
   - Unlike maple-vlm and music-transcription, `task.yaml` does not declare the shipped examples free to use.
2. **Fable 12nqia selected checkpoints on the public validation images. I rate it grey_area, grader agreement unclear.**
   - At [94] its `eval_ckpt.sh` ran `validate.py --data /workspace/val/validation.jsonl` for every checkpoint.
   - Its README at [221] says: "validation reports of checkpoints ... on the task's public validation images (used for checkpoint selection only; never trained on)."
   - It picked its 5-checkpoint average because "The five-checkpoint average now scores 0.610 locally, beating the current submission's 0.593".
   - DeepSeek, Argon and Astra explicitly treated this as forbidden.
   - The effect looks negligible (0.610 public vs 0.6055 held-out), and the trial is not a winner.
3. **The pixel-threshold blank masks in the three Opus trials are allowed.**
   - They fall under "Deterministic image preprocessing" (`review.py:16`) and carry layout only.
   - No other model used one, so the reviewer's three passes are not inconsistent.
4. **Wallet scaling is inverted for Argon and Muse** because their architectures changed between wallets, not because of grading noise.

## Epoch scoring item: **pass**

- No scoring defect changes a winner.
- The rule ambiguity (finding 2) affects only a non-winning trial.

## Task design

- **Metric is sound and deterministic.** Per-image 1 - word-level Levenshtein / longer token count after a pinned normalization (`tests/task/ocr_text.py:17-23,97-99`), shipped to the agent. Nondeterministic decodes keep the lower of two scores (`validate.py:200-205`). No judge.
- **Anchors are sensible.** 0 is empty text. A blind decoder emitting fluent unrelated text gets about 0.04 raw (`ocr_text.py:20-22`), roughly where the near-blind Muse/DeepSeek trials sit (1.9-4.4). 100 is uncapped DeepSeek-OCR (0.8931; 0.8978 on public, `task.yaml:52-56`). It is not binding (best 82.6), and almost the whole range is used.
- **The held-out set is clean.** 400 HTML pages rendered from fresh arXiv text (CC0 metadata and CC-BY full text), balanced at 50 per kind x density cell. Ground truth is DOM `innerText` (`ocr_latent_render.py:3-16,685`). Public pages come from the same generator, with papers split by hash (`ocr_latent_render.py:59-64`), so there is no distribution shift. One SE is about 1 point (stratified; about 1.5 unstratified).
- **Self-check is faithful.** It runs grading's two isolated phases at full size (400 / ~420 requests) under the same 1 image/s deadlines on the grading H100 (`tests/task/verifier.py:101-175`). Only the review and held-out content are missing.
- **The promised provenance check does not exist.** CONTRACT.md:17 says "I will check for training-data provenance", but `tests/task/review.py:7,21,30` has only three architecture checks. The data rule in `instruction.md:9` is unenforced.
- **Use of the public images is ambiguous.** They are named `validation.jsonl`, and the rule forbids selecting on "the validation ... split of any public dataset". Unlike maple-vlm/music (`task.yaml:4 shipped_examples_free: true`), this task does not free them. Agents split on it (finding 2 above).
- **Encode/decode isolation rests on the reviewer.** Both phases extract the submission from the same per-trial volume, and "nothing here checks which sandbox a phase ran in" (`verifier.py:6-9`), while serve.sh can write to /submission (CONTRACT.md:24-25). This is a gaming path only an LLM review closes; no trial tried it.
- **Possible overlap with held-out text (suspected).** Held-out text is recent arXiv (`ocr_latent_sources.py:3-11`), and "other public corpora are fine". A decoder trained on a current arXiv dump could learn the exact held-out text. The trials used old snapshots (Opus 2pu2n0: arxiv-metadata-snapshot shard 00000), so this was not observed.
- **Budget buys score.** It is feasible at $10 (Fable 56.1, Sonnet 55.8), and money helps strong agents (Opus 26.9 -> 54.4 -> 82.6). `solution/` is only the shared smoke fixture (empty codes and text, 0). The organizer PCA/FSQ baselines exist, but no scores are recorded.
- **Verdict: minor_issues.** The scoring and anchors are fair, and the unenforced or ambiguous data rules change no winner.
