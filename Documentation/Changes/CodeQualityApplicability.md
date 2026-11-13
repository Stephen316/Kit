# Applicable Code Quality checks in the PR aggregate

## Problem

`CI Agg` required three fixed GitHub-managed Code Quality jobs on every PR.
The names were `Analyze (python)`, `Analyze (java-kotlin)`, and `Analyze (javascript-typescript)`.
GitHub does not start Code Quality for every PR.
Fork PRs get no Code Quality run.
GitHub also changes the analyzed languages when the repository languages change.
A PR without those exact jobs kept the aggregate pending until its 80-minute deadline.
[PR #94](https://github.com/TryUniCAD/Kit/pull/94) is a fork PR with no Code Quality run.

## Change

The [CI allowlist](../../.github/scripts/CiAllowlist.cjs) no longer lists the Code Quality languages.
It matches each `Analyze (<language>)` job in the managed Code Quality run.
Each matched job must succeed, and the run must complete successfully.

The aggregate expects a Code Quality run only when both conditions are true:

- The PR head repository is the base repository.
- The PR changes a source file in a language that Code Quality analyzes.

The [CI reporter](../../.github/scripts/CiReports.cjs) reads the changed files through the pull request files API.
These extensions count as analyzed source: `.py`, `.pyi`, `.java`, `.kt`, `.kts`, `.js`, `.cjs`, `.mjs`, `.jsx`, `.ts`, `.cts`, `.mts`, `.tsx`, `.cs`, `.go`, and `.rb`.
A renamed file counts when its old or new name matches.
A truncated file list counts as analyzed source.

When the aggregate expects the run, a missing run keeps the aggregate pending as `Code Quality`.
An expected run without a matched job keeps the aggregate pending as `Code Quality analysis`.
When the aggregate does not expect the run, it still checks a run that GitHub reports.
A failed or pending matched job then fails or holds the aggregate.

## Limitations

The aggregate cannot detect a Code Quality run that GitHub starts after aggregation completes.
This applies only to PRs where the aggregate does not expect the run.
Merge-group aggregation is unchanged and does not include Code Quality.
The queue CodeQL jobs `Analyze actions` and `Analyze python` remain required on every candidate.

## Recorded verification

[`CiReportsTests.py`](../../tests/Policy/CiReportsTests.py) runs the aggregate as a Node process with recorded GitHub responses.
It covers a fork PR, a documentation-only PR, and a run with one language.
These cases must pass without the missing jobs.
The existing failed-job case still fails the aggregate.
[`ReviewerAggregationTests.py`](../../tests/Policy/ReviewerAggregationTests.py) covers two same-repository source PRs.
With no run, the aggregate must wait for `Code Quality`.
With a successful run and no `Analyze` job, the aggregate must wait for `Code Quality analysis`.
These tests run in remote PR CI. No local tests ran.
See [merge queue operations](../../MergeQueue.md) and [the Code Quality coverage gotcha](../Gotchas/Ci/CodeQualityRunCoverage.md).
