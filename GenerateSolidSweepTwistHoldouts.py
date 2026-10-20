"""Capture only zero/sixty-degree straight solid-Sweep twist holdouts."""

from pathlib import Path
import runpy


def run(context):
    namespace = runpy.run_path(str(Path(__file__).resolve().parent/"GenerateSolidSweepModes.py"))
    namespace["run"]({"cases": ["solid_twist_zero", "solid_twist_sixty"]})
