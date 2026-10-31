binary_fuse_filter: FN (CONFIRMED), MINOR/CONSTRUCT (CONFIRMED: resident-bytes win is 8 bytes), FP surface (UNCONFIRMED: allocation-accounting bypass not enforced). Affected runs: glm and sol (single-cell lookup loss), plausibly wonder (2 cells).

## How it's scored
- Final = 36 configs (2 seeds × bits {8,16} × n {1e4, 1e5, 1e6} × 3 key families) × 4 query mixtures = 144 workloads (judge/evaluator.py:149-156). Train is the 72 TRAIN_SEED workloads, which are reused in final.
- Per workload: resident_bytes (max of 5), build_ns (median of 5) and lookup_ns (median of 5) must be strictly below the paired reference (evaluator.py:278). FPR and space overhead must also pass certified non-inferiority checks against fixed anchors. Conjunction over all 720 cells.
- Score: mean over rows and metrics of 100·R/(C+R) (evaluator.py:286). The reference vs itself is identically 50 by construction, so the constant reference score of 50 is a tautology and says nothing about noise.

## P(reference passes vs itself)
0. resident_bytes is deterministic, so equality fails the strict rule.

## Findings
1. **FN: strict median-of-5 lookup on 1M-key, 16-bit workloads (CONFIRMED).** These lookups are memory-bound.
   - In sol's last train call, the reference lookup_ns samples within one run span about 6.8–7.4 ns (sd ~2–3%), and the candidate is only 7–9% faster on these cells. The median is ~25% faster elsewhere.
   - Across sol's own train calls, its worst-cell ratio drifts between 0.938 and 0.987 (glm: 0.902–0.984).
   - Final has 24 such b16/n=1e6 cells. A real 5–9% improvement therefore fails at least one cell with non-trivial probability, and a 2–3% improvement almost surely fails (per-cell P(win) ≈ Φ(3/2.8) ≈ 0.86, so 0.86^24 ≈ 3%).
   - glm (score 52.9) and sol (53.9), both 21–26% faster on median lookup, failed exactly 1/144 lookup cells; wonder failed 2. These are plausible noise-driven false negatives on real improvements.
2. **resident_bytes "win" is cosmetic (CONFIRMED, CONSTRUCT/MINOR).** In astra's, sol's and wonder's last train calls, the candidate saves exactly 8 bytes on every workload (relative saving 0 to 6.4e-4). It comes from dropping struct fields (SegmentLengthMask, SegmentCount, ArrayLength; astra patch). The strict memory gate is met without any real space improvement. It does not create passes on its own, since build and lookup must still win.
3. **Allocation-accounting bypass not enforced (FP surface, UNCONFIRMED).** The README forbids bypassing accounting (agent-base/frontier/task/README.md:29-31). However, judge/bridge.c:43-46 only macro-redirects malloc, calloc, realloc and free, and I found no token or ELF check for mmap, posix_memalign, aligned_alloc or static arrays in the evaluator or patch policy. Untracked fingerprint storage would shrink resident_bytes and space_overhead. No passing patch does this (grep over 8 patches: all allocations go through malloc/calloc).
4. **Dev/final overlap (MINOR, CONFIRMED).** Final includes all 72 train workloads (evaluator.py:151). The other 72 are new, so tuning to train keys alone can't secure a pass.

## Passing runs checked (3 PASS)
- astra: legit. Custom fast peeling (`binaryfusefast.h`), with an `ExtraKey` fallback for a single unpeelable key, which is stored and checked exactly, so there is no FPR cheat. All allocations are calloc/malloc.
- opus: legit. Rewritten construction, single-block allocation through tracked malloc.
- gemini-agy: legit. Construction and lookup rewrite. The `malloc(total_bytes)` warm-up sits inside create(), which is timed.

## Notes
- The judge README records that the predecessor rule (strictly separated accuracy intervals) was unattainable and was replaced by non-inferiority guards. Only the initial commit is public, and the reference score is constant by construction.
