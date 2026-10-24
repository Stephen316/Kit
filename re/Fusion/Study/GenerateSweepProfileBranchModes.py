"""Contrast BRep-edge-profile active Sweep distance and reversed source path."""
import runpy
from pathlib import Path


def run(context):
    namespace = runpy.run_path(str(Path(__file__).resolve().with_name('GenerateSweepProfileModes.py')))
    namespace['run']({'cases': ['open_brep_edge_partial', 'open_brep_edge_reversed']})
