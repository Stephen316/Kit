# Historical scan paths use commit spelling

## Expectation

A source-directory rename might appear to require the same path change in every secret-scan exception and fingerprint.

## Actual behavior

A history scan evaluates each finding against its historical commit and path.
Renaming the current directory does not change that earlier path.
The path-policy migration changed `resolved` to `Resolved` inside an exception for commit `86ab1082`.
That commit still contains the lowercase directory.
Its previously classified Python expression stopped matching the exception.
The existing ignore fingerprint also carried a stale historical commit hash.

The [merge-group job](https://github.com/TryUniCAD/Kit/actions/runs/43821151397/job/133144280395) records the resulting failure.
See [the expression analysis](HistoricalCodeExpression.md) for evidence that `axis_kind=None` is source syntax.

## Workaround

Keep historical path constraints tied to the recorded commit's tree.
Use the exact commit, path, rule, and line fingerprint emitted by the scanner.
Update current-tree paths separately.
Do not broaden historical exceptions to whole files or commits.

The restored rule retains its conjunction of commit, anchored path, and anchored extracted value.
The existing scanner negative control and full history audit still run on the merge-group candidate.
No local tests or security scans ran for this repair.

See [the migration record](../../../Changes/Policy/CodeDirectoryCasing.md).
