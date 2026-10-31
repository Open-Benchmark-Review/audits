fast_kv_compaction: FN (CONFIRMED), FP-surface (UNCONFIRMED, unexploited), MINOR. Affected runs: all scored FAILs, opus most clearly (22/24 qa, 24/24 time and bytes).

Paths below are relative to `src/FrontierCS-2/tasks/frontier-cs-2.0-demo/problems/Machine Learning/fast_kv_compaction/`.

## How it's scored
- Final is 24 QuALITY articles: 12 public dev articles plus 12 hidden. Each article must pass all three checks (`judge/beat_spec.json`; `judge/gate.py:9`, `:37`, `:78`):
  - `qa_correct`: min over 3 repetitions >= median(reference captures) - max(1, ceil(0.05 N)). N is 13-20, so the tolerance is always 1.
  - time: median of 3 strictly < r x median reference time.
  - bytes: <= reference bytes (strictly < in bytes mode, TARGET_SIZE < 0.1).
- The reference comes from 3 frozen seeded captures (`judge/targets/manifest.json`) and is never re-run.
- Score note (per_task json): the continuous score was rescored post hoc on an absolute scale, `87.5 x mean accuracy = 60.63` for the reference. Verdicts are unchanged, so there is no PASS/FAIL effect.

## P(reference passes vs itself)
- **Time:** strict `<` against the median on 24 articles, so P ≈ 0 and there is no FP.
- **Accuracy alone, computed from the manifest:**
  - For each article, take the fraction of the 3 reference captures whose min-over-reps is >= median - 1. The product over 24 articles is **0.13**.
  - Resampling: pooling the 9 per-repetition values and drawing min-of-3 gives **0.17**.
  - 5 of 24 articles (22346, 22524, 22876, 23563, 30035) fail for 1 of 3 captures.
  - So the reference method, re-run unchanged, clears the accuracy gate only about 15% of the time.
- **Uncompressed (full) KV cache, the upper bound for any compaction:**
  - On article 30029 the single recorded value `uncompressed_correct = 14` is below the bar of 15 (median 16 - 1).
  - Articles 22102, 22579 and 31282 have uncompressed = bar exactly, and any min-of-3 drop fails them.
  - A lossless compactor would therefore very likely fail as well.

## Findings
1. **FN, CONFIRMED: the accuracy gate is dominated by QA noise.**
   - The bar sits 1 question below the reference median. The candidate's worst-of-3 must clear it on all 24 articles.
   - Reference per-repetition spread within one capture is up to 3 questions (e.g. 22073: [13,10,10]; 22876 captures 19/16/18).
   - P(the reference clears it) ≈ 0.13-0.17, and the uncompressed cache fails article 30029 on its recorded draw.
   - Every scored candidate passes time and bytes 24/24 and fails only qa_correct. opus fails just 2 of 24 articles, consistent with near-reference accuracy plus noise.
   - A compaction method equal to the reference in accuracy and faster passes about 15% of the time, and one equal to a full cache still fails often.
   - This is also why the task reads as "hardest" (FDI 103): the binding constraint is noise, not method quality.
2. **FP surface, UNCONFIRMED (not exploited): dev/final overlap with visible gold answers.**
   - The final suite contains the 12 public articles. The agent image ships them with questions and `gold_label` (`agent-base/frontier/task/repo/data/QuALITY.v1.0.1.htmlstripped.dev`, 12 articles, keys include `gold_label`).
   - Submitted `compaction/` code receives the article text (`agent-base/frontier/task/README.md:60-66`). It could recognise a public article and return a cache built from answer-bearing text, inflating 12 of 24 articles.
   - The hidden 12 still need to pass, so this alone cannot produce a PASS. No passing patch exists.
   - grep of the 14 downloaded patches: only qwen.patch reads the dev file (offline tuning helpers, score 0).
3. **Judge/infra (MINOR):** opus's own final verification raised `HarnessInfrastructureFailure` (failure_code evaluator_error). Its stored final was re-judged independently and scored 22/24 qa, so the FAIL stands and is not an infra artifact.
4. **Train budget:** 8 train calls and 18,000 agent GPU-s on an H100. Adequate. Dev feedback grades only the 12 public articles with a single repetition, so it understates the min-of-3 penalty agents will face.
5. **Statement:** the min-over-repetitions rule and the tolerance are disclosed (`agent-base/frontier/task/README.md` "How you are measured"). No hidden requirement was found.

## Passing runs checked
None (0/17).

## Notes
- Suggested fix: compare like with like. For example, use the mean over repetitions for both sides, or the reference's min-of-3 distribution, and size the tolerance from the measured capture spread.
