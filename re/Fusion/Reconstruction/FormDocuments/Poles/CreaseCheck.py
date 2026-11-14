"""Research: knots and non-cap poles of creased cages against Fusion's saves.

Each case is a Kit cage (.tsm) with Fusion's save beside it. Knots come from KnotRule ('spoke'),
poles from PoleRule with the crease-aware subdivision of CreaseLab.

Usage: CreaseCheck.py [--no-corners] cage.tsm save.f3d [cage.tsm save.f3d ...]
       CreaseCheck.py --round RoundOne [--limit N]
"""

import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PoleData import ROOT, grip_array, saved_faces  # noqa: E402
from KnotRule import as_vector, capped_points, cap_levels, predict as knot_predict  # noqa: E402
from PoleRule import predict_face  # noqa: E402
import CreaseLab  # noqa: E402

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import ReadGraph  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedLayout import CappedLayout, KnotScale  # noqa: E402
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline  # noqa: E402

CREASE = ROOT / 're/Fusion/LocalOracle/FormDocuments/Crease'


def knot_diff(surface, faces):
    shape, knots, _ = knot_predict(surface, 'cell')
    scale = KnotScale(surface)
    bad = []
    for region, (ku, kv) in enumerate(knots):
        if region not in faces:
            bad.append((region, 'missing'))
            continue
        fu, fv, _ = faces[region]
        for axis, mine_k, theirs, period in (('U', ku, fu, shape.Periods[region][0]), ('V', kv, fv, shape.Periods[region][1])):
            lo, hi = Fraction(theirs[0][0]) / scale, Fraction(theirs[-1][0]) / scale
            mine = [(round(x * scale, 9), m) for x, m in as_vector(mine_k, lo, hi, period)]
            if mine != [(round(a, 9), c) for a, c in theirs]:
                bad.append((region, axis, mine, theirs))
    return shape, bad


def check(tsm, f3d, use_corners=True):
    surface = ReadTspline(Path(tsm).read_bytes())
    faces, _ = saved_faces(f3d)
    shape, bad = knot_diff(surface, faces)
    graph = ReadGraph(surface)
    scale = KnotScale(surface)
    caps = cap_levels(graph, capped_points(graph))
    _, base, _ = knot_predict(surface, 'none')
    levels = CreaseLab.Levels(CreaseLab.Mesh.from_surface(surface, use_corners), depth=4)
    grips = grip_array(surface)
    worst, missing, count, capcount = 0.0, 0, 0, 0
    where = None
    for region, cells in enumerate(shape.Regions):
        if region not in faces:
            continue
        ku, kv, grid = faces[region]
        if any(entry[0] == region for entry in bad):
            continue
        rows, keys = predict_face(levels, graph, cells, scale, ku, kv, caps, base[region])
        capcount += len(keys)
        for (r, c), row in rows.items():
            if row is None:
                missing += 1
                continue
            count += 1
            point = row @ grips[:, :3]
            if grid.shape[2] == 4:
                point = point
            err = float(np.abs(point - grid[r, c, :3]).max())
            if err > worst:
                worst, where = err, (region, r, c)
    return len(shape.Regions), len(faces), bad, worst, where, count, missing, capcount


def main():
    args = sys.argv[1:]
    use_corners = True
    if args[:1] == ['--no-corners']:
        use_corners, args = False, args[1:]
    pairs = []
    if args[:1] == ['--round']:
        limit = int(args[3]) if args[2:3] == ['--limit'] else 1000
        for folder in args[1].split(','):
            for tsm in sorted((CREASE / folder).glob('*.tsm'))[:limit]:
                f3d = CREASE / 'tmp' / folder / (tsm.stem + '.f3d')
                if f3d.exists():
                    pairs.append((tsm, f3d))
    else:
        pairs = list(zip(args[0::2], args[1::2]))
    for tsm, f3d in pairs:
        try:
            regions, saved, bad, worst, where, count, missing, capcount = check(tsm, f3d, use_corners)
        except Exception as error:  # research: report and continue
            print('%-22s ERROR %r' % (Path(tsm).stem, error))
            continue
        print('%-22s regions %d/%d knots %s  non-cap worst %.3e at %s poles %d missing %d cap %d' % (
            Path(tsm).stem, regions, saved, 'MATCH' if not bad else 'DIFF %d' % len(bad), worst, where, count, missing, capcount))
        for entry in bad[:3]:
            print('    ', entry)


if __name__ == '__main__':
    main()
