# Pole engine notes

Goal: compute every converted Form face (knots, pole rows over the grips) from the cage alone,
leaving only the G1 cap unknowns to a pluggable hook. Scripts in this folder run with the
scratch venv (numpy, Python 3.14) and `-I`; nothing in src/ loads them.

## Sources

- Old layouts: `FormStencils.xz` rows for Box, Box3, Valence5..8, CreasedPlane, CreasedBox
  (cages from the old saves, `Topology/SavedBodies.py`).
- General probes: `LocalOracle/FormDocuments/General/*.tsm` with Fusion's saves in its `tmp/`.
- Crease rounds: `LocalOracle/FormDocuments/Crease/Round*/*.tsm` with saves in `Crease/tmp/`.

## Knot rule (`KnotRule.py --mode spoke`)

1. Capped points: inside vertices (no open edge) with fewer than three sharp edges that are
   either not valence 4, or darts (exactly one sharp edge), or L-turns (two sharp edges with a
   sector other than two faces). The crease vertex listing plays no part (round 2, below).
2. Level L = 2 when a cage edge joins the point to another capped point, else 1; h = 2^-(L+1).
3. Each cell (cage face) gets, from each capped corner and in both directions, double knots at
   h and 2h, single Catmull-Clark breaklines at 2^-l for l < L, and a double knot on the two
   cell sides through the capped corner (visible only when that spoke runs inside a face, as at
   a dart). Cell corners give single integer knots. Multiplicities merge by max.
4. One step of spoke propagation: each capped point copies, as single knots, the other face's
   own knots crossing each of its spokes within 4h of the point. Propagated knots do not
   propagate again (modes `once` and `closure` over-propagate on LPrism, TPrism, Mixed).
5. Two capped points in one cell on a diagonal keep L = 1 (double knots at 1/4, 1/2, 3/4).

Evidence: exact on Box, Box3, Valence5..8 and on 13 probes fitted after the rule (Box111,
Box122, Box234, LPrism, TPrism, Step, Valence5Tall, Valence3Prism, Mixed56, Mixed78, SharpBox)
plus the five held-out dart saves (Dart0p5, Dart1, Dart2, Dart5, Dart20). Torus86 differs only in
the periodic end form: Fusion writes the closed face clamped (end count 3), poles already agree.

## Non-cap poles (`PoleRule.py`)

A non-cap pole is the Catmull-Clark blossom of the first polynomial piece among its support
spans (de Boor-Fix: every span piece in the support has the same blossom at the pole's
arguments). The span box is clipped to each cell, descended through child faces (child 4f + i
keeps corner i, local axes towards corners i + 1 and i - 1) until a child has a regular 4 x 4
net, and blossomed with the arguments in child coordinates.

Worst error against the exact tables: Box 1.7e-16, Box3 4e-15, Valence5..8 3e-15. Against probe
saves (rows times grips): all of the 11 closed probes and Torus86 at or below 6.4e-15.

Cap unknowns per extraordinary corner: indices i, j <= 4 except (4, 4). A propagated knot
strictly inside (2h, 4h) along one direction adds one index along it for the rows (columns)
<= 3 (Mixed56 EP 1: region 11 has a 3/4 knot region 12 lacks; knot removal leaves 1e-4, so the
extra poles are real degrees of freedom).

## Creases (`CreaseLab.py`, `CreaseCheck.py`)

Hoppe rules with infinite sharpness: sharp edge midpoint, crease vertex (a + 6v + b)/8, corner
(three or more sharp edges) fixed, darts smooth. A listed crease vertex is not a corner: Fusion
drops `Creases.VertexIndices` from its own saves, and listing extra vertices changes nothing
(FixedRound ListedFlat, ListedLine). A face is polynomial
when every corner is smooth valence 4, a crease vertex with exactly two faces on the face's side,
or a corner with the face alone between two sharp edges. Its net reflects every row across a
sharp side (2 near - far), which turns the B-spline vertex rule across the crease into the
identity and keeps 1-6-1 along it, so the reflected tensor spline reproduces the crease rules.

Evidence: SharpBox (all cube edges creased) 150 poles, worst 1.3e-15. Dart saves: all non-cap
poles away from the darts agree; poles next to the darts await the dart cap key set (below).

Cages whose mapping holds compound grips (more grips than vertices: CreasedPlane, the RoundNine
planes) are not Catmull-Clark: the compound grips are the B-spline poles themselves, which is
what `Conversion/ConvertGrid.py` already writes. Since round 2, `BuildTable` routes them through
`Poles/GridRegions.py` (below) instead of raising.

## src engine

`src/convert/formats/Fusion/BrepCodec/Journal/Spline/Poles/PoleTable.py` `BuildTable(Surface,
CapSolver=FillCaps) -> StencilTable` ports the rules above with exact Fraction knots and sparse
grip rows. It loads nothing from re/ and no stencil or shape file, and does no layout lookup.

