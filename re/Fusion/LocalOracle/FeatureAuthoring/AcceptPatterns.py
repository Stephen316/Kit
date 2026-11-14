"""Native acceptance suite for Kit patterns, mirrors and offset planes.

Runs AcceptAuthoredFeatures.py on the copy and construction cases and
writes Authored/NativeAcceptancePatterns.json. Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "PlaneOffset",
    "RectPattern",
    "FeatureCircPattern",
    "MirrorFeature",
    "HoleGrid",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Patterns", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
