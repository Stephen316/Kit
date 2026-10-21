"""Observed mixed finite-Line/Circle profile portions, explicitly derived.

The shared trim/cache reader proves typed native ownership, same-asset BODY and
all-six-literal COEDGE naming before source intersection geometry is evaluated.
Existing Circle/Line analytic point and cached evaluators are reused; only the
proper mixed intersection and captured mixed selector family are new here.
"""
import copy
import math
import struct

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_profile_circle_portions import _point as circle_point, _cached_samples as circle_cached_samples
from decode_profile_line_portions import _point as line_point, evaluate_stored_line_samples
from decode_profiles import read_loops
from decode_sketch import attributes, numbers, reference
from decode_trimmed_profiles import decode_trimmed_profiles

EPS=1e-9
SCOPE='Observed identity-XY horizontal finite-Line/Circle smaller-segment profiles; complete native/cache tuple identity precedes derived Circle angles and Line source fractions, separate from serialized/API parameters'


def read_mixed_profile_loops(body,descriptor_id,sketch):
    seen=set()
    def details(fields,geometry):
        code,tag,secondary,direction,first,second,opaque=fields
        expected={'Circle':(2,2),'Line':(2,3)}.get(geometry['kind'])
        if expected is None or (first,second)!=expected or direction!=0:
            raise ValueError('Uncaptured mixed source selector/direction family')
        if tag in seen:raise ValueError('Repeated mixed source portion is not captured')
        seen.add(tag)
        return {'stored_tuple_code':code,'stored_reference_selector_pair':[first,second],
                'stored_opaque_u64':opaque,'stored_tuple_fields':list(fields),
                'stored_coedge_text_fields':[str(value) for value in (tag,secondary,direction,opaque,first,second)],
                'geometry_scope':'Typed source primitive identity and opaque stored selectors; mixed source geometry is derived separately'}
    loops=read_loops(body,descriptor_id,sketch,curve_reference_details=details)
    if (len(loops)!=1 or not loops[0]['is_outer']
            or sorted(ref['entity_kind'] for ref in loops[0]['curve_references'])!=['Circle','Line']):
        raise ValueError('Only captured one-Circle/one-Line single outer profile supported')
    cursor=25
    for ref in loops[0]['curve_references']:
        if body[cursor:cursor+40]!=struct.pack('<IQQIIIQ',*ref['stored_tuple_fields']):
            raise ValueError('Mixed profile raw reference replay disagrees')
        ref['stored_tuple_offset_in_definition']=cursor;cursor+=40
    return loops


def _eligible_features(features):
    # Eligibility only: these explicit source candidates come from the canonical
    # native profile-descriptor pass. The shared cache reader independently proves
    # descriptor/Sketch/source/BODY ownership rather than trusting this gate.
    sketches={feature['sketch_object_id']:feature for feature in features if feature['kind']=='Sketch'}
    mixed={identity for identity,sketch in sketches.items()
           if sorted(geometry['kind'] for geometry in sketch['geometry'] if geometry['kind']!='Point')==['Circle','Line']}
    owners={feature['object_id'] for feature in features if feature['kind']=='Extrude'
            and len(feature.get('sketch_reference_candidates',[]))==1
            and feature['sketch_reference_candidates'][0]['sketch_object_id'] in mixed}
    return [feature for feature in features if feature['kind']!='Extrude' or feature['object_id'] in owners],owners


