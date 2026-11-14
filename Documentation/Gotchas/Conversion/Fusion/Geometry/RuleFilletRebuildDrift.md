# A rule fillet rebuild does not repeat its own values

## Expectation

Two rebuilds of the same unchanged history give equal body measurements. A re-emitted history can then be compared with its control at a tolerance of 1e-8.

## Actual behavior

The `rule_asymmetric.f3d` history has a rule fillet with `VBL_SURF` and `srf_srf_v_bl_spl_sur` surfaces. Fusion 2706.1.17 gave different values when it rebuilt the same control archive twice.

| Stage | Control area (cm²) | Repeated control area (cm²) | Re-emitted area (cm²) |
| --- | --- | --- | --- |
| Opened | 96.59656982755875 | 96.59656982755875 | 96.59656982755875 |
| Rebuilt | 96.59667252336087 | 96.60035244989258 | 96.59656982755875 |
| `d7` ×1.5 | 96.22611142112896 | 96.22611142112896 | 96.22362405332183 |
| Reopened | 96.22393775095281 | 96.22393775095281 | 96.2262602015179 |

The largest relative difference between the two control runs was 5.06e-5. Every rollback stage gave equal values in all three runs. The re-emitted `.smbh` and `.smb` members are byte-identical to the control members.

## Workaround

Run the control archive twice and measure its self drift. Accept a re-emitted history when structure, strings and integers are equal, and floats are within twice that drift. The re-emitted history had a relative drift of 4.24e-5. Use the strict tolerance of 1e-8 for the other fillet, loft and sweep histories.

## Evidence

- [Native acceptance](../../../../../re/Fusion/LocalOracle/ComplexGeometry/NativeAcceptance.json), entry `RuleFillet`
- [Acceptance script](../../../../../re/Fusion/LocalOracle/AcceptComplexGeometry.py)
- [Complex geometry change entry](../../../../Changes/Fusion/Geometry/FusionComplexGeometry.md)
