"""Run only four independent variations needed to distinguish stored tool fields."""

from pathlib import Path
import runpy


def run(context):
    generator = runpy.run_path(str(Path(__file__).with_name("GenerateMoreToolSamples.py")))
    generator["run"]({"cases": ["CircularPatternSymmetricHoldout", "CombineCutNoKeep", "SweepPartial", "LoftThreeSections"]})