- PoleKnots, SpokeKnots: the knot rule. Ends always count 3; periodic faces too.
- PoleMesh, FaceNets: crease-aware subdivision. Each level keeps only the faces within three
  rings of the faces that are not yet polynomial, so the cost grows with the number of
  extraordinary points, not with the cage.
- PoleSpans: blossoms and descent, all in exact frames; no tolerances.
- CapPlaces, CapRequests, CapHook: one CapInput per capped point (valence, level, sector knots
  measured from the point, reference rows for sector poles i, j < 8, limit row, the face poles
  of each unknown key, the unknown key set). Keys ('ep',), ('spoke', k, i), ('in', k, i, j);
  sector k lies between fan links k and k + 1, i along link k. The hook returns rows per key.
  Reference rows are the Catmull-Clark blossoms, so they equal netref except spoke 1 and (1, 1),
  which are absent. FillCaps is a placeholder: reference rows, ep = limit, spoke 1 = (ep +
  spoke 2) / 2, (1, 1) = spoke 1 (k) + spoke 1 (k + 1) - ep. This is linear precision for the
  knots 0, 0, 0, 0, h, h, 2h, 2h of a cap corner (Greville points 0, h/3, 2h/3).
- PoleLimit: smooth limit (n^2 v + 4 sum e + sum f) / (n (n + 5)); other vertex kinds use the
  fixed point of the one-ring subdivision matrix (power iteration until exactly stationary, at
  most 200 steps; the subdominant eigenvalue stays below 2/3, so 200 steps reach far past double
  precision).
- PoleLines: curve rows are the face side poles (sides 2 and 3 are negated and reversed),
  clamped at Lower and Upper by Boehm insertion. Point rows come from a de Boor evaluation at the
  vertex's face corner; rows are reused when no blend happens.

`EngineCheck.py` results (curves and points matched as sets, since CappedShape orders them
differently from the old tables):

| layout | non-cap | whole body with Fusion cap rows (faces, curves, points) |
| --- | --- | --- |
| Box | 1.7e-16 | 1.7e-16, 5.6e-17 (12/12), exact (8/8) |
| Box3 | 4.0e-15 | 4.0e-15, 1.1e-16, exact |
| Valence5..8 | at most 3.0e-15 | at most 3.0e-15, at most 1.7e-15 (35..56 curves), exact |

Probe saves, non-cap poles times grips: Box111 1.1e-15, Box122 6.9e-15, Box234 5.3e-15, LPrism
4.7e-15, TPrism 3.3e-15, Step 2.4e-15, Valence5Tall 2.9e-15, Valence3Prism 6.7e-16, Mixed56
1.1e-15, Mixed78 1.3e-15, Torus86 1.1e-15, SharpBox 1.3e-15.

What each rule was fitted on:
- Knot levels and doubles: Box, Box3, Valence5..8 (exact tables).
- One-step spoke propagation and its 4h reach: LPrism, TPrism, Mixed56 (the `once` and
  `closure` modes failed there).
- Extended cap set: Mixed56 EP 1, then checked on Mixed78.
- Dart capping and the doubled spoke knot: the RoundTwo dart saves. They share one cage, so
  the five saves count as one layout.
- Non-cap blossom rule: Box. The crease reflection comes from theory and was checked on
  SharpBox only.
- Curve and point rows: no fitting.
- Knots not used in any fitting: Box111, Box122, Box234, Step, Valence5Tall, Valence3Prism,
  Mixed78, SharpBox, Torus86. Their non-cap poles are held out for every rule except the
  extended cap set on Mixed78.

## Round 2

Entry point stays `BuildTable`. Every rule below was rerun on all old layouts, probes and crease
rounds after the last change (`EngineCheck.py`, and `EngineCheck.check_probe` over each
`Crease/Round*` cage with a save).

### Compound-grip creased planes (CreasedPlane, RoundNine planes)

The grips are the poles. `Poles/GridPoles.py`: primary grips and rim compound grips fill a
uniform cubic net on the integer grid places (`BaseGrid`, ends counted 3). Every interior
creased grid line is clamped to full multiplicity by Boehm insertion (`SplitGrid`), then the
interior compound grips (one per crease spoke) and the primary grip replace the poles around
their crease vertex (`CreaseGrid` in `GridRegions.py`). Each CappedLayout region takes the knot
range between its bounding crease lines (`SubRange`), oriented by its first cell (`CellAxes`).
`BuildTable` routes `IsCompound` cages there. It belongs in the engine rather than in
ConvertGrid: ConvertGrid writes one whole grid face, while the creased plane needs CappedLayout's
regions, curves and points, which BuildTable already produces.
Fitted on: the CreasedPlane table. Checked on: the RoundNine plane saves (exact). CreasedPlane:
faces 0, curves 0 (7/7), points 0.

### Cap frames (spoke keys shared by differently knotted faces)

