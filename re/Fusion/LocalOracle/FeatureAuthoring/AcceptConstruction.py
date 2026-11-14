"""Native acceptance suite for Kit construction axes and points.

Runs AcceptAuthoredFeatures.py on parts with an edge axis and a vertex
point and writes Authored/NativeAcceptanceConstruction.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "ConstructionSet",
    "ConstructionPart",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Construction", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
