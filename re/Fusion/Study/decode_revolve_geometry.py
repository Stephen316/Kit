"""Native-input mathematical revolution, with an explicit source-relative axis.

The observed positive sweep leaves the source Sketch along its normal. Its
effective axis is derived from the source plane and occupied radial half-plane;
the stored selected-axis direction is retained separately and never fitted to a
result cache. Full Circle/semicircle analytic cases and convex 3/4-Line sections
produce complete mathematical carriers and bounded FACE/LOOP curves.
"""
import math

from decode_placement import rigid_matrix

EPS=1e-9
TAU=2*math.pi
SCOPE=('Constructed coplanar one-sided meridian revolution with observed '
    'source-relative positive angular orientation. Polygon sections use explicit '
    'one/two-sided/symmetric signed angle intervals; full Circle and semicircle '
    'profiles produce ring torus and sphere. Complete mathematical carrier/loop '
    'geometry, moments, area and bounds use no result cache or ENTITY assignment. '
    'Native UV, API traversal, arbitrary projected/straddling/entity-limit/Boolean '
    'semantics, chronological regeneration and writing remain unresolved.')


def _number(x):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x):
        raise ValueError('Revolve construction requires finite numeric operands')
    return x


def _v(value):
    if not isinstance(value,(list,tuple)) or len(value)!=3:
        raise ValueError('Revolve construction requires three-vector operands')
    return [_number(x) for x in value]


def _dot(a,b):return _number(sum(x*y for x,y in zip(a,b)))
def _sub(a,b):return [_number(x-y) for x,y in zip(a,b)]
def _cross(a,b):return _v([a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]])
def _unit(a):
    length=_number(math.hypot(*a))
    if length<=EPS:raise ValueError('Revolve construction has a degenerate direction')
    return [x/length for x in a]
def _near(a,b):return len(a)==len(b) and max((abs(x-y) for x,y in zip(a,b)),default=0.)<=EPS
def _on(theta,low,high):return (theta-low)%TAU<=high-low+EPS or TAU-(theta-low)%TAU<=EPS


def revolve_angle_interval(controls):
    if controls['operation']['kind']!='NewBody' or controls['is_solid'] is not True or controls['is_project_axis'] is not False:
        raise ValueError('Revolve construction requires unprojected solid NewBody controls')
    revolve=controls['revolve']
    if revolve['extent_kind']!='Angle':raise ValueError('Revolve selected entity angular limits are unsupported')
    along=_number(revolve['angle_radians']);mode=revolve['mode']
    if mode=='OneSided':low,high=sorted((0.,along))
    elif mode in ('Symmetric','TwoSided'):
        against=_number(revolve['against_angle_radians'])
        if along<=EPS or against<=EPS:
            raise ValueError('Revolve negative symmetric/two-sided angle convention is unverified')
        if mode=='Symmetric' and abs(along-against)>EPS:
            raise ValueError('Revolve symmetric native angles disagree')
        low,high=-against,along
    else:raise ValueError('Revolve angular mode unsupported')
    span=_number(high-low)
    if span<=EPS or span>TAU+1e-10:
        raise ValueError('Revolve angular span is degenerate or exceeds one turn')
    return [low,high],math.isclose(span,TAU,rel_tol=0.,abs_tol=1e-10)


