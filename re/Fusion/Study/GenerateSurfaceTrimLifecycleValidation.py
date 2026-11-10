"""One explicitly dispatched owned sheet-face lifecycle validation; no retry."""
from pathlib import Path
import runpy


def run(context):
    entrypoint=Path(__file__).resolve()
    namespace=runpy.run_path(str(entrypoint.with_name('GenerateSurfaceTrimToolContrasts.py')))
    namespace['run']({'cases':['sheet_face'],'lifecycle_validation':True,'entrypoint_source_path':str(entrypoint)})
