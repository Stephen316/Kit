"""Research: Catmull-Clark reference geometry for Fusion Form conversions.

Every value is a coefficient vector over the cage grips, so the tools compare
Fusion's converted poles with candidate rules for every grip move at once.
"""

import json
import lzma
import sys
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 're/Fusion/Reconstruction/FormDocuments/Cages'))

from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument  # noqa: E402
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline  # noqa: E402

STENCILS = ROOT / 're/Fusion/Reconstruction/FormDocuments/Stencil/FormStencils.xz'
if not STENCILS.exists():
    STENCILS = ROOT / 're/Fusion/Reconstruction/FormDocuments/Tables/FormStencils.xz'

CORNERS = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
B2Z = np.array([[1, 4, 1, 0], [0, 4, 2, 0], [0, 2, 4, 0], [0, 1, 4, 1]], dtype=float) / 6.0


def load_surface(path):
    path = Path(path)
    data = path.read_bytes()
    if path.suffix == '.tsm':
        return ReadTspline(data), None
    model = ReadDocument(data)
    return model.Forms[0].Surface, model


class Cage:
    """Level of a quad mesh with grip-space coefficient rows for each vertex."""

    def __init__(self, faces, values, creases=frozenset(), corners=frozenset()):
        self.faces = [tuple(loop) for loop in faces]
        self.values = values
        self.half = {}
        for index, loop in enumerate(self.faces):
            for corner, vertex in enumerate(loop):
                self.half[(vertex, loop[(corner + 1) % len(loop)])] = (index, corner)
        self.valence = {}
        self.boundary = set()
        for (a, b) in self.half:
            self.valence[a] = self.valence.get(a, 0) + 1
            if (b, a) not in self.half:
                self.boundary.add(frozenset((a, b)))
        self.creases = set(creases) | self.boundary
        self.corners = set(corners)

    @classmethod
    def from_surface(cls, surface):
        topology = surface.Topology
        links = topology.Links
        grip_of = {}
        if surface.Mapping is not None:
            for grip, owner in enumerate(surface.Mapping.Owners):
                if owner.IsPrimary:
                    grip_of[owner.VertexIndex] = grip
        faces = []
        for face in topology.Faces:
            loop, link = [], face.OriginLink
            while True:
                loop.append(links[link].VertexIndex)
                link = links[link].NextLink
                if link == face.OriginLink:
                    break
            faces.append(loop)
        count = len(topology.Vertices)
        grips = len(surface.Grips)
        values = np.zeros((count, grips))
        for vertex in range(count):
            values[vertex, grip_of.get(vertex, vertex)] = 1.0
        creases = set()
        corners = set()
        if surface.Creases is not None:
            chosen = set(surface.Creases.EdgeIndices)
            for link in links:
                if link.EdgeIndex in chosen:
                    creases.add(frozenset((link.VertexIndex, links[link.NextLink].VertexIndex)))
            corners = set(surface.Creases.VertexIndices)
        cage = cls(faces, values, creases, corners)
        cage.surface = surface
        cage.grip_of = grip_of
        return cage

    def ring(self, vertex):
        """Faces around a vertex in order, as (face, corner) pairs."""
        start = next(key for key in self.half if key[0] == vertex)
        found = []
        key = start
        while True:
            face, corner = self.half[key]
            found.append((face, corner))
            loop = self.faces[face]
            previous = loop[(corner - 1) % len(loop)]
            key = (vertex, previous)
            if key not in self.half or key == start:
                break
        return found


def subdivide(cage):
    """One Catmull-Clark step without creases. Child face 4f+i keeps corner i of face f."""
    faces, values = cage.faces, cage.values
    rows = []
    face_point = {}
    for index, loop in enumerate(faces):
        face_point[index] = len(rows)
        rows.append(values[list(loop)].mean(axis=0))
    edge_faces = {}
    for (a, b), (face, _) in cage.half.items():
        edge_faces.setdefault(frozenset((a, b)), []).append(face)
    edge_point = {}
    for edge, around in edge_faces.items():
        a, b = tuple(edge)
        edge_point[edge] = len(rows)
        if len(around) == 2:
            rows.append(0.25 * (values[a] + values[b] + rows[face_point[around[0]]] + rows[face_point[around[1]]]))
        else:
            rows.append(0.5 * (values[a] + values[b]))
    vertex_point = {}
    near_faces, near_edges = {}, {}
    for index, loop in enumerate(faces):
        for vertex in loop:
            near_faces.setdefault(vertex, []).append(index)
    for edge in edge_faces:
        for vertex in edge:
            near_edges.setdefault(vertex, []).append(edge)
    for vertex in range(len(values)):
        if vertex not in near_faces:
            vertex_point[vertex] = len(rows)
            rows.append(values[vertex])
            continue
        count = len(near_edges[vertex])
        face_mean = np.mean([rows[face_point[face]] for face in near_faces[vertex]], axis=0)
        edge_mean = np.mean([0.5 * (values[a] + values[b]) for a, b in (tuple(edge) for edge in near_edges[vertex])], axis=0)
        vertex_point[vertex] = len(rows)
        rows.append((face_mean + 2.0 * edge_mean + (count - 3) * values[vertex]) / count)
    children = []
    for index, loop in enumerate(faces):
        size = len(loop)
        for corner, vertex in enumerate(loop):
            after, before = loop[(corner + 1) % size], loop[(corner - 1) % size]
            children.append((vertex_point[vertex], edge_point[frozenset((vertex, after))], face_point[index], edge_point[frozenset((before, vertex))]))
    child = Cage(children, np.array(rows))
    child.parent_vertex = vertex_point
    return child


