import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))
from StencilCheck import compare, form_entities
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import ConvertCage
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.SwapFormCage import SwapFormCage
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

WORK = ROOT / 're/Fusion/LocalOracle/FormDocuments/StencilAccept'
TARGET = BASE / 'StencilAcceptCheck.json'


def main():
    preparation = json.loads((WORK / 'Preparation.json').read_text())
    acceptance = json.loads((WORK / 'NativeAcceptance.json').read_text())
    report = {'scope': 'Kit stencil conversion of the cages that Fusion saved after the acceptance vertex edit, against the bodies Fusion converted and saved, and a second swap of each saved Kit document', 'python': sys.version.split()[0], 'acceptance_sha256': hashlib.sha256((WORK / 'NativeAcceptance.json').read_bytes()).hexdigest(), 'cases': []}
    for prepared, case in zip(preparation['rows'], acceptance['cases']):
        row = {'case': prepared['case']}
        for side in ('oracle', 'kit'):
            stages = case.get(side, {})
            if 'saved_file' not in stages:
                row[side] = 'not saved'
                continue
            path = ROOT / stages['saved_file']
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != stages['saved_sha256']:
                raise RuntimeError('Saved archive changed')
            model = ReadDocument(data)
            result = ConvertCage(model.Forms[0].Surface)
            entry = compare(result, form_entities(path))
            entry['gap_cm'] = max(entry.pop('surface_max'), entry.pop('curve_max'), entry.pop('point_max'))
            row[side] = entry
        kit_saved = case.get('kit', {}).get('saved_file')
        if kit_saved:
            model = ReadDocument((ROOT / kit_saved).read_bytes())
            fresh = ReadTspline((ROOT / prepared['tsm_file']).read_bytes())
            try:
                swapped = SwapFormCage(model, fresh)
                row['second_swap_roundtrip'] = ReadDocument(EmitParsed(swapped)) == swapped
            except ValueError as error:
                row['second_swap_roundtrip'] = 'refused: ' + str(error)
        report['cases'].append(row)
        print(json.dumps(row))
    TARGET.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
