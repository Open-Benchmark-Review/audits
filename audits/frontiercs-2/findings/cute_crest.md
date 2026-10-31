cute_crest: OK (CONFIRMED that the bar is reachable on dev; final difficulty is genuine generalisation). Affected runs: none flip on a defect. k27 timed out with no final selected (agent fault).

## How it's scored
- Final grades 2 hidden programs (vim with 35,556 branches, and sed; judge/programs.json). Dev is grep 2.2 only.
- On each program, 30 seeds × 4000 iterations for the candidate and for the reference (CREST CfgHeuristicSearch), interleaved. Both of these must hold:
  - mean coverage beats the reference by more than 3·s·sqrt(2/30)
  - mean search overhead (strategy CPU + solver CPU, in ms) is lower than the reference's by more than 3·s·sqrt(2/30)
- s is the pooled per-seed sd (beat_spec.json; judge/gate.py `significantly_greater`). There are 4 cells, all required.
- Continuous score: coverage only, relative to bounded DFS. The reference is very stable at 13.22–13.36.

## P(reference passes vs itself)
About 0: a 3-standard-error one-sided margin, about 0.13% per metric, and 4 metrics required.

## Findings
1. **The bar is achievable on the visible program (CONFIRMED).** Train feedback in the traces shows dev PASS on both metrics for sol (21.2), opus (20.8, twice) and astra (22.4, 21.1). Final near-misses at 3/4 cells:
   - sol, opus, terra: coverage on both programs, overhead on one.
   - step, ds1017: overhead on both, coverage on one.
   There is a real coverage-versus-search-CPU trade-off on hidden programs, which is the intended difficulty.
2. **Hidden programs and noise are disclosed.** repo/README.md:108-133 says the final programs are unnamed, that one is 10x larger and that one is non-reproducible. It gives the 3-SE rule and the margin sizes (coverage about 2–4%, overhead about 5% and 30%). This is not a hidden requirement.
3. **FN risk is by design, not a defect.** The 3-SE margin rejects real improvements smaller than about 0.77·s. That is stated, and it is symmetric with the protection against false positives.
4. **No infrastructure errors** in the 16 completed runs. k27: agent_active_deadline_exceeded after 12 train calls, with no final selected.

## Passing runs checked
None (0 PASS).

## Notes
- Static source policy (forbidden includes, identifiers and symbols, sandboxed strategy process) is described in the README "Validity" categories. I found nothing to suggest a reward-hack surface, though I did not audit the sandbox in depth.
- Only the initial commit is public. other_runs contain only cancelled or failed duplicates (gemini, step).
