"""Native acceptance suite for Kit edge-set fillets and chamfers.

Runs AcceptAuthoredFeatures.py on two-distance, distance-angle and
multi-edge corner features and writes Authored/NativeAcceptanceEdges.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "ChamferTwoDistances",
    "ChamferDistanceAngle",
    "FilletTwoEdges",
    "ChamferTwoEdges",
    "CornerSetPart",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Edges", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
