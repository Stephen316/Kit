# Independent rectangle and cuboid authoring

The native Fusion document writer adds two semantic profiles. The `rectangle` profile creates a closed four-line sketch. The `cuboid` profile adds an ordinary positive-Z solid extrusion with a driving height parameter. Both construct fresh Design, ACT, Browser, and container data. The cuboid history is independently generated from its dimensions, topology, tags, and history states.

## Usage

```python
from pathlib import Path

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec

Specification = DocumentSpec(
    "Independent cuboid",
    "boxHeight",
    31.0,
    ProfileKind="cuboid",
    WidthMm=17.0,
    DepthMm=23.0,
    SketchName="Authored Rectangle",
    ExtrusionName="Authored Cuboid Extrusion",
    BodyName="Authored Cuboid",
)
Path("Cuboid.f3d").write_bytes(EmitDocument(Specification))
```

Use `ProfileKind="rectangle"` to emit only the sketch. `WidthMm` and `DepthMm` are positive finite authoring inputs, defaulting to 40 and 30 mm. `LengthMm` remains the extrusion height and the value of the named user parameter. The original `parameter`, `circle`, and `extrusion` profiles retain their existing vocabulary and allocation order.

The rectangle starts at the origin in the XY plane. Its corners are `(0,0)`, `(width,0)`, `(width,depth)`, and `(0,depth)`, with four shared Point3D endpoints. By default, width and depth do not create driving sketch dimensions or geometric constraints. Closure comes from the shared endpoint identities; the origin point remains a separate fixed sketch-origin entity. The [opt-in constrained rectangle extension](FusionConstrainedRectangles.md) adds named driving dimensions, four orientation constraints and a fixed actual corner. See the [original sketch scope gotcha](../../Gotchas/Conversion/Fusion/Sketch/RectangleInputsAndDimensions.md).

## Semantic construction

The writer reuses the accepted document foundation, sketch plane, compute nodes, numeric parameter bindings, and minimal envelope. It adds Line3D version-2 declarations and qualified profile-edge callbacks through a schema-only rectangle vocabulary. No captured Design record, source archive, payload slice, native application, or research module is a runtime input.

Each line's carrier contains a start point and full displacement; its direction is normalized separately. Reciprocal CurveUses references join the two incident lines at each corner. The extrusion's region recipe contains the four independently allocated curve tags. Four curve progenitors carry explicit start/end-adjacent tag sets, and their identities join the generated side-face history tags. A separate body-progenitor identity joins the body's generic history tag.

The cuboid's six face tags, four bottom sketch links, carrier directions, and history states are supplied to `EmitPrismHist`. Bottom carriers follow the authored counterclockwise source curves. Volume, area, centre of gravity, and origin-based inertia cache values are calculated from the same dimensions used by the geometry writer.

`ReadDocument` and `EmitParsed` use the typed Design catalog and prism history model. Unsupported class versions, fields, parts, topology, or history forms retain their existing rejection behavior. The base rectangle profiles do not add arbitrary polygon, offset-plane, tapered-rectangle, thin-extrusion, Boolean-operation, or assembly authoring. Driving dimensions are available through the separately qualified constrained-rectangle option linked above.

## Evidence and verification

The [research plan](../../../re/Fusion/Reconstruction/RectangleAuthoring/AuthoringPlan.md) links the complete decoded control and every identity join. Its ordinary rectangle control has 303 physical Design records, four Line3D entities, shared corner points, and empty constraint/dimension collections. This is evidence for the model; it is not used as a writer template.

The new archive integration cases emit fresh 17×23×31 mm documents and reopen them through the public reader. The cases verify shared corners and carriers, inspect typed prism geometry/history, and reemit/reopen the complete model. They run remotely; no local tests were executed. Local Black, Ruff, Pyright, Mypy, steering, and diff checks passed.

The [acceptance generator](../../../re/Fusion/Reconstruction/RectangleAuthoring/Generate.py) prepares named rectangle and cuboid artifacts without a source archive.
[Fusion 2706.1.17 acceptance](../../../re/Fusion/LocalOracle/RectangleAuthoring/NativeAcceptance.json) passed for both profiles.
The sketch contains four lines, five points, one profile, and no dimensions or constraints.
The cuboid contains two healthy timeline features, one body, six faces, twelve edges, and eight vertices.

| Cuboid state                           | Volume (cm³) | Mass (kg) | Centre of mass (cm) |
| -------------------------------------- | -----------: | --------: | ------------------- |
| Initial 31 mm height, before recompute |       12.121 |  0.012121 | (0.85, 1.15, 1.55)  |
| Edited 37 mm height                    |       14.467 |  0.014467 | (0.85, 1.15, 1.85)  |
| Native save and reopen                 |       14.467 |  0.014467 | (0.85, 1.15, 1.85)  |

Rollback removed the body; restore and rebuild recovered the same solid.
The standalone rectangle also survived save/reopen and supported a subsequent native extrusion and height edit.
The cuboid uses the [independently authored material](Materials/FusionAuthoredMaterials.md) with density 1000 kg/m³.

Accepted cuboid source SHA-256: `9a8bef0ec7d6d0a9012bfb282da594baf3527076b40274a988068d62aa1ece41`.
Native saved SHA-256: `62c03b7aa11ce2c79193e51376e4405e6bbfd34aa5ab8097b72043ad49f38683`.
