"""Native acceptance suite for Kit body copy and paste.

Runs AcceptAuthoredFeatures.py on parts that paste a plain extruded body,
a filleted body, the same body twice, a second body, a pocketed body, and a
pasted body that a later combine cuts away.
It writes Authored/NativeAcceptancePastes.json.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

CASES = [
    "PastePlain",
    "PasteFillet",
    "PasteTwice",
    "PasteSecond",
    "PastePocket",
    "PasteCombine",
]

runpy.run_path(
    str(Path(__file__).resolve().parent / "AcceptAuthoredFeatures.py"),
    init_globals={"SUITE": "Pastes", "CASES": CASES},
    run_name="kit_feature_acceptance",
)
