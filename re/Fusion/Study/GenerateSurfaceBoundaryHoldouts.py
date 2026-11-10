"""Targeted documented feature edits for chaining and alternate-face evidence."""

from pathlib import Path
import runpy


def run(context):
    namespace = runpy.run_path(str(Path(__file__).resolve().parent/"GenerateSurfaceBoundaries.py"))
    namespace["run"].__globals__["CASES"] = ("extend_no_chain", "ruled_alternate")
    namespace["run"](context)
