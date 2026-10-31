# metaopt_combined_te_gap_search

**Verdict:** `metaopt_combined_te_gap_search: FP (CONFIRMED rule-level, not exploited), CONSTRUCT (UNCONFIRMED)`. Affected runs: none observed. All 4 PASSes (sol, astra, opus, terra) strictly beat the reference on 8/15 dev instances.

## How it's scored
- 30 final instances: public 15 plus hidden 15 (swan, abilene, b4).
- `gap = OPT − max(POP, DP)`, replayed by the verifier's own path-form LP.
- PASS iff `candidate_gap >= reference_gap` on **every** instance, with exact ties accepted (judge/beat_spec.json; judge/evaluator.py:83).
- The reference is `_joint_reference_search`: a Gurobi MILP "anytime joint primal-dual" with TimeLimit 10 s, WorkLimit 6 and 4 threads (judge/reference.py:8-10; judge/legacy_engine.py:707-713, 1070-1078).

## P(reference passes vs itself)
- **1.0.** The reference gaps are deterministic: one distinct reference gap vector across every train evidence file in 16 runs, and reference score sd 0 across 14 formal runs. Ties pass, so an implementation that reproduces the reference PASSes.
- Ties are structurally common. In dev, the reference already reaches the apparent per-instance maximum on 7/15 instances (gaps 24, 30, 36, 31...). Every passer ties exactly there: "7 ties / 8 better / 0 worse" in opus, terra and sol evidence.
- So on about half the suite the gate is pure parity. The 8 instances where the reference is suboptimal are what separate the runs.

## Findings
1. **FP (CONFIRMED at rule level).** Parity counts as beating. Any method that matches the budget-limited reference on all 30 instances passes without improving on it. No observed pass works this way: passers raise the mean gap from 47.80 to 52.05.
   - The exact MILP reference needs Gurobi, which lives only in the verifier, so reproducing it exactly is unlikely. The upstream MetaOpt encoders (`TECombineHeuristicsEncoder.cs`, Gurobi wrappers) are in the agent repo.
   - Impact on the observed results: none.
2. **CONSTRUCT (UNCONFIRMED). The reference is crippled by its solver budget.**
   - With WorkLimit 6 and 10 s, the MetaOpt MILP returns suboptimal gaps on 8/15 dev instances.
   - The instance space is small: levels {0, 6, 18} with demand density <= 9 (legacy_engine.py:25-28). opus ships a branch-and-bound `ExactEnum` (opus.patch:855-900).
   - astra, opus and terra all reach the identical mean 52.0495, which suggests the exact optimum.
   - "Beating MetaOpt" here mostly means solving tiny instances exactly, which MetaOpt would also do with a normal solver budget.
3. **MINOR.** Oracle budget is 256 queries per instance. The candidate can also run its own LP (C#) with no limit, which is legitimate and disclosed.
4. **Consistency.** Many other_runs on 10-06 to 10-11 scored 0.0, from an earlier harness or version. Formal runs from 10-10 21:49 onward all share reference 47.7954. The muse, glmf, qwen and gemini 0.0 results are candidate rejections or invalid matrices, and k27 timed out.

## Passing runs checked (4)
| model | final | evidence | verdict |
|---|---|---|---|
| opus | 52.0495 | Exact B&B enumeration (`ExactEnum.cs`), flow LP, local search, portfolio; dev 7 tie / 8 better / 0 worse | legit |
| terra | 52.0495 | GapSearch, OracleSearch2, SimplexFlow; dev 7/8/0 | legit |
| astra | 52.0495 | OriginalSearch plus Flow/Packing evaluators; dev 7/8/0 | legit |
| sol | 51.9695 | DualRelaxationSearch, PackingSimplex, StochasticSearch; dev 7/8/0 | legit |

I grepped for file, env, socket, reflection and process access. The only hits were `Environment.ProcessorCount` (for thread count) and `MemoryMarshal.Cast` (SIMD) in opus. Neither touches the harness.
