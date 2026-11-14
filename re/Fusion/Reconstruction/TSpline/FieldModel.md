# Qualified TSM control-surface model

This model describes the complete `#TS0200` programs in twelve controlled Fusion 2706.1.17 exports: plane, closed box, symmetric box, native vertex edits, and a smooth → creased → uncreased edge contrast. It is a bounded TSM component model, not a claim that every T-spline feature, deleted-slot program, rational surface, or F3D Form graph is implemented.

The initial six TSM descriptions are byte-identical to their embedded F3D members. `ControlInventory.json` binds those archives and the corrected typed research models. `CreaseInventory.json` binds six further files to native control-vertex positions and creased-edge endpoint sets. Native API edge enumeration is independent of TSM edge allocation, so correspondence uses endpoint geometry, not equal integer indices. Coordinate comparisons round components to twelve decimal places in native centimeters.

## Primary evidence

The evidence is the TSM text that Fusion exported for the controls, Fusion's API view of the same bodies, controlled crease and orientation experiments, and Fusion accepting re-emitted and authored files. Earlier binary inspection of the T-spline library guided several field names. That evidence was removed. Claims that rest only on it say so below. No vendor library is executed by the production codec.

The pinned cadmpeg `crates/cadmpeg-codec-f3d/src/tsm.rs` was a structural research reference. Its `EditorSelectionKind` reading of namespace 100 is contradicted by the crease contrast below. Its link labels differ from the order used here, which Fusion accepted in an independently authored cage. Its namespace 50000 and `ec` integer-flags readings also differ from this model. Those two differences rest on earlier binary inspection and are not confirmed by a black-box experiment. Production implementation is independent Python and uses no imported upstream runtime, source cage, fixture, or vendor stream.

## Program and declaration framing

The program is ASCII whitespace-separated records. Table indices are implicit positions within each family. The qualified writer uses LF line endings and 18 significant decimal digits, preserving each decoded binary64 value without keeping lexical tokens.

The qualified declaration prefix is:

| Record | Semantic value |
| --- | --- |
| `#TS0200` | Format-family signature |
| `degree` | Cubic degree 3 |
| `cap-type` | `G1CAPS` cap rule |
| `star-smoothness` | Scalar 0 |
| `units` | Scale 1 and literal `meters` |
| `end-conditions` | `SUBD_CREASES` global rule |
| `star-knot-rule` | `NURCCS` star-knot rule |

The literal units record is retained. In these Fusion API captures, numeric primary grip coordinates equal native centimeter coordinates. Multiplying them by 100 because the text says `meters` would corrupt the model. Unit interpretation outside this exact Fusion route remains unqualified.

The suffix contains positive finite `tol` and `geom-tol`, nonnegative signed-32-range `ver`, `behavior-version 14.2.0` and `compat-version 13.3.0`. `ver` changes during ordinary edits and is a mutation counter, not the TSM schema number. The counter is retained independently; the writer does not derive it from topology cardinality.

## Topology

| Record | Fields in exact wire order | Notes |
| --- | --- | --- |
| `f` | origin link, hidden-face bit | The second field is 0 in every control. Its reading as a hidden-face bit is not confirmed by a black-box experiment |
| `e` | origin link, knot interval binary64 | Qualified captures use interval 1 |
| `v` | origin link, orientation direction | Observed directions are `NORTH`, `EAST`, `SOUTH` and `WEST` |
| `l` | **previous**, next, opposite, vertex, face, edge, valence offset | The authored cage uses this order, and Fusion accepted it as equal to its own primitive |
| `ec` | edge index, end-condition value | Every control writes 0. The binary64 type is not confirmed by a black-box experiment |

The final link word is 0, 1 or 2 in the controls. Its reading as a valence offset in the low two bits came from earlier binary inspection and is not confirmed. The codec rejects higher bits. The face word admits only 0 or 1. Face `-1` identifies a boundary halfedge. Other indices address live records only; deleted slots are unsupported.

The qualified profile requires quad face rings, reciprocal previous/next and opposite links, exactly two links per edge, complete face ownership, a single connected link fan at each vertex, valence 2–4, and matching opposite-edge endpoints. Every declared topology root is checked against its owner. Boundary edges have explicit zero-valued `ec` records. Nonzero end conditions and non-unit knot intervals remain unsupported.

`ec` is not the user crease set. Creasing one interior edge changes namespace 100 while leaving the `ec` records unchanged.

## Grips and compound layouts

`0g x y z weight` is a weighted control point of four binary64 values. The rule that a weight must be positive came from earlier binary inspection and is not confirmed by a black-box experiment. The codec preserves finite positive weights, including the native edited plane's `1.0000000000000002`; it does not round them to unity or normalize coordinates.

Without `0m odd-grip-map`, grip index equals vertex index. An explicit map has one `gvp vertex` or `gv vertex` row per grip. In every control, each live vertex has exactly one `gvp` row. Earlier binary inspection read `gvp` as the central or primary grip, not a selected grip. That reading is not confirmed by a black-box experiment.

`0m cg vertex count lengths... gripIndices...` describes compound grips around that vertex: a spoke count, the spoke lengths and the grip map. The field names came from earlier binary inspection. The qualified controls have four spokes, each length 0 or 1. In every control, the number of referenced grips is:

