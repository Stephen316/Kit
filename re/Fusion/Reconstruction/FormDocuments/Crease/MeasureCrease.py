"""Research: measure the dihedral angle along every converted Form edge.

Reads the Fusion-saved archives listed in a crease probe report, decodes the
converted body and, for every edge with two coedges, samples the angle
between the two face normals densely along the edge. The sign is the triple
product of the two normals with the edge tangent. Each row keeps Fusion's
stored convexity and split bounds next to the measured angles.

Usage: python3.14 -I MeasureCrease.py <round folder name> [...]
"""

import json
import math
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE.parent / 'Cages'))
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.SplineFrame import BasisLevel, BasisSlope, CurveFrame, FindSpan, KnotList
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from ReadConverted import ReadConverted

ORACLE = ROOT / 're/Fusion/LocalOracle/FormDocuments/Crease'
SAMPLES = 48


def surface_point(surface, u, v):
    ku, kv = KnotList(surface.KnotsU), KnotList(surface.KnotsV)
    width = len(ku) - surface.DegreeU - 1
    su, sv = FindSpan(ku, surface.DegreeU, u), FindSpan(kv, surface.DegreeV, v)
    bu, du = BasisLevel(ku, su, surface.DegreeU, u), BasisSlope(ku, su, surface.DegreeU, u)
    bv, dv = BasisLevel(kv, sv, surface.DegreeV, v), BasisSlope(kv, sv, surface.DegreeV, v)
    terms = []
    for j in range(surface.DegreeV + 1):
        for i in range(surface.DegreeU + 1):
            place = (sv - surface.DegreeV + j) * width + su - surface.DegreeU + i
            weight = surface.Weights[place] if surface.Weights else 1.0
            terms.append((bu[i] * bv[j], du[i] * bv[j], bu[i] * dv[j], weight, surface.Points[place]))
    mass = sum(a * w for a, _, _, w, _ in terms)
    mass_u = sum(b * w for _, b, _, w, _ in terms)
    mass_v = sum(c * w for _, _, c, w, _ in terms)
    point = [sum(a * w * p[k] for a, _, _, w, p in terms) / mass for k in range(3)]
    along_u = [(sum(b * w * p[k] for _, b, _, w, p in terms) - point[k] * mass_u) / mass for k in range(3)]
    along_v = [(sum(c * w * p[k] for _, _, c, w, p in terms) - point[k] * mass_v) / mass for k in range(3)]
    return point, along_u, along_v


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def norm(a):
    return math.sqrt(sum(x * x for x in a))


def unit(a):
    size = norm(a)
    return [x / size for x in a]


def side_frame(face, use, param):
    (u, v), _ = CurveFrame(use.Pcurve, param)
    point, along_u, along_v = surface_point(face.Surface.Cache, u, v)
    return point, unit(cross(along_u, along_v))


def sample(edge, sides, param):
    point, tangent = CurveFrame(edge.Curve, param)
    frames = [side_frame(face, use, param) for face, use in sides]
    across = cross(frames[0][1], frames[1][1])
    sine = norm(across)
    cosine = sum(a * b for a, b in zip(frames[0][1], frames[1][1]))
    turn = sum(a * b for a, b in zip(across, unit(tangent)))
    angle = math.degrees(math.atan2(sine, cosine))
    miss = max(norm([a - b for a, b in zip(point, frame[0])]) for frame in frames)
    return {'param': param, 'point': point, 'angle_deg': math.copysign(angle, turn) if angle > 0 else 0.0, 'miss_cm': miss}


def edge_breaks(edge):
    knots = edge.Curve.Knots
    lower, upper = edge.Bounds or (knots[0], knots[-1])
    return [lower, *(value for value in knots if lower < value < upper), upper]


def measure_edge(index, edge, sides):
    breaks = edge_breaks(edge)
    spans = []
    for begin, finish in zip(breaks, breaks[1:]):
        points = [sample(edge, sides, begin + (finish - begin) * step / SAMPLES) for step in range(SAMPLES + 1)]
        angles = [row['angle_deg'] for row in points]
        spans.append({'range': [begin, finish], 'max_abs_deg': max(abs(a) for a in angles), 'min_abs_deg': min(abs(a) for a in angles), 'min_signed_deg': min(angles), 'max_signed_deg': max(angles), 'mid_deg': points[SAMPLES // 2]['angle_deg'], 'start_deg': angles[0], 'end_deg': angles[-1], 'max_miss_cm': max(row['miss_cm'] for row in points), 'signs': sorted({a > 0 for a in angles if abs(a) > 1e-9})})
    start, _ = CurveFrame(edge.Curve, breaks[0])
    finish, _ = CurveFrame(edge.Curve, breaks[-1])
    middle, _ = CurveFrame(edge.Curve, (breaks[0] + breaks[-1]) / 2)
    return {'edge': index, 'convexity': edge.Convexity, 'bounds': edge.Bounds, 'curve_range': [edge.Curve.Knots[0], edge.Curve.Knots[-1]], 'start_cm': start, 'mid_cm': middle, 'end_cm': finish, 'max_abs_deg': max(span['max_abs_deg'] for span in spans), 'min_abs_deg': min(span['min_abs_deg'] for span in spans), 'min_signed_deg': min(span['min_signed_deg'] for span in spans), 'max_signed_deg': max(span['max_signed_deg'] for span in spans), 'spans': spans}


def measure_body(body):
    sides = {}
    for face in body.Faces:
        for use in face.Uses:
            sides.setdefault(use.EdgeIndex, []).append((face, use))
    rows = []
    for index, edge in enumerate(body.Edges):
        pair = sides.get(index, [])
        if len(pair) != 2:
            rows.append({'edge': index, 'convexity': edge.Convexity, 'coedges': len(pair)})
            continue
        pair.sort(key=lambda side: side[1].Reversed)
        row = measure_edge(index, edge, pair)
        row['coedge_senses'] = ['reversed' if use.Reversed else 'forward' for _, use in pair]
        rows.append(row)
    return rows


def main():
    for name in sys.argv[1:]:
        folder = ORACLE / name
        probe = json.loads((folder / 'Probe.json').read_text())
        preparation = json.loads((folder / 'Preparation.json').read_text())
        designs = {row['cage']: row['design'] for row in preparation['cages']}
        out = {'scope': 'Dihedral angle along every converted edge of the Fusion-saved crease probe archives of round ' + name, 'python': sys.version.split()[0], 'samples_per_span': SAMPLES, 'cages': []}
        for row in probe['cages']:
            entry = {'cage': row['cage'], 'design': designs[row['cage']], 'status': row['status']}
            if row['status'] == 'completed':
                body = ReadConverted(ReadDocument((ROOT / row['saved_file']).read_bytes()))
                entry['faces'] = len(body.Faces)
                entry['edges'] = measure_body(body)
            out['cages'].append(entry)
        (BASE / 'tmp' / (name + 'Angles.json')).write_text(json.dumps(out, indent=1) + '\n')
        print('wrote', name + 'Angles.json')


if __name__ == '__main__':
    main()
