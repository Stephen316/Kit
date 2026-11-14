# Crease cap rule (caps where CapInput.Creased has a True entry)

## Status (2026-11-13)

- Proven: single-crease EP caps, n = 3, 5, 6, 7, 8. The rule below reproduces Fusion's cap poles exactly.
  - Fitted on CreaseCaps (n = 3, 5, 6) and CreaseCapsMore (n = 8).
  - Held out: CreaseCapsHeld (n = 3, 5, 6, 7, 8; n = 7 never fitted) and OracleCreasedBox Fresh / Bent / Sheared v13.
  - Max error is 1.2e-13 on fitted caps and 9.7e-14 on held-out caps.
- Darts (n = 4) are solved; see "Status: darts" below. src converts all 15 CreasedBox saves.
- Not covered: two creases at one EP, and r = 1/2 creased caps (all crease data has r = 2/3).
- Ported:
  - src Caps/CreaseRows.py. SolveCaps routes creased requests to it. The hook sits on the current LeastSolve and leaves it untouched.
  - Research rule: CreaseRule.crease_cap_rows.
- Checked against native saves (single-crease EP caps, n != 4), src path: 109 caps in 39 saves, max gap 1.6e-13. This includes OracleCreasedBox Fresh / Bent / Sheared v13, at 8.5e-14.
  - The research rule matches on the same 109 caps, max 6.9e-13.
  - The crease-length-3 saves (Crease3L3, Crease5L3) cannot be matched to native faces. src refines the crease-through vertex and Fusion does not.
- Dart findings (before the rule):
  - The dart CapInput has 68 unknowns. The two spokes perpendicular to the crease are neither Unknown nor in Reference nor placed, and their G1 rows lack far reference poles.
  - Confirmed on CreasedBox v7: the sector knots across that line start (0, 2), not (0, 4). Sectors 0 and 1 place into one native region, and sectors 2 and 3 into another. Fusion keeps one C1 face on each side of the crease line, with no poles on the perpendicular line. The EP is not an unknown.
  - With them as free unknowns, the EP rule leaves 14 free directions at n = 4 and misses by 1.6e-3.
  - The dart needs its own unknown set, defined from how Fusion's face crosses the perpendicular line, before a rule can be read off.

## Status: darts (solved, src ported, not committed, 2026-11-13)

- Data: 67 dart caps, from the L1 ring darts, Dart*.f3d and CreasedBox v7.
- Proven:
  - Fusion's dart poles are the clamped four-sector crease cap at n = 4, merged into one C1 face on each side of the crease line.
  - Completing the poles makes every row of the n = 4 crease rule hold on Fusion to 9e-13: hard rows, pins, windows, ring, tangent, twist, odd sum, w0, and odd@1 = 0 (u = 0). The completion is:
    - perpendicular spoke poles = 1/2 (n(in,k,i,1) + n(in,k-1,1,i));
    - EP = 1/2 (S0.1 + S2.1), which equals the Limit to 2e-15.
- At n = 4 these rows leave 10 free directions (c = 0 degenerates them): 5 mirror-even, 5 mirror-odd. They move only the perpendicular spokes and the sector interiors. They leave spoke 2 and the poles next to it alone.
- Fusion's completed delta lies in one fixed 6-dim key subspace B for all 67 caps (5 mirror-even, 1 mirror-odd; singular values after the 6th are below 4e-13). All dart caps have h = 1/8 and r = 2/3.
- B meets null(M) in 2 directions (M B singular values 2e-7 and 8e-9 are noise), so "8 homogeneous + 2 right sides" stands. The M right sides have rank 4 on darts, all from the kept hard rows. A11 = 0 on the net at n = 4, as the identity predicts.
- Solved (2026-11-13): 10 integer relations on crease-mirror orbits, read by LLL (float, K = 1e9) from the 38 fit caps (Crease3/5/6 L1) only.
  - A term (Offset, i, j, w) means w (d(key) + p d(mirror key)), with parity p = +1 for even rows and -1 for odd rows. Keys on the crease line count once.
  - 5 odd rows, all homogeneous. Example: d(in,1,2,2) - d(in,0,2,2) - (mirrors) = 0, i.e. the alternating A22 sum.
  - 3 even homogeneous rows.
  - 2 even rows with net right sides: one equals U1 - U2, the other -U2 + 2 A12 - A22.
  - Orbit terms per row: 2-19, 77 in total. Coefficients lie in -2..8.
  - The table is src Caps/DartRows.py KDartRows (scratch: crdorb.py, crdtable.py).
