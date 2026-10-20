"""Capture BRepFace Loft sections and actual Free/Tangent/Smooth conditions.

The SDK documents face sections but warns Tangent/Smooth setters are ignored
without BRepEdge sections. Setter results and actual conditions are independent.
"""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ('face_free', 'face_tangent_weight1', 'edge_path_tangent_weight1',
         'edge_path_tangent_weight2', 'edge_path_smooth_weight1')


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/('loftfaces-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': [],
             'sdk_caveat': 'LoftSections.add accepts BRepFace; Tangent/Smooth setter docs say ignored unless section defined by BRepEdge. Actual getters determine captured behavior.',
             'identity_scope': 'API entity tokens/tempIds retained as opaque evidence; no native numeric ID or ASM identity interpretation.'}
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByReal
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        sample = {'file': case+'.f3d', 'case': case, 'getter_errors': []}
        try:
            if case not in CASES:
                raise ValueError('Unknown face Loft case: '+str(case))
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
                    ('component_name', lambda: body.parentComponent.name), ('is_solid', lambda: body.isSolid),
                    ('volume_cm3', lambda: body.volume), ('face_count', lambda: body.faces.count),
                    ('edge_count', lambda: body.edges.count),
                    ('bounding_box_min_cm', lambda: body.boundingBox.minPoint.asArray()),
                    ('bounding_box_max_cm', lambda: body.boundingBox.maxPoint.asArray()))}

            def entity_evidence(entity, field):
                if entity is None:
                    return None
                result = {'entity_type': read(field+'.entity_type', lambda: entity.objectType)}
                selected_path = adsk.fusion.Path.cast(entity)
                if selected_path:
                    result['count'] = read(field+'.count', lambda: selected_path.count)
                    result['segments'] = []
                    for i in range(result['count'] or 0):
                        segment = selected_path.item(i)
                        segment_field = field+'.segments.'+str(i)
                        member = read(segment_field+'.entity', lambda: segment.entity)
                        result['segments'].append({'is_opposed_to_entity': read(segment_field+'.is_opposed_to_entity', lambda: segment.isOpposedToEntity),
                                                   'entity': entity_evidence(member, segment_field+'.entity')})
                    return result
                result['entity_token'] = read(field+'.entity_token', lambda: entity.entityToken)
                edge = adsk.fusion.BRepEdge.cast(entity)
                if edge:
                    result.update(temp_id=read(field+'.temp_id', lambda: edge.tempId),
                                  body=body_evidence(edge.body, field+'.body'),
                                  geometry_type=read(field+'.geometry_type', lambda: edge.geometry.objectType),
                                  start_world_cm=read(field+'.start_world_cm', lambda: edge.startVertex.geometry.asArray()),
                                  end_world_cm=read(field+'.end_world_cm', lambda: edge.endVertex.geometry.asArray()))
                    circle = adsk.core.Circle3D.cast(edge.geometry)
                    if circle:
                        result.update(center_world_cm=read(field+'.center_world_cm', lambda: circle.center.asArray()),
                                      normal=read(field+'.normal', lambda: circle.normal.asArray()),
                                      radius_cm=read(field+'.radius_cm', lambda: circle.radius))
                face = adsk.fusion.BRepFace.cast(entity)
                profile = adsk.fusion.Profile.cast(entity)
                if face:
                    result.update(temp_id=read(field+'.temp_id', lambda: face.tempId),
                                  body=body_evidence(face.body, field+'.body'),
                                  geometry_type=read(field+'.geometry_type', lambda: face.geometry.objectType),
                                  area_cm2=read(field+'.area_cm2', lambda: face.area),
                                  centroid_world_cm=read(field+'.centroid_world_cm', lambda: face.centroid.asArray()),
                                  plane_origin_cm=read(field+'.plane_origin_cm', lambda: adsk.core.Plane.cast(face.geometry).origin.asArray()),
                                  plane_normal=read(field+'.plane_normal', lambda: adsk.core.Plane.cast(face.geometry).normal.asArray()),
                                  is_param_reversed=read(field+'.is_param_reversed', lambda: face.isParamReversed),
                                  loop_count=read(field+'.loop_count', lambda: face.loops.count))
                    edges = []
                    count = read(field+'.edge_count', lambda: face.edges.count)
                    for i in range(count or 0):
                        edge = face.edges.item(i)
                        edge_field = field+'.edges.'+str(i)
                        entry = {key: read(edge_field+'.'+key, getter) for key, getter in (
                            ('entity_token', lambda: edge.entityToken), ('temp_id', lambda: edge.tempId),
                            ('geometry_type', lambda: edge.geometry.objectType),
                            ('body_name', lambda: edge.body.name),
                            ('start_world_cm', lambda: edge.startVertex.geometry.asArray()),
                            ('end_world_cm', lambda: edge.endVertex.geometry.asArray()))}
                        circle = adsk.core.Circle3D.cast(edge.geometry)
                        if circle:
                            entry.update(center_world_cm=read(edge_field+'.center_world_cm', lambda: circle.center.asArray()),
                                         normal=read(edge_field+'.normal', lambda: circle.normal.asArray()),
                                         radius_cm=read(edge_field+'.radius_cm', lambda: circle.radius))
                        edges.append(entry)
                    result['edges'] = edges
                if profile:
                    result.update(sketch_name=read(field+'.sketch_name', lambda: profile.parentSketch.name),
                                  sketch_entity_token=read(field+'.sketch_entity_token', lambda: profile.parentSketch.entityToken),
                                  profile_loop_count=read(field+'.profile_loop_count', lambda: profile.profileLoops.count))
                    loops = []
                    for i in range(result['profile_loop_count'] or 0):
                        loop = profile.profileLoops.item(i)
                        loop_field = field+'.loops.'+str(i)
                        count = read(loop_field+'.curve_count', lambda: loop.profileCurves.count)
                        curves = []
                        for j in range(count or 0):
                            curve = loop.profileCurves.item(j).sketchEntity
                            curve_field = loop_field+'.curves.'+str(j)
                            entry = {'entity_type': read(curve_field+'.entity_type', lambda: curve.objectType),
                                     'entity_token': read(curve_field+'.entity_token', lambda: curve.entityToken)}
                            circle = adsk.fusion.SketchCircle.cast(curve)
                            if circle:
                                entry.update(center_world_cm=read(curve_field+'.center_world_cm', lambda: circle.centerSketchPoint.worldGeometry.asArray()),
                                             radius_cm=read(curve_field+'.radius_cm', lambda: circle.radius))
                            curves.append(entry)
                        loops.append({'is_outer': read(loop_field+'.is_outer', lambda: loop.isOuter), 'curves': curves})
                    result['profile_loops'] = loops
                return result

            def condition_evidence(section, field, is_input=False):
                condition = read(field+'.condition', lambda: section.endCondition)
                if condition is None:
                    return None
                result = {'condition_type': read(field+'.condition_type', lambda: condition.objectType)}
                weighted = adsk.fusion.LoftTangentEndCondition.cast(condition) or adsk.fusion.LoftSmoothEndCondition.cast(condition)
                if weighted:
                    result['weight'] = read(field+'.weight', lambda: weighted.weight.realValue if is_input else weighted.weight.value)
                return result

            seed_section = root.sketches.add(root.xYConstructionPlane)
            seed_section.name = 'LoftFaceSeedSection'
            seed_section.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 1.)
            seed = root.features.extrudeFeatures.addSimple(seed_section.profiles.item(0), value(1.), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = 'LoftFaceCylinderSeed'
            seed.bodies.item(0).name = 'LoftFaceCylinderBody'
            source_face = seed.endFaces.item(0)
            plane_input = root.constructionPlanes.createInput()
            if not plane_input.setByOffset(root.xYConstructionPlane, value(4.)):
                raise RuntimeError('Destination profile plane rejected')
            section = root.sketches.add(root.constructionPlanes.add(plane_input))
            section.name = 'LoftFaceDestinationSection'
            section.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), .6)
            destination = section.profiles.item(0)
            sample['source_face_before_loft'] = entity_evidence(source_face, 'source_face')
            sample['destination_profile_before_loft'] = entity_evidence(destination, 'destination_profile')
            inputs = root.features.loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            inputs.isSolid, inputs.isClosed = True, False
            source_entity = source_face
            if case.startswith('edge_path_'):
                if source_face.edges.count != 1:
                    raise RuntimeError('Expected one circular cylinder-end boundary edge')
                source_entity = adsk.fusion.Path.create(source_face.edges.item(0), adsk.fusion.ChainedCurveOptions.noChainedCurves)
                if source_entity is None:
                    raise RuntimeError('Documented boundary Path creation failed')
            sample['source_section_before_loft'] = entity_evidence(source_entity, 'source_section')
            face_section = inputs.loftSections.add(source_entity)
            inputs.loftSections.add(destination)
            if case == 'face_free':
                sample['requested_condition'] = {'type': 'Free'}
                accepted = face_section.setFreeEndCondition()
            elif '_tangent_' in case:
                weight = 2. if case.endswith('weight2') else 1.
                sample['requested_condition'] = {'type': 'Tangent', 'weight': weight}
                accepted = face_section.setTangentEndCondition(value(weight))
            else:
                sample['requested_condition'] = {'type': 'Smooth', 'weight': 1.}
                accepted = face_section.setSmoothEndCondition(value(1.))
            sample['setter_returned'] = accepted
            sample['actual_input_condition'] = condition_evidence(face_section, 'input_section', True)
            if not accepted:
                raise RuntimeError('Documented face Loft endpoint setter returned false')
            feature = root.features.loftFeatures.add(inputs)
            feature.name = 'ProbeLoftFace'
            settings = {'requested_operation': adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                        'result_bodies': [body_evidence(body, 'result_body'+str(i)) for i, body in enumerate(feature.bodies)]}
            feature.timelineObject.rollTo(True)
            for key, getter in (
                    ('operation', lambda: feature.operation), ('is_solid', lambda: feature.isSolid),
                    ('is_closed', lambda: feature.isClosed), ('is_tangent_edges_merged', lambda: feature.isTangentEdgesMerged),
                    ('start_edge_alignment', lambda: feature.startLoftEdgeAlignment),
                    ('end_edge_alignment', lambda: feature.endLoftEdgeAlignment),
                    ('section_count', lambda: feature.loftSections.count),
                    ('guide_count', lambda: feature.centerLineOrRails.count),
                    ('is_centerline', lambda: feature.centerLineOrRails.isCenterLine)):
                settings[key] = read('settings.'+key, getter)
            settings['sections'] = []
            for i in range(feature.loftSections.count):
                selected = feature.loftSections.item(i)
                field = 'sections.'+str(i)
                entity = read(field+'.entity', lambda: selected.entity)
                settings['sections'].append({'index': read(field+'.index', lambda: selected.index),
                                             'entity': entity_evidence(entity, field+'.entity'),
                                             'end_condition': condition_evidence(selected, field)})
            design.timeline.moveToEnd()
            sample['settings'] = settings
            sample['parameters'] = []
            for i, parameter in enumerate(root.modelParameters):
                field = 'parameters.'+str(i)
                sample['parameters'].append({key: read(field+'.'+key, getter) for key, getter in (
                    ('name', lambda: parameter.name), ('role', lambda: parameter.role), ('value', lambda: parameter.value),
                    ('unit', lambda: parameter.unit), ('created_by', lambda: getattr(parameter.createdBy, 'name', None)))})
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('Face Loft export failed')
            truth['samples'].append(sample)
        except Exception:
            truth['errors'].append({'case': case, 'error': traceback.format_exc(), 'partial_capture': sample})
        finally:
            doc.close(False)
            (output/'ground_truth.json').write_text(json.dumps(truth, indent=2))
    (output/'complete.txt').write_text('Face Loft capture finished; consult errors.\n')
