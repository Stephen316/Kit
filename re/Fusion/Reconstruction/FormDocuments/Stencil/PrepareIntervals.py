import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

SOURCE = 're/Fusion/LocalOracle/FormDocuments/Sourceless/'
TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/Intervals'


def edge_ends(surface, edge):
    links = surface.Topology.Links
    link = links[edge.OriginLink]
    return link.VertexIndex, links[link.NextLink].VertexIndex


def vertex_points(surface):
    places = {}
    for grip, owner in enumerate(surface.Mapping.Owners):
        if owner.IsPrimary:
            value = surface.Grips[grip]
            places[owner.VertexIndex] = (value.CoordX / value.Weight, value.CoordY / value.Weight, value.CoordZ / value.Weight)
    return places


def classify(surface):
    places = vertex_points(surface)
    xs = sorted({round(point[0], 9) for point in places.values()})
    ys = sorted({round(point[1], 9) for point in places.values()})
    rows = []
    for edge in surface.Topology.Edges:
        first, second = (places[index] for index in edge_ends(surface, edge))
        if abs(first[1] - second[1]) < 1e-9:
            rows.append(('u', xs.index(round(min(first[0], second[0]), 9)), ys.index(round(first[1], 9))))
        else:
            rows.append(('v', ys.index(round(min(first[1], second[1]), 9)), xs.index(round(first[0], 9))))
    return rows


def with_intervals(surface, choose):
    edges = tuple(replace(edge, KnotInterval=choose(index, edge)) for index, edge in enumerate(surface.Topology.Edges))
    return replace(surface, Topology=replace(surface.Topology, Edges=edges))


def plane_variants(surface):
    kinds = classify(surface)
    single = next(index for index, kind in enumerate(kinds) if kind[:2] == ('u', 1) and kind[2] == 2)
    return {
        'Base': lambda index, edge: 1.0,
        'Uniform2': lambda index, edge: 2.0,
        'Half': lambda index, edge: 0.5,
        'Column1': lambda index, edge: 2.0 if kinds[index][:2] == ('u', 1) else 1.0,
        'Column0': lambda index, edge: 2.0 if kinds[index][:2] == ('u', 0) else 1.0,
        'Row2': lambda index, edge: 3.0 if kinds[index][:2] == ('v', 2) else 1.0,
        'ColumnRow': lambda index, edge: 2.0 if kinds[index][:2] == ('u', 1) else 0.5 if kinds[index][:2] == ('v', 2) else 1.0,
        'Single': lambda index, edge: 2.0 if index == single else 1.0,
    }


def box_variants(surface):
    return {
        'Base': lambda index, edge: 1.0,
        'Uniform2': lambda index, edge: 2.0,
        'Single': lambda index, edge: 2.0 if index == 0 else 1.0,
    }


def main():
    report = {'scope': 'Non-unit TSM knot intervals on a plane grid and a box cage: uniform scaling, consistent column and row intervals, a boundary column and a single inconsistent edge, imported into Fusion and converted', 'python': sys.version.split()[0], 'cages': []}
    for name, maker in (('Plane4x4', plane_variants), ('Box', box_variants)):
        source = SOURCE + name + '.tsm'
        surface = ReadTspline((ROOT / source).read_bytes())
        folder = TARGET / name
        folder.mkdir(parents=True, exist_ok=True)
        row = {'cage': name, 'source': {'file': source, 'sha256': hashlib.sha256((ROOT / source).read_bytes()).hexdigest()}, 'variants': []}
        for label, choose in maker(surface).items():
            changed = with_intervals(surface, choose)
            text = EmitTspline(changed)
            if ReadTspline(text) != changed:
                raise RuntimeError('TSM text does not read back')
            path = folder / (label + '.tsm')
            if not path.exists() or path.read_bytes() != text:
                path.write_bytes(text)
            counts = {}
            for edge in changed.Topology.Edges:
                counts[str(edge.KnotInterval)] = counts.get(str(edge.KnotInterval), 0) + 1
            row['variants'].append({'variant': label, 'tsm_file': str(path.relative_to(ROOT)), 'tsm_sha256': hashlib.sha256(text).hexdigest(), 'intervals': counts})
        report['cages'].append(row)
    (TARGET / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1)[:1500])


if __name__ == '__main__':
    main()
