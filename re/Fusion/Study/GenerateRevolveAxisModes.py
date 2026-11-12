"""Owned revolve axis selections: custom axis, directed sketch lines, BRep edge."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ('custom_two_points', 'sketch_line', 'sketch_line_reversed', 'brep_edge', 'brep_edge_offset_x')


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/('revolveaxes-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    for case in cases:
        sample = {'file': case+'.f3d', 'getter_errors': []}
        doc = None
        try:
            if case not in CASES:
                raise ValueError('Unknown Revolve axis case')
            (output/'progress.json').write_text(json.dumps({'case':case,'phase':'creating_document'})+'\n')
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            supports = root.sketches.add(root.xYConstructionPlane)
            supports.name = 'AxisSupportSketch'
            if case.startswith('brep_edge'):
                x_axis = case == 'brep_edge_offset_x'
                supports.sketchCurves.sketchLines.addTwoPointRectangle(point(1.1,-.6,0) if x_axis else point(0,0,0), point(4.8,0,0) if x_axis else point(.5,3,0))
                seed = root.features.extrudeFeatures.addSimple(supports.profiles.item(0), value('5 mm'), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                seed.name = 'AxisSeedExtrusion'
                seed.bodies.item(0).name = 'AxisSeedBody'
                candidates = [e for e in seed.startFaces.item(0).edges
                              if all(abs(v.geometry.y if x_axis else v.geometry.x) < 1e-9 and abs(v.geometry.z) < 1e-9 for v in (e.startVertex,e.endVertex))]
                if len(candidates) != 1:
                    raise RuntimeError('Expected unique seed y-directed boundary edge')
                axis = candidates[0]
                origin, direction = ([1.1,0,0], [1,0,0]) if x_axis else ([0,0,0], [0,1,0])
            else:
                origin, direction = [1,-1,0], [1/math.sqrt(5),2/math.sqrt(5),0]
                a, b = point(*origin), point(*[a+4*b for a,b in zip(origin,direction)])
                if case == 'custom_two_points':
                    first, second = supports.sketchPoints.add(a), supports.sketchPoints.add(b)
                    inputs = root.constructionAxes.createInput()
                    if not inputs.setByTwoPoints(first,second):
                        raise RuntimeError('Axis two-point definition rejected')
                    axis = root.constructionAxes.add(inputs)
                    axis.name = 'ProbeCustomAxis'
                else:
                    axis = supports.sketchCurves.sketchLines.addByTwoPoints(b,a) if case.endswith('reversed') else supports.sketchCurves.sketchLines.addByTwoPoints(a,b)
                    axis.isConstruction = True
            profile = root.sketches.add(root.xYConstructionPlane)
            profile.name = 'AxisProbeProfile'
            normal = [-direction[1], direction[0], 0]
            def corner(t,u):
                return point(*[o+t*d+u*n for o,d,n in zip(origin,direction,normal)])
            corners = [corner(1,.8),corner(3,.8),corner(3,1.6),corner(1,1.6)]
            for i in range(4):
                profile.sketchCurves.sketchLines.addByTwoPoints(corners[i],corners[(i+1)%4])
            inputs = root.features.revolveFeatures.createInput(profile.profiles.item(0),axis,adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            if not inputs.setAngleExtent(False,value('73 deg')):
                raise RuntimeError('Angular extent rejected')
            feature = root.features.revolveFeatures.add(inputs)
            feature.name = 'ProbeAxisRevolve'
            if not design.computeAll():
                raise RuntimeError('Revolve recompute failed')
            feature.timelineObject.rollTo(True)
            selected = feature.axis
            source = {'entity_type':selected.objectType,'entity_token':selected.entityToken}
            if isinstance(selected,adsk.fusion.SketchLine):
                source.update(sketch_name=selected.parentSketch.name,start_cm=selected.worldGeometry.startPoint.asArray(),end_cm=selected.worldGeometry.endPoint.asArray())
            elif isinstance(selected,adsk.fusion.ConstructionAxis):
                source.update(name=selected.name,origin_cm=selected.geometry.origin.asArray(),direction=selected.geometry.direction.asArray())
            else:
                source.update(body_name=selected.body.name,start_cm=selected.startVertex.geometry.asArray(),end_cm=selected.endVertex.geometry.asArray(),geometry_type=selected.geometry.objectType)
            sample['actual_axis'] = source
            design.timeline.moveToEnd()
            sample['settings'] = {'operation':int(feature.operation),'is_solid':feature.isSolid,'is_project_axis':feature.isProjectAxis,'angle_radians':feature.extentDefinition.angle.value,'result_body_count':feature.bodies.count}
            sample['parameters'] = [{'name':p.name,'role':p.role,'value':p.value,'unit':p.unit} for p in root.modelParameters]
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('Revolve axis export failed')
            truth['samples'].append(sample)
        except Exception:
            truth['errors'].append({'case':case,'error':traceback.format_exc(),'partial':sample})
        finally:
            if doc is not None:
                doc.close(False)
            (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
    (output/'complete.txt').write_text('Revolve axis capture terminal; consult errors.\n')
