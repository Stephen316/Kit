"""Check curvature continuity/weight and multiple chamfer edge sets."""

from pathlib import Path
import runpy


def run(context):
    generator = runpy.run_path(str(Path(__file__).with_name("GenerateEdgeToolModes.py")))["run"]
    generator.__globals__["CASES"] = ("fillet_curvature", "chamfer_multiple")
    generator(context)
