# General Form conversion: working notes

Branch `form-general-rules` (from e4e99c2b5). Research only; nothing here is loaded by src/.

## Task state

- Goal: replace `FormStencils.xz`, `FormShapes.xz`, `StencilKey.py` and loaders in
  `src/convert/formats/Fusion/BrepCodec/Journal/Spline/Stencil/` with a rule derived from cage topology.
- Acceptance: old 8 layouts (Box, CreasedPlane, CreasedBox, Box3, Valence5..8) model-equal; at least 6
  held-out layouts with valence 3, 5, 6, 7 points, a crease loop, a weighted cage, a non-box topology.
- Method: black box only. Kit cage -> Fusion via `re/Fusion/LocalOracle/RunLocked.mjs` -> read Fusion save.

## Data on hand

- Exact stencil matrices M (grips -> poles) for the 8 old layouts in FormStencils.xz (research data now).
- 12 new probe cages converted by Fusion (all form_health 0, solid):
  `re/Fusion/LocalOracle/FormDocuments/General/{Box111,Box122,Box234,LPrism,TPrism,Step,Valence5Tall,
  Valence3Prism,Mixed56,Mixed78,Torus86,SharpBox}.tsm`; saves in `General/tmp/*.f3d` (gitignored, not
  scrubbed). One sample each: they validate a rule but do not give M.
  Face counts: boxes 6, LPrism 12, TPrism 16, Step 12, Valence5Tall 15, Valence3Prism 9, Mixed56 19,
  Mixed78 25, Torus86 1 (faces 1, edges 2: periodic surface), SharpBox 6.
- Tools: `CapLab.py` (cage, CC subdivision, Bezier, table readers), `Sectors.py`, `CapSystem.py`
  (unknown keys, G1 rows, quadratic-spoke rows), `Exact.py`, `Unfold.py` (sector grid labels).

## Conversion structure (confirmed exactly)

- Linear in grips. Regular regions are the Catmull-Clark limit (uniform bicubic B-spline of the cage).
- Cells touching an extraordinary point (EP) get double knots at h and 2h from the EP.
  h = 1/4 for an isolated EP; h = 1/8 plus a single knot at 1/2 when EPs sit at adjacent cell corners.
- B-rep faces are rectangular blocks bounded by EP spoke lines.
- PatchCell(Face, Window, Offset): (u, v) = rot^turn((s - Offset[1], t - Offset[0])), rot(x, y) = (-y, x).

## G1 cap at an EP (valence n), sector poles P(i, j), 0 <= i, j <= 4

- Unknowns: i, j <= 4 except (4, 4). EP value = CC limit point.
- Sector sharing: P_k(i, 0) = P_{k-1}(0, i).
- G1: cross_k + cross_{k-1} = lambda(s) T_k, lambda = 2 cos(2 pi / n) phi(s / h),
  phi = 1 - 2x/3 on [0, 1], (2 - x)^2 / 3 on [1, 2], 0 beyond.
- Spoke is quadratic on [h, 2h]; C2 at h.
- C2 across s = 2h for rows j = 2, 3 (and columns i = 2, 3 across t = 2h).
  Box3 rank with G1 + C2 = 31, 27 free directions.
- On [2h, 4h] the cross-boundary derivative equals CC: P(4,1) - P(4,0) = CC(4,1) - CC(4,0).
- Spoke poles 1..4 and (1,1), (1,2), (2,1), (2,2) see the 2-ring only through
  sigma_k = 4 (2,0)_k + (2,1)_k + (1,2)_{k-1}.
- EP tangents T_k are pure Fourier mode 1, but the tangent plane differs from CC
  (e:f amplitude ratio 2.5923 vs CC 2.5616).
- Mode-0 coefficients are exact rationals with 1691 = 19 * 89 in denominators, e.g.
  P2 E = 120625/324672, P3 E = 113341/324672, P4 E = 2233/6764, (1,1) E = 366383/974016.
- Mode 0: (1,1) = EP - (P2 - EP)/3; (2,1) = P2 + [-(b3 - P2) - (2/3)(P2 - EP)]/6, b3 = (P2 + P3)/2.
- Split rule (exact for i = 2, 3, 4): (i,1)_k - (1,i)_{k-1} = R(i,1)_k - R(1,i)_{k-1}.
  R = "netref": blossoms at Fusion's knots of the uniform cubic B-spline on the level-2 CC-subdivided
  net of each sector (P(-1, b)_k = (b, 1)_{k+1}, P(a, -1)_k = (1, a)_{k-1}).
  This mirrors the symmetric split of Fan-Peters 2010 ("fewest knots") with netref as reference.
- R equals the CC blossoms for every key except spoke 1 and (1, 1).
- delta = x - R in mode 0 depends only on spoke data (E, e, f, sigma), even for (3,3), (4,3).
  delta(4, j) = (2/3) delta(3, j) for j = 2, 3.

## Newer exact facts (Box3, valence 3)

- Mode 1 is rational too. Cosine parts of the EP tangent rows have denominators 2^a 3^b 73 199,
  e.g. e = 1236979/(2^7 3^3 73 199), f = 44735/(2^3 3^4 73 199), (2,0) = -79/515808 (515808 = 2^5 3^4 199).
  The sine parts carry sqrt(3) from sin(2 pi / 3). So the cap is one rational linear solve per
  Fourier mode: mode 0 brings 19 * 89, mode 1 brings 73 * 199. No CC eigen data is used.
- Mode 0 has 13 pole classes; G1 + quad rows have rank 7, adding C2 rows gives rank 9 (4 free).
- delta = x - netref in mode 0 has rank 2. With data E (EP grip), e (1-ring edge), f (1-ring face),
  sigma = 4 (2,0) + (2,1) + (1,2), let e~ = e + sigma / 2, u = f - E, w = E + f - e~ / 2. Then
  delta = a u + b w with (times 35064576 for a, 17532288 for b; both = 2^k 3^4 19 89):
  (1,0) a 27056 b 0 | (1,1) -22804 -4644 | (1,2) -30476 17556 | (1,3) -17856 19464 |
  (1,4) -14184 -2376 | (2,0) 41356 13932 | (2,2) -27451 13479 | (2,3) -20877 9945 |
  (2,4) -13918 6630 | (3,0) 20736 12744 | (3,3) -17067 6051 | (3,4) -11378 4034 | (4,0) -14184 -2376.
  So spoke 1 moves by (f - E)/1296 only. (4,0) = (1,4). (2,4) = 2/3 (2,3), (3,4) = 2/3 (3,3).
