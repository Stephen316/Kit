# View edge notes (working state)

Branch: local `drawing-view-edges` from PR head 85d852b2e. Commit only here. No push, no PR.

## Goal

Kit writes the edges each view shows: the edge list in every `ACDBVIEWREP` body, the cached curves and the drawn
entities on the synergy-mapped layers (category 7 Visible, 3 Hidden). Fusion 2706.1.17 draws a view on open only
from those stored edges (gotcha FusionDrawingStoredEdges.md, grafts V7NoEdges, V3AboveBelow, V8AboveBelowNoEdges,
V2RightBack).

## Inputs found

- Fusion-saved drawings live outside git, under `$TMPDIR/KitFusionDrawings` and the Fusion cache:
  - `Variants/P0Control.f3z`: A3 control bundle (drawing and design). Design: 40 x 20 x 10 mm box with a
    through hole r 4 mm at (10, 10). Base 5 edges, right and above views 4 each, visible style.
  - `Captures/Edit2` to `Edit8`, `DG1Wheel`: Wheel drawing saves. 369 view bodies, 2,691 stored edges, views in
    the six axis directions, visible and hidden styles. The drawing's Wheel has two bodies (hub r 2.5 to 7.5,
    tire r 7.5 to 12 with cones); the cached Wheel design is a later one-body version, so its edge ids cannot be
    checked, but its silhouettes can.
  - Cache `_KitDrw BoxA Drawing` and `_KitDrw BoxA` design: 25 x 25 x 5 mm box, base from +Z, one side view.
- An exported DWG (`InspectUploads.py` export after open) keeps the `ACDBVIEWREP` edge lists, so a poke followed
  by an export gives Fusion's own edges for any graft.
- `FeatureAuthoring/Authored/CornerSetPart.f3d`: Kit-authored 40 x 30 x 20 block with a 6 mm through hole, two
  r 4 corner fillets and a chamfer (held-out candidate).

## Decoded stored edge form (evidence: control, BoxA, Wheel saves)

- Edge row: `EdgeId`, `EdgeLongA` 1, `EdgeLongB` 1, `EdgeFlagA` 1 visible / 0 hidden, `EdgeLongC` 0,
  `HasCurve` 1, cached curve, `EdgeFlagB` 0, `EdgeEntity` soft pointer to the drawn entity. All 2,691 rows.
