# Diff breakdown CodeQL findings

PR #97 merged the diff breakdown without a merge-group run. The queue CodeQL
jobs then reported three findings on `main`. Every later candidate failed
`Analyze actions` and `Analyze python`, so the queue removed PRs #95 and #96.

## Behavior

- `RunContext.py` validates `GITHUB_REPOSITORY` without a regular
  expression. The value must have exactly one `/`, a non-empty owner and name,
  and only ASCII letters, digits, `_`, `.`, and `-`. The accepted values are
  unchanged.
- A pinned `actions/github-script` step appends `DiffBreakdownResults/Report.md`
  to the workflow summary when the report exists. The publish step no longer
  reads the file in shell.
- The runner budget step prints a fixed error when the budget marker exists.
  It does not print the marker file. The budget guard writes only a fixed
  message to that file.

The report, PR comment, artifact, runner budget, and job name are unchanged.

## Findings

From the [PR #96 candidate](https://github.com/TryUniCAD/Kit/actions/runs/43339811272):

- `py/polynomial-redos` at `RunContext.py:14`. The configuration uses
  `threat-models: local`, so environment variables are untrusted input.
- `actions/output-clobbering/high` at the publish and runner budget `run`
  blocks. The query flags a file-read command in a privileged `run` step,
  including `cat` redirected to the step summary or to standard error.

## Limits

The repository's CodeQL suites run only on merge-group candidates. PR CI does
not report these findings. The next queue run of this change gives the
verification.

## Verification

Zizmor, Prettier, Black, Ruff, Pyright, and repository-wide steering passed
locally. No CodeQL CLI was available locally, and no tests ran locally.
