import json
import sys
from fractions import Fraction
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
NAME = 'Box3'
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

STENCIL = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil/tmp'


def add(*terms):
    out = {}
    for scale, vec in terms:
        for k, v in vec.items():
            out[k] = out.get(k, 0) + scale * v
    return {k: v for k, v in out.items() if v != 0}


class Level:
    def __init__(self, faces, values):
        self.faces = faces
        self.values = values
        self.loops = {}
        self.edge_face = {}
        for fi, loop in enumerate(faces):
            for i, a in enumerate(loop):
                self.edge_face[(a, loop[(i + 1) % len(loop)])] = (fi, i)
        self.valence = {}
        for (a, b) in self.edge_face:
            self.valence[a] = self.valence.get(a, 0) + 1


def load_mesh():
    surface = ReadTspline((STENCIL / NAME / 'Base.tsm').read_bytes())
    links = surface.Topology.Links
    vert_grip = {}
    if surface.Mapping is not None:
        for grip, owner in enumerate(surface.Mapping.Owners):
            if owner.IsPrimary:
                vert_grip[owner.VertexIndex] = grip
    faces = []
    for face in surface.Topology.Faces:
        loop, link = [], face.OriginLink
        while True:
            loop.append(links[link].VertexIndex)
            link = links[link].NextLink
            if link == face.OriginLink:
                break
        faces.append(loop)
    count = len(surface.Topology.Vertices)
    values = {v: {vert_grip.get(v, v): Fraction(1)} for v in range(count)}
    return Level(faces, values)


def subdivide(level):
    faces, values = level.faces, level.values
    newv = {}
    fpt, ept, vpt = {}, {}, {}
    counter = [0]

    def fresh(val):
        key = counter[0]
        counter[0] += 1
        newv[key] = val
        return key

    for fi, loop in enumerate(faces):
        n = len(loop)
        fpt[fi] = fresh(add(*[(Fraction(1, n), values[v]) for v in loop]))
    edge_faces = {}
    for fi, loop in enumerate(faces):
        for i, a in enumerate(loop):
            b = loop[(i + 1) % len(loop)]
            edge_faces.setdefault(frozenset((a, b)), []).append(fi)
    for edge, fl in edge_faces.items():
        a, b = tuple(edge)
        ept[edge] = fresh(add((Fraction(1, 4), values[a]), (Fraction(1, 4), values[b]), (Fraction(1, 4), newv[fpt[fl[0]]]), (Fraction(1, 4), newv[fpt[fl[1]]])))
    vfaces, vedges = {}, {}
    for fi, loop in enumerate(faces):
        for v in loop:
            vfaces.setdefault(v, []).append(fi)
    for edge in edge_faces:
        for v in edge:
            vedges.setdefault(v, []).append(edge)
    for v in values:
        n = len(vedges[v])
        favg = add(*[(Fraction(1, len(vfaces[v])), newv[fpt[f]]) for f in vfaces[v]])
        eavg = add(*[(Fraction(1, 2 * n), values[w]) for e in vedges[v] for w in e])
        vpt[v] = fresh(add((Fraction(1, n), favg), (Fraction(2, n), eavg), (Fraction(n - 3, n), values[v])))
    out = []
    for fi, loop in enumerate(faces):
        n = len(loop)
        for i, v in enumerate(loop):
            nxt = loop[(i + 1) % n]
            prv = loop[(i - 1) % n]
            out.append([vpt[v], ept[frozenset((v, nxt))], fpt[fi], ept[frozenset((prv, v))]])
    child = Level(out, newv)
    child.fpt, child.ept, child.vpt = fpt, ept, vpt
    return child


def stored(level, quad):
    key = (quad[0], quad[1])
    if key not in level.edge_face:
        return False
    loop = level.faces[level.edge_face[key][0]]
    k = level.edge_face[key][1]
    return len(loop) == 4 and loop[(k + 2) % 4] == quad[2] and loop[(k + 3) % 4] == quad[3]


def face_of(level, quad):
    if stored(level, quad):
        return level.edge_face[(quad[0], quad[1])][0]
    return level.edge_face[(quad[0], quad[3])][0]


def net(level, quad):
    if not stored(level, quad):
        mirror = net(level, [quad[0], quad[3], quad[2], quad[1]])
        return None if mirror is None else {(j, i): v for (i, j), v in mirror.items()}
    q0, q1, q2, q3 = quad
    g = {(0, 0): q0, (1, 0): q1, (1, 1): q2, (0, 1): q3}
    for (a, b, p2, p3) in ((q1, q0, (0, -1), (1, -1)), (q2, q1, (2, 0), (2, 1)), (q3, q2, (1, 2), (0, 2)), (q0, q3, (-1, 1), (-1, 0))):
        if (a, b) not in level.edge_face:
            return None
        fi, k = level.edge_face[(a, b)]
        loop = level.faces[fi]
        if len(loop) != 4:
            return None
        g[p2] = loop[(k + 2) % 4]
        g[p3] = loop[(k + 3) % 4]
    for corner, a, v, b in (((-1, -1), (-1, 0), (0, 0), (0, -1)), ((2, -1), (1, -1), (1, 0), (2, 0)), ((2, 2), (2, 1), (1, 1), (1, 2)), ((-1, 2), (0, 2), (0, 1), (-1, 1))):
        if (g[b], g[v]) not in level.edge_face:
            return None
        fi, k = level.edge_face[(g[b], g[v])]
        loop = level.faces[fi]
        if len(loop) != 4 or loop[(k + 2) % 4] != g[a]:
            return None
        g[corner] = loop[(k + 3) % 4]
    return g


