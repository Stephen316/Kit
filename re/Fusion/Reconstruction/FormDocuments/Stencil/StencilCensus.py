import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(ROOT / 're/Fusion/Reconstruction/FormDocuments/Topology'))
from StencilCheck import compare  # noqa: E402
from SavedBodies import read_saved  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import ConvertForm  # noqa: E402
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument  # noqa: E402

TARGET = BASE / 'StencilCensus.json'
SLACK = 1e-12


def main():
    report = {'scope': 'Kit cage conversion (general rules, no stencil tables) of the cage of every local Form archive against its stored converted body; probe outputs in ignored folders excluded', 'python': sys.version.split()[0], 'converter': 'src ConvertForm (general cage rules) against the body read from the archive, in element order', 'slack_cm': SLACK, 'totals': Counter(), 'archives': []}
    seen = set()
    for path in sorted(ROOT.glob('re/Fusion/**/*.f3d')):
        relative = path.relative_to(ROOT)
        if 'tmp' in relative.parts or not path.is_file():
            continue
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        try:
            model = ReadDocument(data)
        except Exception:
            continue
        if len(model.Forms) != 1:
            continue
        surface = model.Forms[0].Surface
        row = {'file': str(relative), 'sha256': digest}
        try:
            native = read_saved(path).body
        except Exception:
            native = None
        try:
            result = ConvertForm(surface)
        except ValueError as error:
            result = None
            row['refusal'] = str(error)
        if result is None:
            row['status'] = 'refused'
        elif native is None:
            row['status'] = 'no body'
        else:
            check = compare(result, native)
            row['gap_cm'] = max(check['surface_max'], check['curve_max'], check['point_max'])
            row['layout_equal'] = check['layout_equal']
            row['jumps_equal'] = check['jumps_equal']
            row['status'] = 'equal' if row['layout_equal'] and row['jumps_equal'] and row['gap_cm'] <= SLACK else 'different'
        report['totals'][row['status']] += 1
        if 'refusal' in row:
            report['totals']['refused: ' + row['refusal']] += 1
        report['archives'].append(row)
    report['totals'] = dict(sorted(report['totals'].items()))
    TARGET.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report['totals']))
    for row in report['archives']:
        if row['status'] in ('equal', 'different'):
            print(row['status'], row['file'], row.get('gap_cm'))


if __name__ == '__main__':
    main()
