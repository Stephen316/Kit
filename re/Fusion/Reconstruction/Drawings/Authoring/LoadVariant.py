"""Load the typed DWG database embedded in a research variant bundle."""

import io
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[4] / 'src'))

import BuildVariants  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402

VARIANTS = Path(tempfile.gettempdir()) / 'KitFusionDrawings' / 'Variants'


def variant_drawing(label):
    bundle = (VARIANTS / f'{label}.f3z').read_bytes()
    outer = zipfile.ZipFile(io.BytesIO(bundle))
    return next(outer.read(name) for name in outer.namelist() if name.endswith('.f2d'))


def load_variant(label):
    return ReadDwgFile(BuildVariants.database(variant_drawing(label)))
