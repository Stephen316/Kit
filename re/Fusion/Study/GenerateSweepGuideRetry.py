"""Retry only six guide cases whose inactive orientation getter blocked export."""

from pathlib import Path
import runpy


def run(context):
    namespace = runpy.run_path(str(Path(__file__).resolve().parent/"GenerateSweepGuideModes.py"))
    namespace["run"]({"cases": ["rail_scale", "rail_stretch", "rail_no_scaling", "rail_full_extents",
                                 "guide_surface", "guide_surface_chain"]})
