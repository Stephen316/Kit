# Next semantic BRep expansion: a planar cuboid

The smallest useful next step is a standalone, typed planar solid reader and writer, initially qualified for one cuboid with six planar faces, twelve straight edges, and eight vertices. It can reuse the ownership and geometric checks already present in `Topology/AsmEdge`, while replacing the cylinder-specific ordinal tables in `BrepCodec`. Merely admitting additional ASM token names would not provide semantic support.

## Corpus evidence and limits

The [inventory script](InventoryBrep.py) inspected the embedded `.smb` and `.smbh` members of all 712 archives in `CorpusInventory.json`, using only the research token decoder. The [summary](Summary.json) and [compressed detailed inventory](Inventory.json.xz) bind the source inventory and every blob digest.

There are 1,170 embedded streams in 582 archives: 605 snapshots and 565 history streams, comprising 1,083 distinct blob hashes. All 1,170 streams passed structural token framing. Initial tables contain 22,303 `straight-curve` records and 11,086 `plane-surface` records, compared with 2,475 `ellipse-curve`, 748 `cone-surface`, 1,242 `intcurve-curve`, and 475 `spline-surface` records. Counts include repeated blobs and selection caches; they are not counts of visible result bodies or supported documents.

The ownership-only classifier finds 1,052 axis-aligned box candidates and 2,454 bodies containing only planar faces and straight edges. It does not check every orientation, attribute, current-body selector, or history revision and therefore does not establish semantic acceptance. Two bodies have unresolved ownership under this restricted classifier; neither is silently counted as a box.

| History-stream candidate class | Members | Interpretation |
| --- | --- | --- |
| Contains at least one box candidate | 204 | May also contain other bodies |
| Every initial body is a box candidate | 162 | May require multiple bodies or complex history |
| Exactly one box candidate | 83 | 83 distinct blobs across 63 archives |
| Exactly one box, two delta states, only the three studied custom attribute types | 60 | 60 distinct blobs across 40 archives; most direct next qualification candidates |
| Every initial body has only planes and straight curves | 281 | Broader planar-body opportunity after the cuboid |

The two-delta-state condition is a structural filter, not proof that each journal has the supported insertion-only board grammar. Each candidate must still be checked before acceptance. Snapshot counts are separate: 318 snapshot members contain a box candidate, but only five contain exactly one box. Most snapshots mix model geometry with profile or selection-cache bodies.

## Existing code to reuse and boundaries to remove

`GeometryCodec` currently constructs the analytic positive-Z cylinder. `BrepCodec/Reading/MapTopology` maps a supplied canonical topology through reciprocal pointer structure, but `ProfileRecords`, `ReadCylinder`, `ReadTagSet`, and the 35/59-record history/snapshot models qualify only that cylinder family. The current header reader fixes root counts to two for history and four for the selected snapshot profile. A general cuboid is therefore not supported by merely using an already available `plane-surface` primitive.

The older `Topology/AsmEdge` code already provides a stronger starting point for planar geometry:

- `AsmPrism` follows body/lump/shell/face ownership and plane carriers
- `AsmRim` checks reciprocal coedge rings, owners, and partner links
- `AsmPrismEdges` checks two opposing face uses per edge and closes each vertex ring
- `AsmPoints` reads physical vertex positions and checks incidence
- `PrismCarriers` checks finite straight-curve intervals against the stored vertices, and checks plane equations and reference vectors

That path is currently a **witness for a separately reconstructed neutral prism**: `ReadPrismCache` receives an expected `BrepModel` and profile curve tags. It is not a standalone reader for all native topology or attributes, and it does not serialize the source history. `ReadFaceName` compares generic name terms without assigning all operation-specific meanings. `ReadCoedgeTag` only accepts its narrowly qualified sketch-attribute form. These limitations must remain visible in the promoted reader.

## Concrete native extrusion control

[CuboidControl.json](CuboidControl.json), produced by [InspectCuboid.py](InspectCuboid.py), records the existing native `ordinary_rectangle_control.f3d` from the thin-extrusion study. Its archived native ground truth reports a healthy ordinary solid extrusion with bounds `(0,0,0)` to `(4,3,2.5)` cm and volume `30` cm³. Its `.smbh` digest is `aa25da5b0c1bf72d5ea53cacea4ec09854a0395ebfcfd46786f32480403d0cf2`.

The initial table has 102 records: 86 topology/geometry records and sixteen attributes. It contains one body, lump, and shell; six faces, loops, and plane carriers; twenty-four coedges; twelve edges and line carriers; eight vertices and points; and one `asmheader`. The journal has one `history_stream`, current and initial `delta_state` records, and no archived geometry revisions. Its current board contains exactly 101 insertion triples, covering every initial entity except `asmheader`, followed by three zero terminators. This control therefore exercises a larger topology with the already studied simple insertion-journal form.

