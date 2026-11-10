"""Prepared owned fixed-NURBS Sweep paths; no execution or native coverage implied.

Three cubic paths share a circle on the root YZ plane at their origin. Constructor
arguments, actual local/world curves, Path semantics and rolled getters stay distinct.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

FOUR = [[0.,0.,0.],[2.,0.,0.],[4.,1.,0.],[6.,2.,0.]]
CASES = {
    'polynomial_cubic': dict(control_points_cm=FOUR,knots=[0.,0.,0.,0.,1.,1.,1.,1.],weights=None),
    'rational_cubic': dict(control_points_cm=FOUR,knots=[0.,0.,0.,0.,1.,1.,1.,1.],weights=[1.,.7,1.3,1.]),
    'polynomial_multispan': dict(control_points_cm=[[0.,0.,0.],[1.5,0.,0.],[3.,.4,0.],[4.5,1.,0.],[6.,1.5,0.],[7.5,1.8,0.]],
        knots=[0.,0.,0.,0.,1./3.,2./3.,1.,1.,1.,1.],weights=None),
}


def run(context):
    app = adsk.core.Application.get()
    cases = CASES
    if isinstance(context,dict) and 'cases' in context:
        selected = context['cases']
        if not isinstance(selected,(list,tuple)) or not selected or len(set(selected))!=len(selected) or set(selected)-set(CASES):
            raise ValueError('Select one to three known distinct fixed-NURBS Sweep cases')
        cases = {name:spec for name,spec in CASES.items() if name in selected}
    source = Path(__file__).resolve()
    output = source.parent/('sweepnurbspaths-'+uuid.uuid4().hex[:12]);output.mkdir()
    executed = source.read_bytes();(output/'executed-generator-source.txt').write_bytes(executed)
    truth = dict(fusion_version=app.version,samples=[],errors=[],planned_cases=list(cases),helper_dependencies=[],
        executed_generator_sha256=hashlib.sha256(executed).hexdigest(),sdk_sources={},
        scope='Fresh owned parametric documents only. Fixed clamped cubic sketch NURBS paths and circular sketch profiles; full solid perpendicular NewBody Sweep, no assigned twist/taper/guide. Requested constructor arrays remain distinct from actual API local/world curve data, path opposition and result collections. No persistent IDs, native curve-family semantics or regeneration coverage inferred.')
    for module,names in ((adsk.core,('NurbsCurve3D','CurveEvaluator3D','ValueInput')),
                         (adsk.fusion,('SketchFixedSplines','SketchFixedSpline','Path','PathEntity','SweepFeatures','SweepFeatureInput','SweepFeature'))):
        path=Path(module.__file__);raw=path.read_bytes();text=raw.decode();blocks=[]
        for name in names:
            begin=text.index('class '+name+'(');end=text.find('\nclass ',begin+1)
            blocks.append(text[begin:] if end<0 else text[begin:end])
        surface='\n'.join(blocks).encode();filename='executed-'+path.stem+'-sdk-surface.txt'
        (output/filename).write_bytes(surface)
        truth['sdk_sources'][path.stem]=dict(runtime_module=str(path),sha256=hashlib.sha256(raw).hexdigest(),
            executed_surface_file=filename,executed_surface_sha256=hashlib.sha256(surface).hexdigest(),classes=list(names))

    def persist():
        (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')

    def journal(phase,case=None,**fields):
        event=dict(time_utc=datetime.now(timezone.utc).isoformat(),phase=phase,case=case,
            sample_count=len(truth['samples']),error_count=len(truth['errors']),**fields)
        with (output/'journal.jsonl').open('a') as stream:stream.write(json.dumps(event)+'\n')
        (output/'progress.json').write_text(json.dumps(event,indent=2)+'\n');persist()

    def read(label,getter,errors):
        try:return getter()
        except Exception:
            errors.append(dict(getter=label,error=traceback.format_exc()));return None

    def items(collection):
        if hasattr(collection,'item') and hasattr(collection,'count'):
            return [collection.item(i) for i in range(collection.count)]
        return list(collection)

    def xyz(point):return [point.x,point.y,point.z]

    def serial(value):
        if value is None or isinstance(value,(str,bool,int,float)):return value
        if isinstance(value,(list,tuple)):
            return [serial(item) for item in value]
        if isinstance(value,(adsk.core.Point3D,adsk.core.Vector3D)):return xyz(value)
        return dict(python_type=type(value).__name__,objectType=getattr(value,'objectType',None))

    def identity(entity):
        if entity is None:return None
        row,errors={},[]
        for prop in ('objectType','isValid','name','entityToken'):
            if hasattr(type(entity),prop):row[prop]=read(prop,lambda prop=prop:getattr(entity,prop),errors)
        row['getter_errors']=errors;return row

    def nurbs_truth(curve):
        if curve is None:return None
        row,errors=identity(curve),[]
        for prop in ('controlPointCount','degree','knotCount','isRational','isClosed','isPeriodic','curveType'):
            row[prop]=read(prop,lambda prop=prop:serial(getattr(curve,prop)),errors)
        for prop in ('controlPoints','knots'):
            row[prop]=read(prop,lambda prop=prop:serial(getattr(curve,prop)),errors)
        data=read('getData',lambda:curve.getData(),errors)
        row['getData_raw']=serial(data)
        row['getData_documented_order']=['return_value','controlPoints','degree','knots','isRational','weights','isPeriodic']
        if isinstance(data,(list,tuple)) and len(data)==7:
            row['getData_fields']=dict(zip(row['getData_documented_order'],serial(data)))
        evaluator=read('evaluator',lambda:curve.evaluator,errors)
        if evaluator is not None:
            row['evaluator_endpoints']=read('evaluator.getEndPoints',lambda:serial(evaluator.getEndPoints()),errors)
            extents=read('evaluator.getParameterExtents',lambda:evaluator.getParameterExtents(),errors)
            row['evaluator_parameter_extents']=serial(extents)
            if isinstance(extents,(list,tuple)) and len(extents)==3 and extents[0] is True:
                row['evaluator_start_first_derivative']=read('evaluator.getFirstDerivative(start)',lambda:serial(evaluator.getFirstDerivative(extents[1])),errors)
                row['evaluator_start_point']=read('evaluator.getPointAtParameter(start)',lambda:serial(evaluator.getPointAtParameter(extents[1])),errors)
                row['evaluator_end_point']=read('evaluator.getPointAtParameter(end)',lambda:serial(evaluator.getPointAtParameter(extents[2])),errors)
        row['getter_errors']=errors;return row

    def sketch_truth(sketch):
        row,errors=identity(sketch),[]
        row['transform']=read('transform',lambda:sketch.transform.asArray(),errors)
        row['origin']=read('origin',lambda:xyz(sketch.origin),errors)
        row['referencePlane']=read('referencePlane',lambda:identity(sketch.referencePlane),errors)
        row['getter_errors']=errors;return row

    def spline_truth(curve):
        row,errors=identity(curve),[]
        row['parentSketch']=read('parentSketch',lambda:sketch_truth(curve.parentSketch),errors)
        row['geometry_local']=read('geometry',lambda:nurbs_truth(curve.geometry),errors)
        row['geometry_world']=read('worldGeometry',lambda:nurbs_truth(curve.worldGeometry),errors)
        for prop in ('startSketchPoint','endSketchPoint'):
            point=read(prop,lambda prop=prop:getattr(curve,prop),errors)
            row[prop]=None if point is None else dict(identity=identity(point),
                geometry_local_cm=read(prop+'.geometry',lambda point=point:xyz(point.geometry),errors),
                geometry_world_cm=read(prop+'.worldGeometry',lambda point=point:xyz(point.worldGeometry),errors))
        row['getter_errors']=errors;return row

    def path_truth(path):
        if path is None:return None
        row,errors=identity(path),[]
        row['count']=read('count',lambda:path.count,errors)
        row['isClosed']=read('isClosed',lambda:path.isClosed,errors)
        row['entities']=[]
        for i in range(row['count'] or 0):
            part=path.item(i);entity=read('item.entity',lambda:part.entity,errors)
            fixed=adsk.fusion.SketchFixedSpline.cast(entity) if entity is not None else None
            row['entities'].append(dict(identity=identity(part),
                isOpposedToEntity=read('item.isOpposedToEntity',lambda:part.isOpposedToEntity,errors),
                entity=spline_truth(fixed) if fixed is not None else identity(entity)))
        row['getter_errors']=errors;return row

    def profile_truth(profile):
        if profile is None:return None
        row,errors=identity(profile),[]
        row['parentSketch']=read('parentSketch',lambda:sketch_truth(profile.parentSketch),errors)
        row['isOnSketchPlane']=read('isOnSketchPlane',lambda:profile.isOnSketchPlane,errors)
        row['loops']=[]
        for loop in items(profile.profileLoops):
            curves=[]
            for part in items(loop.profileCurves):
                entity=read('profileCurve.sketchEntity',lambda:part.sketchEntity,errors)
                circle=adsk.fusion.SketchCircle.cast(entity) if entity is not None else None
                curves.append(dict(identity=identity(part),source=identity(entity),
                    radius_cm=None if circle is None else read('circle.radius',lambda:circle.radius,errors),
                    center_world_cm=None if circle is None else read('circle.centerSketchPoint.worldGeometry',lambda:xyz(circle.centerSketchPoint.worldGeometry),errors)))
            row['loops'].append(dict(isOuter=loop.isOuter,curves=curves))
        row['getter_errors']=errors;return row

    def body_truth(body):
        row,errors=identity(body),[]
        for prop in ('isSolid','area','volume','isVisible'):
            row[prop]=read(prop,lambda prop=prop:getattr(body,prop),errors)
        row['parentComponent']=read('parentComponent',lambda:identity(body.parentComponent),errors)
        row['bounding_box_cm']=read('boundingBox',lambda:dict(min=xyz(body.boundingBox.minPoint),max=xyz(body.boundingBox.maxPoint)),errors)
        row['vertices']=read('vertices',lambda:[dict(tempId=v.tempId,position_cm=xyz(v.geometry)) for v in items(body.vertices)],errors)
        row['face_count']=read('faces.count',lambda:body.faces.count,errors)
        row['edge_count']=read('edges.count',lambda:body.edges.count,errors)
        row['surface_types']=read('faces.geometry.objectType',lambda:[face.geometry.objectType for face in items(body.faces)],errors)
        row['getter_errors']=errors;return row

    def bodies_truth(bodies):return [body_truth(body) for body in items(bodies)]

    def parameter_truth(parameter):
        if parameter is None:return None
        row,errors=identity(parameter),[]
        for prop in ('value','unit','expression','role'):
            if hasattr(type(parameter),prop):row[prop]=read(prop,lambda prop=prop:serial(getattr(parameter,prop)),errors)
        if isinstance(parameter,adsk.core.ValueInput):
            value_type=read('valueType',lambda:parameter.valueType,errors)
            row['valueType']=serial(value_type)
            if value_type==adsk.core.ValueTypes.RealValueType:
                row['realValue']=read('realValue',lambda:parameter.realValue,errors)
                row['stringValue_status']='Not called: actual valueType is RealValueType'
            elif value_type==adsk.core.ValueTypes.StringValueType:
                row['stringValue']=read('stringValue',lambda:parameter.stringValue,errors)
                row['realValue_status']='Not called: actual valueType is StringValueType'
            else:
                row['numeric_or_string_accessor_status']='Not called: valueType did not establish RealValueType or StringValueType; see getter errors'
        if hasattr(type(parameter),'createdBy'):row['createdBy']=read('createdBy',lambda:identity(parameter.createdBy),errors)
        row['getter_errors']=errors;return row

    def controls_truth(subject,definition=False,is_input=False):
        row,errors=identity(subject),[]
        for prop in ('operation','orientation','isSolid'):
            row[prop]=read(prop,lambda prop=prop:serial(getattr(subject,prop)),errors)
        for prop in ('distanceOne','distanceTwo','twistAngle','taperAngle'):
            row[prop]=read(prop,lambda prop=prop:parameter_truth(getattr(subject,prop)),errors)
        if definition:
            row['profile']=read('profile',lambda:profile_truth(subject.profile),errors)
            row['path']=read('path',lambda:path_truth(subject.path),errors)
            row['guideRail']=read('guideRail',lambda:path_truth(subject.guideRail),errors)
            row['guideSurfaces']=read('guideSurfaces',lambda:[identity(face) for face in subject.guideSurfaces],errors)
        if not is_input:
            for prop in ('healthState','errorOrWarningMessage','isSuppressed'):
                row[prop]=read(prop,lambda prop=prop:serial(getattr(subject,prop)),errors)
            row['timeline_index']=read('timelineObject.index',lambda:subject.timelineObject.index,errors)
            row['bodies']=read('bodies',lambda:bodies_truth(subject.bodies),errors)
        row['getter_errors']=errors;return row

    journal('batch_begin',planned_sample_count=len(cases),output_directory=str(output))
    for case,spec in cases.items():
        doc,design,feature=None,None,None
        sample=dict(case=case,file=case+'.f3d',phase='document_create',getter_errors=[],
            requested=dict(**spec,degree=3,isPeriodic=False,profile_plane='RootYZ',profile_center_local_cm=[0.,0.,0.],profile_radius_cm=.2,
                path_sketch_plane='RootXY',path_chaining='noChainedCurves',distanceOne=1.,operation='NewBody',orientation='Perpendicular',
                isSolid=True,twist_or_taper_assigned=False,guide_assigned=False))
        truth['active_sample']=sample
        try:
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if design is None:raise RuntimeError('Owned document lacks Fusion design')
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType;root=design.rootComponent
            sample['root_component']=identity(root)
            sketch=root.sketches.add(root.xYConstructionPlane);sketch.name='OwnedNurbsSweepPath_'+case
            points=[adsk.core.Point3D.create(*point) for point in spec['control_points_cm']]
            knots=list(spec['knots']);weights=None if spec['weights'] is None else list(spec['weights'])
            sample['phase']='nurbs_constructor'
            if spec['weights'] is None:
                returned=adsk.core.NurbsCurve3D.createNonRational(points,3,knots,False)
                sample['constructor_method']='NurbsCurve3D.createNonRational'
            else:
                returned=adsk.core.NurbsCurve3D.createRational(points,3,knots,weights,False)
                sample['constructor_method']='NurbsCurve3D.createRational'
            sample['constructor_return_python_type']=type(returned).__name__
            sample['constructor_return_metadata']=serial(returned)
            if isinstance(returned,(list,tuple)):
                candidates=[item for item in returned if isinstance(item,adsk.core.NurbsCurve3D)]
                if len(candidates)!=1:raise RuntimeError('Constructor tuple/list lacks a unique typed NurbsCurve3D')
                geometry=candidates[0];sample['constructor_selected_tuple_index']=next(i for i,item in enumerate(returned) if item is geometry)
            elif isinstance(returned,adsk.core.NurbsCurve3D):geometry=returned
            else:raise RuntimeError('Constructor returned neither NurbsCurve3D nor a uniquely typed tuple/list')
            sample['constructed_geometry']=nurbs_truth(geometry)
            sample['constructor_inout_arrays']=dict(control_points_cm=serial(points),knots=serial(knots),weights=serial(weights))
            sample['phase']='fixed_spline_add'
            spline=sketch.sketchCurves.sketchFixedSplines.addByNurbsCurve(geometry)
            if spline is None:raise RuntimeError('Owned fixed spline add returned null')
            sample['source_spline_before_sweep']=spline_truth(spline)
            path=adsk.fusion.Path.create(spline,adsk.fusion.ChainedCurveOptions.noChainedCurves)
            if path is None:raise RuntimeError('Owned fixed spline Path.create returned null')
            section=root.sketches.add(root.yZConstructionPlane);section.name='OwnedNurbsSweepCircle_'+case
            circle=section.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0.,0.,0.),.2)
            if section.profiles.count!=1:raise RuntimeError('Owned circle profile not unique')
            profile=section.profiles.item(0)
            sample['circle_source']=identity(circle)
            sample['exact_path_argument_before_sweep']=path_truth(path)
            sample['exact_profile_argument_before_sweep']=profile_truth(profile)
            sample['component_bodies_before_sweep']=bodies_truth(root.bRepBodies)
            sample['phase']='sweep_attempt'
            try:
                inp=root.features.sweepFeatures.createInput(profile,path,adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                if inp is None:raise RuntimeError('Sweep createInput returned null')
                sample['input_defaults_before_assignments']=controls_truth(inp,True,True)
                inp.isSolid=True
                inp.orientation=adsk.fusion.SweepOrientationTypes.PerpendicularOrientationType
                inp.distanceOne=adsk.core.ValueInput.createByReal(1.)
                sample['configured_input']=controls_truth(inp,True,True)
                journal('sweep_add_begin',case)
                feature=root.features.sweepFeatures.add(inp)
                sample['add_returned_feature']=feature is not None
                if feature is None:raise RuntimeError('Sweep add returned null')
                feature.name='OwnedFixedNurbsSweep_'+case
                sample['sweep_status']='FeatureReturned';journal('sweep_feature_returned',case)
            except Exception:
                sample['sweep_status']='AttemptError'
                error=dict(case=case,phase='sweep_attempt',error=traceback.format_exc())
                sample['sweep_error']=error;truth['errors'].append(error);journal('sweep_attempt_error',case)
            design.timeline.moveToEnd()
            sample['compute_all_returned']=bool(design.computeAll())
            if feature is not None:sample['feature_at_timeline_end']=controls_truth(feature)
            sample['component_bodies_after_sweep']=bodies_truth(root.bRepBodies)
            sample['model_parameters_after']=[parameter_truth(parameter) for parameter in items(root.modelParameters)]
            sample['sweep_collection_count_after']=root.features.sweepFeatures.count
            if feature is not None:
                try:
                    rolled=feature.timelineObject.rollTo(True);sample['roll_before_feature_returned']=bool(rolled)
                    if rolled:
                        sample['feature_before_node']=controls_truth(feature,True)
                        sample['source_spline_before_node']=spline_truth(spline)
                except Exception:
                    sample['getter_errors'].append(dict(getter='owned Sweep roll/snapshot',error=traceback.format_exc()))
                finally:design.timeline.moveToEnd()
            sample['timeline_count']=design.timeline.count
            sample['timeline_marker_position']=design.timeline.markerPosition
            sample['phase']='local_export';journal('local_export_begin',case,file=sample['file'])
            destination=output/sample['file']
            success=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not success or not destination.is_file() or destination.stat().st_size==0:raise RuntimeError('Owned local Sweep export did not complete')
            sample['export']=dict(returned_success=bool(success),size_bytes=destination.stat().st_size,sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
            sample['phase']='export_complete';truth['samples'].append(sample);truth.pop('active_sample',None)
            journal('local_export_complete',case,file=sample['file'])
        except Exception:
            truth['errors'].append(dict(case=case,phase=sample['phase'],error=traceback.format_exc(),partial_sample=sample))
            truth.pop('active_sample',None);journal('case_error',case)
        finally:
            if design is not None:
                try:design.timeline.moveToEnd()
                except Exception:truth['errors'].append(dict(case=case,phase='restore_owned_timeline',error=traceback.format_exc()))
            if doc is not None:
                try:
                    journal('owned_document_close_begin',case,save=False)
                    closed=doc.close(False);sample['close_owned_document_returned']=bool(closed)
                    if not closed:truth['errors'].append(dict(case=case,phase='close_owned_document',error='close(False) returned false'))
                    journal('owned_document_close_returned',case,save=False,returned=bool(closed))
                except Exception:truth['errors'].append(dict(case=case,phase='close_owned_document',error=traceback.format_exc()))
            persist()
    truth['terminal_status']='Complete' if not truth['errors'] else 'CompleteWithErrors'
    journal('batch_complete',terminal_status=truth['terminal_status'])
    (output/'complete.txt').write_text('Fixed-NURBS Sweep capture finished; consult ground_truth.json and journal.jsonl.\n')
