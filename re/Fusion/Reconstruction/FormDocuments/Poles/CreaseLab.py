"""Research: Catmull-Clark subdivision with sharp edges (Hoppe crease rules, infinite sharpness)
and the reflected B-spline net of every face whose limit is polynomial.

Rules:
- face point: average of the face vertices;
- smooth edge: (v1 + v2 + f1 + f2) / 4; sharp edge (creased or open): (v1 + v2) / 2;
- vertex with no sharp edge or one (dart): (F + 2E + (n - 3) v) / n;
  two sharp edges (crease): (a + 6 v + b) / 8 with a, b its sharp neighbours;
  three or more sharp edges, or a listed crease vertex: v (corner).
Children of sharp edges stay sharp, corners stay corners.

A face whose four corners are smooth valence 4, crease vertices with exactly two faces on the
face's side of the crease, or corners with the face alone between two sharp edges has a
polynomial limit: the uniform bicubic B-spline of its 4 x 4 net where each row across a sharp
side is the reflection 2 near - far. Reflection makes the B-spline vertex rule across the crease
the identity and leaves the 1-6-1 rule along it, so it reproduces the crease rules exactly.
"""

import numpy as np

CORNERS = ((0, 0), (1, 0), (1, 1), (0, 1))
OUTWARD = ((0, -1), (1, 0), (0, 1), (-1, 0))


class Mesh:
    def __init__(self, faces, values, sharp=(), corners=()):
        self.faces = [tuple(loop) for loop in faces]
        self.values = values
        self.sharp = set(frozenset(e) for e in sharp)
        self.corners = set(corners)
        self.half = {}
        for index, loop in enumerate(self.faces):
            for corner, vertex in enumerate(loop):
                self.half[(vertex, loop[(corner + 1) % len(loop)])] = (index, corner)
        self.neighbours = {}
        for (a, b) in self.half:
            self.neighbours.setdefault(a, set()).add(b)
            self.neighbours.setdefault(b, set()).add(a)
            if (b, a) not in self.half:
                self.sharp.add(frozenset((a, b)))
        self.sharp_at = {}
        for edge in self.sharp:
            for v in edge:
                self.sharp_at.setdefault(v, []).append(edge)

    @classmethod
    def from_surface(cls, surface, use_corners=True):
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
        values = np.zeros((count, len(surface.Grips)))
        for vertex in range(count):
            values[vertex, grip_of.get(vertex, vertex)] = 1.0
        sharp, corners = set(), set()
        if surface.Creases is not None:
            chosen = set(surface.Creases.EdgeIndices)
            for link in links:
                if link.EdgeIndex in chosen:
                    sharp.add(frozenset((link.VertexIndex, links[link.NextLink].VertexIndex)))
            if use_corners:
                corners = set(surface.Creases.VertexIndices)
        mesh = cls(faces, values, sharp, corners)
        mesh.grip_of = grip_of
        return mesh

    def kind(self, v):
        count = len(self.sharp_at.get(v, ()))
        if v in self.corners or count >= 3:
            return 'corner'
        if count == 2:
            return 'crease'
        if count == 1:
            return 'dart'
        return 'smooth'

    def group(self, v, face):
        """Faces around v reachable from `face` without crossing a sharp edge."""
        seen, todo = {face}, [face]
        while todo:
            f = todo.pop()
            loop = self.faces[f]
            corner = loop.index(v)
            for w in (loop[(corner + 1) % len(loop)], loop[(corner - 1) % len(loop)]):
                if frozenset((v, w)) in self.sharp:
                    continue
                for key in ((v, w), (w, v)):
                    if key in self.half and self.half[key][0] not in seen:
                        seen.add(self.half[key][0])
                        todo.append(self.half[key][0])
        return seen