def bspline_basis(t):
    return [(1 - t) ** 3 / 6, (3 * t ** 3 - 6 * t ** 2 + 4) / 6, (-3 * t ** 3 + 3 * t ** 2 + 3 * t + 1) / 6, t ** 3 / 6]


def eval_uniform(level, grid, s, t):
    bu, bv = bspline_basis(s), bspline_basis(t)
    terms = []
    for j in range(4):
        for i in range(4):
            terms.append((bu[i] * bv[j], {k: float(x) for k, x in level.values[grid[(i - 1, j - 1)]].items()}))
    return add(*terms)


def child_quad(parent, child, quad, corner):
    q0, q1, q2, q3 = quad
    fp = child.fpt[face_of(parent, quad)]
    e = lambda a, b: child.ept[frozenset((a, b))]
    v = child.vpt
    return [
        [v[q0], e(q0, q1), fp, e(q0, q3)],
        [e(q0, q1), v[q1], e(q1, q2), fp],
        [fp, e(q1, q2), v[q2], e(q2, q3)],
        [e(q0, q3), fp, e(q2, q3), v[q3]],
    ][corner]


def limit(levels, quad, x, y, depth=0):
    level = levels[depth]
    if all(level.valence[q] == 4 for q in quad):
        grid = net(level, quad)
        if grid is not None:
            return eval_uniform(level, grid, x, y), depth
    if depth + 1 >= len(levels):
        return None, depth
    cx, cy = int(x >= 0.5), int(y >= 0.5)
    corner = {(0, 0): 0, (1, 0): 1, (1, 1): 2, (0, 1): 3}[(cx, cy)]
    sub = child_quad(level, levels[depth + 1], quad, corner)
    return limit(levels, sub, 2 * x - cx, 2 * y - cy, depth + 1)


def basis_funs(knots, x):
    full = []
    for value, count in knots:
        full += [value] * count
    full = [full[0]] + full + [full[-1]]
    if x >= full[-1]:
        x = full[-1] - 1e-12
    return [cox(full, i, 3, x) for i in range(len(full) - 4)]


def cox(t, i, p, x):
    if p == 0:
        return 1.0 if t[i] <= x < t[i + 1] else 0.0
    a = 0.0 if t[i + p] == t[i] else (x - t[i]) / (t[i + p] - t[i]) * cox(t, i, p - 1, x)
    b = 0.0 if t[i + p + 1] == t[i + 1] else (t[i + p + 1] - x) / (t[i + p + 1] - t[i + 1]) * cox(t, i + 1, p - 1, x)
    return a + b


def fusion_eval(rows, findex, ku, kv, s, t):
    nu = sum(c for _, c in ku) - 2
    bu, bv = basis_funs(ku, s), basis_funs(kv, t)
    return add(*[(bu[i] * bv[j], rows[('s', findex, j * len(bu) + i)]) for j in range(len(bv)) for i in range(len(bu)) if bu[i] * bv[j]])


def gap(a, b):
    keys = set(a) | set(b)
    return max(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys)


def walk(level, quad, du, dv):
    q0, q1, q2, q3 = quad
    a, b = (q1, q2) if du else (q3, q2)
    here = face_of(level, quad)
    for key in ((a, b), (b, a)):
        if key in level.edge_face and level.edge_face[key][0] != here:
            loop = level.faces[level.edge_face[key][0]]
            if len(loop) != 4:
                return None
            return orient(loop, a, b, du)
    return None


def orient(loop4, a, b, du):
    for rot in range(4):
        for flip in (False, True):
            cand = loop4[rot:] + loop4[:rot]
            if flip:
                cand = [cand[0], cand[3], cand[2], cand[1]]
            if du and cand[0] == a and cand[3] == b:
                return cand
            if not du and cand[0] == a and cand[1] == b:
                return cand
    return None


INV = [[1, 0, 0, 0], [-5 / 6, 3, -3 / 2, 1 / 3], [1 / 3, -3 / 2, 3, -5 / 6], [0, 0, 0, 1]]
XS = [0.0, 1 / 3, 2 / 3, 1.0]


def inside(lo, hi, x):
    return lo + (hi - lo) * (1e-11 + x * (1 - 2e-11))


def bezier_net(func, a, b, c, d):
    vals = {(i, j): func(inside(a, b, XS[i]), inside(c, d, XS[j])) for i in range(4) for j in range(4)}
    return {(p, q): add(*[(INV[p][i] * INV[q][j], vals[(i, j)]) for i in range(4) for j in range(4)]) for p in range(4) for q in range(4)}


