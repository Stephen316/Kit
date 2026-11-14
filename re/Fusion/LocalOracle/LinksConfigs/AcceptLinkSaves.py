import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
import adsk.fusion
from LinkCommon import acceptance_folder, design_of, private, pump, write

run_name = 'Accept2'
accept = private / 'accept'
prepared = json.loads((accept / 'Prepare.json').read_text())
controls = json.loads((private / 'LinkControls.json').read_text())
native = {step['name']: step for step in controls['steps']}
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'run': run_name + '_saves', 'documents_before': app.documents.count, 'cases': []}
opened = []


def references(doc):
    refs = doc.documentReferences
    rows = []
    for index in range(refs.count):
        item = refs.item(index)
        rows.append({'name': item.dataFile.name if item.dataFile else None, 'version': item.version, 'out_of_date': item.isOutOfDate})
    return sorted(rows, key=lambda row: str(row['name']))


def occurrences(doc):
    rows = {}
    for occ in design_of(doc).rootComponent.allOccurrences:
        height = None
        if occ.component.bRepBodies.count:
            box = occ.component.bRepBodies.item(0).boundingBox
            height = box.maxPoint.z - box.minPoint.z
        rows[occ.fullPathName] = {'component': occ.component.name, 'referenced': occ.isReferencedComponent, 'grounded': occ.isGrounded, 'transform2': list(occ.transform2.asArray()), 'body_height_cm': height}
    return rows


def deviation(rows, expected):
    if set(rows) != set(expected):
        return {'paths_equal': False, 'paths': sorted(rows), 'expected_paths': sorted(expected)}
    worst = max(abs(a - b) for path in rows for a, b in zip(rows[path]['transform2'], expected[path]))
    return {'paths_equal': True, 'max_abs_transform_error': worst}


def snapshot(doc, expected):
    design = design_of(doc)
    rows = occurrences(doc)
    health = [item.healthState for item in design.timeline if item.entity is not None]
    return {'references': references(doc), 'occurrences': rows, 'transform_check': deviation(rows, expected), 'timeline_count': design.timeline.count, 'unhealthy_timeline_items': sum(1 for state in health if state != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState)}


def latest(folder, name):
    for index in range(folder.dataFiles.count):
        item = folder.dataFiles.item(index)
        if item.name == name:
            return item
    return None


def mark(case, stage):
    case['stage'] = stage
    write(private / 'AcceptLinkSaves.json', report)


def open_file(case, data_file):
    doc = app.documents.open(data_file, True)
    if doc is None:
        raise RuntimeError('Open failed: ' + case['name'])
    opened.append(doc)
    pump(lambda: all(row['name'] is not None for row in references(doc)), 180)
    return doc


def run_case(name, expected, folder):
    case = {'name': name}
    report['cases'].append(case)
    data_file = latest(folder, name)
    case['start_version'] = data_file.versionNumber
    case['read_only'] = data_file.isReadOnly
    mark(case, 'opening')
    doc = open_file(case, data_file)
    case['opened'] = snapshot(doc, expected)
    if any(row['out_of_date'] for row in case['opened']['references']):
        mark(case, 'updating')
        case['update_all'] = doc.updateAllReferences()
        case['update_settled'] = pump(lambda: not any(row['out_of_date'] for row in references(doc)), 180)
        case['updated'] = snapshot(doc, expected)
        mark(case, 'saving')
        case['save_result'] = doc.save('Kit link acceptance after reference update')
        start = case['start_version']
        case['saved'] = pump(lambda: (latest(folder, name) or data_file).versionNumber > start and latest(folder, name).isComplete, 600)
    doc.close(False)
    opened.remove(doc)
    saved_file = latest(folder, name)
    case['reopen_version'] = saved_file.versionNumber
    mark(case, 'reopening')
    again = open_file(case, saved_file)
    case['reopened'] = snapshot(again, expected)
    again.close(False)
    opened.remove(again)
    case['documents_after_close'] = app.documents.count
    mark(case, 'done')


try:
    project, folder = acceptance_folder(app, subfolder=run_name)
    entries = {entry['name']: entry for entry in prepared['outputs']}
    replay = {occ['path']: occ['transform2'] for occ in native['R5_saved']['occurrences']}
    run_case('KitLinkReplayR5', replay, folder)
    run_case('KitLinkMovedR1', {'KitLinkPartA:1': entries['KitLinkMovedR1']['written_matrix']}, folder)
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    for doc in reversed(opened):
        try:
            if doc.isValid:
                doc.close(False)
        except Exception:
            report.setdefault('close_errors', []).append(traceback.format_exc())
    report['documents_after'] = app.documents.count
    write(private / 'AcceptLinkSaves.json', report)
