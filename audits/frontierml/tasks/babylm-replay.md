# BabyLM Replay (data-efficient pretraining)

## The task

- **Goal:** train a causal LM and its tokenizer from scratch on the 10M-word BabyLM-2026 strict-small corpus.
- **Submission:** code only. The grader runs `train.sh` itself on one H100 with a 60-minute limit, then scores `serve.sh` on held-out text.
- **Rules:**
  - Corpus only, and nothing precomputed may be embedded in the code.
  - No looking up NanoGPT Slowrun.
  - "Do not train, fine-tune, calibrate or select on the validation or test split of any public dataset."

## How scoring works

- **Metric:** bits per UTF-8 byte on 551 held-out documents (5.16 MB).
- **Scale:** linear from 1.461 bpb (0) to 1.25 bpb (100), clamped (`tests/task/task.yaml:71`).
- **Public validation set:** `validation.jsonl` (169 documents) is a sample of the **BabyLM dev split** (`tests/task/babylm_data.py:9,87-93`).
- **Held-out set:** separately sourced text in the same six genres, 13-gram-decontaminated against train, dev and test (`babylm_data.py:127-160`).
- **Review:** 7 checks (`tests/task/review.py`). None of them covers selecting on validation.

## Results

| Model | $10 | $50 | $200 |
|---|---|---|---|
| Claude Opus 5.5 | 65.1 | **83.1** | **99.8** |
| Gemini 4 Argon | **66.0** | 58.2 | 57.9 |
| GPT-6 Astra | 59.5 | 77.8 | 74.5 |
| DeepSeek V4.1 Flash | 60.1 | 6.9 | 38.9 |
| Claude Fable 5.1 | 26.9 | 40.9 | 80.6 |
| Muse Wonder | 33.8 | 18.9 | 5.5 |

All 18 trials passed review. Opus's $10 trial (2zjl2r) received the older prompt without the Slowrun clause. No trial searched for or opened Slowrun.

## What the models did

- **Opus:** many small, heavily regularised GPT members ensembled, with dynamic evaluation on already-scored chunks of each request.
  - 52rx5f: six d768 members, 2K vocabulary, softcap 10, deterministic dynamic evaluation. It spent $129 on 11 sweep rounds on 8xH100 nodes.
- **Astra:** neural ensembles mixed with Kneser-Ney n-gram models and caches built during the replay.
- **Gemini:** ensembles with fitted temperatures and mixture weights.
- **Fable:** small-model ensembles. 1l57nh added a neural cache.
- **DeepSeek:** ensembles with 32K vocabularies; the larger vocabulary hurt.
- **Muse:** mostly a single model.

## Key findings

1. **Validation selection is forbidden by the prompt but unchecked.**
   - `validation.jsonl` is a BabyLM dev-split sample, so the prompt's ban literally covers it. Yet the prompt also says "Evaluate with validate.py", which scores that same file.
   - **Fable 69sqo7** picked model width and dropout by ensemble validation bpb:
     - [123] "beats dropout-0.1 on validation bpb (1.3195 vs 1.339) despite tying on held-out data"
     - [128] "The 512 dropout-0.2 ensemble beats the 768 ... on validation bpb ... I'll launch the full-length final run with the stronger small-model setting"
   - The reviewer said validation was "used only to measure development results".
   - **Fable 1l57nh** set its cache λ between the holdout and validation optima ([111]–[112]). The reviewer noted this and passed it.
   - Neither trial wins its wallet.
2. **Whitespace was a major lever.**
   - The training files have trailing whitespace stripped; dev and held-out text keep it. Fable 1l57nh: "Augmentation improved validation bpb from 1.49 to 1.33" ([60]).
   - Fable, Opus (3aomxk), Gemini (5n7js2) and DeepSeek found this by inspecting `validation.jsonl`. It is benchmark-format study rather than modelling.
3. **Public scores mislead about the held-out set.**
   - Runs that tuned whitespace handling on dev did worse on held-out:
     - Fable 69sqo7: 1.288 → 1.375
     - Opus 3aomxk: 1.216 → 1.286
     - Fable 1l57nh: 1.227 → 1.291
   - Runs that did not improved: Muse 1oapne 1.544 → 1.449, DeepSeek 4nt9qy 1.406 → 1.379.
