# Research harness steering scope

## Expectation

The repository exempts files under `re/` from code standards.
An archive verifier launched from that tree can appear to share its exemption with its process harness.

## Actual behavior

Harnesses under `tests/Research/` follow the normal repository standards.
The [hosted steering report](https://github.com/TryUniCAD/Kit/actions/runs/43918468820/job/133478955245) rejected two harness function names longer than fifteen letters.
The same report rejected a native reader declaration with thirty-one logical lines.
Passing archive comparisons do not satisfy these separate source checks.

## Workaround

Keep harness declaration names within the normal limits.
Preserve their subprocess calls, assertions and pinned evidence when renaming them.
Check explicit selectors before changing a collected name.
Move an independent projection sequence into a named declaration when the reader exceeds its declaration limit.
Run the repository static policy checks before publication.
Keep process execution and test collection in remote CI.
