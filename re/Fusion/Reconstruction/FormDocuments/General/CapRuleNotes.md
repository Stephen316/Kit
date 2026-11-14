# Cap rule notes

Research notes for the G1 cap at an extraordinary point (EP). Short plain sentences.

## Setup

- Each sector of an EP has knots 0⁴, h², 2h², then the next knot.
- h is a quarter of a face for level-2 caps and an eighth for level-3 caps. HeldBox113 uses level-3 caps.
- The span after 2h is L. Write r = L / (h + L).
- L = 2h gives r = 2/3. L = h gives r = 1/2. Coupled EPs, where two caps share a face, have r = 1/2.
- An EP can mix both values: per sector and per direction ("mixed" corners).
- The cap unknowns per sector are the poles with i, j ≤ 4 except (4,4).
- Poles outside the cap keep netref to 1.5e-13.
- netref is the blossom of the Catmull-Clark net at the real knots. The net level matches h. The EP is the Catmull-Clark limit.
- δ = cap pole − netref, with netref(EP) = EP.
- c = cos(2π/n) and κ = (n − 4)c/(n + 5).

## Known rows

- G1 on the spokes over [0, 2h] with λ = 2c(1 − 2x/3) on [0,h] and 2c(2 − x)²/3 on [h,2h].
- Q: the spoke third difference is zero on [h,2h].
- C2 at 2h on pole rows 2 and 3, in both directions of every sector.
- EP = Catmull-Clark limit.
- C2 at 2h gives δP4 = r δP3 on each knot line.
- G1 samples beyond 2h are not needed. They also fail at mixed corners, so the rule leaves them out.

## Local relations (2-sector window)

- Take a window of two sectors around one spoke. Every linear relation that δ satisfies inside that window is linear in c.
- Index-4 keys also carry an r term: coefficient a + b c + r (a' + b' c).
- The first version kept 25 numerically fitted directions (CapRuleWindow.json, now deleted). That was a float table, and it was not
  mirror invariant. CapRule no longer loads it. The exact relations below replace it.

## Window relations (exact)

- Notation around spoke k: S is spoke k, S′ the far spoke of a sector. A is sector k, B is sector k − 1.
- X(i, j) is a pole of a sector seen from spoke k: i runs along spoke k, j away from it.
  For A this is A(i, j). For B it is the mirror image B̃(i, j) = B(j, i).
- The mirror across spoke k swaps A and B̃ and swaps spokes k − 1 and k + 1. Each relation is even or odd under it.
- All coefficients are integers. r is the knot ratio of the direction in which a key has index 4.
- Split rule (i = 2, 3, 4): δB(1, i) = δA(i, 1). The first pole rows on the two sides of a spoke move together.
  With G1 this also gives δS4 = δA41 = δB14. That even half follows from G1, so it is not a separate row.
- Sector balance (per sector, symmetric in i and j):
  δA41 + δA14 − 2(δA21 + δA12) + 2(δA31 + δA13) + 8(δA22 − δA23 − δA32 + δA33) = 0.
- Spoke balance (per sector, summed over its two spokes):
  32 δA33 − 8(δA13 + δA31) + Σ_spokes [−8 δS1 + 16 δS2 − 12 δS3 + (4 + r) δS4] = 0.
- Cross-spoke even relation: g(A) + g(B̃) = (36 − 28c) δS1 − (66 − 54c) δS2 + (78 − 70c) δS3, with
  g(X) = (18 − 18c) X11 + (−33 + 27c) X21 + 8c X12 + (39 − 19c) X31 − 8c X13 − 32c X32 + 32c X33.
  All terms are δ values. With the split rule, the c-free part of the relation is
  18(δB11 + δA11 − 2 δS1) − 66(δA21 − δS2) + 78(δA31 − δS3): a weighted sum of cross-spoke first differences.
- Cross-spoke odd relation: f(A) = f(B̃), with
  f(X) = (9 − 28c) S′1 + (−12 + 56c) S′2 + (−24 + 24c + 3r) S′4 − (24 + 64c) X22 + (24 − 192c) X23
  + (24 + 128c) X32 + (72 + 384c) X33, all terms δ values.
  So one interior quantity is continuous across the spoke.
- Count: the other rows (hard, EP, ring, tangent, alternating) leave exactly 7n directions. These are seven rows per spoke.
  Dropping any one of them loses n directions in every carrier.
- How they were found: the null space of δ on the 43 window keys, stacked over the carriers, in the coefficient form
  above (116 unknowns, rank 59, clean gap 8e-5 to 1.1e-12). Then an RREF with late pivots, rational reconstruction,
  a greedy search for the smallest supports that still raise the rank, and a split into mirror-even and mirror-odd parts.
- The rational reconstruction errors were 1e-9 to 1e-10. The integer rows hold on Fusion's δ to ≤ 3.8e-12 (relative)
  on all 14 window carriers.
