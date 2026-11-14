"""Research: closed box cages with crease junctions on the top face, held out from the fixed-point
rule (fitted on the roof rounds only), to check its topology, knots and poles in Fusion.

The fixed-point rule: a closed cage vertex that is a corner (three or more sharp edges, or listed)
with a sector of more than one face, or a crease vertex (two sharp edges) with a sector of other
than two faces, is not capped; its cells get single knots 1/2, 1/4, 1/8 from it, the faces are
netref down to level 3, and the face corner pole at it is its limit.

Cages (every box edge and box corner creased, as in the crease rounds):
- LTurn: a crease L on a 3 x 3 top whose turn is an inside crease vertex (sectors 1 and 3).
- LTurnWide: the same on a 4 x 4 top with two-cell arms.
- TJunction: a straight crease across a 2 x 2 top with a one-cell branch (sectors 1, 1, 2).
- TJunctionWide: the same on a 4 x 4 top with two-cell arms.
- Cross: two straight creases across a 4 x 4 top (sectors 1, 1, 1, 1: not a fixed point).
- ListedFlat: a 2 x 2 top with its middle vertex listed and no top crease.
- ListedLine: a straight crease across a 2 x 2 top with its middle vertex listed (sectors 2, 2).

Usage: FixedCages.py            writes Crease/FixedRound/*.tsm and Preparation.json
"""

import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 're/Fusion/Reconstruction/FormDocuments/Crease'))
from CreaseCages import HEADER, crease_sets, grid_box  # noqa: E402
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline  # noqa: E402
from convert.formats.Fusion.TSplineCodec.MakeClosedCage import MakeClosedCage  # noqa: E402
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip  # noqa: E402
from convert.formats.Fusion.TSplineCodec.Model.CreaseData import CreaseData  # noqa: E402
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline  # noqa: E402

TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/Crease/FixedRound'


def path_edges(points):
    return {frozenset(((a[0], a[1], 1), (b[0], b[1], 1))) for a, b in zip(points, points[1:])}


def line(start, stop):
    (x0, y0), (x1, y1) = start, stop
    steps = max(abs(x1 - x0), abs(y1 - y0))
    return [(x0 + (x1 - x0) * k // steps, y0 + (y1 - y0) * k // steps) for k in range(steps + 1)]


def bump(key, counts):
    """Lift inner top grips a little, unevenly, so no top face is planar."""
    x, y, z = key
    if z != counts[2] or x in (0, counts[0]) or y in (0, counts[1]):
        return 0.0
    return 0.07 * x + 0.05 * y + 0.03 * x * y


def cage(name, counts, lines, listed=()):
    keys, points, quads = grid_box(counts, tuple(float(value) for value in counts))
    grips = tuple(ControlGrip(x, y, round(z + bump(key, counts), 12)) for key, (x, y, z) in zip(keys, points))
    surface = MakeClosedCage(grips, tuple(quads), Header=HEADER)
    extra = set()
    for start, stop in lines:
        extra |= path_edges(line(start, stop))
    edges, verts = crease_sets(surface, keys, counts, None, extra_edges=extra)
    lookup = {key: index for index, key in enumerate(keys)}
    verts = tuple(sorted(set(verts) | {lookup[(x, y, counts[2])] for x, y in listed}))
    surface = replace(surface, Creases=CreaseData(edges, verts))
    design = {'layout': 'fixed point box', 'quads': list(counts), 'top_creases': [[list(a), list(b)] for a, b in lines],
              'listed_top': [list(item) for item in listed], 'creased_edges': len(edges), 'crease_vertices': len(verts)}
    return name, surface, design


def cases():
    return [
        cage('LTurn', (3, 3, 1), [((1, 0), (1, 2)), ((1, 2), (3, 2))]),
        cage('LTurnWide', (4, 4, 1), [((2, 0), (2, 2)), ((2, 2), (4, 2))]),
        cage('TJunction', (2, 2, 1), [((1, 0), (1, 2)), ((1, 1), (2, 1))]),
        cage('TJunctionWide', (4, 4, 1), [((2, 0), (2, 4)), ((2, 2), (4, 2))]),
        cage('Cross', (4, 4, 1), [((2, 0), (2, 4)), ((0, 2), (4, 2))]),
        cage('ListedFlat', (2, 2, 1), [], listed=[(1, 1)]),
        cage('ListedLine', (2, 2, 1), [((1, 0), (1, 2))], listed=[(1, 1)]),
    ]


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, surface, design in cases():
        text = EmitTspline(surface)
        if ReadTspline(text) != surface:
            raise RuntimeError('TSM text does not read back')
        path = TARGET / (name + '.tsm')
        path.write_bytes(text)
        rows.append({'cage': name, 'tsm_file': str(path.relative_to(ROOT)), 'tsm_sha256': hashlib.sha256(text).hexdigest(), 'design': design})
    report = {'scope': 'Fixed-point probe: closed boxes with crease junctions on the top face', 'report': 'FixedRound/Probe.json',
              'python': sys.version.split()[0], 'cages': rows}
    (TARGET / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')
    print(len(rows), 'cages written to', TARGET.relative_to(ROOT))


if __name__ == '__main__':
    main()
