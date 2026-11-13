# Squash queue CI reuse

The merge queue now skips static checks that duplicate healthy PR CI when the
queue squashes a PR. Before this change, every merge group ran Ruff, Black,
Pyright, Mypy, Python steering, explicit imports, steering synchronization,
workflow pins, Zizmor, actionlint, and the CI policy suite again.

## Behavior

The reuse preflight finds the queued PRs in a candidate. It previously
required each PR head to be an ancestor of the candidate. The queue uses
`SQUASH`, so a candidate has the base commit as its only parent and never
contains the PR head. Every lookup returned `No matching queued PR heads`.

The preflight now also accepts the PR that the `merge_group.head_ref`
names. The ref has the form `gh-readonly-queue/<branch>/pr-<number>-<sha>`.
The branch must match the queue base. Ancestry still qualifies a PR for
merge-commit candidates.

All other reuse conditions are unchanged. The candidate tree must equal the
tested PR head tree. The group base must equal the base recorded in the PR
evidence, and the PR head must descend from that base. The PR must have
current healthy CI and a verified evidence artifact.

## Limits

- Path policies and rationale comments check a change range, so they always
  run on the candidate.
- The full test suite, CodeQL, and the security and SBOM scans run only in
  the queue. They are not duplicates and always run.
- A PR that is behind `main` produces a candidate tree that differs from its
  head tree. Its static checks run again on the candidate.
- A batched candidate contains several PRs. Its tree matches a PR head only if
  that PR already contains the earlier entries.
- Queue preflights load the verifier from the trusted base commit. The change
  applies to queue runs after it merges.

## Verification

The [PR #93 merge group](https://github.com/TryUniCAD/Kit/actions/runs/43329927148)
ran every static check again. Its squash candidate `a6817e8` had the same tree
(`d814498`) and base (`52dbbe5`) as the tested PR head `a5a9fd0`. The GitHub
compare API reported the PR head as `diverged` from the candidate. The PR
evidence artifact matched all other reuse conditions.

`tests/Policy/CiReportsTests.py` runs the preflight in a Node process with
API-shaped responses. It covers a squash candidate, a merge-commit candidate,
an unnamed PR, a ref for a different branch, a different tree, and a
different base. No tests ran locally. PR CI runs the policy suite.