- Evidence:
  - Full rank 77 with M.
  - Fusion's completed delta, fitted caps: 3.2e-15.
  - Held out, max 4.7e-15: Crease6L1S02, Crease7, Crease8, CreasedBox v7 Fresh / Bent / Sheared and Dart*.f3d (29 caps).
- src (not committed):
  - Caps/DartRows.py has IsDart, DartSpoke, DartHidden, MiddleRows (the 8 perpendicular midpoints plus EP = 1/2 (S0.1 + S2.1)) and the KDartRows table.
  - CreaseRows.py splits CreaseBody off CreaseRows.
  - SolveCaps.py: DartReference fills the perpendicular spoke reference rows (index 1-7) with midpoints. The layout uses all 77 keys, and only the Unknown keys are returned.
- Native checks, src path:
  - all 15 CreasedBox saves: max 1.0e-13;
  - Dart2, Dart5, Dart20: 1.4e-14;
  - uncreased natsrc lines identical (76 lines);
  - heldsrc (7 cases) and probesrc (17 cases, one process each): output identical to the committed SolveCaps;
  - cap poles alone (crrule4.py, src SolveCaps): 64 dart caps in the L1 and Dart saves, max 1.4e-14;
  - checks.sh on the three src files: ruff, black, mypy, pyright and steering all pass.
- Left outside the cap rule:
  - Dart0p5 and Dart1 fail earlier, in Stencil/ClassifyEdges ("may split or reclassify a crease edge").
  - The L1 prism saves convert but differ in edge layout (edge heads, curve forms).
  - Crease4L1S0 stops in Conversion/SpokeIndices ("needs four spokes per vertex").
  - Crease6L1S02 has two creases at one EP, which is not covered.
- Earlier: B's rational forms have large denominators, and sparse relations in B's complement looked accidental. Orbit LLL fixed this.
- Refuted (each fails at 1e-1 or worse):
  - the c -> 0 limit of the crease rule: solving at c = eps diverges like 1/eps;
  - C2 across the perpendicular spokes: X has only the midpoint (C1) relation there;
  - min-norm of delta under I, membrane or thin-plate metrics on the free directions;
  - per-sector tensor profiles: B uses full-rank i and j profiles;
  - B inside the span of the hard, G1 or M rows.
- Limits: the dart rule covers r = 2/3 and h-scaled knots only, the same as CreaseBody, which refuses other ratios.

## Status: crease-end layout (rule found, src ported, not committed, 2026-11-13)

- Data: the 71 CreaseCaps saves in three manifests (CreaseCaps.json fit, CreaseCapsMore.json n = 8, CreaseCapsHeld.json held-out layouts and seeds). The dart caps alone made 66 of them convert silently to a wrong layout.
- Face-line rule (Capped/DrawLines.py):
  - The ray past a dart (the straight continuation past a crease end) starts one round after the extraordinary-point rays.
  - Everything else is unchanged: head-on meetings draw, passed vertices become stops, ties raise.
  - Kind A (L1, the line past the dart ran down the side band) comes from the rim corners. Their rays reach the spoke end in round 3 together with the dart ray, and the vertex is head-on, so the dart line stops there as in Fusion. At L2 the dart ray reaches the rim first and runs down the side, also as in Fusion.
  - Fit (CreaseCaps.json, 48 cages): delay 1 gives 48 of 48 equal face lines. Delay 0 gives 24 of 48 and delay 2 gives 24 of 48. L1 and n = 4 need a delay of at least 1; L2 needs at most 1.
  - Held out: CreaseCapsMore.json 8 of 8; CreaseCapsHeld.json 13 of 15 (delay 0: 9, delay 2: 4).
  - Misses: the two L3 cages, where the crease reaches the rim. There the two dart rays share the side link head-on, Kit draws it, and Fusion leaves it out. DrawLines now raises for a link that joins two crease ends.
  - Scratch: linesonly.py (face lines only, no conversion), drawcmp.py, drawdbg.py.
