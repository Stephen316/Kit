import builtins
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
report = {'fusion_version': app.version, 'run': run_name, 'documents_before': app.documents.count, 'cases': []}
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


def settle(doc):
    return pump(lambda: all(row['name'] is not None for row in references(doc)), 180)


def snapshot(doc, expected):
    design = design_of(doc)
    rows = occurrences(doc)
    health = [item.healthState for item in design.timeline if item.entity is not None]
    return {'references': references(doc), 'occurrences': rows, 'transform_check': deviation(rows, expected), 'timeline_count': design.timeline.count, 'unhealthy_timeline_items': sum(1 for state in health if state != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState)}


def find_file(folder, name):
    for index in range(folder.dataFiles.count):
        item = folder.dataFiles.item(index)
        if item.name == name:
            return item
    return None


def mark(case, stage):
    case['stage'] = stage
    write(private / 'AcceptLinkUploads.json', report)


def open_file(case, data_file):
    mark(case, 'opening')
    doc = app.documents.open(data_file, True)
    if doc is None:
        raise RuntimeError('Open failed: ' + case['name'])
    opened.append(doc)
    case['documents_after_open'] = app.documents.count
    mark(case, 'opened')
    return doc


def run_control(folder):
    case = {'name': 'KitLinkRoot', 'source_control': 'native cloud root after R8_updated_saved'}
    report['cases'].append(case)
    data_file = find_file(folder, 'KitLinkRoot')
    case['found'] = data_file is not None
    if data_file is None:
        return
    case['version'] = data_file.versionNumber
    doc = open_file(case, data_file)
    case['references_settled'] = settle(doc)
    expected = {occ['path']: occ['transform2'] for occ in native['R8_updated_saved']['occurrences']}
    case['opened'] = snapshot(doc, expected)
    doc.close(False)
    opened.remove(doc)
    case['documents_after_close'] = app.documents.count
    mark(case, 'closed')


def run_case(entry, expected, folder):
    case = {'name': entry['name'], 'source_control': entry['source_control'], 'prepared_sha256': entry['output_sha256']}
    report['cases'].append(case)
    data_file = find_file(folder, entry['name'])
    case['uploaded'] = data_file is not None
    if data_file is None:
        return False
    case['uploaded_version'] = data_file.versionNumber
    case['uploaded_complete'] = pump(lambda: data_file.isComplete, 120)
    if not case['uploaded_complete']:
        return False
    doc = open_file(case, data_file)
    case['references_settled'] = settle(doc)
    case['opened'] = snapshot(doc, expected)
    mark(case, 'updating')
    case['update_all'] = doc.updateAllReferences()
    case['update_settled'] = pump(lambda: not any(row['out_of_date'] for row in references(doc)), 180)
    case['updated'] = snapshot(doc, expected)
    mark(case, 'saving')
    if not doc.save('Kit link acceptance after reference update'):
        raise RuntimeError('Save failed: ' + entry['name'])
    target = data_file.versionNumber + 1
    case['saved'] = pump(lambda: doc.dataFile is not None and doc.dataFile.versionNumber >= target and doc.dataFile.isComplete, 300)
    saved_file = doc.dataFile
    case['saved_version'] = saved_file.versionNumber
    doc.close(False)
    opened.remove(doc)
    case['documents_after_close'] = app.documents.count
    mark(case, 'reopening')
    again = open_file(case, saved_file)
    case['reopen_settled'] = settle(again)
    case['reopened'] = snapshot(again, expected)
    again.close(False)
    opened.remove(again)
    mark(case, 'done')
    return True


try:
    state = getattr(builtins, '_kit_link_upload', None)
    if state is not None:
        report['upload_states'] = {name: int(future.uploadState) for name, future in state.futures.items()}
    project, folder = acceptance_folder(app, subfolder=run_name)
    report['folder'] = folder.name
    entries = {entry['name']: entry for entry in prepared['outputs']}
    replay = {occ['path']: occ['transform2'] for occ in native['R5_saved']['occurrences']}
    moved = entries['KitLinkMovedR1']
    _, control_folder = acceptance_folder(app, subfolder='Run1')
    run_control(control_folder)
    done = run_case(entries['KitLinkReplayR5'], replay, folder)
    done = run_case(moved, {'KitLinkPartA:1': moved['written_matrix']}, folder) and done
    report['status'] = 'completed' if done else 'waiting'
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
    write(private / 'AcceptLinkUploads.json', report)
