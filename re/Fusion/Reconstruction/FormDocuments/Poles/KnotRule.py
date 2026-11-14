"""Research: predict every converted face's knot vectors from the cage, compare with Fusion.

Rule under test (all lengths in cage-edge units, scaled by the knot interval at the end):
1. Capped points: inside vertices (not open, not creased) with valence != 4.
2. Cap level L per capped point: 2 when a cage edge joins it to another capped point, else 1.
   h = 2^-(L + 1).
3. Each cell (cage face) gets, for every capped corner and each of its two directions,
   knot lines at distance h and 2h from that corner (double) and the Catmull-Clark
   breaklines 2^-l, l = 1 .. L - 1 (single).
4. A face's knots are the union of its cells' lines, mapped through the PatchCell maps.
5. Propagation (mode 'none', 'once', 'closure'): a face also takes, as single knots, the knot
   lines of each neighbouring face that cross their shared boundary.

Usage: KnotRule.py [--mode closure] [names...]
"""

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PoleData import GENERAL, OLD_LABELS, general_saved, general_surface, old_surface, read_tables, table_faces  # noqa: E402

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import ReadGraph  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedLayout import CappedLayout, KnotScale  # noqa: E402

CORNERS = ((0, 0), (1, 0), (1, 1), (0, 1))


def capped_points(graph):
    """Inside vertices with valence != 4, and darts (inside vertices with one creased edge)."""
    out = set()
    for v, fan in enumerate(graph.Fans):
        if not graph.Inside[v]:
            continue
        creased = sum(1 for link in fan if graph.Creased[link])
        if len(fan) != 4 or creased == 1:
            out.add(v)
    return out


def cap_levels(graph, caps):
    levels = {}
    for v in caps:
        near = any(graph.Heads[link] in caps for link in graph.Fans[v])
        levels[v] = 2 if near else 1
    return levels


def corner_knots(level):
    h = Fraction(1, 2 ** (level + 1))
    out = {h: 2, 2 * h: 2}
    for l in range(1, level):
        out[Fraction(1, 2 ** l)] = max(out.get(Fraction(1, 2 ** l), 0), 1)
    return out


def merge(into, extra):
    for x, m in extra.items():
        into[x] = max(into.get(x, 0), m)


def cell_knots(graph, face, levels):
    """Intrinsic (s_knots, t_knots) of a cage face as {position in (0, 1): multiplicity}."""
    s_knots, t_knots = {}, {}
    for corner, link in enumerate(graph.Loops[face]):
        v = graph.Links[link].VertexIndex
        if v not in levels:
            continue
        cs, ct = CORNERS[corner]
        merge(s_knots, {Fraction(cs): 2})
        merge(t_knots, {Fraction(ct): 2})
        for x, m in corner_knots(levels[v]).items():
            merge(s_knots, {x if cs == 0 else 1 - x: m})
            merge(t_knots, {x if ct == 0 else 1 - x: m})
    return s_knots, t_knots


class FaceMap:
    def __init__(self, cell, scale):
        self.cell = cell
        self.scale = scale

    def to_face(self, s, t):
        off = self.cell.Offset
        x, y = s * self.scale - off[1], t * self.scale - off[0]
        for _ in range(off[2] % 4):
            x, y = -y, x
        return x, y


def face_knots(graph, shape, scale, levels):
    """region -> ({u: mult}, {v: mult}) from intrinsic cell knots and the cell boundaries."""
    out = []
    for cells in shape.Regions:
        ku, kv = {}, {}
        for cell in cells:
            fm = FaceMap(cell, scale)
            for corner in CORNERS:
                p = fm.to_face(*corner)
                merge(ku, {Fraction(p[0]): 1})
                merge(kv, {Fraction(p[1]): 1})
        for cell in cells:
            fm = FaceMap(cell, scale)
            s_knots, t_knots = cell_knots(graph, cell.Face, levels)
            for axis_knots, along in ((s_knots, 0), (t_knots, 1)):
                for x, m in axis_knots.items():
                    a = fm.to_face(x if along == 0 else 0, 0 if along == 0 else x)
                    b = fm.to_face(x if along == 0 else 1, 1 if along == 0 else x)
                    if a[0] == b[0]:
                        merge(ku, {Fraction(a[0]): m})
                    else:
                        merge(kv, {Fraction(a[1]): m})
        out.append((ku, kv))
    return out