def child_frame(corner):
    """Map child-local (s, t) to parent-local coordinates for child corner i."""
    origin = np.array(CORNERS[corner])
    axis_u = np.array(CORNERS[(corner + 1) % 4]) - origin
    axis_v = np.array(CORNERS[(corner - 1) % 4]) - origin
    return origin, 0.5 * axis_u, 0.5 * axis_v


def regular_net(cage, face):
    """4x4 vertex grid around a quad whose corners all have valence 4, in face-local order."""
    loop = cage.faces[face]
    if any(cage.valence.get(vertex) != 4 for vertex in loop):
        return None
    grid = {(0, 0): loop[0], (1, 0): loop[1], (1, 1): loop[2], (0, 1): loop[3]}
    sides = (((loop[1], loop[0]), (0, -1), (1, -1)), ((loop[2], loop[1]), (2, 0), (2, 1)), ((loop[3], loop[2]), (1, 2), (0, 2)), ((loop[0], loop[3]), (-1, 1), (-1, 0)))
    for (a, b), far_b, far_a in sides:
        if (a, b) not in cage.half:
            return None
        other, corner = cage.half[(a, b)]
        ring = cage.faces[other]
        grid[far_b] = ring[(corner + 2) % 4]
        grid[far_a] = ring[(corner + 3) % 4]
    for spot, side_a, middle, side_b in (((-1, -1), (-1, 0), (0, 0), (0, -1)), ((2, -1), (1, -1), (1, 0), (2, 0)), ((2, 2), (2, 1), (1, 1), (1, 2)), ((-1, 2), (0, 2), (0, 1), (-1, 1))):
        key = (grid[side_b], grid[middle])
        if key not in cage.half:
            return None
        other, corner = cage.half[key]
        ring = cage.faces[other]
        if ring[(corner + 2) % 4] != grid[side_a]:
            return None
        grid[spot] = ring[(corner + 3) % 4]
    return np.array([[cage.values[grid[(i - 1, j - 1)]] for i in range(4)] for j in range(4)])


def bezier_from_net(net):
    """Uniform B-spline 4x4 net (rows v, columns u) to bicubic Bezier net."""
    return np.einsum('ai,bj,jik->bak', B2Z, B2Z, net)


def restrict(bezier, low_u, high_u, low_v, high_v):
    """Bezier net of the sub-rectangle [low_u, high_u] x [low_v, high_v] of the unit square."""
    def matrix(low, high):
        out = np.zeros((4, 4))
        nodes = np.linspace(0, 1, 4)
        basis = np.array([[1, 0, 0, 0], [-3, 3, 0, 0], [3, -6, 3, 0], [-1, 3, -3, 1]], dtype=float)
        target = np.array([[1, x, x * x, x ** 3] for x in low + (high - low) * nodes]) @ basis
        local = np.array([[1, x, x * x, x ** 3] for x in nodes]) @ basis
        out = np.linalg.solve(local, target)
        return out
    mu, mv = matrix(low_u, high_u), matrix(low_v, high_v)
    return np.einsum('ai,bj,jik->bak', mu, mv, bezier)


