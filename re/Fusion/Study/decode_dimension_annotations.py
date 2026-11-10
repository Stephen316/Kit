"""Stored shared-linear dimension measurement geometry, not a sketch solver.

Existing annotation readers prove text/binding/targets first. This adds four
stored points, a distance and repeated anchor for bounded source-role layouts.
IDs come from explicit ordered inputs before geometric copy validation.
"""
import math
import struct

from decode_dimension_controls import LINEAR,decode_dimension_controls
from decode_sketch import constraint_prefix,numbers,reference,same

SCOPE='Observed shared-linear dimension measurement/projection caches in sketch-local cm; no general solver, side selection or rendered-label semantics'
GUIDS={'Point':'C2CEDAE7-1716-47C1-B7B1-07B70081D0FB','Line':'DCA267ED-D615-4934-B64F-AD805E8003E2',
       'Ellipse':'FF23079A-D99C-47AB-940E-2F4E18F022AB','Circle':'F0130424-8B7E-4092-93C9-1CA807482534'}


def _sub(a,b):return [x-y for x,y in zip(a,b)]
def _dot(a,b):return sum(x*y for x,y in zip(a,b))
def _unit(a):
    size=math.hypot(*a)
    if size<=1e-12:raise ValueError('Degenerate dimension measurement direction')
    return [x/size for x in a]
def _along(point,offset,direction):return [x+offset*u for x,u in zip(point,direction)]


def encode_dimension_measurement_cache(item):
    """Replay the129-byte stored geometry block; not a sketch/file writer."""
    points=item['stored_measurement_line_points_cm']+item['stored_source_anchor_points_cm']
    return (struct.pack('<12d',*(x for p in points for x in p))+bytes([item['stored_pre_measurement_control_byte']])
            +struct.pack('<4d',item['cached_measurement_cm'],*item['stored_repeated_anchor_cm']))


