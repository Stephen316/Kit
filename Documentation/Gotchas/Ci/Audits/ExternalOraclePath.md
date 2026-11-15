# External oracle paths still need containment

## Expectation

Rejecting a licensed module inside the repository might appear sufficient for an optional compatibility check.

## Actual behavior

The environment-selected path was resolved and read without a positive filesystem boundary.
The maximal Python scan treats environment variables as untrusted local inputs and reported that read.
The later digest assertion did not restrict which path could be opened.

## Resolution

Stage the authorized input in a task-owned directory beneath the operating system's temporary root.
Pass the selected path through `ResolveTemp` before strict existence checks or reads.
This checks lexical containment and resolves symlinks before enforcing canonical containment.
Retain the outside-repository assertion and manifest digest check.
Never put the licensed module into the checkout.

See the [original finding](https://github.com/TryUniCAD/Kit/actions/runs/43691519928/job/132743056786)
and [repair entry](../../../Changes/Ci/PostMergeAuditRepairs.md).
