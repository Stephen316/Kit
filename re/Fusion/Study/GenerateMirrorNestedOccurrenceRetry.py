"""Retry only the two nested sources after optional native-token getter repair."""
from pathlib import Path
import runpy


def run(context):
    generator=runpy.run_path(str(Path(__file__).resolve().with_name('GenerateMirrorAssemblyDatumHoldouts.py')))['run']
    generator({'cases':('nested_occurrence_yz','nested_occurrence_rotated_parent_xz')})
