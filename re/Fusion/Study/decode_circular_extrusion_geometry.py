"""Native-control mathematical cylinders/frusta, without cached BRep inputs.

The caller independently qualifies the source Circle and its component frame.
The observed positive one-side taper grows radius away from the profile plane.
No native UV, topology ID, occurrence solve or history assignment is made.
"""
import math

TOLERANCE=1e-9
SCOPE=('Derived capped circular straight extrusion from a qualified native Circle, '
       'component frame and observed signed Distance/Offset, symmetric Full/Half '
       'or two-sided zero-taper controls; positive one-sided profile-plane taper '
       'uses the observed expanding radius. Mathematical carriers/caps only, no '
       'native UV, cap ENTITY assignment, arbitrary end condition or general regeneration.')


def _number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError('Circular extrusion requires finite numeric operands')
    return value


def _vector(value):
    if not isinstance(value,(list,tuple)) or len(value)!=3:
        raise ValueError('Circular extrusion requires three-vector operands')
    return [_number(v) for v in value]


def _dot(a,b):return _number(sum(x*y for x,y in zip(a,b)))
def _cross(a,b):return _vector([a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]])
def _length(v):return _number(math.hypot(*v))


def extrusion_stations(controls):
    """Radius-free signed stations from the observed native extent/start family.

    Each taper applies to the displacement from the original profile plane.
    The qualified nonzero-taper family has its start on that plane.
    """
    if controls['operation']['kind']!='NewBody' or controls['is_solid'] is not True:
        raise ValueError('Circular extrusion requires a solid NewBody operation')
    start=controls['start'];extent=controls['extent'];one=extent['side_one'];mode=extent['mode']
    if start['kind'] not in ('ProfilePlane','Offset'):
        raise ValueError('Circular extrusion selected start geometry is unsupported')
    offset=0. if start['kind']=='ProfilePlane' else _number(start['offset_cm'])
    if one['condition']!='Distance' or one['uninterpreted_flags']!=0:
        raise ValueError('Circular extrusion requires observed Distance side-one controls')
    distance=_number(one['distance_cm']);taper=_number(one['taper_angle_radians'])
    if abs(distance)<=TOLERANCE:raise ValueError('Circular extrusion requires nonzero signed distance')
    if controls['stored_second_extent_enabled']!=(0 if mode=='OneSided' else 1):
        raise ValueError('Circular extrusion active-side enable field differs')
    if mode=='OneSided':
        if taper and (distance<=0 or start['kind']!='ProfilePlane' or not 0<taper<math.pi/2):
            raise ValueError('Circular extrusion taper outside the observed positive one-side profile-plane family')
        stations=[dict(axial_distance_cm=offset,taper_angle_radians=0.,native_control_role='Start'),
            dict(axial_distance_cm=_number(offset+distance),taper_angle_radians=taper,native_control_role='SideOneEnd')]
    elif mode=='Symmetric':
        if taper or start['kind']!='ProfilePlane' or distance<=0:
            raise ValueError('Circular extrusion symmetric family requires positive zero-taper profile-plane distance')
        convention=extent['distance_convention']
        if convention not in ('FullLength','HalfLength'):
            raise ValueError('Circular extrusion symmetric distance convention unsupported')
        half=distance/2 if convention=='FullLength' else distance
        stations=[dict(axial_distance_cm=-half,taper_angle_radians=0.,native_control_role='NegativeSymmetricEnd'),
            dict(axial_distance_cm=half,taper_angle_radians=0.,native_control_role='PositiveSymmetricEnd')]
    elif mode=='TwoSided':
        two=extent['side_two']
        if (start['kind']!='ProfilePlane' or taper or distance<=0 or two['condition']!='Distance'
                or two['uninterpreted_flags']!=0 or _number(two['taper_angle_radians'])):
            raise ValueError('Circular extrusion two-sided family requires positive zero-taper profile-plane Distance sides')
        other=_number(two['distance_cm'])
        if other<=TOLERANCE:raise ValueError('Circular extrusion side-two distance is not positive')
        stations=[dict(axial_distance_cm=-other,taper_angle_radians=0.,native_control_role='SideTwoEnd'),
            dict(axial_distance_cm=distance,taper_angle_radians=0.,native_control_role='SideOneEnd')]
    else:raise ValueError('Circular extrusion extent mode unsupported')
    stations.sort(key=lambda s:s['axial_distance_cm'])
    if stations[1]['axial_distance_cm']-stations[0]['axial_distance_cm']<=TOLERANCE:
        raise ValueError('Circular extrusion cap separation is not positive')
    return stations