- Darts Fusion leaves alone (Capped/CappedLayout.py CheckDarts):
  - Fusion refines and caps a dart only next to a cap point or corner (an EP), or next to a crease running through a neighbour off the dart's own crease.
  - Covered and matching: CreaseCaps L1 n != 4 and CreasedBox (EP next to the dart); Dart2/5/20 (two darts between crease lines).
  - Not covered: L2 darts (the neighbour is the crease's own through vertex) and the n = 4 centre crease (two darts, plain neighbours).
    - Fusion's faces there carry no dart refinement knots. Uncapping these darts makes the knots equal, but poles still differ by up to 1e-1. Within a face, they differ only in the boundary row along the line through the dart, decaying away from it.
    - Kit's capped surfaces differ geometrically by 5e-2 to 2e-1.
    - So CheckDarts raises for uncovered darts on the cap path. Compound (grid) surfaces such as CreasedPlane skip the check.
  - L2 vertex placement (Fusion's vertex X between the dart and the rim, no vertex at the dart) and the n = 4 vertices therefore stay unsolved behind this refusal.
- One-cut crease split in a dart span (Stencil/ClassifyEdges.py CheckCuts; the parent approved this narrow guard):
  - In L1 the crease span [0, 1] holds both the EP halving knots (1/8, 1/4, 1/2) and the dart knots (7/8, 3/4). IsHalving then strips neither end.
  - In 6 cages Fusion cuts at one of these knots (0.5, 0.75, 0.25) while Kit cuts at the root: 3L1S0_1, 5L1S0_1, 5L1S0_3, 6L1S0_0, 7L1S0_0 and 8L1S0_1 bottom. Fusion's root cuts in such spans (6L1S0_4, 7L1S0_4, 8L1S0_1 top) did match.
  - The guard raises "may split or reclassify a crease edge" for any turn-sign cut inside a span whose two ends both carry their 1/8 and 1/4 knots.
- Result, CreaseCaps (dirsrc): 17 equal, 0 different; 54 raise.
  - 45 raise on the dart check: L2, n = 4 and L3.
  - 8 raise on the cut guard.
  - 1 raises on a two-crease EP (Crease6L1S02).
- Other checks on the final src:
  - natsrc: identical to the dart run (91 lines). Against HEAD, only the 15 CreasedBox lines change, and they now match where they used to raise.
  - Dart2/5/20 match to 1.4e-14. Dart0p5 and Dart1 raise in ClassifyEdges, as they did before this change.
  - heldsrc (14 HeldOut cages) and probesrc: same as HEAD, run one process per case (heldprobe.sh).
  - checks.sh: ruff, black, mypy, pyright and steering all pass.
  - CreaseRuleCheck (scratch copy crc_copy.py, against HEAD via headrun):
    - Part one: 41702 equal, 14 different, 38 refused (HEAD: 41706, 20, 28). Every change is inside CreaseCaps: the 6 misses, the 3 root cuts and Crease4L2S0_2 are refused now, and that cage's conversion already raises on the dart check. No crease-round group moved.
    - Part two: 69 new accept_equal rows (CreasedBox, CreaseCaps, Dart2/5/20) and 10 new refusals (Dart0p5, Dart1 and the 8 guarded CreaseCaps). No row left accept_equal.
  - A first version of the guard tested any knot pair around the cut. It hit pairs several cage spans apart (with integer knots, (0, 8) carries knots at its 1/8 and 1/4 marks) and refused 82 crease groups that HEAD gets right. The span must hold nothing but the two ends' refinement knots (1/8, 1/4, 1/2 from each end).
- src files: Capped/DrawLines.py (DartOrigins, delayed start, link-joining-darts refusal), Capped/CappedLayout.py (IsDartPoint, IsHubPoint, IsDartCovered, CheckDarts), Stencil/ClassifyEdges.py (IsBothMarked, IsTwoEnded, CheckCuts in SpanPieces), plus the dart work in Caps/.

## Rule

Notation:
- The crease is rotated to spoke 0.
- delta = pole - netref, with netref(ep) = Limit.
- c = cos(2 pi / n).
- Net sums run over all sectors k and are taken relative to the EP:
  - A11 = sum_k (nA11_k - EP)
  - A22 = sum_k (nA22_k - EP)
  - A12 = 1/2 sum_k (nA12_k + nA21_k - 2 EP)
- Crease defects: U_i = 1/2 (nA(i,1)_0 + nA(1,i)_{n-1}) - nS(0,i). At a smooth spoke the same expression is 0.

Rows:
1. delta = 0 on the EP, on spoke 0 (i = 1..4), on (in, 0, i, 1) and on (in, n-1, 1, i) (i = 2..4).
2. Hard rows: drop G1 (12 rows) and Q on spoke 0. Keep every other hard row.
3. Window rows (CapRule.WINDOW):
   - keep every split, sector balance and spoke balance;
   - keep cross-even except at spoke 0;
   - keep cross-odd except at spokes 1 and n-1;
   - add odd@1 + odd@(n-1) = 0.
4. Ring rows: CapRule.ring_rows with the left side unchanged. The right side is taken from netref with nS1_0 replaced by V = 1/2 (nA11_0 + nA11_{n-1}).
5. Tangent: keep only the mode-1 row that is odd about spoke 0 (CapRule.tangent_rows[1]).
6. Even n: the alternating twist row, unchanged.
7. w0 relation (homogeneous, on delta), with S_i = dS(1,i) + dS(n-1,i) and A_ij = dA(i,j)_0 + dA(j,i)_{n-1}:
   -c/40 S_1 + (3/160 + c/20) S_2 + (-3/32 + c/20) S_3 + (-3/160 + 3c/20) A_12 + 3/32 A_13 - 4c/5 A_22 + c A_32 = 0
8. odd@1 relation:
   - n >= 5 (also predicted for n = 4):
     odd@1 . delta = 16c / (n (n-3)) [U1 - 2 U2 + A22 - (5n+7) / (2 (4n-7)) (4 A12 - A22)]
   - n = 3:
     odd@1 . delta = -20.4 A11 + 1.3 U1 - 0.2 U2

Notes on row 8:
- The net satisfies (4n-7) A11 = (n-4) (4 A12 - A22) at every n (checked at n = 3, 5, 6). The A11 form of the n >= 5 relation therefore has coefficient -(5n+7)/(2(n-4)), and the A12 form above stays finite at n = 4.
- Any multiple of A11 can be traded through the ring rows, because their sum gives sum_k ring_k . delta = -c A11.
- At n = 3 the bracket U1 - 2U2 + A22 + 11 A11 is identically 0 on the net, so the general relation is empty there.
- The n = 3 relation was fitted on the n = 3 fit caps only. Held-out n = 3 caps and CreasedBox v13 give the same three coefficients to 1e-9.

How the relations were found:
- Rows 1-6: per-row checks on Fusion delta.
- Row 7: a stacked rank search over the w0 window at n = 3, 5, 6, 8, held out at n = 7.
- Row 8: the residual odd@1 . delta is an exact one-ring grip functional, consistent across both crease lengths (net levels h = 1/8 and 1/4). It is spanned by net mode-0 sums and U1, U2 alone.
  - u = 16c/(n(n-3)) and (5n+7) come from n = 5, 6, 8.
  - n = 7 (held out) matches: -4c, 4c/7, 4c/7, -8c/7.

## Refuted on the way

All of these fail by 1e-4 to 1e-1:
- the smooth-net netref, for any row;
- virtual crease keys;
- least squares or min-norm along the free direction;
- sparse net-key or one-ring-net fits of odd@1 up to 4 keys;
- partial sums over the non-adjacent spokes;
- sparse fits of even@0 and of the cos tangent row.
