# Breaking change label checks

The breaking change label workflow uses a separate concurrency group for each PR event type.
An edit no longer displaces a run from opening, reopening, or updating the PR branch.
Running jobs finish when another event of the same type arrives.
The workflow retains its triggers, check name, and CI allowlist entry.

Use the existing breaking change markers in the PR title or description.
The workflow reads the current title, description, and labels from GitHub.
After a change to the label, it reads the PR again to check the result.
If the label does not match after three update attempts, the check fails.

GitHub can still replace a pending run when multiple events of the same type arrive.
The pinned workflow linter does not support [the larger queue option](https://github.com/rhysd/actionlint/issues/657).

## Verification and limits

[PR #78](https://github.com/TryUniCAD/Kit/pull/78) recorded a [cancelled job](https://github.com/TryUniCAD/Kit/actions/runs/43175011024/job/131037021398).
GitHub's job annotation identifies a higher priority request in the same concurrency group.
A [later job](https://github.com/TryUniCAD/Kit/actions/runs/43175024089/job/131037066982) passed on the same head.

GitHub uses the trusted base workflow for `pull_request_target`.
PR CI validates the edited workflow file before merge.
After merge, check that opening and editing a PR complete independently.
Confirm that the label matches the latest PR metadata.
