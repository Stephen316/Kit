# Hosted discovery archive evidence gate

The existing Workflow Quality job now runs the saved-archive evidence commands in an isolated, locked Python 3.14 environment. The gate checks the full JSON report bytes against the independently verified report digests. Each command also verifies the pinned Git artifacts and checks its decoded fields against the source application's recorded observations.

| Source | Coverage |
| --- | --- |
| SOLIDWORKS P01 and P03 | Rectangle placement, directed perimeter, dimension and relation operands, profile return, signed boss depth and full resolved-list boundary |
| SOLIDWORKS P04 | Resolved rectangle, boss and cut history, selected cap and boundaries, signed cut extent, sketch dimensions and relation operands |
| Fusion P01 | Saved principal support, geometry, constraint operands and dimension bindings |
| Fusion P03 | Saved rectangle and the boss's selected perimeter |
| Fusion P04 | Both selected contours, the source edges of the 44 cut projection lines, and the center-offset operands and expressions |

The eight cases run before the existing native adapter compatibility tests on the same hosted job. A failed replay logs its command diagnostics. A changed result digest fails the case and reports the actual digest for investigation. Repeat the measurement comparison after an intentional change to the evidence before updating its digest. [Gate cases](../../../tests/Research/ArchiveEvidenceTests.py), [workflow](../../../.github/workflows/WorkflowQuality.yml)

The gate covers the pinned discovery captures. Fresh application acceptance and editable conversion retain their own verification requirements. The report digests were reproduced with the locked local Python 3.14 evidence commands. The first hosted run with this gate is pending.
