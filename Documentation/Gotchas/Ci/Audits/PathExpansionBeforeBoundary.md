# Path expansion belongs after containment

## Expectation

Wrapping an expanded environment path in `ResolveTemp` might appear to place every filesystem operation behind the boundary.

## Observed behavior

The [maximal Python scan](https://github.com/TryUniCAD/Kit/actions/runs/43693180993/job/132748611779)
still reported path injection at the argument passed to `ResolveTemp`.
The argument called `Path.expanduser` on the untrusted environment value before containment validation.
The boundary cannot protect an operation that evaluates before the call receives its argument.

## Resolution

Pass the raw selection directly to `ResolveTemp`.
Apply strict existence checks and reads only to its validated return value.
Supply an absolute path beneath the operating system's temporary root instead of home-directory notation.
Keep the scanner's local threat model, path query, and failure gate enabled.

See the [repair entry](../../../Changes/Ci/PostMergeAuditRepairs.md).
