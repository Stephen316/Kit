# Merge queue candidate validation

The initial PR 72 merge group surfaced three static-scan failures and a
suite compatibility failure. FreeCAD archive assembly now supplies its feature
emitters to the shared document builder, removing cyclic imports while retaining
the existing write and read-back behavior. SolidWorks axis selection takes
the three fields it uses, so its helper no longer imports the native operation
type. Scale comparison uses the existing XML serialization path.

Scorecard still audits both the repository and the exact candidate. It emits
JSON because the pinned CLI's SARIF formatter failed to create a report for
Binary-Artifacts. The job requires both reports to contain checks and verifies
the commit SHA in the candidate report.

The full queue suite uses Python 3.14 for the standard library's ZIP Zstandard
support, which is required by the checked-in Fusion fixtures. The package
minimum and the static type-check target remain Python 3.11.

The queue test job installs the locked project dev extra, including the
typing extensions used by the tests and the formatter imported by the
program generation check. Scanner tooling keeps its existing
separate environments. Installing the scanner group in the Python 3.14 test
job previously attempted to build a scanner dependency from source and failed
[before pytest ran](https://github.com/TryUniCAD/Kit/actions/runs/43161600774/job/130993867779).

The [prior merge-group run](https://github.com/TryUniCAD/Kit/actions/runs/43155805818)
recorded these failures. The GitHub checks for the revised candidate provide the
end-to-end verification. No tests ran locally.
