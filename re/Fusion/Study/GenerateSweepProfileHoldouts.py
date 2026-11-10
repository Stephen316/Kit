"""Capture actual Path members for the two open-profile Sweep variants."""
import runpy
from pathlib import Path


def run(context):
    namespace = runpy.run_path(str(Path(__file__).resolve().with_name('GenerateSweepProfileModes.py')))
    namespace['run']({'cases': ['open_sketch_surface', 'open_brep_edge_surface']})
