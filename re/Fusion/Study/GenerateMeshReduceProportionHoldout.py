"""One documented real50.0 MeshReduce proportion holdout; root dispatches."""
from pathlib import Path
import runpy


def run(context):
    source=Path(__file__).resolve().with_name('GenerateMeshReduceContrasts.py')
    namespace=runpy.run_path(str(source))
    namespace['run']({'cases':['adaptive_proportion_fifty'],'real_proportion':50.0})
