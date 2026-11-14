"""Research: for one region, list each boundary cell side, the cell across, and the knots
the neighbouring face (Fusion's own knots) puts across that side, against this face's knots.

Usage: KnotSources.py Name region
"""

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from KnotRule import CORNERS, FaceMap, cell_owner, fusion_faces  # noqa: E402

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import ReadGraph  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedLayout import CappedLayout, KnotScale  # noqa: E402


def crossing(faces, region, fm, side, scale):
    ku, kv, _ = faces[region]
    a = fm.to_face(*CORNERS[side])
    b = fm.to_face(*CORNERS[(side + 1) % 4])
    out = []
    if a[0] != b[0]:
        for u, m in ku:
            x = (Fraction(u) / scale - Fraction(a[0])) / (Fraction(b[0]) - Fraction(a[0]))
            if 0 < x < 1:
                out.append((x, m))
    else:
        for v, m in kv:
            x = (Fraction(v) / scale - Fraction(a[1])) / (Fraction(b[1]) - Fraction(a[1]))
            if 0 < x < 1:
                out.append((x, m))
    return out


def main():
    name, region = sys.argv[1], int(sys.argv[2])
    surface, faces = fusion_faces(name)
    graph = ReadGraph(surface)
    shape = CappedLayout(surface)
    scale = KnotScale(surface)
    owner = cell_owner(shape, 1)
    print(name, 'region', region, 'U', faces[region][0], 'V', faces[region][1])
    for cell in shape.Regions[region]:
        fm = FaceMap(cell, 1)
        loop = graph.Loops[cell.Face]
        vals = [len(graph.Fans[graph.Links[link].VertexIndex]) for link in loop]
        print(' cell', cell.Face, 'corners at', [fm.to_face(*c) for c in CORNERS], 'valences', vals)
        for side, link in enumerate(loop):
            across = graph.Links[link].Opposite
            other = graph.Links[across].FaceIndex
            o_region, o_fm = owner[other]
            if o_region == region:
                continue
            o_side = graph.Loops[other].index(across)
            mine = crossing(faces, region, fm, side, scale)
            theirs = [(1 - x, m) for x, m in crossing(faces, o_region, o_fm, o_side, scale)]
            o_vals = [len(graph.Fans[graph.Links[link2].VertexIndex]) for link2 in graph.Loops[other]]
            print('   side', side, 'face', fm.to_face(*CORNERS[side]), '->', fm.to_face(*CORNERS[(side + 1) % 4]),
                  '| across region', o_region, 'cell', other, 'val', o_vals,
                  '| mine', sorted((str(x), m) for x, m in mine), '| theirs', sorted((str(x), m) for x, m in theirs))


if __name__ == '__main__':
    main()
