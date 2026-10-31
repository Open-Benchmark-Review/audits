# approximate_mips_query_stopping: MINOR (CONFIRMED) + construct note. Affected runs: none flip

## How it's scored
- Final has 12 disclosed (c, capacity) workloads with 4 gates each: time strictly <, recall@50 >=, last-result ratio >=, verified candidates <= (`judge/evaluator.py:282-287`).
- It also has 12 undisclosed-capacity workloads (140/280/560/1120; `:33`) with the 3 deterministic gates. That makes 84 comparisons.
- Each candidate/reference measurement is a single process run, sequential, candidate first (`:320-330`).

## P(reference passes vs itself)
- A byte-identical patch reuses the candidate rows as the reference, so the time comparison ties and fails (`:302,323-324`).
- A same-speed equivalent needs 12 strict time wins: about 2^-12 = 0.02%. P about 0.

## Findings
1. **Construct note (CONFIRMED mechanism, not egregious).**
   - All 5 PASSes (astra, sol, opus, gemini, gemini-agy) reproduce the reference rule: CDF lookup with (1-pr)^L < 0.1, which is the upstream authors' rule (`judge/reference.patch`).
   - They precompute per-column cosine thresholds to avoid acos and pow per call (e.g. `astra.patch` StoppingTable, `sol.patch` StopTable).
   - With equality allowed on recall, ratio and cost, PASS effectively requires decision equivalence plus a faster `should_stop`. Margins are +0.6..+1.0 points.
   - Non-equivalent rules (glm, k3, muse, qwen, terra) trade recall for cost and fail.
2. **MINOR:**
   - The final suite includes the public suite 0 with the same hash seed (README Workload section).
   - The final-only capacities are disclosed only as "capacities not shown in train". That is fair, but it makes off-grid tuning unobservable.
   - No timing-only failures among the 17 runs, so the strict single-sample time gate did not visibly cause an FN.

## Passing runs checked (5)
- astra, sol, opus, gemini, gemini-agy: legit.
- Each reads only `policy_resource` once into a static table and evaluates the same Eq.16-style rule faster.
- None of them introspects the process, uses forbidden tokens or keeps per-query state.

## Notes
- The reference score is stable: 80.11–81.07 (sd 0.21).
- Task validity looks fine: the interface and table layout are fully documented. The authors' formula has to be recovered from the paper, which is the intended skill.
