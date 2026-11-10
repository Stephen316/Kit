"""Journaled Sketch/vertex/construction-point Scale and multi-input Shell probes."""

from datetime import datetime, timezone
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ('scale_sketch', 'scale_vertex', 'scale_construction_point',
         'shell_two_bodies', 'shell_body_and_other_face')


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/('scaleshellinputs-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': []}
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString

    def journal(phase, case=None):
        event = {'phase': phase, 'case': case, 'time_utc': datetime.now(timezone.utc).isoformat(),
                 'sample_count': len(truth['samples']), 'error_count': len(truth['errors'])}
        with (output/'journal.jsonl').open('a') as stream:
            stream.write(json.dumps(event)+'\n')
        (output/'progress.json').write_text(json.dumps(event, indent=2)+'\n')
        (output/'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')

    journal('batch_begin')
    for case in cases:
        doc = None
        sample = {'file': case+'.f3d', 'getter_errors': []}

        def observe(field, read):
            try:
                return read()
            except Exception:
                sample['getter_errors'].append({'field': field, 'error': traceback.format_exc()})
                return None

        def entity_truth(entity):
            item = {'entity_type': entity.objectType, 'entity_token': entity.entityToken}
            if isinstance(entity, adsk.fusion.BRepBody):
                item['body_name'] = entity.name
            elif isinstance(entity, adsk.fusion.BRepFace):
                item.update(body_name=entity.body.name, surface_type=int(entity.geometry.surfaceType))
            elif isinstance(entity, adsk.fusion.BRepVertex):
                item.update(body_name=entity.body.name, position_cm=entity.geometry.asArray())
            elif isinstance(entity, adsk.fusion.Sketch):
                item.update(sketch_name=entity.name, curve_count=entity.sketchCurves.count,
                            line_endpoints_cm=[{'start': line.startSketchPoint.geometry.asArray(),
                                                'end': line.endSketchPoint.geometry.asArray()}
                                               for line in entity.sketchCurves.sketchLines])
            elif isinstance(entity, adsk.fusion.ConstructionPoint):
                item.update(name=entity.name, position_cm=entity.geometry.asArray())
            return item

        try:
            journal('creating_document', case)
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            bodies, seeds = [], []
            if case == 'scale_sketch':
                selected_sketch = root.sketches.add(root.xYConstructionPlane)
                selected_sketch.name = 'ScaleInputSketch'
                selected_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, 1, 0), point(4, 3, 0))
                selected = [selected_sketch]
                selected_point = root.originConstructionPoint
            else:
                for index in range(2 if case.startswith('shell') else 1):
                    sketch = root.sketches.add(root.xYConstructionPlane)
                    sketch.name = 'InputSourceSketch'+str(index+1)
                    x = 1+6*index
                    sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(x, 1, 0), point(x+3, 4, 0))
                    seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value('20 mm'),
                                                                adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                    seed.name = 'InputSourceExtrude'+str(index+1)
                    body = seed.bodies.item(0)
                    body.name = 'InputBody'+str(index+1)
                    seeds.append(seed)
                    bodies.append(body)
                selected = bodies
                if case == 'shell_body_and_other_face':
                    selected = [bodies[0], seeds[1].endFaces.item(0)]
                elif case == 'scale_vertex':
                    selected_point = bodies[0].vertices.item(0)
                elif case == 'scale_construction_point':
                    source = root.sketches.add(root.xYConstructionPlane)
                    source.name = 'ReferencePointSketch'
                    vertex = source.sketchPoints.add(point(2, -1, 0))
                    definition = root.constructionPoints.createInput()
                    if not definition.setByPoint(vertex):
                        raise RuntimeError('Construction point source rejected')
                    selected_point = root.constructionPoints.add(definition)
                    selected_point.name = 'ScaleReferencePoint'
            entities = adsk.core.ObjectCollection.create()
            for entity in selected:
                entities.add(entity)
            sample['requested_input_entities'] = [entity_truth(entity) for entity in selected]
            journal('creating_feature', case)
            if case.startswith('scale'):
                sample['requested_point'] = entity_truth(selected_point)
                inputs = root.features.scaleFeatures.createInput(entities, selected_point, value('1.3'))
                feature = root.features.scaleFeatures.add(inputs)
            else:
                inputs = root.features.shellFeatures.createInput(entities, False)
                inputs.insideThickness = value('1 mm')
                feature = root.features.shellFeatures.add(inputs)
            feature.name = 'ProbeScaleShellInput'
            if not design.computeAll():
                raise RuntimeError('Scale/Shell computation failed')
            journal('reading_actual_inputs', case)
            feature.timelineObject.rollTo(True)
            sample['actual_inputs'] = observe('inputEntities', lambda: [entity_truth(e) for e in feature.inputEntities])
            if case.startswith('scale'):
                sample['actual_point'] = observe('point', lambda: entity_truth(feature.point))
            design.timeline.moveToEnd()
            sample['feature_type'] = feature.objectType
            sample['health_state'] = int(feature.healthState)
            sample['warning'] = feature.errorOrWarningMessage
            if case.startswith('scale'):
                sample['settings'] = {'is_uniform': feature.isUniform, 'factor': feature.scaleFactor.value}
            else:
                sample['settings'] = {'is_tangent_chain': feature.isTangentChain, 'shell_type': int(feature.shellType),
                                      'inside_thickness_cm': feature.insideThickness.value if feature.insideThickness else None,
                                      'outside_thickness_cm': feature.outsideThickness.value if feature.outsideThickness else None}
            sample['result_bodies'] = observe('bodies', lambda: [entity_truth(b) for b in feature.bodies])
            sample['parameters'] = [{'name': p.name, 'role': p.role, 'unit': p.unit, 'value': p.value,
                                     'created_by': getattr(p.createdBy, 'name', None)} for p in root.modelParameters]
            journal('exporting', case)
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('Scale/Shell export failed')
            truth['samples'].append(sample)
            journal('export_complete', case)
        except Exception:
            truth['errors'].append({'case': case, 'error': traceback.format_exc(), 'partial': sample})
            journal('case_error', case)
        finally:
            if doc is not None:
                journal('closing_document', case)
                doc.close(False)
            journal('case_terminal', case)
    journal('batch_complete')
    (output/'complete.txt').write_text('Scale/Shell input capture terminal; consult errors.\n')
