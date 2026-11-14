"""Run every Kit feature acceptance suite in one Fusion session.

Runs the cuboid, extrude, hole, pattern, multi-family, edge-set,
construction, revolve, countersink, open shell, move, offset face, draft,
multi-body, loft, sweep and paste wrappers in order.
Each wrapper writes its own Authored/NativeAcceptance*.json report.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

WRAPPERS = ("AcceptCuboid.py", "AcceptExtrudes.py", "AcceptHoles.py", "AcceptPatterns.py", "AcceptMulti.py", "AcceptEdges.py", "AcceptConstruction.py", "AcceptRevolves.py", "AcceptCountersinks.py", "AcceptShells.py", "AcceptMoves.py", "AcceptOffsets.py", "AcceptDrafts.py", "AcceptBodies.py", "AcceptLofts.py", "AcceptSweeps.py", "AcceptRounds.py", "AcceptPastes.py")

for wrapper in WRAPPERS:
    runpy.run_path(str(Path(__file__).resolve().parent / wrapper), run_name="kit_feature_suite")
