"""Owned body/face inputs and non-origin references for Scale, Mirror and Shell."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ('scale_two_bodies_point', 'mirror_two_bodies_plane', 'shell_body', 'shell_two_faces')


def run(context):
    app=adsk.core.Application.get()
    output=Path(__file__).resolve().parent/('bodyselections-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth={'fusion_version':app.version,'samples':[],'errors':[]}
    point,value=adsk.core.Point3D.create,adsk.core.ValueInput.createByString
    cases=context.get('cases',CASES) if isinstance(context,dict) else CASES
    for case in cases:
        doc=None
        sample={'file':case+'.f3d','getter_errors':[]}
        def observe(field, read):
            try:return read()
            except Exception:
                sample['getter_errors'].append({'field':field,'error':traceback.format_exc()})
                return None
        try:
            (output/'progress.json').write_text(json.dumps({'case':case,'phase':'creating_document'})+'\n')
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType
            root=design.rootComponent
            bodies,seeds=[],[]
            for index in range(2 if case.startswith(('scale','mirror')) else 1):
                sketch=root.sketches.add(root.xYConstructionPlane)
                sketch.name='BodySelectionSeedSketch'+str(index+1)
                x=1+6*index
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(x,1,0),point(x+3,4,0))
                seed=root.features.extrudeFeatures.addSimple(sketch.profiles.item(0),value('20 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                seed.name='BodySelectionSeed'+str(index+1)
                body=seed.bodies.item(0);body.name='SelectedBody'+str(index+1)
                bodies.append(body);seeds.append(seed)
            entities=adsk.core.ObjectCollection.create()
            for entity in (list(seeds[0].startFaces)+list(seeds[0].endFaces) if case=='shell_two_faces' else bodies):
                entities.add(entity)
            if case.startswith('scale'):
                support=root.sketches.add(root.xYConstructionPlane);support.name='ScalePointSketch'
                selected_point=support.sketchPoints.add(point(1,-1,0))
                inputs=root.features.scaleFeatures.createInput(entities,selected_point,value('1.4'))
                feature=root.features.scaleFeatures.add(inputs)
            elif case.startswith('mirror'):
                plane_input=root.constructionPlanes.createInput()
                if not plane_input.setByOffset(root.yZConstructionPlane,value('5 mm')):
                    raise RuntimeError('Custom mirror plane definition rejected')
                plane=root.constructionPlanes.add(plane_input);plane.name='SelectionMirrorPlane'
                inputs=root.features.mirrorFeatures.createInput(entities,plane)
                inputs.isCombine=False
                feature=root.features.mirrorFeatures.add(inputs)
            else:
                inputs=root.features.shellFeatures.createInput(entities,False)
                inputs.insideThickness=value('1 mm')
                feature=root.features.shellFeatures.add(inputs)
            feature.name='ProbeBodySelection'
            if not design.computeAll():raise RuntimeError('Body-tool recomputation failed')
            feature.timelineObject.rollTo(True)
            actual_inputs=[]
            for entity in feature.inputEntities:
                item={'entity_type':entity.objectType,'entity_token':entity.entityToken}
                if isinstance(entity,adsk.fusion.BRepBody):item['body_name']=entity.name
                else:item.update(body_name=entity.body.name,surface_type=int(entity.geometry.surfaceType))
                actual_inputs.append(item)
            sample['actual_inputs']=actual_inputs
            if case.startswith('scale'):
                selected=feature.point
                sample['actual_point']={'entity_type':selected.objectType,'position_cm':selected.worldGeometry.asArray(),'sketch_name':selected.parentSketch.name}
            elif case.startswith('mirror'):
                selected=feature.mirrorPlane
                sample['actual_plane']={'entity_type':selected.objectType,'name':selected.name,'origin_cm':selected.geometry.origin.asArray(),'normal':selected.geometry.normal.asArray()}
            design.timeline.moveToEnd()
            sample['feature_kind']=feature.objectType.split('::')[-1]
            sample['result_body_count']=feature.bodies.count
            if case.startswith('scale'):sample['settings']={'is_uniform':feature.isUniform,'factor':feature.scaleFactor.value}
            elif case.startswith('mirror'):sample['settings']={'is_combine':feature.isCombine,'stitch_tolerance_cm':feature.stitchTolerance.value,'compute_option':observe('patternComputeOption',lambda:int(feature.patternComputeOption))}
            else:sample['settings']={'is_tangent_chain':feature.isTangentChain,'shell_type':int(feature.shellType),'inside_thickness_cm':feature.insideThickness.value if feature.insideThickness else None,'outside_thickness_cm':feature.outsideThickness.value if feature.outsideThickness else None}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):raise RuntimeError('Body selection export failed')
            truth['samples'].append(sample)
        except Exception:truth['errors'].append({'case':case,'error':traceback.format_exc(),'partial':sample})
        finally:
            if doc is not None:doc.close(False)
            (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
    (output/'complete.txt').write_text('Body selection capture terminal; consult errors.\n')
