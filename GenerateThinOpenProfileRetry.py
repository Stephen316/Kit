"""Retry only the open-line Thin Extrude after nullable profile-owner capture fix."""
from pathlib import Path
import runpy


def run(context):
    source = Path(__file__).resolve().with_name('GenerateThinExtrudeContrasts.py')
    runpy.run_path(str(source))['run']({'cases': ['open_line_side1']})
