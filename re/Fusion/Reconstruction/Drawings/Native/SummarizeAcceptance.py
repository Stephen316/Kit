import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE.parent / 'NativeAcceptance.json'
VARIANTS = Path(tempfile.gettempdir()) / 'KitFusionDrawings' / 'Variants'
GUID = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')
PRIVATE = ('/Users/', '/var/folders/', 'Library/Application Support', 'AppData', 'urn:adsk', 'W.login')


def load(name, fallback=None):
    path = Path(name) if Path(name).is_absolute() else VARIANTS / name
    if not path.exists():
        return fallback
    return json.loads(path.read_text())


def view(row):
    keep = {'type': row.get('type'), 'curve_count': row.get('curve_count')}
    for key in ('orientation', 'scale', 'style'):
        value = row.get(key)
        keep[key] = value if not isinstance(value, dict) else 'getter failed'
    keep['curves'] = row.get('curves', [])
    return keep


def drawing(info):
    if not isinstance(info, dict) or 'sheets' not in info:
        return info
    sheets = []
    for sheet in info['sheets']:
        sheets.append({'name': sheet.get('name'), 'width_mm': sheet.get('width'), 'height_mm': sheet.get('height'), 'dimensions': sheet.get('dimensions'), 'title_block': sheet.get('title_block'), 'views': [view(row) for row in sheet.get('views', [])]})
    return {'title_blocks': info.get('title_blocks'), 'sheets': sheets}


def opened(row):
    if not isinstance(row, dict):
        return row
    result = {key: row[key] for key in ('ready', 'references', 'modified_after_open', 'open_error', 'missing_folder') if key in row}
    result['files'] = [{key: item[key] for key in ('name', 'extension', 'version', 'complete')} for item in row.get('files', [])]
    if 'opened' in row:
        result['drawing'] = drawing(row['opened'])
    result['captures'] = [{'file': GUID.sub('<guid>', Path(item['cache_relative']).name), 'bytes': item['bytes'], 'sha256': item['sha256']} for item in row.get('captures') or []]
    return result


def inspection(report):
    if report is None:
        return {'status': 'not run'}
    return {'status': report.get('status'), 'stage': report.get('stage'), 'documents_after': report.get('documents_after'), 'uploads': {label: opened(row) for label, row in report.get('uploads', {}).items()}}


def edit(report):
    if report is None:
        return {'status': 'not run'}
    keys = ('status', 'stage', 'design_before', 'design_after', 'references_before', 'update_result', 'references_after', 'drawing_version', 'read_only', 'save_requests', 'documents_after')
    result = {key: report.get(key) for key in keys if key in report}
    result['drawing_before'] = drawing(report.get('drawing_before'))
    result['drawing_after'] = drawing(report.get('drawing_after'))
    if 'reopened' in report:
        result['reopened'] = {**report['reopened'], 'drawing': drawing(report['reopened'].get('drawing'))}
    if 'traceback' in report:
        result['error'] = report['traceback'].strip().splitlines()[-1]
    result['captures_saved'] = [{'file': GUID.sub('<guid>', Path(item['cache_relative']).name), 'bytes': item['bytes'], 'sha256': item['sha256']} for item in report.get('captures_saved') or []]
    return result


def steps(report):
    if report is None:
        return {'status': 'not run'}
    rows = [{key: row.get(key) for key in ('name', 'started', 'finished', 'status', 'documents_after')} for row in report.get('steps', [])]
    waits = report.get('upload_waits') or ([report['upload_wait']] if 'upload_wait' in report else [])
    return {'status': report.get('status'), 'documents_after': report.get('documents_after'), 'upload_waits': waits, 'steps': rows}


def capacity(report):
    if report is None:
        return {'status': 'not run'}
    keys = ('status', 'before', 'blocked', 'needed', 'deleted', 'stopped', 'after', 'watched_after', 'documents_after')
    result = {key: report.get(key) for key in keys if key in report}
    result['watched_before'] = report.get('watched_before')
    if 'traceback' in report:
        result['error'] = report['traceback'].strip().splitlines()[-1]
    return result


