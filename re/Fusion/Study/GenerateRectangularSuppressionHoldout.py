"""Run only the optional rectangular PatternElement.isSuppressed holdout.

Run inside Fusion. The sibling generator creates/closes its own document and
writes a fresh rectmodes-* directory with API getters and any capture errors.
"""

from pathlib import Path
import runpy


def run(context):
    generator = Path(__file__).resolve().with_name("GenerateRectangularPatternModes.py")
    namespace = runpy.run_path(str(generator))
    entry = namespace["run"]
    # run_path's returned dictionary need not be the function's globals object.
    entry.__globals__["CASES"] = ("body_suppressed_element",)
    entry(context)
