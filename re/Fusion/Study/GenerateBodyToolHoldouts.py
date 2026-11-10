"""A different scale value and explicit mirror/shell flag contrasts."""

from pathlib import Path
import runpy


def run(context):
    generator = runpy.run_path(str(Path(__file__).with_name("GenerateBodyToolModes.py")))["run"]
    generator.__globals__["CASES"] = ("scale_holdout", "mirror_xy_combine", "shell_tangent")
    generator(context)
