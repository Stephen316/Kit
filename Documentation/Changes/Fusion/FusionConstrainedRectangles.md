# Fully constrained dimensioned rectangles and cuboids

`DocumentSpec.ConstrainRectangle=True` adds a fixed lower-left corner, two horizontal and two vertical geometric constraints, and two driving sketch dimensions to the `rectangle` and `cuboid` profiles. The default remains `False`, preserving the original free-geometry rectangle behavior. This option is rejected for the circular, parameter-only and tapered profiles.

## Usage

```python
from pathlib import Path

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec

Specification = DocumentSpec(
    "Dimension driven cuboid",
    "boxHeight",
    31.0,
    ProfileKind="cuboid",
    WidthMm=17.0,
    DepthMm=23.0,
    ConstrainRectangle=True,
    WidthParamName="boxWidth",
    DepthParamName="boxDepth",
)
Path("DimensionedCuboid.f3d").write_bytes(EmitDocument(Specification))
```

`WidthParamName` and `DepthParamName` default to `rectangleWidth` and `rectangleDepth`. They and the existing height parameter name must be distinct ASCII identifiers when constraints are enabled. The generated parameter names `d1` through `d7` are reserved in this profile. Width, depth and height use millimetres. Use `ProfileKind="rectangle"` for the fully constrained sketch without a solid; its existing height user parameter remains present but does not drive the sketch.

Width and depth each have a named user parameter and a separate model parameter whose expression refers to that name. Width and depth each also have a `DcDoubleParameter` binding and an update node. Model parameter names and creation indices derive from the existing parameter table watermark. The accepted sketch uses `d4`/`d5`. The cuboid uses `d6`/`d7` because `d2`/`d3` already belong to its extrusion. Callers should edit the specified user names rather than assuming a fixed model parameter number.

## Persistent model

Four fresh `SketchGeomConstraint` entities use horizontal type 64 and vertical type 128. Each references its owning sketch and one line and subscribes to that line. The lower-left rectangle point has `isFixed=True`; it remains distinct from the sketch's separate origin point. The other persistent corner flags retain their qualified values. The native solver determines the sketch's fully constrained state.

Each dimension has a primary `FusionSketchLinearDim → SketchDimension` chain and a `Dimension → CommonBaseEntity → ManagedEntity` continuation. It references ordered point identities, uses uint64 horizontal/vertical dimension types, and stores typed annotation points, plane, text, length, color and reference positions. Its binding has a separate ManagedEntity continuation. The writer constructs both dimension objects and their complete parameter, membership, update, compute-order and reciprocal dependency graphs.

Observer indices are allocated separately for each observed entity. The first two settings observers belong to the new dimensions; Browser construction starts after those entries. A shared corner receives distinct dimension slots. The ordinary extrusion's existing observer indices remain zero and one. No fixed native-capture slot offset, synthetic hidden entity, saved record or payload block is used.

Six additional class declarations are packaged as schema-only vocabulary. [VocabularyEvidence.json](../../../re/Fusion/Reconstruction/DimensionAuthoring/VocabularyEvidence.json) binds their native class versions, namespaces and schema sources. Annotation geometry, entity identities, parameter values, UUIDs, BRep history and material instances are constructed from the specification. Production code does not read the research capture or launch Fusion.

## Verification

[Fusion 2706.1.17 accepted both complete independently authored profiles](../../../re/Fusion/LocalOracle/DimensionAuthoring/NativeAcceptance.json). On initial open, each sketch reports one closed profile, exactly four orientation constraints, two linear dimensions and `isFullyConstrained=True`. Its starting corners are `(0,0)`, `(17,0)`, `(17,23)` and `(0,23)` mm.

Changing the width to 19 mm and depth to 29 mm keeps the lower-left corner at the origin. The standalone sketch retains its fully constrained state through recomputation and native save/reopen. The cuboid additionally passes rollback to sketch-only state, restoration, rebuild, a height edit from 31 to 37 mm, and save/reopen with healthy timeline features.

| Cuboid state              | Volume (cm³) | Mass at 2870 kg/m³ (kg) | Centre (cm)        |
| ------------------------- | -----------: | ----------------------: | ------------------ |
| Initial 17 × 23 × 31 mm   |       12.121 |              0.03478727 | (0.85, 1.15, 1.55) |
| Width 19 mm               |       13.547 |              0.03887989 | (0.95, 1.15, 1.55) |
| Depth 29 mm               |       17.081 |              0.04902247 | (0.95, 1.45, 1.55) |
| Height 37 mm and reopened |       20.387 |              0.05851069 | (0.95, 1.45, 1.85) |

The body retains six faces, twelve edges and eight vertices, together with its independently authored material. Acceptance left zero documents open. Source hashes are `4fbcc6e18301a5c4cbcc9ec06aa422afe75dfdffa67f04938ef9f8efa054c627` for the rectangle and `dd8d4197f480115091378bbf90df1a8179bee47e1cba20339f172594e73bd41d` for the cuboid. The native report SHA-256 is `5c12267d16de40211b1283222d2c55a06e6600d6beec8af5c9335fa72dbc99a1`.

The public `ReadDocument`/`EmitParsed` path reconstructs both complete accepted archives byte-for-byte. For the rectangle, the path reconstructs 57,994 bytes and 203 entity records. For the cuboid, the path reconstructs 113,517 bytes and 246 entity records, one body history and one material package. [TypedReemission.json](../../../re/Fusion/LocalOracle/DimensionAuthoring/TypedReemission.json) records matching source/output digests. Native acceptance therefore covers the exact reconstructed bytes.

Fourteen remote archive integration cases cover both profiles with and without constraints, dimension continuations and parameter joins, and fixed-corner semantics. The cases also cover settings and endpoint observer allocation, reciprocal dependency maps, full typed reconstruction and invalid selector/name/profile inputs. No local tests ran. Black, Ruff, strict Mypy, Pyright and repository steering passed all 27 changed or added authoring and integration Python modules.

This profile implements axis-aligned rectangular geometry with horizontal and vertical point-to-point dimensions. It does not add a general constraint solver, arbitrary polygons, reference dimensions, angular dimensions, coincident constraints or offset anchors. See the [fixed-corner gotcha](../../Gotchas/Conversion/Fusion/Sketch/RectangleDimensionsNeedAnchor.md), [native constraint model](../../../re/Fusion/Reconstruction/SketchConstraints/ConstraintModel.md), [dimension model](../../../re/Fusion/Reconstruction/SketchDimensions/DimensionModel.md) and [observer allocation evidence](../../../re/Fusion/Reconstruction/SketchDimensions/ObserverModel.md).
