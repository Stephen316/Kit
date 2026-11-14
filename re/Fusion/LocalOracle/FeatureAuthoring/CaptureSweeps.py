"""Native rectangle sweeps along a bent path.

Runs CaptureBodies.py for SweepBend (a line and a quarter arc) and
SweepHook (a line, a quarter arc and a second line). Each sweeps a
10 x 10 mm rectangle on the XZ plane along a path on the XY plane.
It writes Controls/CaptureSweeps.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

runpy.run_path(
    str(Path(__file__).resolve().parent / "CaptureBodies.py"),
    init_globals={"ONLY": ["SweepBend", "SweepHook"], "REPORT": "CaptureSweeps.json"},
    run_name="kit_feature_capture",
)
