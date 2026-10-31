# hypergraph_core_numbers

**Verdict:** `hypergraph_core_numbers: OK / MINOR (UNCONFIRMED version-timing ambiguity around the 2026-10-14 framework-first build)`. Affected runs: none confirmed.

## How it's scored
- 4 final hypergraphs (2 public, 2 held out). Each gets 7 alternating fresh-process pairs at 8 threads and another 7 at 1 thread, timed by the parent `perf_counter_ns` around the whole process. Every execution must produce exact core numbers.
- Pass needs `C <= 0.97*R` for both thread counts on every workload (`judge/evaluator.py:16,394-396`; `judge/beat_spec.json`).
- Score: `100*exp(-t/0.25)` on the 8-thread median (`evaluator.py:311`).

## P(reference passes vs itself)
About 0. It needs a 3% win on 8 comparisons, and the authors' worst observed reference paired-median deviation is 1.64% (beat_spec comments).

## Findings
1. **Gate vs noise is reasonable.** The 3% margin is about twice the documented worst reference self-deviation of 1.6%. The sequential metric passes 4/4 in every completed run, so the parallel metric decides.
   - Fails come from real near-parity: glm 0/4 (+0.5% faster), wonder 1/4, step 1/4, qwen 2/4.
   - Borderline fails are sol 3/4 (≈7.5% faster in-run, by the median 8-thread time) and k31 3/4 (≈4.8%). Converting the PASS margins the same way: ds ≈4.5%, k3 ≈5.6%, astra ≈9%.
   - Some FN/FP exposure exists near the 3% line, but a 3% margin against roughly 1-2% noise is defensible. MINOR/UNCONFIRMED.
2. **Version timing, UNCONFIRMED.** "FRAMEWORK-FIRST BUILD (2026-10-14)" forces the framework headers before the editable file and blocks symbol interposition (beat_spec comments). It was introduced the same day the main batch of formal runs was created (Oct 14 09:54).
   - Earlier reruns (Oct 10-12) scored higher (≈57-60) than the Oct 14 formal runs (43-52), but the reference scores also shift by host (41.7-57.2), so I can't attribute the drop.
   - No PASS patch uses macros against the driver or loader, or interposition (see below), so no PASS depends on the pre-fix surface.
   - muse and glmf scored 0.0 ("saved final submission recovered and evaluated"), cause unknown. It might come from the stricter build. UNCONFIRMED.
3. **Reference.** Upstream Ligra `HyperKCore-Efficient.C` at 8 threads, the same build for candidate and reference. Not crippled. The agent repo (`agent-base/frontier/task/repo/apps/hyper/`) contains only the stubbed file and has no `.git` and no binaries.
4. The workload files under `judge/workloads/*.adj` are LFS stubs, judge-side only. The agent Dockerfile copies only `agent-base/frontier/task`.

## Passing runs checked (8)
astra, ds, opus, k3, gemini, ds1017, gemini-agy, terra.
- I grepped them for `#define`/`#undef` targeting the framework, `operator new`, constructors, getenv, file I/O, `exit`, static caches and threads. Only opus has tuning `#define`s (`HKC_PF` and similar) and `exit(1)` on OOM.
- All of them reimplement bucketed parallel peeling in `apps/hyper/HyperKCore-Efficient.C`, some with `frontier_solution/` helpers. **Legit.**

## Notes
- k27 FAIL is an agent OOM (exit 137) with no submission.
- The reference-score spread (stdev 6.1) is host variation across runs; pairing neutralizes it within a run.
