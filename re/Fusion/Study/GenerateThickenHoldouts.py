"""Retry Boolean Thicken modes with a sheet and separate overlapping solid."""

from pathlib import Path
import runpy


def run(context):
    namespace = runpy.run_path(str(Path(__file__).resolve().parent/"GenerateThickenModes.py"))
    namespace["run"]({"cases": ["join", "cut", "intersect"]})
