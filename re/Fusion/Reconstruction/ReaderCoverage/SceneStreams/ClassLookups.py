import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 're/Fusion/Reconstruction/ReaderCoverage'))

import ClassGaps

REFLECTION = ROOT / 're/Fusion/LocalOracle/Reflection'


def lookups():
    data = json.loads((REFLECTION / 'Versions.json').read_text())
    return {item['identifier'].upper(): item for item in data['metatypes']}


def describe(table, guid, version):
    item = table.get(guid)
    if item is None:
        return {'reflected': False}
    found = {entry['lookup_version']: entry for entry in item.get('member_set_lookups') or ()}
    entry = found.get(version)
    return {
        'reflected': True,
        'name': item['name'],
        'current': item['metatype_current_version'],
        'lookup': entry['lookup_status'] if entry else None,
        'relations': [ (s['relation'], s['metatype_identifier'][:8], s['lookup_version'], len(s['members'] or ())) for s in (entry or {}).get('member_sets') or ()],
    }


if __name__ == '__main__':
    table = lookups()
    gaps = ClassGaps.census(sys.argv[1:])
    rows = []
    for (guid, version, name, known, segment), files in sorted(gaps.items(), key=lambda item: (item[0][2] or '', item[0][1])):
        row = {'guid': guid, 'version': version, 'name': name, 'known': list(known), 'segment': segment, 'files': len(files), 'owners': sum(count for _, count in files)} | describe(table, guid, version)
        rows.append(row)
        print(json.dumps(row))
