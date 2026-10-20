"""Retry the perpendicular axis's actual Point3D definition getter."""

from pathlib import Path
import runpy


def run(context):
    namespace = runpy.run_path(str(Path(__file__).resolve().parent/"GenerateConstructionModes.py"))
    namespace["run"]({"cases": ["axis_perpendicular_at_point"]})
