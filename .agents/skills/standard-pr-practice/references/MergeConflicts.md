<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Conflict follow-up

Read this when the task's opened PR becomes conflicting or an explicitly targeted existing Git operation needs completion. Keep working in the task's isolated worktree. Use [GithubCommands.md](GithubCommands.md) for exact target and verification queries.

## Verify a conflict exists before integrating

Refresh the open PR's head/base repositories, refs, and SHAs and fetch both exact remote refs. Verify current GitHub mergeability before starting a merge. `UNKNOWN`/`null` requires waiting and querying again; `BLOCKED` alone may mean checks or approvals, not textual conflicts.

If the current pair is conflict-free, make no merge commit or push just for this gate. Continue CI and review follow-up. This shortcut does not apply to a user-targeted interrupted operation that still needs completion, or to an independently evidenced requirement to update an out-of-date branch.

When conflicting, start from the verified PR head and integrate the freshly fetched base SHA with a reviewable stop before committing. Preserve published history with a merge, not a rebase requiring force-push. Record the head repository/ref as the only publish destination; local `codex/` worktree branch names need not match that destination.

## Resolve behavior and history together

Use `git ls-files --unmerged` to inventory all conflicts, including binary, rename, add/delete, and mode conflicts that have no text markers. Inspect ancestor/head/base versions, the commits introducing each change, callers, and relevant tests. Review automatic merges and reused `rerere` resolutions in integration paths too.

Preserve intended behavior from both revisions. Reconcile moved files, renamed APIs, imports, schemas, call sites, and tests coherently. Do not choose sides by hunk size or timestamp, apply blanket `ours`/`theirs`, or drop one side's feature. During rebase, `ours` denotes the rebased series and `theirs` the replayed commit; those labels do not identify the original PR branch as they do in an ordinary merge.

Resolve dependency manifests before regenerating lockfiles or derived output with pinned tools and documented commands. Reject unrelated upgrades/output drift. Preserve applied migration history, identifiers, snapshots, and ordering. Resolve CI configuration conflicts only when both sides' intended execution and gates can be preserved; weakening CI or review gates is never a conflict solution. For irreconcilable binary/submodule/product decisions, complete independent resolutions and report the exact decision that needs user input.

## Existing operations

Inspect `git status`, worktree metadata, original head, source commits, and staged content before continuing an explicitly targeted merge/rebase/cherry-pick. Discover metadata with `git rev-parse --git-path`; a worktree's `.git` can be a file. Leave unrelated operations alone in their original checkout.

Do not abort/restart the user's operation, begin a second merge inside it, or skip commits to make progress. If the user explicitly targets the operation and worktree, continue the same operation using its `--continue` after each resolution. Check that its final history can be pushed normally. A pre-existing rebase that requires force-push is a blocker; an explicitly local-only task stays unpublished.

## Publish and re-verify

Require no unmerged index entries or conflict markers introduced by the repair. Review staged changes against both parents and the PR's resulting three-dot diff. These are mechanical checks, not semantic proof; verify integration behavior through meaningful coverage and remote PR CI. Run permitted non-test validation only and do not claim unrun tests passed.

Stage only the resolution and necessary generated files. Keep both histories as parents of a conventional merge-resolution commit. Refetch head/base before publication; inspect and integrate concurrent head or base movement, then re-resolve and repeat affected validation. Review outgoing history to ensure only the target history, fetched base work, and this task's repairs are published.

Require the fetched remote head to be an ancestor of the candidate before normal publication. Push only to the verified PR head, with the user's required `--no-verify`, read back the accepted SHA, and request review with the `Comment` loaded from [ReviewBot.json](../ReviewBot.json) for the accepted head as described in [ReviewFindings.md](ReviewFindings.md). A protected push, missing write access, or required force-push is a blocker, never permission to bypass protections.

Refresh the PR and both remote refs after publication. Require an open unchanged target, an accepted head or an inspected successor containing the repair, and GitHub `MERGEABLE`/`mergeable: true` for the fresh pair. Wait responsively and retry on pending calculation; repeat resolution if a new pair conflicts. A local dry-run is supplementary evidence, not remote verification.

Inspect all CI and review evidence from the configured reviewer for the resulting revision, repairing defects caused by the integration. Conflict-free state alone is not green CI, a clean review from the configured reviewer, required approval, or queue readiness. Return to the combined completion gate before handoff.
