"""Retry only the left-handed feature after an explicit documented edit."""

from pathlib import Path
import runpy


def run(context):
    namespace = runpy.run_path(str(Path(__file__).resolve().parent/"GenerateThreadModes.py"))
    namespace["run"].__globals__["CASES"] = ("left_handed",)
    namespace["run"](context)
