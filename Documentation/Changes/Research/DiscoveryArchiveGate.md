# Hosted discovery archive evidence gate

The existing Workflow Quality job now runs the saved-archive evidence commands in an isolated, locked Python 3.14 environment. The gate compares the full JSON reports after normalizing line endings to LF. Each command also verifies the pinned Git artifacts and checks its decoded fields against the source application's recorded observations.

| Source | Coverage |
| --- | --- |
| SOLIDWORKS P01 and P03 | Rectangle placement, directed perimeter, dimension and relation operands, profile return, signed boss depth and full resolved-list boundary |
| SOLIDWORKS P04 | Resolved rectangle, boss and cut history, selected cap and boundaries, signed cut extent, sketch dimensions and relation operands |
| Fusion P01 | Saved principal support, geometry, constraint operands and dimension bindings |
| Fusion P03 | Saved rectangle and the boss's selected perimeter |
| Fusion P04 | Both selected contours, the source edges of the 44 cut projection lines, the center-offset operands and expressions, and saved sketch-relation ownership |

The nine cases run before the existing native adapter compatibility tests on the same hosted job. A failed replay logs its command diagnostics. A changed result digest fails the case and reports the actual digest for investigation. Repeat the measurement comparison after an intentional change to the evidence before updating its digest. [Gate cases](../../../tests/Research/ArchiveEvidenceTests.py), [workflow](../../../.github/workflows/WorkflowQuality.yml)

The gate covers the pinned discovery captures. Fresh application acceptance and editable conversion retain their own verification requirements. All original eight cases passed on the normalized hosted rerun at `c7fd7e59`. Hosted verification of the ninth, Fusion P04 sketch relations, is pending. [Hosted run](https://github.com/TryUniCAD/Kit/actions/runs/43721778227/job/132835216149), [line-ending evidence](../../Gotchas/Research/Readers/ArchiveEvidenceLineEndings.md)
