"""Native acceptance suite for Kit hole features.

Runs AcceptAuthoredFeatures.py on the hole cases and writes
Authored/NativeAcceptanceHoles.json. Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "HoleFlat",
    "HoleThrough",
    "HoleCounterboreFlat",
    "HoleCounterbore",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Holes", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
