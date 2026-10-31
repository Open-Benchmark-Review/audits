# AI-text Detection

Task slug: `ai-text-detection` (Applied NLP, inspired by Pangram)

## The task

The agent trains one local model that gives P(AI-written) for a passage. It must work in 8 languages (ar, zh, en, fr, de, pt, ru, es).

- **Starting point:** any general pretrained backbone, but not an AI-text detector.
- **Data provided:** 200 labeled passages, which the agent may use any way it likes. They contain no Russian.
- **Data rule:** public training splits are allowed. Validation and test splits of public datasets are not.
- **Serving:** `POST /detect` at 10 passages/s or faster, with 32 concurrent requests, ready within 300 s.
- **Statelessness:** the CONTRACT forbids caching or comparing across requests.

## How scoring works

- **Metric:** 1 − mean FNR over language × generator × condition cells. One global threshold is set so that at most 1% of humans score strictly above it (`environment/validation/validate.py:52-55`). An AI passage that ties the threshold counts as missed.
- **Held-out batch:** 5,000 passages. That is one AI row per language/generator/condition/domain (8 × 4 × 16 × 6 = 3,072) plus 1,928 humans (`tests/task/verifier.py:27-60`).
- **Source of the held-out set:** the public test rows of **DetectRL-X** (`WUJUNCHAO/DetectRL-X`). The trusted review policy says: "the held-out passages are drawn from its test rows ... while its training rows are an ordinary public training split" (`tests/task/review.py:36-38`). Held-out groups that overlap DetectRL-X train are dropped (`ai_text_detection.py:157-167`).

## Results

| Model | $10 | $50 | $200 | Used DetectRL-X train? |
|---|---|---|---|---|
| Claude Opus 5.5 | **98.3** (4qgtmq) | **98.9** (5f6q4z) | **99.2** (3ie01s) | yes, all 3 |
| GPT-6 Astra | 90.7 (3z1pot) | 91.9 (30himq) | 94.2 (5im6qs) | yes, all 3 |
| DeepSeek V4.1 Flash | 87.1 (1rg72h) | 78.3 (5pepog) | 89.0 (z7tnpk) | yes (5pepog only late, v7) |
| Gemini 4 Argon | 44.2 (2itta7) | 27.0 (3hgrat) | 87.0 (2li4i8) | no |
| Claude Fable 5.1 | 71.9 (yllepg) | 83.6 (6c6gex) | 83.2 (1h934s) | no |
| Muse Wonder | 73.0 (2jzq5c) | 48.8 (13r3lz) | 69.2 (3p343s) | no |

All 18 reviews passed. I agree with all 18. There are no false positives, no false negatives and no infrastructure zeros.

## What each model did

- **Opus** recognised the benchmark from the validation metadata.
  - 4qgtmq [15]: "Found the likely source benchmark: **DetectRL-X** on HF has exactly these 16 conditions and 8 languages".
  - It trained Qwen2.5-3B or Qwen3-4B (LoRA) on DetectRL-X train rows only.
  - It rebuilt the 16 attack conditions from the paper: character and zero-width edits, truncations, mBERT/mBART, the authors' Qwen-DPO paraphrasers, and an mT5 "humanizer" trained on train pairs to emulate seq2seq paraphrasing (5f6q4z [206]).
- **Astra and DeepSeek** found DetectRL-X too and trained XLM-R or mDeBERTa encoders on it. These are smaller backbones, so they land 5-20 points lower.
- **Fable, Muse and Gemini** never mentioned DetectRL-X.
  - They built training sets from other public MGT corpora (MAGE, RAID, SemEval-2024, COLING-2025, HC3), human corpora and their own LLM generations.
  - They plateau at 70-87.

## Key findings

1. **The task mostly measures whether the agent identifies the source benchmark.**
   - The held-out set is a public benchmark test split, and its train split is legally usable and in-distribution: same generators, domains and 16 attack conditions.
   - DetectRL-X users average 92.0. Non-users average 65.3.
   - The blog's claim of out-of-distribution held-out tests does not hold here.
   - Only the reviewer stands between an agent and the public test rows.
2. **Reading test rows for inspection was judged the same way across models.**
   - Opus 3ie01s [15] matched the validation passages against the full DetectRL-X file. Its finding at [16]: "Validation samples all came from DetectRL-X's test split".
   - DeepSeek z7tnpk [111] compared test-split strategy files.
   - review.py allows reading test rows only for decontamination. Neither trial fed the rows into training, and the reviewer passed both.
