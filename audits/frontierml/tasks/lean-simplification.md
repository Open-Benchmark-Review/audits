# Math Proof Simplification (lean-simplification)

## The task

The agent serves `POST /simplify`. It receives a Lean 4 theorem and a proof, and must return a shorter proof that still checks under Lean v4.15.0 and Mathlib.

- **Limits:** batches of 8 requests, 60 s per batch, on one H100 with 8 CPUs. Lean may run at inference time.
- **Data:** 55 public examples. The held-out set has 354 proofs.
- **Sources:** the held-out statements come from AI-MO/minif2f_test, Lean Workbook, Goedel-Pset-v1 and FormalMATH. The proofs are the shortest organizer-generated proof per statement. Statements that a fixed one-tactic automation already solves were dropped (`tests/task/pipeline/build_data.py:27-34, 129`).
- **Rules:**
  - Do not train or select on any public validation or test split.
  - Do not ship a stored table of proofs keyed by theorem.

## How scoring works

- **Metric:** score = 100 x mean of `max(0, 1 - new_tokens/original_tokens)`. A proof that fails the sandboxed kernel checker, or is not shorter, scores 0. There is no normalization.
- **Noise:** standard errors are about 1.4 points.
- **Selfcheck:** it never runs Lean, so agents get no official score before grading.
- **Reviewer rules** (`tests/task/review.py`):
  - Provenance: "the shipped public examples in /task/public are fine" (line 17).
  - No proof lookup.
  - Actual inference path.

## Results

| Model | $10 | $50 | $200 |
|---|---|---|---|
| Claude Opus 5.5 | **33.9** (10kash) | 29.4 (348kgu) | **40.5** (1g91nm) |
| Claude Fable 5.1 | 21.4 (vb4un4) | **29.8** (5l3hxm) | 25.5 (626t6y) |
| GPT-6 Astra | 21.5 (1qz35o) | 28.0 (4d7hxi) | 24.3 (30f11k) |
| Gemini 4 Argon | 23.7 (1iui1v) | 23.0 (ha33es) | 25.5 (61biwu) |
| DeepSeek V4.1 Flash | 27.0 (teia0r) | 27.1 (417mxo) | 14.7 (4hoy6u) |
| Muse Wonder | 11.4 (3gdrrt) | 6.7 (2dcyfg) | 3.3 (138qky) |

All 18 trials passed review. My verdict agrees with the grader on all 18: 16 engineering, 1 no_gain (Muse 138qky), 0 violations.

## What the models did

Every submission is a generate-and-verify loop. It builds Lean-checked edits of the input proof (one-token closers, deleting steps or `have`s, pruning `nlinarith` hint lists, delta-debugging). Most also add samples from a pretrained prover served with vLLM.

- **Opus** built the strongest search engines and measured them on dev pools from training corpora, not on the public examples. 1g91nm at [23]: "pull a dev set from public training corpora, avoiding miniF2F since that's the source of these statements".
  - 10kash wrote a custom in-Lean `probe%` tactic that tests many edits from a single elaboration.
  - 1g91nm found that `bound` alone solves 183 of 700 dev problems [61].
  - Models: DeepSeek-Prover-V2-7B (10kash, 1g91nm) and Goedel-Prover-SFT (348kgu).
- **Fable, Astra and Muse** used Goedel or DeepSeek provers with similar searches.
- **Gemini** LoRA fine-tuned a prover on Lean-verified simplification pairs from public training splits.
- **DeepSeek** shipped pure search with no model and almost no wallet spend.

## Key findings

1. **No grading errors.** All four provenance and lookup checks are sound on every trial.
   - Nobody shipped proof data.
   - No trial accessed the HF tasks dataset, the benchmark repo or frontierml.org.
   - miniF2F appears only in HF search listings and decontamination filters. Gemini ha33es fetched miniF2F, ProofNet and Putnam metadata, then deleted it. DeepSeek teia0r cloned miniF2F-lean4 at [34] and only grepped it for overlap with validation [35]-[36].
2. **Using the public examples is ambiguous to agents but allowed by the grader.**
   - The prompt's "validation split of any public dataset" rule led cautious agents (Opus, Gemini) to avoid tuning on `validation.jsonl`.
   - Others tuned on it openly: Fable vb4un4 at [95]/[138] ("Run 2 scored 0.290, up from 0.266"), and Muse 3gdrrt (the reviewer says "tuned only against the shipped public examples ... which the policy allows").
   - DeepSeek teia0r admits at [185] "I've already been measuring on validation and choosing transforms partly based on it", yet its DATA.md [263] says validation was "Used only to run the server end to end". The documentation is inaccurate, but this is not a violation under review.py:16-17.
