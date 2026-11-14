"""Research: print a compound-grip cage (grips, owners, creases) and its exact stencil table
rows as grip combinations, to read the open-grid pole rule.

Usage: PlaneTable.py [label]   (default CreasedPlane)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PoleData import old_surface, read_tables, table_faces  # noqa: E402


def show_row(row):
    parts = ['%g*g%d' % (round(v, 6), g) for g, v in enumerate(row) if abs(v) > 1e-12]
    return '+'.join(parts)


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else 'CreasedPlane'
    surface = old_surface(label)
    topo = surface.Topology
    links = topo.Links
    print('vertices', len(topo.Vertices), 'grips', len(surface.Grips), 'faces', len(topo.Faces))
    for grip, owner in enumerate(surface.Mapping.Owners):
        g = surface.Grips[grip]
        print(' g%d' % grip, 'owner', {k: getattr(owner, k) for k in owner.__dataclass_fields__},
              'xyz', (round(g.CoordX, 3), round(g.CoordY, 3), round(g.CoordZ, 3)))
    for index, face in enumerate(topo.Faces):
        loop, link = [], face.OriginLink
        while True:
            loop.append(links[link].VertexIndex)
            link = links[link].NextLink
            if link == face.OriginLink:
                break
        print(' face', index, loop)
    print(' crease edges', sorted({tuple(sorted((lk.VertexIndex, links[lk.NextLink].VertexIndex)))
                                   for lk in links if lk.EdgeIndex in set(surface.Creases.EdgeIndices)}))
    print(' edge intervals', sorted({e.KnotInterval for e in topo.Edges}))
    faces, _ = table_faces(read_tables()[label])
    for region, (ku, kv, grid) in faces.items():
        print('region', region, 'U', ku, 'V', kv)
        for r in range(grid.shape[0]):
            print('  r%d' % r, ' | '.join(show_row(grid[r, c]) for c in range(grid.shape[1])))


if __name__ == '__main__':
    main()
