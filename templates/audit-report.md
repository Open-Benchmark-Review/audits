# <Benchmark name and version>: benchmark audit

| | |
| --- | --- |
| **Reviewed** | <YYYY-MM-DD> |
| **Benchmark creators** | <names> |
| **Version under review** | <repo commit, dataset revision, leaderboard snapshot date> |
| **Verdict** | **<Verified / Flawed / Not enough info>** |
| **Rubric** | [Epoch Rubric v1 + extensions](../../methodology/rubric.md) |
| **Review depth** | <Full / Partial: stopped once the threshold was crossed> |

## Summary

<What the benchmark measures, and how it is scored and reported. How
inspectable it is. The headline finding with its number, for example "X of N
tasks (Y%) contain scoring defects". The verdict in one sentence.>

## Methodology

<What we inspected: tasks, scorers, run logs, issues. Sampling, per the rubric.
What we reproduced, if anything. What we could not inspect.>

## Representative errors

<For each error class: a short definition, then one or two concrete examples
with file and line, trace, or issue links.>

- **<Error class>:** <description>. In `<task>`, <concrete example>.

<Setup, elicitation, or bias findings that fall outside scoring also go here,
as Terminal-Bench 4's review did for non-voluntary termination and scaffold
asymmetry.>

## Errors

| Task | Error type | Evidence |
| --- | --- | --- |
| `<task>` | <FN / FP / IMPOSSIBLE / CONSTRUCT> | <link or path:line> |

**Total:** <n> of <N> inspected tasks (<pct>%). The Flawed threshold is 20%.

## Rubric

### 1. Reviewability

**Status:** <Full / Partial / Inadequate>

<Justification.>

### 2. Scoring

| Item | Status | Notes |
| --- | --- | --- |
| Task validity and scorer accuracy | <Pass / Flag / Not reviewed> | <n>/<N> tasks affected |
| Benchmark consistency | <Pass / Flag / Not reviewed> | |
| Elicitation | <Pass / Flag / Not reviewed> | |
| Bias in evaluation setup | <Pass / Flag / Not reviewed> | |

### 3. Evaluation quality

| Question | Status | Notes |
| --- | --- | --- |
| Elicitation and resource adequacy | | |
| Scaffold fairness | | |
| Contamination | <% tasks public, % solutions public> | |
| Human completability | | |
| Score range | <floor, ceiling> | |
| Statistical adequacy | <runs/model> | |
| Construct validity | | |

## Limitations

<Caveats that did not cross a threshold. Anything not reviewed, and why.>

## Disclaimer

<Partial review or not. Developer contact status and a link to their
response, if any.>

## Notes

1. <footnotes and source links>
