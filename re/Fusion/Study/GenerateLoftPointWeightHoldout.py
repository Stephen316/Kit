"""Run only the additional tangent-start weight2 Loft contrast in Fusion."""

from pathlib import Path
import runpy


def run(context):
    generator = Path(__file__).resolve().with_name("GenerateLoftPointHoldouts.py")
    namespace = runpy.run_path(str(generator))
    entry = namespace["run"]
    entry.__globals__["CASES"] = ("tangent_start_weight2",)
    entry(context)
