# parallel_dbscan

**Verdict:** `parallel_dbscan: FP (CONFIRMED, pre-fix scorer; already fixed and re-run for ds1017); no other PASS uses it. FN timing-noise risk MINOR/UNCONFIRMED`. Affected runs: ds1017 only (already superseded). The pre-fix passes of astra, sol, opus and glmf, and the passes of terra and k31, are clean.

## How it's scored
- 12 final workloads: 8 small (12-14k points) plus 4 seed-spreader workloads of 200k points. Each needs exact DBSCAN output on every execution and the strict `cm < rm` median elapsed time (current `judge/evaluator.py:576,587`; `BEAT_MARGIN = 0.0` at `:30`).
- Pre-fix (`git show 282b1edd^`, lines 27-29 and 517-530): per workload, 8 alternating repeats of one `DBSCAN -r 5` process each. The median of the 5 in-process rounds is taken, then the median of the 8.
- Post-fix (282b1edd, Oct 25): each round is its own `-r 1` process, wrapped in `state_guard.py`.
- Continuous score: `100*0.02/(0.02+C)` over the 8 small workloads.

## P(reference passes vs itself)
Strict `<` on 12 independent paired comparisons gives about 0.5^12 ≈ 2e-4. Not an FP risk.

## Findings
1. **FP, CONFIRMED and fixed.** The pre-fix scorer allowed function-static memoization across the 5 in-process rounds (commit 282b1edd message). ds1017's PASS (78.68) came from this. Its re-run on the revised task is FAIL (72.55 vs 72.51, 10/12).
2. **Pre-fix PASS audit, clean.** I checked the patches of astra, sol, opus and glmf (Oct 10-13, pre-fix) and terra and k31 (Oct 26). I grepped every patch for `static` state other than `static inline`/`static_cast`/`schedule(static)`, file-scope globals, `thread_local`, `getenv`, file I/O, `/tmp`, shm/mmap, and "round"/"first call" logic. None found. opus has a per-cell `boxState` bounding-box cache, but it is allocated per call (`newA(int, m+1)`, and a stack array in `FsolClusterFew`) and freed at the end (`hf/patches/parallel_dbscan/opus.patch:487-497,612,711`). Nothing carries over between rounds.
3. **terra and k31 version.** Both were created Oct 26 18:59 / 19:48, after 282b1edd (Oct 25 05:28) and the image publication (67535c0a, Oct 25 23:10), so they are probably post-fix. Their reference scores (71.9, 72.4) sit on the pre-fix scale, but ds1017's labelled post-fix re-run also shows 72.5, so the score scale can't tell the versions apart. It doesn't matter: neither patch has carried state, so both are legit on either version.
4. **Timing noise, MINOR/UNCONFIRMED.**
   - The in-run reference-score range of 64.6-74.5 reflects host variation across runs. In time that is reference C ≈ 6.9-11 ms, and pairing within a run removes it, so it is not a within-run noise estimate.
   - Within a run, beat_spec reports reference-vs-reference paired ratios "within about 2%" on small workloads (`judge/beat_spec.json` comments).
   - The pass margins look small in score points but are larger in time: geomean time reductions are astra ~12%, sol ~11%, opus ~16%, terra ~9%, glmf ~6%, k31 ~6%. That is well beyond the ~2% noise in aggregate.
   - The real exposure is FN on near-parity workloads, where the editable stage is only 0.15-9 ms of a 1.6-55 ms total (beat_spec comments; uniform-7d has a single core point). There a candidate wins only through constant savings, and strict `<` is close to a coin flip.
   - Fails at 11/12 with positive margins (glm +2.1, ds +1.3, gemini-agy +2.9) are consistent with one noisy loss. Per-workload rows aren't available, so this is UNCONFIRMED.
   - I estimate P(pass) for a candidate uniformly ~2% faster at about 0.84^12 ≈ 12%.

## Passing runs checked
astra, sol, opus, glmf, terra and k31 → **legit**. All are algorithmic core-cell connectivity work: bounding-box prune/accept, sorted-coordinate witness windows, union-find over cells (e.g. k31's header comment). opus adds a 32-byte `.skip` "alignment pad" function to tune code layout (`opus.patch:716-718`). That is noise-chasing, but it is not a harness exploit.

## Notes
- Re-runs show unstable verdicts across different agent runs, e.g. glm PASS on Oct 6 vs FAIL formally, and astra FAIL on Oct 10 vs PASS formally. That is consistent with a borderline strict gate.
