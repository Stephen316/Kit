# Crease edge split rule: research notes

Status: ported to `ClassifyEdges.py` (`SpanPieces` with `Curve`, and `WidePieces`, `RootSplit` and their helpers). The port reproduces the prototype on every saved crease group. `GroupPieces` passes `Curve`. Without it, `SpanPieces` raises as before. ruff, black, mypy, pyright and steering are clean. `MeasureTilt.py` and `CreaseTilt.json` hold the per-case terms. `CreaseRuleCheck.py` passes `Curve`. `CreaseRuleCheck.json` was regenerated over 1474 archives: 41742 groups, 41694 equal, 28 refused and 20 different. All 20 differences predate the port: the old rule gives the same pieces. 19 are crease-end cap saves in `General/CreaseCaps/tmp`, and 1 is `FixedRound/LTurnWide`. The refusals are the 25 crease-round cases listed below, plus 1 in FixedRound and 2 in CreaseCaps. These notes record what black-box rounds show about how Fusion splits and labels a Form crease edge in the cases where `ClassifyEdges` raised `KCreaseFault`.

All evidence comes from Kit-authored roof cages. Each one was run through `RunLocked.mjs` with `ProbeCrease.py`.

## Test cages

- A roof is a 2 x ny x 1 box with a creased ridge.
- The fold angle per outer grip row sets the ridge dihedral.
- Along the ridge parameter t, that dihedral ("turn") is close to a uniform cubic B-spline of the row angles.
- The cages come from `CreaseCages.py`.
- Saves land in `LocalOracle/FormDocuments/Crease/tmp/<Round>/`, which git ignores.

## Ridge curve knots

The ridge curve has cage knots 0, 1, ..., n. Near each end it also has refinement knots at L/8, L/4 and L/2. Fusion never splits at those refinement knots. It splits only at a cage knot or at the root.

## Mirror rule (ported)

This rule covers a flat knot, meaning the turn there is within `KFlatTurn`, between a tangent piece and an unknown piece that face opposite ways. Fusion keeps the edge whole across the knot exactly when the turn is odd about the knot over one span on each side. That means:

- the two spans have equal parameter length;
- turn(z - d) = -turn(z + d) at the samples, within `KFlatTurn`.

`IsMirrored` and `IsBreak` implement this rule.

## Wide tangent run with an off-knot root (I-type)

### When it applies

- The root r lies inside a cage span: c_j < r < c_(j+1).
- Both sides are unknown.
- The turn stays within 1 degree for more than a span around r.

In this case Fusion splits once, either at a cage knot or at r.

### Terms

- **Cage knots c.** The edge ends plus the inner knots, with the end refinement knots removed.
- **first.** The smallest index such that [c_first, r] is tangent, that is, its peak |turn| is at most 1 degree.
- **last.** The largest index such that [r, c_last] is tangent.
- **Confinement.** The left is confined when first == 1. The right is confined when last == len(c) - 2.
- **Split candidates.** L1 = c_1, L2 = c_(first+1), R1 = c_(len-2), R2 = c_(last-1). Use L2 only when L2 <= c_j, and R2 only when R2 >= c_(j+1). Otherwise use r.
- **Crossing slopes.** a and b are the 1 degree crossings of the turn nearest to r. The crossing slopes are |turn'(a)| and |turn'(b)|.
- **tilt.** tilt = (|turn'(b)| - |turn'(a)|) / max of the two.
- **Leaning.** The left is steeper when tilt < -KTangentTurn^2. The right is steeper when tilt > KTangentTurn^2.
- **Steep side.** A side is steep when the turn rate on it exceeds KTurnRate = 0.01 rad per unit length.

### Rule

0. **Run.** If [c_j, r] or [r, c_(j+1)] is not tangent, raise.
1. **Steep root.** If the turn rate at c_j or c_(j+1) exceeds 0.01 rad, split at L2, or at r if L2 is not usable. The rate at a knot is the central difference over knot +- (shortest cage span / KCreaseSamples), clamped to the edge.
2. **Neither side confined:**
   - with no lean (|tilt| <= KTangentTurn^2), split at r;
   - with a lean, raise. Fusion picks a run knot here: `LeanNeitherLeftKink` gave c_first and `LeanNeitherRightKink` gave c_(last-1). Two cases do not fix a rule.
3. **Left confined:**
   - if the left is steeper or the left is steep, split at L2 (or r);
   - otherwise, if the right is confined or the right is steeper, split at r;
   - otherwise, split at L1.
4. **Only the right confined:**
   - if the right is steeper or the right is steep, split at R2 (or r);
   - otherwise, with no lean, split at R1;
   - otherwise (the left is steeper), split at r if the left is steep, and raise if it is not. Fusion gave c_5 on three ny = 8 cages (`FinMirKinkL0p5R0p53P4`, `LeanMirKinkL0p5R0p53P3`, `LeanMirKinkL0p5R0p55P4`) but r on the ny = 10 cage `LeanMirKinkL0p45R0p5P5Ny10`.
5. **Labels.** Both pieces stay unknown. Each piece is relabelled with `PieceClass`.

A steep test reads every consecutive sample pair on the side, both per parameter and per cm of chord. If the two verdicts disagree, the rule raises (see the slope unit section). The tilt uses central differences at a and b with step `KSeamSlack` times the cage range. Rounding then gives a relative error of 1e-5 to 5e-5, which is under KTangentTurn^2, and the step never straddles a knot.

### Constants in the port

