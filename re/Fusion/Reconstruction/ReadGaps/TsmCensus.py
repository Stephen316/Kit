import collections
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))

from Sweep import tracked
from convert.formats.Fusion.TSplineCodec.Wire.MakeCursor import MakeCursor


def members(name):
    data = (ROOT / name).read_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for item in archive.namelist():
            if item.lower().endswith('.tsm'):
                yield archive.read(item)


def main():
    kinds = collections.Counter()
    rows = []
    for name in tracked():
        if not name.endswith('.f3d'):
            continue
        for payload in members(name):
            records = MakeCursor(payload).Records
            edges = [row for row in records if row[0] == 'e']
            knots = [row for row in records if row[0] == '106ek']
            intervals = sorted({float(row[2]) for row in edges if len(row) > 2})
            order = []
            for row in records:
                if not order or order[-1] != row[0]:
                    order.append(row[0])
            kinds[' '.join(order)] += 1
            rows.append({
                'file': name,
                'edges': len(edges),
                'knot_rows': len(knots),
                'unit_intervals': intervals == [1.0],
                'knots_equal_intervals': len(knots) == len(edges) and all(float(a[1]) == float(b[2]) for a, b in zip(knots, edges)),
                'knots_text_equal': len(knots) == len(edges) and all(a[1] == b[2] for a, b in zip(knots, edges)),
            })
    with_knots = [row for row in rows if row['knot_rows']]
    report = {
        'members': len(rows),
        'orders': dict(kinds.most_common()),
        'with_knot_rows': len(with_knots),
        'knot_rows_per_edge': all(row['knot_rows'] == row['edges'] for row in with_knots),
        'knots_equal_intervals': all(row['knots_equal_intervals'] for row in with_knots),
        'knots_text_equal': all(row['knots_text_equal'] for row in with_knots),
        'unit_with_knot_rows': sorted(row['file'] for row in with_knots if row['unit_intervals']),
        'other_without_knot_rows': sorted(row['file'] for row in rows if not row['knot_rows'] and not row['unit_intervals']),
        'files_with_knot_rows': sorted({row['file'] for row in with_knots}),
    }
    (BASE / 'TsmCensus.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'orders'}, indent=1)[:3000])
    for order, count in kinds.most_common(12):
        print(count, order)


if __name__ == '__main__':
    main()
