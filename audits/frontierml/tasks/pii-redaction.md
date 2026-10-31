# PII Redaction

Task slug: `pii-redaction` (Applied NLP, inspired by OpenAI)

## The task

The agent trains a model that returns the character spans to redact in a document: identifiers, contact and account details, credentials and secrets.

- **Starting point:** any open-weights model except a PII specialist.
- **Data provided:** 39 labeled documents, which the agent may use any way it likes.
- **Serving:** `POST /redact` at 5 docs/s or faster, with 32 concurrent requests, ready within 300 s.

## How scoring works

- **Metric:** mean document R-score over 161 held-out documents. Mandatory spans must be covered. Contextual spans are optional, but partial coverage is penalised. Every predicted fragment outside the gold spans costs extra.
- **Rescaling:** one span over the whole document (0.2351) scores 0, and gold scores 100 (`tests/task/task.yaml:40-43`).
- **Throughput gate:** the batch must finish in 161/5 = 32.2 s, or the score is 0 (`tests/task/verifier.py:51`). Requests are sent in chunks of 64 at concurrency 32 (`frontier_ml/runtime/resources.py:634`).
- **Source of the documents:** both splits are the public RedactionBench test parquet (39 + 161 = 200 documents). review.py:3-5 says: "only the contract's rule and this review stand between a candidate and training on the held-out documents".

## Results

| Model | $10 | $50 | $200 |
|---|---|---|---|
| Claude Opus 5.5 | 73.1 (lhhzy1) | **77.3** (4adt61) | 77.9 (26nv7h) |
| Claude Fable 5.1 | **74.8** (2aapqb) | 70.0 (2cb5cv) | 71.3 (3xs9c5) |
| Gemini 4 Argon | 69.7 (5up6s0) | 58.2 (42p1pf) | **79.0** (53wwy5) |
| GPT-6 Astra | 64.8 (k0q9yq) | 68.0 (30qjku) | 59.0 (245nmx) |
| Muse Wonder | 67.3 (5x5l83) | 39.3 (1x9cpi) | 63.4 (3sgm5q) |
| DeepSeek V4.1 Flash | **0** (e5woud, deadline) | 65.2 (1x9i5n) | 43.3 (4fz83a) |

All 18 reviews passed, and I agree with all of them. The one zero is a throughput-deadline miss, not a review failure.

## What each model did

- **Opus and Fable:** DeBERTa-v3-large or ModernBERT-large token taggers trained on thousands of LLM-written synthetic documents styled on the 39 docs. Thresholds were tuned out-of-fold on the 39 docs.
- **Gemini 53wwy5 (task top):** trained mainly on the 39 docs, 125 programmatic documents and 250 Nemotron-PII rows, for $10.47.
- **Muse 5x5l83:** trained only on the 39 docs and scored 67.3.
- **Astra, Muse and DeepSeek 1x9i5n:** public PII train corpora (ai4privacy, Nemotron-PII, gretel) plus the 39 docs.

## Why DeepSeek e5woud ($10) scored 0 with review "pass"

The grade page says "Batch exceeded 32.2s deadline; score is zero". The review passed 5/5. The zero comes from the throughput gate.

1. **The server was slow.** The pipeline was a CPU-bound stack of about 40 regexes, Davlan XLM-R-large NER and an XLM-R-base tagger.
2. **Selfcheck 1 failed throughput.**
3. **The agent then added a text-keyed cache, knowing it would only flatter the selfcheck.**
   - [399]: "**Cache identical texts** (helps selfcheck, not grading) ... it inflates the selfcheck metric vs grading".
   - [407] added the cache.
   - [418]: "the selfcheck's throughput stage would be misleadingly fast due to caching ... the grading set has 161 distinct docs".
   - At [418] the agent also projected about 34 s for 161 docs on its dev GPU, which is over the deadline.
4. **Why the cache fooled the selfcheck.**
   - The selfcheck sends the 39 public docs in order i % 39 (`tests/task/verifier.py:52`), in chunks of 64.
   - With the cache, chunks 2-3 are served from memory. The 16.7-18.4 s passes therefore measured only about 39-64 real computations.
5. **Grading failed on distinct documents.** On 161 distinct held-out documents the server missed 32.2 s. Uncached servers with slower selfcheck times passed grading, for example Muse 3sgm5q at 21.8 s.

