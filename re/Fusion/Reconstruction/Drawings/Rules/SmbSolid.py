"""Read the solid body of a Fusion design's SMB stream into an interchange BrepModel in stored order.

Kit's view edge rules number edges by walking the body's shell faces, each face's loops and each loop's coedges in
the order the design stores them (see ViewEdgeNotes.md). This reader keeps that order: shell faces follow the
shell's face chain, loops the face's loop chain and coedges each loop's chain from its first coedge.

It covers what the control and Wheel designs hold: planes, cylinders and cones, straight lines and whole circles.
Anything else raises. ACIS lengths are centimetres; the model is written in millimetres.

Usage: python3.14 -I SmbSolid.py <design.f3d>  prints a face and edge summary.
"""
import io
import math
import struct
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[4] / 'src'))

from interchange.brep.curves.BrepCurves import CircleCurve, LineCurve  # noqa: E402
from interchange.brep.surfaces.BrepSurfaces import ConeSurface, CylinderSurface, PlaneSurface  # noqa: E402
from interchange.brep.topology.BrepModel import BrepModel  # noqa: E402
from interchange.brep.topology.BrepTopology import (  # noqa: E402
    BrepBody, BrepCoedge, BrepEdge, BrepFace, BrepFaceUse, BrepLoop, BrepRegion, BrepShell, BrepShellUse, BrepVertex,
)
from interchange.geometry.models.VectorSpace import SpaceVector  # noqa: E402

MM = 10.0


@dataclass
class Rec:
    Name: str
    Tokens: tuple


class Cursor:
    def __init__(self, data, wide):
        self.data, self.at, self.wide = data, 0, wide

    def take(self, count):
        value = self.data[self.at:self.at + count]
        self.at += count
        return value

    def token(self):
        tag = self.take(1)[0]
        size = 8 if self.wide else 4
        if tag in (4, 12, 21, 23):
            value = struct.unpack('<q' if self.wide else '<i', self.take(size))[0]
        elif tag == 6:
            value = struct.unpack('<d', self.take(8))[0]
        elif tag in (7, 13, 14):
            value = self.take(self.take(1)[0]).decode('utf-8', 'replace')
        elif tag == 8:
            value = self.take(struct.unpack('<H', self.take(2))[0]).decode('utf-8', 'replace')
        elif tag == 18:
            value = self.take(struct.unpack('<q' if self.wide else '<i', self.take(size))[0])
        elif tag in (19, 20):
            value = struct.unpack('<3d', self.take(24))
        elif tag in (10, 11, 15, 16, 17):
            value = None
        else:
            raise ValueError(f'SAB tag {tag} at {self.at}')
        return tag, value


def records(data):
    wide = data[:15] == b'ASM BinaryFile8'
    cursor = Cursor(data, wide)
    cursor.take(15)
    cursor.take(32 if wide else 16)
    for _ in range(6):
        cursor.token()
    found = []
    while True:
        parts = []
        while True:
            tag, value = cursor.token()
            parts.append(value)
            if tag == 13:
                break
        name = '-'.join(parts)
        if name in ('Begin-of-ASM-History-Data', 'End-of-ASM-data'):
            return found
        tokens = []
        while True:
            token = cursor.token()
            if token[0] == 17:
                break
            tokens.append(token)
        found.append(Rec(name, tuple(tokens)))


def smb_streams(design_bytes):
    archive = zipfile.ZipFile(io.BytesIO(design_bytes))
    return [archive.read(name) for name in archive.namelist() if name.endswith('.smb')]


def chain(recs, first, link):
    out, at = [], first
    while at >= 0:
        out.append(at)
        at = recs[at].Tokens[link][1]
        if at == first:
            break
    return out


def body_faces(recs, body):
    lump = recs[body].Tokens[3][1]
    shell = recs[lump].Tokens[4][1]
    return chain(recs, recs[shell].Tokens[5][1], 3)


def solid_body(recs):
    bodies = [index for index, rec in enumerate(recs) if rec.Name == 'body' and rec.Tokens[3][1] >= 0]
    return max(bodies, key=lambda body: len(body_faces(recs, body)))


def vec(values, scale=1.0):
    return SpaceVector(x=values[0] * scale, y=values[1] * scale, z=values[2] * scale)


def unit(values):
    size = math.sqrt(sum(v * v for v in values))
    return tuple(v / size for v in values)


def point_of(recs, vertex):
    return tuple(v * MM for v in recs[recs[vertex].Tokens[5][1]].Tokens[3][1])


def surface_of(recs, index, key):
    rec = recs[index]
    values = [v for tag, v in rec.Tokens if tag in (6, 19, 20)]
    if rec.Name.startswith('plane-surface'):
        return PlaneSurface(id=key, origin=vec(values[0], MM), normal=vec(unit(values[1])), reference_direction=vec(unit(values[2])))
    if rec.Name.startswith('cone-surface'):
        center, normal, major, ratio, sine, cosine = values[0], values[1], values[2], values[3], values[4], values[5]
        if abs(ratio - 1.0) > 1e-12:
            raise ValueError('elliptic cone')
        radius = math.sqrt(sum(v * v for v in major)) * MM
        if abs(sine) < 1e-12:
            return CylinderSurface(id=key, origin=vec(center, MM), axis=vec(unit(normal)), reference_direction=vec(unit(major)), radius=radius)
        return ConeSurface(id=key, origin=vec(center, MM), axis=vec(unit(normal)), reference_direction=vec(unit(major)), radius=radius, half_angle=math.atan2(abs(sine), abs(cosine)))
    raise ValueError('surface ' + rec.Name)


