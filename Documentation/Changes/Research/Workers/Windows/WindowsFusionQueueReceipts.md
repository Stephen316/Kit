# Windows Fusion queue receipts

The research Fusion phase queue supports durable receipt creation and recovery on Windows through its existing `--receipt` and `--recover-receipt` arguments.
Use an absolute path in an existing owner-private directory and the same supervisor configuration as the submitted pair.
The [durable receipt procedure](../FusionDurableQueueReceipt.md) retains the command and recovery contract.
The stdout-only mode remains available.

Windows persistence reuses the existing protected directory and file-record guards.
Receipt publication holds the checked ancestor chain while inspecting the target and exclusively creating a new record.
An existing receipt must contain the exact expected bytes; conflicting records are refused.
Receipt and intent reads retain the existing private-file, regular-file, single-link and reparse restrictions.
The POSIX custody path remains unchanged.

Every non-anchor path component must be an ordinary Windows name.
The guard rejects stream colons, control characters, wildcard/separator characters, trailing spaces or dots and reserved device names.
The [path-alias gotcha](../../../../Gotchas/Research/Workers/Windows/QueueReceiptAliases.md) explains the Python-version boundary and the explicit checks before the available reserved-name API.

Recovery reads the sealed sibling intent, verifies the exact committed job definitions and plan binding, and publishes only the matching receipt.
It needs no original plan path and submits no replacement pair.
Keep the original intent and run label when recovering an interrupted operation.
Queue persistence does not authorize native dispatch, alter resource availability, release quarantine or establish licensed Fusion acceptance.

## Verification evidence

The accepted implementation is recorded at `880bf0bed53f338933e819eb92b423670c8377d8`.
The dedicated Windows process coverage interrupts the real queue before submission and after commit, then checks recovery without the original plan, repeat recovery, unchanged ledger bytes and exactly the existing phase jobs.
It also exercises conflicting submissions and receipts, hardlinks, alternate streams, reserved device aliases and trailing-dot aliases.
The fixture retains an absent application endpoint and invokes no CAD API.

This documentation update received static formatting, path and whitespace checks.
No local queue, recovery, test, collection or native application execution was performed.
Hosted Windows process execution and native acceptance remain separate requirements; the earlier macOS receipt observation does not verify this Windows expansion.

[Implementation](../../../../../re/automation/ApplicationWorkers/FusionQueueReceipt.py), [process coverage](../../../../../tests/Research/WindowsRecords/FusionQueueReceiptTests.py)
