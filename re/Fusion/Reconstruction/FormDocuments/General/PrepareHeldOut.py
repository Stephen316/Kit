"""Held-out Form cage layouts for accepting the general conversion.

No rule in src was fitted on these layouts. They cover valence 3, 5, 6 and 7 points, a crease
loop, a weighted cage and a torus. HeldCreaseCross, HeldCreaseBands and HeldCreaseSlices were added later
to test the seam pcurve rule that HeldCreaseLoop and HeldCreaseRing suggested. HeldInterval7 was added
later to test the uniform knot interval rule on a new layout. Each cage gets seeded warp so no symmetry hides an error.
"""
import hashlib
import json
import random
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from GeneralCages import ROOT, band, box, closed, prism, sharp_box_edges, torus, warp
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.Model.CreaseData import CreaseData
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/General/HeldOut'
PLAN = TARGET / 'HeldOut.json'


def loop_edges(points, ring, *more):
    rings = (ring,) + more

    def pick(surface):
        topology = surface.Topology
        edges = set()
        for link in topology.Links:
            a = link.VertexIndex
            b = topology.Links[link.NextLink].VertexIndex
            if any(a in each and b in each for each in rings):
                edges.add(link.EdgeIndex)
        return edges, set()
    return pick


def weighted(surface, seed, count):
    generator = random.Random(seed)
    grips = list(surface.Grips)
    for index in generator.sample(range(len(grips)), count):
        grips[index] = replace(grips[index], Weight=round(generator.uniform(0.6, 1.8), 6))
    return replace(surface, Grips=tuple(grips))


def intervals(surface, value):
    edges = tuple(replace(edge, KnotInterval=value) for edge in surface.Topology.Edges)
    return replace(surface, Topology=replace(surface.Topology, Edges=edges))


def cages():
    out = {}
    p, q = band(6, 7, 1.2, 1.4)
    out['HeldBand67'] = closed(warp(p, 0.04, 'HeldBand67'), q)
    p, q = prism(5, 1.2, 1.5, rows=3)
    out['HeldPrism5'] = closed(warp(p, 0.04, 'HeldPrism5'), q)
    p, q = prism(3, 1.0, 1.6, rows=2)
    out['HeldPrism3'] = closed(warp(p, 0.04, 'HeldPrism3'), q)
    p, q = torus(1.7, 0.55, 7, 5, big=1.7, small=0.55)
    out['HeldTorus75'] = closed(warp(p, 0.04, 'HeldTorus75'), q)
    p, q = torus(1.5, 0.5, 9, 6, big=1.5, small=0.5)
    ring = set(range(0, 6))
    out['HeldCreaseLoop'] = closed(warp(p, 0.03, 'HeldCreaseLoop'), q, loop_edges(p, ring))
    p, q = prism(6, 1.1, 1.2, rows=2)
    out['HeldWeighted6'] = weighted(closed(warp(p, 0.04, 'HeldWeighted6'), q), 'HeldWeighted6', 9)
    p, q = box(1, 1, 3, (1.6, 1.8, 3.0))
    out['HeldBox113'] = closed(warp(p, 0.04, 'HeldBox113'), q)
    p, q = torus(1.6, 0.5, 8, 6, big=1.6, small=0.5)
    ring = {index * 6 for index in range(8)}
    out['HeldCreaseRing'] = closed(warp(p, 0.03, 'HeldCreaseRing'), q, loop_edges(p, ring))
    p, q = torus(1.5, 0.6, 7, 5, big=1.5, small=0.6)
    out['HeldWeightedTorus'] = weighted(closed(warp(p, 0.04, 'HeldWeightedTorus'), q), 'HeldWeightedTorus', 6)
    p, q = torus(1.6, 0.5, 8, 7, big=1.6, small=0.5)
    loop, ring = set(range(0, 7)), {index * 7 for index in range(8)}
    out['HeldCreaseCross'] = closed(warp(p, 0.03, 'HeldCreaseCross'), q, loop_edges(p, loop, ring))
    p, q = torus(1.6, 0.5, 8, 6, big=1.6, small=0.5)
    first, second = {index * 6 for index in range(8)}, {index * 6 + 3 for index in range(8)}
    out['HeldCreaseBands'] = closed(warp(p, 0.03, 'HeldCreaseBands'), q, loop_edges(p, first, second))
    p, q = torus(1.6, 0.5, 8, 6, big=1.6, small=0.5)
    out['HeldCreaseSlices'] = closed(warp(p, 0.03, 'HeldCreaseSlices'), q, loop_edges(p, set(range(0, 6)), set(range(24, 30))))
    p, q = box(3, 2, 2, (2.4, 2.0, 1.8))
    out['HeldWeightedSharp'] = weighted(closed(warp(p, 0.03, 'HeldWeightedSharp'), q, sharp_box_edges(p)), 'HeldWeightedSharp', 5)
    p, q = prism(7, 1.2, 1.4, rows=2)
    out['HeldInterval7'] = intervals(closed(warp(p, 0.04, 'HeldInterval7'), q), 3.0)
    return out


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, surface in cages().items():
        text = EmitTspline(surface)
        if ReadTspline(text) != surface:
            raise RuntimeError('TSM text does not read back')
        path = TARGET / (name + '.tsm')
        path.write_bytes(text)
        valence = {}
        for link in surface.Topology.Links:
            valence[link.VertexIndex] = valence.get(link.VertexIndex, 0) + 1
        rows.append({'cage': name, 'tsm_file': str(path.relative_to(ROOT)), 'tsm_sha256': hashlib.sha256(text).hexdigest(), 'grips': len(surface.Grips), 'faces': len(surface.Topology.Faces), 'valences': sorted(set(valence.values())), 'creased_edges': len(surface.Creases.EdgeIndices) if surface.Creases else 0, 'weighted_grips': sum(1 for grip in surface.Grips if grip.Weight != 1.0)})
        print(rows[-1])
    report = {'report': 'HeldOutProbe.json', 'scope': 'Held-out Form cage layouts for the general conversion: a 6/7 band, a 3-row pentagonal prism, a 2-row triangular prism, a 7 x 5 torus, a 9 x 6 torus with one creased meridian loop, a hexagonal prism with weighted grips, a 1 x 1 x 3 box, an 8 x 6 torus with one creased parallel loop, a 7 x 5 torus with weighted grips an 8 x 7 torus with a creased meridian and a creased parallel loop that cross, two 8 x 6 tori cut into two faces by two creased parallels or two creased meridians, a 3 x 2 x 2 box with sharp edges and five weighted grips, and a 2-row heptagonal prism with every knot interval 3', 'python': sys.version.split()[0], 'cages': rows}
    PLAN.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
