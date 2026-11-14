"""Research: every non-cap pole is the Catmull-Clark blossom of the largest polynomial piece
under its knot box. Compare predicted grip rows with the exact old stencil tables and with the
held-out probe saves (rows evaluated at the cage grips).

Pole (r, c) of a face with full knot vectors fu, fv has blossom arguments
U = fu[c + 1 .. c + 3], V = fv[r + 1 .. r + 3]. Its box [min U, max U] x [min V, max V] is clipped
to a cell (cage face) and descended through Catmull-Clark children until a level-l child face whose
corners all have valence 4 contains it; the blossom of that child's uniform bicubic B-spline net at
the arguments is the row. Poles whose box touches a capped point are cap poles (left to the cap hook).

Usage: PoleRule.py [names...]
"""

import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from KnotRule import CORNERS, capped_points, cap_levels, fusion_faces, predict as knot_predict  # noqa: E402
from PoleData import GENERAL, OLD_LABELS, expand, grip_array, read_tables, table_faces  # noqa: E402
from CapLab import Cage, Levels, regular_net  # noqa: E402

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import ReadGraph  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedLayout import CappedLayout, KnotScale  # noqa: E402

TOL = 1e-12


def full_knots(knots):
    out = expand(knots)
    return [out[0]] + out + [out[-1]]


def deboor_blossom(points, xs):
    """Blossom of the uniform cubic B-spline piece on [0, 1] with 4 control values (axis 0)."""
    t = [-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0]
    d = [points[j] for j in range(4)]
    for r in range(1, 4):
        x = xs[r - 1]
        new = list(d)
        for j in range(3, r - 1, -1):
            a = (x - t[j]) / (t[j + 4 - r] - t[j])
            new[j] = (1 - a) * d[j - 1] + a * d[j]
        d = new
    return d[3]


def net_blossom(net, s_args, t_args):
    """net[j][i] (rows t, columns s) of the 4x4 uniform net around [0, 1]^2."""
    rows = [deboor_blossom([net[j][i] for i in range(4)], s_args) for j in range(4)]
    return deboor_blossom(rows, t_args)


class CellFrame:
    """Affine map from level-0 cell coordinates (s, t) to a descendant's local coordinates."""

    def __init__(self, face, level, matrix, shift):
        self.face = face
        self.level = level
        self.matrix = matrix  # 2x2 signed permutation times 2^level
        self.shift = shift

    def apply(self, s, t):
        return (self.matrix[0][0] * s + self.matrix[0][1] * t + self.shift[0],
                self.matrix[1][0] * s + self.matrix[1][1] * t + self.shift[1])

    def child(self, corner):
        """Child 4f + corner keeps corner `corner`; its axes run to the next and previous corners."""
        origin = CORNERS[corner]
        axis_u = tuple(CORNERS[(corner + 1) % 4][k] - origin[k] for k in range(2))
        axis_v = tuple(CORNERS[(corner - 1) % 4][k] - origin[k] for k in range(2))
        # child local (a, b) -> parent local p = origin + (a axis_u + b axis_v) / 2; inverse:
        # a = 2 axis_u . (p - origin), b = 2 axis_v . (p - origin)
        inner = ((2 * axis_u[0], 2 * axis_u[1]), (2 * axis_v[0], 2 * axis_v[1]))
        inner_shift = (-(inner[0][0] * origin[0] + inner[0][1] * origin[1]),
                       -(inner[1][0] * origin[0] + inner[1][1] * origin[1]))
        m = self.matrix
        mat = tuple(tuple(sum(inner[r][k] * m[k][c] for k in range(2)) for c in range(2)) for r in range(2))
        sh = tuple(sum(inner[r][k] * self.shift[k] for k in range(2)) + inner_shift[r] for r in range(2))
        return CellFrame(4 * self.face + corner, self.level + 1, mat, sh)


def box_corners(lo, hi):
    return [(lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1])]