def subdivide(mesh):
    faces, values = mesh.faces, mesh.values
    rows = []
    face_point = {}
    for index, loop in enumerate(faces):
        face_point[index] = len(rows)
        rows.append(values[list(loop)].mean(axis=0))
    edge_faces = {}
    for (a, b), (face, _) in mesh.half.items():
        edge_faces.setdefault(frozenset((a, b)), []).append(face)
    edge_point = {}
    for edge, around in edge_faces.items():
        a, b = tuple(edge)
        edge_point[edge] = len(rows)
        if edge in mesh.sharp or len(around) != 2:
            rows.append(0.5 * (values[a] + values[b]))
        else:
            rows.append(0.25 * (values[a] + values[b] + rows[face_point[around[0]]] + rows[face_point[around[1]]]))
    near_faces, near_edges = {}, {}
    for index, loop in enumerate(faces):
        for vertex in loop:
            near_faces.setdefault(vertex, []).append(index)
    for edge in edge_faces:
        for vertex in edge:
            near_edges.setdefault(vertex, []).append(edge)
    vertex_point = {}
    for vertex in range(len(values)):
        vertex_point[vertex] = len(rows)
        if vertex not in near_faces:
            rows.append(values[vertex])
            continue
        kind = mesh.kind(vertex)
        if kind == 'corner':
            rows.append(values[vertex])
        elif kind == 'crease':
            a, b = [next(iter(e - {vertex})) for e in mesh.sharp_at[vertex]]
            rows.append((values[a] + 6.0 * values[vertex] + values[b]) / 8.0)
        else:
            count = len(near_edges[vertex])
            face_mean = np.mean([rows[face_point[f]] for f in near_faces[vertex]], axis=0)
            edge_mean = np.mean([0.5 * (values[a] + values[b]) for a, b in (tuple(e) for e in near_edges[vertex])], axis=0)
            rows.append((face_mean + 2.0 * edge_mean + (count - 3) * values[vertex]) / count)
    children = []
    for index, loop in enumerate(faces):
        size = len(loop)
        for corner, vertex in enumerate(loop):
            after, before = loop[(corner + 1) % size], loop[(corner - 1) % size]
            children.append((vertex_point[vertex], edge_point[frozenset((vertex, after))], face_point[index],
                             edge_point[frozenset((before, vertex))]))
    sharp = set()
    for edge in mesh.sharp:
        if edge not in edge_point:
            continue
        a, b = tuple(edge)
        sharp.add(frozenset((vertex_point[a], edge_point[edge])))
        sharp.add(frozenset((edge_point[edge], vertex_point[b])))
    corners = {vertex_point[v] for v in near_faces if mesh.kind(v) == 'corner'}
    child = Mesh(children, np.array(rows), sharp, corners)
    child.parent_vertex = vertex_point
    return child


def corner_ok(mesh, v, face):
    kind = mesh.kind(v)
    if kind == 'smooth':
        return len(mesh.neighbours[v]) == 4
    if kind == 'dart':
        return False
    size = len(mesh.group(v, face))
    if kind == 'corner':
        return size == 1
    return size == 2


def diagonal(mesh, loop, k):
    """Vertex diagonally across corner k of a face (smooth valence-4 corner)."""
    v, before = loop[k], loop[(k - 1) % 4]
    if (v, before) not in mesh.half:
        return None
    face, corner = mesh.half[(v, before)]
    ring = mesh.faces[face]
    w = ring[(corner - 1) % 4]
    if (v, w) not in mesh.half:
        return None
    face, corner = mesh.half[(v, w)]
    ring = mesh.faces[face]
    return ring[(corner + 2) % 4]


class Levels:
    def __init__(self, mesh, depth=4):
        self.levels = [mesh]
        for _ in range(depth):
            self.levels.append(subdivide(self.levels[-1]))

    def net(self, level, face):
        return regular_net(self.levels[level], face)


def regular_net(mesh, face):
    """4 x 4 net (rows t, columns s) of a face, reflected across sharp sides, or None."""
    loop = list(mesh.faces[face])
    if len(loop) != 4:
        return None
    if not all(corner_ok(mesh, v, face) for v in loop):
        return None
    vals = mesh.values
    grid = {CORNERS[k]: vals[loop[k]] for k in range(4)}
    side_sharp = [frozenset((loop[k], loop[(k + 1) % 4])) in mesh.sharp for k in range(4)]
    for k in range(4):
        a, b = loop[k], loop[(k + 1) % 4]
        pa, pb = CORNERS[k], CORNERS[(k + 1) % 4]
        dx, dy = OUTWARD[k]
        oa, ob = (pa[0] + dx, pa[1] + dy), (pb[0] + dx, pb[1] + dy)
        if side_sharp[k]:
            grid[oa] = 2 * grid[pa] - grid[(pa[0] - dx, pa[1] - dy)]
            grid[ob] = 2 * grid[pb] - grid[(pb[0] - dx, pb[1] - dy)]
        else:
            other, corner = mesh.half[(b, a)]
            ring = mesh.faces[other]
            grid[oa] = vals[ring[(corner + 2) % 4]]
            grid[ob] = vals[ring[(corner + 3) % 4]]
    for k in range(4):
        p = CORNERS[k]
        prev_side, next_side = (k - 1) % 4, k
        d = (p[0] + OUTWARD[prev_side][0] + OUTWARD[next_side][0], p[1] + OUTWARD[prev_side][1] + OUTWARD[next_side][1])
        if side_sharp[next_side] or side_sharp[prev_side]:
            side = next_side if side_sharp[next_side] else prev_side
            dx, dy = OUTWARD[side]
            near = (d[0] - dx, d[1] - dy)
            far = (d[0] - 2 * dx, d[1] - 2 * dy)
            grid[d] = 2 * grid[near] - grid[far]
        else:
            w = diagonal(mesh, loop, k)
            if w is None:
                return None
            grid[d] = vals[w]
    return np.array([[grid[(i - 1, j - 1)] for i in range(4)] for j in range(4)])
