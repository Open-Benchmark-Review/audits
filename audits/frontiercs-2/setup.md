# FrontierCS 2: evaluation setup audit

Sources:

- `config/candidates.json` and `docs/candidates.md` at FrontierCS-2 commit `57b97dcb`
- Paper Table 4 (arXiv 2610.29932v1)
- The leaderboards on frontier-cs.org and Kaggle (both updated 2026-10-26)
- Raw model-request bodies in one trace per model from HF `FrontierCS2/FrontierCS-2-runs` @ `a3f6c3e2`, summarized by `scripts/req_settings.py`

Budget: every run gets 5 h of wall-clock answering time, no network except the
model route, and the same per-task CPU/GPU, train-call, and eval limits for
every model.

| Entry (HF id) | Harness and version | Reasoning effort, observed | Max output tokens, observed | Settings in repo/paper? | Attempts per task | Non-voluntary terminations, formal runs | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Opus 5.5 (`opus`) | Claude Code 2.1.296 | max (launch flag) | not recorded in the paper ("could not confirm") | yes | 1 | 1 evaluator error | Runs on a **subscription** (`apiKeySource: none`). The sampled trace shows 5-hour window utilization peaking at 0.57 with no throttling. On Progent, a refusal switched the rest of the run to **Claude Opus 4.8**. |
| Gemini 4 Argon, Antigravity (`gemini-agy`) | Antigravity CLI | high on main calls; side calls at minimal and low | 65,536 | **no**: not in `candidates.json` or the paper; added 2026-10-25 | 1 | 2 failed; 1 no final | **Kaggle's #2 row.** Refused requests are retried. In two tasks the retries ran out or summaries were truncated. |
| Gemini 4 Argon, Pi (`gemini`) | Pi 1.2.0 | high | rest of context (~1M) | yes | 1 | 4 no final (2 provider refusals, 2 resource limit); per the site, 10/48 runs had a content-filter refusal that ended Pi | The paper's entry. Kaggle lists it but doesn't rank it. |
| GPT-6 Astra (`astra`) | Codex CLI 0.162.1 | xhigh | not set | yes | 1 | 0 | |
| GPT-6.1 Sol (`sol`) | Codex CLI 0.162.1 | xhigh | not set | yes | 1 | 0 | |
| GPT-6.1 Terra (`terra`) | Codex CLI | xhigh | not set | **no**; added 2026-10-27 | 1 | 0 | On the site but not on Kaggle. |
| GLM 5.3 (`glm`) | ZCode 0.16.9 | max | 262,144 | yes | 1 | 1 | |
| GLM 5.3 Flash (`glmf`) | ZCode 0.16.9 | max | 262,144 | yes | 1 | 0 | |
| Kimi K3 (`k3`) | Kimi Code 0.31.0 | **high** | 131,072 | yes | 1 | 4 | The K3.1 Pro run in the same harness uses **max**. |
| Kimi K3.1 Pro (`k31`) | Kimi Code | max | 131,072 | **no**; added 2026-10-27 | 1 | 2 (infra; recovered) | On the site but not on Kaggle. |
| Muse Wonder 1.0 (`wonder`) | Muse Code 1.4.2 | max on main calls; side calls at low | 128,000 | yes | 1 | 0 | |
| Muse Spark 1.3 (`muse`) | Muse Code 1.4.2 | **high**; side calls at low and medium | 128,000 | yes | 1 | 0 | |
| DeepSeek V4.1 Flash (`ds`) | DeepSeek Harness 0.2.0-rc.2 | max | 262,144 | yes | 1 | 3 | |
| DeepSeek V4.1 Flash 1017 (`ds1017`) | DeepSeek Harness | max (trace) | 262,144 | **no**; added 2026-10-25 | 1 | 6 | Its parallel_dbscan PASS came from a memoization exploit; it was re-run on the fixed task (now FAIL). |
| Qwen 3.8 Max (`qwen`) | Qwen Code 0.25.0 | high; temperature 1 | not set | yes | 1 | 4 | |
| Step 5 Preview (`step`) | Step Code 0.1.0 | high | 64,000 | yes | 1 | 5 (3 timeouts) | |
| Kimi K2.7 (`k27`) | Kimi Code 0.31.0 | medium | up to 131,072 | yes | 1 | 9 (7 timeouts) | FCI zero point only; not ranked. |

## Checklist

- [x] **Equal budgets.** Yes: the same wall-clock time, compute, train calls, and eval limits for every model. Wall-clock limits favor faster APIs; this isn't measured.
- [ ] **Same harness for every entry?** **No.** Each model uses its own vendor's (or a third-party) harness, and the paper says so ("the harness is part of what we measure"). The harness effect is large and measured: the same Gemini 4 Argon passes 26/48 on Antigravity and 19/48 on Pi, with 8 vs 1 discordant tasks (exact McNemar p = 0.039).
- [ ] **Settings at max for every model?** **Not consistently.** Effort is max or xhigh for most models but `high` for Gemini 4 Argon (both harnesses), Kimi K3, Muse Spark 1.3, Qwen 3.8 Max, and Step 5 Preview. The paper doesn't say whether `high` is each provider's top setting. Kimi K3 (high) vs Kimi K3.1 Pro (max) in the same harness suggests a max setting existed for that family.
- [ ] **Same retry/refusal rules?** **No.** Antigravity retries refused requests; Pi ends the run. Claude Code falls back to a different model (Opus 4.8) after a refusal.
- [ ] **No silent model switch mid-run?** **No.** One Opus 5.5 run (Progent) finished on Opus 4.8.
- [x] **Non-voluntary terminations are low.** At most 6/48 per ranked entry, except Pi's provider refusals, which the site reports as 10/48.
- [ ] **One consistent rule for which run counts?** **Partly.** The accepted run is almost always the latest (229/236 records with several scored runs). There were 612 non-accepted runs, mostly batch reruns after mid-campaign task revisions. Their number is very uneven: 38–59 scored-and-discarded runs each for the first-evaluated models vs 0–3 for later entries.
- [ ] **All entries on the same task version?** **No.** See `report.md` (Benchmark consistency): on 5 tasks the leaderboard mixes runs from before and after a scorer fix.
- [ ] **Leaderboard gaps larger than the noise?** **No.** There is 1 attempt per task. Where the dataset holds more than one scored run of the same (task, model), 74/236 (31%) disagree on PASS/FAIL. The paper's own fit gives a run-effect SD of 2.04 logits (20 FCI points). #1 vs #2 is not distinguishable (6 vs 4 discordant tasks, p = 0.75).
- [x] **Modern harness.** Yes: current vendor CLIs with shell, file editing, and train-submit tools.
- [x] **Network access.** None from the agent sandbox (`network.allowed_domains: []` in every `policy.json`), so the agent can't fetch the upstream code.
