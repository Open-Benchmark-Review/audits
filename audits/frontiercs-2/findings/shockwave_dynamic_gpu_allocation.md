# shockwave_dynamic_gpu_allocation

**Verdict:** `shockwave_dynamic_gpu_allocation: CONSTRUCT (CONFIRMED evidence, judgment: moderate) — all 4 PASSes are exhaustive search over 8-job toy instances with an exact simulator replica; no FP/FN`
Affected runs: astra, gemini, gemini-agy, terra (PASS legit in-harness, but not "a better Shockwave").

## How it's scored
- `judge/beat_spec.json`: 2 final traces × 4 metrics (makespan, average JCT, worst finish-time-fairness rho, % unfair jobs), each strictly lower than the Shockwave reference. 8-cell conjunction.
- The simulator is deterministic. Reference score 41.915 in all 17 runs (sd 0).

## P(reference passes vs itself)
0. Deterministic and strict.

## Findings

### 1. CONSTRUCT: toy scale makes brute force win (CONFIRMED evidence)
- Every trace has exactly 8 jobs on 4 V100s. The README says "The eight-job subsets and four-GPU scale are challenge constants (not from materials)" (`agent-base/frontier/task/repo/README.md:26`). The paper (Zheng et al., NSDI'23) targets large clusters and many jobs.
- All 4 passing patches enumerate schedules exhaustively and predict job progress exactly:
  - astra: bitmask enumeration over job subsets, with a greedy fallback only `if len(jobids) > 9` (`hf/patches/shockwave_dynamic_gpu_allocation/astra.patch:143`). It models the simulator's 20 s restart overhead.
  - gemini-agy: `"Exact step-level replica of Scheduler.simulate() dynamics for a single job"` (`gemini-agy.patch:168`) plus `itertools.permutations` over job groups (:1121-1151).
  - gemini: `_simulate_order` over `itertools.permutations(active_ids)` (`gemini.patch:319,442`).
  - terra: `permutations(jobs)` and subset masks (`terra.patch:120,198,251,272`).
- These rely on (a) n ≤ 8 (8! = 40,320) and (b) the per-epoch duration profile being exact in simulation. That's the same metadata Shockwave gets, but Shockwave was designed for uncertainty and scale.
- In-harness these are legitimate online schedulers: they use only metadata of arrived jobs, don't read the trace files, and do no I/O. So it isn't FP. But "beats the reference" here means "beats Shockwave on 8-job instances with a perfect simulator model", not an advance on the paper's method.

### 2. No FN from strictness
The ref is deterministic, so the strict gates aren't noisy. Many FAILs miss only makespan on 1/2 traces (sol, k3, opus, glmf, ds, step), but those are deterministic losses or ties, not noise.

### 3. Hack surfaces checked
- The final traces live in the verifier image (`judge/judge_data/final_*.trace`). A patch *could* try to read them at runtime, but none of the 4 passes uses `open`/`os`/`glob`/`pickle`/`sys`/`inspect`/`__file__`/`environ`/`subprocess` (grep).
- `prof["duration"]` used by gemini/gemini-agy equals the sum of per-epoch durations the reference also receives (`repo/scheduler/utils.py:1403-1428`, README:43). Not extra oracle information.

## Passing runs checked
astra, gemini, gemini-agy, terra: **legit within harness** (no I/O, no hidden-trace access), construct-limited as above.

## Notes
Gurobi has a 15 s timeout and 24 threads, which could make the reference hardware-dependent, but the measured reference was identical across all 17 runs.
