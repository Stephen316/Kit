"""Native offset face controls.

Runs the offset face captures of CaptureFamilies.py, which pass the faces as
a list, and writes Controls/CaptureOffsets.json.
Evidence for Kit authoring, not Kit acceptance.
Run only through RunLocked.mjs. Every document opened here is closed.
"""

import runpy
from pathlib import Path

runpy.run_path(
    str(Path(__file__).resolve().parent / "CaptureFamilies.py"),
    init_globals={"ONLY": {"OffsetTop", "OffsetSide", "OffsetBore"}, "REPORT": "CaptureOffsets.json"},
    run_name="kit_feature_capture",
)
