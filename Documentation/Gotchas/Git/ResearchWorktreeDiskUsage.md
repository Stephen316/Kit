# Research worktree disk usage

## Expectation

An isolated worktree shares Git objects, so creating it can appear to need little additional disk space.

## Actual behavior

The working files are separate copies.
The A08b worktree checkout failed with `No space left on device` while copying the native research corpus.
The failed checkout contained no implementation or user edits.
Git removed its incomplete worktree registration.

## Workaround

Preserve all existing worktrees.
Create the task worktree with `git worktree add --no-checkout` after verifying its permitted branch base.
Set sparse paths for the task's source, tests, documentation, and repository instructions.
Use `git read-tree -mu HEAD` to initialize its empty index and populate those paths.
Then integrate the verified PR head on the task branch.
An empty index after `--no-checkout` can otherwise appear as staged deletions and block that integration.
Expand the sparse paths when an implementation needs more source files.
This approach changes checkout scope without changing the tracked source or CI coverage.
