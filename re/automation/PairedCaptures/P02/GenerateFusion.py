import runpy
from pathlib import Path

RECIPE_ID = "P02"


def run(context):
    script = Path(__file__).resolve()
    runpy.run_path(str(script.parents[1] / "FusionCapture.py"))["capture"](RECIPE_ID, script)