def angle_in(frame, offset):
    major, minor = frame
    return math.atan2(sum(a * b for a, b in zip(offset, minor)), sum(a * b for a, b in zip(offset, major)))


def curve_of(recs, edge, key):
    rec = recs[edge]
    start_vertex, end_vertex = rec.Tokens[3][1], rec.Tokens[5][1]
    start, end = point_of(recs, start_vertex), point_of(recs, end_vertex)
    curve = recs[rec.Tokens[8][1]]
    values = [v for tag, v in curve.Tokens if tag in (6, 19, 20)]
    if curve.Name.startswith('straight-curve'):
        direction = unit(tuple(b - a for a, b in zip(start, end)))
        length = math.dist(start, end)
        return LineCurve(id=key, origin=vec(start), direction=vec(direction)), 0.0, length
    if curve.Name.startswith('ellipse-curve'):
        center, normal, major, ratio = values[0], unit(values[1]), values[2], values[3]
        if abs(ratio - 1.0) > 1e-12 or start_vertex != end_vertex:
            raise ValueError('only whole circles')
        radius = math.sqrt(sum(v * v for v in major)) * MM
        major = unit(major)
        minor = (normal[1] * major[2] - normal[2] * major[1], normal[2] * major[0] - normal[0] * major[2], normal[0] * major[1] - normal[1] * major[0])
        opening = angle_in((major, minor), tuple(a - b * MM for a, b in zip(start, center)))
        return CircleCurve(id=key, center=vec(center, MM), axis=vec(normal), reference_direction=vec(major), radius=radius), opening, opening + 2 * math.pi
    raise ValueError('curve ' + curve.Name)


def to_model(recs, body):
    faces, loops, coedges, edges, curves, surfaces, vertices, face_uses = [], [], [], {}, [], [], {}, []
    for face_index, face in enumerate(body_faces(recs, body)):
        surfaces.append(surface_of(recs, recs[face].Tokens[7][1], f's{face_index}'))
        loop_ids = []
        for loop in chain(recs, recs[face].Tokens[4][1], 3):
            coedge_ids = []
            for coedge in chain(recs, recs[loop].Tokens[4][1], 3):
                edge = recs[coedge].Tokens[6][1]
                if edge not in edges:
                    key = f'e{edge}'
                    curve, low, high = curve_of(recs, edge, f'c{edge}')
                    curves.append(curve)
                    for vertex in (recs[edge].Tokens[3][1], recs[edge].Tokens[5][1]):
                        vertices.setdefault(vertex, BrepVertex(id=f'v{vertex}', point=vec(point_of(recs, vertex))))
                    edges[edge] = BrepEdge(id=key, start_vertex_id=f'v{recs[edge].Tokens[3][1]}', end_vertex_id=f'v{recs[edge].Tokens[5][1]}', curve_id=f'c{edge}', start_parameter=low, end_parameter=high)
                coedges.append(BrepCoedge(id=f'k{coedge}', edge_id=f'e{edge}'))
                coedge_ids.append(f'k{coedge}')
            loops.append(BrepLoop(id=f'l{loop}', coedge_ids=tuple(coedge_ids)))
            loop_ids.append(f'l{loop}')
        faces.append(BrepFace(id=f'f{face_index}', surface_id=f's{face_index}', loop_ids=tuple(loop_ids)))
        face_uses.append(BrepFaceUse(id=f'u{face_index}', face_id=f'f{face_index}'))
    shell = BrepShell(id='shell', face_use_ids=tuple(use.id for use in face_uses), closed=True)
    return BrepModel(
        curves=tuple(curves), surfaces=tuple(surfaces), vertices=tuple(vertices.values()), edges=tuple(edges.values()),
        coedges=tuple(coedges), loops=tuple(loops), faces=tuple(faces), face_uses=tuple(face_uses), shells=(shell,),
        shell_uses=(BrepShellUse(id='shelluse', shell_id='shell'),), regions=(BrepRegion(id='region', shell_use_ids=('shelluse',)),),
        bodies=(BrepBody(id='body', region_ids=('region',)),),
    )


def design_solid(design_bytes):
    models = []
    for data in smb_streams(design_bytes):
        recs = records(data)
        if any(rec.Name == 'body' and rec.Tokens[3][1] >= 0 for rec in recs):
            models.append(to_model(recs, solid_body(recs)))
    if len(models) != 1:
        raise ValueError(f'{len(models)} solid streams')
    return models[0]


if __name__ == '__main__':
    model = design_solid(Path(sys.argv[1]).read_bytes())
    print(len(model.faces), 'faces', len(model.edges), 'edges', [type(s).__name__ for s in model.surfaces])
