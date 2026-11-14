import sys
from pathlib import Path
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
import adsk.fusion
from LinkCommon import acceptance_folder, design_of, digest, export_f3d, private, pump, write

run_name = 'Run1'
out = private / 'configs'
out.mkdir(parents=True, exist_ok=True)
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'run': run_name, 'documents_before': app.documents.count, 'steps': []}
opened = []


def safe(call):
    try:
        return call()
    except Exception:
        return {'error': traceback.format_exc().splitlines()[-1]}


def cell_state(cell):
    kind = cell.objectType
    row = {'type': kind}
    if kind.endswith('ConfigurationParameterCell'):
        row.update(expression=cell.expression, value=safe(lambda: cell.value))
    elif kind.endswith('ConfigurationSuppressCell'):
        row.update(suppressed=cell.isSuppressed)
    elif kind.endswith('ConfigurationAppearanceCell'):
        row.update(appearance=safe(lambda: cell.appearance.name if cell.appearance else None))
    return row


def table_state(table):
    if table is None:
        return None
    columns = [{'id': c.id, 'title': c.title, 'type': c.objectType, 'index': c.index} for c in table.columns]
    rows = []
    for row in table.rows:
        cells = {}
        for column in table.columns:
            cells[column.id] = safe(lambda: cell_state(row.getCellByColumnId(column.id)))
        rows.append({'id': row.id, 'name': row.name, 'index': row.index, 'test': safe(lambda: row.isTestRow), 'cells': cells})
    return {'name': table.name, 'type': table.objectType, 'columns': columns, 'rows': rows}


def config_state(design):
    if not design.isConfiguredDesign:
        return {'configured': False}
    top = design.configurationTopTable
    state = {'configured': True, 'top': table_state(top), 'active_row': safe(lambda: {'id': top.activeRow.id, 'name': top.activeRow.name})}
    state['appearance'] = safe(lambda: table_state(top.appearanceTable))
    return state


def model_state(design):
    root = design.rootComponent
    return {
        'parameters': {p.name: {'expression': p.expression, 'value': p.value} for p in design.allParameters if p.name in ('lengthC', 'holeR')},
        'bodies': [{'name': b.name, 'volume_cm3': b.volume, 'faces': b.faces.count, 'appearance': safe(lambda: b.appearance.name)} for b in root.bRepBodies],
        'timeline': [{'name': t.name, 'suppressed': t.isSuppressed} for t in design.timeline],
    }


def step(name, doc, note, extension='.f3d'):
    design = design_of(doc)
    entry = {'name': name, 'note': note, 'config': safe(lambda: config_state(design)), 'model': safe(lambda: model_state(design))}
    entry['exports'] = safe(lambda: export_f3d(design, out / (name + extension)))
    report['steps'].append(entry)
    write(private / 'ConfigControls.json', report)


def save_as(doc, name, folder, note):
    if not doc.saveAs(name, folder, note, ''):
        raise RuntimeError('saveAs failed: ' + name)
    if not pump(lambda: doc.isSaved and doc.dataFile is not None, 300):
        raise RuntimeError('save did not produce a data file: ' + name)
    complete = pump(lambda: doc.dataFile.isComplete, 300)
    return {'name': name, 'version': doc.dataFile.versionNumber, 'complete': complete}


