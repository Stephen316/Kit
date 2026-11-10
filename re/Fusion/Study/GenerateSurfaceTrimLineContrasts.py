"""Two explicitly dispatched owned SketchLine Trim contrasts; no retry."""
from pathlib import Path
import runpy


def run(context):
    entrypoint=Path(__file__).resolve()
    namespace=runpy.run_path(str(entrypoint.with_name('GenerateSurfaceTrimToolContrasts.py')))
    namespace['run']({'cases':['sketch_line_offset_positive','sketch_line_reversed_negative'],'entrypoint_source_path':str(entrypoint)})
