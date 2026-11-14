"""Crease caps: cap prisms whose extraordinary points carry creased spokes.

Each cage is a cap prism (PrepareCaps.cap_prism): a closed prism whose top and
bottom discs have one extraordinary point (EP) of valence n at the centre.
On both discs the first `length` edges of some spokes are creased, starting at
the centre. A crease of one spoke ends at the EP (the cap sees one creased
spoke); the far end of the crease is a dart at a regular vertex. Two creased
spokes make the crease pass through the EP. Valence 4 makes the centre a
regular vertex, so its crease end is a dart.

The cages are seeded samples of a few layouts. Fusion's poles at the creased
caps give the cap response on data the rule was not fitted on.
argv: plan name, 'fit' (default), 'more' (more valences for the fit) or 'held' (held-out layouts).
"""
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
PLAN = sys.argv[1] if len(sys.argv) > 1 else 'fit'
sys.argv[1:] = []  # PrepareCaps reads sys.argv at import
from GeneralCages import ROOT, closed
from PrepareCaps import cap_prism
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/General/CreaseCaps'
CELLS = 3
FIT = tuple((n, length, (0,), seed) for n in (3, 4, 5, 6) for length in (1, 2) for seed in range(6))
MORE = tuple((8, length, (0,), seed) for length in (1, 2) for seed in range(1, 5))
HELD = (
    (7, 1, (0,), 0), (7, 2, (0,), 1), (3, 3, (0,), 0), (5, 3, (0,), 0), (8, 2, (0,), 0),
    (5, 2, (0, 2), 0), (6, 2, (0, 3), 0), (6, 1, (0, 2), 0), (4, 2, (0, 2), 0), (3, 2, (0,), 9),
    (7, 2, (0,), 2), (7, 2, (0,), 3), (7, 1, (0,), 4), (5, 1, (0,), 9), (6, 2, (0,), 9),
)


def name_of(n, length, spokes, seed):
    return 'Crease%dL%dS%s_%d' % (n, length, ''.join(str(k) for k in spokes), seed)


def crease_edges(n, length, spokes):
    disc = 1 + n * CELLS + n * CELLS * CELLS
    pairs = set()
    for base in (0, disc):
        for k in spokes:
            path = [base] + [base + 1 + k * CELLS + i for i in range(length)]
            pairs.update(frozenset(pair) for pair in zip(path, path[1:]))

    def pick(surface):
        links = surface.Topology.Links
        edges = {link.EdgeIndex for link in links if frozenset((link.VertexIndex, links[link.NextLink].VertexIndex)) in pairs}
        if len(edges) != len(pairs):
            raise RuntimeError('crease edge missing')
        return edges, ()
    return pick


def main():
    cases = {'fit': FIT, 'more': MORE, 'held': HELD}[PLAN]
    TARGET.mkdir(parents=True, exist_ok=True)
    rows = []
    for n, length, spokes, seed in cases:
        name = name_of(n, length, spokes, seed)
        points, quads = cap_prism(n, cells=CELLS, rows=1, noise=0.2, seed=name)
        surface = closed(points, quads, creases=crease_edges(n, length, spokes))
        text = EmitTspline(surface)
        if ReadTspline(text) != surface:
            raise RuntimeError('TSM text does not read back')
        path = TARGET / (name + '.tsm')
        path.write_bytes(text)
        rows.append({'cage': name, 'tsm_file': str(path.relative_to(ROOT)), 'tsm_sha256': hashlib.sha256(text).hexdigest(), 'grips': len(surface.Grips), 'faces': len(surface.Topology.Faces), 'valence': n, 'crease_length': length, 'creased_spokes': list(spokes)})
    stem = {'fit': 'CreaseCaps', 'more': 'CreaseCapsMore', 'held': 'CreaseCapsHeld'}[PLAN]
    scope = ('Crease caps: cap prisms whose top and bottom extraordinary points carry creased spokes from the centre, '
             + {'fit': 'seeded samples of valence 3 to 6 with one creased spoke of length 1 or 2',
                'more': 'seeded samples of valence 8 with one creased spoke of length 1 or 2',
                'held': 'held-out layouts and seeds'}[PLAN])
    plan = {'report': stem + 'Probe.json', 'scope': scope, 'python': sys.version.split()[0], 'cages': rows}
    (TARGET / (stem + '.json')).write_text(json.dumps(plan, indent=1) + '\n')
    print(len(rows), 'cages ->', TARGET / (stem + '.json'))


if __name__ == '__main__':
    main()
