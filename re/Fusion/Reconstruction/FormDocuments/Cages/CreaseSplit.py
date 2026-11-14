"""Research: where Fusion splits a converted crease edge.

For each Fusion-saved creased plane or creased box archive, evaluates the
two faces along each edge that carries a crease and finds where the sign
of the dihedral function changes. The function is the triple product of
the two face normals with the edge tangent. The script reports each sign
change root next to the edge splits that Fusion stored.
"""

import json
import math
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from ReadConverted import ReadConverted

TARGET = BASE / 'CreaseSplit.json'
SAMPLES = 400


def full_knots(values, counts, degree):
    knots = []
    for value, count in zip(values, counts):
        knots += [value] * count
    return [knots[0]] + knots + [knots[-1]] if counts[0] == degree else knots


def basis(knots, degree, x):
    span = degree
    while span < len(knots) - degree - 2 and x >= knots[span + 1]:
        span += 1
    left, right = [0.0] * (degree + 1), [0.0] * (degree + 1)
    table = [[0.0] * (degree + 1) for _ in range(degree + 1)]
    table[0][0] = 1.0
    for j in range(1, degree + 1):
        left[j] = x - knots[span + 1 - j]
        right[j] = knots[span + j] - x
        saved = 0.0
        for r in range(j):
            table[j][r] = right[r + 1] + left[j - r]
            temp = table[r][j - 1] / table[j][r]
            table[r][j] = saved + right[r + 1] * temp
            saved = left[j - r] * temp
        table[j][j] = saved
    values = [table[j][degree] for j in range(degree + 1)]
    derivs = [0.0] * (degree + 1)
    for r in range(degree + 1):
        total = 0.0
        if r >= 1:
            total += table[r - 1][degree - 1] / table[degree][r - 1]
        if r <= degree - 1:
            total -= table[r][degree - 1] / table[degree][r]
        derivs[r] = degree * total
    return span - degree, values, derivs


def curve_eval(curve, t):
    knots = full_knots(curve.Knots, curve.Multiplicity, curve.Degree)
    start, values, derivs = basis(knots, curve.Degree, t)
    poles = curve.Poles[start:start + curve.Degree + 1]
    point = [sum(v * p[k] for v, p in zip(values, poles)) for k in range(curve.Dimension)]
    tangent = [sum(d * p[k] for d, p in zip(derivs, poles)) for k in range(curve.Dimension)]
    return point, tangent


def surface_eval(cache, u, v):
    ku = full_knots([k.Value for k in cache.KnotsU], [k.Count for k in cache.KnotsU], cache.DegreeU)
    kv = full_knots([k.Value for k in cache.KnotsV], [k.Count for k in cache.KnotsV], cache.DegreeV)
    width = len(ku) - cache.DegreeU - 1
    su, bu, du = basis(ku, cache.DegreeU, u)
    sv, bv, dv = basis(kv, cache.DegreeV, v)
    point, along_u, along_v = [0.0] * 3, [0.0] * 3, [0.0] * 3
    for j in range(cache.DegreeV + 1):
        for i in range(cache.DegreeU + 1):
            pole = cache.Points[(sv + j) * width + su + i]
            for k in range(3):
                point[k] += bu[i] * bv[j] * pole[k]
                along_u[k] += du[i] * bv[j] * pole[k]
                along_v[k] += bu[i] * dv[j] * pole[k]
    return point, along_u, along_v


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def unit(a):
    size = math.sqrt(sum(x * x for x in a))
    return [x / size for x in a]


def face_normal(face, use, curve_point, t):
    best = None
    for sign in (1.0, -1.0):
        param = sign * t
        trace = use.Pcurve
        if not trace.Knots[0] - 1e-12 <= param <= trace.Knots[-1] + 1e-12:
            continue
        (u, v), _ = curve_eval(trace, min(max(param, trace.Knots[0]), trace.Knots[-1]))
        point, along_u, along_v = surface_eval(face.Surface.Cache, u, v)
        miss = max(abs(a - b) for a, b in zip(point, curve_point))
        if best is None or miss < best[0]:
            best = (miss, unit(cross(along_u, along_v)))
    return best


def dihedral(curve, pair, t):
    point, tangent = curve_eval(curve, t)
    (miss_a, normal_a), (miss_b, normal_b) = (face_normal(face, use, point, t) for face, use in pair)
    return sum(a * b for a, b in zip(cross(normal_a, normal_b), unit(tangent))), max(miss_a, miss_b), math.degrees(math.asin(min(1.0, math.sqrt(sum(x * x for x in cross(normal_a, normal_b))))))


def roots(curve, pair, low, high):
    found = []
    previous = dihedral(curve, pair, low)[0]
    for index in range(1, SAMPLES + 1):
        t = low + (high - low) * index / SAMPLES
        value = dihedral(curve, pair, t)[0]
        if previous * value < 0:
            a, b = t - (high - low) / SAMPLES, t
            for _ in range(200):
                middle = (a + b) / 2
                if dihedral(curve, pair, a)[0] * dihedral(curve, pair, middle)[0] <= 0:
                    b = middle
                else:
                    a = middle
            found.append((a + b) / 2)
        previous = value
    return found


def study(relative):
    model = ReadDocument((ROOT / relative).read_bytes())
    body = ReadConverted(model)
    carriers = {}
    for index, edge in enumerate(body.Edges):
        carriers.setdefault((edge.Curve.Knots, tuple(map(tuple, edge.Curve.Poles))), []).append(index)
    rows = []
    for edges in carriers.values():
        pair = [(face, use) for face in body.Faces for use in face.Uses if use.EdgeIndex in edges]
        if len({id(face) for face, _ in pair}) != 2 or len(pair) != 2 * len(edges):
            continue
        sides = []
        for face in {id(face): face for face, _ in pair}.values():
            sides.append((face, next(use for f, use in pair if f is face)))
        curve = body.Edges[edges[0]].Curve
        low, high = curve.Knots[0], curve.Knots[-1]
        samples = [dihedral(curve, sides, low + (high - low) * index / 40) for index in range(41)]
        rows.append({'edges': edges, 'convexity': [body.Edges[index].Convexity for index in edges], 'bounds': [body.Edges[index].Bounds for index in edges], 'range': [low, high], 'max_angle_deg': max(item[2] for item in samples), 'min_angle_deg': min(item[2] for item in samples), 'max_trace_miss_cm': max(item[1] for item in samples), 'sign_change_roots': roots(curve, sides, low, high)})
    return {'file': relative, 'faces': len(body.Faces), 'edges': len(body.Edges), 'vertices': len(body.PointsCm), 'creases': [row for row in rows if row['max_angle_deg'] > 1e-6 or any(value != 'tangent' for value in row['convexity'])]}


def main():
    files = [str(path.relative_to(ROOT)) for pattern in sys.argv[1:] for path in sorted(ROOT.glob(pattern))]
    report = {'scope': 'Sign changes of the dihedral triple product along shared edge carriers of converted Form bodies, against the edge splits Fusion stored', 'python': sys.version.split()[0], 'archives': [study(relative) for relative in files]}
    TARGET.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1)[:6000])


if __name__ == '__main__':
    main()
