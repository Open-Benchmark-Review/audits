# Evaluation setup checklist

Fill in one row per leaderboard entry. Every cell needs a source: a config
file and line, a trace, or the leaderboard text. Write "undisclosed" when
there is none; that is itself a reviewability finding.

| Entry | Model ID / snapshot | Harness and version | Reasoning effort | Max output tokens | Context window used | Temperature / sampling | Time, turn, and token budget | Tools and network | Retry and refusal policy | Attempts per task | Non-voluntary terminations | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | | | | | | |

## Questions to answer

- [ ] Are budgets (time, tokens, cost, GPU) equal across entries, or deliberately normalized?
- [ ] Does every entry use the same harness? If not, is the harness effect measured, for example by running one model in two harnesses?
- [ ] Are settings at the provider's recommended or maximum level for every model, or are some under-configured (for example, a max-output-tokens setting left off)?
- [ ] Are retry and refusal rules the same for every entry?
- [ ] Does any run silently switch model mid-run, for example a fallback model after a refusal?
- [ ] What is the rate of non-voluntary termination (API errors, refusals, harness crashes, infrastructure failures) per entry?
- [ ] Were any runs re-run, re-scored, or replaced? Is the rule for which run counts stated and applied the same way to every entry?
- [ ] Are all entries on the same task version? Did the scorer or tasks change after some entries were run?
- [ ] How many attempts per task are there, and are the leaderboard gaps larger than the run-to-run noise?
- [ ] Is the harness modern and realistic: file editing, shell, test running, and retrieval appropriate to the task?
- [ ] Is web or network access allowed? If so, can the agent fetch the answer (for example, the upstream repo the task was derived from)?