- Data: the window carriers CapPrism3, 5–10, 12, Box3, Valence5:10, 6:12, 7:14, 8:16 and Valence5:0.
  Not used: Box3:3, Valence6:13, 8:17, 6:0, 7:0, 8:0, 7:3, 8:5 and every HeldOut save.
- The data hold only r = 1/2 and r = 2/3. An r term is fixed only up to a multiple of (2r − 1)(3r − 2).
  The rows use the linear form.

## Remaining freedom

- After G1, Q, C2, EP and the seven window relations per spoke, n + 2 directions stay free.
- They are the twist A11 of every sector, plus the tangent plane (S1 in Fourier modes ±1).
- Fusion fills them globally. A grip at one sector moves δ in far sectors too.

## Ring rule (all modes, isolated and coupled)

- Per sector k: L_k = c·δA11_k − b2(δS2_k + δS2_k+1) + b3(δS3_k + δS3_k+1).
- Per spoke k: ½(L_k−1 + L_k) + b1(δS1_k−1 + 2δS1_k + δS1_k+1) = −κ(nS1_k − EP) − (9c/(n + 5))·mean_j(nS1_j − EP).
- nS1 is the net row of spoke pole 1. The right side uses only the net and the EP.
- r = 2/3: b1 = 37/104, b2 = 83/52, b3 = 86/52. r = 1/2: b1 = 9/40, b2 = 21/20, b3 = 6/5.
- The same κ and 9/(n + 5) hold for both r.
- The earlier form had −κ·δS1_k and −(9c/(n + 5))·mean(δS1) on the left. It held in every mode except ±1.
- The key observation: in mode 1, Fusion's ring residual is exactly −κ times x̂S1, Fusion's own tangent ring. Read off at n = 3, 5 and 6: −1/16, −c/10 and −1/11.
- x S1 − EP has only modes ±1, so the two forms agree in every other mode. Moving those terms onto the net gives one rule for all modes.
- Fit: the r = 2/3 constants come from the per-mode analysis of the cap prisms (n = 3 to 12). The mode-1 form was read off n = 3, 5 and 6.
- r = 1/2 constants were fitted on Valence5:10. Valence6:12, 7:14 and 8:16 give the same constants on their own.
- The isolated rule's held-out check is HeldBox113 (level-3 caps). The coupled rule's held-out checks are the coupled EPs of HeldPrism3, HeldPrism5 and HeldBand67.

## Tangent rule (modes ±1)

- In mode 1, the spoke classes δS1, δS2 and δS3 have rank 2. The relation is the tangent rule:
  Σ_k (cos, sin)(2πk/n)·[T_k + c·V_k] = 0, with T_k = 2b1 δS1_k − b2 δS2_k + b3 δS3_k.
- r = 2/3: V = (−17 δS1 + 16 δS2 − 49 δS3)/468. In integers: 9(37 S1 − 83 S2 + 86 S3) + c(−17 S1 + 16 S2 − 49 S3) = 0.
- r = 1/2: V = −(δS2 + δS3)/24. In integers: 6(9 S1 − 21 S2 + 24 S3) − 5c(S2 + S3) = 0.
- The T part shares b1, b2 and b3 with the ring rule.
- r = 2/3 fit on n = 3 and 6 (exact rationals). Held out n = 5, 7, 8, 9, 10, 12 and Box3: ≤ 3.6e-11 relative.
- r = 1/2 fit on n = 5, 6 and 7. Held out n = 8: 1.7e-12.
- The mode-1 data per case span only three directions over the grips, and the net spoke rows S1 to S3 span the same three.

## r between the two measured ratios

- Only r = 1/2 and r = 2/3 occur on unit-interval cages, so only these two were measured.
- With t = 6(r − 1/2): b1 = 9/40 + 17t/130, b2 = 21/20 + 71t/130, b3 = 6/5 + 59t/130.
- And v1 = −34t/936, v2 = −1/24 + 71t/936, v3 = −1/24 − 59t/936.
- The r-dependent parts of T and V are the same combination 34 S1 − 71 S2 + 59 S3, scaled by t/130 and −t/936.
- The linear-in-r form is exact at both ratios. It is not tested between them.

## Alternating twist (even n)

- The pair sum in the ring rule hides the alternating mode of the twist. In that mode only A11 moves.
- Fusion scales it exactly: Σ(−1)^k x_A11,k = (9/(n + 5)) · Σ(−1)^k netref_A11,k.
- This is the Loop–Schaefer twist mask (n v + 2(e_k + e_k+1) + f_k)/(n + 5) in that mode, because netref A11 is the regular mask (4v + 2(e + e′) + f)/9.
- It holds for isolated n = 6, 8, 10 and 12, and for coupled n = 6 and 8 with no change.

## Mixed corners and refused spokes