def descend(levels, frame, lo, hi, max_level):
    """Find the child face (frame) whose regular net covers the cell box [lo, hi]."""
    if hasattr(levels, 'net'):
        net = levels.net(frame.level, frame.face)
    else:
        net = regular_net(levels.levels[frame.level], frame.face)
    if net is not None:
        return frame, net
    if frame.level >= max_level:
        return None
    pts = [frame.apply(*p) for p in box_corners(lo, hi)]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    for corner in range(4):
        qx = (0.0, 0.5) if CORNERS[corner][0] == 0 else (0.5, 1.0)
        qy = (0.0, 0.5) if CORNERS[corner][1] == 0 else (0.5, 1.0)
        if min(xs) >= qx[0] - TOL and max(xs) <= qx[1] + TOL and min(ys) >= qy[0] - TOL and max(ys) <= qy[1] + TOL:
            found = descend(levels, frame.child(corner), lo, hi, max_level)
            if found is not None:
                return found
    return None


def cell_inverse(cell, scale):
    """face (u, v) -> cell-local (s, t) in [0, 1]^2."""
    off = cell.Offset

    def inv(u, v):
        x, y = u, v
        for _ in range((-off[2]) % 4):
            x, y = -y, x
        return (x + off[1]) / scale, (y + off[0]) / scale
    return inv


def pole_row(levels, cells, scale, fu, fv, r, c, max_level=4):
    """Catmull-Clark blossom of pole (r, c) from the first support span pair that is polynomial."""
    u_args, v_args = fu[c + 1:c + 4], fv[r + 1:r + 4]
    spans_u = [(fu[k], fu[k + 1]) for k in range(c, c + 4) if fu[k] < fu[k + 1]]
    spans_v = [(fv[k], fv[k + 1]) for k in range(r, r + 4) if fv[k] < fv[k + 1]]
    for span_u in spans_u:
        for span_v in spans_v:
            row = span_row(levels, cells, scale, u_args, v_args, span_u, span_v, max_level)
            if row is not None:
                return row
    return None


def span_row(levels, cells, scale, u_args, v_args, span_u, span_v, max_level):
    lo_u, hi_u = span_u
    lo_v, hi_v = span_v
    results = []
    for cell in cells:
        inv = cell_inverse(cell, scale)
        p0, p1 = inv(lo_u, lo_v), inv(hi_u, hi_v)
        lo = (max(0.0, min(p0[0], p1[0])), max(0.0, min(p0[1], p1[1])))
        hi = (min(1.0, max(p0[0], p1[0])), min(1.0, max(p0[1], p1[1])))
        if lo[0] > hi[0] - TOL or lo[1] > hi[1] - TOL:
            continue
        found = descend(levels, CellFrame(cell.Face, 0, ((1, 0), (0, 1)), (0, 0)), lo, hi, max_level)
        if found is None:
            continue
        frame, net = found
        pts = [frame.apply(*inv(u, v)) for u, v in zip(u_args, v_args)]
        # which local coordinate does u feed? map a u-step
        a0 = frame.apply(*inv(u_args[0], v_args[0]))
        a1 = frame.apply(*inv(u_args[0] + 1.0, v_args[0]))
        u_is_s = abs(a1[0] - a0[0]) > TOL
        s_args = [frame.apply(*inv(u, v_args[0]))[0] for u in u_args] if u_is_s else [frame.apply(*inv(u_args[0], v))[0] for v in v_args]
        t_args = [frame.apply(*inv(u_args[0], v))[1] for v in v_args] if u_is_s else [frame.apply(*inv(u, v_args[0]))[1] for u in u_args]
        del pts
        results.append(net_blossom(net, s_args, t_args))
    if not results:
        return None
    for other in results[1:]:
        if np.abs(other - results[0]).max() > 1e-9:
            raise RuntimeError('cells disagree on a pole blossom')
    return results[0]


def face_corner_vertices(graph, cells, scale, ku, kv):
    """{(u_end, v_end): cage vertex} for the four corners of a face."""
    out = {}
    for ue in (0, 1):
        for ve in (0, 1):
            u = ku[0][0] if ue == 0 else ku[-1][0]
            v = kv[0][0] if ve == 0 else kv[-1][0]
            for cell in cells:
                s, t = cell_inverse(cell, scale)(u, v)
                for corner, (cs, ct) in enumerate(CORNERS):
                    if abs(s - cs) < TOL and abs(t - ct) < TOL:
                        out[(ue, ve)] = graph.Links[graph.Loops[cell.Face][corner]].VertexIndex
    return out


