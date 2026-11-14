import math
import random
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.TSplineCodec.MakeClosedCage import MakeClosedCage
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.Model.CreaseData import CreaseData
from convert.formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader

HEADER = SurfaceHeader(VersionCount=1)


def split_faces(points, faces):
    points = list(points)
    edge_points = {}
    quads = []

    def midpoint(a, b):
        key = (min(a, b), max(a, b))
        if key not in edge_points:
            edge_points[key] = len(points)
            points.append(tuple((p + q) / 2 for p, q in zip(points[a], points[b])))
        return edge_points[key]

    for face in faces:
        center = len(points)
        points.append(tuple(sum(points[index][axis] for index in face) / len(face) for axis in range(3)))
        count = len(face)
        for step in range(count):
            here, after, before = face[step], face[(step + 1) % count], face[step - 1]
            quads.append((here, midpoint(here, after), center, midpoint(before, here)))
    return points, quads


def box(nx, ny, nz, size=(2.0, 2.0, 2.0)):
    counts = (nx, ny, nz)
    lookup = {}
    points = []
    quads = []

    def index(key):
        if key not in lookup:
            lookup[key] = len(points)
            points.append(tuple(size[axis] * key[axis] / counts[axis] for axis in range(3)))
        return lookup[key]

    for axis in range(3):
        other = [item for item in range(3) if item != axis]
        for side in (0, counts[axis]):
            for first in range(counts[other[0]]):
                for second in range(counts[other[1]]):
                    corners = []
                    for du, dv in ((0, 0), (1, 0), (1, 1), (0, 1)):
                        key = [0, 0, 0]
                        key[axis], key[other[0]], key[other[1]] = side, first + du, second + dv
                        corners.append(tuple(key))
                    a, b, d = corners[0], corners[1], corners[3]
                    normal = [(b[1] - a[1]) * (d[2] - a[2]) - (b[2] - a[2]) * (d[1] - a[1]), (b[2] - a[2]) * (d[0] - a[0]) - (b[0] - a[0]) * (d[2] - a[2]), (b[0] - a[0]) * (d[1] - a[1]) - (b[1] - a[1]) * (d[0] - a[0])]
                    outward = normal[axis] * (1 if side else -1)
                    ordered = corners if outward > 0 else list(reversed(corners))
                    quads.append(tuple(index(key) for key in ordered))
    return points, quads


def polycube(cubes, unit=1.0):
    cubes = set(cubes)
    lookup = {}
    points = []
    quads = []

    def index(key):
        if key not in lookup:
            lookup[key] = len(points)
            points.append(tuple(unit * value for value in key))
        return lookup[key]

    for cube in sorted(cubes):
        for axis in range(3):
            for sign in (-1, 1):
                other = list(cube)
                other[axis] += sign
                if tuple(other) in cubes:
                    continue
                plane = cube[axis] + (1 if sign > 0 else 0)
                rest = [item for item in range(3) if item != axis]
                corners = []
                for du, dv in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    key = [0, 0, 0]
                    key[axis] = plane
                    key[rest[0]] = cube[rest[0]] + du
                    key[rest[1]] = cube[rest[1]] + dv
                    corners.append(tuple(key))
                a, b, d = corners[0], corners[1], corners[3]
                normal = [(b[1] - a[1]) * (d[2] - a[2]) - (b[2] - a[2]) * (d[1] - a[1]), (b[2] - a[2]) * (d[0] - a[0]) - (b[0] - a[0]) * (d[2] - a[2]), (b[0] - a[0]) * (d[1] - a[1]) - (b[1] - a[1]) * (d[0] - a[0])]
                ordered = corners if normal[axis] * sign > 0 else list(reversed(corners))
                quads.append(tuple(index(key) for key in ordered))
    return points, quads


def prism(sides, radius, height, rows=1):
    ring = [(radius * math.cos(2 * math.pi * index / sides), radius * math.sin(2 * math.pi * index / sides)) for index in range(sides)]
    points = []
    for level in range(rows + 1):
        points += [(x, y, height * level / rows) for x, y in ring]
    faces = [tuple(range(rows * sides, (rows + 1) * sides)), tuple(reversed(range(sides)))]
    for level in range(rows):
        base = level * sides
        faces += [(base + index, base + (index + 1) % sides, base + sides + (index + 1) % sides, base + sides + index) for index in range(sides)]
    return split_faces(points, faces)


def band(top, bottom, radius, height):
    lower = [(radius * math.cos(2 * math.pi * index / bottom), radius * math.sin(2 * math.pi * index / bottom), 0.0) for index in range(bottom)]
    upper = [(0.8 * radius * math.cos(2 * math.pi * index / top), 0.8 * radius * math.sin(2 * math.pi * index / top), height) for index in range(top)]
    faces = [tuple(range(bottom, bottom + top)), tuple(reversed(range(bottom)))]
    faces += [(index, index + 1, bottom + (index + 1) % top, bottom + index) for index in range(top)]
    faces.append((bottom - 1, 0, bottom))
    return split_faces(lower + upper, faces)


def torus(major, minor, nu, nv, big=1.6, small=0.6):
    points = []
    for i in range(nu):
        for j in range(nv):
            a, b = 2 * math.pi * i / nu, 2 * math.pi * j / nv
            points.append(((big + small * math.cos(b)) * math.cos(a), (big + small * math.cos(b)) * math.sin(a), small * math.sin(b)))
    quads = []
    for i in range(nu):
        for j in range(nv):
            p = lambda x, y: (x % nu) * nv + (y % nv)
            quads.append((p(i, j), p(i + 1, j), p(i + 1, j + 1), p(i, j + 1)))
    return points, quads


def warp(points, amount, seed):
    generator = random.Random(seed)
    out = []
    for x, y, z in points:
        out.append((x + amount * math.sin(1.3 * y + 0.2) + generator.uniform(-amount, amount) * 0.3, y + amount * math.cos(1.1 * z) + generator.uniform(-amount, amount) * 0.3, z + amount * math.sin(0.9 * x + 0.5) + generator.uniform(-amount, amount) * 0.3))
    return out


def closed(points, quads, creases=None):
    grips = tuple(ControlGrip(round(x, 9), round(y, 9), round(z, 9)) for x, y, z in points)
    surface = MakeClosedCage(grips, tuple(tuple(q) for q in quads), Header=HEADER)
    if creases is None:
        return surface
    edges, verts = creases(surface)
    return replace(surface, Creases=CreaseData(tuple(sorted(edges)), tuple(sorted(verts))))


def sharp_box_edges(points):
    def pick(surface):
        topology = surface.Topology
        edges = set()
        verts = set()
        for link in topology.Links:
            pa = points[link.VertexIndex]
            pb = points[topology.Links[link.NextLink].VertexIndex]
            mins = [min(p[k] for p in points) for k in range(3)]
            maxs = [max(p[k] for p in points) for k in range(3)]
            def onbound(p):
                return sum(1 for k in range(3) if abs(p[k] - mins[k]) < 1e-9 or abs(p[k] - maxs[k]) < 1e-9)
            if onbound(pa) >= 2 and onbound(pb) >= 2:
                edges.add(link.EdgeIndex)
            for p, v in ((pa, link.VertexIndex),):
                if onbound(p) == 3:
                    verts.add(v)
        return edges, verts
    return pick
