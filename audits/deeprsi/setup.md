# DeepRSI: evaluation setup audit

Sources:

- the per-trial records at `deeprsi.com/data/trial-viewer/<id>.jgz`, with fields `agent`, `agent_version`,
  `model_provider`, `reasoning_effort` and `final_metrics`
- per-step token counts in the trajectories (`metrics.prompt_tokens`), used to derive peak context and compactions
- the methodology post (2026-10-12)
- [Pi's model registry](https://pi.dev/models)
- each provider's model documentation

Budget for every attempt:

- 48 h of active work time, with auto-resume prompts identical for every model
- no network except the model route
- 1–2 GPUs (H200, B200 or RTX PRO 6000) or CPU only, fixed per task
- 16–32 CPUs and 64–256 GB RAM
- sandboxes rotate at 24 h, which kills running processes

| Entry | Model ID / snapshot | Harness and version | Reasoning effort | Max output tokens | Context window used | Temperature / sampling | Time, turn, and token budget | Tools and network | Retry and refusal policy | Attempts per task | Non-voluntary terminations | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Fable 5.1 | `openrouter/anthropic/claude-fable-5.1` | Pi 0.85.1 | max (provider max) | undisclosed | peak 983k; 1.4 compactions/attempt | undisclosed | 48 h; tokens unlimited (mean $627/attempt) | bash, read, write, edit; no network | Auto-resume; "stalled" ends the trial (11 attempts, all ran ≥47.7 h) | 2 | 0 lost time | trial records |
| GPT-6 Astra | `azure-openai-responses/gpt-6-astra` | Pi 0.85.1 | max (provider max) | undisclosed | **peak 307k; 11.8 compactions/attempt. Pi registry: 272k for this route; native 1.05M** | undisclosed | 48 h (mean $404/attempt) | same | same | 2 (**18 of 30 re-run on Oct 9**) | 1 ArtifactCollectionError | trial records; pi.dev/models/azure/gpt-6-astra |
| Gemini 4 Argon | `openrouter/google/gemini-4-argon` | Pi 0.85.1 | high (provider max) | undisclosed | peak 1.04M; 1.6/attempt | undisclosed | 48 h; **run Oct 15–18, rated against the frozen field** | same | same | 2 | 0 | trial records |
| Gemini 3.8 Flash | `openrouter/google/gemini-3.8-flash` | Pi 0.85.1 | high (provider max) | undisclosed | peak 1.03M; 0.8/attempt | undisclosed | 48 h; **84 resume prompts/attempt on average (max 868)** | same | same | 2 | 4 ArtifactCollectionError | trial records |
| Kimi K3 | `openrouter/moonshotai/kimi-k3` | Pi 0.85.1 | max (provider max) | undisclosed | peak 1.03M; 0.2/attempt | undisclosed | 48 h | same | same | 2 (**1 excluded as "ungraded"**) | 1 ArtifactCollectionError | trial records |
| Grok 4.7 | `openrouter/x-ai/grok-4.7` | Pi 0.85.1 | xhigh (provider max) | undisclosed | peak 492k (native 500k); 3.6/attempt | undisclosed | 48 h | same | same | 2 (**2 FlashMLA excluded as "ungraded"**) | 1 ArtifactCollectionError | trial records |

## Questions answered

- [x] **Equal budgets?** Yes: 48 h and the same per-task hardware. Token spend is uncapped and varies 4.9× between
  models in mean cost per attempt.
- [x] **Same harness?** Yes, Pi 0.85.1 for every model. Its effect is not measured, and the methodology post lists
  native harnesses as future work.
- [ ] **Settings at provider max?** Reasoning effort is at the maximum for every model. **Context is not for GPT-6
  Astra**: capped at about 272k by Pi's default for the Azure route, against 1.05M native. Max output tokens are
  undisclosed.
- [x] **Same retry and refusal rules?** Yes, identical auto-resume prompts. Gemini 3.8 Flash needed far more of them.
- [x] **Silent model switches?** None observed; every step logs the same model.
- [x] **Non-voluntary terminations:** 22 "AgentContinuationStalledError" (Fable 11, Kimi 7, Grok 2, Flash 2) and
  7 "ArtifactCollectionError". All of these attempts ran at least 47.6 h and still received rewards.
- [ ] **Re-runs and replacements:** 18 of GPT-6 Astra's 30 attempts were re-run on Oct 9, 04:27–04:37, with no
  stated rule. The originals are unpublished and the re-runs lack reward breakdowns. Trial `ZDjKTPm`, cited in the
  methodology post, is not on the leaderboard.
- [x] **Same task version?** No version changes observed. Gemini 4 Argon ran 10 days later, against a frozen field.
- [x] **Attempts per task:** 2. The top-4 order is stable under bootstrap; the bottom two (Grok and Flash) are not.
- [x] **Modern harness?** Pi is a minimal, modern agent harness with shell and file tools. There is no retrieval and
  no network, which is reasonable for offline optimisation.
- [x] **Network?** None, so upstream answers cannot be fetched.
