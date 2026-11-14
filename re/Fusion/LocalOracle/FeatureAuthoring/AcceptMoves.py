"""Native acceptance suite for Kit body moves.

Runs AcceptAuthoredFeatures.py on a translated cuboid and on a part that turns
and lifts its body before a fillet.
It writes Authored/NativeAcceptanceMoves.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "MoveBody",
    "MoveTurnPart",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Moves", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
