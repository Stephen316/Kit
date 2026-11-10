"""Owned Move definition examples with actual API inputs and output bounds."""
import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/('movemodes-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    cases = ['free', 'xyz_design', 'xyz_component', 'xyz_nested_design', 'along_axis',
             'along_sketch_line', 'rotate_axis', 'point_to_point', 'point_to_position']
    if isinstance(context, dict) and 'cases' in context:
        cases = context['cases']

    def bounds(body):
        box = body.boundingBox
        return {'min_cm': box.minPoint.asArray(), 'max_cm': box.maxPoint.asArray()}

    def entity(e):
        result = {'kind': e.objectType.split('::')[-1]}
        if hasattr(e, 'name'):
            result['name'] = e.name
        if adsk.fusion.ConstructionAxis.cast(e):
            result.update(origin_cm=e.geometry.origin.asArray(), direction=e.geometry.direction.asArray())
        elif adsk.fusion.ConstructionPoint.cast(e):
            result['point_cm'] = e.geometry.asArray()
        elif adsk.fusion.SketchLine.cast(e):
            result.update(start_cm=e.worldGeometry.startPoint.asArray(), end_cm=e.worldGeometry.endPoint.asArray())
        return result

    for case in cases:
        doc = None
        try:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            component = root
            occurrence = None
            if case in ('xyz_component', 'xyz_nested_design', 'point_to_position_nested_design'):
                placement = adsk.core.Matrix3D.create()
                placement.setToRotation(math.pi/4, adsk.core.Vector3D.create(0, 0, 1), point(0, 0, 0))
                placement.translation = adsk.core.Vector3D.create(4, -2, 1)
                occurrence = root.occurrences.addNewComponent(placement)
                component = occurrence.component
                component.name = 'MovedComponent'
            sketch = component.sketches.add(component.xYConstructionPlane)
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(2, 1, 0))
            seed = component.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value('10 mm'),
                         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            body = seed.bodies.item(0)
            body.name = 'MovedBody'
            before = bounds(body)
            selected = adsk.core.ObjectCollection.create()
            selected.add(body)
            move_input = component.features.moveFeatures.createInput2(selected)

            def construction_point(x, y, name):
                support = component.sketches.add(component.xYConstructionPlane)
                p = support.sketchPoints.add(point(x, y, 0))
                inputs = component.constructionPoints.createInput()
                if not inputs.setByPoint(p):
                    raise RuntimeError('Construction point definition rejected')
                result = component.constructionPoints.add(inputs)
                result.name = name
                return result

            if case == 'free':
                transform = adsk.core.Matrix3D.create()
                transform.setToRotation(math.radians(20), adsk.core.Vector3D.create(0, 0, 1), point(0, 0, 0))
                transform.translation = adsk.core.Vector3D.create(1, -.5, .8)
                ok = move_input.defineAsFreeMove(transform)
            elif case.startswith('xyz_'):
                ok = move_input.defineAsTranslateXYZ(value('11 mm'), value('-5 mm'), value('7 mm'), case != 'xyz_component')
            elif case == 'along_axis':
                ok = move_input.defineAsTranslateAlongEntity(component.yConstructionAxis, value('-13 mm'))
            elif case == 'along_sketch_line':
                path_sketch = component.sketches.add(component.xYConstructionPlane)
                path_sketch.name = 'MoveDirection'
                line = path_sketch.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(3, 4, 0))
                ok = move_input.defineAsTranslateAlongEntity(line, value('15 mm'))
            elif case == 'rotate_axis':
                ok = move_input.defineAsRotate(component.zConstructionAxis, value('-35 deg'))
            elif case == 'point_to_point':
                ok = move_input.defineAsPointToPoint(component.originConstructionPoint, construction_point(1.3, -.7, 'DestinationPoint'))
            else:
                ok = move_input.defineAsPointToPosition(construction_point(.4, .8, 'MoveOrigin'), value('11 mm'),
                                                       value('-5 mm'), value('7 mm'), case != 'point_to_position_component')
            if not ok:
                raise RuntimeError('Move definition rejected')
            feature = component.features.moveFeatures.add(move_input)
            if feature is None:
                raise RuntimeError('Move add returned null')
            feature.name = 'ProbeMove'
            sample = {'file': case+'.f3d', 'before_bounds': before,
                      'after_bounds': bounds(feature.bodies.item(0)),
                      'component_name': component.name,
                      'occurrence_transform': occurrence.transform2.asArray() if occurrence else None,
                      'health_state': feature.healthState, 'warning': feature.errorOrWarningMessage}
            feature.timelineObject.rollTo(True)
            definition = feature.definition
            settings = {'definition_type': definition.objectType.split('::')[-1],
                        'input_names': [feature.inputEntities.item(i).name for i in range(feature.inputEntities.count)]}
            if case == 'free':
                settings['transform'] = definition.transform.asArray()
            elif case.startswith('xyz_') or case.startswith('point_to_position'):
                settings.update(x_distance_cm=definition.xDistance.value, y_distance_cm=definition.yDistance.value,
                                z_distance_cm=definition.zDistance.value, is_design_space=definition.isDesignSpace)
                if case.startswith('point_to_position'):
                    settings['point'] = entity(definition.point)
            elif case.startswith('along_'):
                settings.update(distance_cm=definition.distance.value, linear_entity=entity(definition.linearEntity))
            elif case == 'rotate_axis':
                settings.update(angle_radians=definition.angle.value, axis_entity=entity(definition.axisEntity))
            else:
                settings.update(origin_point=entity(definition.originPoint), target_point=entity(definition.targetPoint))
            sample['settings'] = settings
            design.timeline.moveToEnd()
            sample['parameters'] = [{'name': p.name, 'role': p.role, 'value': p.value, 'unit': p.unit,
                                    'created_by': getattr(p.createdBy, 'name', None)} for p in component.modelParameters]
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('Move export failed')
            truth['samples'].append(sample)
        except Exception:
            truth['errors'].append({'case': case, 'error': traceback.format_exc()})
        finally:
            if doc is not None:
                doc.close(False)
            (output/'ground_truth.json').write_text(json.dumps(truth, indent=2))
    (output/'complete.txt').write_text('Move capture finished; inspect errors.\n')
