"""Native acceptance suite for Kit revolves.

Runs AcceptAuthoredFeatures.py on full and partial revolves, a revolve join
and a revolve cut, and writes Authored/NativeAcceptanceRevolves.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "RevolveFull",
    "RevolveHalf",
    "RevolveJoin",
    "RevolveCut",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Revolves", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
