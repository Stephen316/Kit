"""Native acceptance suite for Kit multi-body parts.

Runs AcceptAuthoredFeatures.py on parts with a second extruded or revolved
body, body combines (join, cut, intersect, keep tools), splits along offset
planes and rectangular or circular patterns of bodies.
It writes Authored/NativeAcceptanceBodies.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "ExtrudeSecondBody",
    "RevolveBody",
    "CombineJoin",
    "CombineCut",
    "CombineIntersect",
    "CombineKeep",
    "SplitYZ",
    "SplitXZ",
    "SplitXY",
    "BodyRectPattern",
    "BodyCircPattern",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Bodies", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
