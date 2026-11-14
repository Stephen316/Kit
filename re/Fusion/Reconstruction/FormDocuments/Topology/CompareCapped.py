"""Research: compare the src capped layout rule with Fusion's own bodies.

Run with /opt/homebrew/bin/python3.14 -I (method-93 F3D reads need 3.14).

Part one checks the eight old layouts against the frozen FormShapes table.
Part two checks the twelve held-out General cages against the bodies Fusion
saved for them. Floats compare within SLACK (Fusion fit values are ~1e-16
noise, the rule writes 0.0). Labels are reported apart from the structural
verdict because Fusion relabels the same layout between saves.

Usage: CompareCapped.py [--json out.json] [names...]
"""

import json
import math
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE.parent / 'Tables'))
from SavedBodies import GENERAL, OLD_SAVES, ROOT, general_saved, old_saved, read_saved  # noqa: E402

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedLayout import CappedLayout  # noqa: E402
from ReadShapes import ReadShapes  # noqa: E402
from ReadStencils import ReadStencils  # noqa: E402
from StencilKey import StencilKey  # noqa: E402

SLACK = 1e-12


def close(a, b):
    return abs(a - b) <= SLACK


def same_trace(mine, theirs):
    if (mine.Rational, mine.Degree, mine.Closure, mine.Multiplicity, mine.Dimension) != (
        theirs.Rational, theirs.Degree, theirs.Closure, theirs.Multiplicity, theirs.Dimension
    ):
        return False
    if len(mine.Knots) != len(theirs.Knots) or len(mine.Poles) != len(theirs.Poles):
        return False
    if not all(close(a, b) for a, b in zip(mine.Knots, theirs.Knots)):
        return False
    return all(close(a, b) for p, q in zip(mine.Poles, theirs.Poles) for a, b in zip(p, q))


def window_tuple(window):
    return (window.Face, window.ULow, window.UHigh, window.VLow, window.VHigh)


def compare_faces(shape, faces, region_of, out):
    if len(shape.Faces) != len(faces):
        out.append('face count %d vs %d' % (len(shape.Faces), len(faces)))
        return
    for index, (mine, theirs) in enumerate(zip(shape.Faces, faces)):
        if mine.Region != region_of(theirs):
            out.append('face %d region %d vs %d' % (index, mine.Region, region_of(theirs)))
        if (mine.DoubleSided, mine.Contained) != (theirs.DoubleSided, theirs.Contained):
            out.append('face %d sidedness %s vs %s' % (index, (mine.DoubleSided, mine.Contained), (theirs.DoubleSided, theirs.Contained)))
        if len(mine.Uses) != len(theirs.Uses):
            out.append('face %d use count %d vs %d' % (index, len(mine.Uses), len(theirs.Uses)))
            continue
        for slot, (a, b) in enumerate(zip(mine.Uses, theirs.Uses)):
            if (a.EdgeIndex, a.Reversed) != (b.EdgeIndex, b.Reversed):
                out.append('face %d use %d edge %s vs %s' % (index, slot, (a.EdgeIndex, a.Reversed), (b.EdgeIndex, b.Reversed)))
            elif not same_trace(a.Pcurve, b.Pcurve):
                out.append('face %d use %d pcurve %s %s vs %s %s' % (index, slot, a.Pcurve.Knots, a.Pcurve.Poles, b.Pcurve.Knots, b.Pcurve.Poles))
            if not close(a.Fit, b.Fit):
                out.append('face %d use %d fit %r vs %r' % (index, slot, a.Fit, b.Fit))


def compare_closures(shape, edges, out):
    for index, (mine, theirs) in enumerate(zip(shape.Edges, edges)):
        if shape.Curves[mine.CurveIndex].Closure != theirs.Curve.Closure:
            out.append('edge %d curve closure %d vs %d' % (index, shape.Curves[mine.CurveIndex].Closure, theirs.Curve.Closure))


