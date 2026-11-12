# README contract checks

The README gives the public conversion call and states that production conversion requires no CAD application.
The documentation check compares the listed read and write suffixes with the registered readers and writers.
This check includes Kit interchange JSON.
The CAD swap matrix checks every registered non-JSON read and write suffix.
The existing JSON interchange and CAD corpus checks still run in the full suite.

The [workflow quality job](../Reference/Operations/Testing.md#pr-and-queue-evidence) runs the README checks on PRs and pushes to `main`.
The complete suite still runs in the merge queue.
Registry agreement does not prove format coverage or vendor acceptance.

The [baseline replay](https://github.com/TryUniCAD/Kit/actions/runs/43175328820/job/131038081509) found two README-related failures on `0ac42013d`.
Remote CI verifies the repair.
