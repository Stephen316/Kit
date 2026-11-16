# Missing rationale comments were silently skipped

## Expectation

The rationale workflow should reject every Python declaration without its required purpose comment.
A full-tree scan should include unchanged files and compatibility aliases.

## Observed behavior

`CheckReasons` skipped declarations when the preceding line did not start with a comment.
It also skipped alias bindings.
Consequently, deleting the entire comment could pass while editing an existing comment could fail.
The workflow compared only changed files, and its full-tree fallback subtracted accepted baseline entries.

## Resolution

The checker now validates every required site.
The workflow runs a complete tracked-source scan before its supplementary change-range check.
The full scan does not subtract a rationale baseline.
Keep `re/` excluded and fix missing comments in owned source files.

See the [restoration entry](../../Changes/Policy/RationaleCommentEnforcement.md) and
[checker](../../../tools/Steering/SteeringCompliance.py).