3. **The held-out set overlaps the provers' home benchmark.** It draws on miniF2F-test, the benchmark DeepSeek-Prover-V2 and Goedel-Prover-V2 were tuned and reported on. review.py:24-25 allows such "incidental exposure", but the score partly measures off-the-shelf prover strength.
4. **The gap between validation and held-out is invisible.**
   - Muse 138qky measured 0.115 on validation with its own checker [268] but scored 0.0325.
   - Three trials returned proofs that failed the official checker (valid_fraction 0.90-0.99).
   - Because the selfcheck does not run Lean, agents cannot detect either problem.

## Epoch scoring item: **pass**

I found no false positive, false negative or infrastructure zero.

- **$10 and $200:** Opus wins clearly.
- **$50:** Fable (29.77) leads Opus (29.42) and Astra (27.98) by less than the standard error. This is a statistical tie, not a scoring defect.

## Task design

- **Spec is mostly consistent, and the scorer is public.** The instruction, CONTRACT and `task.yaml` agree. The validator and the token metric shipped to the agent are byte-identical to the grader's (`environment/validation/validate.py` and `simplification_metric.py` diff clean against `tests/task/`). The checker parses the proof as a term, replays it into the original environment, compares types and whitelists axioms (`tests/task/checker/ProofCheck.lean:27-59`). I found no metric bug. Unchanged proofs and failed requests both score 0 (`tests/task/validate.py:43-47, 68-75`).
- **The reference checker cannot be run where the agent is told to run it.** CONTRACT.md:15 says to "run it and pass `--checker-url`". The checker needs Docker (`tests/task/checker/README.md:44-48`: "Do not run the service in the candidate sandbox"), and the sandbox has none (Muse 3gdrrt: "docker: not found"). The self-check also runs no Lean (`tests/task/verifier.py:161`). So no agent gets an official validity check before grading. This is how three trials shipped invalid proofs and Muse 138qky dropped from 0.115 to 0.0325.
- **The public-example rule contradicts the prompt.** The prompt bans selecting on any public benchmark's validation or test split (`instruction.md:7`). The reviewer explicitly allows the shipped examples (`tests/task/review.py:16-17`), and in the shared pipeline these are half miniF2F-test. lean-validity spells out this exception in its CONTRACT; this task does not. Cautious agents (Opus, Gemini) lost the tuning signal that others used.
- **The held-out set is probably shifted from the public one (suspected).** `pipeline/build_data.py:85-119, 179` reads a lean-validity-style source run and sends upstream "validation" to public and "heldout" plus organizer "train" to private. In lean-validity's pipeline, validation is 50% miniF2F / 25% Workbook / 25% Pset, used verbatim. Held-out and train are numeric or renamed variants of Workbook, Pset and FormalMATH, with no miniF2F (`lean-validity/tests/task/pipeline/statements.py:239-240`). If that is right, finding 3 above (held-out "draws on miniF2F-test") is overstated. The data date from 2026-09-24 (`pipeline/validation_results.json:3`), before lean-validity's 2026-09-26 fix that removed held-out statements (26% of them) found verbatim in public pools. This build has no verbatim-public audit.
- **Noise.** One SE is about 1.5 points (Opus 1g91nm reports standard_error 0.0149 on 354 proofs). The $50 Fable/Opus/Astra spread is within 1.3 SE.
- **No measured anchors.** There is no `score_normalization` block (`tests/task/task.yaml:24`), so the reward is the raw reduction and the unchanged proof is the only floor. The data drop only statements solved by a single fixed `first | ... | exact?` closer (`pipeline/build_data.py:27-28, 128-129`), so cheap closers and model-free search still reach about 27 (DeepSeek teia0r at $0.25). The ceiling of 100 is unreachable (an empty proof scores 0). Observed range: 0-40.5.
- **The gate is all-or-nothing but well self-checked.** One late batch of 8 fails the run (`tests/task/validate.py:151-152`). The self-check times 7 of the 45 windows, the first one cold (`tests/task/verifier.py:23`). Search is anytime and wall-clock bound, so scores are not exactly reproducible across hardware. No trial lost its run this way.
- **Budget hardly matters.** The 19-model means are 15.8 / 15.4 / 14.6. Lean search runs on the grader's H100 box and 8 CPUs at no wallet cost, and only Opus's $200 run gains clearly.
- **Neutrality.** No judge, and the lexer is model-agnostic. The organizer's only baseline is a GPT-6 Astra API probe (0.243 on public; `pipeline/validation_results.json:27-38`), which is not used in grading. One lexer quirk: dot chains count as one token (`tests/task/simplification_metric.py:88`). It is the same for everyone.
- **Reference solution.** It is the smoke fixture, which returns the input proof (`solution/server.py:80-81`) and scores 0. The organizer marked the task `"release_ready": false` with no permitted baseline or $50 pilot (`pipeline/validation_results.json:14-17`).

**Fairness verdict: minor issues.** The kernel check and the metric are sound and public. But agents cannot run the official checker, the public-example rule is contradictory, the held-out set is probably shifted from the public one, and a no-ML search reaches two thirds of the top score, so the task separates Lean search engineering more than ML or budget use.
