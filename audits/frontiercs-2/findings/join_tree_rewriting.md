join_tree_rewriting: FN (CONFIRMED), IMPOSSIBLE (UNCONFIRMED), MINOR (CONFIRMED). Affected runs: all 16 scored runs (0/17 PASS; ds = agent OOM, no submission).

## How it's scored
- 39 queries in final (20 dev + 19 hidden). Each query needs (a) the exact original result and (b) a fresh candidate median latency strictly below the paired reference median: `latency_pass = not identical and candidate < reference` (judge/query_measurements.py:128). Ten observations per role (A-B-B-A block, 5 reps).
- Byte-identical lowered JSON fails automatically. Conjunction over all 39 queries (query_measurements.py:144).
- The continuous score (`smooth_score(binary/candidate)`) is separate. Reference score ~10 (n=16, sd 0.32).

## P(reference passes vs itself)
0. A byte-identical plan fails by rule. Any byte-different plan of equal speed would need 39 coin flips (~0.6^39).

## Findings
1. **FN / near-unreachable bar (CONFIRMED).** I extracted per-query medians from every train evidence file in all 16 traces: 638 train calls, 20 dev queries each.
   - No train call by any model ever cleared all 20 dev queries. The best was 15/20 (gemini, sol, gemini-agy).
   - Several queries are "flat": the reference's own speedup over the binary plan is about 1.0 (dev/1 1.01, dev/8 0.99, dev/9 1.00). Rewriting hardly matters there, so any plan sits at parity and wins by noise or loses.
     - dev/1: 36/636 passes; the 10th-percentile candidate/reference ratio over 353 non-identical tries is 1.000 (median 1.089).
     - dev/9: 122/610 passes, p10 0.998.
     - dev/14: 130/636 passes, p10 0.995.
   - Final queries show the same pattern: final/11 and final/16 were beaten by 0/16 formal runs, final/1 and dev/8 by 2/16, final/8 and dev/1 by 3/16.
   - With roughly 5 or more parity queries in the 39, even a perfect policy is capped near 0.6^5 ≈ 8%. Any query where the reference's rewrite is actually optimal (for example final/16, which has only 12 distinct lowerings) caps it at 0.
   - Correct, genuinely better work fails: k31, gemini, k27 and gemini-agy beat the reference's continuous score by 1.6–2.4 points with 39/39 exact results, but cleared at most 27/39 latency cells.
2. **IMPOSSIBLE (UNCONFIRMED).** Using the shipped binary_plan package (script $SCRATCH/jtr_enum.py), every ≤8-leaf query has 10 to 70,560 distinct valid lowerings, so the reference is never the only valid plan. I could not run the engine (join_runner is an LFS stub), so I can't prove that no lowering beats the reference on final/11 or final/16. 0/16 runs did, and no model ever beat dev/1 systematically.
3. **Noise / position bias (MINOR, CONFIRMED).** Over 1,152 byte-identical (auto-fail) query measurements, candidate/reference median ratios have sd 2.1%, and the candidate position wins 65.5% of the time (dev/12: 97%). This bias helps candidates, so it can't produce false negatives. A byte-different but execution-equivalent plan would still need about 0.65^39, so there is no FP risk either.
4. **Stale judge readme (MINOR, CONFIRMED).** judge/readme describes a different scoring (a "twelve-query suite", `100*log10(A_q*R_q)`, fourteen observations, whole-point rounding). The agent-visible agent-base/frontier/task/repo/README.md matches the evaluator, so this has no effect on runs.

## Passing runs checked
None (0 PASS). The near-misses gemini (66/78), gemini-agy (65), sol (65) and k27 (62) all have 39/39 exact results, so their failures are latency-only.

## Notes
- Statement completeness is fine: the strict per-query rule and the byte-identical rule are stated in repo/README.md ("Scoring and reference PASS").
- No scorer change across runs: only the initial commit; reference score is stable at 9.56–10.76 from Oct 12 to Oct 26.
- Bottom line: the 0/17 result reflects a bar that is essentially unattainable (a strict per-query latency win on 39 queries, several of which are at parity), not a lack of capability.
