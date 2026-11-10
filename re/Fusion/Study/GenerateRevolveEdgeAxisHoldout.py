"""Contrast the BRep Revolve-axis context cache with an offset X-directed edge."""

from pathlib import Path
import runpy


def run(context):
    generator = runpy.run_path(str(Path(__file__).with_name('GenerateRevolveAxisModes.py')))['run']
    generator({'cases': ('brep_edge_offset_x',)})
