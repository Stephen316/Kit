"""Capture the three axis variants interrupted by the previous native crash."""

from pathlib import Path
import runpy


def run(context):
    generator = runpy.run_path(str(Path(__file__).with_name('GenerateRevolveAxisModes.py')))['run']
    generator({'cases': ('sketch_line', 'sketch_line_reversed', 'brep_edge')})