def cell_owner(shape, scale):
    owner = {}
    for region, cells in enumerate(shape.Regions):
        for cell in cells:
            owner[cell.Face] = (region, FaceMap(cell, scale))
    return owner


def side_crossings(knots, fm, side):
    """Positions x in (0, 1) along cell side `side` where the face knot lines cross it."""
    ku, kv = knots
    a = fm.to_face(*CORNERS[side])
    b = fm.to_face(*CORNERS[(side + 1) % 4])
    out = set()
    if a[0] != b[0]:
        lo, hi = a[0], b[0]
        for u in ku:
            x = Fraction(u - lo) / Fraction(hi - lo)
            if 0 < x < 1:
                out.add(x)
    else:
        lo, hi = a[1], b[1]
        for v in kv:
            x = Fraction(v - lo) / Fraction(hi - lo)
            if 0 < x < 1:
                out.add(x)
    return out


def period_reduce(value, period):
    return value % period if period else value


def cell_crossings(graph, face, side, levels):
    """Positions along cell side `side` where the cell's own cap lines cross it."""
    s_knots, t_knots = cell_knots(graph, face, levels)
    values = s_knots if side in (0, 2) else t_knots
    return {x if side in (0, 1) else 1 - x for x in values if 0 < x < 1}


def spoke_once(graph, shape, scale, base, levels, own_cell=False):
    """Each capped point unifies, along each spoke within 4h of it, the base knots of the two faces.

    own_cell: copy only the lines the other cell draws itself (its capped corners), not every
    knot of the other face."""
    owner = cell_owner(shape, scale)
    current = [(dict(ku), dict(kv)) for ku, kv in base]
    for v, level in levels.items():
        reach = Fraction(4, 2 ** (level + 1))
        for link in graph.Fans[v]:
            across = graph.Links[link].Opposite
            pair = []
            for lk in (link, across):
                face = graph.Links[lk].FaceIndex
                region, fm = owner[face]
                side = graph.Loops[face].index(lk)
                pair.append((region, fm, side, lk == link))
            faces = [graph.Links[lk].FaceIndex for lk in (link, across)]
            for ((r1, fm1, s1, out1), (r2, fm2, s2, out2)), other in zip((pair, pair[::-1]), faces[::-1]):
                if own_cell:
                    xs = cell_crossings(graph, other, s2, levels)
                else:
                    xs = side_crossings(base[r2], fm2, s2)
                for x in xs:
                    dist = x if out2 else 1 - x
                    if dist > reach:
                        continue
                    y = dist if out1 else 1 - dist
                    p = tuple((1 - y) * c0 + y * c1 for c0, c1 in zip(CORNERS[s1], CORNERS[(s1 + 1) % 4]))
                    a = fm1.to_face(*p)
                    ku, kv = current[r1]
                    if fm1.to_face(*CORNERS[s1])[0] != fm1.to_face(*CORNERS[(s1 + 1) % 4])[0]:
                        key = period_reduce(Fraction(a[0]), shape.Periods[r1][0])
                        ku.setdefault(key, 1)
                    else:
                        key = period_reduce(Fraction(a[1]), shape.Periods[r1][1])
                        kv.setdefault(key, 1)
    return current


