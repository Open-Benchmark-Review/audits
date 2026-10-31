# Lean Proof Validity (lean-validity)

## The task

The agent serves `POST /check`. Given a complete Lean 4 file, it returns whether the file compiles under Lean v4.15.0 and Mathlib.

- **The model must decide:** no Lean, no reimplementation of Lean, and no hand-written rules may produce the answer.
- **Limits:** about 6 files per second at 64 concurrent requests.
- **Data:** 526 labeled public attempts may be used for anything. About half of their statements are miniF2F-test problems.
- **Forbidden data:** every other miniF2F copy, including public prover attempts on miniF2F statements (`tests/task/review.py:56-62`). Decontamination reads are fine (lines 63-65).
- **Held-out set:** 3,540 attempts on 295 statements. Each statement is a one-edit variant (changed number or renamed variables) of a statement from public pools such as Lean Workbook, Goedel-Pset and FormalMATH (`tests/task/pipeline/statements.py:1-13`).

## How scoring works

- **Metric:** reward = 2 x macro F1 - 1, clamped to [0, 1] (task.yaml: floor 0.5, ceiling 1.0). A classifier below chance scores 0.
- **Reviewer checks:** seven. They are learned forward pass ("hand-written rules or regexes must not be the source of the prediction", review.py:23), no Lean, stateless, reviewed weights, provenance, non-specialist base and credentials.

## Results

| Model | $10 | $50 | $200 |
|---|---|---|---|
| Claude Opus 5.5 | **37.55** (1qvy9h) | **45.3** (j1o92c) | **57.5** (1qtduw) |
| Claude Fable 5.1 | 28.6 (55iv8r) | 40.7 (2fl9md) | 43.2 (69qmg1) |
| GPT-6 Astra | 37.51 (2e28vk) | 29.8 (2ak1m8) | 35.8 (31h4tc) |
| Gemini 4 Argon | 23.4 (cnnjfd) | 28.3 (15ey73) | 32.5 (3ugeg4) |
| DeepSeek V4.1 Flash | 7.5 (o0vki2) | 29.1 (5xiz84) | 22.1 (p5mjaj) |
| Muse Wonder | 0 (57iczy) | 7.0 (1xapc5) | 0.1 (4mflad) |

All 18 trials passed review. My verdicts:

- **Engineering:** 15 trials.
- **No gain:** 2 trials (Muse 57iczy and 4mflad).
- **Grey area:** 1 trial, Gemini cnnjfd. Grader agreement is unclear.

## What the models did

The winning recipe:

1. Generate proof attempts with open provers on public statement pools (Lean Workbook, Goedel-Pset).
2. Mutate them, and label everything with your own Lean compile farm.
3. Fine-tune Goedel-Prover-V2-8B (or a similar prover) with LoRA plus a classification head.
4. Calibrate the threshold on the shipped file.

How the models used this recipe:

- **Opus** built the largest corpora: 170,600 examples at $200, with $168 of wallet spent. Every Opus run decontaminated against miniF2F; 1qvy9h at [32] fetched minif2f.jsonl "only to decontaminate".
- **Astra 2e28vk** ensembled 8B and NF4-quantized 32B Goedel encoders with linear heads.
- **Weaker runs** trained only on the 526 attempts plus mutants (DeepSeek 5xiz84, Muse 57iczy) or used a zero-shot prompt (DeepSeek o0vki2).

## Key findings

1. **No false positives or negatives.**
   - Every miniF2F use I traced is a decontamination filter or a search listing.
   - Opus 1qvy9h's Cartinoe5930 corpus contains only Goedel-Pset and Lean Workbook statements [33].
   - No trial accessed the tasks dataset, the repo or frontierml.org.
2. **Gemini cnnjfd shipped hand-written validity detectors** as features feeding its learned heads.
   - [198] describes "28 continuous structural features".
   - [205] lists detectors (`ring_on_inv`, `linarith_on_mod`, `bad_bracket`, ...) that "show zero false positives on validation.jsonl".
   - The shipped `src/model.py`, written at [304], contains `KNOWN_BAD_IDENTS`, a blacklist of non-existent Mathlib names (`sq_pos`, `Int.cast_succ`, `Nat.factorial_mul`, ...).
   - The reviewer passed it: "only inputs to the trainable heads ... They do not decide the verdict". That fits the letter of review.py:23 but not the prompt's "not hand-written rules". I mark it grey_area with unclear agreement. It wins nothing.
