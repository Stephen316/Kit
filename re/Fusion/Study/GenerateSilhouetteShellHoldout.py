"""Probe shelled-body SilhouetteSplit using an explicitly hollow solid target."""

from pathlib import Path
import runpy


def run(context):
    runpy.run_path(str(Path(__file__).with_name('GenerateSilhouetteSplitModes.py')))['run'](
        {'cases': ['shelled_hollow_axis_x']})
