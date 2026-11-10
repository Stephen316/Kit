"""Run only the two preregistered suppression-index holdouts after discovery."""

from pathlib import Path
import runpy


def run(context):
    script = Path(__file__).resolve().parent / "GenerateSketchSymmetricIndexModes.py"
    runpy.run_path(str(script))["run"]({"cases": ["circular_odd_holdout", "rectangular_both_holdout"]})