Keyed per face, then reconciled by knot insertion. A capped point's own frame K0 is OwnList of
the base knots of the cells that have the point as a corner, plus the spoke-propagated knots
whose target cell is one of those cells (`RegionKnots.CellAdds`). Hook keys live on K0
(`CapFrames.RegionFrames`); the face's final rows are sums of MixV x MixU x K0 rows (exact
Fraction Boehm weights, `InsertWeights`). Non-key K0 rows are netref on K0. CapInput.Places lists
only final places reached by unit weights.
Fitted on: Mixed56 and Mixed78 residuals, Valence5..8. Checked on: all others below.

| layout | frame fit | clash over shared keys (differently knotted) |
| --- | --- | --- |
| Box, Box3, Box111 | 0 | 0 over 112 (0) |
| Box122, Box234 | 0 | 0 over 112 (80, 112) |
| Valence5..8 | 0 | 0 over 188..302 (100..160) |
| LPrism, TPrism, Step, Valence5Tall, Valence3Prism | 0 | 0 |
| Mixed56, Mixed78 | 3.3e-16, 2.8e-16 | 1.1e-16 over 207 (135), 283 (177) |
| CreasedBox | 7.8e-16 | 9.4e-16 over 120 (94) |

### CreasedBox (dart into an extraordinary point)

Topology: `Capped/CappedLayout.py` `CreaseEnds` adds every crease end (one creased edge, no
compound grips) to the region loop breaks. Wide curves carry `Bounds` for partly creased box
edges (`EdgePlans.EdgeBounds`). No cage raised BlockSides' split closed seam error.
Knots: the dart and the extraordinary point both cap; levels by adjacency as before. Whole body
with Fusion cap rows: faces 9.4e-16, curves 7.8e-16 (12/12), points 2.2e-16. EditedCreasedBox
(RoundSeven) 5.8e-15. Fitted on: the CreasedBox table. Checked on: EditedCreasedBox.

### Darts

CapInput carries `Creased` (which fan links are sharp) so a solver can see the dart sector.
The dart limit is `PoleLimit.LevelLimit`. Dart0p5..Dart20: non-cap at most 2.7e-15, frame fit
0, clash 0. FillCaps still raises at mid-side darts: it has no rule for a cap pole mid-side.

### Fixed points and the roof and ramp rounds

- Lines: `CageGraph.Inside` means no open edge, and `Regular` means inside and valence 4. The
  listing is ignored, so sharp lines run straight through ridge ends and Fusion's 9 faces come
  out. Regions now match Fusion on all 169 Kit cage and save pairs (crease rounds, general
  probes, Accept; Held* not used).
- Fixed point: inside, three or more sharp edges, some sector wider than one face. Level 2 when
  a neighbour is a capped point or a corner point, else 1. Knots: singles at 2^-p for
  p = 1..level+1 (roof ridge ends 1/2, 1/4, 1/8). The face corner pole at a fixed point is the
  vertex itself (`FixedPoles.FixedRows`); all other poles are netref, at depth max level + 1.
- Crease rounds, engine against Fusion poles (no caps): RoundOne 5.3e-14 (Roof scale 10),
  RoundTwo 2.5e-14, RoundThree 6.2e-15, RoundFour..Six, Ten, Eleven 1.2e-14, RoundSeven 5.8e-15,
  RoundEight Roof2Edited 6.2e-15 (from Fusion's own exported cage, `*.edited.tsm`). Knots match
  on every face.
- Fitted on: RoundOne roofs, then FixedRound (`FixedCages.py`, `FixedProbe.py`) for the
  listing, the level and L-turn capping. FixedRound results: TJunction, TJunctionWide,
  ListedFlat, ListedLine exact.

## Not yet matched

- FixedRound Cross (four sharp edges at one point): knots match, poles off by 2.95e-2 in the
  four top quadrants. The tensor reflection at a four-sharp corner disagrees with Fusion.
- FixedRound LTurn, LTurnWide: Fusion caps the L-turn at level 1, but the knots differ. In the
  one-face sector Fusion has single knots at 2h where Kit has doubles. In the three-face sector
  Fusion adds single knots at 3h along non-sharp spokes.
- Ramp*Edited (RoundEight): Fusion's exported cages hold compound grips on a closed cage
  (72 grips, 42 vertices). `GridGrids` needs four spokes per vertex. A compound-grip path for
  closed creased cages is not written. The Accept Held* pairs with compound grips are the checks
  for it.
- Weighted cages: HeldWeighted6 (held out) is 2.3e-1 off in plain rows and in homogeneous rows.
  Weights stay 4e-3..1e-2 off. Final check only, no rule changed.
- Dart0p5 and Dart1: CompareCapped differs only by a tangent merge that belongs to
  ClassifyEdges.
- netref rows for spoke 1 and (1, 1) via the level L + 1 sector chart.

Held-out final check (run once, no rule changed): HeldBand67 non-cap 1.6e-15, frame fit
3.3e-16, clash 1.1e-16; HeldBox113 3.6e-15; HeldPrism3 2.2e-15; HeldPrism5 2.0e-15; HeldTorus75
8.9e-16; HeldCreaseLoop 6.7e-16; HeldWeighted6 2.3e-1 (weights, above). The other held-out
cages have no save.
