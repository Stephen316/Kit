"""Research: shared readers for the pole engine study.

Run with the scratch venv (Python 3.14, numpy) and -I. Puts src and the General and
Topology research folders on sys.path. Nothing in src/ loads this.

Sources:
- old 8 layouts: FormStencils.xz rows (grips -> poles), the TSM cage from the old saves;
- 12 General probes and the cap prisms: the cage TSM and Fusion's own save (one sample).
"""

import json
import lzma
import sys
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
for extra in ('src', 're/Fusion/Reconstruction/FormDocuments/General', 're/Fusion/Reconstruction/FormDocuments/Topology',
              're/Fusion/Reconstruction/FormDocuments/Cages'):
    if str(ROOT / extra) not in sys.path:
        sys.path.insert(0, str(ROOT / extra))

from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline  # noqa: E402

STENCILS = ROOT / 're/Fusion/Reconstruction/FormDocuments/Tables/FormStencils.xz'
GENERAL_DIR = ROOT / 're/Fusion/LocalOracle/FormDocuments/General'
OLD_LABELS = ('Box', 'CreasedPlane', 'CreasedBox', 'Box3', 'Valence5', 'Valence6', 'Valence7', 'Valence8')
GENERAL = ('Box111', 'Box122', 'Box234', 'LPrism', 'TPrism', 'Step', 'Valence5Tall', 'Valence3Prism', 'Mixed56',
           'Mixed78', 'Torus86', 'SharpBox')


def read_tables():
    data = json.loads(lzma.decompress(STENCILS.read_bytes()))
    return {table['Label']: table for table in data['Tables']}


def table_matrix(table):
    rows = np.zeros((len(table['Rows']), table['GripCount']))
    for index, row in enumerate(table['Rows']):
        for grip, value in row:
            rows[index, grip] = value
    return rows


def expand(knots):
    out = []
    for value, count in knots:
        out += [float(value)] * int(count)
    return out


def table_faces(table):
    """region -> (knots_u, knots_v, matrix grid [v][u][grip])"""
    rows = table_matrix(table)
    out = {}
    for face_index, knots_u, knots_v, poles in table['Faces']:
        count_u = sum(c for _, c in knots_u) - 2
        count_v = sum(c for _, c in knots_v) - 2
        out[face_index] = ([tuple(k) for k in knots_u], [tuple(k) for k in knots_v],
                           rows[poles].reshape(count_v, count_u, -1))
    return out, rows


def old_surface(label):
    from SavedBodies import OLD_SAVES
    from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
    model = ReadDocument((ROOT / OLD_SAVES[label]).read_bytes())
    return model.Forms[0].Surface


def general_surface(name):
    path = GENERAL_DIR / (name + '.tsm')
    if not path.exists():
        path = GENERAL_DIR / 'Caps' / (name + '.tsm')
    return ReadTspline(path.read_bytes())


def saved_faces(path):
    """region -> (knots_u, knots_v, grid [v][u][xyz or xyzw]) from Fusion's own save."""
    from SavedBodies import read_saved
    saved = read_saved(path)
    out = {}
    for face in saved.body.Faces:
        cache = face.Surface.Cache
        knots_u = [(k.Value, k.Count) for k in cache.KnotsU]
        knots_v = [(k.Value, k.Count) for k in cache.KnotsV]
        count_u = sum(c for _, c in knots_u) - 2
        count_v = sum(c for _, c in knots_v) - 2
        weights = getattr(cache, 'Weights', ()) or ()
        points = np.array([tuple(p)[:3] for p in cache.Points], dtype=float)
        if weights:
            points = np.hstack([points, np.array(weights, dtype=float)[:, None]])
        out[face.Surface.Region] = (knots_u, knots_v, points.reshape(count_v, count_u, -1))
    return out, saved


def general_saved(name):
    return saved_faces(GENERAL_DIR / 'tmp' / (name + '.f3d'))


def grip_array(surface):
    return np.array([[g.CoordX, g.CoordY, g.CoordZ, g.Weight] for g in surface.Grips], dtype=float)
