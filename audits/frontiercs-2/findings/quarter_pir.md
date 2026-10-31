# quarter_pir

**Verdict:** `quarter_pir: OK / MINOR (UNCONFIRMED timing-gate FN for ds)`
Affected runs: none confirmed. ds possibly noise-decided (server_compute 3991/4000, end-to-end 3/4).

## How it's scored
`judge/beat_spec.json` `beats_reference` (conjunction):
- Per RPC query (4000 final): online bytes strictly < reference (exact integer accounting), and server time strictly < reference (median of 5 replays each).
- Per experiment (4 final: 2 seeds × N∈{2^16, 2^26}): preprocessing time <, end-to-end online time <, and client storage ≤ ref + 32,768 B (`judge/table2_metrics.py:19,215`).
- Plus a long list of validity checks: request = ReduceRequest(reference request), correct values, additional adversarial untimed queries, primary-hint audit, server replay.

## P(reference passes vs itself)
0. Byte equality fails the strict communication comparison on every query.

## Findings

### 1. Thresholds (OK)
- Communication is exact and deterministic. Timing gates are strict with no tolerance, but they're applied to 5-run medians.
- All 11 passing runs clear 4000/4000 server-time cells and 4/4 on every experiment metric, so their margins are large.
- Storage jitter (32 KB, about 1.5% at 2^16 and 0.04% at 2^26) is disclosed (`repo/README.md:186`), with an empirical reference spread of 19,344 B. That's too little to buy meaningful communication with storage.

### 2. Strict per-query timing for marginal candidates (UNCONFIRMED FN)
- ds fails 9/4000 server-time cells and 1/4 end-to-end cells, which looks like a candidate whose speedup is marginal on some queries.
- muse (3999/4000 time, but 0/4000 communication) and others fail for substantive reasons: k3 on storage, k27/qwen on communication at one DB size.
- No per-query timing data were inspected, so whether ds's misses are noise is UNCONFIRMED.

### 3. Hack surfaces checked
- Trusted harness: seeds, transport, clocks and value oracle are outside `quarter_pir/code/pir/`. A source policy bans package variables, cgo and unsafe; heap-measured storage is taken after a forced GC.
- Privacy is enforced mechanically: the server sees only ReduceRequest(reference request).

## Passing runs checked (11 PASS: astra, sol, glm, opus, wonder, glmf, gemini, ds1017, gemini-agy, terra, k31)
- All patches touch only `quarter_pir/code/pir/*.go`. Grep for `os.`, `ioutil`, `/tmp`, `/proc`, `syscall`, `exec`, `unsafe`, `runtime.`, `net.` and `reflect` found **nothing**.
- gemini-agy (top score 62.8) read in detail: ReduceRequest drops the 16-byte keys of superblocks whose parities the client stores, and offsets are bit-packed (9/14-bit). That's a genuine protocol/communication trade inside the storage allowance (passes storage 4/4).
- Verdict: **legit** (protocol engineering). Other passes spot-checked by file list and grep only.

## Notes
- The reference score (continuous, timing-derived) spans 24.3–29.3 across runs (sd 1.37), showing run-to-run machine variation of about 10–20% in timing-based quantities. But pass/fail uses paired same-evaluation comparisons.
- step: TIMED_OUT (agent deadline), infra/agent-side.
