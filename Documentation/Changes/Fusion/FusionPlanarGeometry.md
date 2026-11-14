# Independent rectangular cuboid geometry

## Behavior

`GeometryCodec.Prism` independently serializes axis-aligned rectangular cuboids as SMT text or binary SMB.
The writer derives complete planar topology from dimensions and a base point.
It receives no source archive, geometry payload, donor records, or native CAD object.

The output contains one solid body with six planar faces, twelve straight edges, and eight vertices.
Twenty-four coedges connect the face loops through reciprocal edge partners.
Every vertex owns a separate point record.

The output is standalone geometry. It does not contain a Design graph, feature history, sketch links, or a complete F3D envelope.
The existing `BrepCodec` and `DocumentCodec` are unchanged by this addition.

## API and units

`CuboidBody(Width, Depth, Height, BasePoint)` uses millimetres throughout.
`BasePoint` is the minimum corner `(x, y, z)`.
The three lengths extend along positive X, Y, and Z respectively.

`EmitCuboidSmt(Model, Stamp)` and `EmitCuboidSmb(Model, Stamp)` return bytes.
`GeometryStamp` supplies printable product, version, and save-time provenance strings.
The geometry serializers do not choose the current time or inspect the filesystem.

```python
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody
from convert.formats.Fusion.GeometryCodec.Prism.EmitCuboidSmb import EmitCuboidSmb
from convert.formats.Fusion.GeometryCodec.Prism.EmitCuboidSmt import EmitCuboidSmt

Model = CuboidBody(17.5, 23.25, 8.75, (-12.5, 7.25, 3.5))
Stamp = GeometryStamp("Kit", "Independent rectangular cuboid", "2026-11-12T00:00:00Z")
BinaryData = EmitCuboidSmb(Model, Stamp)
TextData = EmitCuboidSmt(Model, Stamp)
```

This example documents the API; native acceptance used the separately recorded dimensions below.

SMT positions and straight-curve displacements use millimetres with the existing unit-factor-one header.
SMB positions and displacements use centimetres with the existing unit-factor-ten header.
Plane normals and plane reference vectors are dimensionless.

## Semantic topology

Corner numbers are three-bit coordinates: bit zero selects maximum X, bit one maximum Y, and bit two maximum Z.
Each unset axis bit produces one edge from that corner to the corner with the bit set.
This derives twelve unique edges without reading native record order.

The six face loops use these outward corner cycles:

| Face      | Corner cycle | Outward normal |
| --------- | ------------ | -------------- |
| Minimum Z | 0, 2, 3, 1   | `(0, 0, -1)`   |
| Maximum Z | 4, 5, 7, 6   | `(0, 0, 1)`    |
| Minimum Y | 0, 1, 5, 4   | `(0, -1, 0)`   |
| Maximum Y | 2, 6, 7, 3   | `(0, 1, 0)`    |
| Minimum X | 0, 4, 6, 2   | `(-1, 0, 0)`   |
| Maximum X | 1, 3, 7, 5   | `(1, 0, 0)`    |

Each face owns one loop containing four coedges.
The next and previous links wrap around that loop.
A coedge's partner uses the same edge in the opposite direction on its adjacent face.
The coedge sense compares its ordered corner pair with the edge's ordered endpoints.

Every edge has one incident coedge as its owner.
Every vertex has an incident edge as its owner and an endpoint selector matching that edge.
Selector zero refers to the start endpoint; selector one refers to the finish endpoint in this linear profile.
This does not reinterpret the separate closed-circle vertex-index variants.

Records are allocated in complete semantic groups:

| Ordinals | Entity family                 | Count |
| -------- | ----------------------------- | ----- |
| 0–3      | ASM header, body, lump, shell | 4     |
| 4–9      | Face                          | 6     |
| 10–15    | Loop                          | 6     |
| 16–39    | Coedge                        | 24    |
| 40–51    | Edge                          | 12    |
| 52–57    | Plane surface                 | 6     |
| 58–65    | Vertex                        | 8     |
| 66–77    | Straight curve                | 12    |
| 78–85    | Point                         | 8     |

