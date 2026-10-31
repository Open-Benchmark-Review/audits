# Zero-shot Classification

Task slug: `zero-shot-classification` (Applied NLP, inspired by TypeSafe)

## The task

The agent trains a classifier that takes a text plus 2-256 label descriptions and returns calibrated probabilities.

- **Data rules:** no split of BTZSC or its source datasets may be used. `DATA_POLICY.md` lists 22 sources, plus their "mirrors, subsets or derivatives".
- **Model rules:** no benchmark-tuned checkpoints and no JEV reproductions.
- **Provided rows:** the 500 shipped DBpedia-14 test rows may only be used to check the server.
- **Serving:** 50 docs/s or faster at 32 concurrency.
- **Statelessness:** no caching, not even label embeddings.

## How scoring works

- **Metric:** macro-F1 × (1 − top-label ECE, 15 bins) per dataset.
- **Held-out set:** 22 BTZSC datasets × 200 rows.
- **Rescaling:** each dataset is rescaled from a uniform-probability floor to 1.0, then the datasets are averaged (`tests/task/task.yaml:42-67`). Binary datasets have floors around 0.51, which roughly doubles their noise.

## Results

| Model | $10 | $50 | $200 |
|---|---|---|---|
| Claude Fable 5.1 | **59.6** (42xw3e) | 0 — review fail (4zb5b5) | **62.1** (1w83ln) |
| Claude Opus 5.5 | 59.3 (2bb9rl) | **57.7** (1j4hzb) | 59.0 (3jhxni) |
| Gemini 4 Argon | 58.6 (2pnpy0) | 54.8 (1bf19e) | 37.7 (61pi2e) |
| GPT-6 Astra | 52.5 (66jjjy) | 47.8 (18lqgv) | 46.7 (2pngu5) |
| Muse Wonder | 48.6 (5gai5b) | 16.0 (4tvmr8) | 37.1 (1ftq4w) |
| DeepSeek V4.1 Flash | 45.2 (3ctw07) | 39.8 (5cndkd) | 41.2 (58tjfz) |

## What each model did

- **Top tier (58-62):** Qwen3-4B-Instruct (or Qwen2.5-3B) with LoRA plus a listwise or pointer label head (Fable, Opus, Gemini 2pnpy0 and 1bf19e).
  - Trained on 25-50 public train splits with paraphrased label descriptions, NLI data and LLM-generated synthetic tasks.
  - Temperature calibrated on held-out train rows.
- **Lower tier (37-52):**
  - NLI cross-encoders: DeepSeek, Astra 18lqgv, Muse 5gai5b.
  - Bi-encoders: DeepSeek 58tjfz, Muse.
  - A frozen `deberta-v3-large-zeroshot-v2.0-c` with a new head (Astra 2pngu5). The -c variant is trained only on MNLI, FEVER-NLI and synthetic data, so it is allowed.

## Key findings

1. **The one review fail is correct.**
   - Fable 4zb5b5 trained on `FinanceInc/auditor_sentiment`. [47]: "emitted auditor_sentiment: 3877 rows, 3 labels".
   - That dataset re-hosts Financial PhraseBank, a BTZSC source (DATA_POLICY.md:12). 3,877 + 969 rows = 4,846, the size of the 50agree set.
   - The agent picked it from an HF candidate list ([16]) without checking where it came from. The violation looks inadvertent, but the rule is explicit.
   - No Opus trial used a Financial PhraseBank mirror.
2. **The rule on upstream sources is ambiguous, and agents split on it.**
   - Social Bias Frames is built partly from the Davidson 2017, Founta, Waseem & Hovy and Stormfront (`hate_speech18`) corpora. DATA_POLICY.md:10 bans SBF and its "mirrors, subsets or derivatives" but names no upstream corpora for it. For TrueTeacher it does name the upstream source (CNN/DM, DATA_POLICY.md:28-33).
   - Opus 2bb9rl [15] excluded the upstream sources: "Banned (plus upstream sources): SLURP/HWU64 (MASSIVE source), Davidson/Founta/Waseem/Gab/Stormfront (SBF sources)". Opus 3jhxni [106] did the same.
   - These trials trained on Davidson and/or Stormfront: Fable 1w83ln ([23] "== davidson: +3000"), Fable 42xw3e ([50]), Opus 1j4hzb ([98] "hate_speech_offensive toxicity 3 8000"), DeepSeek 58tjfz and Muse 1ftq4w.
   - The reviewer passed all of them, consistently across models. Per-dataset scores show no benefit: the SBF normalised mean is 42-44 for the Fable and Opus users and 42.6 for Opus 3jhxni, which did not use them.
