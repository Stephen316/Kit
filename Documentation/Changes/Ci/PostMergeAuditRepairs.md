# Repair findings from the post-merge audit

## Behavior

The first complete audit of merged rationale revision `4b730a8ff92f2a63dfdf3c16566d835b79c04835`
reported two blocking security findings that its PR phase had deferred.
The original results remain visible in [the audit run](https://github.com/TryUniCAD/Kit/actions/runs/43691519928).

The raw optional signature-table compatibility input now passes directly through `ResolveTemp` before filesystem access.
Home-directory expansion is not performed before containment validation.
Its resolved path must remain inside the operating system's temporary root and outside the repository.
The existing manifest digest comparison still verifies the licensed module's identity.
Stage an authorized module in a task-owned temporary directory before setting `KIT_SOLIDWORKS_DLL`.
The recorded-format comparison remains available without that variable or vendor software.
See the [research artifact guide](../../Reference/Research/ResearchArtifacts.md).

The history scanner also identified an unquoted Python keyword argument in an old source revision.
A rule-specific exception requires all three conditions: the exact historical commit, exact source path,
and an extracted value equal to `axis_kind=None`.
It leaves every other finding in that commit and file subject to the original detection rules.
A scanner process probe requires the same source expression to remain detectable without that historical context.
The full-history scan, upstream default rules, and failure threshold remain enabled.

## Verification

The original audit collected 4,585 tests and scheduled all of them afresh across four shards.
Fifteen of its seventeen security checks passed; Python path analysis and the history secret scan failed.
The exact failures are [the input-path finding](https://github.com/TryUniCAD/Kit/actions/runs/43691519928/job/132743056786)
and [the historical expression](https://github.com/TryUniCAD/Kit/actions/runs/43691519928/job/132743056959).
The [first containment revision](https://github.com/TryUniCAD/Kit/actions/runs/43693180993/job/132748611779)
still expanded the untrusted path before the boundary; the final revision passes the raw string instead.

Compatibility subprocess cases cover an outside-root input, a symlink escape, and a temporary file with an incorrect digest.
These cases execute through the actual pytest compatibility command in remote CI.
No tests ran locally.
The repaired revision must pass a fresh complete audit before it can be reported green.

All seventeen security jobs subsequently passed on `0469a67989e505afe6ac4c3e1932ec267f4bcad5`.
Its full suite exposed the already documented aggregate startup race in one unchanged process probe.
The [pending probe repair](PendingAggregateProbe.md) synchronizes on the real pending message and retains its two-second liveness check.

See the [pinned audit](PostMergeQueueAudit.md),
[oracle boundary gotcha](../../Gotchas/Ci/Audits/ExternalOraclePath.md),
[path expansion gotcha](../../Gotchas/Ci/Audits/PathExpansionBeforeBoundary.md),
and [historical expression gotcha](../../Gotchas/Ci/Audits/HistoricalCodeExpression.md).
