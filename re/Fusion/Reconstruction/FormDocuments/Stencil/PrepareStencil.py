import hashlib
import json
import math
import random
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.MakeClosedCage import MakeClosedCage
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil'
WORK = TARGET / 'tmp'
NATIVE = {
    'Box': 're/Fusion/LocalOracle/TSpline/Box.f3d',
    'SymmetricBox': 're/Fusion/LocalOracle/TSpline/SymmetricBox.f3d',
    'CreasedPlane': 're/Fusion/LocalOracle/TSplineCodec/vendor_PlaneCreasedControl.f3d',
    'CreasedBox': 're/Fusion/LocalOracle/TSplineCodec/vendor_BoxCreasedControl.f3d',
}
FITTED = ('Box', 'CreasedPlane', 'CreasedBox', 'Valence5', 'Valence6', 'Box3', 'Valence8', 'Valence7', 'Mixed56', 'Mixed78')
CHECKED = ('SymmetricBox', 'Valence5Warped')
SECOND = ('Valence5', 'Valence6', 'Valence5Warped', 'Valence8', 'Valence7', 'Mixed56', 'Mixed78')
STEP = {'CreasedPlane': 0.125, 'Box3': 0.125, 'Valence8': 0.125, 'Valence7': 0.125, 'Mixed56': 0.125, 'Mixed78': 0.125}
SPREAD = {'CreasedPlane': 0.04}
SCALE = {'CreasedBox': 0.5}
LIMITS = {'CreasedPlaneLimits': ('CreasedPlane', ((3, 1.0), (8, 1.0), (10, 1.0), (31, 1.0))), 'CreasedBoxLimits': ('CreasedBox', ((7, 2.5),))}
WEIGHTED = {'BoxWeighted': ('Box', {0: 2.0}), 'BoxWeightUniform': ('Box', {index: 2.0 for index in range(26)})}


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


def prism(sides, radius, height, warp):
    ring = [(radius * math.cos(2 * math.pi * index / sides), radius * math.sin(2 * math.pi * index / sides)) for index in range(sides)]
    points = [(x, y, 0.0) for x, y in ring] + [(x, y, height) for x, y in ring]
    faces = [tuple(range(sides, 2 * sides)), tuple(reversed(range(sides)))]
    faces += [(index, (index + 1) % sides, sides + (index + 1) % sides, sides + index) for index in range(sides)]
    points, quads = split_faces(points, faces)
    return [warp(*point) for point in points], quads


def band(top, bottom, radius, height):
    lower = [(radius * math.cos(2 * math.pi * index / bottom), radius * math.sin(2 * math.pi * index / bottom), 0.0) for index in range(bottom)]
    upper = [(0.8 * radius * math.cos(2 * math.pi * index / top), 0.8 * radius * math.sin(2 * math.pi * index / top), height) for index in range(top)]
    faces = [tuple(range(bottom, bottom + top)), tuple(reversed(range(bottom)))]
    faces += [(index, index + 1, bottom + (index + 1) % top, bottom + index) for index in range(top)]
    faces.append((bottom - 1, 0, bottom))
    return split_faces(lower + upper, faces)


def cube(count, size):
    lookup = {}
    points = []
    quads = []

    def index(key):
        if key not in lookup:
            lookup[key] = len(points)
            points.append(tuple(size * value / count for value in key))
        return lookup[key]

    for axis in range(3):
        for side in (0, count):
            other = [item for item in range(3) if item != axis]
            for first in range(count):
                for second in range(count):
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


def closed(points, quads, header):
    grips = tuple(ControlGrip(round(x, 12), round(y, 12), round(z, 12)) for x, y, z in points)
    return MakeClosedCage(grips, tuple(quads), Header=header)


def shifted(surface, moves):
    grips = list(surface.Grips)
    for index, (dx, dy, dz) in moves.items():
        grip = grips[index]
        grips[index] = replace(grip, CoordX=grip.CoordX + dx, CoordY=grip.CoordY + dy, CoordZ=grip.CoordZ + dz)
    return replace(surface, Grips=tuple(grips))


