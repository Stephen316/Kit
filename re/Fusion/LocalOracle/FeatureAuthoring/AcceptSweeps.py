"""Native acceptance suite for Kit sweeps.

Runs AcceptAuthoredFeatures.py on rectangle profiles on the XZ plane swept
along open paths on the XY plane: a line and a left quarter arc, the same
path with a second line, an offset profile along a line and two arcs that
turn right and then left, and a bend swept as a second body beside an
extruded block.
It writes Authored/NativeAcceptanceSweeps.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "SweepBend",
    "SweepHook",
    "SweepSCurve",
    "SweepSecondBody",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Sweeps", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