3. **Overfitting the 200 public passages is allowed but costly.**
   - Gemini 3hgrat fitted its readouts by 5-fold CV on the 200 passages.
   - Its public diagnostic was 0.98 ([289], [294]). Its held-out score was 27.0.
4. **Saturated scores are penalised.**
   - Muse thresholds sit at 1.0000 or 0.9999, with realized FPR 0.0093.
   - Every AI passage scored 1.0 ties the threshold and counts as a miss.
5. **Other observations.**
   - The Gemini trials are re-runs. 3hgrat is r4, from 2026-10-17, after release. Its web search at [20] returned a generic summary whose sources were all frontierml.org pages. The agent did not open them.
   - No trial accessed `inductionlabs/frontier-ml-tasks` or the benchmark repo.

## Epoch scoring item: **pass**

- No scoring defect changes a winner. Opus wins every wallet by 5 or more points with clean train-split provenance.
- The design flaw (held-out = public test split, train split allowed) affects what is measured, not who wins.

## Task design

- **Held-out set = public benchmark test rows, and the train split is allowed.** The 78,090 held-out rows are DetectRL-X's ungated test rows (MIT; `tests/task/ai_text_detection_sources.json:2-5`). Its train split is "an ordinary public training split" (`tests/task/review.py:38-39`). Only the rubric names the source; the agent never sees it. The 16 DetectRL-X condition names ship verbatim in the public rows (`ai_text_detection.py:33-35`, `:327`), so recognising the benchmark is the main skill measured: users average 92.0, non-users 65.3.
- **Not out-of-distribution.** Public and held-out rows come from the same DetectRL-X test pool. The only shift is that Russian is withheld from the 200 public rows (`ai_text_detection.py:206-211`). The instruction lists Russian, and self-check warns about it (`tests/task/verifier.py:109-110`).
- **Only 6.4% of the held-out set is graded.** 5,000 of 78,090 rows: 3,072 AI (one per language × family × condition × domain) plus 1,928 humans (`tests/config.json:5-6`, `tests/task/verifier.py:27-59`). The 1% FPR threshold therefore rests on about 19 human passages. A Gaussian-ROC simulation puts one SE at about 3.4 points for a model scoring 53, 2.1 at 85 and 0.4 at 98. That is larger than the 0.5-point estimate above, and it matters for mid-table ranks only.
- **Anchors: none.** There is no `score_normalization` (`tests/task/task.yaml:1-50`). The reward is raw 1 − macro FNR. A constant or blind detector scores 0, because ties count as misses (`environment/validation/validate.py:52-55`, `:102`). The full 0-100 range is used: observed 0-99.2.
- **Saturation trap.** p_ai is capped at 1, and an AI passage at or below the threshold is missed. A detector that outputs 1.0 for at least 1% of humans therefore loses every AI passage scored 1.0. The contract documents "at or below" (`CONTRACT.md:11`), but not this consequence; it is what cost Muse points.
- **Prompt rule without a check.** "Not one already trained for AI-text detection" (`instruction.md:3`) has no named review check. The rubric's `single_local_model_scores` only requires that the candidate trained the detector, and it bans zero-shot LM-likelihood features, which the prompt implies but does not state (`tests/task/review.py:11-17`).
- **Gate.** All-or-nothing: 500 s for the 5,000-row batch, including the cold first request (`tests/task/verifier.py:175`). 10 passages/s is lenient, and self-check runs the same path at the same size, so its fidelity is good. Self-check cannot test the review, which is where leakage control lives.
- **Budget.** $10 is enough (Opus 98.3). The 19-model mean barely moves: 69.7 / 71.3 / 73.0 at $10 / $50 / $200.
- **Reference solution.** It is the shared smoke fixture, a constant `{"p_ai": 0.5}` (`solution/server.py:127`). It scores 0 and does not show the task is solvable.
- **Fine:** the scoring is deterministic (SHA-256 subset selection, no judge). Failed requests score as the worst answer. Source groups that overlap DetectRL-X train were removed (`ai_text_detection.py:166-167`).

**Fairness verdict: unfair.** The metric is correct, but the design rewards recognising DetectRL-X, whose in-distribution train split is legal, more than detector-building skill.
