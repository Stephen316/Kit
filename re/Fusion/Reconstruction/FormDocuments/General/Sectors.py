"""Research: the sectors of Fusion's converted faces around each extraordinary vertex.

A sector is the corner of one converted face at the vertex. Its local pole
grid p[i][j] runs i along spoke k and j along spoke k + 1, with knot vectors
read outward from the vertex.
"""

import math

import numpy as np

from CapLab import CORNERS, Cage, cell_map, knot_list, load_surface, read_tables, table_faces
from ReadConverted import ReadConverted


def basis(knots, x, degree=3):
    """All degree-3 B-spline basis values at x on a full knot vector (right-continuous, closed at the end)."""
    count = len(knots) - degree - 1
    values = np.zeros(count)
    top = knots[-1]
    for i in range(count):
        values[i] = cox(knots, i, degree, min(x, top - 1e-13) if x >= top else x)
    return values


def cox(t, i, p, x):
    if p == 0:
        return 1.0 if t[i] <= x < t[i + 1] else 0.0
    a = 0.0 if t[i + p] == t[i] else (x - t[i]) / (t[i + p] - t[i]) * cox(t, i, p - 1, x)
    b = 0.0 if t[i + p + 1] == t[i + 1] else (t[i + p + 1] - x) / (t[i + p + 1] - t[i + 1]) * cox(t, i + 1, p - 1, x)
    return a + b


def dbasis(knots, x, degree=3):
    count = len(knots) - degree - 1
    lower = basis(knots, x, degree - 1) if degree > 1 else None
    lower = [cox(knots, i, degree - 1, min(x, knots[-1] - 1e-13)) for i in range(count + 1)]
    out = np.zeros(count)
    for i in range(count):
        a = knots[i + degree] - knots[i]
        b = knots[i + degree + 1] - knots[i + 1]
        out[i] = degree * ((lower[i] / a if a > 0 else 0.0) - (lower[i + 1] / b if b > 0 else 0.0))
    return out


class Sector:
    def __init__(self, k, face, corner, region, grid, knots_u, knots_v, origin, axis_u, axis_v):
        self.k = k
        self.face = face
        self.corner = corner
        self.region = region
        self.grid = grid
        self.origin = origin
        self.axis_u = axis_u
        self.axis_v = axis_v
        full_u, full_v = knot_list(knots_u), knot_list(knots_v)
        count_u, count_v = grid.shape[1], grid.shape[0]

        def local(full, start, step):
            if step > 0:
                return [x - start for x in full], (lambda i: i)
            return [start - x for x in reversed(full)], None

        # direction of local i (spoke k) in face params
        def axis_info(axis):
            if axis[0] != 0:
                return 'u', axis[0], origin[0]
            return 'v', axis[1], origin[1]

        self.iu = axis_info(axis_u)
        self.iv = axis_info(axis_v)
        knots = {'u': full_u, 'v': full_v}
        counts = {'u': count_u, 'v': count_v}
        self.knots_i = self._local(knots[self.iu[0]], self.iu[1], self.iu[2])
        self.knots_j = self._local(knots[self.iv[0]], self.iv[1], self.iv[2])
        self.count = counts

    @staticmethod
    def _local(full, step, start):
        if step > 0:
            return [x - start for x in full]
        return [start - x for x in reversed(full)]

    def index(self, i, j):
        """Face grid index (row v, column u) of local pole (i, j)."""
        place = {}
        for name, step, start, value in ((self.iu[0], self.iu[1], self.iu[2], i), (self.iv[0], self.iv[1], self.iv[2], j)):
            place[name] = value if step > 0 else self.count[name] - 1 - value
        return place['v'], place['u']

    def pole(self, i, j):
        r, c = self.index(i, j)
        return self.grid[r, c]


class Vertex:
    def __init__(self, vertex, valence, sectors):
        self.vertex = vertex
        self.valence = valence
        self.sectors = sectors


def load(label, carrier):
    surface, model = load_surface(carrier)
    body = ReadConverted(model)
    cage = Cage.from_surface(surface)
    tables = read_tables()
    faces, rows = table_faces(tables[label])
    return cage, body, faces


def find_sectors(cage, body, faces, vertex):
    where = {}
    for region, cells in enumerate(body.Regions):
        for cell in cells:
            where[cell.Face] = (region, cell)
    ring = cage.ring(vertex)
    sectors = []
    for k, (face, corner) in enumerate(ring):
        region, cell = where[face]
        to_face = cell_map(cell)
        origin = np.array(to_face(*CORNERS[corner]))
        axis_u = np.array(to_face(*CORNERS[(corner + 1) % 4])) - origin
        axis_v = np.array(to_face(*CORNERS[(corner - 1) % 4])) - origin
        knots_u, knots_v, grid = faces[region]
        sectors.append(Sector(k, face, corner, region, grid, knots_u, knots_v, origin, axis_u, axis_v))
    return Vertex(vertex, len(ring), sectors)


def extraordinary(cage):
    return [v for v, n in sorted(cage.valence.items()) if n != 4]


class SectorSurface:
    """Evaluate one sector from its local poles p[(i, j)] (grip vectors), i, j < size."""

    def __init__(self, sector, size=8):
        self.sector = sector
        self.size = size

    def weights(self, s, t, ds=0, dt=0):
        ki, kj = self.sector.knots_i, self.sector.knots_j
        bi = dbasis(ki, s) if ds else basis(ki, s)
        bj = dbasis(kj, t) if dt else basis(kj, t)
        out = {}
        for i in range(self.size):
            for j in range(self.size):
                w = bi[i] * bj[j]
                if w != 0.0:
                    out[(i, j)] = w
        return out
