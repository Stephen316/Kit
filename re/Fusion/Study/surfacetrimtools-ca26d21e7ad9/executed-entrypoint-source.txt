"""Resume only the two uncaptured SurfaceTrim cases in fresh owned documents."""
from pathlib import Path
import runpy


def run(context):
    entrypoint=Path(__file__).resolve()
    namespace=runpy.run_path(str(entrypoint.with_name('GenerateSurfaceTrimToolContrasts.py')))
    namespace['run']({'cases':['sheet_body','sketch_line'],'entrypoint_source_path':str(entrypoint)})
