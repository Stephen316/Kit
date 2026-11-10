"""Retry only fitted-spline evidence with SWIG vector serialization support."""

from pathlib import Path
import runpy


def run(context):
    script = Path(__file__).resolve().parent / "GenerateSketchCurvedPatternModes.py"
    runpy.run_path(str(script))["run"]({"cases": ["rectangular_fitted_spline"]})
