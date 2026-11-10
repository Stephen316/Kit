"""Study-owned Sweep alternate profile inputs; capture actual API types/owners."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ('planar_face', 'open_sketch_surface', 'open_brep_edge_surface', 'two_profile_collection')
BRANCH_CASES = ('open_brep_edge_partial', 'open_brep_edge_reversed')


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/('sweepprofiles-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': [],
             'scope': 'Opaque API tokens/tempIds retained as getter evidence; no stable native ID or ASM index interpretation.'}
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByReal
    operations = adsk.fusion.FeatureOperations
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        sample = {'file': case+'.f3d', 'case': case, 'getter_errors': []}
        try:
            if case not in CASES+BRANCH_CASES:
                raise ValueError('Unknown Sweep profile case: '+str(case))
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
                collection = adsk.core.ObjectCollection.cast(entity)
                if collection:
                    result['count'] = read(field+'.count', lambda: collection.count)
                    result['items'] = [entity_evidence(collection.item(i), field+'.items.'+str(i)) for i in range(result['count'] or 0)]
                    return result
                selected_path = adsk.fusion.Path.cast(entity)
                if selected_path:
                    result['count'] = read(field+'.count', lambda: selected_path.count)
                    result['segments'] = []
                    for i in range(result['count'] or 0):
                        segment = selected_path.item(i)
                        segment_field = field+'.segments.'+str(i)
                        source = read(segment_field+'.entity', lambda: segment.entity)
                        result['segments'].append({'is_opposed_to_entity': read(segment_field+'.is_opposed_to_entity', lambda: segment.isOpposedToEntity),
                            'entity': entity_evidence(source, segment_field+'.entity') if source else None})
                    return result
                result['entity_token'] = read(field+'.entity_token', lambda: entity.entityToken)
                profile, face = adsk.fusion.Profile.cast(entity), adsk.fusion.BRepFace.cast(entity)
                edge, line = adsk.fusion.BRepEdge.cast(entity), adsk.fusion.SketchLine.cast(entity)
                if face or edge:
                    brep = face or edge
                    result.update(temp_id=read(field+'.temp_id', lambda: brep.tempId),
                                  body=read(field+'.body', lambda: body_evidence(brep.body, field+'.body')),
                                  geometry_type=read(field+'.geometry_type', lambda: brep.geometry.objectType))
                if edge:
                    result.update(start_world_cm=read(field+'.start_world_cm', lambda: edge.startVertex.geometry.asArray()),
                                  end_world_cm=read(field+'.end_world_cm', lambda: edge.endVertex.geometry.asArray()),
                                  adjacent_faces=read(field+'.adjacent_faces', lambda: [{'temp_id': f.tempId, 'entity_token': f.entityToken} for f in edge.faces]))
                if face:
                    result.update(area_cm2=read(field+'.area_cm2', lambda: face.area),
                                  centroid_world_cm=read(field+'.centroid_world_cm', lambda: face.centroid.asArray()),
                                  plane_origin_cm=read(field+'.plane_origin_cm', lambda: adsk.core.Plane.cast(face.geometry).origin.asArray()),
                                  plane_normal=read(field+'.plane_normal', lambda: adsk.core.Plane.cast(face.geometry).normal.asArray()),
                                  edge_evidence=read(field+'.edge_evidence', lambda: [entity_evidence(e, field+'.edges.'+str(i)) for i, e in enumerate(face.edges)]))
                if line:
                    result.update(sketch_name=read(field+'.sketch_name', lambda: line.parentSketch.name),
                                  sketch_entity_token=read(field+'.sketch_entity_token', lambda: line.parentSketch.entityToken),
                                  start_world_cm=read(field+'.start_world_cm', lambda: line.startSketchPoint.worldGeometry.asArray()),
                                  end_world_cm=read(field+'.end_world_cm', lambda: line.endSketchPoint.worldGeometry.asArray()))
                if profile:
                    result.update(sketch_name=read(field+'.sketch_name', lambda: profile.parentSketch.name),
                                  sketch_entity_token=read(field+'.sketch_entity_token', lambda: profile.parentSketch.entityToken),
                                  is_on_sketch_plane=read(field+'.is_on_sketch_plane', lambda: profile.isOnSketchPlane),
                                  profile_loop_count=read(field+'.profile_loop_count', lambda: profile.profileLoops.count))
                    loops = []
                    for i in range(result['profile_loop_count'] or 0):
                        loop = profile.profileLoops.item(i)
                        loop_path = field+'.loops.'+str(i)
                        curve_count = read(loop_path+'.curve_count', lambda: loop.profileCurves.count)
                        curves = []
                        for j in range(curve_count or 0):
                            curve = loop.profileCurves.item(j)
                            curve_path = loop_path+'.curves.'+str(j)
                            source = read(curve_path+'.sketch_entity', lambda: curve.sketchEntity)
                            curves.append({'geometry_type': read(curve_path+'.geometry_type', lambda: curve.geometry.objectType),
                                           'sketch_entity': entity_evidence(source, curve_path+'.sketch_entity') if source else None})
                        loops.append({'is_outer': read(loop_path+'.is_outer', lambda: loop.isOuter), 'curves': curves})
                    result['profile_loops'] = loops
                return result

            section = root.sketches.add(root.xYConstructionPlane)
            section.name = 'SweepProfileSection'
            path_start, path_end = point(0, 0, 0), point(0, 0, 3)
            sample['source_entities'] = []
            if case == 'planar_face':
                section.sketchCurves.sketchLines.addTwoPointRectangle(point(-.5, -.4, 0), point(.5, .4, 0))
                seed = root.features.extrudeFeatures.addSimple(section.profiles.item(0), value(1.), operations.NewBodyFeatureOperation)
                seed.name = 'SweepProfileSeed'
                seed.bodies.item(0).name = 'SweepProfileSeedBody'
                profile = seed.endFaces.item(0)
                path_start, path_end = point(0, 0, 1), point(0, 0, 4)
                sample['source_entities'].append(entity_evidence(profile, 'source_face'))
            elif case == 'open_sketch_surface':
                line = section.sketchCurves.sketchLines.addByTwoPoints(point(-1, 0, 0), point(1, 0, 0))
                profile = root.createOpenProfile(line, False)
                sample['source_entities'].append(entity_evidence(line, 'source_open_line'))
            elif case.startswith('open_brep_edge_'):
                line = section.sketchCurves.sketchLines.addByTwoPoints(point(-1, 0, 0), point(1, 0, 0))
                open_profile = root.createOpenProfile(line, False)
                seed_inputs = root.features.extrudeFeatures.createInput(open_profile, operations.NewBodyFeatureOperation)
                seed_inputs.isSolid = False
                seed_inputs.setDistanceExtent(False, value(1.))
                seed = root.features.extrudeFeatures.add(seed_inputs)
                seed.name = 'SweepProfileSurfaceSeed'
                body = seed.bodies.item(0)
                body.name = 'SweepProfileSurfaceBody'
                edges = [e for e in body.edges if e.startVertex and e.endVertex
                         and abs(e.startVertex.geometry.z) < 1e-8 and abs(e.endVertex.geometry.z) < 1e-8]
                if len(edges) != 1:
                    raise RuntimeError('Expected one bottom open edge on surface seed')
                edge = edges[0]
                profile = root.createBRepEdgeProfile(edge, False)
                path_start, path_end = point(0, 0, 0), point(0, 3, 0)
                sample['source_entities'].append(entity_evidence(edge, 'source_open_edge'))
            else:
                section.sketchCurves.sketchCircles.addByCenterRadius(point(-.7, 0, 0), .25)
                section.sketchCurves.sketchCircles.addByCenterRadius(point(.7, 0, 0), .25)
                if section.profiles.count != 2:
                    raise RuntimeError('Expected two disjoint coplanar profiles')
                profile = adsk.core.ObjectCollection.create()
                for item in section.profiles:
                    profile.add(item)
                sample['source_entities'].append(entity_evidence(profile, 'source_collection'))
            if profile is None:
                raise RuntimeError('Alternate Sweep profile construction returned null')
            sample['input_profile'] = entity_evidence(profile, 'input_profile')
            if case == 'open_brep_edge_reversed':
                path_start, path_end = path_end, path_start
            path_sketch = root.sketches.add(root.xYConstructionPlane if case.startswith('open_brep_edge_') else root.xZConstructionPlane)
            path_sketch.name = 'SweepProfilePath'
            line = path_sketch.sketchCurves.sketchLines.addByTwoPoints(path_sketch.modelToSketchSpace(path_start), path_sketch.modelToSketchSpace(path_end))
            sample['input_path'] = entity_evidence(line, 'input_path')
            path = root.features.createPath(line, False)
            inputs = root.features.sweepFeatures.createInput(profile, path, operations.NewBodyFeatureOperation)
            inputs.isSolid = case in ('planar_face', 'two_profile_collection')
            inputs.orientation = adsk.fusion.SweepOrientationTypes.PerpendicularOrientationType
            if case == 'open_brep_edge_partial':
                inputs.distanceOne = value(.4)
            feature = root.features.sweepFeatures.add(inputs)
            feature.name = 'ProbeSweepProfile'
            settings = {'result_bodies': [body_evidence(body, 'result_body'+str(i)) for i, body in enumerate(feature.bodies)]}
            feature.timelineObject.rollTo(True)
            for key, getter in (
                    ('operation', lambda: feature.operation), ('orientation', lambda: feature.orientation),
                    ('is_solid', lambda: feature.isSolid), ('distance_one', lambda: feature.distanceOne.value if feature.distanceOne else None),
                    ('distance_two', lambda: feature.distanceTwo.value if feature.distanceTwo else None),
                    ('taper_angle_radians', lambda: feature.taperAngle.value if feature.taperAngle else None),
                    ('twist_angle_radians', lambda: feature.twistAngle.value if feature.twistAngle else None),
                    ('guide_rail_present', lambda: feature.guideRail is not None),
                    ('guide_surface_count', lambda: len(feature.guideSurfaces))):
                settings[key] = read('settings.'+key, getter)
            actual_profile = read('settings.profile', lambda: feature.profile)
            settings['profile'] = entity_evidence(actual_profile, 'settings.profile') if actual_profile else None
            actual_path = read('settings.path', lambda: feature.path)
            settings['path_entity_count'] = read('settings.path.count', lambda: actual_path.count) if actual_path else None
            settings['path_entities'] = [entity_evidence(actual_path.item(i).entity, 'settings.path.'+str(i)) for i in range(settings['path_entity_count'] or 0)]
            design.timeline.moveToEnd()
            sample['settings'] = settings
            sample['parameters'] = []
            for i, parameter in enumerate(root.modelParameters):
                field = 'parameters.'+str(i)
                sample['parameters'].append({key: read(field+'.'+key, getter) for key, getter in (
                    ('name', lambda: parameter.name), ('role', lambda: parameter.role), ('value', lambda: parameter.value),
                    ('unit', lambda: parameter.unit), ('created_by', lambda: getattr(parameter.createdBy, 'name', None)))})
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('Sweep profile export failed')
            truth['samples'].append(sample)
        except Exception:
            truth['errors'].append({'case': case, 'error': traceback.format_exc(), 'partial_capture': sample})
        finally:
            doc.close(False)
            (output/'ground_truth.json').write_text(json.dumps(truth, indent=2))
    (output/'complete.txt').write_text('Alternate Sweep profile capture finished; consult errors.\n')