def _derive_intersections(data,records,sketch,sources):
    curves=[geometry for geometry in sketch['geometry'] if geometry['kind']!='Point']
    if sorted(curve['kind'] for curve in curves)!=['Circle','Line']:
        raise ValueError('Mixed context must contain exactly one Line and one Circle')
    if {curve['object_id'] for curve in curves}!={source['native_entity_object_id'] for source in sources}:
        raise ValueError('Mixed sources lack complete independently qualified native/cache membership')
    identity=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]
    matrix=sketch.get('placement',{}).get('sketch_to_component_matrix')
    if matrix is None or len(matrix)!=16 or any(not math.isclose(a,b,abs_tol=EPS) for a,b in zip(matrix,identity)):
        raise ValueError('Mixed source Sketch placement outside observed identity context')
    line=next(curve for curve in curves if curve['kind']=='Line');circle=next(curve for curve in curves if curve['kind']=='Circle')
    start,end=line['start_cm'],line['end_cm'];center=circle['center_cm'];radius=circle['radius_cm']
    if (any(curve.get('entity_genesis')!=2 or curve.get('is_construction') is not False for curve in curves)
            or not all(math.isfinite(value) for value in (*start,*end,*center,radius))
            or math.dist(circle['normal'],[0.,0.,1.])>EPS or math.dist(circle['reference_axis'],[1.,0.,0.])>EPS
            or max(abs(start[2]),abs(end[2]),abs(center[2]))>EPS
            or abs(start[1]-end[1])>EPS or end[0]-start[0]<=EPS
            or not EPS<start[1]-center[1]<radius-EPS):
        raise ValueError('Mixed source frame/direction/positive chord height outside captured family')
    primary=[record for record in records if record.is_primary and record.object_id==line['object_id']]
    if len(primary)!=1:raise ValueError('Mixed native source Line ambiguous')
    body=data[primary[0].body:primary[0].end];props,cursor=attributes(body,2)
    if (len(body)-cursor!=171 or reference(body,cursor+107)!=line['start_point_id']
            or reference(body,cursor+96)!=line['end_point_id']):
        raise ValueError('Mixed native Line endpoint reference framing disagrees')
    values=numbers(body,cursor,12)
    if (math.dist(values[:3],start)>EPS or math.dist([a+b for a,b in zip(values[:3],values[3:6])],end)>EPS):
        raise ValueError('Mixed canonical Line differs from its native endpoint/vector representation')
    direction=[b-a for a,b in zip(start,end)];relative=[a-b for a,b in zip(start,center)]
    aa=sum(value*value for value in direction);bb=2*sum(a*b for a,b in zip(relative,direction));cc=sum(value*value for value in relative)-radius*radius
    discriminant=bb*bb-4*aa*cc
    if not math.isfinite(discriminant) or discriminant<=EPS:
        raise ValueError('Mixed Line/Circle intersection is tangent/nonproper')
    root=math.sqrt(discriminant);fractions=sorted(((-bb-root)/(2*aa),(-bb+root)/(2*aa)))
    if not EPS<fractions[0]<fractions[1]<1-EPS:
        raise ValueError('Both mixed intersections must be proper interior finite-Line cuts')
    points=[line_point(line,fraction) for fraction in fractions]
    angles=sorted(math.atan2(point[1]-center[1],point[0]-center[0])%(2*math.pi) for point in points)
    if not EPS<angles[0]<angles[1]<math.pi-EPS:
        raise ValueError('Mixed Circle cuts outside captured positive-height nonseam family')
    return line,circle,fractions,angles,points


