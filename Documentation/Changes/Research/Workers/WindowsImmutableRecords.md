# Windows immutable application records

The research application dispatcher reads Windows installation and job records
through protected file and ancestor handles. This repairs a source-proven invalid
comparison between CPython 3.14.10 path and descriptor change-time fields. The
Windows output-intake reader uses the same shared-field comparison while keeping
its existing protected handles. Both readers retain descriptor change-time checks,
regular-file and single-link requirements, reparse rejection and restrictive
sharing. POSIX application reads retain their guards and use one final path
snapshot.

This uses the existing locked `pywin32==312` dependency and adds no configuration.
It changes file transport only: Fusion on Windows and SOLIDWORKS application
workers still park as unsupported. It provides no native CAD qualification.

See the [timestamp gotcha](../../../Gotchas/Research/Workers/WindowsPathAndHandleTimes.md)
for the pinned CPython and Windows API sources and actual failing Windows job.
New real-process cases live in `tests/Research/WindowsRecords`; the rewritten-file
case exercises both application reads and output intake. Existing output-intake
and application parking process cases must also pass on the repaired head.
Static checks run locally; actual Windows results remain pending remote CI.

The [pywin32 timestamp precision gotcha](../../../Gotchas/Research/Workers/PythonWinBasicTimePrecision.md)
explains the exact-second fixture baseline needed to prove a change-time-only
mutation independently of modification-time checks.

The [Windows gate at `2ff96767`](https://github.com/TryUniCAD/Kit/actions/runs/43676632437/job/132698100644)
passed twenty-one cases, including both application parking cases, output intake,
owner fencing, rewritten records, unsafe paths and the change-time-only mutation.
One sharing-fixture assertion failed because it required native error codes from
every Python file API. The [CRT sharing error gotcha](../../../Gotchas/Research/Workers/WindowsCrtSharingErrors.md)
records the pinned source distinction. The revised case logs each refusal, adds a
native write probe, and requires successful same-path controls after releasing
the protected reader. Its remote verification remains pending.