def derive_revolve_geometry(profile,sketch_to_component_matrix,source_axis,controls):
    matrix=rigid_matrix(sketch_to_component_matrix)
    if not all(math.isfinite(x) for x in matrix):raise ValueError('Revolve Sketch frame is nonfinite')
    def point(p):
        p=_v(p)
        if p[2]!=0:raise ValueError('Revolve profile is outside its native local XY plane')
        return [_number(sum(matrix[4*i+j]*p[j] for j in range(3))+matrix[4*i+3]) for i in range(3)]
    def vector(p):
        p=_v(p);return [_number(sum(matrix[4*i+j]*p[j] for j in range(3))) for i in range(3)]
    plane_origin=point([0.,0.,0.]);normal=_unit(vector([0.,0.,1.]))
    origin=_v(source_axis['origin_cm']);stored_axis=_v(source_axis['direction']);axis=_unit(stored_axis)
    if abs(math.hypot(*stored_axis)-1.)>EPS or abs(_dot(axis,normal))>EPS or abs(_dot(_sub(origin,plane_origin),normal))>EPS:
        raise ValueError('Revolve selected axis is not a qualified unit line in the source Sketch plane')
    interval,full=revolve_angle_interval(controls);low,high=interval;span=high-low
    kind=profile['kind'];polygon=None;circle=None
    if kind=='Polygon':
        raw=profile['points_cm']
        if not isinstance(raw,list) or len(raw) not in (3,4):raise ValueError('Revolve polygon requires three/four cyclic corners')
        polygon=[point(p) for p in raw];representatives=polygon
    elif kind in ('Circle','Semicircle'):
        center=point(profile['center_cm']);radius=_number(profile['radius_cm'])
        cn,cu=vector(profile['normal']),vector(profile['reference_axis'])
        if (radius<=EPS or abs(math.hypot(*cn)-1)>EPS or abs(math.hypot(*cu)-1)>EPS
                or abs(_dot(cn,cu))>EPS or not (_near(cn,normal) or _near(cn,[-x for x in normal]))):
            raise ValueError('Revolve circular source frame/radius unsupported')
        cv=_cross(cn,cu)
        if not full:raise ValueError('Only captured full-turn circular/semicircular Revolves are qualified')
        def circle_point(theta):return [_number(c+radius*(math.cos(theta)*u+math.sin(theta)*v)) for c,u,v in zip(center,cu,cv)]
        circle=dict(center=center,radius=radius,normal=cn,u=cu,v=cv)
        if kind=='Circle':representatives=[center]
        else:
            a,b=[_number(x) for x in profile['angle_interval_radians']]
            if abs(b-a-math.pi)>EPS:raise ValueError('Revolve sphere source must be one semicircle')
            ends=[circle_point(a),circle_point(b)]
            diameter=[point(profile['diameter_start_cm']),point(profile['diameter_end_cm'])]
            if not all(any(_near(p,q) for q in diameter) for p in ends) or _near(*diameter):
                raise ValueError('Revolve semicircle/diameter endpoint correspondence differs')
            representatives=[circle_point((a+b)/2)];circle.update(ends=ends,interval=[a,b])
    else:raise ValueError('Revolve profile primitive family is unsupported')
    radial=None
    for p in representatives:
        delta=_sub(p,origin);height=_dot(delta,axis);candidate=[x-height*n for x,n in zip(delta,axis)]
        if math.hypot(*candidate)>EPS:radial=_unit(candidate);break
    if radial is None:raise ValueError('Revolve profile has no occupied radial half-plane')
    multiplier=1 if _dot(_cross(axis,radial),normal)>0 else -1
    axis=[multiplier*x for x in axis];tangent=_cross(axis,radial)
    if not _near(tangent,normal):raise ValueError('Revolve source-relative axis/radial/Sketch frame is not coplanar')
    def section(p):
        delta=_sub(p,origin);r,h=_dot(delta,radial),_dot(delta,axis)
        reconstructed=[o+h*n+r*u for o,n,u in zip(origin,axis,radial)]
        if not _near(reconstructed,p) or r<-EPS:
            raise ValueError('Revolve source crosses the axis or leaves its meridian half-plane')
        return [0. if abs(r)<=EPS else r,h]
    def rotate(r,h,theta):return [_number(o+h*n+r*(math.cos(theta)*u+math.sin(theta)*v)) for o,n,u,v in zip(origin,axis,radial,tangent)]
    def boundary(r,h,a=low,b=high):
        if r<=EPS:return dict(kind='PointSingularity',point_cm=rotate(0.,h,0.))
        return dict(kind='CircleArc',center_cm=rotate(0.,h,0.),radius_cm=r,unit_axis=axis,
            reference_u=radial,reference_v=tangent,angle_interval_radians=[0.,TAU] if full else [a,b],is_full_circle=full)
    def loop(curves):return dict(curves=curves,native_LOOP_identity=None,native_traversal_semantics=None)
    faces=[];extrema=[];meridian={};surface_area=0.
    if polygon is not None:
        rz=[section(p) for p in polygon];n=len(rz)
        turns=[]
        for i in range(n):
            a,b,c=rz[i-1],rz[i],rz[(i+1)%n]
            if math.dist(a,b)<=EPS:raise ValueError('Revolve source polygon edge degenerates')
            turns.append((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))
        if not (all(t>EPS for t in turns) or all(t<-EPS for t in turns)):
            raise ValueError('Revolve source polygon is not the observed simple convex section')
        crosses=[rz[i][0]*rz[(i+1)%n][1]-rz[(i+1)%n][0]*rz[i][1] for i in range(n)]
        signed_area=sum(crosses)/2;area=abs(signed_area)
        moment=sum((rz[i][0]+rz[(i+1)%n][0])*crosses[i] for i in range(n))/6
        if area<=EPS or abs(moment)<=EPS:raise ValueError('Revolve source section area/radial moment degenerates')
        volume=_number(abs(moment)*span)
        meridian=dict(vertices=[dict(position_cm=p,radial_distance_cm=r,axial_coordinate_cm=h) for p,(r,h) in zip(polygon,rz)],
            area_cm2=area,centroid_radius_cm=abs(moment)/area,radial_first_moment_cm3=abs(moment))
        for i,((r0,h0),(r1,h1)) in enumerate(zip(rz,rz[1:]+rz[:1])):
            if max(r0,r1)<=EPS:continue
            dh,dr=h1-h0,r1-r0
            edge_length=math.hypot(dh,dr);surface_area+=span*(r0+r1)*edge_length/2
            if abs(dh)<=EPS:
                carrier=dict(kind='Plane',origin_cm=rotate(0.,h0,0.),unit_normal=axis,
                    plane_constant_cm=_dot(axis,rotate(0.,h0,0.)))
            elif abs(dr)<=EPS:
                carrier=dict(kind='Cylinder',axis_origin_cm=origin,unit_axis=axis,radius_cm=r0)
            else:
                slope=_number(dr/dh);intercept=_number(r0-slope*h0)
                carrier=dict(kind='Cone',axis_origin_cm=origin,unit_axis=axis,radial_slope=slope,
                    radial_intercept_cm=intercept,axial_domain_cm=sorted((h0,h1)),
                    apex_cm=rotate(0.,_number(-intercept/slope),0.),half_angle_radians=math.atan(abs(slope)))
            if full:
                loops=[]
                for r,h in ((r0,h0),(r1,h1)):
                    if r>EPS or carrier['kind']=='Cone':loops.append(loop([boundary(r,h)]))
            else:
                curves=[dict(kind='LineSegment',start_cm=rotate(r0,h0,low),end_cm=rotate(r1,h1,low))]
                if r1>EPS:curves.append(boundary(r1,h1))
                curves.append(dict(kind='LineSegment',start_cm=rotate(r1,h1,high),end_cm=rotate(r0,h0,high)))
                if r0>EPS:
                    arc=boundary(r0,h0);arc['mathematical_direction']=-1;curves.append(arc)
                loops=[loop(curves)]
            faces.append(dict(role_key='meridian:'+str(i),carrier=carrier,boundary_loops=loops,native_FACE_identity=None))
        if not full:
            surface_area+=2*area
            for cap,theta in enumerate((low,high)):
                cap_points=[rotate(r,h,theta) for r,h in rz]
                out=[(-1 if cap==0 else 1)*(-math.sin(theta)*u+math.cos(theta)*v) for u,v in zip(radial,tangent)]
                curves=[dict(kind='LineSegment',start_cm=a,end_cm=b) for a,b in zip(cap_points,cap_points[1:]+cap_points[:1])]
                faces.append(dict(role_key='angular:'+str(cap),carrier=dict(kind='Plane',origin_cm=origin,
                    unit_normal=out,plane_constant_cm=_dot(out,origin)),boundary_loops=[loop(curves)],native_FACE_identity=None))
        for r,h in rz:
            angles=[low,high]
            for i in range(3):
                theta=math.atan2(tangent[i],radial[i])
                for t in (theta,theta+math.pi):
                    if full or _on(t,low,high):angles.append(t)
            extrema.extend(rotate(r,h,t) for t in angles)
        bounds=dict(minimum=[min(p[i] for p in extrema) for i in range(3)],maximum=[max(p[i] for p in extrema) for i in range(3)])
        result_kind='PolygonRevolve'
    elif kind=='Circle':
        major,height=section(circle['center']);minor=circle['radius']
        if major<=minor+EPS:raise ValueError('Revolve Circle must remain in the captured ring-torus radial half-plane')
        center=rotate(0.,height,0.);volume=_number(TAU*math.pi*major*minor*minor)
        surface_area=_number(4*math.pi*math.pi*major*minor)
        carrier=dict(kind='Torus',center_cm=center,unit_axis=axis,major_radius_cm=major,minor_radius_cm=minor)
        faces=[dict(role_key='torus',carrier=carrier,boundary_loops=[],native_FACE_identity=None)]
        extents=[major*math.sqrt(max(0.,1-n*n))+minor for n in axis]
        bounds=dict(minimum=[c-d for c,d in zip(center,extents)],maximum=[c+d for c,d in zip(center,extents)])
        meridian=dict(area_cm2=math.pi*minor*minor,centroid_radius_cm=major,source_circle_radius_cm=minor)
        result_kind='Torus'
    else:
        center=circle['center'];radius=circle['radius'];delta=_sub(center,origin)
        if math.dist(center,rotate(0.,_dot(delta,axis),0.))>EPS or any(section(p)[0]>EPS for p in circle['ends']):
            raise ValueError('Revolve semicircle centre/diameter is not on the selected axis')
        volume=_number(4*math.pi*radius**3/3);surface_area=_number(4*math.pi*radius*radius)
        faces=[dict(role_key='sphere',carrier=dict(kind='Sphere',center_cm=center,radius_cm=radius),boundary_loops=[],native_FACE_identity=None)]
        bounds=dict(minimum=[c-radius for c in center],maximum=[c+radius for c in center])
        meridian=dict(area_cm2=math.pi*radius*radius/2,centroid_radius_cm=4*radius/(3*math.pi),source_arc_angle_interval_radians=circle['interval'])
        result_kind='Sphere'
    _number(surface_area)
    for values in bounds.values():_v(values)
    return dict(kind=result_kind,profile_kind=kind,source_axis=dict(origin_cm=origin,direction=stored_axis),
        effective_axis=dict(origin_cm=origin,direction=axis,stored_direction_multiplier=multiplier,
            radial_reference_u=radial,normal_reference_v=tangent,
            orientation_rule='Observed positive angular sweep is source-normal directed: effective_axis cross occupied_radial = Sketch_normal; no target geometry input'),
        angular_interval_radians=interval,angular_span_radians=span,is_full_turn=full,
        meridian_profile=meridian,faces=faces,volume_cm3=volume,surface_area_cm2=surface_area,
        component_axis_aligned_bounds_cm=bounds,source_to_cache_entity_mapping=None,native_UV=None,scope=SCOPE)
