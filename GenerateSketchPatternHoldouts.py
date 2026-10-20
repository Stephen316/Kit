"""Retry sketch rectangular patterns using numeric properties and default axes."""

from pathlib import Path
import runpy


def run(context):
    generator = runpy.run_path(str(Path(__file__).with_name("GenerateSketchToolModes.py")))["run"]
    generator.__globals__["CASES"] = ("RectangularSpacing", "RectangularExtent", "RectangularSymmetric")
    generator(context)
