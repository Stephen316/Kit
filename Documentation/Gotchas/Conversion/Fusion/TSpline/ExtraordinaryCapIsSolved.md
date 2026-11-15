# Extraordinary-vertex caps come from a solved system

## Expectation

Fusion converts a T-spline cage to the Catmull–Clark limit surface away from extraordinary vertices. A converter could then add a fixed cap mask for each valence, and Kit would convert any cage with valences 3 to 8.

## Actual behavior

Fusion 2706.1.17 matches the Catmull–Clark limit only outside a cap region.

- Each cell with an extraordinary point (EP) at a corner has double knots at h and 2h from that corner.
- h is 1/4 of a face for an isolated EP. It is 1/8 when another EP or a fixed crease point is next to it.
- The cap changes the B-spline poles with indices i, j ≤ 4 from the EP, except pole (4, 4).
- Every other pole equals the blossom of the Catmull–Clark net ("netref").

The cap is not a local mask. A grip in one sector moves cap poles in every sector, in every Fourier mode. For valence 3, mode 0 has denominators with the primes 19 and 89. A mask built from cos(2π/n) cannot give those primes, but one small linear solve can. So Fusion solves a sparse linear system per EP.

Black-box experiments recovered the whole system:

- Kit built cap prisms with one or two EPs of valence 3 to 12 and gave the grips seeded noise.
- Local Fusion converted them, and Kit read the saved poles.
- The unknowns are δ = pole − netref, with netref(EP) = the Catmull–Clark limit point.
- With c = cos(2π/n), every row has integer coefficients in 1, c, r and 1/(n + 5).
- r = L / (h + L), where L is the span after the knot at 2h.

| Rows    | Count                | Content                                                                                                                                                                       |
| ------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hard    | per spoke and sector | EP = limit. G1 across each spoke on [0, 2h], weight 2c times a profile (linear, then quadratic, then zero). The spoke is quadratic on [h, 2h]. C2 at 2h on pole rows 2 and 3. |
| Window  | 7 per spoke          | Split rule δB(1, i) = δA(i, 1) for i = 2, 3, 4. A sector balance, a spoke balance, and one mirror-even and one mirror-odd relation across the spoke.                          |
| Ring    | 1 per spoke          | Pairs of sector twists and spoke poles, with right side −κ(net S1 − EP) − 9c/(n + 5) · mean, where κ = (n − 4)c/(n + 5).                                                      |
| Tangent | 2                    | Fourier modes ±1 of the spoke poles 1 to 3.                                                                                                                                   |
| Twist   | 1 for even n         | The alternating twist is 9/(n + 5) times netref's, the Loop–Schaefer mask in that mode.                                                                                       |

The rows leave no free direction. The research rule and the Kit port agree to 2.7e-13 in grip coefficients.

- Fitted on: cap prisms of valence 3, 5 to 10 and 12, Box3, and the Valence5 to Valence8 layouts.
- Not fitted on: HeldBox113 (level-3 caps), HeldPrism3, HeldPrism5 (coupled and mixed caps of valence 3 and 5), and 13 probe cages.
- On every one of them the converted faces match Fusion's own conversion within 1.9e-13 cm.
- HeldBand67 (valence 6 and 7 in one band) also matched in its caps. Its face lines now raise at a tie, so it no longer converts.

A crease that ends at an EP changes the system. Turn the crease to spoke 0.

- The EP, the crease spoke and the poles beside it keep their net values.
- The G1 and Q rows on the crease spoke drop out. So do the window relations that cross it.
- One relation on the first window of the two crease sectors replaces them.
- A second relation ties the odd part at spoke 1 to the crease defects. U_i is the gap between the crease spoke and the mean of its two neighbours at step i. The relation has the coefficient 16c / (n (n − 3)). Valence 3 has its own three coefficients.
- Fitted on valence 3, 5, 6 and 8. Valence 7 and the creased box saves were held out.
- 109 caps in 39 Fusion saves match within 1.6e-13 cm.

A crease that ends at a valence-4 vertex is a dart. Fusion caps a dart like an EP of valence 4 when an EP or a crease from another vertex is next to it.

- Each side of the crease line keeps one C1 face.
- The poles on the two spokes across the crease line are midpoints of the poles beside them. The dart point is the midpoint of the two first poles beside the crease.
- At valence 4 the crease rows leave 10 free directions. Ten relations with whole-number coefficients from −2 to 8 fix them. Each relation pairs a pole with its mirror across the crease.
- Fitted on 38 caps, largest gap 3.2e-15. Held out: 29 caps from other valences, the creased box and three dart probes, largest gap 4.7e-15.
- Fusion leaves a dart with only plain neighbours uncapped, and its poles there have no Kit rule yet.

Two details change the answer:

- The knots of each spoke come from the strip of cells beside the spoke, from the EP outward. A knot that another cell adds to the same B-rep face does not enter the solve. Fusion inserts it afterwards. Using the whole face knot list breaks HeldBand67, and clamping at the EP's own cells breaks HeldPrism3.
- Fusion ignores the TSM header `cap-type` and `star-smoothness` on import for `G0CAPS`, `G1CAPS`, `G2CAPS`, and star values 0, 1, and 2. [The declaration lifecycle acceptance](../../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/NativeAcceptance.json) confirms equal bodies on Box3 and a held-out HeldPrism5 cage. Kit preserves these declarations while using the topology-derived cap solve.

## Workaround

Kit ships no per-layout table. `SolveCaps` in `convert.formats.Fusion.BrepCodec.Journal.Spline.Caps` builds the rows from the request's valence and knots and solves them with a pivoted Householder least-squares solve in pure Python. The window rows are a literal table of integer coefficients. It raises `ValueError` when:

- a spoke's two sides see different spans;
- a knot ratio is not 1/2 or 2/3;
- the rows leave a free direction.

`CreaseRows` builds the rows of a creased cap, and `DartRows` adds the dart midpoints and the ten dart relations. The dart relations are a literal table of integer coefficients. Conversion raises `ValueError` when:

- two creases meet at one EP;
- a creased cap has a knot ratio other than 2/3;
- a dart has no EP or crease next to it.

Weighted grips need no other rule. The cap rows apply to the homogeneous grips (w x, w y, w z, w), like every other pole row. HeldWeighted6 has nine weighted grips, some of them inside caps, and Kit's rational faces match Fusion's within 9.0e-15 cm in poles and 2.1e-14 in weights.

## Evidence

- [Cap rule notes](../../../../../re/Fusion/Reconstruction/FormDocuments/General/CapRuleNotes.md)
- [Research cap rule](../../../../../re/Fusion/Reconstruction/FormDocuments/General/CapRule.py)
- [Crease cap and dart notes](../../../../../re/Fusion/Reconstruction/FormDocuments/General/CreaseRuleNotes.md)
- [Research crease cap rule](../../../../../re/Fusion/Reconstruction/FormDocuments/General/CreaseRule.py)
- [General conversion notes](../../../../../re/Fusion/Reconstruction/FormDocuments/General/GeneralNotes.md)
- [Cap header variants](../../../../../re/Fusion/LocalOracle/FormDocuments/General/CapVariantsProbe.json)
