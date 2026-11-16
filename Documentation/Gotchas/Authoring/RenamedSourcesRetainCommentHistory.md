# Renamed sources retain comment history

## Expectation

A file rename should preserve the distinction between existing comments and newly added explanatory comments.

## Actual behavior

The rationale range checker originally loaded base content from the destination path.
A renamed file had no base content there.
The checker could treat its historical explanatory comments as new additions.

## Workaround

The [rename loader](../../../tools/Policy/LoadRenameBases.py) reads Git rename pairs for the compared revisions.
The checker loads the base text from the original path.
It compares that text against the destination and still rejects newly added explanatory comments.
Rename detection remains a Git content-similarity decision.
An unrecognized move receives ordinary new-file validation.

See [the migration record](../../Changes/Policy/CodeDirectoryCasing.md) and [the rationale checker](../../../tools/Steering/CheckRationaleComments.py).
