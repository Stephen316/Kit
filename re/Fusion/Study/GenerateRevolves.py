"""Run only the revolve cases without repeating the extrusion experiments."""

from pathlib import Path
import runpy


def run(context):
    script = Path(__file__).resolve().with_name("GenerateModelFeatures.py")
    runpy.run_path(str(script))["run"]({"cases": ["revolve_partial", "revolve_full"]})
