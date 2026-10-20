"""Study-owned planar Emboss/Deboss using editable SketchText inputs."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ('text_emboss', 'text_deboss', 'mixed_text_profile', 'two_texts')


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/('embosstext-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': [],
             'sdk_scope': 'EmbossFeatures.createInput accepts coplanar Profile/SketchText arrays. Editable text remains source text; never exploded or inferred from glyph outlines.',
             'identity_scope': 'API tokens/tempIds are opaque evidence, not interpreted as native design IDs or ASM indices.'}
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in cases:
        doc, design = None, None
        sample = {'file': case+'.f3d', 'case': case, 'getter_errors': []}
        try:
            if case not in CASES:
                raise ValueError('Unknown Emboss Text case: '+str(case))
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent

            def read(field, getter):
                try:
                    return getter()
                except Exception:
                    sample['getter_errors'].append({'field': field, 'error': traceback.format_exc()})
                    return None

            def parameter_truth(parameter, field):
                if parameter is None:
                    return None
                result = {key: read(field+'.'+key, getter) for key, getter in (
                    ('name', lambda: parameter.name), ('role', lambda: parameter.role),
                    ('expression', lambda: parameter.expression), ('unit', lambda: parameter.unit),
                    ('entity_token', lambda: parameter.entityToken),
                    ('created_by', lambda: getattr(parameter.createdBy, 'name', None)))}
                is_text = result['unit'] == 'Text'
                result['text_value' if is_text else 'value'] = read(field+'.value', lambda: parameter.textValue if is_text else parameter.value)
                return result

            def body_truth(body, field):
                return {key: read(field+'.'+key, getter) for key, getter in (
                    ('name', lambda: body.name), ('entity_token', lambda: body.entityToken),
                    ('component_name', lambda: body.parentComponent.name), ('is_solid', lambda: body.isSolid),
                    ('volume_cm3', lambda: body.volume), ('face_count', lambda: body.faces.count),
                    ('bounding_box_min_cm', lambda: body.boundingBox.minPoint.asArray()),
                    ('bounding_box_max_cm', lambda: body.boundingBox.maxPoint.asArray()))}

            def face_truth(face, field):
                return {key: read(field+'.'+key, getter) for key, getter in (
                    ('entity_type', lambda: face.objectType), ('entity_token', lambda: face.entityToken),
                    ('temp_id', lambda: face.tempId), ('body', lambda: body_truth(face.body, field+'.body')),
                    ('geometry_type', lambda: face.geometry.objectType), ('area_cm2', lambda: face.area),
                    ('point_on_face_cm', lambda: face.pointOnFace.asArray()),
                    ('centroid_world_cm', lambda: face.centroid.asArray()),
                    ('normal', lambda: adsk.core.Plane.cast(face.geometry).normal.asArray()))}

            def profile_truth(entity, field):
                if entity is None:
                    return None
                result = {'entity_type': read(field+'.entity_type', lambda: entity.objectType),
                          'entity_token': read(field+'.entity_token', lambda: entity.entityToken),
                          'sketch_name': read(field+'.sketch_name', lambda: entity.parentSketch.name),
                          'sketch_entity_token': read(field+'.sketch_entity_token', lambda: entity.parentSketch.entityToken)}
                text = adsk.fusion.SketchText.cast(entity)
                if text:
                    for key, getter in (
                        ('font_name', lambda: text.fontName), ('text_style', lambda: text.textStyle),
                        ('is_horizontal_flip', lambda: text.isHorizontalFlip), ('is_vertical_flip', lambda: text.isVerticalFlip)):
                        result[key] = read(field+'.'+key, getter)
                    result['text_parameter'] = parameter_truth(read(field+'.text_parameter', lambda: text.textParameter), field+'.text_parameter')
                    result['height_parameter'] = parameter_truth(read(field+'.height_parameter', lambda: text.heightParameter), field+'.height_parameter')
                    definition = read(field+'.definition', lambda: text.definition)
                    result['definition_type'] = read(field+'.definition_type', lambda: definition.objectType) if definition else None
                    if definition:
                        lines = read(field+'.rectangle_lines', lambda: definition.rectangleLines)
                        result['rectangle_lines'] = []
                        for i, line in enumerate(lines or []):
                            result['rectangle_lines'].append({
                                'start_sketch_cm': read(field+'.rectangle'+str(i)+'.start', lambda: line.startSketchPoint.geometry.asArray()),
                                'end_sketch_cm': read(field+'.rectangle'+str(i)+'.end', lambda: line.endSketchPoint.geometry.asArray())})
                else:
                    profile = adsk.fusion.Profile.cast(entity)
                    count = read(field+'.loop_count', lambda: profile.profileLoops.count)
                    result['loop_count'] = count
                    result['loops'] = []
                    for i in range(count or 0):
                        loop = profile.profileLoops.item(i)
                        curve_count = read(field+'.loop'+str(i)+'.curve_count', lambda: loop.profileCurves.count)
                        curves = []
                        for j in range(curve_count or 0):
                            curve = loop.profileCurves.item(j).sketchEntity
                            entry = {'entity_type': read(field+'.curve'+str(j)+'.entity_type', lambda: curve.objectType),
                                     'entity_token': read(field+'.curve'+str(j)+'.entity_token', lambda: curve.entityToken)}
                            circle = adsk.fusion.SketchCircle.cast(curve)
                            if circle:
                                entry.update(center_sketch_cm=read(field+'.curve'+str(j)+'.center', lambda: circle.centerSketchPoint.geometry.asArray()),
                                             radius_cm=read(field+'.curve'+str(j)+'.radius', lambda: circle.radius))
                            curves.append(entry)
                        result['loops'].append({'is_outer': read(field+'.loop'+str(i)+'.is_outer', lambda: loop.isOuter), 'curves': curves})
                return result

            seed_sketch = root.sketches.add(root.xYConstructionPlane)
            seed_sketch.name = 'EmbossTextTargetSection'
            seed_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(6, 4, 0))
            seed = root.features.extrudeFeatures.addSimple(seed_sketch.profiles.item(0), value('20 mm'), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = 'EmbossTextTargetExtrude'
            seed.bodies.item(0).name = 'EmbossTextTargetBody'
            target = seed.endFaces.item(0)
            plane_input = root.constructionPlanes.createInput()
            if not plane_input.setByOffset(root.xYConstructionPlane, value('25 mm')):
                raise RuntimeError('Emboss Text source plane rejected')
            sketch = root.sketches.add(root.constructionPlanes.add(plane_input))
            sketch.name = 'EmbossTextInputs'

            def add_text(content, x1, x2):
                inputs = sketch.sketchTexts.createInput3("'"+content+"'", value('5 mm'))
                inputs.fontName, inputs.textStyle = 'Arial', 0
                inputs.isHorizontalFlip, inputs.isVerticalFlip = False, False
                if not inputs.setAsMultiLine(point(x1, 1, 0), point(x2, 2.5, 0),
                        adsk.core.HorizontalAlignments.LeftHorizontalAlignment,
                        adsk.core.VerticalAlignments.TopVerticalAlignment, 0.):
                    raise RuntimeError('Editable Text rectangle setup failed')
                return sketch.sketchTexts.add(inputs)

            selections = [add_text('KIT', 1., 3.)]
            if case == 'two_texts':
                selections.append(add_text('UCAD', 3.5, 5.5))
            elif case == 'mixed_text_profile':
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(4.5, 2., 0), .3)
                if sketch.profiles.count != 1:
                    raise RuntimeError('Expected one ordinary circle profile beside editable Text')
                selections.append(sketch.profiles.item(0))
            sample['source_inputs_before_emboss'] = [profile_truth(entity, 'source_input'+str(i)) for i, entity in enumerate(selections)]
            sample['target_before_emboss'] = face_truth(target, 'target')
            depth = '-1.5 mm' if case == 'text_deboss' else '2 mm'
            inputs = root.features.embossFeatures.createInput(selections, [target], value(depth))
            inputs.isTangentChain = True
            sample['requested'] = {'depth_expression': depth, 'is_tangent_chain': True,
                                   'horizontal_distance_cm': 0., 'vertical_distance_cm': 0., 'rotation_angle_radians': 0.}
            sample['input_profiles'] = read('inputs.profiles', lambda: [profile_truth(entity, 'input_profile'+str(i)) for i, entity in enumerate(inputs.profiles)])
            feature = root.features.embossFeatures.add(inputs)
            if feature is None:
                raise RuntimeError('Emboss Text feature creation returned null')
            feature.name = 'ProbeEmbossText'
            settings = {'health_state': read('feature.health_state', lambda: feature.healthState),
                        'warning': read('feature.warning', lambda: feature.errorOrWarningMessage),
                        'result_bodies': [body_truth(body, 'result_body'+str(i)) for i, body in enumerate(feature.bodies)]}
            feature.timelineObject.rollTo(True)
            for key, getter in (
                ('depth_cm', lambda: feature.depth.value), ('horizontal_distance_cm', lambda: feature.horizontalDistance.value),
                ('vertical_distance_cm', lambda: feature.verticalDistance.value), ('rotation_angle_radians', lambda: feature.rotationAngle.value),
                ('is_tangent_chain', lambda: feature.isTangentChain)):
                settings[key] = read('feature.'+key, getter)
            actual_profiles = read('feature.profiles', lambda: feature.profiles)
            settings['profiles'] = [profile_truth(entity, 'actual_profile'+str(i)) for i, entity in enumerate(actual_profiles or [])]
            actual_faces = read('feature.input_faces', lambda: feature.inputFaces)
            settings['input_faces'] = [face_truth(face, 'actual_face'+str(i)) for i, face in enumerate(actual_faces or [])]
            design.timeline.moveToEnd()
            sample['settings'] = settings
            sample['model_parameters'] = [parameter_truth(parameter, 'model_parameter'+str(i)) for i, parameter in enumerate(root.modelParameters)]
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('Emboss Text local export failed')
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
    (output/'complete.txt').write_text('Emboss Text generation finished; consult errors.\n')
