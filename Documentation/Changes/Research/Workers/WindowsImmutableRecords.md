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
