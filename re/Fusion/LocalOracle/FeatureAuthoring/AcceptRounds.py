"""Native acceptance suite for Kit edge rounds on horizontal and curved edges.

Runs AcceptAuthoredFeatures.py on fillets and chamfers that select edges by a
point on the edge and its level: a top edge of a block as a fillet, an equal
chamfer, a two-distance chamfer and a distance-and-angle chamfer, two opposite
top edges, a bottom edge, the rim of a disc as a fillet and a chamfer, the
base of a joined boss, the rim of a cut bore, the tangent rim of a block with
rounded corners as a fillet and a chamfer, and the rim of a slot bar.
Eleven chamfers check the leg rule on edges it was not fitted on: a bottom
edge, a top edge on another side, a disc rim, a bore rim, the base of a boss,
a disc bottom, a rounded rim seeded on a line and on a corner arc, a rounded
bottom rim seeded on a corner arc, the inner step edge of an L-shaped bar and
one base edge of a square post. A fillet on that step edge ends where it meets
a concave corner, and a fillet on the post base edge is concave with open
ends. Four
cases select every top or bottom edge, or two adjacent top edges, so the
blends meet at sharp corners.
It writes Authored/NativeAcceptanceRounds.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "RoundTopEdge",
    "BevelTopEdge",
    "BevelTopTwo",
    "BevelTopAngle",
    "RoundTwoEdges",
    "RoundBottomEdge",
    "RoundDiscRim",
    "BevelDiscRim",
    "RoundBossBase",
    "RoundHoleRim",
    "RoundRimChain",
    "BevelRimChain",
    "RoundSlotRim",
    "BevelBottomTwo",
    "BevelSideAngle",
    "BevelDiscTwo",
    "BevelBoreAngle",
    "BevelTopLoop",
    "RoundTopLoop",
    "RoundTopPair",
    "RoundBottomLoop",
    "BevelBossTwo",
    "BevelDiscBottom",
    "BevelRimTwo",
    "BevelArcTwo",
    "BevelArcBottom",
    "RoundStepEdge",
    "BevelStepTwo",
    "RoundPostEdge",
    "BevelPostTwo",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Rounds", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
