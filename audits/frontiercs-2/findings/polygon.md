# polygon

**Verdict:** `polygon: FN (CONFIRMED), FP (CONFIRMED surface, no observed exploit)`.
- FN-affected runs: astra, ds, k3, muse, opus, wonder, glmf. All are refuted 21/21 and fail only `wall_time_seconds` on 8–11 small original records.
- FP surface: the timed value is self-reported by the editable code. The 4 passes (glm, ds1017, terra, k31) are legitimate under the reference's own timing convention.

## How it's scored
- 21 workloads: 16 LeetCode pairs, 3 D-50/D-100 disambiguation, and 2 "paper_hard" pairs.
- `refuted_pair`: cand >= ref.
- Wall time on original records: `cand <= ref + max(0.03, 0.2*ref)`. On hard records: `cand < 0.5*ref` (judge/evaluator.py:854-875).
- PASS is the conjunction over all 21 × 2 checks.
- The continuous score quantizes total time to 0.5 s (evaluator.py:192-205). That is why nearly every run scores 95.5–96; the score says nothing about the gate.

## P(reference passes vs itself) / P(tie passes)
- **P(reference passes vs itself) ≈ 0**, because hard records need a 2x speedup. The authors report 0/72 self or same-work pairs passing (beat_spec.json comments).
- **P(tie-level solution passes) ≈ 0** for the same reason.
- The coordinator's guess that this is timing noise near a tie is **not** right. The 9–21 pass counts are driven by a deterministic ~0.3 s offset (Finding 1), not by noise. Repeated submissions of the same patch reproduce the same per-workload times and flags, for example sol's and terra's repeated ~98.28 submissions with ±0.01 s on small cases.

## Findings
1. **FN (CONFIRMED). Pass/fail is decided by where the candidate starts its stopwatch, specifically whether it includes the one-time SQL grammar build.**
   - `Time` is the `total_time` that the candidate's `Environment.check` returns (repo `evaluation/leetcode/online.py:97,109` → `frontier_runner.py` reads CSV `Time` → evaluator.py:723 `result["time_seconds"]`). The worker does not measure it.
   - The agent README says otherwise: "`time_seconds` is the worker's elapsed time around `Environment.check`" (repo README.md:171).
   - The reference parses both queries **before** starting its timer (judge/reference.patch lines 8-31). That excludes mo_sql_parsing's lazy grammar build. I measured that build locally at **0.284–0.290 s** on the first `parse()` call, versus 0.0005 s for later calls. Each case runs in a fresh worker process, so every case pays it.
   - Candidates that time the whole of `check` report about 0.32 s on trivial pairs. This includes muse, k3, glmf and wonder (timer set before `parser.parse`) and astra (timer set before `discover`). Each of them fails 8–11 small originals, where the reference must be under about 0.27 s.
   - Candidates that exclude the build pass those same records at 0.01–0.03 s. k31 parses before `start_time` (k31.patch:20-24). glm warms the parser in `engine` before its timer (glm.patch:330-345). ds1017 says it triggers "the one-time SQL grammar initialization while the module is being loaded, before any per-case search timer is started" (ds1017.patch:110-115).
   - Table from the trace evidence: the trivial-pair times are 0.32–0.34 s in every failing run's dev submissions and 0.01–0.03 s in every passing run's.
2. **FP surface (CONFIRMED by code, not exploited).** The evaluator only checks `0 <= time_seconds <= budget` (evaluator.py:725-733). The real worker wall time (`record["wall_seconds"]`, evaluator.py:747) is never used for the decision. A submission could return a tiny constant time and pass every wall-time check while being slower. The hard-record 0.5x ratio offers no protection.
3. **k27 reference_score 0.0 (benign).** k27's patch was rejected by policy ("changes immutable scaffolding" in 19 of 24 train calls and in the final). `_invalid` returns `_metrics(workloads)` with the default `reference_score=0.0` (evaluator.py:232-233), so the reference never runs. It is a reporting artifact, not a reference failure.
4. **gemini evaluator_error (MINOR, CONFIRMED).** The original final raised `ReferenceFailure`, meaning the reference did not refute within its budget. It was re-judged as FAIL with 96.57 and wall 19/21. The 2 failures are its slow disambiguation records (dev 3.8–6.4 s), which are genuine. Reference flakiness exists but did not flip the verdict.
5. **Consistency.** v3 hard records (10-07/10-08) were added after early glm runs that all scored 92.13 (in other_runs). All formal runs (10-09 onward) share the reference scores 95.55–95.75. The spread comes from 0.5 s quantization of the reference's own total time.

## Passing runs checked
| model | final | verdict | evidence |
|---|---|---|---|
| glm | 97.66 | legit | In-process z3 pipeline; parser warmed before timer, same convention as reference; hard records 0.05–0.10 s vs ref 1.8/7.1 s |
| ds1017 | 97.66 | legit | In-process z3; grammar warmed at import (patch:110-115); timer covers encode+search+decode |
| terra | 97.95 | legit | Custom fast_parser plus search extensions; timer covers parse; small cases 0.02 s |
| k31 | 97.95 | legit | Timer starts after parse (like the reference), covers encode, search and decode; incremental prover |

All four passes are real speedups (in-process solving and better search). They pass partly because they follow the reference's undocumented timing convention.

## Notes
- The authors' 0.5x hard-record ratio is well justified as a noise guard. The problem is the definition of the timed window.