SECOND_PLANS = ('Plan.json', 'Plan2.json', 'Plan3.json', 'Plan4.json', 'Plan5.json', 'Plan6.json', 'Plan7.json', 'Plan8.json', 'Plan9.json', 'Plan10.json', 'Plan11.json', 'PlanAuthored.json')
SECOND_INSPECTIONS = ('Prune1', 'Prune3', 'Prune5', 'Authored2', 'Prune7Fixed', 'Prune7Late', 'Prune7D', 'DataStore1', 'Sections1', 'Authored5', 'Trust1', 'Trust2', 'Sections2', 'Sections3', 'Trust3', 'Shell1', 'Tail1', 'Tail2', 'Shorts1', 'Bisect1', 'Bisect2', 'Bisect3', 'Bisect4', 'Bisect5', 'Shell6', 'Shell7', 'Shell8', 'Shell9')
SECOND_ROUNDS = ('Round6', 'Round7', 'Round8', 'Round9', 'Round10', 'Round11', 'Round12', 'Round13', 'Round14', 'Round15', 'Round16', 'Round17', 'Round18')


def planned(row):
    keep = ('label', 'bytes', 'sha256', 'dwg_bytes', 'dwg_sha256', 'objects', 'sections')
    result = {key: row[key] for key in keep if key in row}
    for key in ('removed', 'nulled_references'):
        if key in row:
            result[key] = {'kinds': len(row[key]), 'objects': sum(value if isinstance(value, int) else 1 for value in row[key].values())}
    return result


def recycled(report):
    if report is None:
        return {'status': 'not run'}
    keys = ('status', 'before', 'after', 'deleted_count', 'refused_count', 'deleted', 'refused')
    return {key: report.get(key) for key in keys if key in report}


def second_pass():
    plans = {}
    for name in SECOND_PLANS:
        plan = load(name)
        if plan:
            plans[name[:-5]] = [planned(row) for row in plan['variants']]
    return {
        'plans': plans,
        'inspections': {tag: inspection(load('Inspect' + tag + '.json')) for tag in SECOND_INSPECTIONS},
        'edits': {label: edit(load('Edit' + label + '.json')) for label in ('T3ThreeViews', 'U3ThreeViews')},
        'rounds': {tag: steps(load('Accept' + tag + '.json')) for tag in SECOND_ROUNDS},
        'dialogs': load('Dialogs.json', []),
        'quarantine': load('Quarantine.json', {}).get('labels', {}),
        'recycle': {tag: recycled(load('Recycle' + tag + '.json')) for tag in ('Before1', 'Before2', 'Before3', 'Before4', 'Before5', 'Before6', 'Before7', 'Before8')},
    }


FIRST_PASS = ('schema', 'fusion_version', 'variants', 'inputs', 'historical', 'modern_typed', 'controls', 'typed_reemission', 'edit_acceptance', 'views_control', 'no_database', 'swapped_database', 'missing_database', 'reverse_swap', 'capacity', 'saved_edit', 'runs')


def main(extra):
    """Keep the first-pass evidence of the committed report, and rebuild the second pass from the scratch records."""
    previous = json.loads(OUT.read_text())
    report = {key: previous[key] for key in FIRST_PASS}
    report['fixtures'] = json.loads((BASE.parent / 'Fixtures.json').read_text())
    report['second_pass'] = second_pass()
    report.update(json.loads(Path(extra['notes']).read_text()) if 'notes' in extra else {})
    text = json.dumps(report, indent=1, default=str) + '\n'
    leaks = [token for token in PRIVATE if token in text]
    if leaks:
        raise ValueError('Private tokens in acceptance report: ' + ', '.join(leaks))
    OUT.write_text(text)
    print(OUT.name, hashlib.sha256(text.encode()).hexdigest())


if __name__ == '__main__':
    main(dict(item.split('=', 1) for item in sys.argv[1:]))
