# Durable worker outputs

Research supervisor runners can declare files that must survive session cleanup.
The A03 controller accepts their bytes before the supervisor removes the session.
This implements an A08c prerequisite. It does not implement application dispatch
or qualify native CAD output.

## Runner contract

A successful runner may add `artifacts` to its existing result record:

```json
{
  "outcome": "completed",
  "reason": "capture saved",
  "records": {},
  "artifacts": {
    "native": {
      "path": "saved/part.native",
      "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
      "size_bytes": 123
    }
  }
}
```

Each path is relative to the session's private `work` directory. The manifest
permits 64 files and 256 MiB in aggregate. Paths must use relative slash-separated
components without traversal, stream syntax or Windows device names. The reader
rejects symbolic links, Windows reparse points, non-regular files, hardlinks and
multiple roles that identify the same file.

The controller copies from opened file handles into private staging objects. It
checks the actual size, SHA-256, and file identity before and after reading. It
checks the current lease after staging and immediately before publishing job
state. Invalid files produce a retry with a bounded diagnostic. Stale leases
publish no accepted result or output references. Content-addressed objects left
by a rolled-back transaction can remain unreferenced.

Accepted result records contain `output_artifacts_version: 1` and
`output_artifacts`, mapping each role to `sha256` and `size_bytes`. The nested
runner manifest also contains these durable references, without private paths.
The existing `artifact` operation retrieves the bytes by digest. Status and
dependency checks verify the referenced objects, including their declared sizes.
The controller does not create global input bindings.

## Controller adapters

An adapter must declare `OutputArtifactsVersion = 1` to accept this optional
runner field. The A03 adapter derives the output root from the supervisor finish
record and passes it to the research controller's `finish --output-root` option.
The controller requires the adjacent private `work` directory. Custom adapters
without the capability retain the existing result protocol; results that declare
artifacts are rejected before those adapters receive them.

On Windows, intake requires a local volume and the existing locked `pywin32`
dependency. Directory handles prevent write/delete sharing during traversal;
the final file handle prevents write/delete sharing during copying. Intake fails
closed when those handles cannot be acquired.

## Verification

`tests/Research/Outputs` adds real supervisor/controller process scenarios for
durability after cleanup, output corruption at dependency checks, unsafe files,
manifest limits, adapter capability and revoked leases. Local tests were not run.
The [Windows job at `ef431a17`](https://github.com/TryUniCAD/Kit/actions/runs/43668887044/job/132674284189)
reported three failed and eight passed process cases. The three failures exposed
an incorrect owner for the mandatory reparse-open flag. The repair uses the
`win32file` export proven by pinned pywin32 source. The successful later Windows checkpoint is recorded below; this failed
checkpoint did not qualify Windows intake.

The post-copy lease-expiry and concurrent-file-mutation rejection paths require
independent synchronized process evidence. This change does not claim those
branches were exercised. Licensed application capture/readback remains separate.

See [the intake gotcha](../../../Gotchas/Research/Workers/WorkerOutputsNeedIntake.md).
The [flag-owner gotcha](../../../Gotchas/Research/Workers/PythonWinReparseFlagOwner.md)
records the real Windows failure and source verification.

At source checkpoint `22a59e68c839354f3e6672eec6f67aa647aa1dce`, all five output-intake cases passed within the [Linux](https://github.com/TryUniCAD/Kit/actions/runs/43678423785/job/132703622509), [macOS](https://github.com/TryUniCAD/Kit/actions/runs/43678423785/job/132703622604) and [Windows](https://github.com/TryUniCAD/Kit/actions/runs/43678423785/job/132703622723) selections. This verifies the flag-owner repair and declared output lifecycle through real processes. It does not establish the independently synchronized branches or licensed application evidence identified above.