The header declares two top-level roots, including the ASM header itself and the body.
The other eighty-four records are owned through explicit topology or geometry references.
Attribute heads and saved entity identities are absent because this profile supplies no corresponding application identities.
The writer does not invent color, DXID, feature-tag, sketch-link, or journal attributes.

## Curve and surface fields

Each straight curve uses the affine equation `C(u) = Start + u × (Finish − Start)`.
Its owning edge clips the curve at dimensionless parameters zero and one.
The carrier itself has absent lower and upper bounds, represented by `I I` in SMT.

The origin is a position token. The displacement is a vector token whose magnitude has length units.
It is not normalized. Both fields scale during the millimetre-to-centimetre conversion.
The edge parameters remain unchanged.
This explicit role distinction avoids inferring units from numeric magnitude or vector token type alone.

Each plane stores an origin at its first corner, its outward unit normal, and a perpendicular unit reference vector.
The V sense is forward. Both parameter directions have absent bounds.
All face senses are forward, and the face loops match those outward normals.
The straight boundary curves provide trimming, so this profile requires no stored pcurves.

## Limits

Lengths must be positive finite real numbers. Coordinates must be finite real numbers.
Boolean values, coordinate overflow, zero lengths after unit conversion, and coordinate-precision collapse are rejected.
The profile supports axis-aligned cuboids only.
Rotated boxes, bevels, fillets, cavities, sheet bodies, and parametric feature histories require other models.

Small geometry remains subject to the target kernel's tolerances.
Finite arithmetic and valid topology alone do not establish acceptance for every numerical magnitude.

## Evidence and verification

A controlled native capture produced a 12 × 18 × 24 mm cuboid at base `(20, -30, 5)`.
Fusion reported one solid, six faces, twelve edges, eight vertices, and volume `5.184 cm³`.
The [capture report](../../../re/Fusion/LocalOracle/Brep/CuboidCapture.json) records source hashes and geometry.
The native SMT shows unbounded straight carriers with non-unit direction magnitudes and reciprocal planar topology.
It served as semantic evidence only. The production writer neither reads nor copies that file.

The [independent preparation script](../../../re/Fusion/LocalOracle/PrepareCuboid.py) defines a different 17 × 23 × 31 mm cuboid at base `(-7, 13, 5)`.
Fusion 2706.1.17 accepted both production outputs, measured the expected `12.121 cm³` volume and translated bounds, and saved/reopened each as a native F3D. The [SMT report](../../../re/Fusion/LocalOracle/Brep/CuboidAcceptance.json) records output SHA-256 `b733961dd412d61fdc06650a3a69b04ae0ae0fe2b09e3bcb21840ce69c5ef89c`; the [SMB report](../../../re/Fusion/LocalOracle/Brep/CuboidBinaryAcceptance.json) records `a33e7a8acd2aed33aa44e34ee6e362010a1f16c1d60329b1143a7a92c0efd03b`. Both paths retain six faces, twelve edges, eight vertices, correct center and bounds after insertion into the native document and after reopening. Each session left zero documents open.

Integration cases write generated SMB files and cross the existing `ReadAsmTable`, shell, loop, edge, point, and plane-reader boundaries.
They check signed volume, translated bounds, face orientation, edge incidence, reciprocal loops, endpoint identities, and malformed trailing bytes.
The tests use three dimension sets and remain reserved for remote CI.

Mypy, Ruff, Pyright, and steering compliance passed for the 22 new production and integration Python files.
Pyright reported three existing unrecognized configuration settings and no code errors or warnings.
Native acceptance is established for the measured cuboid. Automated integration execution remains reserved for remote CI.

## Sources

The planar and straight-curve equations agree with the pinned [cadmpeg ASM specification](https://github.com/cadmpeg/cadmpeg/blob/de2726870ff728352163f601ab4e60bbd54fbade/docs/formats/asm.md), sections 5 and 6.
The specification is licensed CC BY 4.0 at commit `de2726870ff728352163f601ab4e60bbd54fbade`.
The production implementation was independently written from the typed semantic model.

See [analytic cylinder serialization](FusionAnalyticGeometry.md) for the shared token and header encoding.
