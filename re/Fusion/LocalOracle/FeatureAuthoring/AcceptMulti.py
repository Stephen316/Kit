"""Native acceptance suite for Kit multi-family parts.

Runs AcceptAuthoredFeatures.py on parts that chain several families and
writes Authored/NativeAcceptanceMulti.json. Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "MultiPocketPart",
    "MultiDiscPart",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Multi", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
