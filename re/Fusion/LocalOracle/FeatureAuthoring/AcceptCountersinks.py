"""Native acceptance suite for Kit countersink holes.

Runs AcceptAuthoredFeatures.py on a through countersink and a blind flat
countersink, and writes Authored/NativeAcceptanceCountersinks.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "HoleCountersink",
    "HoleCountersinkFlat",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Countersinks", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