class Levels:
    def __init__(self, cage, depth=4):
        self.levels = [cage]
        for _ in range(depth):
            self.levels.append(subdivide(self.levels[-1]))

    def bezier(self, face, low_u, high_u, low_v, high_v, level=0):
        """CC limit Bezier net of a rectangle of a level-0 face, or None near an irregular corner."""
        cage = self.levels[level]
        net = regular_net(cage, face)
        if net is not None:
            return restrict(bezier_from_net(net), low_u, high_u, low_v, high_v)
        if level + 1 >= len(self.levels):
            return None
        mid_u, mid_v = 0.5, 0.5
        if not ((high_u <= mid_u + 1e-12 or low_u >= mid_u - 1e-12) and (high_v <= mid_v + 1e-12 or low_v >= mid_v - 1e-12)):
            return None
        quadrant = (low_u >= mid_u - 1e-12, low_v >= mid_v - 1e-12)
        corner = {(False, False): 0, (True, False): 1, (True, True): 2, (False, True): 3}[quadrant]
        origin, axis_u, axis_v = child_frame(corner)
        inverse = np.linalg.inv(np.array([axis_u, axis_v]).T)
        points = [inverse @ (np.array(p) - origin) for p in ((low_u, low_v), (high_u, low_v), (low_u, high_v))]
        start, along_u, along_v = points
        child = 4 * face + corner
        lows = np.minimum.reduce(points)
        highs = np.maximum.reduce(points)
        net = self.bezier(child, lows[0], highs[0], lows[1], highs[1], level + 1)
        if net is None:
            return None
        return reorient(net, start, along_u, along_v, lows, highs)


def reorient(net, start, along_u, along_v, lows, highs):
    """Reindex a child Bezier net so that its axes follow the parent rectangle."""
    flip_u_child = None
    du = along_u - start
    dv = along_v - start
    swap = abs(du[0]) < 1e-12
    out = net
    if swap:
        out = np.transpose(out, (1, 0, 2))
        du = du[::-1]
        dv = dv[::-1]
    if du[0] < 0:
        out = out[:, ::-1]
    if dv[1] < 0:
        out = out[::-1, :]
    return out


def knot_list(knots):
    full = []
    for value, count in knots:
        full += [float(value)] * int(count)
    return [full[0]] + full + [full[-1]]


def insert_knot(knots, poles, value, axis):
    """Boehm insertion of one knot into a degree-3 B-spline with poles along the given axis."""
    p = 3
    k = max(i for i in range(len(knots) - 1) if knots[i] <= value and knots[i] < knots[-1])
    if value >= knots[-1]:
        raise ValueError('knot at end')
    poles = np.moveaxis(poles, axis, 0)
    new = [None] * (len(poles) + 1)
    for i in range(len(poles) + 1):
        if i <= k - p:
            new[i] = poles[i]
        elif i >= k + 1:
            new[i] = poles[i - 1]
        else:
            alpha = (value - knots[i]) / (knots[i + p] - knots[i])
            new[i] = alpha * poles[i] + (1 - alpha) * poles[i - 1]
    knots = knots[: k + 1] + [value] + knots[k + 1:]
    return knots, np.moveaxis(np.array(new), 0, axis)


def to_bezier(knots_u, knots_v, poles):
    """Split a bicubic B-spline (poles indexed [v][u][...]) into Bezier patches keyed by span."""
    ku, kv = knot_list(knots_u), knot_list(knots_v)
    for value, count in knots_u[1:-1]:
        for _ in range(3 - count):
            ku, poles = insert_knot(ku, poles, value, 1)
    for value, count in knots_v[1:-1]:
        for _ in range(3 - count):
            kv, poles = insert_knot(kv, poles, value, 0)
    breaks_u = [value for value, _ in knots_u]
    breaks_v = [value for value, _ in knots_v]
    patches = {}
    for j in range(len(breaks_v) - 1):
        for i in range(len(breaks_u) - 1):
            patches[(i, j)] = poles[3 * j:3 * j + 4, 3 * i:3 * i + 4]
    return breaks_u, breaks_v, patches


def read_tables():
    data = json.loads(lzma.decompress(STENCILS.read_bytes()))
    return {table['Label']: table for table in data['Tables']}


def table_rows(table):
    grips = table['GripCount']
    rows = np.zeros((len(table['Rows']), grips))
    for index, row in enumerate(table['Rows']):
        for grip, value in row:
            rows[index, grip] = value
    return rows


def table_faces(table):
    rows = table_rows(table)
    out = {}
    for face_index, knots_u, knots_v, poles in table['Faces']:
        count_u = sum(c for _, c in knots_u) - 2
        count_v = sum(c for _, c in knots_v) - 2
        grid = rows[poles].reshape(count_v, count_u, -1)
        out[face_index] = (knots_u, knots_v, grid)
    return out, rows


def cell_map(cell):
    """Return a function mapping cage-face local (s, t) to B-rep face (u, v) for a patch cell."""
    off_v, off_u, turn = cell.Offset
    def to_face(s, t):
        x, y = s - off_u, t - off_v
        for _ in range(turn % 4):
            x, y = -y, x
        return x, y
    return to_face