try:
    project, folder = acceptance_folder(app, subfolder=run_name)
    report['stage'] = 'archive_probe'
    root_file = None
    for index in range(folder.dataFiles.count):
        if folder.dataFiles.item(index).name == 'KitLinkRoot':
            root_file = folder.dataFiles.item(index)
    if root_file is not None:
        link_doc = app.documents.open(root_file, False)
        opened.append(link_doc)
        report['link_archive'] = safe(lambda: export_f3d(design_of(link_doc), private / 'links' / 'R9_archive.f3z'))
        report['link_documents_open'] = app.documents.count
        link_doc.close(False)
        opened.remove(link_doc)
    report['stage'] = 'part'
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    opened.append(doc)
    design = design_of(doc)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    length = design.userParameters.add('lengthC', adsk.core.ValueInput.createByString('30 mm'), 'mm', 'Kit configured length')
    root = design.rootComponent
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(3, 2, 0))
    base = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), adsk.core.ValueInput.createByString('lengthC'), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    body = base.bodies.item(0)
    body.name = 'KitCfgBody'
    hole_sketch = root.sketches.add(root.xYConstructionPlane)
    hole_sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(1.5, 1.0, 0), 0.4)
    hole_profile = None
    for index in range(hole_sketch.profiles.count):
        candidate = hole_sketch.profiles.item(index)
        if abs(candidate.areaProperties().area - 3.141592653589793 * 0.16) < 1e-6:
            hole_profile = candidate
    hole = root.features.extrudeFeatures.addSimple(hole_profile, adsk.core.ValueInput.createByString('lengthC'), adsk.fusion.FeatureOperations.CutFeatureOperation)
    hole.name = 'KitCfgHole'
    report['part'] = save_as(doc, 'KitCfgPart', folder, 'Kit configuration control part')
    step('C0_plain', doc, 'Saved part before configuration')
    report['stage'] = 'configured'
    top = design.createConfiguredDesign()
    if top is None:
        raise RuntimeError('createConfiguredDesign returned null')
    step('C1_configured', doc, 'Configured design with one row and no columns')
    param_column = top.columns.addParameterColumn(design.userParameters.itemByName('lengthC'))
    step('C2_param_column', doc, 'Parameter column for lengthC')
    long_row = top.rows.add('Long')
    step('C3a_row_added', doc, 'Second row Long with default cells')
    adsk.fusion.ConfigurationParameterCell.cast(long_row.getCellByColumnId(param_column.id)).expression = '50 mm'
    step('C3b_row_value', doc, 'Row Long lengthC expression 50 mm')
    suppress_column = top.columns.addSuppressColumn(hole)
    step('C4a_suppress_column', doc, 'Suppression column for KitCfgHole')
    adsk.fusion.ConfigurationSuppressCell.cast(long_row.getCellByColumnId(suppress_column.id)).isSuppressed = True
    step('C4b_suppressed', doc, 'Row Long suppresses KitCfgHole')
    report['stage'] = 'appearance'
    appearance_table = top.appearanceTable
    appearance_column = appearance_table.columns.add(body)
    step('C5a_appearance_column', doc, 'Appearance column for KitCfgBody')
    library = app.materialLibraries.itemByName('Fusion Appearance Library')
    red = None
    for name in ('Paint - Enamel Glossy (Red)', 'Plastic - Matte (Red)'):
        red = library.appearances.itemByName(name) if library else None
        if red is not None:
            break
    report['appearance_choice'] = red.name if red else None
    appearance_row = appearance_table.rows.item(0)
    report['appearance_rows'] = [{'id': r.id, 'name': r.name} for r in appearance_table.rows]
    if red is not None:
        local = design.appearances.itemByName(red.name) or design.appearances.addByCopy(red, red.name)
        adsk.fusion.ConfigurationAppearanceCell.cast(appearance_column.getCell(0)).appearance = local
    step('C5b_appearance_value', doc, 'Appearance table first row uses a red appearance')
    short_row = top.rows.add('Short')
    adsk.fusion.ConfigurationParameterCell.cast(short_row.getCellByColumnId(param_column.id)).expression = '15 mm'
    step('C6_third_row', doc, 'Third row Short with lengthC 15 mm')
    report['stage'] = 'activate'
    report['activate_long'] = long_row.activate()
    step('C7_active_long', doc, 'Row Long active')
    report['stage'] = 'rules'
    manager = design.configurationRulesManager
    report['rules_manager'] = manager is not None
    if manager is not None:
        result = safe(lambda: manager.addRule('KitRuleA'))
        if isinstance(result, dict):
            report['rule_add'] = result
        else:
            report['rule_add'] = {'issues': [safe(lambda: {'code': i.code, 'message': i.message}) for i in result.issues], 'rule': safe(lambda: result.rule.toJson())}
        report['rules_after'] = safe(lambda: [r.toJson() for r in manager.getRules().rules])
    step('C8_rule', doc, 'After adding rule KitRuleA')
    report['activate_first'] = top.rows.item(0).activate()
    step('C9_active_first', doc, 'First row active again')
    if not doc.save('Kit configuration control complete'):
        raise RuntimeError('Configured save failed')
    pump(lambda: doc.dataFile.versionNumber >= 2, 300)
    report['saved_version'] = doc.dataFile.versionNumber
    step('C10_saved', doc, 'Configured design after save')
    step('C11_archive', doc, 'Configured design archive export', '.f3z')
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
    raise
finally:
    for item in reversed(opened):
        try:
            if item.isValid:
                item.close(False)
        except Exception:
            report.setdefault('close_errors', []).append(traceback.format_exc())
    report['documents_after'] = app.documents.count
    write(private / 'ConfigControls.json', report)
