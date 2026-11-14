import hashlib
import json
import math
import random
import shutil
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.SwapFormCage import SwapFormCage
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/StencilAccept'
OUTPUT = TARGET / 'General'
PROBES = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil/tmp'
CARRIERS = {
    'Box': 're/Fusion/LocalOracle/TSpline/Box.f3d',
    'SymmetricBox': 're/Fusion/LocalOracle/TSpline/SymmetricBox.f3d',
    'CreasedPlane': 're/Fusion/LocalOracle/TSplineCodec/vendor_PlaneCreasedControl.f3d',
    'CreasedBox': 're/Fusion/LocalOracle/TSplineCodec/vendor_BoxCreasedControl.f3d',
}
PROBED = ('Valence5', 'Valence6', 'Box3', 'Valence8')
SPREAD = {'Box': 0.25, 'CreasedPlane': 0.03, 'CreasedBox': 0.2, 'Valence5': 0.2, 'Valence6': 0.2, 'Box3': 0.12, 'Valence8': 0.12}
WARP = {'CreasedPlane': 0.01, 'Box3': 0.03, 'Valence8': 0.03}


def fresh(name, surface):
    generator = random.Random(name + 'Fresh')
    spread = SPREAD[name]
    warp = WARP.get(name, 0.05)
    grips = []
    for grip in surface.Grips:
        x, y, z = grip.CoordX, grip.CoordY, grip.CoordZ
        moved = (x + warp * math.sin(1.3 * y) + generator.uniform(-spread, spread), y + warp * math.cos(1.1 * z) + generator.uniform(-spread, spread), z + warp * math.sin(0.9 * x) + generator.uniform(-spread, spread))
        grips.append(replace(grip, CoordX=round(moved[0], 9), CoordY=round(moved[1], 9), CoordZ=round(moved[2], 9)))
    return replace(surface, Grips=tuple(grips))


def mirrored(surface):
    grips = []
    for grip in surface.Grips:
        u, y, z = grip.CoordX - 0.15, grip.CoordY, grip.CoordZ
        moved = (grip.CoordX + 0.12 * u * math.cos(y), y + 0.1 * math.cos(u) * math.sin(z), z + 0.13 * math.cos(u) * math.cos(y))
        grips.append(replace(grip, CoordX=round(moved[0], 12), CoordY=round(moved[1], 12), CoordZ=round(moved[2], 12)))
    return replace(surface, Grips=tuple(grips))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    (TARGET / 'Cases').mkdir(parents=True, exist_ok=True)
    (TARGET / 'Carriers').mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    carriers = dict(CARRIERS)
    for name in PROBED:
        copied = TARGET / 'Carriers' / (name + '.f3d')
        source = PROBES / name / 'Base.f3d'
        if not copied.exists():
            shutil.copyfile(source, copied)
        carriers[name] = str(copied.relative_to(ROOT))
    rows = []
    for name, relative in carriers.items():
        carrier = ROOT / relative
        model = ReadDocument(carrier.read_bytes())
        base = model.Forms[0].Surface
        case = name + ('Edited' if name == 'SymmetricBox' else 'Fresh')
        surface = mirrored(base) if name == 'SymmetricBox' else fresh(name, base)
        text = EmitTspline(surface)
        if ReadTspline(text) != surface:
            raise RuntimeError('TSM text does not read back')
        tsm = TARGET / 'Cases' / (case + '.tsm')
        tsm.write_bytes(text)
        document = OUTPUT / (case + 'Kit.f3d')
        try:
            payload = EmitParsed(SwapFormCage(model, ReadTspline(text)))
        except ValueError as error:
            rows.append({'case': case, 'table': name, 'carrier_file': relative, 'carrier_sha256': digest(carrier), 'tsm_file': str(tsm.relative_to(ROOT)), 'tsm_sha256': digest(tsm), 'status': 'refused', 'refusal': str(error), 'grips': len(surface.Grips)})
            print(case, 'refused', error)
            continue
        if ReadDocument(payload).Forms[0].Surface != ReadTspline(text):
            raise RuntimeError('Kit document does not read back')
        document.write_bytes(payload)
        rows.append({'case': case, 'table': name, 'carrier_file': relative, 'carrier_sha256': digest(carrier), 'tsm_file': str(tsm.relative_to(ROOT)), 'tsm_sha256': digest(tsm), 'document_file': str(document.relative_to(ROOT)), 'document_sha256': digest(document), 'status': 'prepared', 'grips': len(surface.Grips)})
        print(case, len(surface.Grips), digest(document)[:12])
    report = {'scope': 'Fresh cages for every packaged stencil table, not used to fit: random and warped grips, and a mirror-preserving edit of the symmetric box. Kit documents are SwapFormCage results on the Fusion carrier archive. Carriers are copied once and then kept, because the committed copies are scrubbed. A cage that SwapFormCage refuses gets no document. The cages stay in Cases; the documents of the general rules go to General, and Cases keeps the first run of the stencil tables', 'python': sys.version.split()[0], 'rows': rows}
    (OUTPUT / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
