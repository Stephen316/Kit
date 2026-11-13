# Diff breakdown reports

The `Pull request diff breakdown` workflow publishes an immutable analysis comment for each new PR head.
The report divides changed lines into Documentation, Reverse Engineering, Source, Tests, Tools, GitHub, and Agents categories.
Documentation and the `re/` research workspace use the `excluded` policy.
Their lines do not count as reviewable lines.
The [PR diff breakdown guide](../Reference/Operations/DiffBreakdown.md) describes the report, rules, and limits.

The engine adapts an existing diff breakdown implementation to Kit standards.
It uses PascalCase modules under `.github/scripts/DiffBreakdown/` and configuration under `.github/config/`.
Path rules use glob matching only, with no configured regular expressions.
GitHub API calls use the `gh` CLI.
The `Publish diff breakdown` job is registered in the CI allowlist for `pull_request_target`.

## Limits

The workflow uses `cancel-in-progress: false` without the larger concurrency queue.
The pinned workflow linter rejects the queue option.
GitHub can replace a pending run when several heads arrive during one run.
The newest head still receives a report.
The excluded policy reduces the review-size metric only.
It does not show that excluded changes are safe.

## Verification

Black, steering, path policy, rationale comment, and Ruff checks passed locally on the new Python files.
Pyright and Mypy passed on the new test module.
Their configured scope does not include `.github/scripts/`.
The pinned actionlint 1.7.12 with ShellCheck and Zizmor 1.32.0 in pedantic mode passed on the new and changed workflows.
Actionlint 1.7.12 reported `unexpected key "queue" for "concurrency" section` for the original queue option.

[DiffBreakdownTests.py](../../tests/Policy/DiffBreakdownTests.py) runs the engine against a temporary Git repository in PR CI.
The tests were not run locally under the repository test policy.
The publication workflow loads trusted base code, so it cannot run on the PR that adds it.
After merge, check that the next PR receives one collapsed report.
Confirm that Documentation and `re/` lines appear as excluded.