def extra_reach(knots, base, end, level, scale):
    """Propagated (non-intrinsic) knots at distance in (2h, 4h) from the face end `end`."""
    if base is None:
        return 0
    h = Fraction(1, 2 ** (level + 1))
    lower, upper = Fraction(knots[0][0]) / scale, Fraction(knots[-1][0]) / scale
    count = 0
    for value, _ in knots[1:-1]:
        x = Fraction(value) / scale
        if x in base:
            continue
        dist = x - lower if end == 0 else upper - x
        if 2 * h < dist < 4 * h:
            count += 1
    return count


def cap_keys(graph, cells, scale, ku, kv, count_u, count_v, caps, base=None):
    """{(r, c): (ep, i, j)} for cap unknowns of this face.

    Standard set: i, j <= 4 except (4, 4). A propagated knot inside (2h, 4h) along one
    direction adds one more index along it for the rows i <= 3 (columns j <= 3)."""
    corners = face_corner_vertices(graph, cells, scale, ku, kv)
    levels = caps if isinstance(caps, dict) else {v: 1 for v in caps}
    out = {}
    for (ue, ve), vertex in corners.items():
        if vertex not in levels:
            continue
        more_i = extra_reach(ku, base[0] if base else None, ue, levels[vertex], scale)
        more_j = extra_reach(kv, base[1] if base else None, ve, levels[vertex], scale)
        for r in range(count_v):
            for c in range(count_u):
                i = c if ue == 0 else count_u - 1 - c
                j = r if ve == 0 else count_v - 1 - r
                standard = i <= 4 and j <= 4 and (i, j) != (4, 4)
                extended = (i <= 3 and j <= 4 + more_j) or (j <= 3 and i <= 4 + more_i)
                if standard or extended:
                    out[(r, c)] = (vertex, i, j)
    return out


def predict_face(levels, graph, cells, scale, ku, kv, caps, base=None):
    fu, fv = full_knots(ku), full_knots(kv)
    count_u, count_v = len(fu) - 4, len(fv) - 4
    keys = cap_keys(graph, cells, scale, ku, kv, count_u, count_v, caps, base)
    rows = {}
    for r in range(count_v):
        for c in range(count_u):
            if (r, c) in keys:
                continue
            rows[(r, c)] = pole_row(levels, cells, scale, fu, fv, r, c)
    return rows, keys


def check_old(label):
    table = read_tables()[label]
    surface, faces = fusion_faces(label)
    graph = ReadGraph(surface)
    shape = CappedLayout(surface)
    scale = KnotScale(surface)
    caps = capped_points(graph)
    cage = Cage.from_surface(surface)
    levels = Levels(cage, depth=4)
    worst, missing, count, capcount = 0.0, 0, 0, 0
    for region, cells in enumerate(shape.Regions):
        ku, kv, grid = faces[region]
        rows, keys = predict_face(levels, graph, cells, scale, ku, kv, caps)
        capcount += len(keys)
        for (r, c), row in rows.items():
            if row is None:
                missing += 1
                continue
            count += 1
            worst = max(worst, float(np.abs(row - grid[r, c]).max()))
    return worst, count, missing, capcount


def check_probe(name):
    surface, faces = fusion_faces(name)
    graph = ReadGraph(surface)
    shape = CappedLayout(surface)
    scale = KnotScale(surface)
    caps = cap_levels(graph, capped_points(graph))
    _, base, _ = knot_predict(surface, 'none')
    cage = Cage.from_surface(surface)
    levels = Levels(cage, depth=4)
    grips = grip_array(surface)[:, :3]
    worst, missing, count, capcount = 0.0, 0, 0, 0
    for region, cells in enumerate(shape.Regions):
        ku, kv, grid = faces[region]
        rows, keys = predict_face(levels, graph, cells, scale, ku, kv, caps, base[region])
        capcount += len(keys)
        for (r, c), row in rows.items():
            if row is None:
                missing += 1
                continue
            count += 1
            worst = max(worst, float(np.abs(row @ grips - grid[r, c, :3]).max()))
    return worst, count, missing, capcount


def main():
    names = sys.argv[1:] or list(OLD_LABELS) + list(GENERAL)
    for name in names:
        try:
            if name in OLD_LABELS:
                result = check_old(name)
            else:
                result = check_probe(name)
        except Exception as error:  # research: report and continue
            print('%-14s ERROR %r' % (name, error))
            continue
        print('%-14s non-cap worst %.3e  poles %d  missing %d  cap poles %d' % ((name,) + result))


if __name__ == '__main__':
    main()
