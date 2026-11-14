# Sphere and torus bodies and trimmed round histories

The typed BRep journal codec now reads, writes and independently authors closed sphere and ring-torus bodies. It also reconstructs complete trimmed histories that contain sphere and torus carriers. This entry extends the [round carrier research](FusionRoundCarrierResearch.md) with production codecs and native acceptance.

## Usage

`CreateRoundBody(Model, History, Stamp)` in `convert.formats.Fusion.BrepCodec.Journal.Round.CreateRoundBody` returns a complete `JournalModel`. `Model` is a `SphereBody` or a `TorusBody`. `History` gives the state identifiers and the next entity tag. `Stamp` gives the product, kernel version and date that the SMB header records. Emit the model with `EmitJournal` for an `.smbh` history and with `EmitStateSmb` for the current `.smb` geometry.

| Class | Fields | Constraint |
| --- | --- | --- |
| `SphereBody` | `RadiusMm`, `CenterMm`, `EntityTag` | Positive finite radius |
| `TorusBody` | `MajorRadiusMm`, `MinorRadiusMm`, `CenterMm`, `AxisVector`, `ReferenceAxis`, `EntityTag` | Ring torus: major radius greater than minor radius; orthogonal unit frame |

The authored body has one closed periodic face, one loop-free shell and one lump. It has no edges and no vertices. `ReadJournal` and `ReadGeometry` read the same sphere and torus nodes from native files. The field order follows the decoded native controls in the research entry.

## Semantic checks

The reader decodes the fixed sphere and torus field sequences. It rejects nonfinite values, a radius that is not positive, a horn or spindle torus, a non-unit axis and a non-perpendicular frame. Optional parameter bounds must be finite, and the V-reversal flag must be a Boolean.

A face without loops is admitted only on a sphere or torus carrier with no parameter bounds. That face must terminate its single-sided shell, and the shell must own it as its face list. A polygon-only Euler check cannot classify these bodies, because a closed periodic face has no edges and no vertices.

The trimmed history path is the general linear journal from the [document history entry](FusionDocumentGeometry.md) with these carriers added. It keeps every active and archived record and every state.

## Limits

- Horn, spindle and self-intersecting tori are rejected.
- A negative stored radius is rejected. The qualified reader and writer admit positive radii only.
- Authored round bodies are direct-design bodies. No parametric feature history is synthesized for them.
- Trimmed histories are reconstructed from typed source state. Arbitrary new fillet or sweep features are not authored.

## Verification evidence

[Native acceptance](../../../../re/Fusion/LocalOracle/RoundBodies/NativeAcceptance.json), SHA-256 `7ce52b6fd762408fd9aa0fe98380ad9cd4e223588c26882ef1e285c0c6025b9f`, has status `accepted` in Fusion 2706.1.17. Zero documents remained open.

| Group | Cases | Native checks |
| --- | --- | --- |
| Source-free authored bodies | Sphere r 19 mm, torus 31/9 mm, tilted torus axis (0, 0.6, 0.8) | Temporary BRep import, persisted body, analytic surface type, save and reopen |
| Re-emitted native carriers | Sphere, torus, tilted torus, placed torus | Byte-exact `.smb` regeneration, body equality with the native control, save and reopen |
| Trimmed histories | Pipe partial closed, composite circular pipe, rule-all-rounds fillets | Every rollback marker, rebuild, driving-parameter edit, save and reopen, equal to the control |

The authored sphere volume is 28.73091201462985 cm³ and its area is 45.36459791783661 cm². These equal 4/3·π·r³ and 4·π·r² for r = 1.9 cm. Each authored torus has volume 49.56515330227076 cm³ and area 110.14478511615724 cm². These equal 2·π²·R·r² and 4·π²·R·r for R = 3.1 cm and r = 0.9 cm. Fusion reported `adsk::core::Sphere` and `adsk::core::Torus` surfaces.

The history edits changed `d3` to 8 mm and 6 mm in the two pipe documents and `d7` to 0.8 mm in the fillet document. Volumes changed from 3.46423114478236 to 6.158633146279758 cm³, from 1.166559470517908 to 2.6247588086652924 cm³, and from 37.96633332328521 to 37.97836761590841 cm³. Control and re-emitted archives gave equal observations at each stage. The fillet history has 454 records, 359 active, and four states.

[Standalone](../../../../re/Fusion/LocalOracle/RoundBodies/PreparationStandalone.json), [geometry](../../../../re/Fusion/LocalOracle/RoundBodies/PreparationGeometry.json) and [history](../../../../re/Fusion/LocalOracle/RoundBodies/PreparationHistories.json) preparation reports bind every input and output hash. [The preparation script](../../../../re/Fusion/Reconstruction/RoundBodies/PrepareProduction.py) uses the production modules only.

Remote integration cases cover authored round bodies, byte-exact current geometry in natural and reordered allocation, and the three trimmed histories. Local tests did not run. Black, Ruff, Mypy, Pyright and steering checks passed.