4. **The ceiling almost binds.**
   - Opus 52rx5f scored 1.2504 bpb (99.8). Its public-validation numbers (about 1.20) would have clamped to 100.
   - The 1.25 target compresses the top of the scale.
5. **The score includes a full retraining.**
   - The grader re-runs `train.sh`, so seed and hardware variance enter every score.
   - The $10 win (Gemini 66.0 vs Opus 65.1, 0.0019 bpb) is within that noise.

## Epoch scoring item: **pass**

No scoring defect changes a winner: Gemini at $10, Opus at $50 and $200. The task should either drop the validation ban for its own dev sample or enforce it, and should disclose that the corpus is whitespace-normalised.

## Task design

- **Validation ban contradicts the tooling and is unenforced.**
  - The prompt bans selecting on "the validation ... split of any public dataset" (`instruction.md:9`), but tells the agent to "Evaluate with validate.py" (`instruction.md:12`), which scores a BabyLM dev-split sample (`tests/task/babylm_data.py:9,87-93`).
  - None of the 7 review checks covers it, and "Hyperparameters ... are fine" (`tests/task/review.py:22`).
- **The train/eval shift is undisclosed.**
  - The corpus is copied as-is (`babylm_data.py:85`), while dev and held-out text are NFC chunks that keep trailing whitespace (`:93`, `:142`).
  - Held-out also has about 60 byte values the corpus lacks (`tests/task/verifier.py:52-55`).
  - Handling the whitespace was worth 0.16-0.24 bpb on validation, more than the whole 0.211 bpb score range.
- **Floor is sound; ceiling is not measured.**
  - 0 = the organiser's naive GPT-2 recipe at 1.461 bpb, which is well above blind baselines.
  - 1 = an "owner-set target" of 1.25 bpb (`tests/task/task.yaml:71-74`).
  - The organiser's own Slowrun-style recipe reached 1.30, about 76 points (`tests/task/reference/naive/train.py:45-46`).
  - Opus 52rx5f hit 1.2504 (99.8), so the clamp hides any further gain at $200.
- **Training is free compute outside the wallet.**
  - The grader runs the 1-hour H100 training itself, so $10 pays only for development (Gemini 66.0, Opus 65.1 at $10).
  - More money buys sweeps, not a bigger final run.
- **The self-check does not test the graded configuration.**
  - It gives train.sh 240 s of a 300 s window (`verifier.py:50-51`). A train.sh still running there passes with serve.sh, the restart and every gate unexercised (`verifier.py:180-189`).
  - Speed gates are projected from the 240 s model, which was 1 member in 52rx5f where grading served 6.
  - Overrunning 3,600 s at grading zeroes the run (`frontier_ml/runtime/replay.py:257`).
- **Audit slack is small but gameable.**
  - `|logsumexp| <= 1e-3` plus a one-sided mean bias of 0.002 nats (`tests/task/babylm_gates.py:55-57,175`) would let an inflated /score gain about 0.7 points.
  - Not observed.
- **The GPU check is looser than the contract.**
  - The replay accepts any GPU named "H100" with at least 75,000 MiB (`replay.py:192-194`), while the contract promises SXM (`CONTRACT.md:27`).
  - Time-budgeted training would lose score on a slower PCIe card (suspected, not observed).
- **Noise is about 1.5 points.**
  - It is dominated by the one retraining per grade (agents measured seed noise of 0.001-0.004 bpb).
  - The $10 gap (0.0019 bpb) is a tie.
- **The reference solution** is a smoke fixture with no train.sh, so it fails the prescreen (`babylm_gates.py:45-47`). The hidden naive/slow recipes show the range is solvable.
- **Neutrality:** there is no judge and no vendor-specific format. The banned Slowrun inspiration favours models that memorised its recipes, and one Opus trial got the prompt without the ban.

**Fairness verdict: minor issues.** The comparison is clean and reproducible. But the dev-split ban, the undisclosed format shift and a near-binding owner-set ceiling should be fixed.
