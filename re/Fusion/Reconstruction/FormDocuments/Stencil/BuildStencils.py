import hashlib
import json
import lzma
import sys
from fractions import Fraction
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 're/Fusion/Reconstruction/FormDocuments/Tables'))
from StencilKey import StencilKey
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

WORK = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil'
TARGET = ROOT / 're/Fusion/Reconstruction/FormDocuments/Tables/FormStencils.xz'
REPORT = BASE / 'StencilTables.json'
DENOMINATOR = 4096
SNAP = 1e-13


def snapped(value):
    fraction = Fraction(value).limit_denominator(DENOMINATOR)
    if abs(float(fraction) - value) <= SNAP:
        return float(fraction), True, abs(float(fraction) - value)
    return value, False, 0.0


def build(name):
    table = json.loads((WORK / 'tmp' / (name + 'Table.json')).read_text())
    surface = ReadTspline((WORK / 'tmp' / name / 'Base.tsm').read_bytes())
    unique, ids, mapping = [], {}, []
    stats = {'snapped': 0, 'kept': 0, 'snap_delta_max': 0.0, 'row_sum_error_max': 0.0}
    for row in table['rows']:
        entries = []
        for grip, text in row:
            value, hit, delta = snapped(float(text))
            stats['snapped' if hit else 'kept'] += 1
            stats['snap_delta_max'] = max(stats['snap_delta_max'], delta)
            entries.append((grip, value))
        stats['row_sum_error_max'] = max(stats['row_sum_error_max'], abs(sum(value for _, value in entries) - 1.0))
        signature = tuple((grip, round(value, 13)) for grip, value in entries)
        if signature not in ids:
            ids[signature] = len(unique)
            unique.append([[grip, value] for grip, value in entries])
        mapping.append(ids[signature])
    keys = [tuple(key) for key in table['keys']]
    faces, curves = [], []
    for item in table['layout']:
        if item[0] == 'surface':
            poles = [mapping[index] for index, key in enumerate(keys) if key[0] == 's' and key[1] == item[1]]
            faces.append([item[1], item[2], item[3], poles])
        elif item[0] == 'curve':
            poles = [mapping[index] for index, key in enumerate(keys) if key[0] == 'c' and key[1] == item[1]]
            curves.append([item[2], item[3], poles])
    points = [mapping[index] for index, key in enumerate(keys) if key[0] == 'p']
    entry = {'Label': name, 'LayoutKey': StencilKey(surface), 'GripCount': len(surface.Grips), 'Rows': unique, 'Faces': faces, 'Curves': curves, 'Points': points}
    summary = {'cage': name, 'layout_key': entry['LayoutKey'], 'grips': len(surface.Grips), 'poles': len(keys), 'unique_rows': len(unique), 'faces': len(faces), 'curves': len(curves), 'points': len(points)}
    summary.update(stats)
    return entry, summary


def main():
    names = sys.argv[1:]
    entries, summaries = [], []
    for name in names:
        entry, summary = build(name)
        entries.append(entry)
        summaries.append(summary)
        print(json.dumps(summary))
    text = json.dumps({'Tables': entries}, sort_keys=True, separators=(',', ':')).encode('ascii')
    data = lzma.compress(text, preset=9 | lzma.PRESET_EXTREME)
    TARGET.write_bytes(data)
    report = {'scope': 'Packaged Form stencil tables: coefficient rows fitted from single-grip Fusion probes, snapped to fractions with denominators up to 4096 when within 1e-13, deduplicated', 'python': sys.version.split()[0], 'file': str(TARGET.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'tables': summaries}
    REPORT.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
