edlib_exact_alignment: FN (CONFIRMED). Affected runs: astra and sol (59/60 cpu-time cells), wonder, opus, gemini, k31 and terra partially. Also a consistency concern (UNCONFIRMED): non-accepted reruns passed 8/12.

## How it's scored
- 60 final workloads (lengths {10k, 30k} × similarity {60, 70, 80, 90, 99}% × modes {NW, SHW, HW} × public/held-out).
- Per workload:
  - T = min(15 path-run times) − min(15 location-only times), the reconstruction time of one executable (judge/evaluator.py:449-451). It must satisfy 0 < T_C < T_R strictly.
  - Core live bytes A_C ≤ A_R (evaluator.py:461).
- Conjunction over all 60.
- Score: 100·mean(L²/(L²+median path time)), with L = length/1e5 (evaluator.py:445-447). The reference sits at 58.5–66.1.

## P(reference passes vs itself)
About 0 (60 noisy strict cells). Equality passes the memory rule, but the time rule is strict.

## Findings
1. **FN: a noise-dominated time metric (CONFIRMED).** Across 48 train evaluations from 4 traces (gemini-agy, astra, sol, terra):
   - The reference's T is only 0.06–0.17 ms on the 10k/99% workloads (median 0.10–0.12 ms, robust CV 14–31%), and 0.35–0.42 ms on the other 10k workloads.
   - It is computed as a difference of minima of whole-process wall times.
   - 6/48 evaluations had a non-positive reference T on some workload (for example −0.0108 s). The rule then makes PASS impossible for that evaluation regardless of the candidate (beat_spec "a workload whose reference difference is not positive cannot be passed").
   - Even good candidates flip between calls:
     - gemini-agy (final PASS): 0, 3 or 12 failing cells across similar patches.
     - astra: 0, 7 or 22.
     - sol: 0, 1, 1, 1 or 2.
   - In final, astra and sol, with median T ratios of about 0.45–0.75, failed exactly 1/60 cells. Their failures are plausibly noise on the ~0.1 ms workloads.
2. **Verdict instability across same-evaluation reruns (CONFIRMED data, cause UNCONFIRMED).** The per_task other_runs record "relation: same_formal_evaluation" reruns: glm, astra, sol, ds, k3 and muse all PASSED on the 2026-10-12T03:24 batch, and astra and sol also passed on 10-11T23:22 (8/12 scored reruns PASS). The accepted runs (10-12T12:19 onward) are 0/6 for those models. Either the verdict is close to a lottery on this metric, or something changed that the public git history doesn't show (initial commit only).
3. **Reference score drift (MINOR).** ds1017 (Oct 24) has a reference score of 58.7 and terra (Oct 26) 58.5, against about 65.5 elsewhere. That points to slower judge hardware or load for later runs; the PASS rule is paired, so verdicts aren't directly biased.
4. Memory failures (0/60 for ds, k3, muse, k27, glmf, step, ds1017, opus) are genuine: they used more reconstruction storage than Hirschberg. Not a defect.

## Passing runs checked (1 PASS)
- gemini-agy: legit. A ~2,000-line rewrite of the reconstruction as a bit-parallel Myers/Hirschberg with snapshot checkpoints and a single scratch buffer (patch excerpt: `struct Snap`, `struct Task`, one `malloc(bufCap)`). It stays inside the reconstruction function, as check_surface and the ELF surface checks require. It passed 60/60 in final, but its own train calls show the same patch family failing 3 to 12 cells, so the pass itself partly reflects favourable noise.

## Notes
- Statement completeness is fine (beat_spec statement_sentences, README). The location-only subtraction design is sound in principle, but the signal (0.1 ms) is too small for a strict per-cell win on wall-clock process times.