def compare_edges(shape, edges, curve_range, curve_of, out):
    if len(shape.Edges) != len(edges):
        out.append('edge count %d vs %d' % (len(shape.Edges), len(edges)))
        return
    for index, (mine, theirs) in enumerate(zip(shape.Edges, edges)):
        if (mine.StartVertex, mine.EndVertex) != (theirs.StartVertex, theirs.EndVertex):
            out.append('edge %d ends %s vs %s' % (index, (mine.StartVertex, mine.EndVertex), (theirs.StartVertex, theirs.EndVertex)))
        if mine.Convexity != theirs.Convexity:
            out.append('edge %d convexity %s vs %s' % (index, mine.Convexity, theirs.Convexity))
        if mine.Bounds != theirs.Bounds:
            out.append('edge %d bounds %s vs %s' % (index, mine.Bounds, theirs.Bounds))
        a = [window_tuple(w) for w in mine.Windows]
        b = [window_tuple(w) for w in theirs.Windows]
        if len(a) != len(b) or not all(p[0] == q[0] and all(close(x, y) for x, y in zip(p[1:], q[1:])) for p, q in zip(a, b)):
            out.append('edge %d windows %s vs %s' % (index, a, b))
        curve = shape.Curves[mine.CurveIndex]
        lower, upper = curve_range(index)
        if not (close(curve.Lower, lower) and close(curve.Upper, upper)):
            out.append('edge %d curve range %s vs %s' % (index, (curve.Lower, curve.Upper), (lower, upper)))
    mine_groups = sorted(sorted(i for i, e in enumerate(shape.Edges) if e.CurveIndex == c) for c in {e.CurveIndex for e in shape.Edges})
    their_keys = [curve_of(i) for i in range(len(edges))]
    their_groups = sorted(sorted(i for i, k in enumerate(their_keys) if k == c) for c in set(their_keys))
    if mine_groups != their_groups:
        out.append('curve sharing %s vs %s' % ([g for g in mine_groups if len(g) > 1], [g for g in their_groups if len(g) > 1]))


def label_report(shape, face_labels, edge_labels):
    mine_faces = [f.Label for f in shape.Faces]
    mine_edges = [e.Label for e in shape.Edges]
    tagged_mine = [bool(x) for x in mine_edges]
    tagged_theirs = [bool(x) for x in edge_labels]
    return {
        'faces_equal': mine_faces == list(face_labels),
        'edges_equal': mine_edges == list(edge_labels),
        'tagged_edges_equal': tagged_mine == tagged_theirs,
        'label_set_equal': sorted(mine_faces + [x for x in mine_edges if x]) == sorted(list(face_labels) + [x for x in edge_labels if x]),
        'fusion_faces': list(face_labels),
        'fusion_edges': [x for x in edge_labels],
    }


def grip_vertex(surface, grip):
    if surface.Mapping is None:
        return grip
    return surface.Mapping.Owners[grip].VertexIndex


def old_points(surface, table, shape):
    out = []
    for index in shape.Points:
        row = table.Rows[table.Points[index]]
        grip = max(row, key=lambda pair: pair[1])[0]
        out.append(grip_vertex(surface, grip))
    return out


def compare_old(name):
    saved = old_saved(name)
    surface = saved.surface
    key = StencilKey(surface)
    table_shape = ReadShapes().get(key)
    table = ReadStencils().get(key)
    if table_shape is None or table is None:
        return {'name': name, 'verdict': 'NO TABLE', 'diffs': ['layout key missing from FormShapes']}
    shape = CappedLayout(surface)
    diffs = []
    if shape.Regions != table_shape.Regions:
        diffs.append('regions differ')
    compare_faces(shape, table_shape.Faces, lambda face: face.FaceIndex, diffs)

    def curve_range(index):
        curve = table.Curves[table_shape.Edges[index].CurveIndex]
        return curve.Knots[0], curve.Knots[-1]

    compare_edges(shape, table_shape.Edges, curve_range, lambda i: table_shape.Edges[i].CurveIndex, diffs)
    points = old_points(surface, table, table_shape)
    if list(shape.Points) != points:
        diffs.append('points %s vs %s' % (list(shape.Points), points))
    labels = label_report(shape, [f.Label for f in table_shape.Faces], [e.Label for e in table_shape.Edges])
    save = compare_general(name, saved)
    return {'name': name, 'verdict': 'MATCH' if not diffs else 'DIFF', 'diffs': diffs, 'labels': labels, 'save': save}


def limit_points(surface):
    from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import ReadGraph

    graph = ReadGraph(surface)
    grips = [(g.CoordX, g.CoordY, g.CoordZ) for g in surface.Grips]
    if surface.Mapping is not None:
        primary = {owner.VertexIndex: grip for grip, owner in enumerate(surface.Mapping.Owners) if owner.IsPrimary}
        grips = [grips[primary[vertex]] for vertex in range(len(graph.Fans))]

    def at(vertex):
        return grips[vertex]

    out = []
    for vertex, fan in enumerate(graph.Fans):
        sharp = [link for link in fan if graph.Sharp[link]]
        if len(sharp) == 2:
            a, b = (graph.Heads[link] for link in sharp)
            out.append(tuple((4 * at(vertex)[k] + at(a)[k] + at(b)[k]) / 6 for k in range(3)))
        elif sharp:
            out.append(at(vertex))
        else:
            n = len(fan)
            edge_sum = [sum(at(graph.Heads[link])[k] for link in fan) for k in range(3)]
            face_sum = [sum(at(graph.Heads[graph.Links[link].NextLink])[k] for link in fan) for k in range(3)]
            out.append(tuple((n * n * at(vertex)[k] + 4 * edge_sum[k] + face_sum[k]) / (n * (n + 5)) for k in range(3)))
    return out


