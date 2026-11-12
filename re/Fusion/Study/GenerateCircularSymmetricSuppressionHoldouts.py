"""Run only three additional API-ID contrasts; original exports remain intact."""
from pathlib import Path
import runpy


def run(context):
    module=runpy.run_path(str(Path(__file__).resolve().with_name('GenerateCircularSymmetricSuppressionContrasts.py')))
    module['run']({'cases':['quantity5_suppress_id0','quantity5_suppress_id4','quantity4_suppress_id0']})
