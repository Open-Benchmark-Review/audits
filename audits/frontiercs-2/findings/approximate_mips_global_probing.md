# approximate_mips_global_probing: MINOR + FN (UNCONFIRMED). Affected runs: possibly k3, glmf (time-only failures)

## How it's scored
- 48 final operating points (2 datasets x 2 query/hash splits x 3 c x 4 k).
- Per point: recall >= ref, ratio >= ref, verified candidates <= ref, and mean query time strictly < ref (`judge/evaluator.py:236-244`).
- Each point is measured once: one process per (dataset, split) for candidate, then reference, sequentially in a fixed order, not interleaved (`:225-233`).

## P(reference passes vs itself)
- A byte-identical patch gets reference := candidate, so the time comparison ties and fails (`:216,227-228`).
- A same-speed re-implementation needs 48 strict time wins: about 2^-48. P about 0.

## Findings
1. **MINOR / construct note.**
   - Three of the four gates allow equality, and the README fully specifies the reference's frontier and stop rule (p_tau=0.1, conservative rounding; `repo/README.md:44-66`).
   - So a decision-identical re-implementation with less per-probe overhead passes. 13/17 runs pass, with margins of only +0.7..+1.7 points.
   - This tests "the same algorithm, coded faster", not a better algorithm. That is disclosed and not egregious.
2. **MINOR:**
   - The candidate always runs before the reference within a trial (`:225-233`), so there is no order rotation and any order bias is systematic.
   - The final suite includes the dev split (split 0, same hash seed 314159) as 24 of its 48 points (`:26-27`).
3. **FN (UNCONFIRMED):**
   - k3 (score 52.13) and glmf (51.96) pass recall, ratio and candidates on 48/48 but miss query time on 3 and 2 points.
   - Many PASSes have lower scores (k27 51.71, ds1017 51.79).
   - With one timing sample per point and no tolerance, points where verification dominates the time give little real advantage, so a few flips are expected.

## Passing runs checked (13; spot-checked all via grep, read astra/sol/opus/terra in full)
- glm, astra, sol, muse, opus, k27, wonder, qwen, gemini, ds1017, gemini-agy, terra, k31: legit. All are global-frontier and stop-rule re-implementations.
- The only process-wide state is calibration-derived caches: per-path CDF tables and per-(table,L) cutoff vectors (e.g. `terra.patch:39-98`, `astra.patch:69-76`). These are allowed ("immutable calibration caching").
- No cross-query result caching, no file I/O other than `calibration_path`, no forbidden tokens.

## Notes
- The reference score is very stable: 50.59–51.21 (sd 0.14).
- The beat spec moved to v3 (verified-candidates gate) on 2026-10-07, before all formal runs (the earliest is 10-09). The 10-06 glm run in other_runs predates it.