- Scripts (scratch, to be moved here): dfrac.py, dpattern.py (exact patterns), dictfit.py (fits a
  dictionary of energies and netref fidelities to the KKT conditions of all probes at once).

## Frozen columns and the T-spline lineage

- 19 grips touch the Box3 cap; 16 change (EP, e, f, (2,0), (2,1), (1,2)). The 3 diagonal 2-ring
  grips (2,2) keep their netref column exactly. Their cubic basis touches only one face around the EP.
- This matches the published T-splines EP method: one constrained least-squares solve per basis
  function over the one-ring faces; basis functions living in one face are not changed.
  Scott et al., "Isogeometric boundary element analysis using unstructured T-splines", ICES 12-23
  (2012), App. A-B: fairing keeps neighbour Bezier differences (c_a - c_b = c0_a - c0_b), G1 rows
  with lambda = -2 cos(2 pi / N), outer rows fixed, boundary curve degree cap. May, PhD Glasgow 2016,
  4.7 and B.3, adds partition of unity. Fusion's cap is a bicubic variant (double knots h, 2h).
- Tested and failed with netref as reference: Bezier-net first and second differences per piece,
  B-spline pole-net differences (reach 4-6), L2/H1/H2 Gram, jump penalties, CC samples on h/6 grid,
  nonnegative LP mixes of all of these. Next: other references (level 0 and 1 netref, Scott vertex
  rule), and per-column constraints.

## Refuted (KKT residual equals its scale)

- Pure energies (1st, 2nd, 3rd derivative and mixes) under G1 or G1 + C2.
- L2, H1, H2 deviation from CC or from netref, full or inner spans; Bezier-point norms.
- Sampled least squares on dyadic grids h, h/2, h/4 (no nonnegative weights fit).
- Identity and per-class diagonal pole weights to CC blossoms or netref, with spokes,
  first rows or (1, 1) freed.
- Spoke-only 1D fits; Coons-type interior corrections.
- Conclusion: no single quadratic objective with these constraints. Likely a sequential
  construction (FS10-like): tangent and spoke first, then G1 rows, then interior.

## Session 4 results

- Fusion ignores the TSM header `cap-type` (G0CAPS, G2CAPS) and `star-smoothness` (1, 2) on import:
  Box3G0, Box3G2, Box3Star1, Box3Star2 and Box3Same convert to the same body (CapVariantsProbe.json).
- More refuted objectives (netref reference, G1q / G1qC2 constraints): fingerprint scans
  (denominator primes of the mode-0 projector never give {19, 89}) over Bezier-net and pole-net
  differences, elevated nets d4-d6, the inner 7x7 Bezier net of [0, 2h]^2 (orders 0-2),
  interior-only KKT, per-pair-class pole difference weights (null space forces interior pairs to 0),
  Greville limit-point reference, one-parameter boundary stage (g = (0,-39,95,229,216,117,225,216)/229).
- netref is level independent: level 3-5 blossom references equal level 2 where defined.
- Fusion breaks C2 at h in rows 1-4 and at 2h in rows 0, 1, 4; netref is C2 there.
- delta at Bezier level lives on the [0, 2h]^2 net plus the shared boundary rows; the far 2x2
  corner Bezier points of [h, 2h]^2 keep netref.
- Lineage: the knot layout and the G1 weights match Fan and Peters ("On smooth bicubic surfaces from
  quad meshes", ISVC 2008; "Smooth bi-3 spline surfaces with fewest knots", CAD 2011, preprint
  cise.ufl.edu SurfLab 10fan_sbs.pdf): 3 x 3 pieces with two double knots, alpha linear on the
  first span, quadratic on the middle span, zero beyond. Fusion's knots are h, 2h (not 1/3, 2/3) and its
  tangents are rational, so it is a variant, not FP11.
