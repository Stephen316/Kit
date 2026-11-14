# Mixed-valence layouts change with the grip positions

## Expectation

Fusion converts each cage layout with a fixed linear map. The converted faces, edges and vertices then depend only on the cage topology. A table keyed by the topology converts every cage of the layout.

## Actual behavior

This holds for the eight old layouts. It fails for cages that join extraordinary vertices of different valences in one band. Fusion 2706.1.17 converted two band cages under single-grip, paired and random grip moves. `LayoutDrift.py` compared the BRep layout of each saved variant with the unmoved cage.

| Cage | Grips | Variants | Base faces, edges, vertices | Variants with another layout |
| --- | --- | --- | --- | --- |
| Valence-7 prism | 44 | 55 | 21, 49, 30 | None |
| Band with valences 5 and 6 | 36 | 47 | 19, 44, 27 | `X33` with 19, 45, 28 and `RandomB` with 20, 46, 28 |
| Band with valences 7 and 8 | 48 | 59 | 25, 58, 35 | `RandomA` with 25, 59, 36 and `RandomB` with 26, 60, 36 |

A single grip move in `X33` split one more edge. The random moves also grouped the patches into another set of faces. Fusion therefore groups faces and splits edges by geometry in these cages.

The face lines follow a ray race. Each ray leaves an extraordinary point or a crease end along a straight spoke. All rays advance one cage link per step. Two rays that meet head-on join and stop. A ray stops at a drawn line, at an earlier ray's trail, at an irregular vertex or at its own start. Without ties this race gives Kit's lines on all 537 stored cages and on every stencil variant.

A crease that ends at a valence-4 vertex makes a dart, and a ray also runs straight on past the crease end. That ray starts one round after the rays from extraordinary points. On the 48 fitted crease-end cages, this delay gives Fusion's lines on all 48. A delay of 0 or 2 rounds gives 24 of 48. On 23 held-out crease-end cages it gives 21. The two misses have the crease reach the rim, so two dart rays share one link, and Kit refuses them.

A tie is two rays that reach one fresh vertex in the same step from perpendicular sides. Only one of them goes on. Ties occur only in the 5-6 band, the 7-8 band, `TPrism` and `HeldBand67`. In the 5-6 band, Fusion picks the winner from the grips ahead of the crossing. Five rounds of grip moves found these flip points at one tie:

| Grip move | Flip between |
| --- | --- |
| Grip 33 in +x | 0.124995 and 0.124999 |
| Grip 33 in +y | 0.215 and 0.21875 |
| Grip 32 in -x, grip 34 in +x, grip 6 in +x | 0.1875 and 0.203 |
| Grip 34 in -z | 0.125 and 0.140625 |
| Grip 6 in +y, grip 35 in -y | 0.15625 and 0.171875 |
| Grip 6 in -z | 0.234 and 0.25 |
| Grip 13 in -z | 0.171875 and 0.1875 |

Grips 5, 18, 12 and 7 never flip it. Shifting or doubling the whole cage scales the flip point with the cage, so the rule is invariant under translation and uniform scale. One tie can change the outcome of another tie later in the race.

With Fusion's tie outcomes forced, Kit reproduces Fusion's bodies within 2e-13. No tested tie-break fits all flip points. The tested tie-breaks were ray straightness, ray index, cage and limit track lengths, and next-link lengths and angles. The tested tie-breaks were also edge arc lengths, curvature jumps across the lines, the shape of the candidate faces, and pole order flips. The remaining tested tie-breaks were equalities of grip distances, angles and dot products.

## Workaround

`DrawLines` runs the race. It raises `ValueError` at a tie, so Kit refuses the 5-6 band, the 7-8 band, `TPrism` and `HeldBand67` instead of guessing. All other probes, held-out cages and stencil natives have no tie and convert as before. A future rule must decide each tie from the grips ahead of it.

## Evidence

- [Layout drift](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/LayoutDrift.json)
- [Probe preparation](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Preparation.json)
- [Probe results](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Probe.json)
