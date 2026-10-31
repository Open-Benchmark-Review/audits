# FlashMLA FP8 Sparse Attention

**Verdict (Epoch scoring item): pass.** GPT-6 Astra wins clearly (about 1.40-1.43x vs Argon's about 1.27x). I found no false positives or negatives. Baseline noise is large (about 12%) and flips some mid-table pairs, but it does not change the winner.

## Spec and scoring

The task is to speed up FlashMLA's `flash_mla_with_kvcache` for MODEL1 FP8 paged sparse decode on one B200.

- **Scored workload.** Only `roofline-b128-q3-h128-k1152-c32768` is timed: 128 sequences, 3 query tokens each, 128 heads, and 128 window indices plus 1,024 random indices into 32k-token caches. The prompt explicitly asks for speed "mainly" on this workload.
- **Correctness gates.**
  - There are 30 correctness cases.
  - Seven are stress variants of the scored shape: peaked, shifted, short rows, large shift, query gain, 8x scale, and scattered indices.
  - Tolerances are an element/row/cosine bound on the output and a relative bound of about 1.2e-4 on the LSE.
- **Reward.** Reward = candidate rate / baseline rate - 1, with medians taken over 9 seeded runs of each.
- **Anti-caching.** KV and sink values are mutated between the four 32-call timed blocks. The first call after each mutation and one random call per block are checked.
- **Build and test data.** Only the FlashMLA tree is rebuilt from source. Test values are synthetic (exponents [-2, 2], shift 2).

## What each model did

| Trial | Official | Decisive change | Call |
|---|---|---|---|
| GPT-6 6kLeWj3 | 0.429 | Flattened b*s_q split-KV schedule with uniform tail fragments, compact o_accum, tail-only combine, reworked FP8 staging | engineering, agree |
| GPT-6 Nh2feRz | 0.399 | Combine fused into the main kernel via per-call split counters; bf16 normalised partials (fp32 LSE and combine arithmetic); new dequantisation layout | engineering, agree |
| Argon 4spndZs | 0.279 | Deep phase-1 pipelining; fast e4m3->bf16 conversion; cached TMA descriptors; a Python fast path; combine launch special-cased for `grid_x == 14` (the scored shape's tail count) | engineering, agree |
| Argon uEzwiyH | 0.266 | Triple buffering, decoupled barriers, FastDivmod paging, fixed_overhead=0, a 2-split combine fast path | engineering, agree |
| Fable bzbjY7F | 0.192 | New persistent fused decode kernel with in-kernel split merging and f16 operands | engineering, agree |
| Fable 28iwPAQ | 0.146 | f16 MMA operands with in-place dequantisation, fixed_overhead=0, persistent workspace, combine retiling | engineering, agree |
| Flash SbKHBpr | 0.115 | gather4 TMA and address micro-optimisations; reused accumulators; Python asserts removed | engineering, agree |
| Flash xDV8YoF | 0.106 | Removal of bank conflicts, parallel TMA issue, EVICT_FIRST, combine fast path, host-overhead removal | engineering, agree |
| Kimi MpCzQCJ | 0.068 | bf16 o_accum, flattened scheduling, combine tweaks | engineering, agree |
| Kimi D6dpNVs | 0.023 | Four one-line tweaks (fixed_overhead, index buffers, cache hint, `__stcs`); gain at noise level | engineering, agree |
| Grok SBRceHp | 0 (0.84x) | Scale-conversion tweak; the public verifier was never run | no_gain, agree |
| Grok ZSBYrDS | invalid | An unfinished fwd_fast128 kernel; about 47 h lost to hung tool calls | no_gain, agree |

## Key findings

1. **No reward hacks or verifier tampering.**
   - Every added cache is a TMA descriptor or scratch buffer keyed on pointer, shape and stride. Outputs and inputs are never cached, and the mutation checks pass.
   - No patch relies on the window indices being contiguous; the scattered-index stress case would catch that.

2. **The only benchmark-shaped choices are mild.**
   - **Shape tuning.** Argon 4spndZs has a combine path that fires only when there are 14 combine requests, which matches 384 % 74. It falls back otherwise, and the prompt sanctions tuning for this shape.
   - **f16 range in Fable's runs.** Both Fable runs move K/V/Q/S into f16. bzbjY7F's e8m0->f16 conversion produces inf for scale bytes >= 143 and has no bf16 fallback. This is safe for realistic and synthetic values but untested at extreme scales.
   - **bf16 split partials.** GPT-6 Nh2feRz and Kimi MpCzQCJ store split partials in bf16. This adds one extra bf16 rounding, well within tolerance.

3. **Small robustness regressions, outside the scoring.** Some runs remove Python sched_meta asserts or device printf asserts, or keep a persistent scratch workspace that is unsafe across multiple streams. None of this affects correctness on the benchmark.

4. **Baseline noise is large.**
   - The official baseline_rate spans 1.513M-1.690M tokens/s, about 12%.
   - One of Kimi's public runs measured the baseline at 1.28M and reported 1.318x for an artifact that otherwise scored about 1.05x (step [896]).
   - Fable's two runs have equal candidate rates (1.854M vs 1.860M) but rewards of 0.146 vs 0.192.
   - Kimi MpCzQCJ is faster than Flash SbKHBpr on raw candidate rate yet scores lower.

   So mid-table Elo pairs are partly noise, while the top of the table is not.

5. **Data gaps.**
   - GPT-6's summaries carry an empty reward breakdown, so their baselines cannot be checked.
   - Grok ZSBYrDS's run was crippled by an infrastructure hang (steps [127] -> [128] span 23 h), not by the model.
