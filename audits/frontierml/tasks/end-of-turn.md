# Voice endpointing (end-of-turn)

## The task

- **Goal:** serve `POST /predict`, which takes both speakers' 48 kHz audio of a 10–15 minute conversation and returns a causal per-frame probability that each speaker's turn just ended.
- **Data given:** 8 labelled conversations, usable freely.
- **Rules:**
  - Each probability may depend only on audio through the end of its frame.
  - No validation or test splits of public datasets.
  - No other copy of this task's conversations or labels.

## How scoring works

- **Metric:** recall of end-of-turn windows at the threshold where at most 5% of mid-turn pause windows fire, pooled over 30 held-out conversations.
  - The Opus 20rpqt grade shows 1,523 positive and 819 pause windows.
  - Rescaled so that the shipped silence heuristic (0.655) = 0 and perfect recall = 100, clamped (`tests/task/task.yaml:46-48`).
  - The binomial SE is about 2.4 score points.
- **Held-out set:** the other 30 conversations of the public TurnBench dev release (`tests/task/review.py:30-37`). That release is on HF as mundo-ai/turn-benchmark-dev (gated "auto") and as an ungated JSALT derivative.
- **Causality:** checked only by the reviewer, never by the grader.

## Results

| Model | $10 | $50 | $200 |
|---|---|---|---|
| Claude Opus 5.5 | **74.7** | **68.8** | 55.8 |
| Gemini 4 Argon | 53.2 | 65.2 | **64.8** |
| GPT-6 Astra | 50.5 | 62.9 | 60.4 |
| Claude Fable 5.1 | 65.0 | 0 (fail) | 50.7 |
| DeepSeek V4.1 Flash | 0 (fail) | 42.3 | 0 (fail) |
| Muse Wonder | 0 (fail) | 5.2 | 0 (fail) |

Five trials failed review.

## What each model did

- **Opus:** frozen Mimi features plus causal transformers.
  - $10 and $200: pretrained on Seamless Interaction train.
  - $50: found TurnBench by web search ([16]) and trained on its official training split, otoSpeech-104h, with labels from TurnBench's own gold.py.
- **Gemini:** fused frozen public turn-taking models (VAP variants, SmartTurn, DualTurn) with heads trained on Switchboard/otoSpeech DualTurn train shards, or on the 8 conversations only ($50).
- **Astra:** small heads on frozen Silero, VAP and SmartTurn features, fitted on the 8 conversations in under an hour.
- **Fable:**
  - $10: causal WavLM on AMI train meetings.
  - $50: VAP fine-tuned on all of AMI.
  - $200: fine-tuned DualTurn checkpoints.
- **DeepSeek:** all three found TurnBench. The runs used a public VAP checkpoint or a from-scratch model on otoSpeech-104h.
- **Muse:** gradient boosting, or Mimi + GRU/TCN on Switchboard.

## Key findings

1. **Missed violation (false positive): DeepSeek 64qbza, 42.3.**
   - Inference runs in 60 s windows with a final window anchored to the end of the file: `tail = ((T100 - win) // STRIDE) * STRIDE ... starts.append(tail)` ([43]). It overwrites the last ≤30 s of every conversation.
   - The served path uses it ([218]).
   - This is the same pattern for which the reviewer failed Fable 4dhosx: "Where that last window starts depends on the total file length". Here the reviewer called it causal.
   - Zeroing it changes nothing at $50.
2. **Wrong violation (false negative): DeepSeek 61zfoj.**
   - It was zeroed because `DEV = {20,21,22,38,...,172}` appears in its download script.
   - That list is the public `turnbench/splits/dev.txt` from GitHub ([17]). It is used only to *exclude* same-numbered otoSpeech folders ([201]).
   - The agent listed the dev parquet sizes but decided not to download them ([23]-[24]).
   - The zero follows the literal policy (`review.py:38-41`), not the prompt.
   - Its LOO estimate of 0.735 (~23 points) would not beat Opus 74.7.
3. **Correct fails.**
   - **Fable 4dhosx:** VAP fine-tuned on AMI test meetings EN2002/ES2004/IS1009/TS3003 ([50], [108]: no split filter). Fable 5xshq9 excluded those meetings and passed.
   - **Muse 11g1u8 and 2ad6ya:** whole-file FFT resampling in the served path ([122], [71]), named as a violation in `review.py:16-20`.
   - **DeepSeek usg3o5:** tried to read the dev release ([53]-[55], all failed) and shipped `snapshot_download("mundo-ai/turn-benchmark-dev")` in download.sh.
