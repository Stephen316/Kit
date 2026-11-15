# Unicode paths during checkout changes

## Expectation

Untracked files might appear safe during a branch switch when Git reports no tracked modifications.

## Actual behavior

On this macOS checkout, Git reported accented CAD filenames as untracked while their normalized names also matched tracked paths.
Switching to the scrubbed tree removed those paths as part of moving the tracked examples directory.
The sixteen affected files were recovered from relocated copies with matching SHA-256 digests.
Every recorded untracked file matched its original digest after recovery.

## Workaround

Before switching a checkout with ambiguous Unicode paths, copy untracked files outside that checkout and record their digests.
Verify those files after the switch.
Restore missing files from verified copies without overwriting changed files.
Prefer an isolated worktree for repository edits.
Git documents its macOS Unicode handling through [`core.precomposeUnicode`](https://git-scm.com/docs/git-config#Documentation/git-config.txt-coreprecomposeUnicode).