def variants(name, surface):
    count = len(surface.Grips)
    rows = [('Base', {})]
    generator = random.Random(name)
    step = STEP.get(name, 1.0)
    spread = SPREAD.get(name, 0.3)
    if name in LIMITS:
        return rows + [('X%dLarge' % index, {index: (step, 0.0, 0.0)}) for index, step in LIMITS[name][1]]
    if name == 'BoxWeightUniform':
        return rows
    if name in WEIGHTED:
        return rows + [('X0', {0: (1.0, 0.0, 0.0)}), ('X3', {3: (1.0, 0.0, 0.0)}), ('Pair0_3', {0: (1.0, 0.0, 0.0), 3: (1.0, 0.0, 0.0)}), ('Scale0', {0: (2.5, 0.0, 0.0)}), ('RandomA', {index: tuple(round(generator.uniform(-spread, spread), 6) for _ in range(3)) for index in range(count)})]
    if name in FITTED:
        rows += [('X%d' % index, {index: (step, 0.0, 0.0)}) for index in range(count)]
        for index in generator.sample(range(count), 3):
            rows.append(('Y%d' % index, {index: (0.0, step, 0.0)}))
            rows.append(('Z%d' % index, {index: (0.0, 0.0, step)}))
        pick = generator.randrange(count)
        rows.append(('Scale%d' % pick, {pick: (SCALE.get(name, 2.5) * step, 0.0, 0.0)}))
        pair = generator.sample(range(count), 2)
        rows.append(('Pair%d_%d' % tuple(pair), {pair[0]: (step, 0.0, 0.0), pair[1]: (step, 0.0, 0.0)}))
    for label in ('RandomA', 'RandomB'):
        rows.append((label, {index: tuple(round(generator.uniform(-spread, spread), 6) for _ in range(3)) for index in range(count)}))
    return rows


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    cages = {}
    sources = {}
    for name, relative in NATIVE.items():
        data = (ROOT / relative).read_bytes()
        cages[name] = ReadDocument(data).Forms[0].Surface
        sources[name] = {'file': relative, 'sha256': hashlib.sha256(data).hexdigest()}
    header = cages['Box'].Header
    points, quads = cube(3, 2.4)
    cages['Box3'] = closed(points, quads, header)
    for sides in (5, 6, 8):
        points, quads = prism(sides, 1.1, 1.3, lambda x, y, z: (x, y, z))
        cages['Valence%d' % sides] = closed(points, quads, header)
    points, quads = prism(7, 1.1, 1.3, lambda x, y, z: (x, y, z))
    cages['Valence7'] = closed(points, quads, header)
    for top, bottom in ((5, 6), (7, 8)):
        points, quads = band(top, bottom, 1.1, 1.3)
        cages['Mixed%d%d' % (top, bottom)] = closed(points, quads, header)
    points, quads = prism(5, 1.1, 1.3, lambda x, y, z: (x + 0.07 * math.sin(2.1 * y), y + 0.05 * math.cos(1.7 * z), z + 0.09 * math.sin(1.3 * x + 0.4)))
    cages['Valence5Warped'] = closed(points, quads, header)
    for name, (source, _) in LIMITS.items():
        cages[name] = cages[source]
        sources[name] = sources[source]
    for name, (source, weights) in WEIGHTED.items():
        grips = tuple(replace(grip, Weight=weights.get(index, grip.Weight)) for index, grip in enumerate(cages[source].Grips))
        cages[name] = replace(cages[source], Grips=grips)
    report = {'scope': 'Single-grip, scaled, paired and random grip displacements of native and Kit-authored cages for the T-spline conversion linearity probe, large single-grip moves of the creased cages for the conversion limits, and grip moves of box cages with non-unit grip weights', 'python': sys.version.split()[0], 'fitted': list(FITTED), 'checked': list(CHECKED), 'limits': list(LIMITS), 'weighted': {'BoxWeighted': 'box primitive with grip 0 at weight 2', 'BoxWeightUniform': 'box primitive with all 26 grips at weight 2'}, 'cages': []}
    for name in sorted(FITTED + CHECKED, key=lambda item: item in SECOND) + list(LIMITS) + list(WEIGHTED):
        surface = cages[name]
        folder = WORK / name
        folder.mkdir(parents=True, exist_ok=True)
        base_text = EmitTspline(surface)
        if ReadTspline(base_text) != surface:
            raise RuntimeError('TSM text does not read back')
        if name not in NATIVE and name not in LIMITS and (not (TARGET / (name + '.tsm')).exists() or (TARGET / (name + '.tsm')).read_bytes() != base_text):
            (TARGET / (name + '.tsm')).write_bytes(base_text)
        row = {'cage': name, 'source': sources.get(name, {'file': str((TARGET / (name + '.tsm')).relative_to(ROOT)), 'sha256': hashlib.sha256(base_text).hexdigest()}), 'grips': len(surface.Grips), 'faces': len(surface.Topology.Faces), 'vertices': len(surface.Topology.Vertices), 'variants': []}
        for label, moves in variants(name, surface):
            text = EmitTspline(shifted(surface, moves))
            path = folder / (label + '.tsm')
            if not path.exists() or path.read_bytes() != text:
                path.write_bytes(text)
            row['variants'].append({'variant': label, 'tsm_file': str(path.relative_to(ROOT)), 'tsm_sha256': hashlib.sha256(text).hexdigest(), 'moves': {str(index): list(move) for index, move in moves.items()}})
        row['batch'] = 2 if name in SECOND else 1
        report['cages'].append(row)
        print(name, len(row['variants']), 'variants', len(surface.Grips), 'grips')
    (TARGET / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
