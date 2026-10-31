# graph_mining_method_selection: OK (MINOR). Affected runs: none

## How it's scored
- The table of stored runtimes is fixed (`judge/measured_workloads.json`, 224 rows). The final suite is rows 112–223, which come from 8 graph profiles disjoint from dev.
- For each pattern (triangle, 4clique), the candidate's geometric-mean selected runtime must be lower than the reference's by more than a 1e-12 relative guard, and `accuracy_qualified` must hold (`judge/evaluator.py:71-84`).

## P(reference passes vs itself)
- The evaluation is deterministic and ties fail. P = 0.

## Findings
1. **MINOR: `accuracy_qualified` is vacuous.**
   - `_load_suite` rejects the table if either engine misses the error target (`judge/evaluator.py:45-46`).
   - So every GS/NS choice is accuracy-qualified, and the metric always passes.
   - This cannot flip PASS.
2. **MINOR / construct note: the reference's paper-specific overheads never fire.**
   - The harness names every graph "measured" and sets `mem_look_up_time=1.0` (`:144`).
   - So the reference's per-graph `MANUAL_OVERHEAD` and the `livej` special case (`judge/reference.patch`) never apply. Its fitted log-linear coefficients do the work.
   - The reference still lands at 86.9 against an oracle at 100, so it is not crippled.
3. **No leakage path found.**
   - The runner uses `python -I` and passes only nine public fields per case via stdin (`:87-89,136-155`).
   - The stored runtimes and errors are never passed to the candidate.
4. **No noise.** Runs like glm (87.97) and terra (88.21) beat the reference score but fail one pattern. That is the stated per-pattern rule, not an FN.

## Passing runs checked (7)
- astra, sol, opus, qwen, gemini, ds1017 and gemini-agy are all legit.
- Each is an analytic or fitted cost model of the GS and NS engines, using vertices, edges, triangles, max_degree, c, ns, cores and pattern.
- The only import is `math`. There is no file, os, sys, inspect or frame access, and no call counters.
- opus fitted per-(pattern, cores) coefficients from local engine timings (comments in `opus.patch`).

## Notes
- The in-run reference score is constant at 86.92. The task is well specified, and the agent can time the bundled C++ engines locally to fit a model.
