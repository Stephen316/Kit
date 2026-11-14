import glob
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadModelHead import ReadModelHead
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmName, ReadAsmToken


def records(payload):
    cursor = MetaCursor(payload)
    ReadModelHead(cursor, True)
    found = []
    while cursor.Offset < len(payload):
        name = ReadAsmName(cursor)
        tokens = []
        if name in ('Begin-of-ASM-History-Data', 'End-of-ASM-History-Section', 'End-of-ASM-data'):
            continue
        while (token := ReadAsmToken(cursor))[0] != 17:
            tokens.append(token)
        found.append((name, tokens))
    return found


def main():
    rows = []
    for path in sorted(glob.glob(str(ROOT / 're/**/*.f3d'), recursive=True)):
        archive = zipfile.ZipFile(path)
        for info in archive.infolist():
            if not info.filename.endswith('.smbh'):
                continue
            payload = archive.read(info.filename)
            try:
                found = records(payload)
            except Exception as error:
                rows.append({'file': str(Path(path).relative_to(ROOT)), 'error': str(error)})
                continue
            states = [tokens for name, tokens in found if name == 'delta_state']
            others = [tokens for name, tokens in found if name != 'delta_state']
            rows.append({
                'file': str(Path(path).relative_to(ROOT)),
                'member': info.filename.rsplit('/', 1)[-1],
                'payload_bytes': len(payload),
                'records': len(found),
                'states': len(states),
                'max_state_tokens': max(map(len, states), default=0),
                'max_other_tokens': max(map(len, others), default=0),
            })
    rows.sort(key=lambda row: -row.get('max_state_tokens', 0))
    report = {
        'scope': 'Token counts of every ASM record in every .smbh history member under re/, read without record-size limits',
        'histories': len(rows),
        'errors': sum('error' in row for row in rows),
        'histories_over_4095_state_tokens': sum(row.get('max_state_tokens', 0) > 4095 for row in rows),
        'max_state_tokens': max(row.get('max_state_tokens', 0) for row in rows),
        'max_other_tokens': max(row.get('max_other_tokens', 0) for row in rows),
        'max_payload_bytes': max(row.get('payload_bytes', 0) for row in rows),
        'max_records': max(row.get('records', 0) for row in rows),
        'largest': rows[:40],
    }
    Path(__file__).with_name('BoardSizes.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'largest'}, indent=1))
    for row in rows[:20]:
        print(row)


if __name__ == '__main__':
    main()
