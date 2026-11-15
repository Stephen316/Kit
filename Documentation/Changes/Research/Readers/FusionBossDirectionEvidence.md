# Fusion P03 saved blind-boss direction

The P03 command compares saved extrusion controls and reciprocal `AlongDistance` bytes with the original Fusion API measurements. It reads the eight P03 discovery saves pinned at `89c25945f5833ad9c3a1c6c683df510b5702dd54` and checks the exact paired specification, recipe, capture receipt, measurement digest and variant roster. Run it with Python 3.14 or later for ZIP Zstandard support. [Evidence command](../../../../re/automation/FusionBossDirectionEvidence.py), [P03 source generator](../../../../re/automation/PairedCaptures/P03/GenerateFusion.py)

```powershell
python -B re/automation/FusionBossDirectionEvidence.py > FusionBossDirectionEvidence.json
```

Python 3.14.6 read all eight exact exports. Each contains one solid `BlindBoss` with New Body code `4`, one-sided mode `1`, Profile Plane start and Distance end code `1`. The stored vector matches the normal formed by the independently measured sketch axes. The signed distance is attached to `depth_mm` through a reciprocal parameter binding. With the archived sketch origin and centimeter-to-millimeter conversion, that signed distance gives the two independently measured solid bounds on the extrusion axis.

| Saved variants | Stored vector | Attached depth in cm | Historical world bounds on extrusion axis in mm |
| --- | --- | ---: | --- |
| Both baselines, width and height edits, inch display | `[0,0,1]` | `+1.0` | Z `[0,10]` |
| Boss-depth edit | `[0,0,1]` | `+1.2` | Z `[0,12]` |
| YZ | `[1,0,0]` | `+1.0` | X `[0,10]` |
| Negative direction | `[0,0,1]` | `−1.0` | Z `[−10,0]` |

The negative-direction save has SHA-256 `4cfc1e792d33d48e4b80f9829a4496cf70c2059378ce1b3cfa716b3a1c9e8aab`. Its distance bytes `000000000000f0bf` and expression `-( 10 mm )` agree with the historical API parameter. The baseline uses bytes `000000000000f03f` and expression `10 mm`. YZ changes the stored vector with the sign held positive. The inch save preserves the physical distance. [Direction in saved extrusion controls](../../../Gotchas/Research/FusionCutExtentControls.md)

The P03 receipt SHA-256 is `f42a7e81b9ae108ba69d440ff411a8828dbc9ee0bbd54d6242c22370cf6560b8` and the measurements SHA-256 is `a21f81df15c4fd2afad5ed846b7a19c4f500b6dfea89f6fa7ede72985e4ed636`. The observation labels distinguish same-process reopens and the rebuild before the baseline B export. P03 contains only blind cases. Fresh-process Fusion load, exact live sketch bindings, editable acceptance and through-all generalization remain open.
