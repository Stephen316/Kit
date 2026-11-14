# Independent tapered circular extrusion documents

`DocumentSpec` adds the `frustum` profile and `TaperDegrees`, which defaults to zero. `EmitDocument` builds a complete native F3D from those semantic inputs. The F3D contains fresh Design, ACT and Browser graphs, a circular sketch and an ordinary extrusion feature with independent height and angle bindings. The F3D also contains a generated two-state BRep history, analytic mass-property cache, and a fresh physical material and appearance package.

The existing `extrusion` profile remains a cylinder. Nonzero `TaperDegrees` requires `ProfileKind="frustum"`; unsupported combinations fail before an archive is returned. Existing specifications retain their default behavior and positional field order.

## Usage

```python
from pathlib import Path

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec

Specification = DocumentSpec(
    "Independent expanding frustum",
    "frustumHeight",
    17.0,
    ProfileKind="frustum",
    RadiusMm=10.0,
    TaperDegrees=7.0,
    SketchName="Base circle",
    ExtrusionName="Tapered extrusion",
    BodyName="Frustum",
)
Path("Frustum.f3d").write_bytes(EmitDocument(Specification))
```

`RadiusMm` is the lower radius, `LengthMm` is the positive axial height, and the base lies at the origin with axis +Z. The upper radius is `RadiusMm + LengthMm * tan(radians(TaperDegrees))`. Positive angles expand the body; negative angles contract it. Both radii must remain finite, positive and distinguishable at the model's floating-point precision. Zero taper is the cylinder limit. Apex cones, hollow or thin extrusions, offset start planes, negative heights, arbitrary axes, later Draft features and multi-stage kernel journals are outside this profile.

The named user parameter drives extrusion height. The ordinary feature parameters `d2` and `d3` are the along-distance and taper-angle parameters. `d2` refers to the user parameter by expression. `d3` has a degree expression and degree display unit, while both its numeric value and its `DcDoubleParameter` binding store radians. These parameters remain editable in Fusion. The initial circular radius is geometry input, not an independently created driving sketch dimension.

`DocumentSpec.Material` uses the existing [fresh material specification](Materials/FusionAuthoredMaterials.md). Its density and appearance are independent inputs; no captured material instances or source archives are consulted.

## Model consistency

The Design extrusion, its profile and curve progenitor, the body and body progenitor, and the BRep tags share the same independently allocated identities. The generated history uses the qualified [frustum history codec](FusionTaperedHistory.md), including its cone carrier, circular trims, senses, topology, attributes and insertion journal. No saved body record or opaque history block is embedded.

Lower radius `a`, upper radius `b` and height `h` are in centimetres. For these values, the volume is `πh(a² + ab + b²)/3`, the area is `π(a² + b²) + π(a + b)hypot(h, b − a)`, and the centre height is `h(a² + 2ab + 3b²)/(4(a² + ab + b²))`. The mass cache stores geometric volume moments about the origin, before density multiplication. With `Q = h(a⁴ + a³b + a²b² + ab³ + b⁴)/5` and `Z = h³(a²/3 + a(b − a)/2 + (b − a)²/5)`, its diagonal moments are `π(Q/4 + Z)`, `π(Q/4 + Z)` and `πQ/2`. Off-diagonal terms vanish for this axis-centred profile.

The same semantic dimensions supply parameters, cache and history. Native recomputation therefore starts from a coherent persisted solid rather than a placeholder that becomes valid only after rebuilding.

## Verification

The [preparation generator](../../../re/Fusion/LocalOracle/TaperedAuthoring/PrepareCandidates.py) emits three complete files directly through the production API. The expanding file has 10 mm radius / 17 mm height / +7°, and the contracting file has 14 mm radius / 23 mm height / −5°. The third file is the 9 mm radius / 11 mm height / zero-angle limit. Each has a fresh material with density 2870 kg/m³ and RGBA `(0.2, 0.4, 0.6, 1)`. [Preparation.json](../../../re/Fusion/LocalOracle/TaperedAuthoring/Preparation.json) records source hashes, input specifications and expected physical properties. This generation is not itself native acceptance.