4. **The benchmark is discoverable.**
   - Four trials identified TurnBench from the label field names.
   - Its training split is legitimately allowed and in-distribution.
   - Protection of the dev release rests on the reviewer alone.
5. **One open risk for the $200 winner.**
   - Gemini gg161j (and Fable 4ldtkv) rely on DualTurn data and checkpoints derived from otoSpeech-full-duplex-280h, from the same recording project as TurnBench ([34] in gg161j).
   - Whether that release contains the held-out conversations is neither checked by the policy nor checkable here.

## Epoch scoring item: **pass**

Both defects found (DeepSeek 64qbza's missed violation and DeepSeek 61zfoj's wrong zero) leave the winners unchanged: Opus at $10 and $50, Gemini at $200. The pass is conditional on the unverified DualTurn/otoSpeech-280h overlap question.

## Lead-auditor adjudication

- DeepSeek 64qbza is recorded as `unclear`, not as a confirmed false positive. Its served path does anchor a last
  window to the end of the file, the pattern cited against Fable 4dhosx. But Fable's zero also rests on a separate,
  clear provenance violation (fine-tuning on AMI test meetings), and inside each window 64qbza's model is causal, so its
  outputs depend on file length rather than on future audio. The reviewer described the same pattern differently in the
  two trials; that inconsistency is the finding.
- DeepSeek 61zfoj is kept as a probable false negative. Its ID set is the public `splits/dev.txt`, used only to
  exclude conversations; at [23] it listed the dev release's files through the HF API and did not download them.

## Task design

- **Causality is never tested by the grader.** The server gets whole files, and `verifier.py:63-69` is one full-file pass plus the review receipt. Causality (`CONTRACT.md:7`, `review.py:11-13`) is judged only by the LLM reviewer, which split on the same end-anchored-window pattern (Fable 4dhosx failed, DeepSeek 64qbza passed). A prefix-truncation replay in the grader would remove the judgement call.
- **Metric matches the prompt.** Window maxima, a pooled threshold sweep and recall at FPR ≤ 0.05 (`turn_taking.py:93-150, 255-256`). It is deterministic and needs no judge. A positive window with no scoreable frames counts as a miss (`turn_taking.py:85-87`), a small fixed cap on the ceiling.
- **Anchors.** 0 = raw recall 0.655 of a training-free two-channel silence heuristic, 1 = perfect recall (`task.yaml:46-48`). Neither the split nor the scorer revision of the floor measurement is stated, and the heuristic is not in `/task`. Because the 1 s late window (`turn_taking.py:43`) credits reacting to the partner's onset, the floor is high. Clipping puts up to 9 review-passing trials at the same 0 as failures. The best raw recall is 0.913 (74.7 points); the top quarter of the scale is probably unreachable.
- **Latency is not scored.** The title promises replies "promptly" (`task.yaml:2`), but latency inside the 1 s window is only reported (`turn_taking.py:265-266`).
- **Held-out set.** 30 of the 38 conversations of the public TurnBench dev release (`end_of_turn.py:3, 18-22`). Agents are told only not to use "any other copy or derivative of this task's conversations" (`CONTRACT.md:3`), without the source. Identifying TurnBench also unlocks its permitted, in-distribution training split.
- **Review-only rules.** Any held-out id in any file fails the run, even in an exclusion list (`review.py:38-41`). The 5 ms resampler tolerance and the FFT-resampling ban (`review.py:16-20`) exist only in the review policy. These rules caused 3 of the 12 review zeros (DeepSeek 61zfoj, Muse 11g1u8 and 2ad6ya).
- **Noise.** Every non-zero score is k/1523 positives, so one positive is worth 0.19 points. With 819 pauses (about 41 allowed false positives) and 30 clustered conversations, I estimate the SE at about 4 points, above the 2.4-point binomial figure.
- **Speed gate is fair and well mirrored.** The 3x real-time gate is charged on a server-side clock that excludes the grader's ~100 MB transfers (`validate.py:46-74`). The self-check projects it from two near-mean-length public conversations with the cold start counted once (`verifier.py:29-35, 72-110`).
- **Feasible at $10, flat or negative scaling.** Opus 74.7 at $10 is the best of any wallet; more money did not help any model.
- **Reference solution.** `solution/` returns all-zero streams and would score 0. The floor heuristic would fail the "learned_causal_model" check.
- **Fairness verdict: minor issues.** The scoring is sound and the speed gate is fair. The core causality rule and the held-out exclusion rest entirely on an LLM reviewer that applied them inconsistently, and noise is about 4 points.
