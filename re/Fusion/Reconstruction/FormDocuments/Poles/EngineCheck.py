"""Research: run the src pole engine (BuildTable) on the old layouts and the probes.

Old layouts: non-cap agreement with the exact FormStencils rows (cap keys get their netref rows), and
whole-body agreement (faces, curves, points) when a hook hands back Fusion's own cap rows.
Probes and crease saves: non-cap poles evaluated at the grips against Fusion's save.

Usage: EngineCheck.py [names...] | EngineCheck.py --pair cage.tsm save.f3d
"""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PoleData import GENERAL, OLD_LABELS, general_saved, general_surface, grip_array, old_surface, read_tables, saved_faces, table_faces, table_matrix  # noqa: E402

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import ReadGraph  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedLayout import CappedLayout, KnotScale  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapFrames import BaseRow, RegionFrames  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapPlaces import SectorKnots  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.FaceNets import MeshLevels  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.GridPoles import IsCompound  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleMesh import MeshFromCage  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleKnots import CapPoints  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleTable import BuildTable, FacePlans  # noqa: E402
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline  # noqa: E402

EXACT = ('Box', 'Box3', 'Valence5', 'Valence6', 'Valence7', 'Valence8')


def dense(table, grips):
    out = np.zeros((len(table.Rows), grips))
    for index, row in enumerate(table.Rows):
        for grip, value in row:
            out[index, grip] = value
    return out


def frames_of(surface):
    if IsCompound(surface):
        return []
    graph = ReadGraph(surface)
    shape = CappedLayout(surface)
    scale = KnotScale(surface)
    levels = CapPoints(graph)
    plans = FacePlans(graph, shape, scale, levels)
    return [RegionFrames(graph, plan, scale, levels) for plan in plans]


def cap_places(frames):
    """Every final face place whose row comes from a cap frame (own-frame caps refined by insertion)."""
    return {(frame.Region, r, c) for region in frames for frame in region for r, c in frame.Places}


def frame_solve_hook(surface, faces, points=None):
    """Solve Fusion's own-frame cap rows from its face poles: every final place in a frame is the
    insertion mix of own-frame rows; non-key own-frame rows come from netref, the key rows are
    least squares unknowns.  Reports the worst fit residual and the worst disagreement between
    two frames (regions) that answer the same spoke key.  With grip points (probe saves in xyz)
    the solve runs in xyz and the hook is only good for its residual and clash numbers."""
    if IsCompound(surface):
        return netref_fill, 0.0, (0.0, 0, 0)
    graph = ReadGraph(surface)
    shape = CappedLayout(surface)
    scale = KnotScale(surface)
    levels = CapPoints(graph)
    plans = FacePlans(graph, shape, scale, levels)
    net = MeshLevels(MeshFromCage(surface, graph), max(levels.values(), default=0) + 1)
    grips = len(surface.Grips)
    width = grips if points is None else 3
    answers, worst, clash, owner, shared = {}, 0.0, 0.0, {}, [0, 0]
    for plan in plans:
        grid = faces[plan.Region][2]
        if grid.shape[:2] != (len(plan.FullV) - 4, len(plan.FullU) - 4):
            worst = float("inf")
            continue
        for frame in RegionFrames(graph, plan, scale, levels):
            keys = sorted(frame.Keys)
            spot = {place: index for index, place in enumerate(keys)}
            places = sorted(frame.Places)
            lhs = np.zeros((len(places), len(keys)))
            rhs = np.array([grid[r, c][:width] for r, c in places], dtype=float).reshape(len(places), width)
            cache = {}
            for index, (r, c) in enumerate(places):
                for inner, weight_v in frame.MixV[r].items():
                    for outer, weight_u in frame.MixU[c].items():
                        weight = float(weight_v * weight_u)
                        if (inner, outer) in spot:
                            lhs[index, spot[(inner, outer)]] += weight
                            continue
                        if (inner, outer) not in cache:
                            row = np.zeros(grips)
                            for grip, value in BaseRow(frame, {}, (net, plan, scale), (inner, outer)).items():
                                row[grip] = value
                            cache[(inner, outer)] = row if points is None else row @ points
                        rhs[index] -= weight * cache[(inner, outer)]
            solved = np.linalg.lstsq(lhs, rhs, rcond=None)[0]
            worst = max(worst, float(np.abs(lhs @ solved - rhs).max(initial=0.0)))
            mine = answers.setdefault(frame.Vertex, {})
            sign = sorted((SectorKnots(plan.FullU, use.PointU, use.SignU), SectorKnots(plan.FullV, use.PointV, use.SignV))
                          for use in frame.Uses)
            sign = sorted(axis for pair in sign for axis in pair)
            for place, index in spot.items():
                key = frame.Keys[place]
                if key in mine:
                    clash = max(clash, float(np.abs(mine[key] - solved[index]).max()))
                    shared[0] += 1
                    shared[1] += owner[(frame.Vertex, key)] != sign
                else:
                    mine[key] = solved[index]
                    owner[(frame.Vertex, key)] = sign
    rows = {vertex: {key: {grip: float(value) for grip, value in enumerate(row) if abs(value) > 1e-15}
                     for key, row in found.items()} for vertex, found in answers.items()}

    def inner(request):
        return rows.get(request.Vertex, {})
    return inner, worst, (clash, *shared)


