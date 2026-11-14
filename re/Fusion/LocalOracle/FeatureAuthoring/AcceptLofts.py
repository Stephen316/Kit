"""Native acceptance suite for Kit lofts.

Runs AcceptAuthoredFeatures.py on lofts between two parallel profiles:
a rectangle to a smaller rectangle, a circle to a smaller coaxial circle,
and a wedge loft between rectangles of different proportions added as a
second body beside an extruded block.
It writes Authored/NativeAcceptanceLofts.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "LoftRects",
    "LoftCircles",
    "LoftWedgeBody",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Lofts", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
