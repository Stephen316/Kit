"""Swap the selected full-round sides and between-rule groups independently."""

from pathlib import Path
import runpy


def run(context):
    runpy.run_path(str(Path(__file__).with_name('GenerateSpecialFilletModes.py')))['run'](
        {'cases': ['full_explicit_swapped', 'rule_between_faces_swapped']})
