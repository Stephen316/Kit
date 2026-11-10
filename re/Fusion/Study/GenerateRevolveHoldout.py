"""Explicit contrast for the projected-axis revolve flag."""

from pathlib import Path
import runpy


def run(context):
    generator = runpy.run_path(str(Path(__file__).with_name("GenerateRevolveModes.py")))["run"]
    generator.__globals__["CASES"] = ("project_axis",)
    generator(context)
