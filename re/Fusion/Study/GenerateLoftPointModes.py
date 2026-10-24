"""Capture four study-owned Loft sketch-point endpoint condition contrasts."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ('sharp_end', 'sharp_start', 'tangent_end_weight1', 'tangent_end_weight2')


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/('loftpoints-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': [],
             'identity_scope': 'API entity tokens are opaque evidence, not decoded native sketch IDs. Parent sketch name/token and actual entity types identify API selections.'}
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    point = adsk.core.Point3D.create
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        sample = {'file': case+'.f3d', 'case': case, 'getter_errors': []}
        try:
            if case not in CASES:
                raise ValueError('Unknown point loft case: '+str(case))
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent

            def read(field, getter):
                try:
                    return getter()
                except Exception:
                    sample['getter_errors'].append({'field': field, 'error': traceback.format_exc()})
                    return None

            def body_evidence(body, field):
                return {key: read(field+'.'+key, getter) for key, getter in (
                    ('name', lambda: body.name), ('entity_token', lambda: body.entityToken),
                    ('component_name', lambda: body.parentComponent.name),
                    ('is_solid', lambda: body.isSolid), ('volume_cm3', lambda: body.volume),
                    ('bounding_box_min_cm', lambda: body.boundingBox.minPoint.asArray()),
                    ('bounding_box_max_cm', lambda: body.boundingBox.maxPoint.asArray()))}

            def entity_evidence(entity, field):
                result = {'entity_type': read(field+'.entity_type', lambda: entity.objectType),
                          'entity_token': read(field+'.entity_token', lambda: entity.entityToken)}
                selected_point = adsk.fusion.SketchPoint.cast(entity)
                profile = adsk.fusion.Profile.cast(entity)
                sketch = selected_point.parentSketch if selected_point else profile.parentSketch if profile else None
                if sketch:
                    result.update(sketch_name=read(field+'.sketch_name', lambda: sketch.name),
                                  sketch_entity_token=read(field+'.sketch_entity_token', lambda: sketch.entityToken))
                if selected_point:
                    result.update(sketch_point_cm=read(field+'.sketch_point_cm', lambda: selected_point.geometry.asArray()),
                                  world_point_cm=read(field+'.world_point_cm', lambda: selected_point.worldGeometry.asArray()))
                if profile:
                    result['profile_loop_count'] = read(field+'.profile_loop_count', lambda: profile.profileLoops.count)
                    loops = []
                    for loop_index in range(profile.profileLoops.count):
                        loop = profile.profileLoops.item(loop_index)
                        path = field+'.loops.'+str(loop_index)
                        curves = []
                        for curve_index in range(loop.profileCurves.count):
                            curve = loop.profileCurves.item(curve_index).sketchEntity
                            curve_path = path+'.curves.'+str(curve_index)
                            entry = {'entity_type': read(curve_path+'.entity_type', lambda: curve.objectType),
                                     'entity_token': read(curve_path+'.entity_token', lambda: curve.entityToken)}
                            circle = adsk.fusion.SketchCircle.cast(curve)
                            if circle:
                                entry.update(center_world_cm=read(curve_path+'.center_world_cm', lambda: circle.centerSketchPoint.worldGeometry.asArray()),
                                             radius_cm=read(curve_path+'.radius_cm', lambda: circle.radius))
                            curves.append(entry)
                        loops.append({'is_outer': read(path+'.is_outer', lambda: loop.isOuter), 'curves': curves})
                    result['profile_loops'] = loops
                return result

            sources = []
            for index, height in enumerate((0., 3.)):
                plane = root.xYConstructionPlane
                if height:
                    plane_input = root.constructionPlanes.createInput()
                    if not plane_input.setByOffset(plane, adsk.core.ValueInput.createByReal(height)):
                        raise RuntimeError('Point loft section plane rejected')
                    plane = root.constructionPlanes.add(plane_input)
                sketch = root.sketches.add(plane)
                sketch.name = 'LoftPointSection'+str(index+1)
                is_point = index == (0 if case == 'sharp_start' else 1)
                if is_point:
                    entity = sketch.sketchPoints.add(point(0, 0, 0))
                else:
                    sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 1.)
                    entity = sketch.profiles.item(0)
                sources.append(entity)
            sample['source_entities_before_loft'] = [entity_evidence(entity, 'source'+str(i)) for i, entity in enumerate(sources)]
            inputs = root.features.loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            inputs.isSolid, inputs.isClosed = True, False
            sections = [inputs.loftSections.add(entity) for entity in sources]
            point_index = 0 if case == 'sharp_start' else 1
            if case.startswith('tangent_'):
                weight = 2. if case.endswith('weight2') else 1.
                accepted = sections[point_index].setPointTangentEndCondition(adsk.core.ValueInput.createByReal(weight))
                sample['requested_condition'] = {'type': 'PointTangent', 'section_index': point_index, 'weight': weight}
            else:
                accepted = sections[point_index].setPointSharpEndCondition()
                sample['requested_condition'] = {'type': 'PointSharp', 'section_index': point_index}
            if not accepted:
                raise RuntimeError('Point loft endpoint condition rejected')
            feature = root.features.loftFeatures.add(inputs)
            feature.name = 'ProbeLoftPoint'
            settings = {'requested_operation': adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                        'result_bodies': [body_evidence(body, 'result_body'+str(i)) for i, body in enumerate(feature.bodies)]}
            feature.timelineObject.rollTo(True)
            for key, getter in (
                    ('operation', lambda: feature.operation), ('is_solid', lambda: feature.isSolid),
                    ('is_closed', lambda: feature.isClosed), ('is_tangent_edges_merged', lambda: feature.isTangentEdgesMerged),
                    ('section_count', lambda: feature.loftSections.count), ('guide_count', lambda: feature.centerLineOrRails.count),
                    ('is_centerline', lambda: feature.centerLineOrRails.isCenterLine)):
                settings[key] = read('settings.'+key, getter)
            settings['sections'] = []
            for index in range(feature.loftSections.count):
                section = feature.loftSections.item(index)
                field = 'sections.'+str(index)
                entity = section.entity
                item = entity_evidence(entity, field+'.entity')
                item['index'] = read(field+'.index', lambda: section.index)
                condition = read(field+'.end_condition', lambda: section.endCondition)
                item['end_condition_type'] = read(field+'.end_condition_type', lambda: condition.objectType) if condition else None
                tangent = adsk.fusion.LoftPointTangentEndCondition.cast(condition) if condition else None
                if tangent:
                    item['weight'] = read(field+'.weight', lambda: tangent.weight.value)
                settings['sections'].append(item)
            design.timeline.moveToEnd()
            sample['settings'] = settings
            sample['parameters'] = []
            for index, parameter in enumerate(root.modelParameters):
                field = 'parameters.'+str(index)
                item = {key: read(field+'.'+key, getter) for key, getter in (
                    ('name', lambda: parameter.name), ('role', lambda: parameter.role),
                    ('value', lambda: parameter.value), ('unit', lambda: parameter.unit),
                    ('created_by', lambda: getattr(parameter.createdBy, 'name', None)))}
                sample['parameters'].append(item)
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('Point loft export failed')
            truth['samples'].append(sample)
        except Exception:
            truth['errors'].append({'case': case, 'error': traceback.format_exc(), 'partial_capture': sample})
        finally:
            doc.close(False)
            (output/'ground_truth.json').write_text(json.dumps(truth, indent=2))
    (output/'complete.txt').write_text('Point loft capture finished; consult errors.\n')