def saved_points(saved):
    limits = limit_points(saved.surface)
    best = None
    for factor in (1.0, 100.0, 10.0, 0.1, 0.01):
        picks, worst = [], 0.0
        for point in saved.body.PointsCm:
            dists = [math.dist(point, tuple(factor * x for x in limit)) for limit in limits]
            pick = min(range(len(dists)), key=dists.__getitem__)
            picks.append(pick)
            worst = max(worst, dists[pick])
        if best is None or worst < best[1]:
            best = (picks, worst, factor)
    return best


def compare_general(name, saved=None):
    saved = saved or general_saved(name)
    shape = CappedLayout(saved.surface)
    body = saved.body
    diffs = []
    if shape.Regions != body.Regions:
        diffs.append('regions differ: mine %s vs fusion %s' % (
            [[(c.Face, c.Offset) for c in r] for r in shape.Regions],
            [[(c.Face, c.Offset) for c in r] for r in body.Regions]))
    compare_faces(shape, body.Faces, lambda face: face.Surface.Region, diffs)

    def curve_range(index):
        knots = body.Edges[index].Curve.Knots
        return knots[0], knots[-1]

    compare_edges(shape, body.Edges, curve_range, lambda i: saved.curve_order[i], diffs)
    compare_closures(shape, body.Edges, diffs)
    picks, worst, factor = saved_points(saved)
    if list(shape.Points) != picks:
        diffs.append('points %s vs nearest limit %s' % (list(shape.Points), picks))
    labels = label_report(shape, [f.Label for f in body.Faces], [e.Label for e in body.Edges])
    return {
        'name': name,
        'verdict': 'MATCH' if not diffs else 'DIFF',
        'diffs': diffs,
        'labels': labels,
        'point_fit': {'unit_factor': factor, 'worst_cm': worst},
    }


ACCEPTANCE = (
    're/Fusion/LocalOracle/FormDocuments/Acceptance/Saved/BoxControl.f3d',
    're/Fusion/LocalOracle/FormDocuments/Acceptance/Saved/PlaneCreasedControl.f3d',
    're/Fusion/LocalOracle/FormDocuments/Acceptance/Saved/PlaneControl.f3d',
    're/Fusion/LocalOracle/FormDocuments/Grid/Primitives/Plane2x5.f3d',
)


def main(argv):
    out_path = None
    if argv[:1] == ['--json']:
        out_path, argv = argv[1], argv[2:]
    names = argv or (list(OLD_SAVES) + list(GENERAL) + list(ACCEPTANCE))
    rows = []
    for name in names:
        try:
            if name in OLD_SAVES:
                row = compare_old(name)
            elif name.endswith('.f3d'):
                row = compare_general(name.rsplit('/', 1)[-1], read_saved(ROOT / name))
            else:
                row = compare_general(name)
        except ValueError as error:
            row = {'name': name, 'verdict': 'RAISED', 'diffs': [str(error)]}
        rows.append(row)
        labels = row.get('labels', {})
        print('%-14s %-7s labels faces=%s edges=%s tagged=%s set=%s' % (
            name, row['verdict'], labels.get('faces_equal'), labels.get('edges_equal'),
            labels.get('tagged_edges_equal'), labels.get('label_set_equal')))
        for line in row['diffs'][:12]:
            print('    ' + line)
        if 'point_fit' in row:
            print('    nearest-limit point fit: factor %g worst %.3g cm' % (row['point_fit']['unit_factor'], row['point_fit']['worst_cm']))
        if 'save' in row:
            print('    against its own save (%s): %s' % (OLD_SAVES[name].rsplit('/', 1)[-1], row['save']['verdict']))
            for line in row['save']['diffs'][:12]:
                print('        ' + line)
    if out_path:
        Path(out_path).write_text(json.dumps({'python': sys.version.split()[0], 'slack': SLACK, 'cases': rows}, indent=1) + '\n')


if __name__ == '__main__':
    main(sys.argv[1:])
