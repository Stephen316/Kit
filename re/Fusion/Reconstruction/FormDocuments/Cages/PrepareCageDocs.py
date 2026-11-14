"""Research preparation: source-free Form documents from a cage alone.

Each document is written by the production EmitFormDoc with the body that
the production ConvertForm derives from the cage: stencil tables and body
shapes for stencil layouts, ConvertGrid and GridBody for plain grids. The
cages are the fresh stencil acceptance cages, which took no part in any
fit, a warped plane grid, and bent, twisted and sheared copies of the two
vendor creased cages. A bent crease makes ClassifyEdges mark the crease edge
unknown instead of tangent. The archives are read only for their cages.
"""

import hashlib
import json
import math
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 're/Fusion/Reconstruction/FormDocuments/Tables'))
sys.path.insert(0, str(BASE.parent / 'Stencil'))
from StencilCheck import compare, form_entities
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import ConvertForm
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import ConvertCage
from ReadShapes import ReadShapes
from StencilKey import StencilKey
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Form.EmitFormDoc import EmitFormDoc
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

ORACLE = 're/Fusion/LocalOracle/FormDocuments/'
WORK = ROOT / ORACLE / 'CageDocuments'
FRESH = ('BoxFresh', 'SymmetricBoxEdited', 'CreasedPlaneFresh', 'CreasedBoxFresh', 'Valence5Fresh', 'Valence6Fresh', 'Box3Fresh', 'Valence8Fresh')
PLANE = ORACLE + 'Grid/Primitives/Plane2x5.f3d'
VENDOR = 're/Fusion/LocalOracle/TSplineCodec/'
CREASED = {
    'CreasedPlaneBent': ('vendor_PlaneCreasedControl.f3d', lambda grip: replace(grip, CoordZ=grip.CoordZ + 0.25 * grip.CoordX ** 2)),
    'CreasedPlaneSagged': ('vendor_PlaneCreasedControl.f3d', lambda grip: replace(grip, CoordZ=grip.CoordZ - 0.3 * (grip.CoordX - 0.15) ** 2)),
    'CreasedPlaneTwisted': ('vendor_PlaneCreasedControl.f3d', lambda grip: replace(grip, CoordZ=grip.CoordZ + 0.15 * grip.CoordX * (grip.CoordY - 2.4))),
    'CreasedBoxBent': ('vendor_BoxCreasedControl.f3d', lambda grip: replace(grip, CoordZ=grip.CoordZ + 0.12 * grip.CoordX ** 2)),
    'CreasedBoxSheared': ('vendor_BoxCreasedControl.f3d', lambda grip: replace(grip, CoordX=grip.CoordX + 0.1 * grip.CoordZ, CoordY=grip.CoordY + 0.05 * math.sin(1.7 * grip.CoordX))),
}


def warp(grip):
    x, y, z = grip.CoordX, grip.CoordY, grip.CoordZ
    return replace(grip, CoordX=x + 0.06 * math.sin(1.7 * y), CoordY=y + 0.05 * math.cos(2.1 * x), CoordZ=z + 0.35 * math.sin(1.3 * x) * math.cos(0.9 * y))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(case, cage, tsm_file):
    body = ConvertForm(cage)
    payload = EmitFormDoc(FormSpec('Kit ' + case, cage, body))
    model = ReadDocument(payload)
    if len(model.Forms) != 1 or model.Forms[0].Surface != cage:
        raise RuntimeError(case + ': written cage differs')
    if ReadDocument(EmitParsed(model)) != model:
        raise RuntimeError(case + ': written document does not round-trip')
    target = WORK / (case + '.f3d')
    target.write_bytes(payload)
    row = {'case': case, 'body': 'CageBody' if StencilKey(cage) in ReadShapes() else 'GridBody', 'grips': len(cage.Grips), 'faces': len(body.Faces), 'edges': len(body.Edges), 'vertices': len(body.PointsCm), 'unknown_edges': sum(edge.Convexity == 'unknown' for edge in body.Edges)}
    row.update({'tsm_file': tsm_file, 'tsm_sha256': digest((ROOT / tsm_file).read_bytes()), 'document_file': str(target.relative_to(ROOT)), 'document_sha256': digest(payload)})
    if row['body'] == 'CageBody':
        check = compare(ConvertCage(cage), form_entities(target))
        row['stencil_gap_cm'] = max(check['surface_max'], check['curve_max'], check['point_max'])
        row['stencil_layout_equal'] = check['layout_equal'] and check['jumps_equal']
    return row


def derived(case, cage):
    text = EmitTspline(cage)
    if ReadTspline(text) != cage:
        raise RuntimeError(case + ' TSM does not read back')
    (WORK / (case + '.tsm')).write_bytes(text)
    return write(case, cage, ORACLE + 'CageDocuments/' + case + '.tsm')


def main():
    WORK.mkdir(exist_ok=True)
    rows = []
    for case in FRESH:
        tsm_file = ORACLE + 'StencilAccept/Cases/' + case + '.tsm'
        rows.append(write(case, ReadTspline((ROOT / tsm_file).read_bytes()), tsm_file))
        print(json.dumps(rows[-1]))
    plane = ReadDocument((ROOT / PLANE).read_bytes()).Forms[0].Surface
    rows.append(derived('WarpedPlane2x5', replace(plane, Grips=tuple(warp(grip) for grip in plane.Grips))))
    print(json.dumps(rows[-1]))
    for case, (carrier, move) in CREASED.items():
        cage = ReadDocument((ROOT / (VENDOR + carrier)).read_bytes()).Forms[0].Surface
        rows.append(derived(case, replace(cage, Grips=tuple(move(grip) for grip in cage.Grips))))
        rows[-1]['carrier_file'] = VENDOR + carrier
        print(json.dumps(rows[-1]))
    report = {'scope': 'Source-free Kit Form documents: EmitFormDoc with the body ConvertForm derives from the cage alone, for fresh stencil cages, a warped plane grid and bent, twisted and sheared creased cages', 'python': sys.version.split()[0], 'rows': rows}
    (WORK / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
