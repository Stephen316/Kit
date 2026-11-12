"""Study-owned AlongPath/FitOnPath SketchText source and definition contrasts."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ('line_along_above', 'line_along_below', 'line_along_center_spacing',
         'line_fit_above', 'arc_along_above', 'arc_fit_above')


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/('sketchtextpaths-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': [],
             'sdk_methods': ['SketchTexts.createInput3', 'SketchTextInput.setAsAlongPath', 'SketchTextInput.setAsFitOnPath'],
             'identity_scope': 'API entity tokens are opaque. Curve study labels are generator labels; parent-sketch names are actual getters. Numeric native IDs/tags are not inferred from tokens.'}
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    point = adsk.core.Point3D.create
    for case in cases:
        doc, design = None, None
        sample = {'file': case+'.f3d', 'case': case, 'getter_errors': []}
        try:
            if case not in CASES:
                raise ValueError('Unknown SketchText path case: '+str(case))
            (output/'progress.json').write_text(json.dumps({'case':case,'phase':'creating_document'})+'\n')
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = 'SketchTextPathProbe'

            def read(field, getter):
                try:
                    return getter()
                except Exception:
                    sample['getter_errors'].append({'field': field, 'error': traceback.format_exc()})
                    return None

            def curve_truth(curve, field):
                if curve is None:
                    return None
                result = {'entity_type': read(field+'.entity_type', lambda: curve.objectType),
                          'entity_token': read(field+'.entity_token', lambda: curve.entityToken),
                          'sketch_name': read(field+'.sketch_name', lambda: curve.parentSketch.name),
                          'sketch_entity_token': read(field+'.sketch_entity_token', lambda: curve.parentSketch.entityToken)}
                for key, getter in (
                    ('is_construction', lambda: curve.isConstruction), ('is_fixed', lambda: curve.isFixed),
                    ('is_reference', lambda: curve.isReference), ('is_2d', lambda: curve.is2D),
                    ('start_sketch_cm', lambda: curve.startSketchPoint.geometry.asArray()),
                    ('end_sketch_cm', lambda: curve.endSketchPoint.geometry.asArray()),
                    ('start_world_cm', lambda: curve.startSketchPoint.worldGeometry.asArray()),
                    ('end_world_cm', lambda: curve.endSketchPoint.worldGeometry.asArray())):
                    result[key] = read(field+'.'+key, getter)
                arc = adsk.fusion.SketchArc.cast(curve)
                if arc:
                    for key, getter in (
                        ('center_sketch_cm', lambda: arc.centerSketchPoint.geometry.asArray()),
                        ('center_world_cm', lambda: arc.centerSketchPoint.worldGeometry.asArray()),
                        ('radius_cm', lambda: arc.geometry.radius),
                        ('start_angle_radians', lambda: arc.geometry.startAngle),
                        ('end_angle_radians', lambda: arc.geometry.endAngle),
                        ('normal', lambda: arc.geometry.normal.asArray())):
                        result[key] = read(field+'.'+key, getter)
                return result

            def definition_truth(definition, field):
                if definition is None:
                    return None
                result = {'entity_type': read(field+'.entity_type', lambda: definition.objectType),
                          'is_above_path': read(field+'.is_above_path', lambda: definition.isAbovePath)}
                path = read(field+'.path', lambda: definition.path)
                result['path'] = curve_truth(path, field+'.path')
                along = adsk.fusion.AlongPathTextDefinition.cast(definition)
                if along:
                    result['horizontal_alignment'] = read(field+'.horizontal_alignment', lambda: along.horizontalAlignment)
                    result['character_spacing_percent'] = read(field+'.character_spacing_percent', lambda: along.characterSpacing)
                else:
                    result['horizontal_alignment'] = None
                    result['character_spacing_percent'] = None
                return result

            def parameter_truth(parameter, field, is_text):
                if parameter is None:
                    return None
                result = {key: read(field+'.'+key, getter) for key, getter in (
                    ('name', lambda: parameter.name), ('role', lambda: parameter.role),
                    ('expression', lambda: parameter.expression), ('unit', lambda: parameter.unit),
                    ('entity_token', lambda: parameter.entityToken))}
                result['text_value' if is_text else 'value_cm'] = read(field+'.value', lambda: parameter.textValue if is_text else parameter.value)
                return result

            if case.startswith('arc_'):
                curve = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(point(5, 5, 0), point(1, 5, 0), math.pi/2)
            else:
                curve = sketch.sketchCurves.sketchLines.addByTwoPoints(point(1, 1, 0), point(9, 1, 0))
            sample['source_curve_label'] = 'StudySketchTextPathCurve'
            sample['source_curve_before_text'] = curve_truth(curve, 'source_curve')
            above = case != 'line_along_below'
            fit = '_fit_' in case
            alignment = adsk.core.HorizontalAlignments.CenterHorizontalAlignment if case == 'line_along_center_spacing' else adsk.core.HorizontalAlignments.LeftHorizontalAlignment
            spacing = 20. if case == 'line_along_center_spacing' else 0.
            sample['requested'] = {'text': 'KIT', 'height_expression': '5 mm', 'font_name': 'Arial', 'text_style': 0,
                                   'is_horizontal_flip': False, 'is_vertical_flip': False,
                                   'layout': 'FitOnPath' if fit else 'AlongPath', 'is_above_path': above,
                                   'horizontal_alignment': None if fit else alignment,
                                   'character_spacing_percent': None if fit else spacing}
            inputs = sketch.sketchTexts.createInput3("'KIT'", adsk.core.ValueInput.createByString('5 mm'))
            inputs.fontName, inputs.textStyle = 'Arial', 0
            inputs.isHorizontalFlip, inputs.isVerticalFlip = False, False
            accepted = inputs.setAsFitOnPath(curve, above) if fit else inputs.setAsAlongPath(curve, above, alignment, spacing)
            sample['setter_returned'] = accepted
            if not accepted:
                raise RuntimeError('Documented SketchText path definition setter returned false')
            sample['input_definition'] = definition_truth(read('input.definition', lambda: inputs.definition), 'input.definition')
            text = sketch.sketchTexts.add(inputs)
            if text is None:
                raise RuntimeError('SketchTexts.add returned null')
            design.timeline.moveToEnd()
            settings = {'entity_type': read('text.entity_type', lambda: text.objectType),
                        'entity_token': read('text.entity_token', lambda: text.entityToken),
                        'sketch_name': read('text.sketch_name', lambda: text.parentSketch.name)}
            for key, getter in (
                ('font_name', lambda: text.fontName), ('text_style', lambda: text.textStyle),
                ('is_horizontal_flip', lambda: text.isHorizontalFlip), ('is_vertical_flip', lambda: text.isVerticalFlip),
                ('is_fixed', lambda: text.isFixed), ('is_reference', lambda: text.isReference), ('is_2d', lambda: text.is2D)):
                settings[key] = read('text.'+key, getter)
            settings['text_parameter'] = parameter_truth(read('text.text_parameter', lambda: text.textParameter), 'text.text_parameter', True)
            settings['height_parameter'] = parameter_truth(read('text.height_parameter', lambda: text.heightParameter), 'text.height_parameter', False)
            settings['definition'] = definition_truth(read('text.definition', lambda: text.definition), 'text.definition')
            settings['sketch_text_count'] = read('text.sketch_text_count', lambda: sketch.sketchTexts.count)
            settings['bounding_box_sketch_cm'] = read('text.bounding_box_sketch_cm', lambda: [text.boundingBox.minPoint.asArray(), text.boundingBox.maxPoint.asArray()])
            settings['source_curve_after_text'] = curve_truth(curve, 'source_curve_after_text')
            sample['settings'] = settings
            design.timeline.moveToEnd()
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('SketchText path local export failed')
            truth['samples'].append(sample)
        except Exception:
            truth['errors'].append({'case': case, 'error': traceback.format_exc(), 'partial_capture': sample})
        finally:
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    truth['errors'].append({'case': case, 'cleanup': 'timeline restore', 'error': traceback.format_exc()})
            if doc is not None:
                try:
                    doc.close(False)
                except Exception:
                    truth['errors'].append({'case': case, 'cleanup': 'owned document close(False)', 'error': traceback.format_exc()})
            (output/'ground_truth.json').write_text(json.dumps(truth, indent=2))
    (output/'complete.txt').write_text('SketchText path generation finished; consult errors.\n')
