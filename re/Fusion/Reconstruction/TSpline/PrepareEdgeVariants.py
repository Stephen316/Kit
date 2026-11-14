import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from PrepareRootVariants import coordinates, face_roots, make_surface, vertex_roots


def native_rank(point):
    return point[2], point[0], point[1]


def directed_edges(surface, rank):
    topology = surface.Topology
    edges = []
    for edge_index, edge in enumerate(topology.Edges):
        choices = []
        for link_index, link in enumerate(topology.Links):
            if link.EdgeIndex != edge_index:
                continue
            start = link.VertexIndex
            end = topology.Links[link.NextLink].VertexIndex
            if rank(surface, start) < rank(surface, end):
                choices.append(link_index)
        if len(choices) != 1:
            raise ValueError('Expected one oriented half-edge per edge')
        edges.append(replace(edge, OriginLink=choices[0]))
    return replace(surface, Topology=replace(topology, Edges=tuple(edges)))


def by_index(surface, vertex):
    return vertex


def by_native_order(surface, vertex):
    return native_rank(coordinates(surface.Grips[vertex]))


def main():
    target = ROOT / 're/Fusion/LocalOracle/TSplineCodec/EdgeVariants'
    target.mkdir(parents=True, exist_ok=True)
    base = make_surface()
    semantic = face_roots(vertex_roots(make_surface(True, True)))
    variants = {
        'EdgeOnly': directed_edges(base, by_native_order),
        'BaseEdgeAscending': directed_edges(base, by_index),
        'AllSemanticEdges': directed_edges(semantic, by_index),
        'FaceRootsEdges': directed_edges(face_roots(base), by_native_order),
        'FaceRootsAscending': directed_edges(face_roots(base), by_index),
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
                      'face_origins': [item.OriginLink for item in surface.Topology.Faces],
                      'edge_origins': [item.OriginLink for item in surface.Topology.Edges]})
    report = {'scope': 'Source-free edge-origin experiments; no source TSM reads',
              'purpose': 'Separate TSM edge-origin, face-root and vertex-root effects on the native solved surface',
              'geometry_mm': {'Width': 17, 'Depth': 23, 'Height': 31},
              'baseline': 're/Fusion/LocalOracle/TSplineCodec/AuthoredClosedCage.tsm',
              'cases': cases}
    (target / 'Preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'cases': len(cases), 'output': str(target / 'Preparation.json')}))


if __name__ == '__main__':
    main()
