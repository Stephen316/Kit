"""Native acceptance suite for Kit offset faces.

Runs AcceptAuthoredFeatures.py on parts that raise or lower the top face and
push a straight side face out, one of them after a fillet.
It writes Authored/NativeAcceptanceOffsets.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "OffsetTop",
    "OffsetTopTrim",
    "OffsetSide",
    "OffsetRoundFront",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Offsets", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