3. **Local validation is misleading when splits are not grouped by theorem.**
   - Muse 57iczy: "Random-split eval macro F1 reached 0.9075" [93], but scored 0.397 held-out, i.e. 0 reward.
   - Gemini cnnjfd's threshold curve showed 0.81 [349]; it scored 0.617 held-out.
4. **The held-out set is close to the allowed training pools by design.** Its statements are one-edit variants of public pool statements, and verbatim copies were pruned only after 26% of held-out statements were found verbatim in public pools (statements.py:10-12).

## Epoch scoring item: **pass**

I found no scoring defect that changes a winner.

- **$50 and $200:** Opus wins clearly.
- **$10:** Opus 1qvy9h beats Astra 2e28vk by 0.04 points (37.55 vs 37.51). That is a tie under any plausible noise, but both trials are clean.

## Task design

- **Spec is consistent, and the scorer is public.** The instruction, CONTRACT and `task.yaml` agree, and the CONTRACT resolves the miniF2F question explicitly: the shipped file may be used for anything, and every other miniF2F copy is banned (`environment/validation/CONTRACT.md:3`). The metric is pooled macro F1 over the two classes (`tests/task/validate.py:78-94`). A failed request counts as the wrong verdict, not a dropped item (`validate.py:72-75`). Both are correct for a non-per-item metric.
- **The held-out pool mix is undisclosed and differs.** Validation statements are verbatim public problems, 50% miniF2F-test / 25% Workbook / 25% Pset (`tests/task/pipeline/statements.py:239`). Held-out statements are numeric or renamed variants drawn 45% Workbook / 45% Pset / 10% FormalMATH, with no miniF2F (`statements.py:240`). The public SCHEMA says only "private variants of public statements" (`pipeline/build_data.py:76-77`). Thresholds tuned on the shipped file transfer poorly (Gemini cnnjfd: 0.81 locally, 0.617 held-out).
- **The reviewer is looser than the prompt on rules.** The prompt says "not hand-written rules" (`instruction.md:3`). The reviewer requires only that rules not be "the source of the prediction" (`tests/task/review.py:20-23`), so hand-written detectors may feed a learned head. This is where Gemini cnnjfd's grey area comes from.
- **Stateless is enforced only by review.** SCHEMA tells agents every theorem has equally many compiling and non-compiling attempts (`pipeline/build_data.py:58`), so grouping requests by theorem would pay well. Only `review.py:34-38` forbids it. No trial tried.
- **Anchors are sensible.** 0 = macro F1 0.5, a fair coin (analytic); 1 = perfect (`tests/task/task.yaml:38-44`). Constant answers score 1/3 and clamp to 0 (`validate.py:10-11`). Below-chance classifiers also clamp to 0: Muse 57iczy's raw 0.397 would be about 0.60 inverted. Organizer baselines exist as code (`pipeline/baselines/`) but have no recorded results. Observed range: 0-57.9.
- **Noise.** There are 3,540 attempts on 295 theorems (12 each). One SE is about 1.4 points unclustered and about 2 points with theorem clustering, after the x2 rescale. The $10 Opus/Astra tie (37.55 vs 37.51) is well inside that.
- **The gate is faithfully self-checked.** The 600 s whole-batch gate is all-or-nothing (`tests/task/verifier.py:75-76`). The self-check sends a full 3,540-request batch of distinct public copies at concurrency 64 and counts the first request too (`verifier.py:114-181`). The only gap is that public file lengths follow the miniF2F-heavy mix (suspected).
- **Budget helps.** The 19-model means are 17.4 / 19.2 / 22.7, and Opus rises 37.5 / 45.3 / 57.5 with $168 spent on self-labelled data. $10 is enough for about 40 (Sonnet 41.8).
- **Neutrality.** No judge. The held-out attempts come from five open provers (`pipeline/generate.py:19-25`), and classifiers built on the same families (Goedel-Prover-V2-8B) may gain from familiarity. Every harness can do this, and the non-specialist rule allows it (`review.py:78-91`).
- **Reference solution.** It is the smoke fixture, which always answers `{"valid": false}` (`solution/server.py:76-79`), scores macro F1 1/3 and gets reward 0. Solvability is shown only by the trials.

**Fairness verdict: minor issues.** The metric, floor and gates are sound and self-checkable. But the held-out pool mix differs from the shipped file without disclosure, the rules on hand-written features and statelessness rest on reviewer judgment, and one SE of about 2 points ties the $10 winners.
