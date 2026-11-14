"""Native acceptance suite for Kit shells that remove side faces.

Runs AcceptAuthoredFeatures.py on a cuboid shell that removes its top and
front faces and on one that also removes its right face.
It writes Authored/NativeAcceptanceShells.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "ShellOpenSide",
    "ShellOpenCorner",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Shells", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