def circular_extrusion_stations(radius_cm,controls):
    """Add Circle radii to the independently derived signed axial stations."""
    radius=_number(radius_cm)
    if radius<=TOLERANCE:raise ValueError('Circular extrusion source radius is not positive')
    stations=extrusion_stations(controls)
    for row in stations:
        row['radius_cm']=_number(radius+row['axial_distance_cm']*math.tan(row['taper_angle_radians']))
    if any(s['radius_cm']<=TOLERANCE for s in stations):
        raise ValueError('Circular extrusion radius collapses at a cap')
    return stations


def derive_circular_extrusion(center_cm,unit_axis,reference_u,radius_cm,controls):
    center,axis,u=_vector(center_cm),_vector(unit_axis),_vector(reference_u)
    if not math.isclose(_length(axis),1.,abs_tol=TOLERANCE,rel_tol=0.) or not math.isclose(_length(u),1.,abs_tol=TOLERANCE,rel_tol=0.) or abs(_dot(axis,u))>TOLERANCE:
        raise ValueError('Circular extrusion component Circle frame is not orthonormal')
    v=_cross(axis,u)
    stations=circular_extrusion_stations(radius_cm,controls)
    for row in stations:
        row['center_cm']=_vector([c+row['axial_distance_cm']*a for c,a in zip(center,axis)])
    low,high=stations;length=_number(high['axial_distance_cm']-low['axial_distance_cm'])
    slope=_number((high['radius_cm']-low['radius_cm'])/length)
    intercept=_number(low['radius_cm']-slope*low['axial_distance_cm'])
    caps=[]
    for ordinal,row in enumerate(stations):
        normal=[(-1 if ordinal==0 else 1)*x for x in axis]
        caps.append(dict(semantic_role='LowerAxialCap' if ordinal==0 else 'UpperAxialCap',
            center_cm=row['center_cm'],radius_cm=row['radius_cm'],axis_unit=axis,reference_u=u,reference_v=v,
            mathematical_outward_unit_normal=normal,plane_constant_cm=_dot(normal,row['center_cm']),
            circle_definition='C + R*(U*cos(theta)+V*sin(theta)), 0<=theta<2*pi; chosen mathematical angle, no native UV',
            disk_definition='C + rho*(U*cos(theta)+V*sin(theta)), 0<=rho<=R',
            native_FACE_identity=None,native_EDGE_identity=None,native_UV=None))
    radial_extents=[math.hypot(u[i],v[i]) for i in range(3)]
    bounds=dict(minimum=[min(s['center_cm'][i]-s['radius_cm']*radial_extents[i] for s in stations) for i in range(3)],
        maximum=[max(s['center_cm'][i]+s['radius_cm']*radial_extents[i] for s in stations) for i in range(3)])
    _vector(bounds['minimum']);_vector(bounds['maximum'])
    r0,r1=low['radius_cm'],high['radius_cm']
    volume=_number(math.pi*length*(r0*r0+r0*r1+r1*r1)/3)
    slant=_number(math.hypot(length,r1-r0))
    lateral_area=_number(math.pi*(r0+r1)*slant)
    total_area=_number(lateral_area+math.pi*(r0*r0+r1*r1))
    if volume<=TOLERANCE:raise ValueError('Circular extrusion has no positive finite volume')
    return dict(source_circle=dict(center_cm=center,radius_cm=radius_cm,unit_axis=axis,reference_u=u,reference_v=v),
        axial_stations=stations,mathematical_disk_caps=caps,
        lateral_carrier=dict(kind='Cylinder' if slope==0 else 'Cone',axis_origin_cm=center,unit_axis=axis,
            radial_slope=slope,radial_intercept_cm=intercept,axial_domain_cm=[low['axial_distance_cm'],high['axial_distance_cm']],
            radius_definition='radius(h)=radial_intercept+radial_slope*h, h=axis dot (P-axis_origin)',
            implicit_definition='squared norm(P-axis_origin-h*axis) = radius(h)^2',
            chosen_parameterization='P(h,theta)=axis_origin+h*axis+radius(h)*(U*cos(theta)+V*sin(theta))',
            chosen_half_angle_radians=math.atan(slope),native_UV=None,native_FACE_identity=None),
        axial_length_cm=length,volume_cm3=volume,lateral_area_cm2=lateral_area,total_area_cm2=total_area,
        component_axis_aligned_bounds_cm=bounds,
        source_to_cache_entity_mapping=None,scope=SCOPE)
