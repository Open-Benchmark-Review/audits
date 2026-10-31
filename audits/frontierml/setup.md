# FrontierML: evaluation setup audit

Sources:

- per-trial records and trial pages on frontierml.org (`/data/trials/`, `/trials/<id>/`)
- full trajectories (`/trajectories/<run-id>.json`)
- [`induction-labs/frontier-ml`](https://github.com/induction-labs/frontier-ml) at commit `31837e0`
- the methodology post (2026-10-13)

Per-trial judgements cover the six models below. The other 13 models on the leaderboard (819 trials) are used only
for leaderboard-wide statistics.

Budget for every trial:

- 12 hours of agent time
- a compute wallet of $10, $50 or $200, spent through the Spin compute service; one trial per wallet, so three per
  task and model
- a 2-CPU sandbox with **internet access**
- a Hugging Face token: `FML_AGENT_HF_TOKEN`, else the operator's `HF_TOKEN` (`frontier_ml/harbor_plugin.py:521-526`)

Grading:

- per-task metric, linearly scaled between a floor and a ceiling and clamped to [0, 100]
- review by Claude Opus 5.5, which can zero a trial; it is told the agent's model name
  (`frontier_ml/review_trajectory.py:154`)

| Entry | Model ID / snapshot | Harness and version | Reasoning effort | Max output tokens | Context window used | Temperature / sampling | Time, turn, and token budget | Tools and network | Retry and refusal policy | Attempts per task | Non-voluntary terminations | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Opus 5.5 | `claude-opus-5-5` | Claude Code 2.1.282 (`--print`) | xhigh | undisclosed | not recorded | undisclosed | 12 h; mean 5.9 h used; mean wallet spend $56 | shell, files, web, sub-agents (5 used); internet + HF token | Claude Code exits when the model ends its turn | 3 (one per wallet); **5 re-runs** (4 at $200) | 0 | repo README; trajectories |
| Claude Fable 5.1 | `claude-fable-5-1` | Claude Code 2.1.282 | xhigh | undisclosed | not recorded | undisclosed | 12 h; 4.8 h used; $38 | same | same; one turn cut off by a safety classifier (`3jm1su`) | 3; 1 re-run | 1 safety-classifier cutoff | repo README; trajectories |
| GPT-6 Astra | `gpt-6-astra` | Codex CLI 0.157.0 (**wrapper unpublished**) | xhigh | undisclosed | not recorded | undisclosed | 12 h; 4.5 h used; $48 | shell, files, `view_image`; told "Do not spawn sub-agents unless the user… explicitly ask[s]" | wrapper resumes after a failed command (`submissions.py:3-6`) | 3; 1 re-run | 0 | trajectories |
| Gemini 4 Argon | `gemini-4-argon` | Antigravity CLI 1.2.11 (**unpublished**) | high (provider max) | undisclosed | 9 context-limit warnings | undisclosed | 12 h; **3.4 h used**; $20 | same | wrapper resumes | 3; **62 of 63 are re-runs** (`-r2`…`-r4`) | **332 `RESOURCE_EXHAUSTED` quota errors in 38 of 63 trials**; `sa323x` stopped at 62 min | trajectories |
| DeepSeek V4.1 Flash | `deepseek-v4-1-flash` | Claude Code 2.1.304 | max | undisclosed | 21 compactions | undisclosed | 12 h; 5.2 h used; $20 | same | Claude Code | 3; **21 trials graded with review skipped** (`FML_REVIEW_SKIP`) | 144 model-API errors across 32 trials | repo README; trajectories |
| Muse Wonder | `muse-wonder` | Muse Code 1.4.0 (**unpublished**) | max | undisclosed | not recorded | undisclosed | 12 h; 6.0 h used; $18 | same | wrapper resumes | 3; 3 re-runs | 0 | trajectories |

## Questions answered

- [x] **Equal budgets?** Yes: the same 12 h, wallets and sandbox for every model.
- [ ] **Same harness?** No. Each model runs in "the harness its developer used for agentic benchmarks on its model
  card". That is disclosed, but harness and model cannot be separated, and only Claude Code's settings are published.
- [x] **Settings at provider max?** The methodology post says each model gets the effort level "that provided the best
  score on other agentic benchmarks". Gemini's `high` is its maximum.
- [ ] **Same retry and refusal rules?** No. The Codex, Antigravity and Muse Code wrappers resume a session after a failed
  command; Claude Code exits when the model ends its turn.
- [x] **Silent model switches?** None observed.
- [ ] **Non-voluntary terminations:** Gemini 4 Argon was throttled by a provider quota in 38 of 63 trials and averaged
  3.4 of 12 hours. That plausibly deflates its scores; the size of the effect cannot be measured.
- [ ] **Re-runs:** 62 of 63 Argon trials, 5 of Opus's (4 at $200), 3 of Muse's and 1 each of Astra's and Fable's are
  re-runs. The originals are unpublished, and no rule is stated for which run counts.
- [ ] **Same task version?** Mostly. maple-vlm's floor was raised on 2026-10-07, after Opus, Fable and Astra had run;
  all trials are scored against the new floor. Opus `2zjl2r` received an older babylm prompt.
- [x] **Attempts per task:** one per model, task and wallet (Epoch recommends at least 5). Near-replicate pairs differ by
  a median 5.2 points.
- [x] **Modern harness?** Yes, vendor CLIs with shell, files and web.
- [ ] **Network, and can the agent fetch the answer?** **Yes.** Agents have internet and a Hugging Face token, and the
  held-out data for every task is in a public, ungated dataset (`inductionlabs/frontier-ml-tasks`, `<task>/private/`).
  Opus, Fable, Astra and Muse ran before the benchmark code was released (Oct 3–12); Argon (Oct 13) and DeepSeek
  (Oct 20) ran after it. DeepSeek `4ttc3o` found the repository and learned where the private split lives.