def decode_profile_mixed_portions(data,records,features,member,members,body_identifier_summary):
    eligible,owners=_eligible_features(features)
    if not owners:return {'decoded':[],'unresolved':[],'scope':SCOPE}
    base=decode_trimmed_profiles(data,records,eligible,member,members,body_identifier_summary,
                                 profile_loops_reader=read_mixed_profile_loops)
    decoded=[];unresolved=list(base['unresolved'])
    for cached in base['decoded']:
        try:
            row=copy.deepcopy(cached);sketches=[feature for feature in features if feature['kind']=='Sketch' and feature['sketch_object_id']==row['native_sketch_object_id']]
            if len(sketches)!=1:raise ValueError('Mixed source Sketch missing/ambiguous')
            line,circle,fractions,angles,intersection_points=_derive_intersections(data,records,sketches[0],row['source_curves'])
            topology=decode_topology(inspect_asm(members[row['history_blob_member']]))
            graphs=[graph for graph in topology['body_graphs'] if graph['body_index']==row['asm_body_index']]
            if len(graphs)!=1 or graphs[0]['body_transform_is_identity'] is not True:
                raise ValueError('Mixed source/cache comparison requires identity BODY transform')
            portions=[]
            for source in row['source_curves']:
                ref=source['stored_profile_reference'];kind=source['native_entity_kind'];ordinal,count=ref['stored_reference_selector_pair']
                if kind=='Line':
                    a,b=fractions;points=[line_point(line,t) for t in (a,(a+b)/2,b)]
                    parameter={'derived_native_start_end_fraction_interval':[a,b],
                               'native_line_endpoint_object_ids':[line['start_point_id'],line['end_point_id']],
                               'native_line_start_end_cm':[copy.deepcopy(line['start_cm']),copy.deepcopy(line['end_cm'])]}
                    evaluator=evaluate_stored_line_samples
                else:
                    a,b=angles;points=[circle_point(circle,t) for t in (a,(a+b)/2,b)]
                    parameter={'derived_reference_axis_angle_interval_radians':[a,b]};evaluator=circle_cached_samples
                evidence=[]
                for candidate in source['cached_coedge_candidates']:
                    if candidate['stored_decimal_text_fields']!=ref['stored_coedge_text_fields']:
                        raise ValueError('Mixed candidate lacks complete native tuple identity')
                    observed=evaluator(candidate)
                    endpoint_error=max(min(math.dist(point,other) for other in (observed[0],observed[2])) for point in (points[0],points[2]))
                    midpoint_error=math.dist(points[1],observed[1])
                    if max(endpoint_error,midpoint_error)>EPS:
                        raise ValueError('Derived mixed source portion disagrees with a full-tuple named cached boundary')
                    evidence.append({'coedge_record_index':candidate['coedge_record_index'],'edge_record_index':candidate['edge_record_index'],
                                     'max_endpoint_set_error_cm':endpoint_error,'midpoint_error_cm':midpoint_error})
                portions.append({'native_source_object_id':source['native_entity_object_id'],'native_source_tag':source['native_entity_tag'],
                                 'native_source_kind':kind,'stored_profile_reference':ref,
                                 'geometry_status':'DerivedAnalyticMixedSource'+kind+'Portion',
                                 'derived_portion_ordinal':ordinal,'derived_portion_count':count,
                                 **parameter,'derived_sketch_local_points_cm':{'start':points[0],'midpoint':points[1],'end':points[2]},
                                 'all_full_tuple_cache_candidates_corroborate':evidence,
                                 'parameter_status':'Derived from proper finite-Line/Circle intersections; no serialized trim parameters, API evaluator conversion or stored traversal semantics'})
            row.update(derived_source_circle_line_intersections={
                        'native_source_line_object_id':line['object_id'],'native_source_circle_object_id':circle['object_id'],
                        'derived_line_fractions':fractions,'derived_circle_reference_axis_angles_radians':angles,
                        'derived_intersection_points_sketch_cm':intersection_points},
                       derived_source_portions=portions,
                       geometry_status='Bounded derived mixed source portions, independently corroborated by every full-tuple qualified cached boundary',
                       remaining_uncertainty=['Other mixed selections/directions, major segments, nonhorizontal/3D frames and endpoint/tangent intersections',
                                              'Other selector/count combinations or repeated mixed source portions',
                                              'Serialized/native/API parameterization and stored direction flag traversal semantics',
                                              'Modified cached geometry, persistent topology identity and lifecycle'])
            decoded.append(row)
        except (ValueError,KeyError,IndexError,TypeError,ArithmeticError,UnicodeError,struct.error) as error:
            unresolved.append({'source_feature_object_id':cached['source_feature_object_id'],'reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,'scope':SCOPE}
