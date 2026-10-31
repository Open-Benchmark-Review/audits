# parallel_radix_sort

**Verdict:** `parallel_radix_sort: FN (CONFIRMED mechanism; per-run flips UNCONFIRMED)`. Likely affected FAILs: sol, gemini-agy, k31, terra and k3 (9-11/12 sort wins with a 5-8% in-run geomean advantage). The PASSes (glm, step) are legit.

## How it's scored
- 12 final workloads: 8 original plus 4 16M-key v3 workloads. Each runs one candidate process and one reference process of 21 in-process rounds, alternating order by workload (`judge/evaluator.py:109-124`). Every round re-copies the input and checks sortedness and the multiset (`judge/benchmark.cpp:135,148-149`).
- Pass needs, on every workload, strict `c<r` sort_time_ns, strict `cg<rg` region_graph_ns, and aux ≤ 5% of input (`evaluator.py:125-127`). There is no tolerance.
- Continuous score: `100 L/(ln10+L)` on the geomean speedup vs std::sort over the original 8 workloads only (`evaluator.py:55-64,129-132`).

## P(reference passes vs itself)
About 0: 24 strict comparisons give 0.5^24. No FP risk.

## Findings
1. **FN, CONFIRMED by the authors' own calibration and by run data.**
   - `judge/beat_spec.json` comments say the editable planner is about 7% of a 28 ms sort and that "reference-vs-reference runs of this evaluator vary by 0.5-4% (outliers 15%) per workload". They also say a better planner "is not separable in sort time (ratios 0.99-1.05)".
   - The v3 witness, a planner 29-44% faster, is only "0.6-2% faster in paired sort time" on 3 of the 4 new inputs. Even so, strict `c<r` sort time on all 12 workloads was kept, and each comparison rests on a single process pair.
   - Run data: region_graph_ns is 12/12 and aux is 12/12 for **all 17 runs**, so sort_time alone decides the verdict. Its pass counts are 12, 8, 10, 6, 10, 6, 7, 1, 6, 7, 7, 8, 12, 4, 11, 9, 11.
   - Converting the in-run margins (score − reference_score on the same baseline) to geomean time advantage gives: glm (PASS) +5.3%; sol FAIL +7.3% (10/12); gemini-agy FAIL +8.2% (11/12); terra FAIL +5.5% (9/12); k31 FAIL +5.1% (11/12).
   - So candidates that are faster on average than a PASS run fail on 1-3 of the 12 single-pair comparisons. Near-parity runs (ds +2%, muse −0.2%) land at 6/12, which is coin-flip behaviour.
   - The v2 note says the same thing: "PASS and FAIL runs interleave, so the verdict did not track speed". v3 didn't fix it for sort_time.
   - Rough estimate: with per-workload noise sd ≈ 2-3% and a true 2% gain, P(12/12) ≈ 0.75^12 ≈ 3%.
2. The failing workloads aren't identifiable: per-workload rows are private and absent from the run JSON. Some fails may be genuine regressions on the 16M workloads, which are not in the continuous score. That is why the per-run flips are UNCONFIRMED.
3. No memoization exploit. In-process rounds re-copy the input and are fully checked, and only `RadixSort/edgelistgraph.h` and `frontier_solution/` are editable (the planner), so caching could only save the planner fraction. The thread_local and static scratch buffers (step, wonder, gemini-agy) are allocation reuse, which is legitimate. The witness itself is "per-thread scratch lists reused across calls".

## Passing runs checked
- glm (`hf/patches/parallel_radix_sort/glm.patch`, 117 lines): the planner first pairs reciprocal from/to regions (two-cycles), then drains the rest greedily. That means fewer and longer exchanges, so less data movement. **Legit.**
- step (`step.patch`, with `frontier_solution/edge_list_graph_impl.h`): the same two-cycle-first pairing plus a thread_local scratch array (`step.patch:90-93`). **Legit.**

## Notes
- The reference is the authors' Regions Sort planner at 4 Cilk workers, which is not crippled.
- The task's construct is weak: it rewards a component that is under 10% of the timed metric (paper Figure 12). The authors acknowledged this and responded by adding region_graph_ns.