- Mixed corners use r per spoke in the ring and tangent rows and r of the key's index-4 direction in the window rows.
- At mixed corners, the old G1 samples beyond 2h failed on Fusion's poles at about 1. The rows on [0, 2h] hold.
- Two EPs of HeldBand67 (v1, v5) have a spoke whose two sectors see different spans after 2h: r = 1/2 on one side, 2/3 on the other.
- There the shared spoke pole 4 cannot serve both sectors. Fusion's hard rows fail at about 0.2 to 0.3.
- CapRule refuses that case instead of returning wrong poles.

## CapRule.py

- One entry point: cap_rows(request). The request carries what src's CapInput holds: Valence, Sectors with KnotsI and KnotsJ, Reference, Limit and Unknown.
- Reference must also hold the poles of keys outside the cap that the hard rows touch (indices up to 7).
- It builds the hard rows from the knots, then adds the window, ring, tangent and alternating rows. It solves once and returns a grip row for every unknown key.
- No free directions remain. A rank loss raises ValueError.
- It refuses creased EPs, other unknown sets, and spokes whose two sides disagree on r.
- No Fusion data, no JSON and no per-valence or per-layout table. Valence enters through c, κ and 9/(n + 5); knots through r.
- The window rows are the literal integer table WINDOW, written in local names around one spoke.

## Validation of cap_rows

- Carriers compare grip-coefficient rows. The worst per-pole error is the largest coefficient difference over all cap poles.
- Isolated (CapPrism3, 5–10, 12, Box3 both EPs): worst 5.9e-13 (CapPrism7). The fitted window family gave 1.0e-11.
- Coupled (Valence5:10, 6:12, 6:13, 7:14, 8:16, 8:17): worst 3.4e-13.
- Mixed (Valence5:0, 6:0, 7:0, 8:0, 7:3, 8:5): worst 1.5e-14. These six corners share one geometry.
- Held-out Fusion saves compare xyz poles in model units. The caps reach 0.15 to 0.65 from the EP. Nothing in the rule was fitted on them.
- HeldBox113, 8 isolated level-3 EPs: worst 2.4e-13.
- HeldPrism3, HeldPrism5 and HeldBand67, 9 coupled EPs with n = 3, 5, 6 and 7: worst 1.8e-13.
- The same three cages, 24 mixed EPs: worst 6.9e-14.
- HeldBand67 v1 and v5 are refused (see above).
- Mirror test: every request was solved again with the sector order reversed (KnotsI and KnotsJ swapped, keys remapped).
  Worst relative gap: 1.0e-12 over the 22 carrier caps and 4.9e-13 over the 41 held-out caps.
  The fitted family failed this test at mixed corners (4e-2 in the src port).
- HeldWeighted6 is out of scope. Its EP is not the plain Catmull-Clark limit, and the plain net misses its poles.

## Lead tested: least-squares fit to limit points

- Test: does Fusion's cap satisfy the KKT conditions of a least-squares fit of the cap surface to Catmull-Clark limit points, with the hard rows as constraints?
- Each sample orbit (a point and its mirror, in every sector) got a free weight. A real fit shows as a null vector of the weighted KKT system.
- Pools: the knot grid (multiples of h), level-3 points up to 3h/2, and level-4 points up to 7h/4.
- Over the hard-row complement, the smallest singular value matched the control (x moved along feasible directions): 3.4e-2 for both on level 3.
- Over the n + 2 free directions only: level 2 gave 2.3e-2 against a control of 8.6e-3, and level 3 gave 1.8e-3 against 2.7e-4. Fusion is no closer than the control.
- Level 4 is underdetermined, so both have null vectors.
- So the limit-point fit lead is refuted for these sample sets. The rule is algebraic instead.
- Also refuted, with controls: a diagonal per-class metric projection onto the hard rows, with netref targets or ACC twist targets. Both show only the trivial null vectors.
- The ACC twist mask p11 is not Fusion's twist plus a multiple of δS1 in any mode (residual 2e-3 to 0.8).
- x̂S1 is not in the span of the level-2 one-ring (e, f) in mode 1 (residual 6e-3). So the tangent is not a limit-tangent mask.

## Energy tests with controls

- The KKT tests run against controls on the same free directions.
- No per-sector or spoke-window quadratic energy in δ explains Fusion.
- Without controls these tests mislead. Trivial energies built from known rows fill most dimensions.

## Refuted

- Quadratic energies per sector, per spoke window, and per two-sector window.
- Minimum-norm δ in the pole, Bezier and L2 metrics along the free directions.
- The FP11 Step 2 and Step 5 twist rules.
- Pointwise derivative identities at the EP.
- Integral functionals.
- Least-squares fits to limit points on the h, h/2 and h/4 grids.

## Open

- The r-dependence between r = 1/2 and r = 2/3 is untested. Unit-interval cages produce no other ratio.
- The cross-spoke relations have no full geometric reading yet. Their c-free parts read as weighted cross-spoke differences.
- Spokes whose two sides see different spans after 2h need split spoke keys.
- Creased and weighted EPs.
