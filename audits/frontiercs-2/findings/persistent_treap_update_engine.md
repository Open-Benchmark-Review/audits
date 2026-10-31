persistent_treap_update_engine: OK, MINOR (UNCONFIRMED construct note). Affected runs: none flip.

## How it's scored
- 6 cases × 4 (threads, clients) configs = 24 pairs (judge/evaluator.py:52, 130-143). Each pair needs three strict median-of-5 wins over the paired reference, with no tolerance:
  - throughput >
  - peak RSS (ru_maxrss via wait4) <
  - historical range-query time <, plus an exact answer checksum against the serial scaffold
- Comparisons are at evaluator.py:584-595 and 410-419; the conjunction is at 102-106. Final seeds are secret-keyed (evaluator.py:121-127).
- Continuous score: `100*ln Q/(ln10+ln Q)`, where Q is the geomean of the candidate/naive-serial throughput ratio. Reference Q ≈ 1.30, which gives score ~10. The 8.2–12.6 spread is throughput noise against the naive baseline.

## P(reference passes vs itself)
About 0 (72 strict comparisons, each ~50%).

## Findings
1. **No hack found (CONFIRMED by patch review).**
   - Correctness is checked at checkpoint versions with concurrent clients (judge/judge/correctness.cpp).
   - The history benchmark queries uniformly random retained versions after process(), against an oracle checksum (judge/judge/history_bench.cpp).
   - Timed throughput includes Close()→process() (repo main.cpp).
   - So lazy materialisation or version dropping would be caught by the history and memory metrics. Source-policy tokens block timing and introspection (evaluator.py:56-62).
2. **Construct note (MINOR, UNCONFIRMED as egregious).** The paper's optimized parallel scheduler reaches only ~1.3x over the serial scaffold at 4–6 threads (aggregate_reference_naive_ratio 1.296 in ds's key_metrics). Several passes use no parallel scheduler at all:
   - k31 (patch: serial path-copying AVL, `pry` reused as height, mmap bump allocator) beats the reference by 1.33–1.7x on throughput, with 0.85x memory and 0.76x history time (k31 train evidence).
   - muse is also serial.
   The task allows replacing helper types (repo README "Design space"), and the metrics really did improve. But "beat the reference" here does not require beating the paper's idea, which is concurrent treap update scheduling.
3. **Near-miss failures look like real parity, not FN.** ds and ds1017 failed historical_query_us on 1/24 pairs, and step failed throughput on 1/24. Their train evidence shows the worst history-pair ratio at 0.91–1.00 (ds1017 1.000, 0.999) and step's worst throughput ratio at 1.045. They were at parity on one metric, so failing a strict rule there is defensible.

## Passing runs checked (12 PASS)
All 12 patches downloaded; I read k31 and astra in full and spot-checked opus, glm and qwen (process/get_snapshot):
- k31: legit (serial AVL + bump allocator; huge, consistent margins).
- astra: legit-ish. Treap priority uses `countr_zero(key)` to exploit the documented even initial keys 2..2n, plus parlay parallel batch application.
- opus, glm, qwen: legit. process() waits for all published versions; get_snapshot blocks or returns published roots.
- muse, sol, wonder, glmf, k3, gemini-agy, terra: grep shows no caching, file access or timing tricks. Mixed serial and threaded designs.
Margins are large (scores 21.8–40.2 vs ref 8.5–12.6).

## Notes
- Beat spec v2 is dated 2026-10-07 (beat_spec.json comments). All formal runs date from Oct 8 onward, and the repo has only the initial commit, so there is no consistency issue. The glm other_run on 10-06 predates v2.
- gemini: agent_job_failed (exit 137), no submission.
