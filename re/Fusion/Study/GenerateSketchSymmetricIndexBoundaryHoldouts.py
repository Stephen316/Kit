"""Two discriminating even-axis probes after the first seed-rounding hypothesis.

Keeps original generators/captures intact. New case names make the independent
boundary probes distinct; API masks differ from the earlier edge-index cases.
"""

from pathlib import Path
import runpy


def run(context):
    script = Path(__file__).resolve().parent / "GenerateSketchSymmetricIndexModes.py"
    generator = runpy.run_path(str(script))["run"]
    configs = generator.__globals__["CONFIGS"]
    configs["rectangular_first_even_boundary"] = dict(configs["rectangular_first_even"],
        stage="boundary_holdout", suppressed_api_indices=[1])
    configs["rectangular_both_boundary"] = dict(configs["rectangular_both_holdout"],
        stage="boundary_holdout", suppressed_api_indices=[4])
    generator({"cases": ["rectangular_first_even_boundary", "rectangular_both_boundary"]})
