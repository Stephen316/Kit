import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from GeneralCages import ROOT, band, box, closed, polycube, prism, sharp_box_edges, torus, warp
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/General'
LSHAPE = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
TSHAPE = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 1, 0)]
STEP = [(0, 0, 0), (1, 0, 0), (1, 0, 1)]


def cages():
    out = {}
    p, q = box(2, 3, 4, (2.0, 2.4, 2.8))
    out['Box234'] = closed(warp(p, 0.05, 'Box234'), q)
    p, q = box(1, 2, 2, (1.4, 2.0, 2.0))
    out['Box122'] = closed(warp(p, 0.04, 'Box122'), q)
    p, q = box(1, 1, 1, (2.0, 1.6, 1.2))
    out['Box111'] = closed(warp(p, 0.04, 'Box111'), q)
    p, q = polycube(LSHAPE, 1.0)
    out['LPrism'] = closed(warp(p, 0.03, 'LPrism'), q)
    p, q = polycube(TSHAPE, 1.0)
    out['TPrism'] = closed(warp(p, 0.03, 'TPrism'), q)
    p, q = polycube(STEP, 1.0)
    out['Step'] = closed(warp(p, 0.03, 'Step'), q)
    p, q = prism(5, 1.1, 1.6, rows=2)
    out['Valence5Tall'] = closed(warp(p, 0.04, 'Valence5Tall'), q)
    p, q = prism(3, 1.1, 1.3)
    out['Valence3Prism'] = closed(warp(p, 0.04, 'Valence3Prism'), q)
    p, q = band(5, 6, 1.1, 1.3)
    out['Mixed56'] = closed(p, q)
    p, q = band(7, 8, 1.1, 1.3)
    out['Mixed78'] = closed(p, q)
    p, q = torus(1.6, 0.6, 8, 6)
    out['Torus86'] = closed(p, q)
    p, q = box(2, 2, 2, (2.0, 2.0, 2.0))
    out['SharpBox'] = closed(warp(p, 0.03, 'SharpBox'), q, sharp_box_edges(p))
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
        rows.append({'cage': name, 'tsm_file': str(path.relative_to(ROOT)), 'tsm_sha256': hashlib.sha256(text).hexdigest(), 'grips': len(surface.Grips), 'faces': len(surface.Topology.Faces), 'valences': sorted(set(valence.values())), 'creased_edges': len(surface.Creases.EdgeIndices) if surface.Creases else 0})
        print(rows[-1])
    report = {'scope': 'New Form cage layouts for the general conversion probe: boxes with other face counts, polycube prisms with valence-5 and valence-6 vertices, a taller valence-5 prism, a triangular prism, the two band cages, a torus without extraordinary vertices and a box with creased cube edges', 'python': sys.version.split()[0], 'cages': rows}
    (TARGET / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
