# DPO preference alignment (Zephyr/Mistral 7B → IFEval): task review

**Verdict: `MINOR`. Confirmed, not counted toward the threshold.**
Structured data: [`../data/task_reviews/dpo_preference_alignment.json`](../data/task_reviews/dpo_preference_alignment.json).

## Spec

- **Starting point:** a frozen merged Zephyr-SFT policy, trained with the shipped QLoRA sigmoid DPO (β 0.01, 772 steps) on UltraFeedback.
- **Proxy:** IFEval strict prompt-level accuracy on 128 visible rows.
- **Final:** the same metric on 413 rows.
- **Row split:** all tiers are cut from the 541 IFEval rows in sha256(key) order:
  - rows 0–127 are retired and scored by neither tier;
  - the final is rows 128–540;
  - the proxy is rows 128–255, so it is a prefix of the final (`grade.py:23-26,193-211`);
  - the 285 rows from 256 on are held out.
- **References on the case pages:** fixed start 164/413 = 0.397, shipped recipe 210/413 = 0.508.
- **Paper anchors:** baseline 0.424, uninformative 0, optimum 1.

## Findings

1. **Overlap is declared, and the held-out rows are not exposed.**
   - 31% of the final (the proxy) is visible during exploration. Agents are told this (`instruction.md:81`), and the final evaluator reports score(P), score(F\P) and the gap between them as diagnostics (`final_eval.py:138-173`).
   - The other 285 rows are mounted only in the score phase (`declaration.py:87-89,102-115,184`).
   - The split rule can be read in `grade.py`, but the held-out text cannot. Case pages report literal searches of trajectories and patches for the held-out rows, with zero matches.
   - IFEval is public and the agents know its instruction families, but there is no network access (`task.toml:32`).
2. **The scorer matches the instruction.**
   - Greedy decoding, chat template, max_new_tokens 1280, strict prompt-level accuracy.
   - The lighteval IFEval scorer is patched: regex tokenizers replace nltk, and a letter-frequency fix is applied (`grade.py:102-128,258-319`). Numbers are therefore slightly off the official IFEval, but consistent within the benchmark.
   - There is no universal format hack, because constraints conflict across rows.
3. **Teaching to the test, which the rules allow.** The two top cells, Opus medium (0.622) and Opus high (0.615), synthesise 20–24 families of IFEval-style constraint pairs from UltraFeedback, labelled by checkers the agents wrote. The rules permit this (`instruction.md:83`), and it generalises to the held-out complement (Opus high scores 173/285 = 0.607). We class both cells `grey_area` because they specialise to the evaluation distribution.
4. **The shipped reference is not reproduced.**
   - The instruction and every case page give the shipped recipe as 210/413 (`instruction.md:93-95`).
   - Four formal replays of the unchanged recipe score far lower: 165/413 (Sol none), and 161, 167 and 181/413 (Terra xhigh's three branches).
   - The likely cause is stale configuration: `declaration.py:19,84` say the shipped default uses 8,192 rows, while `run.sh:33` uses 61,135.
   - The paper's 0.424 anchor is close to the replay mean of 0.408, so σ is probably calibrated correctly. Agents and case pages, however, were given a reference about 42 items too high.
   - If σ had been anchored on 0.508, the task mean would be 0.116 instead of 0.187, and 7 cells would beat the baseline instead of 22.
5. **Noise.**
   - The standard error is about 0.024 at n = 413.
   - Same-seed replicates differ by 6 items, and changing the seed moves a score by up to 20 items.
   - Only the two Opus constraint-data cells separate clearly from the pack. Orderings among the cells scoring 0.43–0.50 are noise.
6. **Checkpoint selection.**
   - In 16 of 29 cells, the reported checkpoint is not the last one.
   - Task mean σ is 0.187 under best-of-3 and 0.173 under the last checkpoint, an average of about 6 items selected on the scored set.
   - One cell (Opus low) flips across σ = 0.1.
   - Terra xhigh turns best-of-3 into a seed lottery over three shipped-recipe replicates.

## Cells

| Classification | Count |
|---|---|
| `engineering` (DPO + SFT/NLL, filtering, β/learning-rate/schedule, length-bias token weighting) | 19 |
| `no_gain` | 7 |
| `grey_area` (Opus high and medium: IFEval-family synthetic constraint pairs; Terra xhigh: seed replicates under best-of-3) | 3 |

- **`false_positive` (1):** Terra xhigh. The recipe is unchanged, and best-of-3 over seed replicates lifts σ from about 0.093 to 0.122.
- **`unclear` (1):** Sol xhigh. Its credited best of 199/413 comes from an "orphan summary" that the page itself calls "official result not available". Without it the best would be 0.46.
- **No false negatives.**
- **The case pages disagree with our reading in 2 cells:** Sol none and Terra xhigh. Both pages keep 210/413 as the shipped reference although their own replays of that recipe score 161–181/413.