Twelve new remote archive integration cases cover complete author/read/reemit/reopen paths for all three taper signs, parameter-to-feature angle bindings and body/material references. The cases also cover cached properties against the controlled native taper, invalid angles, collapsed geometry and use with the wrong profile. No tests ran locally. Black, Ruff, strict Mypy, Pyright and repository steering passed all 19 changed or added Python modules.
Remote run [43239432056](https://github.com/TryUniCAD/Kit/actions/runs/43239432056) on revision `223781e4a066ef5cc3bcedb05cac61ca3868e738` passed all 897 compatibility cases in 54.96 seconds, including all twelve tapered-document cases.

[Fusion 2706.1.17 accepted all three complete independently authored files](../../../re/Fusion/LocalOracle/TaperedAuthoring/NativeAcceptance.json). Before recomputation, each had one solid, three faces, two edges, two vertices and two healthy timeline features. The acceptance measured geometry, volume, surface area, bounding box, centre of mass, density, material name and mass against the analytic specification. The acceptance also measured the full XYZ inertia tensor against that specification. All inertia components use relative tolerance `1e-7` and absolute tolerance `1e-8 kg·cm²`; the native approximation has small nonzero cross terms.

| Initial specification           |       Volume (cm³) |            Mass (kg) |      Centre Z (cm) |
| ------------------------------- | -----------------: | -------------------: | -----------------: |
| Radius 10 mm, height 17 mm, +7° |  6.533057919954655 | 0.018749876230269857 | 0.9033932075833666 |
| Radius 14 mm, height 23 mm, −5° | 12.224257804391037 |  0.03508361989860227 | 1.0907551947364311 |
| Radius 9 mm, height 11 mm, 0°   |  2.799159054348626 | 0.008033586485980557 | 0.5500000000000002 |

Each file rolled back to a sketch-only state, restored and rebuilt the same solid, and accepted a driving-height edit to 27 mm. Each file then accepted a taper edit to −3°. Native save and reopen retained the edited parameters, geometry, physical properties, material and healthy history. The acceptance left zero documents open.

The accepted source SHA-256 values are `d7a548387c6cc6583204937b9010ba5c7c5c4c5e239c15750cb62dcec4a1bbbe`, `7384dcc335a2263affe322338afa585e67be9604c228cc4e756255d47551ab03`, and `a533f88786f9a88fa561b30cdba654d1c7d520fdad1ffee8ee1e3ef2e8f472b1`, in table order. The report SHA-256 is `a0c3bdab656a3f0aa43fffac03755b4dbadb75398e171a260e33054be3105140`.

This proves the complete independent authoring boundary separately from the earlier source-specific BRep replacement acceptance. It qualifies these circular extrusion profiles and edits, not arbitrary Fusion features or geometry.

See the [angle-unit gotcha](../../Gotchas/Conversion/Fusion/Geometry/FusionTaperParameterUnits.md) and the [controlled tapered history model](../../../re/Fusion/Reconstruction/TaperedHistory/TaperedHistoryModel.md) for field-level evidence.

## Complete typed reconstruction

[TypedReemission.json](../../../re/Fusion/LocalOracle/TaperedAuthoring/TypedReemission.json) records full `ReadDocument`/`EmitParsed` reconstruction of all three accepted archives. Each contains three entity segments, 213 physical entity records, one complete history and one material package with nine schemas and four assets. All three output archives are byte-identical to their accepted inputs: 97,486 bytes for expansion, 97,496 for contraction and 97,486 for the cylinder limit. The nonzero-angle files use `FrustumHistory`; zero angle retains the qualified `HistoryModel` cylinder path. The identical hashes link the regenerated bytes directly to the native acceptance above.
