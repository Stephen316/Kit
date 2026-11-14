"""Research: the linear system of the G1 cap around one extraordinary vertex."""

import math

import numpy as np

from CapLab import Levels, cell_map, knot_list, reorient
from Sectors import SectorSurface, find_sectors


def blossom1(points, a, b, xs):
    pts = list(points)
    for x in xs:
        t = (x - a) / (b - a)
        pts = [(1 - t) * pts[k] + t * pts[k + 1] for k in range(len(pts) - 1)]
    return pts[0]


def blossom2(patch, au, bu, av, bv, xu, xv):
    rows = [blossom1(patch[q], au, bu, xu) for q in range(4)]
    return blossom1(rows, av, bv, xv)


class Reference:
    """Catmull-Clark limit pieces of each converted face, and blossoms of its poles."""

    def __init__(self, cage, body, faces, depth=4):
        self.levels = Levels(cage, depth)
        self.body = body
        self.faces = faces
        self.cache = {}

    def pieces(self, region):
        if region in self.cache:
            return self.cache[region]
        ku, kv, grid = self.faces[region]
        bu = [k for k, _ in ku]
        bv = [k for k, _ in kv]
        out = {}
        for j in range(len(bv) - 1):
            for i in range(len(bu) - 1):
                u0, u1, v0, v1 = bu[i], bu[i + 1], bv[j], bv[j + 1]
                for cell in self.body.Regions[region]:
                    to_face = cell_map(cell)
                    o = np.array(to_face(0, 0))
                    m = np.array([np.array(to_face(1, 0)) - o, np.array(to_face(0, 1)) - o]).T
                    inv = lambda u, v: np.linalg.solve(m, np.array([u, v]) - o)
                    p00, p10, p01 = inv(u0, v0), inv(u1, v0), inv(u0, v1)
                    lows = np.minimum.reduce([p00, p10, p01])
                    highs = np.maximum.reduce([p00, p10, p01])
                    if lows.min() < -1e-9 or highs.max() > 1 + 1e-9:
                        continue
                    net = self.levels.bezier(cell.Face, lows[0], highs[0], lows[1], highs[1])
                    if net is not None:
                        out[(i, j)] = reorient(net, p00, p10, p01, lows, highs)
                    break
        self.cache[region] = (bu, bv, out)
        return self.cache[region]

    def blossom(self, region, row, column):
        """CC blossom of face pole (row, column), or None when only irregular spans support it."""
        ku, kv, grid = self.faces[region]
        fu, fv = knot_list(ku), knot_list(kv)
        bu, bv, pieces = self.pieces(region)
        xu, xv = fu[column + 1:column + 4], fv[row + 1:row + 4]
        for j in range(len(bv) - 1):
            if not (fv[row] < bv[j + 1] and fv[row + 4] > bv[j]):
                continue
            for i in range(len(bu) - 1):
                if not (fu[column] < bu[i + 1] and fu[column + 4] > bu[i]):
                    continue
                if (i, j) in pieces:
                    return blossom2(pieces[(i, j)], bu[i], bu[i + 1], bv[j], bv[j + 1], xu, xv)
        return None


def lam_shape(x):
    """Fusion's G1 weight profile in units of the first cap knot h."""
    if x <= 1.0:
        return 1.0 - 2.0 * x / 3.0
    if x <= 2.0:
        return (2.0 - x) ** 2 / 3.0
    return 0.0


class CapSystem:
    def __init__(self, cage, body, faces, vertex, reach=4, size=8):
        self.vert = find_sectors(cage, body, faces, vertex)
        self.n = self.vert.valence
        self.sectors = self.vert.sectors
        self.size = size
        self.surfaces = [SectorSurface(sector, size) for sector in self.sectors]
        self.h = self.sectors[0].knots_i[4]
        self.reach = reach
        # unknown keys
        self.keys = [('ep',)]
        for k in range(self.n):
            for i in range(1, reach + 1):
                self.keys.append(('spoke', k, i))
        for k in range(self.n):
            for i in range(1, reach + 1):
                for j in range(1, reach + 1):
                    if (i, j) != (reach, reach):
                        self.keys.append(('in', k, i, j))
        self.slot = {key: index for index, key in enumerate(self.keys)}

    def key(self, k, i, j):
        k %= self.n
        if i == 0 and j == 0:
            return ('ep',)
        if i <= self.reach and j <= self.reach and (i, j) != (self.reach, self.reach):
            if j == 0:
                return ('spoke', k, i)
            if i == 0:
                return ('spoke', (k + 1) % self.n, j)
            return ('in', k, i, j)
        return ('fixed', k, i, j)

    def fusion_pole(self, key):
        if key[0] == 'ep':
            return self.sectors[0].pole(0, 0)
        if key[0] == 'spoke':
            return self.sectors[key[1]].pole(key[2], 0)
        if key[0] == 'in':
            return self.sectors[key[1]].pole(key[2], key[3])
        return self.sectors[key[1]].pole(key[2], key[3])

    def check_sharing(self):
        worst = 0.0
        for k in range(self.n):
            for i in range(self.size):
                a = self.sectors[k].pole(i, 0)
                b = self.sectors[(k - 1) % self.n].pole(0, i)
                worst = max(worst, np.abs(a - b).max())
        return worst

    def functional(self, k, s, t, ds=0, dt=0):
        """Linear functional over unknown slots plus a fixed part (grip vector)."""
        row = np.zeros(len(self.keys))
        fixed = 0.0
        for (i, j), w in self.surfaces[k].weights(s, t, ds, dt).items():
            key = self.key(k, i, j)
            if key[0] == 'fixed':
                fixed = fixed + w * self.sectors[k].pole(i, j)
            else:
                row[self.slot[key]] += w
        return row, fixed

    def g1_rows(self, sign=1.0, samples=None):
        """Rows of cross_k + cross_{k-1} - lambda * along = 0 along spoke k."""
        lam0 = 2.0 * math.cos(2.0 * math.pi / self.n)
        rows, fixed = [], []
        if samples is None:
            samples = np.concatenate([np.linspace(0, self.h, 6), np.linspace(self.h, 2 * self.h, 6), np.linspace(2 * self.h, 4 * self.h, 6)])
        for k in range(self.n):
            for s in samples:
                ra, fa = self.functional(k, s, 0.0, dt=1)
                rb, fb = self.functional((k - 1) % self.n, 0.0, s, ds=1)
                rt, ft = self.functional(k, s, 0.0, ds=1)
                lam = sign * lam0 * lam_shape(s / self.h)
                rows.append(ra + rb - lam * rt)
                fixed.append(fa + fb - lam * ft)
        return np.array(rows), fixed

    def quad_rows(self):
        """Third derivative of each spoke vanishes on [h, 2h] (third difference of Bezier points)."""
        rows, fixed = [], []
        h = self.h
        for k in range(self.n):
            vals = [self.functional(k, h + h * x / 3.0, 0.0) for x in range(4)]
            row = vals[3][0] - 3 * vals[2][0] + 3 * vals[1][0] - vals[0][0]
            fix = vals[3][1] - 3 * vals[2][1] + 3 * vals[1][1] - vals[0][1]
            rows.append(row)
            fixed.append(fix)
        return np.array(rows), fixed

    def fusion_vector(self):
        return np.array([self.fusion_pole(key) for key in self.keys])


def as_matrix(fixed, grips):
    out = []
    for value in fixed:
        if isinstance(value, float):
            out.append(np.zeros(grips))
        else:
            out.append(value)
    return np.array(out)
