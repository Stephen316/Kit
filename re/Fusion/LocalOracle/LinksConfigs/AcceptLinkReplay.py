import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
import adsk.fusion
from LinkCommon import acceptance_folder, design_of, digest, private, pump, write

run_name = 'Accept1'
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
        body = occ.component.bRepBodies.item(0) if occ.component.bRepBodies.count else None
        height = None
        if body is not None:
            box = body.boundingBox
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
    rows = occurrences(doc)
    return {'references': references(doc), 'occurrences': rows, 'transform_check': deviation(rows, expected), 'healthy': design_of(doc).rootComponent.allOccurrences.count == len(expected)}


def run_case(entry, expected, folder):
    case = {'name': entry['name'], 'source_control': entry['source_control'], 'file_sha256': digest(accept / (entry['name'] + '.f3d')), 'prepared_sha256': entry['output_sha256']}
    report['cases'].append(case)
    options = app.importManager.createFusionArchiveImportOptions(str(accept / (entry['name'] + '.f3d')))
    doc = app.importManager.importToNewDocument(options)
    if doc is None:
        raise RuntimeError('Fusion import returned no document: ' + entry['name'])
    opened.append(doc)
    case['references_settled'] = settle(doc)
    case['opened'] = snapshot(doc, expected)
    case['update_all'] = doc.updateAllReferences()
    case['update_settled'] = pump(lambda: not any(row['out_of_date'] for row in references(doc)), 180)
    case['updated'] = snapshot(doc, expected)
    if not doc.saveAs(entry['name'], folder, 'Kit link replay acceptance', ''):
        raise RuntimeError('saveAs failed: ' + entry['name'])
    case['saved'] = pump(lambda: doc.isSaved and doc.dataFile is not None and doc.dataFile.isComplete, 300)
    data_file = doc.dataFile
    case['saved_version'] = data_file.versionNumber
    doc.close(False)
    opened.remove(doc)
    again = app.documents.open(data_file, True)
    if again is None:
        raise RuntimeError('Reopen failed: ' + entry['name'])
    opened.append(again)
    case['reopen_settled'] = settle(again)
    case['reopened'] = snapshot(again, expected)
    again.close(False)
    opened.remove(again)
    write(private / 'AcceptLinkReplay.json', report)


try:
    project, folder = acceptance_folder(app, subfolder=run_name)
    report['folder'] = folder.name
    entries = {entry['name']: entry for entry in prepared['outputs']}
    replay = {path: row['transform2'] for path, row in ((occ['path'], occ) for occ in native['R5_saved']['occurrences'])}
    run_case(entries['KitLinkReplayR5'], replay, folder)
    moved = entries['KitLinkMovedR1']
    run_case(moved, {'KitLinkPartA:1': moved['written_matrix']}, folder)
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
    write(private / 'AcceptLinkReplay.json', report)
