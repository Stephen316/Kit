# A degenerate edge has no curve

## Expectation

Every live edge points to a curve. A null curve slot looks like a broken reference.

## Actual behavior

Hole and loft-point members contain degenerate edges. Such an edge has a null curve, and its start vertex is also its end vertex. All 40 corpus records of this kind are plain `edge` records with the same field values.

| Field | Value in all 40 records |
| --- | --- |
| Start parameter | 1.0 |
| End parameter | 0.0 |
| Curve reference | Null |
| Reversed | `F` |
| Convexity | `unknown` |

The records occur in 33 members from the hole, hole placement, tapped hole, loft point, analytic and tool studies.

Each degenerate edge closes a cone face at its apex. A survey of every `.smb` and `.smbh` member under `re/` found 47 live records of this kind.

| Property | Value in all 47 live records |
| --- | --- |
| Vertex position | The cone apex, within 4.5e-16 cm |
| Coedge | One coedge, whose next and prior slots point to itself |
| Coedge partner and pcurve | Null |
| Face surface | `cone-surface` |

## Workaround

Accept a null curve on a live edge only when `IsApexEdge` matches the shape in both tables. Require a curve on every other live edge. Keep the parameters as stored, because the start parameter is larger than the end parameter.

## Evidence

Fusion 2706.1.17 reports the degenerate tapped-hole edge with a `None` geometry object. A native script must check `BRepEdge.geometry` before it reads `objectType`. The re-emitted tapped-hole archive equaled its native control within 1e-8 at every stage.

The reader coverage acceptance also opened a re-emitted hole document with an apex edge. It matched its native control through rollback, rebuild, save and reopen.

- [Corpus bounds summary](../../../../../re/Fusion/Reconstruction/ComplexGeometry/VerifyBounds.json)
- [Native acceptance](../../../../../re/Fusion/LocalOracle/ComplexGeometry/Bounds/NativeAcceptance.json)
- [Apex edge survey](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/ApexEdges.json)
- [Missing references](../../../../../re/Fusion/Reconstruction/ReaderCoverage/JournalStructure/MissingRefs.json)
- [Reader coverage acceptance](../../../../../re/Fusion/LocalOracle/ReaderCoverage/NativeAcceptance.json)
