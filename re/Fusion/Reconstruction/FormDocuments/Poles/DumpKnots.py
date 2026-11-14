"""Research: print every converted face's knot vectors next to its cage cells.

For each region the cells (cage face, offset, turn) and the valence of each cell corner
are listed, so the knot rule can be read against the extraordinary points.
Usage: DumpKnots.py [names...]  (old labels read FormStencils, others read General saves)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PoleData import GENERAL, OLD_LABELS, general_saved, general_surface, old_surface, read_tables, table_faces  # noqa: E402

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import ReadGraph  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedLayout import CappedLayout  # noqa: E402


def show(name):
    if name in OLD_LABELS:
        surface = old_surface(name)
        faces, _ = table_faces(read_tables()[name])
    else:
        surface = general_surface(name)
        faces, _ = general_saved(name)
    graph = ReadGraph(surface)
    shape = CappedLayout(surface)
    print('==', name, 'faces', len(surface.Topology.Faces), 'regions', len(shape.Regions), 'periods', shape.Periods)
    for region, cells in enumerate(shape.Regions):
        ku, kv, grid = faces[region]
        print(' region', region, 'poles', grid.shape[:2])
        print('   U', [(round(a, 4), c) for a, c in ku])
        print('   V', [(round(a, 4), c) for a, c in kv])
        for cell in cells:
            loop = graph.Loops[cell.Face]
            vals = [len(graph.Fans[graph.Links[link].VertexIndex]) for link in loop]
            inside = [graph.Inside[graph.Links[link].VertexIndex] for link in loop]
            print('   cell face', cell.Face, 'offset', cell.Offset, 'valences', vals, 'inside', inside)


def main():
    names = sys.argv[1:] or list(OLD_LABELS) + list(GENERAL)
    for name in names:
        show(name)


if __name__ == '__main__':
    main()
