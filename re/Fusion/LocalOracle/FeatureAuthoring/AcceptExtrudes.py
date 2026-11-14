"""Native acceptance suite for Kit part bodies authored from sketch profiles.

Runs AcceptAuthoredFeatures.py on the extrude cases and writes
Authored/NativeAcceptanceExtrudes.json. Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "ExtrudeNew",
    "ExtrudeSymmetric",
    "ExtrudeTwoSided",
    "ExtrudeFlip",
    "ProfileSlot",
    "ProfileConcave",
    "ProfileCircle",
    "ExtrudeJoin",
    "ExtrudeCut",
    "ExtrudeIntersect",
    "ExtrudeBlindCut",
    "ExtrudeSlotCut",
    "ExtrudeSymmetricCut",
    "PartCutFillet",
    "PartConcaveShell",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Extrudes", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
