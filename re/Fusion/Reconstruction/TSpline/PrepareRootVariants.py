import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.MakeClosedCage import MakeClosedCage
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip


def coordinates(grip):
    return grip.CoordX, grip.CoordY, grip.CoordZ


def make_surface(reorder_vertices=False, reorder_faces=False):
    points = ((0, 0, 0), (1.7, 0, 0), (1.7, 2.3, 0), (0, 2.3, 0),
              (0, 0, 3.1), (1.7, 0, 3.1), (1.7, 2.3, 3.1), (0, 2.3, 3.1))
    faces = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))
    if reorder_faces:
        plane_order = ((2, 0), (1, 0), (0, 0), (2, 3.1), (1, 2.3), (0, 1.7))
        faces = tuple(next(face for face in faces
                           if all(points[index][axis] == value for index in face))
                      for axis, value in plane_order)
    if reorder_vertices:
        ordered = tuple(sorted(points, key=lambda point: (point[2], point[0], point[1])))
        lookup = {point: index for index, point in enumerate(ordered)}
        faces = tuple(tuple(lookup[points[index]] for index in face) for face in faces)
        points = ordered
    return MakeClosedCage(tuple(ControlGrip(*point) for point in points), faces)


def vertex_roots(surface):
    topology = surface.Topology
    vertices = []
    ymax = max(grip.CoordY for grip in surface.Grips)
    for vertex_index, vertex in enumerate(topology.Vertices):
        point = coordinates(surface.Grips[vertex_index])
        axis = 1 if point[1] < ymax else 2
        choices = []
        for link_index, link in enumerate(topology.Links):
            if link.VertexIndex != vertex_index:
                continue
            target = topology.Links[link.NextLink].VertexIndex
            delta = tuple(right - left for left, right in
                          zip(point, coordinates(surface.Grips[target])))
            if delta[axis] and all(not delta[other] for other in range(3) if other != axis):
                choices.append(link_index)
        if len(choices) != 1:
            raise ValueError('Expected a unique axis-aligned root candidate')
        vertices.append(replace(vertex, OriginLink=choices[0]))
    return replace(surface, Topology=replace(topology, Vertices=tuple(vertices)))


def face_roots(surface):
    topology = surface.Topology
    bounds = tuple((min(coordinates(point)[axis] for point in surface.Grips),
                    max(coordinates(point)[axis] for point in surface.Grips))
                   for axis in range(3))
    faces = []
    for face_index, face in enumerate(topology.Faces):
        candidates = [(index, coordinates(surface.Grips[link.VertexIndex]))
                      for index, link in enumerate(topology.Links)
                      if link.FaceIndex == face_index]
        plane = next((axis, side) for axis in range(3) for side in (0, 1)
                     if all(point[axis] == bounds[axis][side] for _, point in candidates))
        preferences = {(2, 0): (-1, 1, 1), (1, 0): (1, 1, 1),
                       (0, 0): (1, 1, 1), (2, 1): (1, 1, 1),
                       (1, 1): (1, 1, -1), (0, 1): (1, 1, -1)}[plane]
        root, _ = min(candidates, key=lambda item:
                      tuple(value * sign for value, sign in zip(item[1], preferences)))
        faces.append(replace(face, OriginLink=root))
    return replace(surface, Topology=replace(topology, Faces=tuple(faces)))


def main():
    target = ROOT / 're/Fusion/LocalOracle/TSplineCodec/RootVariants'
    target.mkdir(parents=True, exist_ok=True)
    base = make_surface()
    variants = {
        'CounterOnly': replace(base, Header=replace(base.Header, VersionCount=254)),
        'VertexRoots': vertex_roots(base),
        'VertexOrder': make_surface(reorder_vertices=True),
        'RootsAndVertexOrder': vertex_roots(make_surface(reorder_vertices=True)),
        'FaceRoots': face_roots(base),
        'RootsAndFaceOrder': face_roots(vertex_roots(make_surface(reorder_faces=True))),
        'AllSemanticOrders': face_roots(vertex_roots(make_surface(True, True))),
    }
    cases = []
    for name, surface in variants.items():
        data = EmitTspline(surface)
        output = target / (name + '.tsm')
        output.write_bytes(data)
        cases.append({'name': name, 'output_file': str(output.relative_to(ROOT)),
                      'output_sha256': hashlib.sha256(data).hexdigest(),
                      'control_points_cm': [list(coordinates(point)) for point in surface.Grips],
                      'vertex_origins': [item.OriginLink for item in surface.Topology.Vertices],
                      'face_origins': [item.OriginLink for item in surface.Topology.Faces]})
    report = {'scope': 'Source-free semantic root and allocation experiments; no source TSM reads',
              'purpose': 'Isolate the native primitive versus authored cage fitting difference without changing acceptance tolerances',
              'geometry_mm': {'Width': 17, 'Depth': 23, 'Height': 31},
              'baseline': 're/Fusion/LocalOracle/TSplineCodec/AuthoredClosedCage.tsm',
              'cases': cases}
    (target / 'Preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'cases': len(cases), 'output': str(target / 'Preparation.json')}))


if __name__ == '__main__':
    main()