def decode_dimension_annotations(data,records,features,dimension_controls=None):
    """Return extra measurement caches for already validated annotations only."""
    if dimension_controls is None:dimension_controls=decode_dimension_controls(data,records,features)
    grouped={}
    for r in records:
        if r.is_primary:grouped.setdefault(r.object_id,[]).append(r)
    primary={i:rs[0] for i,rs in grouped.items() if len(rs)==1}
    ag={}
    for a in dimension_controls['decoded']:ag.setdefault(a['object_id'],[]).append(a)
    annotations={i:rows[0] for i,rows in ag.items() if len(rows)==1}
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    for sketch in features:
        if sketch['kind']!='Sketch':continue
        geometry={g['object_id']:g for g in sketch.get('geometry',[])}
        for dim in sketch.get('dimensions',[]):
            r=primary.get(dim['object_id'])
            if r is None or r.class_guid!=LINEAR:continue
            try:
                a=annotations.get(r.object_id)
                if (a is None or a['class_guid']!=LINEAR or a['entity_ids']!=dim['entity_ids']
                        or a['binding_object_id']!=dim['binding_object_id'] or a['sketch_object_id']!=sketch['sketch_object_id']):
                    raise ValueError('Dimension measurement cache lacks validated annotation/binding/owner/targets')
                body=data[r.body:r.end];inputs,props,cursor=constraint_prefix(body)
                if (props!={'EntityGenesis':0} or inputs[0]!=0 or inputs[1:]!=dim['entity_ids']
                        or len(set(dim['entity_ids']))!=len(dim['entity_ids'])):
                    raise ValueError('Unobserved dimension measurement dependency framing')
                if cursor+148>a['value_expression_offset']-r.body or body[cursor+96]!=0 or body[cursor+146:cursor+148]!=b'\1\0':
                    raise ValueError('Unobserved bounded measurement/style framing')
                projections=[numbers(body,cursor+24*i,3) for i in range(2)]
                anchors=[numbers(body,cursor+48+24*i,3) for i in range(2)]
                distance=numbers(body,cursor+97,1)[0];repeated=numbers(body,cursor+105,3)
                if (distance<=0 or not math.isclose(distance,dim['value_cm'],abs_tol=1e-9)
                        or not math.isclose(math.dist(*projections),distance,abs_tol=1e-9)
                        or not same(repeated,anchors[1])):
                    raise ValueError('Dimension cached measurement/anchor distances disagree with bound value')
                source=[geometry.get(i) for i in dim['entity_ids']]
                for identity,g in zip(dim['entity_ids'],source):
                    native=primary.get(identity)
                    if (g is None or g['kind'] not in GUIDS or native is None or native.class_guid!=GUIDS[g['kind']]
                            or g['sketch_object_id']!=sketch['sketch_object_id']
                            or reference(data[native.body:native.end],native.end-native.body-11)!=sketch['sketch_object_id']):
                        raise ValueError('Dimension measurement source type/reciprocal sketch ownership unsupported')
                text=a['annotation_position_cm']
                if any(not math.isclose(p[2],0.,abs_tol=1e-9) for p in projections+anchors+[text]):
                    raise ValueError('Only observed XY sketch measurement caches supported')
                kind=dim['kind'];roles=[]
                if kind=='Linear' and [g['kind'] for g in source]==['Point','Point']:
                    expected=[source[1]['position_cm'],source[0]['position_cm']]
                    direction=_unit(_sub(expected[0],expected[1]))
                    if dim['orientation']=='Horizontal':direction=[1.,0.,0.]
                    elif dim['orientation']=='Vertical':direction=[0.,1.,0.]
                    projected=[_along(text,_dot(_sub(p,text),direction),direction) for p in expected]
                    # Horizontal/vertical anchor copies retain full source
                    # points: their Euclidean source distance differs from the
                    # projected scalar measurement, checked specially below.
                    roles=[dict(source_entity_object_id=source[1]['object_id'],role='SecondInputPoint'),
                           dict(source_entity_object_id=source[0]['object_id'],role='FirstInputPoint')]
                elif kind=='Offset' and [g['kind'] for g in source]==['Line','Line']:
                    direction=_unit(_sub(source[0]['end_cm'],source[0]['start_cm']))
                    other=_unit(_sub(source[1]['end_cm'],source[1]['start_cm']))
                    if not math.isclose(abs(_dot(direction,other)),1.,abs_tol=1e-9):
                        raise ValueError('Offset cache source lines are not parallel')
                    expected=[source[1]['end_cm'],source[0]['end_cm']]
                    projected=[_along(p,_dot(_sub(text,p),direction),direction) for p in expected]
                    roles=[dict(source_entity_object_id=g['object_id'],source_point_object_id=g['end_point_id'],role='ExplicitLineEndPoint') for g in source[::-1]]
                elif kind in ('EllipseMajorRadius','EllipseMinorRadius') and [g['kind'] for g in source]==['Ellipse']:
                    g=source[0];major=kind=='EllipseMajorRadius';axis=g['stored_major_axis' if major else 'stored_minor_axis']
                    radius=g['major_radius_cm' if major else 'minor_radius_cm'];center=g['center_cm']
                    if not math.isclose(distance,radius,abs_tol=1e-9):raise ValueError('Ellipse measurement differs from explicit selected radius')
                    expected=[_along(center,radius,axis),center]
                    projected=[_along(text,_dot(_sub(p,text),axis),axis) for p in expected]
                    roles=[dict(source_entity_object_id=g['object_id'],role='StoredPositiveMajorAxisRadiusPoint' if major else 'StoredPositiveMinorAxisRadiusPoint'),
                           dict(source_entity_object_id=g['object_id'],source_point_object_id=g['center_point_id'],role='ExplicitEllipseCenter')]
                elif kind=='ConcentricCircle' and [g['kind'] for g in source]==['Circle','Circle']:
                    first,second=source
                    if (not same(first['center_cm'],second['center_cm']) or not second['radius_cm']>first['radius_cm']
                            or any(not same(g['normal'],[0.,0.,1.]) for g in source)):
                        raise ValueError('Only observed concentric inner-first full circles supported')
                    direction=_unit(_sub(text,first['center_cm']))
                    expected=[_along(g['center_cm'],g['radius_cm'],direction) for g in source[::-1]]
                    projected=expected
                    roles=[dict(source_entity_object_id=g['object_id'],role='CirclePointAlongAnnotationRadialDirection') for g in source[::-1]]
                elif kind=='LinearDiameter' and [g['kind'] for g in source]==['Line','Point']:
                    line,point=source;direction=_unit(_sub(line['end_cm'],line['start_cm']))
                    center=_along(line['start_cm'],_dot(_sub(point['position_cm'],line['start_cm']),direction),direction)
                    reflected=[2*x-y for x,y in zip(center,point['position_cm'])]
                    expected=[reflected,point['position_cm']]
                    projected=[_along(p,_dot(_sub(text,p),direction),direction) for p in expected]
                    roles=[dict(source_entity_object_id=line['object_id'],reflected_source_point_object_id=point['object_id'],role='PointReflectedAcrossExplicitFirstInputLine'),
                           dict(source_entity_object_id=point['object_id'],role='ExplicitSecondInputPoint')]
                else:raise ValueError('Unobserved shared-linear measurement source variant')
                if not all(same(p,q) for p,q in zip(anchors,expected)) or not all(same(p,q) for p,q in zip(projections,projected)):
                    raise ValueError('Stored dimension points disagree with explicit source-role construction and annotation projection')
                result['decoded'].append(dict(object_id=r.object_id,kind=kind,sketch_object_id=sketch['sketch_object_id'],
                    binding_object_id=dim['binding_object_id'],entity_ids=dim['entity_ids'],
                    stored_measurement_line_points_cm=projections,stored_source_anchor_points_cm=anchors,source_anchor_roles=roles,
                    cached_measurement_cm=distance,stored_repeated_anchor_cm=repeated,
                    geometry_cache_offset=r.body+cursor,geometry_cache_byte_count=129,
                    stored_pre_measurement_control_byte=0,
                    coordinate_system='sketch-local',coordinate_units='cm',
                    source_identity_scope='Explicit ordered dimension inputs and typed reciprocal sketch ownership before geometric copy/construction checks',
                    annotation_scope='Existing bounded annotation field reused; no new textPosition getter, flag or style semantics claimed',scope=SCOPE))
            except (ValueError,KeyError,IndexError,struct.error) as error:
                result['unresolved'].append(dict(object_id=r.object_id,kind='DimensionMeasurementCache',reason=str(error)))
    return result
