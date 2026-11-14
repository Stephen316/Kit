# Round 4 working notes: edge rounds, loops and pasted bodies

Branch `features-fourth`, from `e4e99c2b5`.
Earlier commits: `ff1f0282c` (neutral feature defaults), `be4540264` (re-acceptance of 16 suites, 73 cases),
`50d9872f3` (horizontal and curved edge rounds), `2eb34395c` (sharp-corner loops),
`27ea32fe6` and `9ffac7c4a` (body paste, cherry-picked from `features-fourth-paste`, 6 of 6 accepted).

## State

- Edge rounds on horizontal edges are implemented in `src/convert/formats/Fusion/DocumentCodec/PartFeatures/Brep/`.
  `FilletSpec` and `ChamferSpec` take `LevelMm`; the points then name horizontal edges at that height.
- Kit follows the tangent chain from the seed edge along the cap loop: seed first, then forward, then backward.
  A closed chain is a loop (disc rim, rounded-block rim, slot rim).
- Surfaces: a fillet along a line is a cylinder, along an arc a torus about Z.
  A chamfer along a line is a plane, along an arc a cone through the two leg circles.
- Mass: prism mass plus the swept section integrals in `RoundMass.py` and `RoundSum.py`.
  Offline, Kit matches the four native controls `FilletTop`, `ChamferTop`, `FilletChain` and `FilletRim` in volume, area and topology.
- Suite `AcceptRounds.py` (13 cases), report `Authored/NativeAcceptanceRounds.json`.
  First full run: 11 of 13 accepted.
  `BevelTopTwo` and `BevelTopAngle` opened with the legs swapped.
  Recompute matched the control, so only Kit geometry was wrong.
  Fix applied in `SolvePart.BevelLegs`: the first distance runs on the cap face, the second distance or the angle leg on the wall.
  The centre of mass of both controls fixes this: a removed cap leg of 0.3 cm puts the centre at y = 1.507035 cm, and 0.2 cm gives 1.507203 cm.
- Untagged circles, such as the base of a joined boss, use a two-face edge recipe (wall, cap) with no vertex.
  `RoundBossBase` was accepted with it.
- Fusion recipe differences that did not block acceptance:
  for arc edges in a tangent chain the native recipe lists the cap before the wall, and tangent vertices carry UV orders.
  Kit lists the wall first and writes no UV orders there.

- Sharp loops: adjacent straight edges of one cap loop join into one chain (`RoundGroup.py`).
  Convex sharp corners get a mitre frame; fillet mitre is a quarter ellipse, chamfer mitre a line.
- Chamfer leg rule, from the edge caches in the Fusion saves of every chamfer control:
  Fusion orients each horizontal edge. A profile, cut or join edge runs with the loop of its cap when the cap faces up
  and with the loop of its side face when the cap faces down. An edge made by a vertical-edge fillet runs with the loop of the fillet face.
  The first distance (or the distance of a distance-and-angle chamfer) lies on the face whose loop runs with the selected edge,
  and the whole tangent chain takes that side.
  Kit models it with `PrismSolid.Blends` (labels of vertical-edge fillet faces), `EdgeRound.Blends`, `IsWithCap` and `PlanLegs` in `RoundGroup.py`.
  `LevelPicks` writes the edge caches in Fusion's edge direction too (start point, displacement, arc normal, refVec).
- Runs: 11 of 13, then 20 of 21 (`BevelBottomTwo` legs swapped), then 23 of 25 (`BevelBossTwo`, `BevelArcTwo` swapped).
  After the rule: 26 of 26, then 28 of 28 with `RoundStepEdge` and `BevelStepTwo` on an L-bar,
  then 30 of 30 with `RoundPostEdge` and `BevelPostTwo` on the concave open edge at the base of a square post.
  `BevelArcBottom`, `BevelStepTwo`, `BevelPostTwo`, `RoundStepEdge` and `RoundPostEdge` were predicted before their runs and matched.
- Every run rewrites every vendor save of the suite, so all 30 `vendor_Round*` and `vendor_Bevel*` saves are scrubbed again after the last run.
  The report holds the scrubbed digests. The 100 cases of the other suites are unchanged by the round code.
- Kit rejects adjacent picks at concave corners and concave loops with "need flat end faces".

## Docs

- Change entry `Documentation/Changes/Fusion/Features/FusionEdgeRounds.md`, gotcha `FeatureChamferLegs.md`.
- `FusionPartFeatures.md` and `FusionAcceptanceEvidence.md` cite the Rounds suite.
- The features section of `FusionDataModel.md` now covers rounds 2 to 4, with mode codes counted only in native controls.
  It replaces the old `DataModelSection.md` draft.

## Open

- Edges next to leaning, drafted or swept side faces, and other solid features after an edge round, are rejected.
- Chain ends on curved or slanted faces, concave corners between picks and concave loops are rejected.
- Vertical and horizontal edges in one feature, three-blend corners, variable radius, setbacks and chord-length fillets are not authored.
- Edge rounds on revolve bodies are not tested in Fusion.
- Native recipes for arcs in a chain list the cap first and carry UV orders; Kit writes the side face first. Fusion accepts both.