def recording(hook, seen):
    def inner(request):
        seen.append(request)
        return hook(request)
    return inner


def netref_fill(request):
    """Non-cap checks only: hand back the netref row (or nothing) for every cap key."""
    return {key: dict(request.Reference.get(key, {})) for key in request.Unknown}


def limit_errors(seen, fusion, points, grips):
    """Worst gap between each cap's Limit row and the nearest Fusion point row."""
    worst = 0.0
    for request in seen:
        row = np.zeros(grips)
        for grip, value in request.Limit.items():
            row[grip] = value
        worst = max(worst, min(float(np.abs(fusion[p] - row).max()) for p in points))
    return worst


def face_errors(table, rows, faces, skip, grips=None):
    worst = 0.0
    for face in table.Faces:
        count_u = sum(k.Count for k in face.KnotsU) - 2
        mine = rows[list(face.Poles)].reshape(-1, count_u, rows.shape[1])
        theirs = faces[face.FaceIndex][2]
        knots_u = [(round(k.Value, 9), k.Count) for k in face.KnotsU]
        if knots_u != [(round(a, 9), c) for a, c in faces[face.FaceIndex][0]] or mine.shape[:2] != theirs.shape[:2]:
            return float('inf')
        for r in range(mine.shape[0]):
            for c in range(mine.shape[1]):
                if (face.FaceIndex, r, c) in skip:
                    continue
                if grips is None:
                    err = np.abs(mine[r, c] - theirs[r, c]).max()
                else:
                    err = np.abs(mine[r, c] @ grips - theirs[r, c, :3]).max()
                worst = max(worst, float(err))
    return worst


def check_old(label):
    surface = old_surface(label)
    table = read_tables()[label]
    faces, rows = table_faces(table)
    seen = []
    start = time.time()
    mine = BuildTable(surface, recording(netref_fill, seen))
    took = time.time() - start
    grips = len(surface.Grips)
    frames = frames_of(surface)
    noncap = face_errors(mine, dense(mine, grips), faces, cap_places(frames))
    hook, residual, clash = frame_solve_hook(surface, faces)
    whole = BuildTable(surface, hook)
    whole_rows = dense(whole, grips)
    body = face_errors(whole, whole_rows, faces, set())
    fusion = table_matrix(table)
    # curve and point order follows CappedShape, the old tables follow the old layout: match as sets
    curve = 0.0
    for right in table['Curves']:
        options = [float(np.abs(whole_rows[list(left.Poles)] - fusion[right[2]]).max())
                   for left in whole.Curves
                   if list(left.Multiplicity) == list(right[1]) and len(left.Poles) == len(right[2])
                   and np.allclose(left.Knots, right[0])]
        curve = max(curve, min(options, default=float('inf')))
    point = 0.0
    for right in table['Points']:
        point = max(point, min(float(np.abs(whole_rows[left] - fusion[right]).max()) for left in whole.Points))
    print('%-12s non-cap %.2e | whole faces %.2e curves %.2e (%d/%d) points %.2e | caps %d frame fit %.1e clash %.1e over %d shared keys (%d differently knotted) | limit %.2e | %.1fs' % (
        label, noncap, body, curve, len(whole.Curves), len(table['Curves']), point, len(cap_places(frames)), residual, *clash,
        limit_errors(seen, fusion, table['Points'], grips), took))


def check_probe(name, surface=None, faces=None):
    if surface is None:
        surface = general_surface(name)
        faces, _ = general_saved(name)
    seen = []
    start = time.time()
    mine = BuildTable(surface, recording(netref_fill, seen))
    took = time.time() - start
    grips = grip_array(surface)[:, :3]
    frames = frames_of(surface)
    noncap = face_errors(mine, dense(mine, len(grips)), faces, cap_places(frames), grips)
    _, residual, clash = frame_solve_hook(surface, faces, grips)
    print('%-12s non-cap %.2e | faces %d curves %d points %d | caps %d frame fit %.1e clash %.1e over %d shared keys (%d differently knotted) | %.1fs' % (
        name, noncap, len(mine.Faces), len(mine.Curves), len(mine.Points), len(cap_places(frames)), residual, *clash,
        took))


def main():
    args = sys.argv[1:]
    if args[:1] == ['--pair']:
        surface = ReadTspline(Path(args[1]).read_bytes())
        faces, _ = saved_faces(args[2])
        check_probe(Path(args[1]).stem, surface, faces)
        return
    for name in args or list(EXACT) + [name for name in GENERAL]:
        try:
            if name in OLD_LABELS:
                check_old(name)
            else:
                check_probe(name)
        except Exception as error:  # research: report and continue
            print('%-12s ERROR %r' % (name, error))


if __name__ == '__main__':
    main()
