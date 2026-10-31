# batch_local_counting: FP (CONFIRMED, pre-fix harness surface; no formal PASS used it) + MINOR. Affected runs: none

Problems/Database/batch_local_counting. 17 formal runs, 5 PASS (astra, sol, opus, gemini, terra), and nearly all were scored on the pre-fix harness (fix b11a73b8, 2026-10-25 05:21).

## How it's scored
- 6 workloads (3 graphs x {4voc, 5voc} query halves). Each workload needs exact output bytes, plus candidate case time < reference case time in **all 5** interleaved rounds (`judge/evaluator.py:266`, pre-fix line 262).
- The continuous score is median log2(naive/candidate) mapped to 100L/(2+L). The reference scores about 20 (about 1.41x over naive).

## P(reference passes vs itself)
- A byte-identical reference patch is deduplicated (`_paired_protocol`), so it ties and fails: P = 0.
- A different patch running at the same speed passes with probability about (1/32)^6, roughly 1e-9. No FP from the rule itself.

## Findings
1. **FP surface pre-fix (CONFIRMED, now fixed).**
   - Pre-fix `_run_prepared` (`git show b11a73b8^:.../judge/evaluator.py:215-221`) only cleared the candidate's own result dir before each run.
   - Naive and reference outputs stayed on disk under their trees across rounds, and nothing stopped writes to /tmp, $HOME or /dev/shm.
   - The commit message reports that caching patches scored about 83 vs a reference of about 17. The fix adds `shutil.rmtree(output)` after hashing (line 232) and `StateGuard` per candidate round (line 297).
2. **No formal PASS used it (CONFIRMED, by reading every PASS patch).**
   - None of the 5 PASS patches opens, lists or writes anything except the `-d` graph, the `-q` query dir, the `-t` triangle file and `-r/<query>` outputs. None uses std::filesystem, getenv, shm, sockets or SysV IPC (grep for fopen/ifstream/ofstream/opendir/mmap/getenv/HOME/tmp/shm/unlink/rename over all + lines).
   - Details per patch are in the table below.
   - Static storage cannot outlive a scope.out process, and no patch persists anything to disk. Pass scores (65–73) sit well below the about-83 caching signature.
3. **MINOR:** per-workload strict timing is enforced on the small 4voc batches, where loading dominates. glm/ds/k3 got 5/6 with 1.9–2.5x aggregate speedups. That looks like genuine per-workload slowness, not noise: they missed one workload while others passed 6/6 by large margins. UNCONFIRMED as FN.

## Passing runs checked
| run | score | approach | verdict |
|---|---|---|---|
| astra | 70.3 | homomorphism/inclusion–exclusion batch counter. Reads only the `-d` graph (`astra.patch:944-950`); output goes through the existing `saveCount` to resultPath | legit |
| sol | 65.1 | shared counter. Reads the `-t` triangle file (`sol.patch:235`, a documented input that all variants receive) and writes `resultPath/<file>` (`:1504`) | legit |
| opus | 72.1 | rooted homomorphism vectors. `fopen(path,"rb")` only on the data graph and query files (`opus.patch:231-237,261,281`), `fopen(...,"wb")` only on `resultPath/files[i]` (`:336,1982`), `mmap` is MAP_ANONYMOUS only (`:114`) | legit |
| gemini | 73.1 | hard-coded table of canonical 5-vertex pattern → hom/sub Möbius coefficients (`gemini.patch:52-100`). The table depends only on the pattern, covers all patterns in the visible collection, and has an independent-path fallback. I/O touches only the query/graph/triangle inputs and `resultPath/files[i]` (`:1691-1764`) | legit (pattern-algebra precomputation, not output caching) |
| terra | 65.1 | triangle-fork specialisation. `fopen` on the data graph only (`terra.patch:1696`) | legit |

## Notes
- The in-run reference score is stable: 19.49–20.74 (sd 0.31).
- The candidates' 13–27x speedups over naive are plausible for homomorphism-based batch counting. The pre-fix Preview cache exploit reached about 900x (score about 83).
