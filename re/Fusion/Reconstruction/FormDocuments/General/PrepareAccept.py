"""Research preparation: Kit Form documents for the general conversion acceptance run.

Every converted body comes from the production ConvertForm on the cage alone. No stencil table,
shape table or Fusion save reaches it. Old layouts take the cage that Fusion stored in their old
control archives. Probe layouts take the General probe TSM files; their non-cap poles were held out
from the knot rule fit except where PoleNotes.md says otherwise. Held-out layouts take the Kit-authored TSM files in General/HeldOut. Cages that
the general rules refuse are listed with the refusal message and get no document.

Run with /opt/homebrew/bin/python3.14 and src on PYTHONPATH (method-93 archives need 3.14).
Usage: PrepareAccept.py [names...]
"""

import hashlib
import io
import json
import sys
import time
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(BASE.parent / 'Topology'))
from SavedBodies import GENERAL, GENERAL_DIR, OLD_SAVES  # noqa: E402

from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import ConvertForm  # noqa: E402
from convert.formats.Fusion.DocumentCodec.Form.EmitFormDoc import EmitFormDoc  # noqa: E402
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument  # noqa: E402
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline  # noqa: E402
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline  # noqa: E402

TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/General/Accept'
HELD = ROOT / 're/Fusion/LocalOracle/FormDocuments/General/HeldOut'
OLD = ('Box', 'Box3', 'CreasedBox', 'CreasedPlane', 'Valence5', 'Valence6', 'Valence7', 'Valence8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def cages():
    out = []
    for name in OLD:
        source = OLD_SAVES[name]
        cage = ReadDocument((ROOT / source).read_bytes()).Forms[0].Surface
        out.append((name, 'old', source, cage))
    for name in GENERAL:
        path = GENERAL_DIR / (name + '.tsm')
        out.append((name, 'probe', str(path.relative_to(ROOT)), ReadTspline(path.read_bytes())))
    for path in sorted(HELD.glob('*.tsm')):
        out.append((path.stem, 'held-out', str(path.relative_to(ROOT)), ReadTspline(path.read_bytes())))
    return out


def valences(cage):
    count = {}
    for link in cage.Topology.Links:
        count[link.VertexIndex] = count.get(link.VertexIndex, 0) + 1
    return sorted(set(count.values()))


def write_case(name, group, source, cage):
    row = {'case': name, 'group': group, 'cage_source': source, 'grips': len(cage.Grips), 'valences': valences(cage), 'creased_edges': len(cage.Creases.EdgeIndices) if cage.Creases else 0, 'weighted_grips': sum(1 for grip in cage.Grips if grip.Weight != 1.0)}
    start = time.time()
    try:
        body = ConvertForm(cage)
    except ValueError as error:
        row['status'] = 'refused'
        row['refusal'] = str(error)
        return row
    row['convert_seconds'] = round(time.time() - start, 2)
    text = EmitTspline(cage)
    if ReadTspline(text) != cage:
        raise RuntimeError(f'{name}: TSM text does not read back')
    payload = EmitFormDoc(FormSpec('Kit ' + name, cage, body))
    model = ReadDocument(payload)
    if len(model.Forms) != 1 or model.Forms[0].Surface != cage:
        raise RuntimeError(f'{name}: written Form cage differs')
    (TARGET / (name + '.tsm')).write_bytes(text)
    (TARGET / (name + '.f3d')).write_bytes(payload)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        parts = sorted(entry.split('/', 1)[-1] for entry in archive.namelist() if not entry.endswith('/'))
    row.update({
        'status': 'prepared',
        'faces': len(body.Faces),
        'edges': len(body.Edges),
        'vertices': len(body.PointsCm),
        'rational_faces': sum(1 for face in body.Faces if face.Surface.Cache.Weights),
        'tsm_file': str((TARGET / (name + '.tsm')).relative_to(ROOT)),
        'tsm_sha256': digest(text),
        'document_file': str((TARGET / (name + '.f3d')).relative_to(ROOT)),
        'document_sha256': digest(payload),
        'document_parts': parts,
    })
    return row


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    wanted = set(sys.argv[1:])
    rows = []
    for name, group, source, cage in cages():
        if wanted and name not in wanted:
            continue
        rows.append(write_case(name, group, source, cage))
        print(json.dumps({key: rows[-1].get(key) for key in ('case', 'group', 'status', 'refusal', 'faces', 'edges', 'vertices', 'rational_faces')}))
    report = {
        'scope': 'Kit Form documents whose converted body comes from the general ConvertForm rules on the cage alone; old layouts and held-out layouts',
        'python': sys.version.split()[0],
        'rows': rows,
    }
    (TARGET / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