- Isolated cap data for valences 3, 5, 6, 7, 8 (new): PrepareCaps.py writes cap prisms (top and bottom
  discs of n sectors of 3 x 3 quads, side band of 2 rows), three seeded samples per valence
  (General/Caps/*.tsm, plan CapPrisms.json, report CapPrismsProbe.json, saves General/tmp, ignored).
  CapSamples.py recovers the rotation-equivariant cap response per local pole (i, j) < 8 over the EP
  grip and grips (d, a, b), a <= 3, b <= 3, by least squares: residual <= 2.3e-14 for every valence.
  Valence 3 equals the Box3 stencil to 1.8e-14. G1 + quad + C2 rows hold for valences 5-8 (<= 3e-12).
- Reader fix: Fusion writes journal program text longer than 32767 characters with ASM tag 9 and an
  8-byte length (CapPrism6-8 saves). AsmTable, ReadWideText, WideWord and EmitWireField now handle it.
- Scrub: pull re/Fusion/LocalOracle/ScrubSaved.py from the PR worktree before scrubbing new saves.

## Session 5 results

- delta = cap pole - netref obeys 22 valence-independent linear rows in the two-sector window around a
  spoke (CapRelations.json). Fitted on CapPrism5-8, they hold on held-out CapPrism3 to 8.4e-14. All
  coefficients are small rationals (denominators 2, 3, 4, 6, 12, 18, 24, 36, 48, 72). 8 rows are C2 rows,
  1 row is EP = CC limit, 13 rows are new.
- One family of new rows is the Fan-Peters split (FP11 step 4): across spoke k the pairs
  (in(k, i, 1), in(k-1, 1, i)) keep netref's difference for i = 2, 3, 4. G1 fixes their sum. i = 1 is
  not split this way.
- Other new rows (sector A, spokes S0 and S1, A31 = B13 by the split):
  A42 = 2/3 A32, A41 = 2 S03 - 2 S02 + S01 (same as S04), A43 = A34,
  A34 = 1/6 (A13 + A31) + 1/18 (S03 + S13) - 5/36 (S02 + S12) + 5/72 (S01 + S11),
  A33 = 1/4 (A13 + A31) + 1/12 (S03 + S13) - 5/24 (S02 + S12) + 5/48 (S01 + S11),
  plus rows for A24 and A23 + A32.
- With G1 + quad + C2 + EP + these rows, the cap keeps 3n + 2 free values: 3 per Fourier mode, 4 in
  modes +1 and -1 (the tangent plane). delta has rank 3 in most modes, so the data fill that space.
- Per-sector quadratic test in local free coordinates (13 per sector after the local rows): the KKT
  family of q with N^T (sum_k P_k^T q P_k) delta = 0 has dimension 19 of 91. It is the same 19 when
  any one valence is held out, so every member reproduces the held-out valence. No diagonal pole
  weight, no pole-neighbour difference energy, and no Bezier-net difference energy (orders 0-2, 7 x 7
  or 10 x 10 nets, axis or all directions) lies in the family (KKT residual about 1e-3).
- FP11 (cise.ufl.edu SurfLab 10fan_sbs) is an explicit construction: Step 3 spoke formulas with
  lambda, Step 4 split rule, Step 5 interior "single cubic curve subdivided into three pieces and
  remaining coefficients as least deviation". Fusion follows Step 4 exactly, so the remaining
  freedom may be set by FP-style least deviation steps, not one global energy.
- Also refuted under the full hard rows: per-piece Bezier-net first and second differences of delta
  (all 9 pieces, inner 4, L 8), and 45 pure energies of x (derivative orders 1-3 per piece of the
  first face, any linear mix). All give KKT residuals near 1e-3.
- Coupled caps in the old layouts: around the Valence5 centre EP each disc quad has double knots at
  1/4, 1/2 and 3/4 in both directions (the diagonal valence-3 EP uses the far half). The 22 isolated
  relations fail there (3.1e-4), so the far knot after 2h matters, and side quads of the corner EPs
  mix h per direction. The cap rule must be a solve stated on actual knots, not on local indices.
- Session 5 delegated the non-cap pole engine (knots, netref poles, boundaries, creases, torus,
  weights) to a sub-agent; research goes to re/.../Poles/.
- Crease rule (commit ba74e8c79): the 1 degree label was set from constant folds (Crease/Pilot,
  RoundOne, RoundThree: 0.99999 and 1.0 deg tangent, 1.000001 deg unknown). Held-out cases that the
  rule predicted before or without fitting: scale 10 and 0.1 and 4x length (RoundOne, RoundTwo);
  ramps whose peak sits at an edge end (1.0006 deg) or mid-span (0.999 tangent, 1.002 unknown,
  RoundFive); creased-plane carrier grip moves with peaks 0.608, 0.667, 0.775 deg (tangent) and
  1.216 deg (unknown), which sit inside the old refused band (RoundNine, predictions written to
  RoundNinePrediction.json before the Fusion run); and a replay over 333 Fusion-saved archives
  (5509 curve groups equal, 46 refused, 0 different; CreaseRuleCheck.json). A fitted threshold
  between 0.78 and 1.0 deg or between 1.0 and 1.096 deg would have been tested by these; only 1 deg
  fits all of them.
- Cap relations in Bezier terms (beznature.py): of the 22 window rows of delta, 18 are natural
  conditions: EP fixed; C2 at h on the spoke; C2 at 2h on Bezier lines 2-4 (pole rows 2, 3); the split
  at Bezier positions 2-6 along the spoke; delta C1 across the spoke at Bezier positions 5, 6; and
  zero twist of delta at Bezier corners (0, 5), (0, 6), (5, 0), (6, 0). 4 rows are still unexplained.
- Per-valence window rank is 18 for n >= 6 (21 jointly), so each valence adds 3 n-dependent local rows
  (rank 2n). With them, the cap closes once one ring value per sector (for example (1,1) or spoke 2)
  and the tangent plane are given. Per-sector and spoke-window quadratics in delta never curve those
  last n + 2 directions (secq/secw curvature test), so they are not set by such an energy.
- Scrub: the PR worktree ScrubSaved.py now limits the echo search to protein AssetData members.
  Copy it before scrubbing, and compare ReadDocument models before and after.
- Window rank of delta grows slowly with the window: 18 (2 sectors), 21 (3 sectors), 22 (4 sectors),
  3n + 2 for the whole cap (n = 7, 8). A 3-sector window has 2 relations per valence that are not
  shifted 2-sector rows (n = 7, 8; 5 for n = 6). Free cap values after G1 + Q + C2 + EP:
  66 / 58 / 50 (n = 8 / 7 / 6); after the 22 rows 26 / 23 / 20; after the extras 10 / 9 / 8; after the
  rotated 3-sector rows 4 / 3 / 1. So the ring freedom is mostly fixed by 3-sector (cyclic) rules,
  as in G1 vertex enclosure, and the rest sits in modes +1 and -1.
- Locality tests by grip sector are not useful for n <= 8: near the EP every sector is within reach
  of netref's CC stencils, so "far" grips still enter legitimately. Fusion's delta is confined to
  i, j <= 4 except (4, 4) (checked pole by pole on CapPrism8, rest <= 1.5e-13).
- Knot-aware rules (coupled Valence5 centre cap, sectors with next knot 0.75 or 1 after 2h):
  r = L / (h + L), L = length of the span after 2h (r = 2/3 isolated, 1/2 coupled).
  C2 at 2h with zero outer delta gives delta P4 = r delta P3 on rows 2 and 3 in both directions, exact
  per sector and direction. The split (i = 2..4), A41 = S04 and S04 = 2 S03 - 2 S02 + S01 hold exactly
  on the coupled cap. The two unexplained rows hold with an r term (Bezier points b, b50 = S04,
  b60 = r S04 on each spoke):
  R1: b44 = 1/4 (b41 + b14) - 1/8 (b40 + b04) + 1/8 (b50 + b05) - 1/32 (b60 + b06)
  R3: b24 + b42 = b22 + 1/2 (b14 + b41) - 1/4 (b12 + b21) - 1/8 (b40 + b04) + 1/4 (b50 + b05)
      - 1/32 (b60 + b06)
  (pole form for r = 2/3: A33 = 1/4 (A13 + A31) - 1/8 (S03 + S13) + 5/48 (S04 + S14); 7/64 for r = 1/2).
  So the cap is stated on the actual knots. Only two spans occur after 2h (h or 2h), so r has two values.
- FP11 Step 5 is not Fusion's interior: netref satisfies b42 = b41/2 + b44 - b45/2 and the b22 rule
  exactly, Fusion breaks both (residual 1e-3).
- KKT family with spokes (or spokes and first rows) held fixed: per-sector quadratics still never curve
  2 directions per sector, all in (2,2), (2,3) + (3,2), (2,4) + (4,2). These are set by rules, not by
  an energy. Of the 3 per-valence extras, 1 lies in rows j <= 2 next to the spoke (n = 6, 7, 8).
- Scripts (scratch): locality2.py, win3.py, closure.py, secs.py, bezpoint2.py, bezint.py (integral
  functionals: none hold), fptest.py, c2ratio.py, coupledrel.py, fitrel.py, fitrel2.py, supprel2.py.
- 11 single-sector delta rows hold for every valence (3 to 8). Free cap coordinates after the
  22 rows: per sector one of {s2, s3, s4, 11} and two of {22, 23, 24, 32, 42}, plus the tangent.
  A minimal n-dependent row has 19 keys (A11, A12, A13, A22, the B mirror, spokes 0, 1, -1 up to 3).
  For n = 6 its coefficients are rational with denominators 9, 27 and 81.
- Delegated the rest of the cap rule to a fork (writes General/CapRule.py and CapRuleNotes.md).

## Session 6 status

- Pole engine (src Spline/Poles, research Poles/PoleNotes.md):
  - It builds knots and every non-cap pole from the cage.
  - Given Fusion's cap rows, it reproduces Box, Box3 and Valence5-8 exactly (faces 4e-15, curves 1.7e-15).
  - The cap hook (CapInput, KCapHook) is a placeholder.
  - Still open: roof/ramp crease rounds (9 faces vs 7), CreasedBox (dart into an EP), darts in the
    engine, and spoke keys shared by faces with different knots.
  - Compound-grip planes (CreasedPlane) stay on ConvertGrid.
- Held-out layouts: General/HeldOut. No rule was fitted on them. Fusion converted all 7 (HeldOutProbe.json).
  - HeldBand67: valences 3, 6, 7.
  - HeldPrism5, HeldPrism3.
  - HeldTorus75 and HeldCreaseLoop: tori, the second with one creased meridian loop.
  - HeldWeighted6: 9 weighted grips.
  - HeldBox113.
- Next: wire Capped + Poles + cap rule into ConvertForm, then delete the tables and loaders. Then accept
  the old 8 and the held-out layouts in Fusion, and regenerate StencilCensus and StencilCheck.

## Session 7 status

- src wiring:
  - ConvertForm sends cages with more grips than vertices to ConvertGrid. Every other cage goes
    through CageBody, which is CappedLayout + BuildTable + ClassifyEdges + CheckFolds.
  - Nothing reads the stencil or shape tables.
  - The default cap hook is Caps/SolveCaps. It raises until the cap rule lands, so an EP cage
    refuses to convert.
  - ConvertCage refuses header profiles other than cubic, G1CAPS, star smoothness 0, unit scale,
    SUBD_CREASES and NURCCS.
- Crease split rule:
  - Fusion splits a crease edge at each exact sign change of the dihedral turn, and adds a vertex there.
  - Every piece keeps the curve, the label and the windows. Each piece is labelled by the 1 degree rule.
  - Evidence (held-out HeldCreaseLoop): Fusion split the meridian at 1.4693578134647791 and
    4.491317241470378. Bisection on the turn gives 1.4693578134647796 and 4.491317241470378.
  - ClassifyEdges now does this, but only when both sides pass 1 degree within the zero's knot span
    and its neighbour span. Otherwise:
    - It joins the pieces when one side stays within 1 degree. Fusion keeps one unknown edge there.
    - It raises in every other case. Linear ramps with small sides split at a cage vertex instead,
      for example Rampm1p25To1p75 at 1.
  - Crease/CreaseRuleCheck.json replays the rule over 346 archives: 5734 groups equal, 28 refused,
    0 different. The old rule refused 46.
- Acceptance (General/Accept, AcceptGeneral.py):
  - Fusion opened the Kit documents for Torus86, SharpBox, HeldCreaseLoop, HeldCreaseRing,
    HeldTorus75 and HeldWeightedTorus. Each matched Fusion's own conversion within 7.1e-15.
  - Every cage with an extraordinary point is refused until the cap rule lands.
- Closed edges: CheckFormBody now allows closed edges on closed curves, and split pieces that
  share a label.
- Closure:
  - On a periodic direction, Fusion writes closure 2 on the face and the curve.
  - The seam knot 0 then joins the jump list at its derivative level.
  - A wrapped direction closed by a crease seam gets closure 1 and no seam jump (HeldCreaseLoop u).
  - Done: closure 2 and the seam jump.
  - Open: closure 1. It needs CappedLayout to flag closed, non-periodic regions and curves.
- Cap-free cages against Fusion's saves (faces, curves, points, closures, jumps):
  - HeldTorus75, Torus86 and SharpBox match to 1.3e-15.
  - HeldCreaseLoop matches to 7e-16 except the closure 1 flags.

## Session 8 status

- Body order: with the topology from CappedLayout, the old Box, Box3 and Valence5 to Valence8 bodies
  list points, faces, edges and uses in Fusion's order. So do the six accepted cap-free cages. The
  cap poles were placeholders for this check; only the order was compared.
- Seam pcurves differ from Fusion on closed (closure 1) faces. The B-rep geometry still matched.
  - Fusion's saves of three cages:
    - Torus86, both directions periodic: both coedges of each seam edge sit at the low end.
    - HeldCreaseRing (u periodic, v closed by the crease): the crease ring (curve closure 2) has both
      coedges at v = 0. The meridian seam (curve closure 1) has the forward coedge at u = 0 and the
      reversed one at u = 8.
    - HeldCreaseLoop (u closed by the crease, v periodic): the crease pieces (curve closure 2) have
      both coedges at u = 0. The parallel seam (curve closure 1) has the forward coedge at v = 0
      and the reversed one at v = 6.
  - Rule: a seam edge whose curve has closure 1 puts the forward coedge at the low end and the
    reversed one at the high end. A seam edge whose curve has closure 0 or 2 puts both coedges at the
    low end. The progenitor windows follow the pcurves: low cells at 0, high cells at 1. The pcurve
    of a closure 1 seam has closure 1 too.
  - Test, predicted before the run: HeldCreaseCross (8 x 7 torus, creased meridian and parallel at
    the seam) has two closure 1 seams. Fusion split both, as the rule says. A rule keyed on the seam
    direction would have put both at the low end.
  - HeldCreaseBands (two creased parallels, two band faces) and HeldCreaseSlices (two creased
    meridians) add closure 0 seams. Fusion put both coedges at the low end.
  - Kit: BlockSides reads which grid axes are seams (the last and first cell rows share cage edges)
    and places each seam side by that rule. ClassifyEdges measures a seam crease from the face side,
    so a coedge whose face lies past the domain end is moved to the other end for the measure.
- Split piece order: Fusion numbers the pieces of a split crease, and their new vertices, in the
  order of the first use that meets the edge. HeldCreaseSlices meets its crease loops on reversed
  uses first, so Fusion lists their pieces against the curve direction. ClassifyEdges now does this.
- Acceptance harness: AcceptGeneral also saves each document right after conversion, before the
  vertex edit (OracleXConverted.f3d, KitXConverted.f3d in the ignored tmp folder). The older saves
  are taken after the edit, so they hold another cage. Fusion adds compound grips on crease vertices
  when it saves a creased cage.
- Result: Fusion accepted nine cap-free cages: Torus86 and SharpBox (probes), and HeldTorus75,
  HeldWeightedTorus, HeldCreaseLoop, HeldCreaseRing, HeldCreaseCross, HeldCreaseBands and
  HeldCreaseSlices (held out). Against the pre-edit Fusion saves, Kit's body has the same order of
  points, edges, faces and uses, the same knots, closures, jumps, pcurve forms and windows. Poles,
  points, bounds, windows and pcurves agree to 1.3e-15 and fit tolerances to 5e-15. Only labels
  differ, and HeldWeightedTorus weights differ by 2e-16 of rounding.
- Vertex order: Fusion numbers body vertices by first appearance in the edge list, start before
  end, after splits. HeldWeightedSharp (3 x 2 x 2 sharp box, five weighted grips) splits three
  crease edges, and Fusion's split vertices sit between the corners. ClassifyEdges.OrderPoints now
  does this. Fusion accepted HeldWeightedSharp. Against its pre-edit save, Kit has the same five
  rational faces of six and agrees to 1.8e-15; the weights differ by 9e-16 of rounding. The
  acceptance JSON in Accept/ still lists the nine-case run; the final run will cover every case.
- The fork's cap work is in CapRuleNotes.md and CapRule.py.
- Crease refusals (28 groups in Crease/CreaseRuleCheck.json, all roof cages with ny = 6): Kit's turn
  profile (degrees, at knots 0..6) against Fusion's pieces.
  - Linear ramps with the zero at knot 1 or 5 (Ramp0p3Tom1p5, Ramp1p5Tom0p3, KnotOneSlope0p6/0p8):
    split at that knot, tangent on the small side.
  - Linear ramps with the zero at knot 2 or 4 (Rampm0p6To1p2, Rampm0p8To1p6, Rampm1p6To0p8, again,
    Rampm2To1): no split, one unknown edge.
  - Same left side and zero at 4 with a kink at knot 5 (KnotFourEnd0p7..0p9, KnotFourSide,
    KnotFourSlope0p6): split at 4, tangent on the right. KnotFourEnd0p85 is within 0.05 degrees of
    Rampm1p6To0p8 everywhere, so the label threshold does not explain it.
  - Zero at knot 3 with a kink at 3 or 5 (KnotThree*): split at 3, tangent on the left.
  - Zero off a knot, at 2.4 to 2.6 (Rampm1p2To1p8, Rampm1p25To1p75, Rampm1p3To1p7): split at knot 1,
    both pieces unknown.
  - So the split is not where the turn crosses 1 degree, and not only at the zero. Next: controlled
    roof ramps that vary only where the zero sits and whether the profile is linear.
- Cap port to src (in progress, session 9): Spline/Caps holds CapKnots (exact B-spline basis),
  CapLayout, HardRows, RingRows, LeastSolve (pivoted Householder, pure Python) and SolveCaps.
  - CapRuleWindow.json cannot ship: its 111 fitted members have no rank gap and the research rule
    keeps the top 25 SVD directions. The fork is deriving exact window rows.
  - src CapRequests gives no net pole for spoke 1 and (1,1): their spans touch the EP corner.
    The polar form gives them from poles that are present. With knots 0^4 h^2 2h^2, the four
    blossoms S1..S4 of a uniform cubic share no weight on the column behind the EP, so
    S1 = 2 S2 - 2 S3 + S4 along each direction (checked on the three basis columns).
  - With the research window family injected, src ConvertForm matches Fusion on HeldBox113
    (3.4e-13) and HeldBand67 (2.0e-12). HeldPrism3 is off by 3.9e-3 near EPs 6, 7, 8, and the
    window family is not mirror invariant there (4e-2 when the sector order is reversed, 5e-13 at
    the other EPs). HeldPrism5 raises a folded face. The fork is deriving exact window rows.
- Tables retired: FormStencils.xz, FormShapes.xz and their six loader modules now live in
  re/Fusion/Reconstruction/FormDocuments/Tables. StencilTable lost Label and LayoutKey; the cap
  placeholder FillCaps is gone and BuildTable defaults to SolveCaps. A cap whose rows touch a
  weighted grip raises (WeightGuard), since HeldWeighted6 shows Fusion's weighted caps differ.
  ConvertForm sends compound-grip cages with inner creases to the cage engine.
- Exact window rows (session 10): the fork replaced the fitted family with seven exact relations
  per spoke (CapRuleNotes.md, "Window relations (exact)"). They are mirror invariant. The fitted
  CapRuleWindow.json is deleted. src Caps/WindowRows.py holds the same rows as format vocabulary.
  - Port check: src SolveCaps agrees with CapRule.cap_rows to 2.7e-13 on every cap of HeldBox113,
    HeldPrism3, HeldPrism5 and HeldBand67.
  - Against Fusion's pre-edit saves: HeldBox113 8.6e-14, HeldBand67 4.8e-14. HeldPrism3 is still
    off by 7.2e-3 at EPs 6, 7, 8, and HeldPrism5 raises a folded face. The fork traced both to
    src CapRequests: the fixed poles at index 5 on the r = 2/3 spoke differ from Fusion's (5e-3 to
    0.6), and the knots past the face end differ (src 2, 2 / 4, 4, 4; Fusion 1.25, 1.5 / 3, 3.5).
  - Old layouts against every native save in StencilNatives: Box (33 saves) 1.1e-13, Box3 6.8e-14,
    CreasedPlane 1.4e-15, Valence5 4.8e-14, Valence6 2.6e-14, Valence7 2.0e-13, Valence8
    1.7e-14, with the same element order and forms. CreasedBox raises: the cap rule has no rule
    for a creased cap yet.
- Cap knots past the face end (session 10): src frames solve caps on "own" knots (cells of the
  EP's faces) and drop the other knots of the face. With the whole face knot list instead,
  HeldPrism3 (2.0e-14) and HeldPrism5 (5.7e-14) match Fusion. HeldBand67 then fails at v1 and
  v5: face 14 holds a knot at 3/4 along the spoke that face 17 on the other side does not, so the
  two sides see r = 1/2 and r = 2/3. With own knots HeldBand67 matches, so Fusion ignores that
  knot. Rule (CapPlaces.OwnLists): along each axis, the cap sees the knots of the cells on the
  strip beside that spoke, from the EP outward, like a T-spline ray. Knots that other cells of
  the face add are inserted after the solve. Fitted on HeldPrism3 and HeldBand67. With it, src
  matches Fusion on HeldPrism5 5.7e-14, HeldBox113 8.6e-14, the 13 probes (Mixed78 1.9e-13) and
  every native save of Box, Box3, CreasedPlane and Valence5..8 (2.0e-13).

- Weighted caps (session 10): with the exact window rows and strip knots, the cap rule applied
  to homogeneous grips matches HeldWeighted6 (nine weighted grips, held out) within 9.0e-15 in
  poles and 2.1e-14 in weights. The 0.23 gap was the old fitted rows and frames, not weights.
  WeightGuard is removed; weighted cages convert like any other.
- Uniform knot intervals: the general path already scales by one whole-number interval.
  Intervals/Box/Uniform2.f3d (box, every interval 2) matches Fusion within 1.0e-13.
- Census and check: StencilCensus.py and StencilCheck.py now use ConvertCage with no tables.
  ProbeStencil.py has a 600 s budget per run so the shared Fusion lock is released between
  chunks; rerun it until Probe.json says completed.

- Interim Fusion acceptance (session 10, 22 capped cases): Fusion accepted Box, Box3,
  CreasedPlane, Valence5, Valence6, Valence8, the probes and HeldBand67, HeldBox113, HeldPrism3,
  HeldPrism5 and HeldWeighted6 (18 rational faces). Valence7 and Mixed78 differed only in the
  order of vertex_cm: the harness sorted raw floats, and noise in x flipped two vertices.
  Offline, Kit equals the Fusion pre-edit saves of both in order (points 8.9e-16). The harness
  now sorts vertices by rounded keys like faces and edges. CreasedBox waits for the crease-end
  cap rule.

- Rational faces and rounding (session 11): on Stencil/tmp/BoxWeighted, Kit made edges 2, 3 and
  4 rational where Fusion keeps them polynomial. Their Kit weights differed from 1 by only 9e-15 to
  2e-14. SolveCaps kept every nonzero solution entry, so rounding residue on a weighted grip made
  the row count as weighted. Over BoxWeighted, HeldBand67, HeldPrism5 and HeldBox113 the cap
  coefficients fall in two groups: 1e-24 to 1e-18 (rounding) and 1e-8 to 1 (real). No coefficient
  lies between. Fix: drop entries below the solve's own rounding bound (see LeastSolve).
  LeastSolve.RoundFloor sets that bound to eps * rows * (largest / smallest R diagonal) * largest
  entry. It is about 1e-12 on these cages, six decades from both groups. After the fix every
  BoxWeighted variant has Fusion's structure, and no other compared save changed.
- Face partition under grip moves (session 11): Mixed56 X33 moves grip 33 by 0.125 in x. Fusion
  then groups cage faces {27, 28} and {29, 30, 33}; Kit keeps the base {27, 28, 29, 30} and {33}.
  In line terms Fusion drops line 34-6 and draws 34-33-32. Two rays reach vertex 34 after one
  link each: the ray from EP 5 (line 5-34-6) and the ray from EP 35 (line 35-34-33-32). In the
  base the 5 ray goes on; in X33 the 35 ray goes on. So Fusion breaks this tie by geometry.
  Track order by cage polyline length, alone or as a tie-break, fits neither base nor X33.
- Partition probe (session 11, Partition/ folders): a simultaneous ray race (one link per step,
  head-on rays join, a ray stops on a line or trail) with the tie outcomes read from the save
  reproduces Fusion's lines on every Mixed56 and Mixed78 variant, the probes and the held-out
  cages. Kit converts X33, RandomB (Mixed56) and RandomA, RandomB (Mixed78) exactly when given
  Fusion's lines. So only the tie rule at perpendicular arrivals is missing.
- Mixed56 ties: vertices 12 (7 vs 11), 13 (10 vs 11), 25 (0 vs 35), 34 (5 vs 35), all at step 1.
  Rounds One to Four (Partition/RoundOne..RoundFour, 185 Fusion conversions) moved single grips.
  Site 34 flips to 35 past these thresholds: grip 33 +x at 0.124995..0.124999, 33 +y
  0.215..0.21875, 32 -x 0.1875..0.203, 34 +x 0.1875..0.203, 34 -z 0.125..0.14, 6 +x 0.1875..0.203,
  6 +y 0.156..0.172, 6 -z 0.234..0.25, 35 -y 0.156..0.172, 13 -z 0.172..0.1875. Grip 5, 18 and
  most moves of 12 and 7 never flip it. Z33 flips at both +0.5 and -0.5. X35 -0.5 also flips
  site 12, so ties couple through later events.
- Refuted tie-breaks: straighter ray, lower origin index, cage or limit polyline lengths of the
  whole track or of the next links, forward crossing angle, B-rep edge arc lengths of the two
  outcomes, single cage features and their pairwise differences or ratios.
- More refuted tie-breaks: curvature jumps across the candidate lines, shape of the candidate
  faces (normal spread, speed ratios, skew, corner angles, aspect), order flips of converted pole
  coordinates, and equalities of pairwise distances, angles or dot products of strip grips.
- RoundFive (Partition/RoundFive, 18 conversions): shifting or doubling the whole cage keeps the
  33 +x threshold at 0.124995..0.124999 times the scale. So the tie rule is invariant under
  translation and uniform scale.
- Ties occur only in HeldBand67, Mixed56, Mixed78 and TPrism. Over the 537 stored TSMs and all
  Stencil variant sets, the race without ties equals the old DrawLines.
- Decision (session 11): DrawLines now runs the race and raises ValueError at a tie. Kit refuses
  those four layouts instead of guessing. The old 8 and the other probes and held-out cages have
  no tie and keep converting.
- Race check (session 11): the new lines equal the old lines on 967 stored cages and 91 natives.
  The variant run refuses only the 47 Mixed56 and 59 Mixed78 variants at the tie. The CreasedBox
  natives and 38 crease variants still fail in the crease cap rule, with or without the race.
- Interval held-out (session 11): HeldInterval7 (two-row heptagonal prism, every interval 3) is
  in HeldOut for the final run. Offline, Kit's poles equal those of its unit twin within 3.1e-13.
- Final run plan: PrepareAccept for all cases, AcceptGeneral through RunLocked, then
  CollectAccept.py copy, ScrubSaved.py over Accept/Fusion only, CollectAccept.py cases. The
  committed GeneralAcceptance.json keeps row digests; the full rows stay in Accept/tmp.
- Crease-end caps (session 11): CreaseRows (src) solves caps at an EP with one creased spoke,
  valence 3 and 5 or more (CreaseRuleNotes.md). Fitted on n = 3, 5, 6, 8; n = 7 held out. 109
  caps in 39 saves within 1.6e-13. Darts (valence 4 crease ends, CreasedBox v7) still raise;
  the cap fork now works on them in Poles/ and Caps/.
- Read gaps (session 11, from the coordinator): Intervals/Plane4x4/Half and ColumnRow store
  patch words as doubles (0.5, -1.5); Plane4x4/Single and Box/Single carry one 106ek record per
  edge, equal to the edge interval. Both now read and round-trip byte for byte. ConvertForm
  refuses 106ek values that differ from the intervals. Gotcha text still to add to
  KnotIntervalConversion.md.
- Crease split rule committed (session 11, Crease/CreaseSplitNotes.md): ClassifyEdges cuts a
  bent crease once where its turn changes sign inside a cage span. 155 former refusals match,
  25 still raise, none differ over crease rounds 12 to 21.
- Darts (session 11, CreaseRuleNotes.md): the dart is the n = 4 crease cap with the
  perpendicular spoke poles and the EP as midpoints, plus 10 integer mirror rows (DartRows).
  CreasedBox then matches all 15 native saves within 1.0e-13. Not committed yet: with darts,
  66 CreaseCaps cages convert to a layout that differs from Fusion (an extra face split near
  the crease end, or an extra vertex and edge). The cap fork is finding the layout rule at
  crease ends; until then darts stay out of src.
- Darts and crease-end layout committed (session 11, 5e99779a0): the line past a dart starts one
  round late; uncovered darts, links joining two dart lines and cuts in spans refined from both
  ends raise. CreaseCaps: 17 equal, 0 different, 54 raise.
- Final acceptance run (session 11, Accept/GeneralAcceptance.json, status accepted, 0 documents
  open before and after): 30 of 30 prepared cases accepted within 1e-8 cm, largest gap 2.0e-13.
  Old: all 8 (Box, Box3, CreasedBox, CreasedPlane, Valence5 to 8). Probe: 9. Held out: 13
  (HeldBox113, HeldCrease Bands/Cross/Loop/Ring/Slices, HeldInterval7, HeldPrism3, HeldPrism5,
  HeldTorus75, HeldWeighted6, HeldWeightedSharp, HeldWeightedTorus). Refused by the tie rule:
  TPrism, Mixed56, Mixed78, HeldBand67. Fusion's conversions kept in Accept/Fusion (the scrubber
  changed no byte) and pinned by GeneralAcceptTests; Kit against them offline: 30 equal, 2.0e-13.
- StencilCensus regenerated: 259 equal, 7 different (6 deliberately stale probes and the old Kit
  swap CreasedPlaneFreshKit.f3d), 11 refused (4 ties, 7 interval cases), 2 without a body.
  SwapFormCage now refuses CreasedPlaneFresh (the fresh cage changes a crease class, and Fusion's
  own conversion agrees with Kit), and the other swap payloads changed at bit level. The stencil
  swap documents and TestStencilSwap digests need regenerating.
- Stencil swaps regenerated (6afce2b48, c8d087063): the general-rule swap documents and their
  Fusion run live in StencilAccept/General (7 of 7 accepted, CreasedPlaneFresh refused by Kit);
  StencilAccept/Cases, Saved and NativeAcceptance.json keep the first stencil-table run, so
  StencilAcceptCheck and StencilAcceptGap still match. TestStencilSwap pins the new digests.
- Docs committed (3c2f701a7). Still open: the change entry's general verification section
  (waits for the CreaseRuleCheck replay), the CreaseEdgeClass replay numbers, an audit of the
  Form tests that bf4011a27, 4de2b76e3 and 5e99779a0 left stale (TestCreaseFault expects the
  fresh creased plane split to raise, but it now converts and equals Fusion), and the rebase
  onto a13625323 (take KnotSurface, drop EdgeKnots and CheckEdgeKnots, restore TsmSources.xz
  and PromoteCases.py, update FusionEdgeKnotRows.md for the patch word fix).
- Done (session 11): CreaseRuleCheck regenerated (1484 archives; 41811 of 41863 groups equal,
  38 refused, 14 differ; 793 converted bodies equal, 10 refused, 0 differ). Stale Form tests
  fixed (3fa8d59e4). Rebased onto a13625323: the read gap commit now uses the PR head's
  KnotSurface and CheckKnots; CheckEdgeKnots and the TsplineSurface field are gone, TsmSources.xz
  and PromoteCases.py equal the PR head, and ConvertForm tests isinstance(KnotSurface). Its commit
  message still describes the old field. After the rebase: the four interval files round-trip
  (sorted names equal, only .protein differs), and the 30 accepted cases still equal their
  Fusion saves within 2.0e-13.
- Session 11 closed: every task item is committed on form-general-rules (head e86d2b8df before
  this note). Open research items: tie rule for perpendicular face-line arrivals, uncapped darts
  with plain neighbours, cuts in spans refined from both ends, two creases at one EP, crease caps
  with knot ratio 1/2, mixed or fractional intervals in capped cages.

## Cap declaration qualification

- PrepareCapVariants.py emits G0CAPS, G1CAPS, G2CAPS and star smoothness 0, 1 and 2 through typed SurfaceHeader replacements on Box3 and held-out HeldPrism5.
- ConvertCage now relies on CheckSurface, which admits those declarations and rejects unknown values without a second G1-only gate.
- Local Fusion 2706.1.17 accepted all 11 independently emitted F3D documents through load, computeAll, control-point edit, export and reopen. CapAccept/NativeAcceptance.json records 319 comparisons, zero problems and zero open documents before and after.
- The retained Oracle*Converted controls are under CapAccept/Fusion. ScrubSaved changed zero bytes. ScrubValidation.json records ten identical typed models before and after.
- REA inspected the independent HeldPrism5G2 F3D as a ZIP. ContainerInspection.json binds its preparation digest, 24 occurrences and zero integrity contradictions. This static inventory does not establish runtime semantics.
- Fusion canonicalizes every G0CAPS and G2CAPS input to G1CAPS before editing and after reopen, while star smoothness remains unchanged. Kit still preserves the supplied declaration before native import; do not attribute the canonical export to a Kit data loss.
- Refuted: omitting MassPropertyCacheValue as an empty collection fails the inherited schema with Fusion entity inherited group count differs from its schema.
- The first fresh process 24703 also exposed 30 initial center-of-mass differences across 10 cache variants; Kit loaded all centers as zero before computeAll. InitialMassFailure.json preserves the failed report. Surface integration of the required mass cache is necessary, while the remaining body shapes already match.
- A graceful restart first reported user cancelled -128, then the bridge closed and application running became false. SessionRecovery.json records the guarded subsequent fresh launch; no forced termination or open-document loss occurred.
- Resolved: FormCache evaluates stored bicubic faces with a sixteen-point Gaussian rule. Divergence-theorem area and volume moments become origin-based inertia and off-diagonal terms, with the center computed separately from first moments. CheckTrimming refuses trimmed nonperiodic faces outside full parameter boundaries, and open sheets retain zero volumetric values.
- Fresh process 24703 accepted all 11 final documents with 319 comparisons, zero problems, zero dropped items and zero open documents before and after. NativeAcceptance.json now has SHA-256 55e37af5b25d4603399b042fc8ae1fb8c1dba9639afae4818b4d08ba43e8f109, with vendor_loadable and application_usable true. Initial Box3, HeldPrism5 and off-origin Box3 centers and six tensor components match their native controls before computeAll. Cap aliases are Fusion canonicalization rather than Kit data loss.
- The native API returns one success flag plus six mass-weighted inertia moments. Native Steel controls have density 0.00785 kg/cm3 and Kit has density 0.001 kg/cm3. Direct comparison caused 264 differences in InertiaDensityFailure.json. The final oracle retains those raw material observations but compares volumetric tensors after division by each density.
- Box3ShiftedG2 translates all grips by (13, -21, 42) cm. Its initial center is (14.2, -19.80000255164962, 43.2) cm and edited center is (14.202998017352988, -19.79712185783366, 43.20305682252197) cm. All six normalized tensor components match at every stage. The largest mixed-unit scalar deviation is 2.9103830456733704e-11.
- Review found that PointOnSurface revalidated and lifted every pole for every quadrature point. SurfaceSample now evaluates position and both derivatives from one local pole window, while SurfaceMass hoists expanded knot vectors. A later review found the remaining linear FindSpan calls per quadrature point; KnotSpans now computes every nonzero interval's basis index once, passes them directly and skips zero-width intervals. Full typed validation remains in CheckFormSpec before emission. This removes both whole-net and per-node span-search work from the sampling loop.
- The eight-point and sixteen-point native-cache comparisons failed an exact-area assumption in remote runs 43583291958 and 43584701390, but changing quadrature moved Box3 only 1e-13 cm2 and HeldPrism5 only 3.21e-13 cm2. AreaConvergence.json distinguishes independent numerical estimators; it does not authorize any tolerance relaxation. The 1e-4 proposal was reverted. TestPlanarArea now checks raw area at 1e-8 through the untouched native Plane3x2 fixture. TestShiftMass uses the exact parallel-axis translation invariant instead of equating different curved volume estimators, while the full curved BRep lifecycle remains at 1e-8. The sixteen-node full lifecycle remains accepted as 55e37af5b25d4603399b042fc8ae1fb8c1dba9639afae4818b4d08ba43e8f109.
- ScrubSaved changed two final native controls. All 11 typed models remained identical. ScrubValidation.json has changed_by_scrubber 2. TestShiftMass and TestCapDeclFlow both regenerate archives through the current EmitFormDoc writer; they no longer depend on stored Kit output paths in the staged research subset. TestShiftMass also checks translation area/volume invariance, the translated center and all six components of the parallel-axis origin-tensor formula.
- TestCubeMass builds the closed analytic unit cube with the existing sharp-box cage constructors, converts it, emits a complete document and reads it back. The recovered body and cage must match, and the typed cache is checked for area 6, volume 1, center (0.5, 0.5, 0.5), diagonal inertia 2/3 and off-diagonal products -1/4 at 1e-8. This full writer/reader boundary prevents shared absolute mass-scale errors from passing the translation invariant without introducing a prohibited isolated unit test.

## Open questions

1. Spoke and tangent rule: spoke has 1 free value in mode 0 after constraints; tangent mode 1 is
   not a small rational, so it is probably computed (eigen or solve), not tabulated.
2. Interior poles (2,2), (2,3), (3,3), (2,4), (3,4): rule unknown; delta(2,2) is nonzero but no
   constraint in the current set fixes it.
3. (3,1), (4,1) sums: from G1 on [0, h] and [h, 2h].
4. Valence 5..8 data in hand is not isolated (prism EPs next to valence-3 EPs, h = 1/8).
   Need isolated valence 3, 5, 6, 7 controls: vary one grip at a time and read M from saves.
5. Done by sub-agents: crease label rule (1 degree, Crease/CreaseRule.json, ClassifyEdges) and B-rep
   topology from the cage (Topology/, src Spline/Capped). Not started: SUBD_CREASES poles at
   boundaries and creases, weights, src pole engine, tests, docs, Fusion acceptance runs,
   StencilCensus.json / StencilCheck.json regeneration.

## Next steps

00. Determine the 3n + 2 free cap values: try FP-style sequential least deviation (spoke from G1 and
    netref, then the (1, 1) and first-layer pairs, then the interior), each step a small local solve.
    Fallback: a solve with the exact rows plus one member of the 19-dim q family, validated on a
    held-out valence and on Box3.
0. With the cap prism responses, fit candidate objectives jointly over valences 3, 5, 6, 7, 8 (same
   weights for every valence); hold one valence out. Mode-0 primes for valence 6 (c = 1/2) give a
   second rational fingerprint.
1. (done) Build isolated-EP controls (valence 3, 5, 6, 7 on a large regular grid) and read exact M per
   valence from unit-grip experiments. Compare the cap rows across valences to find the rule.
2. Try sequential construction: spoke from spoke data, (1,1) and first rows from G1 plus split rule,
   interior from C2 rows plus netref twist.
3. If the cap stays unresolved, keep the cap as a computed least-norm or constraint solve whose
   equations come from these notes, and validate against the 12 probe saves.
