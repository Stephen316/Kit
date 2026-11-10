"""Capture point-to-position coordinate-space contrasts only."""
from pathlib import Path
import runpy

def run(context):
    namespace = runpy.run_path(str(Path(__file__).resolve().with_name('GenerateMoveModes.py')))
    namespace['run']({'cases': ['point_to_position_component', 'point_to_position_nested_design']})
