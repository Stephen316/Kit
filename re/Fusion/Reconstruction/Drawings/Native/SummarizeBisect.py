"""Add the content-bisection rounds of BuildBisect.py to NativeAcceptance.json.

Each round report comes from BisectRound.py. The summary keeps labels, DWG digests, guard outcomes and the
opened sheet facts, without folder names or cloud identities.
"""

import json
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE.parent / 'NativeAcceptance.json'
VARIANTS = Path(tempfile.gettempdir()) / 'KitFusionDrawings' / 'Variants'
CHANGES = {
    'B0Base': 'Q1NoDataStore emitted again, with the A1 header values',
    'B1VersionGuid': 'VERSIONGUID changed, a header string',
    'B8UserReal': 'USERR4 changed from 0.0 to 1.0, a header variable that every save shares',
    'B9AllVaried': 'Every header variable that differs between Fusion saves changed together',
    'B10FifthLong': 'BL value 1 written after the four BS values',
    'C1AppNoTrust': 'Q8AuthoredSections with the Fusion product entry only and Kit auxiliary header',
    'C2AppKitProduct': 'Q8AuthoredSections with Kit product entry, the trusted-file entry and Kit auxiliary header',
    'C7AppOnly': 'Q8AuthoredSections with Kit AppInfo',
}


def row(item, plans):
    guard = item.get('guard') or {}
    result = item.get('result') or {}
    plan = plans.get(item['label'], {})
    entry = {
        'label': item['label'],
        'change': CHANGES.get(item['label']),
        'dwg_sha256': plan.get('dwg_sha256'),
        'dwg_bytes': plan.get('dwg_bytes'),
        'guard': guard.get('status'),
    }
    if guard.get('status') == 'completed' and 'open_seconds' in result:
        entry['result'] = 'opened'
        entry['open_seconds'] = result['open_seconds']
        entry['view_curves'] = result.get('views')
        entry['dimensions'] = result.get('dimensions')
    else:
        entry['result'] = 'stalled' if guard.get('status') == 'stalled' else guard.get('status')
        entry['waited_seconds'] = guard.get('age')
        entry['dialog'] = guard.get('dialog')
        entry['restart_seconds'] = item.get('restart')
    return entry


def pairs():
    plans = {item['label']: item for item in json.loads((VARIANTS / 'Plan12.json').read_text())['variants']}
    dialogs = json.loads((VARIANTS / 'Dialogs.json').read_text())
    rows = []
    for label in ('Y0', 'YX', 'YS', 'YAX'):
        plan = plans[label]
        entry = {'label': label, 'parts': plan.get('parts'), 'dwg_sha256': plan.get('dwg_sha256'), 'dwg_bytes': plan.get('dwg_bytes')}
        stalls = [item['age'] for item in dialogs if item['tag'] == 'Inspect' + label]
        path = VARIANTS / ('Inspect' + label + '.json')
        found = json.loads(path.read_text()).get('uploads', {}).get(label) if path.exists() else None
        if found and 'open_seconds' in found:
            sheet = found['opened']['sheets'][0]
            entry.update(result='opened', open_seconds=found['open_seconds'], view_curves=[view['curve_count'] for view in sheet['views']], dimensions=sheet['dimensions'])
        elif stalls:
            entry.update(result='stalled', waited_seconds=stalls)
        rows.append(entry)
    return {'base': 'Q8AuthoredSections', 'parts': {'A': 'Kit AppInfo', 'X': 'Kit auxiliary header', 'S': 'Kit summary'}, 'variants': rows}


def main():
    tags = sys.argv[1:] or ['R1', 'R2']
    plans = {item['label']: item for item in json.loads((VARIANTS / 'PlanBisect.json').read_text())['variants']}
    report = json.loads(OUT.read_text())
    rounds = []
    for tag in tags:
        data = json.loads((VARIANTS / ('Bisect' + tag + '.json')).read_text())
        upload = data.get('upload') or {}
        rounds.append({'tag': tag, 'started': data.get('started'), 'finished': data.get('finished'), 'upload_status': upload.get('status'), 'variants': [row(item, plans) for item in data['rows']]})
    report['bisection'] = {'base': 'Q1NoDataStore for B labels, Q8AuthoredSections for C labels', 'stall_limit_seconds': 60, 'pairs': pairs(), 'rounds': rounds}
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(rounds, indent=1))


if __name__ == '__main__':
    main()
