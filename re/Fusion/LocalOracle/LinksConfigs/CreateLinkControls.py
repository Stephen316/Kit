import sys
from pathlib import Path
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
import adsk.fusion
from LinkCommon import acceptance_folder, design_of, export_f3d, matrix, private, pump, write

run_name = 'Run1'
out = private / 'links'
out.mkdir(parents=True, exist_ok=True)
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'run': run_name, 'documents_before': app.documents.count, 'steps': []}
opened = []


def occurrence_state(design):
    rows = []
    for occ in design.rootComponent.allOccurrences:
        ref = None
        try:
            data = occ.component.parentDesign.parentDocument.dataFile if occ.isReferencedComponent else None
            if data is not None:
                ref = {'name': data.name, 'version': data.versionNumber}
        except Exception:
            ref = {'error': traceback.format_exc().splitlines()[-1]}
        rows.append({'path': occ.fullPathName, 'component': occ.component.name, 'referenced': occ.isReferencedComponent, 'grounded': occ.isGrounded, 'transform2': list(occ.transform2.asArray()), 'reference': ref})
    return rows


def references(doc):
    refs = doc.documentReferences
    return [{'name': refs.item(i).dataFile.name if refs.item(i).dataFile else None, 'version': refs.item(i).version, 'out_of_date': refs.item(i).isOutOfDate} for i in range(refs.count)]


def timeline(design):
    rows = []
    for item in design.timeline:
        try:
            rows.append({'name': item.name, 'type': item.entity.objectType if item.entity else None, 'suppressed': item.isSuppressed})
        except Exception:
            rows.append({'name': item.name, 'error': traceback.format_exc().splitlines()[-1]})
    return rows


def step(name, doc, note):
    design = design_of(doc)
    entry = {'name': name, 'note': note, 'exports': export_f3d(design, out / (name + '.f3d')), 'occurrences': occurrence_state(design), 'references': references(doc), 'timeline': timeline(design), 'joints': [j.name for j in design.rootComponent.allJoints], 'as_built_joints': [j.name for j in design.rootComponent.allAsBuiltJoints], 'is_saved': doc.isSaved}
    report['steps'].append(entry)
    write(private / 'LinkControls.json', report)


def new_design():
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    opened.append(doc)
    design = design_of(doc)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    return doc, design


def save_as(doc, name, folder, note):
    if not doc.saveAs(name, folder, note, ''):
        raise RuntimeError('saveAs failed: ' + name)
    if not pump(lambda: doc.isSaved and doc.dataFile is not None, 300):
        raise RuntimeError('save did not produce a data file: ' + name)
    complete = pump(lambda: doc.dataFile.isComplete, 300)
    return {'name': name, 'version': doc.dataFile.versionNumber, 'complete': complete}


def box_part(name, parameter, expression, size):
    doc, design = new_design()
    design.userParameters.add(parameter, adsk.core.ValueInput.createByString(expression), 'mm', 'Kit link control height')
    root = design.rootComponent
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(size[0], size[1], 0))
    feature = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), adsk.core.ValueInput.createByString(parameter), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    feature.bodies.item(0).name = name + 'Body'
    return doc


try:
    project, folder = acceptance_folder(app, subfolder=run_name)
    report['folder'] = folder.name
    report['stage'] = 'parts'
    part_a = box_part('KitLinkPartA', 'heightA', '5 mm', (2.0, 1.0))
    step('P_A0_unsaved', part_a, 'Part A before cloud save')
    report['part_a_v1'] = save_as(part_a, 'KitLinkPartA', folder, 'Kit link control part A')
    step('P_A1_saved', part_a, 'Part A after cloud save')
    part_b = box_part('KitLinkPartB', 'heightB', '12 mm', (0.8, 0.8))
    report['part_b_v1'] = save_as(part_b, 'KitLinkPartB', folder, 'Kit link control part B')
    step('P_B1_saved', part_b, 'Part B after cloud save')
    report['stage'] = 'subassembly'
    sub, sub_design = new_design()
    occ_b = sub_design.rootComponent.occurrences.addByInsert(part_b.dataFile, matrix(0.0, (0, 0, 1), (1.0, 2.0, 0.0)), True)
    if occ_b is None:
        raise RuntimeError('Part B insert failed')
    step('S0_inserted', sub, 'Subassembly with Part B reference at translation (1,2,0) cm')
    report['sub_v1'] = save_as(sub, 'KitLinkSub', folder, 'Kit link control subassembly')
    step('S1_saved', sub, 'Subassembly after cloud save')
    report['stage'] = 'root'
    root_doc, root_design = new_design()
    step('R0_empty', root_doc, 'Empty root design')
    occ_a = root_design.rootComponent.occurrences.addByInsert(part_a.dataFile, matrix(30.0, (0, 0, 1), (5.0, 2.0, 1.0)), True)
    if occ_a is None:
        raise RuntimeError('Part A insert failed')
    step('R1_part_a', root_doc, 'Part A reference, rotation 30 deg about Z, translation (5,2,1) cm')
    occ_a.isGrounded = True
    step('R2_grounded', root_doc, 'Part A occurrence grounded')
    occ_s = root_design.rootComponent.occurrences.addByInsert(sub.dataFile, matrix(90.0, (1, 0, 0), (0.0, 6.0, 0.0)), True)
    if occ_s is None:
        raise RuntimeError('Subassembly insert failed')
    step('R3_nested', root_doc, 'Subassembly reference, rotation 90 deg about X, translation (0,6,0) cm')
    joint_input = root_design.rootComponent.asBuiltJoints.createInput(occ_a, occ_s, None)
    joint_input.setAsRigidJointMotion()
    joint = root_design.rootComponent.asBuiltJoints.add(joint_input)
    if joint is None:
        raise RuntimeError('As-built joint failed')
    step('R4_joint', root_doc, 'Rigid as-built joint between Part A and subassembly occurrences')
    report['root_v1'] = save_as(root_doc, 'KitLinkRoot', folder, 'Kit link control root')
    step('R5_saved', root_doc, 'Root after cloud save')
    report['stage'] = 'part_a_v2'
    design_of(part_a).userParameters.itemByName('heightA').expression = '8 mm'
    if not part_a.save('Kit link control part A height 8 mm'):
        raise RuntimeError('Part A version 2 save failed')
    report['part_a_v2_saved'] = pump(lambda: part_a.dataFile.versionNumber >= 2 and part_a.dataFile.isComplete, 300)
    report['part_a_v2'] = {'version': part_a.dataFile.versionNumber, 'complete': part_a.dataFile.isComplete}
    report['root_out_of_date'] = pump(lambda: any(item['out_of_date'] for item in references(root_doc)), 180)
    step('R6_out_of_date', root_doc, 'Root after Part A version 2, before reference update')
    report['update_all'] = root_doc.updateAllReferences()
    step('R7_updated', root_doc, 'Root after updateAllReferences')
    if not root_doc.save('Kit link control root updated references'):
        raise RuntimeError('Root version 2 save failed')
    pump(lambda: root_doc.dataFile.versionNumber >= 2, 300)
    report['root_v2'] = {'version': root_doc.dataFile.versionNumber, 'complete': root_doc.dataFile.isComplete}
    step('R8_updated_saved', root_doc, 'Root version 2 after cloud save')
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
    raise
finally:
    for doc in reversed(opened):
        try:
            if doc.isValid:
                doc.close(False)
        except Exception:
            report.setdefault('close_errors', []).append(traceback.format_exc())
    report['documents_after'] = app.documents.count
    write(private / 'LinkControls.json', report)