The newly captured [12×18×24 mm native control](../../LocalOracle/Brep/CuboidCapture.json) independently supplies a translated box at base `(20,-30,5)` mm, native volume `5.184` cm³, and the same six/twelve/eight topology. Its SMT and F3D hashes are recorded in that capture. This is source evidence captured by the parent task, not acceptance of the proposed independent cuboid writer.

## Field-level starting contract

For these ordinary topology records, fields 0–2 are the attribute head, stored entity/body identity, and the qualified null entity-pattern reference. Attribute records instead have their own next/previous/owner linkage and must not be treated as ordinary topology records.

| Record | Fields after the ordinary three-field prefix |
| --- | --- |
| `body` | first lump, first wire, transform |
| `lump` | next lump, first shell, owner body |
| `shell` | next shell, first subshell, first face, wire, owner lump |
| `face` | next face, first loop, owner shell, qualified null reference, surface, sense, sidedness |
| `loop` | next loop, first coedge, owner face |
| `coedge` | next, previous, partner, edge, sense, owner loop, qualified zero integer, pcurve |
| `edge` | start vertex, start parameter, end vertex, end parameter, owner coedge, curve, sense, convexity string |
| `vertex` | owner edge, owner-edge endpoint index, point |
| `point` | physical position |

In the rectangle control, all eight vertex endpoint indices agree with their owner-edge references: index zero chooses the owner's start vertex, and index one its end vertex. Seven use one; one uses zero. This is a linear-edge rule for this control. The closed-circle source's index two must not be normalized under it.

The `straight-curve` fields after its prefix are origin, parametric direction, then optional lower and upper bounds. A finite bound is a true token followed by a double; an absent bound is a false token. The control's first line uses origin `(4,3,0)` cm, direction `(-1,0,0)`, and interval `[0,4]`, producing endpoints `(4,3,0)` and `(0,3,0)` cm. This permits direct verification of `P(t)=origin+direction*t` independently of the vertex positions. Native lines may be unbounded carriers with a bounded edge interval; the existing witness supports both seven- and nine-field line records.

A `plane-surface` stores origin, normal, reference vector, V sense, and four optional parameter bounds. The reference vector is a parametric basis, not a point or automatically a unit direction. The new native cuboid SMT writes reference vectors of magnitude ten where embedded binary carriers use their own scale. Position conversion must not be indiscriminately applied to parameter intervals or direction vectors. The first promotion should explicitly preserve the line and plane parameter frames and choose its writer's frames from semantic inputs.

## Ranked implementation sequence

1. **One planar cuboid, complete topology and analytic carriers.** Add typed semantic tables for bodies, faces, loops, directed coedge uses, edges, vertices, line carriers, and planes. Preserve source owner-edge indices and parameter frames. Validate finite coordinates, reciprocal ownership, closed rings, exactly two opposite coedge uses per edge, outward face orientation, and geometric incidence. Independently generate the topology from dimensions and placement. First prove standalone SMT/SMB vendor import and measured geometry, then add the simple insertion journal and attribute ownership from semantic inputs. Do not claim parametric rectangle-document writing until its Design sketch/profile/feature graph is independently generated and accepted too.
2. **Variable root counts, multiple planar bodies, and complete attribute chains.** Use body-map selectors to distinguish model results from profile/cache bodies. Generalize timestamp, sketch, and generic tags as typed per-entity attributes, with complete multiplicity and next/previous/owner links. Qualify multiple shells/loops and transformed bodies separately. This reaches the broader planar candidates without requiring spline geometry.
3. **General journal graphs and archived entity revisions.** The corpus history sections include 1,821 delta states, 3,269 archived custom attributes, 3,109 archived coedges, and archived topology/carriers of many other types. The present reader supports a two-state insertion-only journal. Reading only the initial geometry and discarding revision records would lose rollback/history semantics even for a visually simple final box.
4. **Analytic curved mixed solids.** Generalize circle/ellipse and cone carriers beyond the current fixed cylinder, then sphere/torus records, with complete parameter ranges, face trims, and orientation. This expands common mixed planar/curved bodies but is a larger semantic step than a box.
5. **Intersection curves, pcurves, splines, and tolerant topology.** The corpus contains 2,076 pcurves, 1,242 intersection curves, 475 spline surfaces, plus tolerant edge/coedge/vertex variants. Token framing does not resolve their nested subtypes, trim mappings, or tolerance semantics. These require separate models and vendor acceptance, not generic raw-token retention labeled as a reader.

The first two steps have high corpus relevance and substantial existing field evidence. Later steps remain necessary for broad Fusion format support; the current and proposed qualifications are not universal.
