# parbutterfly

**Verdict:** `parbutterfly: OK, plus MINOR (CONFIRMED: reference measurement degraded in 2 runs; no verdict affected)`. Affected runs: astra and sol (reference timing anomaly, verdict unaffected). The low bar is a difficulty observation, not a CONSTRUCT defect.

## How it's scored
- `judge/evaluator.py:212-231`: for each of 8 graphs (6 uniform, 2 skewed Chung-Lu), 31 alternating candidate/reference fresh-fork runs. Pass needs exact counts and `median(ref_i/cand_i) > 1.05` (`evaluator.py:13,26-27`) on every graph.
- The continuous score is `100 ln S/(ln10 + ln S)`, where S is the geomean paired speedup over a frozen **serial** baseline on the uniform graphs only (`evaluator.py:148-159`). `reference_score` is the same curve applied to reference/baseline (`evaluator.py:161-171`).
- Timing is a fork per run with landlock and seccomp isolation (`judge/trusted_count_total.h:13-75`, `judge/trusted_isolation.h`). The graph is preloaded and wedge preprocessing is excluded. No state can persist between runs.

## What the "reference" is
- The source-locked authors' ParButterfly `CountTotal`, restored by `judge/reference.patch` (all 7 headers). The CLI forces `-countType BATCHS -rankType ACOCORE` (`evaluator.py:133`).
- On 2026-10-12 the BATCHS path changed to the paper's Section 6.2.2 f-rule. It always computes degree ranks, then uses side order when f<0.1 and degree order otherwise (`reference.patch:1045-1076`). After that comes the authors' simple batching, with `stepSize = min(workers*60, max_array/nu)` = 240 at 4 threads (`reference.patch:598`).
- The "baseline" behind the 3.5-16x figures is `baseline_naive.patch`, the frozen **serial** dispatch (`baseline_naive.patch:982,1091`). It is not the reference, so those multiples are versus serial code. In normal runs the reference itself is about 3.4x over that baseline (reference_score ≈ 34.7).
- **Not egregiously crippled.** It is the authors' code with the authors' own ordering rule and their default aggregation, both sides get 4 threads, and it is built with `-O3 -march=native -fopenmp -DOPENMP` (`judge/trusted_build.py:13`). Using 4 threads instead of the paper's 48 cores is a deliberate calibration choice (`upstream.lock.json` calibration block). It shrinks the regime, but it isn't asymmetric.

## P(reference passes vs itself)
About 0. It needs a paired median above 1.05 on all 8 graphs, and the self-ratio median is about 1.0.

## Findings
1. **Passing is easy, but legitimately.** 16/17 runs pass and the one fail is glm, whose agent was OOMKilled with no submission. The k27 patch (`hf/patches/parbutterfly/k27.patch`) passes with about 90 lines: textbook global-degree-ordered wedge counting with per-thread `cnt/ver` arrays. That is essentially the paper's own algorithm, written without the 240-batch × nu arrays. It runs about 1.15x faster than the reference (counting_seconds 0.152 vs 0.176). The top patches reach 0.029 s vs 0.17 s. The 5% bar over the authors' general-purpose framework code is low, but this is an implementation-quality win in the agreed harness, not a hack. Not flagged as CONSTRUCT.
2. **MINOR, CONFIRMED: degraded reference measurement in astra and sol.** In those two runs `reference_counting_seconds` = 1.947 / 2.004 s, against 0.16-0.30 s in all 13 other runs. The serial baseline was 1.18 / 1.21 s against about 0.58 s elsewhere. So the reference was slower than the serial baseline, which is why `reference_score` = 0.0 (`evaluator.py:151-153`). The host was apparently contended: the parallel reference slowed about 11x and serial code about 2x. There is no reference-noise gate, unlike clusterwise_spgemm. Both runs would still pass on a normal host: their baseline_speedup_geomean is 11.6x and 11.1x against the reference's normal ~3.4x, and both have earlier PASS reruns (53.1, 54.8). Verdict is not affected.
3. A `reference_score` of null (muse, gemini, step) is a record-format artifact. Those records predate the `-refscore` version string and have no reference_score key; reference_counting_seconds is normal (0.16-0.17 s).
4. All formal runs are dated Oct 12 20:34 or later. The f-metric reference change is dated 2026-10-12. The reference times of 0.16-0.19 s match the post-change calibration (about 0.14 s uniform), so these runs appear to be on the f-metric version.

## Passing runs checked (16)
I grepped all 16 patches for getenv, file I/O, static caches, threads and hard-coded sizes, and read k27, astra and the comment headers of the rest. All of them implement CountTotal as wedge counting with side or degree ordering, dense per-thread counters, and a skew detector (e.g. astra's `maximum_center_degree > 4*avg` switch to the ranked path).
- muse: reads `getenv("PARB_SIDE_MAXDEG")`, a tuning knob. It is harmless because the worker runs `clearenv()` (`trusted_count_total.h:25`).
- wonder: adds a test script under solver_extensions that is not used by the build.
- Verdict for all 16: **legit**.

## Notes
- Four graded uniform graphs out of 8 make the skewed graphs the only place ranking matters. Beat spec v3 added them because v2 was passable by side order alone (`beat_spec.json` comments).
