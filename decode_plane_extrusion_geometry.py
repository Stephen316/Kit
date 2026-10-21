"""Mathematical limits from an independently qualified selected native plane.

No selection identities or cached BRep coordinates are inputs to this helper.
Original ToEntity/FromEntity controls stay distinct from constructed equivalent
Distance operands, which exist only to reuse the established primitive builder.
"""
import math

from decode_circular_extrusion_geometry import derive_circular_extrusion

TOLERANCE=1e-9
SCOPE=('Native selected parallel/co-directed plane, positive plane intersection, '
       'observed nonnegative ToEntity/FromEntity offset and zero-taper one-sided '
       'solid NewBody construction. Distance-equivalent operands are derived '
       'mathematical inputs, not rewritten native controls. No selected BRep, '
       'reversed/oblique target convention, UV, ENTITY or chronological identity.')


def _number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError('Plane extrusion requires finite numeric operands')
    return value


def _vector(value):
    if not isinstance(value,(list,tuple)) or len(value)!=3:
        raise ValueError('Plane extrusion requires three-vector operands')
    return [_number(v) for v in value]


def _dot(a,b):return _number(sum(x*y for x,y in zip(a,b)))


def plane_extrusion_stations(profile_plane_origin_cm,unit_axis,controls,planes):
    """Intersect the extrusion axis with the selected plane before offsets.

    The caller proves native plane definition/selection/component provenance.
    Co-directed normals bound the offset law to the observed convention: offset
    along either the plane normal or extrusion axis is the same displacement.
    """
    profile,axis=_vector(profile_plane_origin_cm),_vector(unit_axis)
    if not math.isclose(_dot(axis,axis),1.,rel_tol=0.,abs_tol=TOLERANCE):
        raise ValueError('Plane extrusion axis is not unit')
    extent,start=controls['extent'],controls['start'];one=extent['side_one']
    if (controls['operation']['kind']!='NewBody' or controls['is_solid'] is not True
            or extent['mode']!='OneSided' or controls['stored_second_extent_enabled']!=0
            or _number(one['taper_angle_radians'])!=0.):
        raise ValueError('Plane extrusion requires observed zero-taper one-sided solid NewBody controls')
    if start['kind']=='ProfilePlane' and one['condition']=='ToEntity' and one['uninterpreted_flags']==1:
        role,kind='side_one','ToParallelPlane'
        offset=_number(one['offset_cm'])
    elif start['kind']=='FromEntity' and one['condition']=='Distance' and one['uninterpreted_flags']==0:
        role,kind='start','FromParallelPlane'
        offset=_number(start['offset_cm'])
    else:
        raise ValueError('Plane extrusion start/end pair outside the observed selected-plane family')
    if offset<0:
        raise ValueError('Plane extrusion negative selected-plane offset convention is unverified')
    if not isinstance(planes,dict) or set(planes)!={role}:
        raise ValueError('Plane extrusion requires exactly the active selected-plane operand')
    origin,normal=_vector(planes[role]['origin_cm']),_vector(planes[role]['normal'])
    if not math.isclose(_dot(normal,normal),1.,rel_tol=0.,abs_tol=TOLERANCE):
        raise ValueError('Plane extrusion selected-plane normal is not unit')
    denominator=_dot(normal,axis)
    if (not math.isclose(denominator,1.,rel_tol=0.,abs_tol=TOLERANCE)
            or max(abs(n-a) for n,a in zip(normal,axis))>TOLERANCE):
        raise ValueError('Plane extrusion requires parallel co-directed plane and extrusion normals')
    distance=_number(_dot(normal,[p-q for p,q in zip(origin,profile)])/denominator)
    if distance<=TOLERANCE:
        raise ValueError('Plane extrusion selected plane is not forward from the profile plane')
    limit=_number(distance+offset)
    if kind=='ToParallelPlane':
        low,high=0.,limit
        roles=('ProfilePlaneStart','ToEntityEnd')
    else:
        length=_number(one['distance_cm'])
        if length<=TOLERANCE:
            raise ValueError('Plane extrusion FromEntity requires positive Distance')
        low,high=limit,_number(limit+length)
        roles=('FromEntityStart','DistanceEnd')
    length=_number(high-low)
    if length<=TOLERANCE:
        raise ValueError('Plane extrusion selected limits have no positive separation')
    equivalent=dict(operation=dict(kind='NewBody'),is_solid=True,stored_second_extent_enabled=0,
        start=dict(kind='ProfilePlane') if low==0 else dict(kind='Offset',offset_cm=low),
        extent=dict(mode='OneSided',side_one=dict(condition='Distance',uninterpreted_flags=0,
            taper_angle_radians=0.,distance_cm=length)))
    return dict(axial_stations=[dict(axial_distance_cm=h,taper_angle_radians=0.,native_control_role=role_name)
            for h,role_name in zip((low,high),roles)],
        plane_limit_derivation=dict(kind=kind,selected_plane_role=role,profile_plane_origin_cm=profile,
            extrusion_unit_axis=axis,selected_plane_origin_cm=origin,selected_plane_unit_normal=normal,
            selected_plane_equation_constant_cm=_dot(normal,origin),plane_axis_denominator=denominator,
            selected_plane_intersection_distance_cm=distance,original_selected_offset_cm=offset,
            derived_axial_interval_cm=[low,high],offset_scope='Observed nonnegative offset with co-directed plane normal and extrusion axis only',
            native_start_kind=start['kind'],native_end_kind=one['condition'],
            native_uninterpreted_side_flags=one['uninterpreted_flags'],
            mathematical_equivalent_controls_are_native_records=False),
        mathematical_equivalent_distance_controls=equivalent,scope=SCOPE)


def derive_plane_limited_circular_extrusion(center_cm,unit_axis,reference_u,radius_cm,controls,planes):
    derivation=plane_extrusion_stations(center_cm,unit_axis,controls,planes)
    result=derive_circular_extrusion(center_cm,unit_axis,reference_u,radius_cm,
        derivation['mathematical_equivalent_distance_controls'])
    for published,source in zip(result['axial_stations'],derivation['axial_stations']):
        published['native_control_role']=source['native_control_role']
    result['plane_limit_derivation']=derivation['plane_limit_derivation']
    result['mathematical_equivalent_distance_controls']=derivation['mathematical_equivalent_distance_controls']
    result['scope']=SCOPE
    return result