3. **Fable 42xw3e may have used an SBF derivative.**
   - It also trained on `allenai/prosocial-dialog` ([50]; "prosocial" is in its in-domain dev at [108]).
   - If ProsocialDialog's contexts come from the Social Bias Inference Corpus, as I believe, it is an explicitly banned derivative. The trajectory does not show its card, so this is unclear.
4. **Money did not help.** No model improves monotonically with wallet size. Astra used under 1.3 of 12 hours in every trial.

## Epoch scoring item: **unclear**

- **Under the written rule (the reviewer's reading), the winners stand:** Fable at $10 and $200, Opus at $50.
- **Under the strict reading that Opus itself applied (SBF upstream sources banned),** Fable 42xw3e, Fable 1w83ln and Opus 1j4hzb would be voided. The wins would go to Opus 2bb9rl ($10), Gemini 1bf19e ($50) and Opus 3jhxni ($200).
- **The $10 result is also a three-way tie within noise** (59.6 / 59.3 / 58.6, SE about 1.4).

## Task design

- **Spec is consistent and unusually explicit.** The prompt, CONTRACT, `DATA_POLICY.md` and the rubric all name the 22 BTZSC sources and ban selection on the 500 DBpedia rows. The one gap is upstream corpora: other-name derivatives are listed for Rotten Tomatoes and TrueTeacher (`tests/task/review.py:18-22`), but not for Social Bias Frames, MASSIVE or Yelp (`tests/task/pipeline/DATA_POLICY.md:10`). Agents split on this, and the reviewer passed both readings.
- **Genuinely out-of-distribution.** The public rows are DBpedia-14 topic rows with the label descriptions "This text describes …" (`tests/task/zsc_data.py:81-84`). The held-out set is 200 hash-sampled rows from each of BTZSC's 22 public test parquets (`zsc_data.py:71-73`, `pipeline/source_lock.json`). Leakage control is review-only, and the organisers' own manifest still says "BTZSC redistribution license audit pending" (`zsc_data.py:168`).
- **Anchors.** Each dataset is rescaled from its own uniform-probability floor (raw 0.3212 overall) to one-hot gold 1.0, and clamped at 0 (`tests/task/task.yaml:40-68`). Binary floors are about 0.51, which roughly doubles those datasets' noise. No trained or off-the-shelf baseline was measured (`pipeline/sanity_results.json:4`, `"trained_model_baseline": null`). A frozen NLI zero-shot encoder with a new head already reaches about 47. Observed range 0-63.6.
- **Noise.** One SE is about 1.3 points. Simulation gives a per-dataset normalised SD of about 6 points (binary) or 4 (10-class) at 200 rows. Related datasets share texts (4 wikitoxic, 3 biasframes = 32% of weight; `zsc_data.py:168`), so the effective number of independent datasets is under 22.
- **Metric and grading are correct and deterministic.** Macro-F1 over the union of gold and predicted classes, times (1 − 15-bin top-label ECE) (`tests/task/zsc_metric.py:74-99`). Label order is permuted with a fixed seed (`tests/task/zsc_protocol.py:85`). A failed request scores as a confidently wrong answer (`zsc_metric.py:23-31`). There is no judge.
- **Self-check under-loads the gate.** Grading allows 88 s for 4,400 documents, all-or-nothing (`tests/task/verifier.py:96-97`). Held-out requests are about 1.75× the public ones in bytes (longer descriptions, 2-72 labels), and the self-check discloses this only as a note (`verifier.py:167-173`). Four non-audited trials scored 0 with a review pass; a gate miss is plausible but unconfirmed.
- **Unenforceable-by-code rules.** "No caching (not even label embeddings)" and "no label-frequency fitting" (`CONTRACT.md:7`, `tests/task/review.py:44-50`) are checked only by the reviewer, even though every dataset repeats one label set 200 times.
- **Budget.** $10 is enough (Fable 59.6, Opus 59.3). Money does not help: the 19-model mean is 35.5 / 32.7 / 33.3. Review fails (9 of 13 zeros) matter more than compute.
- **Reference solution.** It is the smoke fixture, which returns uniform probabilities (`solution/server.py:86`). That is the floor, so it scores 0, and it fails `task_time_training`.

**Fairness verdict: minor issues.** The design is OOD and well specified, but the upstream-source rule is uneven, the self-check throughput batch is about 1.75× lighter than grading, and binary-dataset floors amplify the noise.