def load_table(name):
    global NAME
    NAME = name
    levels = [load_mesh()]
    for _ in range(3):
        levels.append(subdivide(levels[-1]))
    table = json.loads((STENCIL / (name + 'Table.json')).read_text())
    rows = {tuple(k): {g: float(v) for g, v in r} for k, r in zip(table['keys'], table['rows'])}
    surfaces = [item for item in table['layout'] if item[0] == 'surface']
    return levels, rows, surfaces


def corner_cell(levels, rows, surface):
    _, findex, ku, kv = surface
    for loop in levels[0].faces:
        if len(loop) != 4:
            continue
        for rot in range(4):
            for flip in (False, True):
                cand = loop[rot:] + loop[:rot]
                if flip:
                    cand = [cand[0], cand[3], cand[2], cand[1]]
                hits = 0
                for (s, t) in ((0.7, 0.8), (0.95, 0.6), (0.55, 0.9)):
                    got, _ = limit(levels, cand, s, t)
                    if got is not None and gap(got, fusion_eval(rows, findex, ku, kv, s, t)) <= 1e-12:
                        hits += 1
                if hits == 3:
                    return cand
    return None


def regions(name):
    levels, rows, surfaces = load_table(name)
    out = {'layout': name, 'valences': sorted(set(levels[0].valence.values())), 'faces': []}
    for surface in surfaces:
        _, findex, ku, kv = surface
        corner = corner_cell(levels, rows, surface)
        row = {'face': findex, 'corner_cell_found': corner is not None}
        if corner is None:
            out['faces'].append(row)
            continue
        cells = {(0, 0): corner}
        for i in range(int(ku[-1][0])):
            for j in range(int(kv[-1][0])):
                if (i, j) in cells:
                    continue
                if i > 0 and (i - 1, j) in cells and cells[(i - 1, j)] is not None:
                    cells[(i, j)] = walk(levels[0], cells[(i - 1, j)], True, False)
                elif (i, j - 1) in cells and cells[(i, j - 1)] is not None:
                    cells[(i, j)] = walk(levels[0], cells[(i, j - 1)], False, True)
        gaps = {}
        steps = 12
        for a in range(steps * int(ku[-1][0])):
            for b in range(steps * int(kv[-1][0])):
                s, t = (a + 0.37) / steps, (b + 0.61) / steps
                cell = cells.get((int(s), int(t)))
                if cell is None:
                    continue
                got, depth = limit(levels, cell, s - int(s), t - int(t))
                if got is None:
                    continue
                corners = [levels[0].valence[q] for q in cell]
                if all(value == 4 for value in corners):
                    key = 'regular_cells'
                elif levels[0].valence[cell[0]] != 4 and all(value == 4 for value in corners[1:]):
                    span = lambda x: 0 if x < 0.25 else 1 if x < 0.5 else 2
                    key = 'ev_cell_span_%d%d' % (span(s - int(s)), span(t - int(t)))
                else:
                    key = 'other_cells'
                gaps[key] = max(gaps.get(key, 0.0), gap(got, fusion_eval(rows, findex, ku, kv, s, t)))
        row['max_gap_vs_catmull_clark'] = dict(sorted(gaps.items()))
        out['faces'].append(row)
    return out, levels, rows, surfaces


def bezier_masks(levels, rows, surface):
    _, findex, ku, kv = surface
    corner = corner_cell(levels, rows, surface)
    spans = [(0.0, 0.25), (0.25, 0.5), (0.5, 1.0)]
    masks = {}
    for i, (a, b) in enumerate(spans):
        for j, (c, d) in enumerate(spans):
            if i == 0 and j == 0:
                continue
            fz = bezier_net(lambda s, t: fusion_eval(rows, findex, ku, kv, s, t), a, b, c, d)
            cc = bezier_net(lambda s, t: limit(levels, corner, s, t)[0], a, b, c, d)
            masks['span_%d%d' % (i, j)] = ['' .join('X' if gap(fz[(p, q)], cc[(p, q)]) > 1e-12 else '.' for p in range(4)) for q in range(4)]
    return masks


def main():
    report = {'scope': 'Fusion Form stencil surfaces against the Catmull-Clark limit surface of the same cage, evaluated as grip coefficient vectors. Regular cells and the far quarter of each extraordinary-vertex cell match to rounding, the rest of the extraordinary-vertex cell is the G1 cap region. Bezier masks mark the control points that differ, rows q=0..3 along v, columns p=0..3 along u, for the cell with the extraordinary vertex at u=v=0', 'python': sys.version.split()[0], 'layouts': []}
    for name in ('Box3', 'Box', 'Valence5', 'Valence7'):
        out, levels, rows, surfaces = regions(name)
        if name == 'Box3':
            out['bezier_masks_face0'] = bezier_masks(levels, rows, surfaces[0])
        report['layouts'].append(out)
        print(name, json.dumps(out['faces'][0])[:300])
    (BASE / 'CapStructure.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
