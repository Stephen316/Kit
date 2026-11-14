"""Native acceptance suite for Kit drafts.

Runs AcceptAuthoredFeatures.py on parts whose straight side faces lean out or
in about the bottom face, one of them after a chamfer.
It writes Authored/NativeAcceptanceDrafts.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "DraftSides",
    "DraftInward",
    "DraftCutPart",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Drafts", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