- Rows in a body are sorted by `EdgeId` read as a signed 32-bit number (369 of 369 bodies). No id repeats in a body.
- B-rep edge id: 0-based position of the edge in the list of distinct edges met by the walk face -> loop ->
  coedge (loop's first coedge, then `next`), faces in shell order, loops in face order. Not the coedge index:
  control ids 9 and 12 come out as 10 and 14 that way. Control: 10 of 10 ids match (`edgeorder.py walk`).
  BoxA (unrelated design): 8 of 8 match. Not ACIS save (BFS) order.
- Silhouette id: `0xFFFFFFFF - 2048 * FaceIndex - Side`, FaceIndex the face's index in the walk, Side 0 or 1.
  Wheel cylinders and cones, four sight directions.
  Side 0 sits at offset `Eye x Along` from the axis, where `Along` is the line's direction.
  The line runs between the face's two boundary circles. What sets `Along` per face is open (needs a known B-rep).
- Cached line: start vertex and `end - start` of the edge (model mm). Cached circle: centre, the curve normal, the
  DWG arbitrary-axis X of that normal as reference axis, radius, 0 to 2 pi for every saved circle edge.
- Drawn entity: the visible or hidden piece of the 3D edge curve in model mm, in the view's inner `*S` block,
  layer Visible (`EdgeFlagA` 1) or Hidden (0). Line -> LINE; whole circle -> CIRCLE; part circle -> ARC, with
  the curve normal as extrusion and OCS angles counterclockwise about it. The viewport does the projection.
- A circle seen edge on (Wheel side view) is one ARC: the half nearer the eye. The far half projects onto it and
  is not stored, visible or hidden.
- Coincident pieces: a piece that projects onto a nearer drawn piece is dropped (hole circles end on, Wheel hub
  circles behind tire circles). Hidden pieces from two bodies that coincide are both kept (Wheel r 7.5 lines).
- Style: `ViewLongB` 2 = visible edges only (no hidden rows), 1 = visible and hidden. Children carry 6.
  Two Wheel views switched from style 1 to 2 (Edit6 views 0x466a, 0x4778) keep their hidden silhouette rows with
  `Invisible` 1 entities; every view Fusion computed in style 2 stores no hidden rows. Kit writes the computed form.
- Drawn entity common fields (1,431 entities): ColorIndex 256, LtypeScale 1.0, LtypeFlags 0, LineWeight 29,
  NoXdic 1, no reactors, Invisible 0 (except the switched views above). `EdgeEntity` is a soft pointer (code 4).

## Oracle round E1 (control, hidden style, layout A)

- Graft `E1HiddenA` (`Rules/BuildEdges.py`): layout A, every stored edge removed, base `ViewLongB` 1.
  Run with `Native/EdgeRound.py E1 E1HiddenA` (upload, open, poke, export).
- Open: 0, 0, 0 curves (no stored edges). After the poke: 5, 6, 6 curves.
  Boxes base [100.4688, 80.6094, 260.4688, 160.6094], right [278.0, 80.6094, 318.0, 160.6094],
  above [100.4688, 177.2031, 260.4688, 217.2031].
- Export `Exports/E1HiddenA.dwg`: base `[11, 1, 11296]` with visible ids 1 (bottom hole circle), 2, 6, 9, 12; the
  top hole circle projects onto the bottom one and is dropped. Right child `[15, 5, 48224]`: hole silhouettes
  0xFFFFFFFE (y 14) and 0xFFFFFFFF (y 6) hidden, cached start z 0, direction (0, 0, 10), visible 5, 6, 7, 8.
  Above child: silhouettes at x 14 and x 6 hidden, visible 8, 9, 10, 11. The hole circles seen edge on coincide
  with outline edges and are dropped.
- So children take `ViewLongB` 4 + base style (6 visible, 5 hidden), and a view update adds 0x2000 to `ViewFlags`
  (3104 -> 11296, 40032 -> 48224). For the control hole (cylinder axis +z, face reversed) `Along` is the surface
  axis, which also fits the Wheel cones (direction of growing radius along the axis).

## Implementation plan (in progress)

- Input: `ViewSource.Solid`, the body B-rep (interchange `BrepModel`, mm) with shell faces, face loops and loop
  coedges in the order the design stores them. Edge ids come from that walk. No solid, or a surface or curve the
  rules do not cover, raises.
- Candidates: every B-rep edge (lines, circles, arcs) plus cylinder and cone silhouettes.
- Each candidate point is covered (a nearer candidate of the same body projects onto it with the same tangent),
  hidden (the ray toward the eye enters a face strictly inside it) or visible. Covered pieces are dropped.
- Open: how Fusion stores an edge split into visible and hidden pieces. No saved view has one (ids never repeat).
  Needs an oracle round on a design whose axis views split an edge.
- Open: the cached form of a part arc edge (every saved circle edge is whole) and whether Fusion draws tangent
  edges. Until a round shows them, Kit raises for split edges, part arc edges and tangent edges.
- More decoded facts: CIRCLE and ARC centres are stored in the entity's OCS (arbitrary axis of the extrusion),
  246 of 246 Wheel entities with extrusion (0, 0, -1); the cached circle centre is in model coordinates.
  `CurveReal` is 0.0 in all 255 cached circles. LINE pieces use `ZeroDepth` 1 only when both ends have z 0.
- Code: `Dwg/Author/Edges/` (solid reading, faces, coverage, ray hits, silhouettes, piece split, rows) and
  `Views/PlaceEdges.py`; `ViewSource.Solid`, `ViewDraft.ShowHidden`; CIRCLE and ARC sheet defaults.
- Offline check against Fusion (`Rules/BuildEdges.py` T16 grafts, scratch `edgecmp.py`): Kit's rows and drawn
  entities for layout A equal Fusion's, value for value, in the visible control (`P0Control`, 5/4/4 rows) and
  the hidden export (`E1HiddenA`, 5/6/6 rows), including OCS centres and cached circles.
- Re/ graft builders now pass a box solid and author views without edges (`Rules/KitSolids.py`), so their
  output is unchanged: E1HiddenA rebuilt to the same SHA-256 (bd19647a...).

## Round T16 (control, Kit edges)

Grafts: T16{Visible,Hidden}{A, LeftBelow, RightBack, AboveBelow}. A is the training layout; the other three are
held-out directions (left, below, back views never used to derive the rules). Run with `Native/EdgeRound.py T16`.
Kit row counts per view: A 5/4/4 and 5/6/6, LeftBelow 5/4/4 and 5/6/6, RightBack 5/4/5 and 5/6/5,
AboveBelow 5/4/4 and 5/6/6.

Results (report `Rules/GraftRoundT16.json`, built by `Rules/ReportEdges.py`):

- All 8 grafts opened (2.6 to 4.9 s). On open, every view showed Kit's curves: curve counts equal Kit's row
  counts, and open counts and boxes equal the counts and boxes after the poke, view for view.
- Layout A open boxes equal the boxes Fusion gave in E1 after its own update.
- The DWG Fusion exported after the poke holds Fusion's recomputed edges. In all 8 grafts, all 24 views, every
  row and drawn entity equals Kit's (fields, entity kind, layer, data; handles left out; floats to 1e-5).
- Held-out directions (left, below, back) behave the same as the training layout.
- `modified_after_open` is true, as in all 66 earlier bisect grafts; it is not an edge effect.

## Held-out design (offline)

- BoxA, a Fusion-saved drawing of an unrelated design (25 x 25 x 5 mm box), base view sight +Z with up +X and
  one projected view sight +Y. Kit authors the same two views from the BoxA solid (scratch `boxacmp.py`).
  Kit's rows and drawn entities equal Fusion's stored ones, 4 and 4 rows (`held_out_design` in the T16 report).
- The Fusion sample `Boxes Drawing` holds one isometric view of two bodies; Kit refuses both, so it is no check.
- No Fusion-saved drawing of a design with fillets, part arcs or partly hidden edges exists here, and creating
  one needs a new cloud document (`DrawingManager.createDrawing` returns a cloud DataFile). Those cases raise.

## Split edges tightened

- In the 1,920 line rows of the Wheel saves (both styles), every drawn LINE is the whole cached line. No saved
  view draws part of a line. The only shortened drawn piece Fusion stores is the edge-on circle, cut by covering.
- So Kit now raises for any edge that the view splits into more than one piece, hidden or visible, also in the
  visible style where the hidden piece would not be written. A piece shortened only by covering is kept.
- All 9 grafts rebuilt byte for byte the same after the change (PlanEdges digests).

## Steps

1. Decode the stored edges of every saved view (done above, scratch dumpers).
2. Oracle round E1 on the control: hidden style, poke, export, read Fusion's edges (done above).
3. Implement in `src/convert/formats/Fusion/DrawingCodec/Dwg/Author/Views/`.
4. Graft Kit views into Fusion saves and open them (round T16 done, held-out directions; BoxA offline).
5. Docs: FusionDrawingCodec.md, FusionDataModel.md, FusionAcceptanceEvidence.md, the stored edge gotcha (done).

## Open

- Tangent edges (fillets): whether and how Fusion draws them. Needs a Fusion-saved drawing of a filleted body;
  making one needs a new cloud document, which the trial limit forbids. Kit raises.
- Part arc edges: cached form unknown (all 255 saved cached circles are whole). Kit raises.
- Edges split into visible and hidden pieces, or into several pieces: no saved view has one. Kit raises.
- Surfaces other than planes, cylinders and cones; more than one body; moved bodies. Kit raises.
- A Fusion round on a held-out design: grafts only carry the control design. Swapping the bundled design needs
  the design target ids (component, body, instance) of the new design, which BuildAuthored reads from a
  Fusion-saved link. BoxA was checked offline instead.