`sum(length[i] + length[i] * length[(i+1) % count])`

The codec preserves the ordered map. Each referenced grip is secondary and has the same vertex owner. Compound maps cover every secondary grip exactly once. General T-junction, absent-grip, multispan compound layouts and patch evaluation are outside this profile.

## Extension namespaces

| Namespace | Observed in | Qualified semantic model |
| --- | --- | --- |
| 100 | Plane and box controls; changes with the crease contrast | `100edges` creased-edge indices and `100verts` creased-vertex indices; preserve absent extension versus present empty sets |
| 105 | Symmetric box controls | One mode-0 plane symmetry with frame and six correspondence maps |
| 50000 | Plane controls; grows when an edge is creased | `50000grip index` ordered grip set. The name smart grip came from earlier binary inspection |
| 50001 | Not observed | Unsupported. Earlier binary inspection named it a separate freeze extension; that is not confirmed |

The crease contrast establishes native Box edge count 0→1→0 and Plane count 10→11→10. Box serialization gains edge 18; plane gains edge 12. The plane gains four secondary `50000grip` entries and compound layouts at vertices 4 and 7, which disappear on uncreasing.

The planar symmetry block is `105sym 0`, `105plane` followed by three homogeneous four-tuples (origin weight 1, two orthonormal axes weight 0), then `105a fr/er/vr/f/e/v`. The `f/e/v` maps are the forward partitions, and `fr/er/vr` the reverse partitions including fixed elements. The codec validates identity ranges, unique domain/range membership, complete topology partition and reciprocal non-fixed pairs. It retains these maps instead of inferring them from coordinates. Multiple reflections, isolated/radial symmetry and user knots are rejected.

## Orientation roots

The three root records are not allocation bookkeeping. `f <link>` is the face origin, `e <link>` the edge origin and `v <link> NORTH` the vertex orientation link and direction. The controlled imports below show that they change the converted BRep while the control cage stays identical. These names came from earlier binary inspection. The explanation that the roots select the local parameter frame of each basis function is not confirmed by a black-box experiment.

Controlled imports isolate the effect on a 17×23×31 mm box (`TSplineCodec/RootVariants` and `TSplineCodec/EdgeVariants`). Every variant had equal control, smooth-point, crease and face-incidence hashes to Fusion's box primitive. First-incident roots gave default area 12.710561939032758 cm². Native face origins alone gave the primitive's 12.7105676688771 cm² but a very-high-accuracy center offset of about 3e-6 cm. Adding native edge origins did not remove that offset. Native face, edge and vertex roots together matched the primitive within 1e-8 in every observation, initially and after an edit. The `ver` record is an export edit counter; setting it to the primitive's 254 alone changed nothing.

The native box primitive's edge origins all run from the lower to the higher vertex index; the larger native box has ten of 48 edges in the other direction, so ascending order is a convention, not a format rule.

## Independent authoring

`MakeClosedCage` takes explicit weighted control vertices and oriented quad index loops, plus an optional `CageOrientation(Spokes, EdgeOrigins)`. It derives directed link pairs, previous/next face rings, edge allocation and connected vertex fans. The first vertex of each loop is the face origin. `Spokes` names the neighbor for each vertex orientation link and `EdgeOrigins` one directed pair per edge. Without an orientation, vertex roots are the first outgoing link in face order and edge origins ascend by vertex index. It uses the qualified cubic declaration profile, unit knot intervals, zero valence offsets, NORTH orientation, no boundary conditions, no compound mapping and no extensions. No input archive, captured cage, point array or vendor payload is loaded.

The prepared independent example declares an eight-vertex, six-face closed control cage with 17×23×31 mm control bounds, Fusion's vertex order, face origins, vertex spokes and edge origins. Those are control bounds, not an assertion that the limit surface is a sharp cuboid. Native comparison is against a newly created one-face-per-axis smooth Fusion box.

## Verification and remaining boundaries

`PrepareTsplines.py` emits complete TSM files from all twelve typed controls and the independent cage, with SHA-bound preparation records. All twelve re-emissions are byte-identical; the `105a` symmetry-map writer reproduces Fusion's two-space pair separators. Product code imports no research modules and invokes no CAD runtime.

`AcceptTsplines.py` accepted all thirteen cases in Fusion 2706.1.17 (`TSplineCodec/NativeAcceptance.json`, SHA-256 `c6f6973215fbb0f46cc454f2fc998132d988e2f76fc03ec002981e4c8551964d`): form import, conversion, control-point edit, native save and reopen, with controls and re-emissions equal at every stage, and the authored cage equal to the native primitive. Zero documents remained open.

Remote cases cover twelve complete native input files with byte-exact re-emission, six malformed file inputs, independent file authoring, orientation agreement with the native primitive and four rejected orientations. Static Black, Ruff, Mypy, Pyright and steering checks passed.

Full F3D Form graph/serializer joins, general rational surface evaluation, arbitrary T-junctions, radial symmetry, additional extensions, deleted slots and older behavior profiles remain unsupported. These are explicit rejection boundaries, not retained opaque records.
