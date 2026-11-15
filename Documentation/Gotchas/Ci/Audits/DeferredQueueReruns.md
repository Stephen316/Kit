# A PR rerun retains queue deferral

## Expectation

Rerunning a green PR workflow after a direct merge might appear to execute its skipped acceptance jobs.

## Actual behavior

The queue workflow uses the triggering event to select its validation phase.
The PR phase skips the suite and heavy security jobs.
Its green acceptance check confirms deferral only.
Rerunning that phase does not turn the event into a merge-group candidate.

## Resolution

Use a remote audit phase that executes the complete job set against an immutable source SHA.
Keep the original merged revision's results separate from any explicitly recorded repair revision.
Require fresh suite execution and a successful result from every security job.
Report the audit separately from native queue acceptance.

See the [pinned post-merge audit](../../../Changes/Ci/PostMergeQueueAudit.md).
