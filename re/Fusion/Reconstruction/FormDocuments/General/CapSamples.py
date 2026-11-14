"""Recover the cap response of an isolated extraordinary point from cap prism saves.

Each cap prism save gives the converted poles for one grip sample. The response is
rotation equivariant, so the poles of every sector of every sample constrain one row
per local pole (i, j): coefficients over the EP grip and the grips (d, a, b) of the
sector d steps ahead, 1 <= a <= reach, 0 <= b <= reach. Writes CapResponse<n>.npz with
rows[(i, j)] and the fit residual.
"""
import sys
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from CapLab import ROOT, Cage, load_surface  # noqa: E402
from Sectors import find_sectors  # noqa: E402
from Unfold import unfold  # noqa: E402
from ReadConverted import ReadConverted  # noqa: E402

SAVES = ROOT / 're/Fusion/LocalOracle/FormDocuments/General/tmp'
CAGES = ROOT / 're/Fusion/LocalOracle/FormDocuments/General/Caps'
OUT = ROOT / 're/Fusion/LocalOracle/FormDocuments/General/tmp'
CELLS = 3
REACH = 3
SIZE = 8


def faces_3d(body):
    out = {}
    for face in body.Faces:
        cache = face.Surface.Cache
        knots_u = [(k.Value, k.Count) for k in cache.KnotsU]
        knots_v = [(k.Value, k.Count) for k in cache.KnotsV]
        count_u = sum(c for _, c in knots_u) - 2
        count_v = sum(c for _, c in knots_v) - 2
        grid = np.array([tuple(p)[:3] for p in cache.Points], dtype=float).reshape(count_v, count_u, 3)
        out[face.Surface.Region] = (knots_u, knots_v, grid)
    return out


def centres(sides):
    return [0, 1 + sides * CELLS + sides * CELLS * CELLS]


def samples(sides):
    out = []
    for path in sorted(SAVES.glob('CapPrism%d_*.f3d' % sides)):
        surface = load_surface(CAGES / (path.stem + '.tsm'))[0]
        model = load_surface(path)[1]
        cage = Cage.from_surface(surface)
        body = ReadConverted(model)
        faces = faces_3d(body)
        grips = np.array([[g.CoordX, g.CoordY, g.CoordZ] for g in surface.Grips], dtype=float)
        for v in centres(sides):
            vert = find_sectors(cage, body, faces, v)
            ring = [(sec.face, sec.corner) for sec in vert.sectors]
            labels = unfold(cage, v, REACH + 1, ring)[1]
            poles = {}
            for k, sec in enumerate(vert.sectors):
                for i in range(SIZE):
                    for j in range(SIZE):
                        try:
                            poles[(k, i, j)] = np.array(sec.pole(i, j), dtype=float)
                        except IndexError:
                            pass
            out.append((path.stem, v, grips[[cage.grip_of.get(v, v)]][0], labels, grips, cage, poles))
    return out


def features(sides, k, sample):
    _, v, ep, labels, grips, cage, _ = sample
    cols = [ep]
    for d in range(sides):
        for a in range(1, REACH + 1):
            for b in range(0, REACH + 1):
                vertex = labels[((k + d) % sides, a, b)]
                cols.append(grips[cage.grip_of.get(vertex, vertex)])
    return np.array(cols)


def names(sides):
    return ['ep'] + ['%d,%d,%d' % (d, a, b) for d in range(sides) for a in range(1, REACH + 1) for b in range(0, REACH + 1)]


def recover(sides):
    data = samples(sides)
    rows, worst = {}, {}
    for i in range(SIZE):
        for j in range(SIZE):
            A, y = [], []
            for sample in data:
                poles = sample[-1]
                for k in range(sides):
                    if (k, i, j) not in poles:
                        continue
                    F = features(sides, k, sample)
                    for c in range(3):
                        A.append(F[:, c])
                        y.append(poles[(k, i, j)][c])
            if not A:
                continue
            A, y = np.array(A), np.array(y)
            coef, *_ = np.linalg.lstsq(A, y, rcond=None)
            rows[(i, j)] = coef
            worst[(i, j)] = float(np.abs(A @ coef - y).max())
            if np.linalg.matrix_rank(A) < A.shape[1]:
                worst[(i, j)] = float('nan')
    return rows, worst, len(data)


def main():
    for sides in [int(a) for a in sys.argv[1:]] or [3, 5, 6, 7, 8]:
        rows, worst, count = recover(sides)
        keys = sorted(rows)
        np.savez(OUT / ('CapResponse%d.npz' % sides), keys=np.array(keys), rows=np.array([rows[k] for k in keys]), worst=np.array([worst[k] for k in keys]), names=np.array(names(sides)))
        bad = [k for k in keys if not worst[k] < 1e-9]
        print('valence', sides, 'samples', count, 'poles', len(keys), 'worst residual %.2e' % max(w for w in worst.values() if w == w), 'unresolved', bad[:6], 'ep row sum %.12f' % rows[(0, 0)].sum())


if __name__ == '__main__':
    main()
