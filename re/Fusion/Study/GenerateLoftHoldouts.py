"""Retry only the corrected three-section and centerline loft captures."""

from pathlib import Path
import runpy


def run(context):
    namespace = runpy.run_path(str(Path(__file__).resolve().with_name("GenerateLoftModes.py")))
    namespace["run"]({"cases": ["solid_three", "centerline"]})
