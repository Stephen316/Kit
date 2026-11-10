"""Journaled thin-extrude contrasts in new owned parametric documents only.

Actual feature getters are read with timeline immediately before that feature;
owned exports/closes occur after restoring the timeline end. No user document
or global display setting is modified. Failures remain in the journal/truth.
"""
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CONFIGS = {
    'closed_side1': dict(profile='rectangle', one='Side1', thickness_one=.12, length_one=2.5),
    'closed_center': dict(profile='rectangle', one='Center', thickness_one=.20, length_one=2.5),
    'closed_side2': dict(profile='rectangle', one='Side2', thickness_one=.15, length_one=2.5),
    'closed_two_sides_mixed': dict(profile='rectangle', one='Side1', thickness_one=.12, length_one=2.5,
                                   two='Side2', thickness_two=.22, length_two=1.3),
    'closed_two_sides_center': dict(profile='rectangle', one='Center', thickness_one=.25, length_one=1.7,
                                    two='Center', thickness_two=.10, length_two=.8),
    'open_line_side1': dict(profile='open_line', one='Side1', thickness_one=.12, length_one=2.5),
    'ordinary_rectangle_control': dict(profile='rectangle', thin=False, length_one=2.5),
}
CASES = tuple(CONFIGS)


def run(context):
    app = adsk.core.Application.get(); root = Path(__file__).resolve().parent
    output = root/('thinextrudes-'+uuid.uuid4().hex[:12]); output.mkdir()
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    if not isinstance(cases, (list, tuple)) or any(case not in CONFIGS for case in cases):
        raise ValueError('Unknown thin-extrude contrast cases')
    truth = {'fusion_version': app.version, 'samples': [], 'errors': [], 'status': 'running',
        'enum_values': {name: int(getattr(adsk.fusion.ThinExtrudeWallLocation, name)) for name in ('Side1','Center','Side2')},
        'scope': 'Actual thin/ordinary Extrude getters and owned source profiles; no native writer or regeneration claim',
        'SDK_notes': ['setThinExtrude(sideOneLocation,sideOneThickness[,sideTwoLocation,sideTwoThickness]) uses extrusion extent sides, not independently asymmetric offsets around one profile.',
                      'Component.createOpenProfile accepts one SketchCurve; whether the thin-solid operation accepts that open profile is captured as success/error, not assumed.',
                      'Inactive side-two getters are not read in one-sided cases.']}

    def save(event=None):
        (output/'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')
        (output/'progress.json').write_text(json.dumps({'status':truth['status'], 'samples':[
            {'case':sample['case'],'status':sample['status']} for sample in truth['samples']], 'errors':len(truth['errors'])}, indent=2)+'\n')
        if event:
            with (output/'journal.jsonl').open('a') as journal: journal.write(json.dumps(event)+'\n')

    save({'event':'started','cases':list(cases)})
    for case in cases:
        config = dict(CONFIGS[case]); config.setdefault('thin', True)
        sample = {'case':case,'file':case+'.f3d','requested':config,'getter_errors':[],'status':'creating_document'}
        truth['samples'].append(sample); document = None; design = None; save({'event':'case_started','case':case})
        try:
            document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            component = design.rootComponent
            point = adsk.core.Point3D.create; value = adsk.core.ValueInput.createByReal

            def read(field, callback):
                try: return callback()
                except Exception:
                    sample['getter_errors'].append({'field':field,'error':traceback.format_exc()})
                    return None

            def parameter(item, label):
                if item is None: return {'getter_returned_null':True}
                return {'entity_type':item.objectType,'name':item.name,'role':item.role,'raw_value':item.value,
                        'unit':item.unit,'expression':item.expression,
                        'created_by':read(label+'.created_by',lambda:getattr(item.createdBy,'name',None))}

            def profile_truth(entity, label):
                result = {'entity_type':read(label+'.type',lambda:entity.objectType)}
                profile = adsk.fusion.Profile.cast(entity)
                if profile:
                    parent_sketch = profile.parentSketch
                    result['parent_sketch_is_null'] = parent_sketch is None
                    if parent_sketch is None:
                        result['loop_capture_status'] = 'Generic open profile has no parent Sketch; original selected curve is captured separately, closed-profile loops not assumed'
                        result['entity_token_status'] = 'Generic open-profile token failed in original capture; unsupported optional getter not retried'
                        return result
                    result['entity_token'] = read(label+'.token',lambda:entity.entityToken)
                    result['sketch_name'] = parent_sketch.name
                    result['sketch_token'] = read(label+'.sketch_token',lambda:parent_sketch.entityToken)
                    result['loops'] = []
                    for i in range(profile.profileLoops.count):
                        loop = profile.profileLoops.item(i); curves = []
                        for j in range(loop.profileCurves.count):
                            curve = loop.profileCurves.item(j).sketchEntity
                            entry = {'entity_type':curve.objectType,'entity_token':read(label+'.curve_token',lambda curve=curve:curve.entityToken)}
                            line = adsk.fusion.SketchLine.cast(curve)
                            if line:
                                entry.update(start_world_cm=list(line.startSketchPoint.worldGeometry.asArray()),
                                             end_world_cm=list(line.endSketchPoint.worldGeometry.asArray()))
                            curves.append(entry)
                        result['loops'].append({'is_outer':loop.isOuter,'curves':curves})
                return result

            def extent_truth(extent, label):
                result = {'entity_type':extent.objectType}
                distance = adsk.fusion.DistanceExtentDefinition.cast(extent)
                if distance:
                    result['distance'] = parameter(distance.distance,label+'.distance')
                return result

            def body_truth(body):
                return {'entity_type':body.objectType,'name':body.name,'is_solid':body.isSolid,
                        'face_count':body.faces.count,'edge_count':body.edges.count,'vertex_count':body.vertices.count,
                        'volume_cm3':body.volume,'bounds_min_cm':list(body.boundingBox.minPoint.asArray()),
                        'bounds_max_cm':list(body.boundingBox.maxPoint.asArray())}

            sketch = component.sketches.add(component.xYConstructionPlane)
            sketch.name = 'ThinProbeSource'
            if config['profile']=='open_line':
                line = sketch.sketchCurves.sketchLines.addByTwoPoints(point(0,0,0),point(4,0,0))
                profile = component.createOpenProfile(line,False)
                if profile is None: raise RuntimeError('Documented createOpenProfile returned null')
                sample['open_profile_input'] = {'chain_curves':False,'selected_curve_type':line.objectType,
                    'selected_curve_token':read('open_profile.curve_token',lambda:line.entityToken),
                    'start_world_cm':list(line.startSketchPoint.worldGeometry.asArray()),'end_world_cm':list(line.endSketchPoint.worldGeometry.asArray())}
            else:
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0,0,0),point(4,3,0))
                profile = sketch.profiles.item(0)
            sample['source_profile_before_feature'] = profile_truth(profile,'source_profile')
            inputs = component.features.extrudeFeatures.createInput(profile,adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            if inputs is None: raise RuntimeError('Extrude createInput returned null')
            extent_one = adsk.fusion.DistanceExtentDefinition.create(value(config['length_one']))
            if 'two' in config:
                accepted = inputs.setTwoSidesExtent(extent_one,adsk.fusion.DistanceExtentDefinition.create(value(config['length_two'])))
            else:
                accepted = inputs.setOneSideExtent(extent_one,adsk.fusion.ExtentDirections.PositiveExtentDirection)
            sample['set_extent_returned'] = accepted
            if not accepted: raise RuntimeError('Extrude extent input rejected')
            if config['thin']:
                arguments = [getattr(adsk.fusion.ThinExtrudeWallLocation,config['one']),value(config['thickness_one'])]
                if 'two' in config:
                    arguments += [getattr(adsk.fusion.ThinExtrudeWallLocation,config['two']),value(config['thickness_two'])]
                sample['set_thin_returned'] = inputs.setThinExtrude(*arguments)
                if not sample['set_thin_returned']: raise RuntimeError('setThinExtrude input rejected')
            sample['actual_input'] = {'is_thin_extrude':read('input.isThinExtrude',lambda:inputs.isThinExtrude),
                'is_solid':read('input.isSolid',lambda:inputs.isSolid),'profile_type':inputs.profile.objectType,
                'has_two_extents':inputs.hasTwoExtents}
            if config['thin']:
                sample['actual_input']['wall_one'] = {'location':int(inputs.thinExtrudeWallLocationOne),
                    'thickness_value_input_real':inputs.thinExtrudeWallThicknessOne.realValue}
                sample['actual_input']['wall_two'] = ({'applicable':True,'location':int(inputs.thinExtrudeWallLocationTwo),
                    'thickness_value_input_real':inputs.thinExtrudeWallThicknessTwo.realValue} if 'two' in config else
                    {'applicable':False,'getter_status':'Inactive side two not read'})
            sample['status']='adding_feature';save({'event':'adding_feature','case':case})
            feature = component.features.extrudeFeatures.add(inputs)
            if feature is None: raise RuntimeError('Parametric Extrude add returned null')
            feature.name = 'ProbeThinExtrude' if config['thin'] else 'ProbeOrdinaryExtrudeControl'
            sample['compute_all_returned'] = design.computeAll()
            sample['result_bodies'] = [body_truth(body) for body in feature.bodies]
            sample['root_body_count'] = component.bRepBodies.count
            sample['health_state'] = feature.healthState; sample['warning'] = feature.errorOrWarningMessage
            sample['status']='reading_actual_getters';save({'event':'reading_getters','case':case})
            feature.timelineObject.rollTo(True)
            settings = {'feature_type':feature.objectType,'feature_name':feature.name,
                'is_thin_extrude':read('feature.isThinExtrude',lambda:feature.isThinExtrude),
                'is_solid':read('feature.isSolid',lambda:feature.isSolid),
                'operation':int(feature.operation),'extent_type':int(feature.extentType),
                'has_two_extents':feature.hasTwoExtents,
                'profile':profile_truth(feature.profile,'actual_profile'),
                'start_extent_type':read('feature.startExtent.type',lambda:feature.startExtent.objectType),
                'extent_one':extent_truth(feature.extentOne,'extent_one'),
                'taper_one':parameter(feature.taperAngleOne,'taper_one')}
            if feature.hasTwoExtents:
                settings['extent_two']=extent_truth(feature.extentTwo,'extent_two')
                settings['taper_two']=parameter(feature.taperAngleTwo,'taper_two')
            if settings['is_thin_extrude']:
                settings['wall_one']={'location':read('feature.wallLocationOne',lambda:int(feature.thinExtrudeWallLocationOne)),
                    'thickness':read('feature.wallThicknessOne',lambda:parameter(feature.thinExtrudeWallThicknessOne,'wall_one.thickness'))}
                settings['wall_two']=({'applicable':True,'location':read('feature.wallLocationTwo',lambda:int(feature.thinExtrudeWallLocationTwo)),
                    'thickness':read('feature.wallThicknessTwo',lambda:parameter(feature.thinExtrudeWallThicknessTwo,'wall_two.thickness'))} if feature.hasTwoExtents else
                    {'applicable':False,'getter_status':'Inactive side two not read'})
            sample['settings']=settings
            sample['actual_is_thin_matches_request']=settings['is_thin_extrude']==config['thin']
            design.timeline.moveToEnd()
            sample['parameters']=[parameter(p,'model_parameter') for p in component.modelParameters]
            sample['status']='exporting';save({'event':'exporting','case':case})
            options = design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))
            if not design.exportManager.execute(options): raise RuntimeError('Thin contrast export failed')
            sample['status']='exported';save({'event':'exported','case':case})
        except Exception:
            sample['status']='error';truth['errors'].append({'case':case,'error':traceback.format_exc()});save({'event':'case_error','case':case})
        finally:
            if document is not None:
                try:
                    if design is not None: design.timeline.moveToEnd()
                    sample['close_owned_document_result']=document.close(False)
                except Exception:
                    sample['getter_errors'].append({'field':'close_owned_document','error':traceback.format_exc()})
            save({'event':'case_finished','case':case,'status':sample['status']})
    truth['status']='complete';save({'event':'complete'})
    (output/'complete.txt').write_text('Thin Extrude contrasts finished; inspect actual samples and errors.\n')
