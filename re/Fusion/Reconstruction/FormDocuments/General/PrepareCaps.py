"""Cap prisms: closed cages with two isolated extraordinary points of one valence.

Each cage is a prism whose top and bottom caps are discs of n sectors with m x m quads.
The disc centres have valence n; the sector far corners have valence 3 and sit m cells
away, like the corners of the Box3 control. Grips get seeded noise so that a few cages
of one valence determine the cap response by least squares.
"""
import hashlib
import json
import math
import random
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from GeneralCages import ROOT, closed
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/General/Caps'
MORE = len(sys.argv) > 1
SIDES = tuple(int(a) for a in sys.argv[1].split(',')) if MORE else (3, 5, 6, 7, 8)
PLAN = ROOT / ('re/Fusion/LocalOracle/FormDocuments/General/CapPrismsMore.json' if MORE else 're/Fusion/LocalOracle/FormDocuments/General/CapPrisms.json')


def cap_prism(sides, cells=3, rows=2, radius=1.5, height=1.2, noise=0.08, seed='x'):
    rng = random.Random(seed)
    points = []

    def add(p):
        points.append(p)
        return len(points) - 1

    def disc(z, flip):
        dirs = [(math.cos(2 * math.pi * k / sides), math.sin(2 * math.pi * k / sides)) for k in range(sides)]
        centre = add((0.0, 0.0, z))
        spoke = {(k, i): add((radius * i / cells * dirs[k][0], radius * i / cells * dirs[k][1], z * (1 - 0.15 * (i / cells) ** 2))) for k in range(sides) for i in range(1, cells + 1)}
        inner = {}
        for k in range(sides):
            a, b = dirs[k], dirs[(k + 1) % sides]
            for i in range(1, cells + 1):
                for j in range(1, cells + 1):
                    x = radius / cells * (i * a[0] + j * b[0])
                    y = radius / cells * (i * a[1] + j * b[1])
                    r = math.hypot(x, y) / radius
                    inner[(k, i, j)] = add((x, y, z * (1 - 0.15 * r * r)))

        def grid(k, i, j):
            if i == 0 and j == 0:
                return centre
            if j == 0:
                return spoke[(k, i)]
            if i == 0:
                return spoke[((k + 1) % sides, j)]
            return inner[(k, i, j)]
        quads = []
        for k in range(sides):
            for i in range(cells):
                for j in range(cells):
                    q = (grid(k, i, j), grid(k, i + 1, j), grid(k, i + 1, j + 1), grid(k, i, j + 1))
                    quads.append(tuple(reversed(q)) if flip else q)
        ring = []
        for k in range(sides):
            ring += [grid(k, cells, j) for j in range(cells + 1)]
            ring += [grid(k, i, cells) for i in range(cells - 1, 0, -1)]
        return quads, ring

    top, ring_top = disc(height, False)
    bottom, ring_bottom = disc(-height, True)
    rings = [ring_top]
    for level in range(1, rows):
        t = level / rows
        rings.append([add(tuple((1 - t) * points[a][c] + t * points[b][c] for c in range(3))) for a, b in zip(ring_top, ring_bottom)])
    rings.append(ring_bottom)
    side = []
    count = len(ring_top)
    for level in range(rows):
        upper, lower = rings[level], rings[level + 1]
        for t in range(count):
            side.append((upper[t], lower[t], lower[(t + 1) % count], upper[(t + 1) % count]))
    scale = noise * radius / cells
    points = [tuple(c + rng.uniform(-scale, scale) for c in p) for p in points]
    return points, top + side + bottom


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    rows = []
    for sides in SIDES:
        for sample in range(3):
            name = 'CapPrism%d_%d' % (sides, sample)
            points, quads = cap_prism(sides, seed=name)
            surface = closed(points, quads)
            text = EmitTspline(surface)
            if ReadTspline(text) != surface:
                raise RuntimeError('TSM text does not read back')
            path = TARGET / (name + '.tsm')
            path.write_bytes(text)
            valence = {}
            for link in surface.Topology.Links:
                valence[link.VertexIndex] = valence.get(link.VertexIndex, 0) + 1
            counts = {}
            for v in valence.values():
                counts[v] = counts.get(v, 0) + 1
            rows.append({'cage': name, 'tsm_file': str(path.relative_to(ROOT)), 'tsm_sha256': hashlib.sha256(text).hexdigest(), 'grips': len(surface.Grips), 'faces': len(surface.Topology.Faces), 'valence_counts': {str(k): v for k, v in sorted(counts.items())}})
            print(rows[-1])
    report = {'report': 'CapPrismsMoreProbe.json' if MORE else 'CapPrismsProbe.json', 'scope': 'Cap prisms: closed cages whose top and bottom discs have one isolated extraordinary point of valence ' + ', '.join(str(s) for s in SIDES) + ', three seeded grip samples per valence, for least-squares recovery of the cap response', 'python': sys.version.split()[0], 'cages': rows}
    PLAN.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
