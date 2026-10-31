# HotpotQA Dense Retriever Training

Raw id: `learn-to-retrieve-both-supporting-documents-for-hotpotqa-c3200db1` (Deep learning training, 2x H200)

## The task

The agent must improve the training recipe for a BERT-Tiny bi-encoder (mean pooling, cosine ranking) so it ranks HotpotQA's two supporting paragraphs higher.

- **Fixed:** architecture, tokenizer, pooling, checkpoint initialisation.
- **Budgets:** 900 s of training on 2 GPUs; 600 s of retrieval.
- **Data:** only `assets/hotpotqa/train` (questions plus a 200k-paragraph corpus).
- **The workspace also ships a public panel:** 3,072 queries, a 60k-paragraph corpus, and the gold labels. The prompt does not allow training on it.

## How scoring works

- **Metric:** nDCG@10 over 3,072 private questions and 60k private paragraphs.
- **Reward:** `C / B − 1`.
- **Private baseline:** exactly 0.45676 in all 10 breakdowns, so it is cached or deterministic. The public baseline is 0.4473.
- **Invalid:** training over 900 s, or weights that do not fit the fixed model.

## Results

| Model | Trial | Official | Private nDCG | Final public | Verdict |
|---|---|---|---|---|---|
| Claude Fable 5.1 | 9pA8cjv | **0.619** | 0.739 | 0.733 | research, agree |
| Claude Fable 5.1 | aJjZCsq | 0.608 | 0.734 | 0.730 | research, agree |
| GPT-6 Astra | X9nMioc | 0.581 | ≈0.722 (no breakdown) | 0.713 | engineering, agree |
| GPT-6 Astra | UP8vb7Q | 0.550 | ≈0.708 (no breakdown) | 0.703 | engineering, agree |
| Gemini 4 Argon | 4b65pXr | 0.450 | 0.662 | 0.663 | engineering, agree |
| Gemini 4 Argon | j9GZ5Ey | 0.427 | 0.652 | 0.653 | engineering, agree |
| Grok 4.7 | ztGi4di | 0.378 | 0.629 | 0.628 | engineering, agree |
| Grok 4.7 | 2Kkt2pC | 0.372 | 0.627 | ≈0.62 | engineering, agree |
| Kimi K3 | 8moZreh | 0.351 | 0.617 | ≈0.610 | engineering, agree |
| Gemini 3.8 Flash | PhEvjxs | 0.338 | ≈0.611 (no breakdown) | 0.613 | engineering, agree |
| Kimi K3 | cMLMUiT | 0.315 | 0.601 | 0.585 | engineering, agree |
| Gemini 3.8 Flash | rJ6pCLZ | 0.247 | 0.570 | 0.567 | engineering, agree |

## What the agents did

**Fable: research.**
- Spends most of the budget (~760 s and ~85%) on contrastive pretraining with pseudo-queries over the train corpus (inverse-cloze, ICT-style).
- Then runs a short supervised fine-tune with negatives re-mined by the current model.
- Two transferable data ideas, with ablations:
  - multi-positive *composite* queries built from two random paragraphs (+1.2 points);
  - keyword queries sampled by idf², to close the lexical gap to BM25 on bridge questions.
- Ablation path (RECIPE.md): 0.447 → 0.566 (mined negatives) → 0.644 (ICT) → 0.686 (full budget) → 0.733.

**GPT: corpus pretraining plus teachers.**
- Corpus pretraining, either crop/ICT or graph adaptation over title-mention links.
- Then cross-encoder teachers and distillation.

**Argon, Grok, Kimi, Flash: known supervised techniques.**
- Mined hard negatives, cross-GPU in-batch negatives, longer schedules.
- Cross-encoder or ensemble distillation; weight soups.
- Argon additionally used an embedding reparameterisation during training (exported as plain BERT weights) and PCA distillation of a 10-branch ensemble.
- These trials did not do large-scale corpus pretraining.

**Rule compliance.** Every `training.py` reads only `--train_dir`. The public panel was used only by dev and evaluation helpers.

## Key findings

**1. The train corpus overlaps the evaluation corpus.**
- 24,389 of the 60k public-panel paragraphs, and 2,292 of the 5,922 gold paragraphs (~39%), also appear in the 200k train corpus (Fable 9pA8cjv [15], [87]; aJjZCsq [13]–[14]).
- So corpus pretraining partly memorises evaluation documents. Fable: link pretraining "only works because ... roughly 39% of gold docs overlap".
- This is allowed by the rules and probably mirrored in the private panel.
- It inflates absolute nDCG and favours the corpus-pretraining recipes, which are exactly the top two models.

**2. Private and public match closely.**
- The private set is the same distribution but a different sample (baseline 0.4568 vs 0.4473).
- Every trial's private nDCG is within −0.001 to +0.016 of its public nDCG.
- No training on eval queries or documents, and no leakage of supporting-document labels, was found.

**3. Missing breakdowns.**
- Three trials have none (both GPT trials, Flash PhEvjxs).
- Flash PhEvjxs was scored despite an `ArtifactCollectionError`. Its implied nDCG (≈0.611) matches its public 0.6126.

**4. Noise is small next to the gaps.**
- Run-to-run noise is ±0.003 nDCG (±0.007 reward), and the baseline is fixed.
- Gaps between models are ≥0.03, so the ranking is robust.

## Epoch scoring item

**Pass.** The baseline is fixed, the noise is small, the private set is distinct, and there are no false positives or negatives. The corpus overlap inflates absolute scores but does not change the winner (Fable).
