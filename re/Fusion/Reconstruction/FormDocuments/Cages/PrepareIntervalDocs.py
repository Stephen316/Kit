import json
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))
from PrepareFourthDocs import ORACLE, check, digest, fresh
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import ConvertForm
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Form.EmitFormDoc import EmitFormDoc
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

WORK = ROOT / ORACLE / 'IntervalDocuments'
CASES = {
    'Plane4x4Interval2': ('Sourceless/Plane4x4.tsm', 0.08, 0.2, 2.0),
    'Plane2x5Interval3': ('Sourceless/Plane2x5.tsm', 0.06, 0.15, 3.0),
}


def with_interval(surface, interval):
    edges = tuple(replace(edge, KnotInterval=interval) for edge in surface.Topology.Edges)
    return replace(surface, Topology=replace(surface.Topology, Edges=edges))


def main():
    WORK.mkdir(exist_ok=True)
    rows = []
    for case, (source, spread, warp, interval) in CASES.items():
        base = ReadTspline((ROOT / ORACLE / source).read_bytes())
        cage = with_interval(fresh(case, base, spread, warp, {}), interval)
        text = EmitTspline(cage)
        if ReadTspline(text) != cage:
            raise RuntimeError(case + ' TSM does not read back')
        tsm = WORK / (case + '.tsm')
        tsm.write_bytes(text)
        payload = EmitFormDoc(FormSpec('Kit ' + case, cage, ConvertForm(cage)))
        model = ReadDocument(payload)
        if len(model.Forms) != 1 or model.Forms[0].Surface != cage:
            raise RuntimeError(case + ': written cage differs')
        if ReadDocument(EmitParsed(model)) != model:
            raise RuntimeError(case + ': written document does not round-trip')
        document = WORK / (case + '.f3d')
        document.write_bytes(payload)
        row = {'case': case, 'layout_source': ORACLE + source, 'grips': len(cage.Grips), 'knot_interval': interval, 'weights': {}, 'tsm_file': str(tsm.relative_to(ROOT)), 'tsm_sha256': digest(text), 'document_file': str(document.relative_to(ROOT)), 'document_sha256': digest(payload)}
        body = ConvertForm(cage)
        row['surface_jumps'] = body.Faces[0].Surface.Jumps
        row['knots_u'] = [knot.Value for knot in body.Faces[0].Surface.Cache.KnotsU]
        rows.append(row)
        print(json.dumps(row))
    report = {'scope': 'Source-free Kit Form documents of warped plane grids whose edges all carry one whole-number knot interval above 1, each written by EmitFormDoc from the cage alone', 'python': sys.version.split()[0], 'rows': rows}
    (WORK / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