def propagate(graph, shape, scale, base, mode, levels=None):
    if mode == 'none':
        return base
    if mode == 'spoke':
        return spoke_once(graph, shape, scale, base, levels)
    if mode == 'cell':
        return spoke_once(graph, shape, scale, base, levels, own_cell=True)
    owner = cell_owner(shape, scale)
    current = [(dict(ku), dict(kv)) for ku, kv in base]
    source = base
    for _ in range(50 if mode == 'closure' else 1):
        changed = False
        for region, cells in enumerate(shape.Regions):
            ku, kv = current[region]
            for cell in cells:
                fm = FaceMap(cell, scale)
                for side, link in enumerate(graph.Loops[cell.Face]):
                    across = graph.Links[link].Opposite
                    other = graph.Links[across].FaceIndex
                    if other < 0 or other not in owner:
                        continue
                    o_region, o_fm = owner[other]
                    o_side = graph.Loops[other].index(across)
                    xs = side_crossings(source[o_region] if mode == 'once' else current[o_region], o_fm, o_side)
                    for x in xs:
                        y = 1 - x
                        p = tuple((1 - y) * c0 + y * c1 for c0, c1 in zip(CORNERS[side], CORNERS[(side + 1) % 4]))
                        a = fm.to_face(*p)
                        if fm.to_face(*CORNERS[side])[0] != fm.to_face(*CORNERS[(side + 1) % 4])[0]:
                            u = Fraction(a[0])
                            u = period_reduce(u, shape.Periods[region][0])
                            if u not in ku:
                                ku[u] = 1
                                changed = True
                        else:
                            v = Fraction(a[1])
                            v = period_reduce(v, shape.Periods[region][1])
                            if v not in kv:
                                kv[v] = 1
                                changed = True
        if not changed:
            break
    return current


def as_vector(knots, lower, upper, period):
    inner = sorted((x, m) for x, m in knots.items() if lower < x < upper)
    if period:
        return [(float(lower), 1)] + [(float(x), m) for x, m in inner] + [(float(upper), 1)]
    return [(float(lower), 3)] + [(float(x), m) for x, m in inner] + [(float(upper), 3)]


def predict(surface, mode='closure'):
    graph = ReadGraph(surface)
    shape = CappedLayout(surface)
    scale = KnotScale(surface)
    caps = capped_points(graph)
    levels = cap_levels(graph, caps)
    base = face_knots(graph, shape, 1, levels)
    knots = propagate(graph, shape, 1, base, mode, levels)
    return shape, knots, levels


def fusion_faces(name):
    if name in OLD_LABELS:
        surface = old_surface(name)
        faces, _ = table_faces(read_tables()[name])
        return surface, faces
    surface = general_surface(name)
    faces, _ = general_saved(name)
    return surface, faces


def compare(name, mode):
    surface, faces = fusion_faces(name)
    shape, knots, levels = predict(surface, mode)
    scale = KnotScale(surface)
    bad = []
    for region, (ku, kv) in enumerate(knots):
        fu, fv, _ = faces[region]
        lo_u, hi_u = Fraction(fu[0][0]) / scale, Fraction(fu[-1][0]) / scale
        lo_v, hi_v = Fraction(fv[0][0]) / scale, Fraction(fv[-1][0]) / scale
        pu = [(x * scale, m) for x, m in as_vector(ku, lo_u, hi_u, shape.Periods[region][0])]
        pv = [(x * scale, m) for x, m in as_vector(kv, lo_v, hi_v, shape.Periods[region][1])]
        if [(round(a, 9), c) for a, c in pu] != [(round(a, 9), c) for a, c in fu]:
            bad.append((region, 'U', pu, fu))
        if [(round(a, 9), c) for a, c in pv] != [(round(a, 9), c) for a, c in fv]:
            bad.append((region, 'V', pv, fv))
    return bad, levels


def main():
    args = sys.argv[1:]
    mode = 'closure'
    if args[:1] == ['--mode']:
        mode, args = args[1], args[2:]
    names = args or list(OLD_LABELS) + list(GENERAL)
    for name in names:
        try:
            bad, levels = compare(name, mode)
        except Exception as error:  # research: report and continue
            print('%-14s ERROR %s' % (name, error))
            continue
        counts = {}
        for v in levels.values():
            counts[v] = counts.get(v, 0) + 1
        print('%-14s %s  levels %s' % (name, 'MATCH' if not bad else 'DIFF %d' % len(bad), counts))
        for entry in bad[:4]:
            print('    region %d %s mine %s' % entry[:3])
            print('                 fusion %s' % (entry[3],))


if __name__ == '__main__':
    main()