- `KTurnRate = 0.01` rad per unit. On unit cages the threshold lies between 0.5725 and 0.5735 degrees per cm, and 0.01 rad is 0.57296 degrees, so this is Fusion's own 0.01 rad, not a fitted value.
- `KEndHalves = (8, 4, 2)`. Fusion's end refinement puts knots at L/8, L/4 and L/2 of the first and last cage spans. `CageKnots` drops them, matched to within `KSeamSlack` of the span.
- The tie tolerance is `KTangentTurn * KTangentTurn`, derived below.

### Why the tie tolerance is KTangentTurn^2

At a crossing the turn is exactly KTangentTurn. The turn is the angle between blended normals, so it differs from a linear blend of row angles by terms of relative size theta^2. That residue makes the two crossing slopes of a symmetric cage differ by a relative amount up to KTangentTurn^2, about 3.0e-4.

| Measured | Relative slope difference |
| --- | --- |
| Largest on 45 symmetric cages, step 1e-4 | 6.2e-6 |
| Largest of 119 ties over all saves, port step (`MeasureTilt.py`, `BothS0p4Z2p9`) | 4.9e-5 |
| Smallest real asymmetry (`RchNy10S0p55Z2p3K0p6P5`) | 6.3e-4 |

`MeasureTilt.py` computes these terms with the `ClassifyEdges` helpers for every wide-root group in the saved crease rounds and writes `CreaseTilt.json`. Over 183 groups, 158 match Fusion's cut, 25 raise and 0 differ.

The tangent half widths b - r and r - a separate the same cases with a much smaller gap: ties reach 1.6e-6, and real asymmetry starts at 2.4e-5. So the port uses the slope comparison.

### Slope unit is undecided, so the port raises when the units disagree

On unit cages the steep threshold falls between 0.5725 and 0.5735 degrees per cm, which is 0.01 rad. Stretching and scaling the cage move it:

- **Stretch along the ridge, span length L.** The threshold goes like L^p with p between 0.63 and 0.89.
  - L = 0.5: steep at 0.37 per parameter, shallow at 0.31.
  - L = 0.8: steep at 0.50, shallow at 0.47.
  - L = 1.04 and 1.05: steep at 0.6.
  - L = 1.25: shallow at 0.66, steep at 0.70.
  - L = 2: shallow at 0.88.
- **Uniform scale.** It moves the threshold less than stretch does. At scale 0.5, 0.37 is shallow. At scale 1.25, 0.66 is steep.

The port decides steep or shallow only when the per-parameter and per-cm rates agree. Otherwise it raises. That covers 19 stretch and scale cages.

### Asymmetry evidence (left priority)

| Case | Fusion | Its mirror | Fusion |
| --- | --- | --- | --- |
| KinkSteepEndLong | L2 | HoldMirKinkSteepEndLong | r |
| BothS0p4Z2p7EndLeft | L2 | BothS0p4Z2p7EndRight | r |
| Ny8BothS0p3Z3p95EndLeft | L2 | Ny8BothS0p3Z3p95EndRight | r |

Turning the cage 180 degrees, or 45 degrees with a shift, leaves the split unchanged. The left preference follows the curve parameter, not space.

### What decides blocking

These hypotheses are refuted by rounds 17 and 18:

- steep anywhere on the far side;
- steep within c_(last+2);
- steep within 3 of r;
- steep start within b + 1;
- turn at the steep start below 1.5 degrees.

Blocking happens exactly when the kink's B-spline support reaches the crossing on the far side. That is what the crossing-slope comparison measures.

## Rounds

| Round | Cages | Role | Result under the final rule |
| --- | --- | --- | --- |
| 12 to 15 | 82 | fit | all I-type cases match |
| 16 | 18 | held out for the earlier CR2 rule | 12 of 17 matched; the misses gave the length unit, left priority and limited blocking |
| 17 | 19 | fit: blocking reach, both ends confined, threshold pins | match, except stretch 1.05, which raises |
| 18 | 24 | fit: stretch and scale sweep, blocking sweep at ny = 10 | match, except 15 unit-ambiguous cages, which raise |
| 19 | 18 | held out for the half-width rule | 16 of 18 matched; `HoldShortLeftShallow` and `HoldShortLeftShallowBlk` gave L2, which led to the "left steeper" test |
| 20 | 16 | held out for the slope-tilt rule (R5) | 15 of 16 matched; `FinMirKinkL0p5R0p53P4` (right confined, shallow left lean) gave c_5 against R5's r and now raises |
| 21 | 10 | exploration of the lean branches | every decided case matches (`LeanLeftSteepRightSteeper` and `LeanLeftSteepRightSteeper2` give c_2, `LeanMirEndLeftMild` and `LeanMirKinkL0p5R0p6P6` give c_7, `LeanNeitherLeftSteep` gives r); the other five raise |

Totals for the port, `SpanPieces(..., Curve=...)`, which equal the prototype group for group:

- Rounds 12 to 21: 3832 groups. 3677 were already decided and still match, 155 that used to raise now match, 25 still raise, and 0 differ.
- The 25 that raise are 19 unit-ambiguous stretch or scale cages from rounds 16 to 18, 2 unconfined lean cages and 4 right-confined shallow-left lean cages.
- Older rounds (Pilot, One to Eleven, FixedRound): 2989 match, including 3 that used to raise, and 1 still raises. The one difference is the pre-existing `FixedRound/LTurnWide`.
- Held-out scores before each refit: round 16 12/17, round 19 16/18, round 20 15/16.
- Out of sample, from cages built by the crease-end cap work (`General/CreaseCaps/tmp`, 2472 groups): the port matches the 1 wide-root case the old rule refused (`Crease4L2S0_2`, cut at 0.25), 2 still raise, and nothing else changes.
