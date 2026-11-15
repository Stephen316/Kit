# Fusion P03 signed-depth field search

The Stage 7 search uses eight Git-pinned Fusion P03 discovery captures from build `2706.1.17`. The original API observations give signed `AlongDistance` values for the named `BlindBoss`. The two baselines, independent width and height edits, YZ support and inch display all preserve +10 mm. The depth edit gives +12 mm and the direction edit gives −10 mm. The baseline B evidence comes from the rebuild before the repeated export. The remaining observations come from same-process reopen. [Automation plan](../../../Reference/Research/AutomationPlan.md), [Signed Boss evidence](../Readers/FusionBossDirectionEvidence.md)

```powershell
python -B re/automation/P03DepthSearch.py > FusionP03DepthSearch.json
```

The command runs with Python 3.14 or later for ZIP Zstandard support. It loads commit `89c25945f5833ad9c3a1c6c683df510b5702dd54`, checks the paired specification, receipt, roster, measurements and native file hashes, and records the measured depth and exact intended grid separately. The measurement for the 12 mm edit converts to `12.000000000000002` mm. Checking the raw reading against the specified length tolerance before searching from exactly 12 mm keeps integral unit hypotheses testable. [Search command](../../../../re/automation/P03DepthSearch.py)

The experiment selects typed `Parameter` and `DcDoubleParameter` record bodies from `BulkStream.dat` using the archived name, role, class, binding and Boss subject. It scans every byte position in each body. The 100 models combine f32, f64 and signed i16/i32/i64, both byte orders, metre/centimetre/millimetre/inch/micrometre scales and signed or magnitude-only values. Floating searches allow the two adjacent finite representable values. Candidate bytes must land at a common start-relative or end-relative position in every save. The existing reader field offsets and reciprocal ownership checks corroborate the result afterward.

| Typed body | Surviving model | Alignment |
| --- | --- | --- |
| `Parameter` | Signed little-endian f64 in centimetres | End −20. The start-relative position changes from +118 to +128 in the direction edit as its expression grows. |
| `DcDoubleParameter` | Signed little-endian f64 in centimetres | Start +21 and end −64 in every 85-byte body. |

In each window, 36 models cannot represent at least one exact grid value and 63 representable models lack predicted bytes in at least one capture. The −10 mm control refutes magnitude-only f64 centimetres. Big-endian f64 centimetres, little-endian f32 centimetres and little-endian i32 micrometres have no expected bytes in either window in any capture. Both surviving fields contain `000000000000f03f` at +10 mm, `343333333333f33f` at +12 mm and `000000000000f0bf` at −10 mm. The +12 mm encoding is one f64 step above 1.2 cm and agrees with the historical API measurement.

The Python 3.14.6 report SHA-256 is `beffd2fe7ad6fa085973ea65ab273b396083f74cf04f0ca6520bdb449ca44ac5` with UTF-8 and LF bytes. It binds receipt `f42a7e81b9ae108ba69d440ff411a8828dbc9ee0bbd54d6242c22370cf6560b8` and measurements `a21f81df15c4fd2afad5ed846b7a19c4f500b6dfea89f6fa7ede72985e4ed636`. Each record includes the body digest, range and matching stream position. Each rejected encoding lists the contradictory captures or unrepresentable inputs.

The field search and the shared inference runner use one finite adjacent-float routine. The scoped search retains its one-step rounding rule and the shared runner applies its declared tolerance. Replaying the archived Fusion P03 grid preserved the scoped report byte for byte. The shared assessment also matched its previous NumPy neighbor implementation byte for byte, with canonical SHA-256 `b144c09890bc8796982f7237fa0a811ccd9d3263f95fdc16506a06ccb0e800d5`.

This known-field commissioning run exercises Stage 7 search and the controlled refutation and provenance used in Stages 8–9. Both saved copies covary under all eight controls. Determining which copy governs rebuild would require independent evidence from a licensed reopen and rebuild with divergent copies, or a typed serializer and recompute path that establishes precedence. The claim is scoped to the two reached record types and this discovery grid.
