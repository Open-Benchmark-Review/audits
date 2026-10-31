# Audit rubric

Our rubric is Epoch AI's Benchmark Review **Rubric v1**
(<https://epoch.ai/data/benchmark-reviews-documentation/methodology>), applied as
written, plus a small set of **extensions** (marked `[ext]`) for failure modes
that Rubric v1 does not name explicitly. Extensions never change the verdict
logic: a finding under an extension is filed under the Rubric v1 item it
ultimately affects (usually Scoring or Bias), and the report says so.

## Verdicts

| Verdict | Definition |
| --- | --- |
| **Verified** | Reviewability is Full or Partial, and no score-affecting defect (Section 2) crosses its threshold. Minor issues are logged as caveats. |
| **Flawed** | Reviewability is Full or Partial, and at least one Section 2 item crosses its threshold. |
| **Not enough info** | Required information is unavailable, so neither label can be supported. Give developers a week to offer private access before using this. |

## 1. Reviewability (gate)

| Level | Meaning | Next |
| --- | --- | --- |
| Full | All tasks and scoring logic are inspectable (publicly or under NDA), and every model's harness/API settings are disclosed: reasoning effort, token/time limits, tool access, system prompts | Section 2 |
| Partial | A representative sample of tasks and scoring logic is inspectable, and harness/API settings are fully disclosed | Section 2 |
| Inadequate | Inspectable tasks or scoring logic are limited, biased, or absent, or harness/API settings are undisclosed | Stop: Not enough info |

## 2. Scoring (minimum standard; failing any item means Flawed)

### 2a. Task validity and scorer accuracy

Each sampled task gets one or more of these classifications (see
`templates/task-log.csv`):

| Code | Meaning | Examples |
| --- | --- | --- |
| `IMPOSSIBLE` | Essentially impossible to answer correctly as written | Underspecified task, hidden requirement, missing file/tool, contradictory instructions |
| `FN` | False negative: correct work scored wrong | Overly strict scorer, stale or incorrect ground truth, dependence on live external state that drifts, sandbox or infrastructure failure the agent did not cause, measurement noise larger than the pass margin |
| `FP` | False positive: incorrect work scored right | Lax scorer, reward-hackable environment, answer readable from the harness, repo, or web, shortcut that bypasses the stated skill, measurement noise that lets a non-improvement pass |
| `CONSTRUCT` | Task egregiously fails to measure the claimed capability | |
| `OK` | No defect found | |
| `MINOR` | Defect found, but it cannot plausibly change the task's outcome | Logged as a caveat |

**Threshold:** Flawed if defects affect **≥20% of the total score in the
inspected sample**, or if one issue corrupts grading at scale.

- With equally weighted all-or-nothing tasks, this is ≥20% of tasks.
- With partial credit or unequal weights, it is ≥20% of the total possible score.
- For a single-task benchmark, it means defects could move the reported score by ≥20%.

**Sampling:** for more than 50 tasks, take 50 at random, stratified by
category. If the observed error rate is 15–25%, expand to 100. For 50 or
fewer tasks, assess all of them. Once the threshold is clearly crossed, the
review may stop and be published as a partial review; say so.

**Evidence standard:** every non-`OK` row cites concrete evidence: a file and
line in the benchmark, a reproduction, a trace excerpt, or an upstream issue.
A suspicion without evidence goes in the notes as `UNCONFIRMED` and does not
count toward the threshold.

`[ext]` **Check passing tasks, not only failing ones.** False negatives show up
in failing runs, but false positives (reward hacks, leaked answers, lax
checks) only show up in runs that pass. Inspect both.

`[ext]` **LLM-judge validity.** If any part of the score comes from a model
judge (or a committee of judges) rather than a deterministic check, verify:

- Agreement with human or ground-truth labels on a held-out set, reported and adequate.
- Self-preference: the judge is not the same model, or from the same family, as a graded model, or the bias was measured.
- Determinism: repeated judging of the same output gives the same score, within less than the leaderboard gaps.
- Aggregation: averaging or summing judge outputs onto a 0–100 scale preserves the ordering the ground truth implies.
- Score meaning: the scale is anchored to something (a pass threshold, a human baseline), not free-floating.

Failures here are filed as `FP`/`FN` under 2a, or as `CONSTRUCT`.

`[ext]` **Measurement noise in "beat the baseline" tasks.** When a pass
requires beating a reference on timing or other noisy metrics, check:

- Whether the reference passes against itself, and how often.
- Whether the pass margin is larger than the run-to-run variance.

A margin inside the noise band is `FP` when it lets the unimproved reference
pass, and `FN` when it fails genuine improvements.

### 2b. Benchmark consistency

**Examples:** scorer, instructions, or ground truth changed without a version
bump.

**Threshold:** Flawed if the leaderboard has incomparable results from
different versions.

### 2c. Elicitation

**Examples:** model elicitation is extremely constraining and is not the focus
of the benchmark:

- Under-resourced relative to task size: token, turn, or time limits, or sandbox resources
- Poor context management
- No agentic environment where one would be natural
- Excessive non-voluntary termination in agentic benchmarks: refusals, API errors, harness crashes

**Threshold:** Flawed if performance is substantially reduced compared with
reasonable alternatives for the tasks.

`[ext]` Check that each model runs with **sensible API settings**: context
window, max output tokens, reasoning effort, and temperature for reasoning
models. Check also that the harness is **modern and realistic**, with
reasonable tools and retrieval for the task.

### 2d. Bias in evaluation setup

**Examples:** uneven compute or token budgets, unfair scaffold choice (for
example, only some models are optimized), retry or refusal policy that differs
by model, a different number of attempts per model.

**Threshold:** Flawed if a material model-specific advantage is found.

## 3. Evaluation quality (recommended; not disqualifying)

| Question | Options |
| --- | --- |
| Elicitation and resource adequacy | Sufficient / Constraining / Unreasonably constraining / Unknown |
| Scaffold fairness: what scaffold does the leaderboard report? | Shared common / Mix of model-specific and common / Model-specific |
| Contamination evidence or risk | % of tasks public, % of solutions public as of the review date |
| Human completability assessed? | All tasks / Representative set / Poor implementation / Not established |
| Score range | Floor and ceiling |
| Statistical adequacy | Runs per model; at least 5 recommended for error bars |
| Construct validity | Measures / Partially measures / Does not measure the stated capabilities |

Where a credible external review exists, cite it instead of redoing its
findings.

## Process

1. **Scope.** Pin the exact version under review: commit, dataset revision, and leaderboard date. Record them in the report header.
2. **Sources.** Gather the paper, repo, leaderboard, run logs, issue tracker, and any prior external audits.
3. **Reviewability.** Rate it (Section 1). If Inadequate, contact the developers and wait a week.
4. **Setup audit.** Fill in `templates/setup-checklist.md` for every leaderboard entry. This feeds 2b, 2c, 2d, and Section 3.
5. **Task audit.** Sample per Section 2a and log each task in `task-log.csv` with evidence.
6. **Threshold check.** Compute the affected share of score. Stop early if it is clearly crossed.
7. **Report.** Write it from `templates/audit-report.md`. Include representative errors, the full error table, the rubric statuses, and the limitations.
8. **Developer notice.** Contact the benchmark developers before publishing, and link their response if they give one.