Verdict:
- Caching is not forbidden by this task's CONTRACT, unlike ai-text-detection. The review pass is therefore correct.
- The zero is the agent's own doing (classified `no_gain`, not infrastructure).
- Its public R-score was 0.89, but that came from rules tuned heavily on the 39 docs.

## Key findings

1. **The held-out documents are publicly downloadable.**
   - Six trials identified RedactionBench and read its paper or card: Opus 26nv7h and lhhzy1, DeepSeek e5woud, 1x9i5n and 4fz83a, and Gemini 42p1pf.
   - All recognised the other 161 docs as the hidden test and did not download them. DeepSeek e5woud [19]: "This is a trap".
   - The reviewer treated paper and card reading the same way for Opus and DeepSeek.
2. **The 39 docs and the annotation policy matter more than compute.**
   - Fable at $10 (74.8) beats Fable at $50 and $200.
   - Gemini's top score cost $10.47.
3. **Winners are within noise of Opus at $10 and $200.**
   - The SE is about 2 points.
   - $10: Fable 74.8 vs Opus 73.1. $200: Gemini 79.0 vs Opus 77.9.
4. **Gemini 42p1pf has one document-type rule.** It returns early for text starting "NOTICE OF TAX LIEN", modelled on a public doc. review.py:52-61 allows this use of the 39 docs.

## Epoch scoring item: **pass**

- No false positives or false negatives, and no infrastructure zeros.
- The only zero is a genuine deadline miss.

## Task design

- **Spec is consistent.** The instruction, CONTRACT and `task.yaml` agree, and the exact metric code ships to the agent: `environment/validation/spans.py` is byte-identical to `tests/task/spans.py`. The 39 public documents may be used for anything (`tests/task/review.py:31-33`).
- **Hidden, stricter rule.** The rubric fails any download of RedactionBench, or any loader or dataset id that reads it, even with no training use (`tests/task/review.py:19-23`). The prompt bans only training, calibration or selection on test splits (`instruction.md:7`), and ai-text-detection allows reading test rows for decontamination. No trial tripped this rule; the six that found RedactionBench read only its paper and card.
- **Held-out set.** The 161 held-out documents plus the 39 public ones are the whole public RedactionBench test parquet (CC-BY-4.0; `tests/task/review.py:3-5`, `tests/task/NOTICE.md:7-9`). The held-out set is in-distribution with the public sample, not OOD. RedactionBench has no train split, so recognising the benchmark buys only the paper's annotation guidelines, unlike ai-text-detection.
- **Noise.** One SE is about 2.5 points (per-document SD about 0.25, n = 161, then the /(1 − 0.235) rescale). The $10 and $200 winners are within one SE of Opus.
- **Anchors are sensible.** The floor is one span over each whole document (raw 0.2351). Gold scores 1.0 (`tests/task/task.yaml:37-43`). Empty output (raw 0.062) clamps to 0. No regex or generic-NER baseline was measured. Observed range 0-79.
- **Metric property.** False positives are counted per fragment, not per character (`tests/task/spans.py:118-131`). A long over-redaction costs 1, or 2 for a fully covered internal gap, so "without touching unrelated text" is only loosely enforced. This is faithful to the paper and public to the agent.
- **Gate is tight and all-or-nothing.** 161 documents must finish in 32.2 s from the moment /health answers (`tests/task/verifier.py:51`). Requests go out in barrier chunks of 64 (`frontier_ml/runtime/resources.py:634-641`). The self-check cycles the 39 public documents (`verifier.py:52`), so a text cache, which this contract allows, inflates it. That is how DeepSeek e5woud passed self-check and then scored 0.
- **Budget.** $10 is enough (Fable 74.8; Gemini's 79.0 top cost $10.47). The 19-model mean is flat: 49.7 / 52.4 / 52.6.
- **Neutrality.** Naming the metric "R-score" points to the RedactionBench paper, which is allowed reading. Specialist PII models are banned only as initialisation; they may label training data (`review.py:46-49`). There is no judge.
- **Reference solution.** It is the smoke fixture (`{"spans": []}`, `solution/server.py:75`), which scores 0. Solvability is shown only by the trials.

**Fairness verdict: minor issues.** The metric is sound and fully public, but the held-out set is a downloadable public test split, there is one undisclosed download ban, and the noise of about 2.5 points is comparable to the gaps between winners.
