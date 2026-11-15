# Restore rationale comment enforcement

## Behavior

Every tracked, owned Python class, function, method, lambda statement, and module binding requires a rationale comment.
This includes asynchronous functions, nested functions, decorated definitions, compatibility aliases, and unchanged files.
Comments explain purpose in 5–25 lowercase words without punctuation.
Place one comment directly above the declaration or decorator stack, with a blank line before it.

The checker now reports missing comments instead of silently skipping uncommented declarations and aliases.
The full-tree command does not consult `SteeringBaseline.txt`.
The same PR backfills the missing comments throughout the owned Python sources.
Other explanatory comments and comment-oriented docstrings remain prohibited.

## CI and merge queue

The [rationale workflow](../../../.github/workflows/RationaleComments.yml) scans the complete tracked source tree on PRs, merge groups, and `main` pushes.
Its existing check name remains registered in the [CI allowlist](../../../.github/scripts/CiAllowlist.cjs) for both PR and queue aggregation.
The merge queue always executes this check on the candidate.
It cannot reuse a passing PR report to skip the scan.
The subsequent change-range check still rejects newly added explanatory comments.

The repository-root `re/` tree remains excluded.
Vendored `Parashell/` and `modules/` trees and externally supplied `examples/` trees retain their existing exclusions.
The convention applies to Python; it does not introduce a comment convention for other languages.

## Usage

Run the static policy command from the repository root:

```sh
uv run python -m tools.steering.CheckRationaleComments
```

`--root` selects another Git worktree.
Paired `--base` and `--head` flags retain the change-range diagnostic mode.
That diagnostic is supplementary; CI always runs the complete scan first.
Fix reported `RAT001` through `RAT004` violations at their source.
Do not add rationale failures to a baseline.

See the [rationale standard](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/RationaleComments.md),
[contribution guide](../../Reference/Overview/Contributing.md), and [merge queue guide](../../../MergeQueue.md).

## Verification

Source inspection identified 6,924 missing comments across 2,557 files before the backfill.
The initial inventory covered 3,768 owned Python files and excluded `re/`.
After the main update, the signature-row fixture helper also received its required rationale comment.
Process-level regression coverage exercises the command against real temporary Git repositories.
It covers missing declarations, aliases, nested scopes, lambdas, removal, unchanged debt, ignored baseline entries, and invalid rationale text.
No tests ran locally.
Remote PR results and configured reviewer evidence are recorded in the PR.
Merge-group acceptance remains deferred until an administrator authorizes queue enrollment.
