import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
import adsk.fusion
from LinkCommon import acceptance_folder, design_of, export_f3d, private, pump, write

author = private / 'author'
plan = json.loads((author / 'Accept.json').read_text())
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'run': plan['run'], 'documents_before': app.documents.count, 'stages': {}}
before = [app.documents.item(index) for index in range(app.documents.count)]
out_path = private / 'AcceptAsmRoot.json'


def find_file(folder, name):
    for index in range(folder.dataFiles.count):
        item = folder.dataFiles.item(index)
        if item.name == name:
            return item
    return None


def close_new():
    for doc in [app.documents.item(index) for index in range(app.documents.count)]:
        if doc.isValid and not any(doc == old for old in before):
            doc.close(False)


def mark(stage):
    report['stage'] = stage
    write(out_path, report)


def references(doc):
    refs = doc.documentReferences
    rows = []
    for index in range(refs.count):
        item = refs.item(index)
        data_file = item.dataFile
        rows.append({'name': data_file.name if data_file else None, 'version': item.version, 'out_of_date': item.isOutOfDate})
    return sorted(rows, key=lambda row: str(row['name']))


def occurrences(design):
    rows = {}
    for occ in design.rootComponent.allOccurrences:
        height = None
        if occ.component.bRepBodies.count:
            box = occ.component.bRepBodies.item(0).boundingBox
            height = box.maxPoint.z - box.minPoint.z
        rows[occ.fullPathName] = {
            'component': occ.component.name,
            'referenced': occ.isReferencedComponent,
            'grounded': occ.isGrounded,
            'transform2': list(occ.transform2.asArray()),
            'bodies': occ.component.bRepBodies.count,
            'body_height_cm': height,
        }
    return rows


def joints(design):
    rows = []
    root = design.rootComponent
    for index in range(root.asBuiltJoints.count):
        joint = root.asBuiltJoints.item(index)
        rows.append({
            'name': joint.name,
            'type': int(joint.jointMotion.jointType),
            'one': joint.occurrenceOne.fullPathName if joint.occurrenceOne else None,
            'two': joint.occurrenceTwo.fullPathName if joint.occurrenceTwo else None,
            'health': int(joint.timelineObject.healthState) if joint.timelineObject else None,
        })
    return rows


def snapshot(doc):
    design = design_of(doc)
    rows = occurrences(design)
    expected = plan['expected']
    check = {'paths_equal': set(rows) == set(expected)}
    if check['paths_equal']:
        check['max_abs_transform_error'] = max(abs(a - b) for path in rows for a, b in zip(rows[path]['transform2'], expected[path]))
        check['exact_transform_paths'] = sorted(path for path in rows if rows[path]['transform2'] == expected[path])
    health = [item.healthState for item in design.timeline if item.entity is not None]
    return {
        'references': references(doc),
        'occurrences': rows,
        'transform_check': check,
        'grounded': sorted(path for path, row in rows.items() if row['grounded']),
        'joints': joints(design),
        'timeline_count': design.timeline.count,
        'unhealthy_timeline_items': sum(1 for state in health if state != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState),
    }


def open_file(data_file):
    doc = app.documents.open(data_file, True)
    if doc is None:
        raise RuntimeError('Open failed: ' + data_file.name)
    pump(lambda: all(row['name'] is not None for row in references(doc)), 180)
    return doc


try:
    project, folder = acceptance_folder(app, subfolder=plan['run'])
    root_file = find_file(folder, plan['root'])
    if root_file is None:
        raise RuntimeError('Root upload is absent')
    report['root_complete'] = pump(lambda: root_file.isComplete, 600)
    report['root_version_start'] = root_file.versionNumber

    mark('open_uploaded')
    doc = open_file(root_file)
    report['stages']['opened'] = snapshot(doc)
    doc.close(False)
    report['documents_after_first_close'] = app.documents.count

    mark('edit_part')
    edit = plan['edit']
    part_file = find_file(folder, edit['name'])
    part_start = part_file.versionNumber
    part_doc = app.documents.open(part_file, True)
    parameter = design_of(part_doc).allParameters.itemByName(edit['parameter'])
    report['part_edit'] = {'name': edit['name'], 'start_version': part_start, 'parameter_before': parameter.expression}
    parameter.expression = edit['expression']
    report['part_edit']['parameter_after'] = parameter.expression
    report['part_edit']['save_result'] = part_doc.save('Kit assembly acceptance part edit')
    report['part_edit']['saved'] = pump(lambda: (find_file(folder, edit['name']) or part_file).versionNumber > part_start and find_file(folder, edit['name']).isComplete, 600)
    report['part_edit']['end_version'] = find_file(folder, edit['name']).versionNumber
    part_doc.close(False)

    mark('update_references')
    root_file = find_file(folder, plan['root'])
    doc = open_file(root_file)
    report['stages']['before_update'] = snapshot(doc)
    report['update_all'] = doc.updateAllReferences()
    report['update_settled'] = pump(lambda: not any(row['out_of_date'] for row in references(doc)), 180)
    report['stages']['after_update'] = snapshot(doc)
    after = report['stages']['after_update']['occurrences'].get('KitAsmPartA:1', {})
    report['edit_propagated'] = after.get('body_height_cm') is not None and abs(after['body_height_cm'] - edit['height_cm']) < 1e-9

    mark('save_root')
    start = root_file.versionNumber
    report['root_save_result'] = doc.save('Kit assembly acceptance after reference update')
    report['root_saved'] = pump(lambda: find_file(folder, plan['root']).versionNumber > start and find_file(folder, plan['root']).isComplete, 600)
    doc.close(False)

    mark('reopen')
    saved = find_file(folder, plan['root'])
    report['root_version_end'] = saved.versionNumber
    again = open_file(saved)
    report['stages']['reopened'] = snapshot(again)
    report['export'] = export_f3d(design_of(again), author / 'AcceptedKitAsmRoot.f3d')
    again.close(False)
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    try:
        close_new()
    except Exception:
        report.setdefault('close_errors', []).append(traceback.format_exc())
    report['documents_after'] = app.documents.count
    write(out_path, report)
