# Typed Fusion TSM control surfaces

Kit adds `ReadTspline(bytes)`, `EmitTspline(TsplineSurface)` and `MakeClosedCage(Vertices, Faces, Header=None, Orientation=None)` under `convert.formats.Fusion.TSplineCodec`.

The immutable model contains the cubic declaration profile, quad topology, native link orientation and valence offsets, weighted control points and primary/secondary grip ownership. The model also contains compound spoke layouts, edge end conditions, creased edges/vertices, smart grips and one planar symmetry. The writer derives text from these typed values without retaining source bytes or invoking Fusion.

`MakeClosedCage` authors a fresh closed quad cage from explicit vertices and oriented face loops. It allocates edges, links and roots independently. Coordinates follow the captured Fusion route: numeric grip coordinates are in centimeters even though the native TSM declaration says `units 1 meters`. Do not apply a scale conversion from that declaration alone.

## Orientation state

The three TSM root fields are evaluation state. The first vertex of each face loop is the face origin. `CageOrientation(Spokes, EdgeOrigins)` sets the other two explicitly. `Spokes[i]` is the neighbor vertex that the orientation link of vertex `i` points to. `EdgeOrigins` lists one directed `(start, end)` pair for each cage edge. Without `Orientation`, each vertex uses its first outgoing link in face order and each edge starts at its lower vertex index. A spoke to a non-neighbor, a missing or repeated edge, or a spoke list of the wrong length is rejected.

Two cages with identical control points, creases and face incidence can solve to different BRep numerics when these roots differ. The [orientation gotcha](../../../Gotchas/Conversion/Fusion/TSpline/RootLinksAreOrientation.md) gives the measured effect.

The qualified profile is `#TS0200`, cubic degree, `SUBD_CREASES`, `NURCCS`, behavior 14.2.0 and compatibility 13.3.0. The cap declaration can be `G0CAPS`, `G1CAPS`, or `G2CAPS`. Star smoothness can be 0, 1, or 2. The [cap declaration change](FusionCapDeclarationProfiles.md) records native acceptance for these profiles. New cages still default to `G1CAPS` and star value 0.

The codec admits unit knot intervals, zero boundary end conditions, valence 2–4, and the captured four-spoke compound layouts. Unknown records, high flag bits, deleted slots, radial/multiple symmetry, nonzero end conditions and unqualified declaration profiles are rejected. This component does not yet provide a general T-spline evaluator. [Form documents](FusionFormDocuments.md) supplies the complete F3D routing.

The [field model](../../../../re/Fusion/Reconstruction/TSpline/FieldModel.md) binds the grammar to controlled edits. It corrects three misleading structural interpretations: links store previous before next; `ec` stores an end-condition double; namespaces 100 and 50000 mean crease and smart-grip state. The crease contrast shows that namespace 100 holds the creased edges and that `ec` is not the crease set. The authored box, accepted by Fusion, follows the previous-before-next link order. The end-condition reading of `ec` and the smart-grip name of namespace 50000 came from binary inspection. They are not confirmed by a black-box experiment.

## Verification

[Native acceptance](../../../../re/Fusion/LocalOracle/TSplineCodec/NativeAcceptance.json), SHA-256 `c6f6973215fbb0f46cc454f2fc998132d988e2f76fc03ec002981e4c8551964d`, has status `accepted` in Fusion 2706.1.17. Zero documents remained open. The twelve native TSM controls and their typed re-emissions gave equal cage and solved-body observations. The observations were equal after form import, conversion, a control-point edit, native save and reopen. All twelve re-emissions are byte-identical, including the two-space pair separators in the `105a` symmetry-map records.

The source-free closed cage is a 17 × 23 × 31 mm box. It declares eight vertices, six oriented face loops, eight vertex spokes and twelve edge origins with no source TSM read. Fusion's own box primitive and the authored cage gave equal observations at every stage within 1e-8. Both solved to area 12.710567668877099 cm² initially. After the edit, both had area 12.43421957296201 cm² and volume 3.8361736781260087 cm³, and both kept these values after save and reopen.

[Root](../../../../re/Fusion/LocalOracle/TSplineCodec/RootVariants/Capture.json) and [edge](../../../../re/Fusion/LocalOracle/TSplineCodec/EdgeVariants/Capture.json) experiments isolate the orientation fields. The [preparation script](../../../../re/Fusion/Reconstruction/TSpline/PrepareTsplines.py) generates the SHA-bound artifacts without source templates.

Black, Ruff, Mypy, Pyright and steering checks passed for the production and test modules. Remote integration cases cover twelve complete native TSM files, six malformed files, closed-cage authoring, orientation agreement with the native box primitive and four rejected orientations. No local tests ran.
