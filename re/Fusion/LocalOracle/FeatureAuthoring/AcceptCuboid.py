"""Native acceptance suite for the Kit cuboid corner and shell features.

Runs AcceptAuthoredFeatures.py on the five cuboid cases and writes
Authored/NativeAcceptance.json. Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "Fillet",
    "Chamfer",
    "Shell",
    "FilletShell",
    "MultiFeature",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
