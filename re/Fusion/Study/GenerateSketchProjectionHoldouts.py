"""Retry detached projection controls without querying invalid reference getters."""

from pathlib import Path
import runpy


def run(context):
    namespace = runpy.run_path(str(Path(__file__).resolve().with_name("GenerateSketchProjections.py")))
    namespace["run"]({"cases": ["unlinked_line", "broken_line"]})
