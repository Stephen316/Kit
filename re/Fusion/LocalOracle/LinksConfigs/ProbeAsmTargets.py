import builtins
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
plan = json.loads((author / 'Probe.json').read_text())
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'run': plan['run'], 'documents_before': app.documents.count, 'probes': []}
before = [app.documents.item(index) for index in range(app.documents.count)]


def find_file(folder, name):
    for index in range(folder.dataFiles.count):
        item = folder.dataFiles.item(index)
        if item.name == name:
            return item
    return None


def close_new():
    for index in reversed(range(app.documents.count)):
        doc = app.documents.item(index)
        if doc.isValid and not any(doc == old for old in before):
            doc.close(False)


try:
    state = getattr(builtins, '_kit_asm_upload', None)
    if state is not None:
        report['upload_states'] = {name: int(future.uploadState) for name, future in state.futures.items()}
    project, folder = acceptance_folder(app, subfolder=plan['run'])
    report['folder'] = folder.name
    for name in plan['names']:
        row = {'name': name}
        report['probes'].append(row)
        data_file = find_file(folder, name)
        row['found'] = data_file is not None
        if data_file is None:
            continue
        row['complete'] = pump(lambda: data_file.isComplete, 300)
        row['version'] = data_file.versionNumber
        row['lineage_urn'] = data_file.id
        row['version_urn'] = data_file.versionId
        if not row['complete']:
            continue
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = design_of(doc)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        occ = design.rootComponent.occurrences.addByInsert(data_file, adsk.core.Matrix3D.create(), True)
        row['inserted'] = occ is not None
        if occ is not None:
            row['occurrence'] = occ.fullPathName
            row['exports'] = export_f3d(design, author / ('Probe' + name + '.f3d'))
        row['documents_open'] = app.documents.count
        close_new()
        write(private / 'ProbeAsmTargets.json', report)
    report['status'] = 'completed' if all(row.get('inserted') for row in report['probes']) else 'waiting'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    try:
        close_new()
    except Exception:
        report.setdefault('close_errors', []).append(traceback.format_exc())
    report['documents_after'] = app.documents.count
    write(private / 'ProbeAsmTargets.json', report)
