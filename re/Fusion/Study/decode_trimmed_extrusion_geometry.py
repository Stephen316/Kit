"""Straight extrusion of a native-derived simple Line/Circle portion boundary.

Only source primitives, selected mathematical parameter intervals, a rigid
Sketch frame and native controls are inputs. Endpoint joins construct abstract
mathematical roles; no cached coordinate or native VERTEX identity is chosen.
"""
import math

from decode_circular_extrusion_geometry import extrusion_stations
from decode_placement import rigid_matrix

EPS=1e-9
TAU=2*math.pi
SCOPE=('Finite zero-taper extrusion of a qualified simple two/four-portion Line/Circle '
    'boundary. Source-derived mathematical endpoints establish only an abstract '
    'closed cycle. Exact carriers/domains, Green area, volume and rigid-frame bounds '
    'are constructed without cached coordinates, native ENTITY assignments, native '
    'UV/traversal, chronology, a solver or general CAD regeneration.')


def _number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError('Trimmed extrusion requires finite numeric operands')
    return value


def _point(value):
    if not isinstance(value,(tuple,list)) or len(value)!=3:
        raise ValueError('Trimmed extrusion requires three-vector source operands')
    result=[_number(v) for v in value]
    if abs(result[2])>EPS:raise ValueError('Trimmed extrusion source must lie in local XY')
    return result


def _dot(a,b):return _number(sum(x*y for x,y in zip(a,b)))
def _cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def _cross2(a,b):return a[0]*b[1]-a[1]*b[0]
def _close(a,b):return math.dist(a,b)<=EPS


def _angle_on(value,a,b,interior=False):
    delta=(value-a)%TAU
    if TAU-delta<=EPS:delta=0.
    return EPS<delta<b-a-EPS if interior else -EPS<=delta<=b-a+EPS


def _contains(row,point,interior=False):
    if row['kind']=='CircleArc':
        c=row['source_geometry']['center_cm'];radius=row['source_geometry']['radius_cm']
        if abs(math.hypot(point[0]-c[0],point[1]-c[1])-radius)>EPS:return False
        return _angle_on(math.atan2(point[1]-c[1],point[0]-c[0]),*row['parameter_interval'],interior=interior)
    a,b=row['_ends'];v=[y-x for x,y in zip(a,b)];delta=[p-x for p,x in zip(point,a)]
    t=_dot(delta,v)/_dot(v,v)
    if math.dist([x+t*d for x,d in zip(a,v)],point)>EPS:return False
    return EPS<t<1-EPS if interior else -EPS<=t<=1+EPS


def _intersections(a,b):
    """All finite underlying intersections, then bounded-window filtering."""
    if a['kind']=='LineSegment' and b['kind']=='CircleArc':return _intersections(b,a)
    points=[]
    if a['kind']==b['kind']=='LineSegment':
        p,p1=a['_ends'];q,q1=b['_ends'];r=[y-x for x,y in zip(p,p1)];s=[y-x for x,y in zip(q,q1)]
        delta=[y-x for x,y in zip(p,q)];denominator=_cross2(r,s)
        if abs(denominator)<=EPS:
            if abs(_cross2(delta,r))<=EPS:
                if any(_contains(a,p,True) for p in b['_ends']) or any(_contains(b,p,True) for p in a['_ends']):
                    raise ValueError('Trimmed extrusion has overlapping collinear portions')
                if all(any(_close(x,y) for y in b['_ends']) for x in a['_ends']):
                    raise ValueError('Trimmed extrusion repeats a Line segment')
            return []
        t=_cross2(delta,s)/denominator
        points=[[x+t*d for x,d in zip(p,r)]]
    elif a['kind']==b['kind']=='CircleArc':
        ca,cb=a['source_geometry']['center_cm'],b['source_geometry']['center_cm']
        ra,rb=a['source_geometry']['radius_cm'],b['source_geometry']['radius_cm']
        delta=[y-x for x,y in zip(ca,cb)];distance=math.hypot(*delta[:2])
        if distance<=EPS:
            if abs(ra-rb)<=EPS:
                for row,other in ((a,b),(b,a)):
                    if any(_contains(other,p,True) for p in row['_ends']+[row['_midpoint']]):
                        raise ValueError('Trimmed extrusion has overlapping coincident-Circle portions')
            return []
        if distance>ra+rb+EPS or distance<abs(ra-rb)-EPS:return []
        along=(ra*ra-rb*rb+distance*distance)/(2*distance)
        squared=ra*ra-along*along
        if squared<-EPS:return []
        spread=math.sqrt(max(0.,squared));ux,uy=delta[0]/distance,delta[1]/distance
        points=[[ca[0]+along*ux-sign*spread*uy,ca[1]+along*uy+sign*spread*ux,0.] for sign in (-1,1)]
    else:
        circle,line=a,b;c=circle['source_geometry']['center_cm'];radius=circle['source_geometry']['radius_cm']
        p,q=line['_ends'];d=[y-x for x,y in zip(p,q)];relative=[x-y for x,y in zip(p,c)]
        aa=_dot(d,d);bb=2*_dot(relative,d);cc=_dot(relative,relative)-radius*radius
        discriminant=bb*bb-4*aa*cc
        if discriminant<-EPS:return []
        root=math.sqrt(max(0.,discriminant))
        points=[[x+((-bb+sign*root)/(2*aa))*v for x,v in zip(p,d)] for sign in (-1,1)]
    return [p for p in points if _contains(a,p) and _contains(b,p)]


def _prepare(portions):
    if not isinstance(portions,list) or len(portions) not in (2,4):
        raise ValueError('Trimmed extrusion requires the observed two/four-portion family')
    rows=[];roles=set();sources={}
    for source in portions:
        role=source['role_key'];identity=source['source_primitive_id'];kind=source['kind'];geometry=source['source_geometry']
        if not isinstance(role,str) or not role or role in roles:
            raise ValueError('Trimmed extrusion portion role missing or duplicated')
        if isinstance(identity,bool) or not isinstance(identity,int) or identity<=0:
            raise ValueError('Trimmed extrusion source primitive identity is invalid')
        roles.add(role)
        interval=source['parameter_interval']
        if not isinstance(interval,(tuple,list)) or len(interval)!=2:
            raise ValueError('Trimmed extrusion interval must have two finite values')
        a,b=[_number(v) for v in interval]
        if b-a<=EPS:raise ValueError('Trimmed extrusion source portion degenerates')
        if kind=='CircleArc':
            center=_point(geometry['center_cm']);radius=_number(geometry['radius_cm'])
        elif kind=='LineSegment':
            start,end=_point(geometry['start_cm']),_point(geometry['end_cm'])
        else:raise ValueError('Trimmed extrusion source kind is unsupported')
        if kind=='CircleArc':
            normal=geometry['normal'];reference=geometry['reference_axis']
            if (not isinstance(normal,(tuple,list)) or len(normal)!=3 or not isinstance(reference,(tuple,list)) or len(reference)!=3
                    or any(abs(_number(v)-w)>EPS for v,w in zip(normal,[0.,0.,1.]))
                    or any(abs(_number(v)-w)>EPS for v,w in zip(reference,[1.,0.,0.]))
                    or radius<=EPS or not 0<=a<b<=2*TAU or b-a>=TAU-EPS):
                raise ValueError('Trimmed extrusion Circle frame/radius/window is unsupported')
            geometry=dict(center_cm=center,radius_cm=radius,normal=list(normal),reference_axis=list(reference))
            def evaluate(t):return [center[0]+radius*math.cos(t),center[1]+radius*math.sin(t),0.]
            ends=[evaluate(a),evaluate(b)];midpoint=evaluate((a+b)/2)
            perimeter=radius*(b-a)
            integral=(radius*center[0]*(math.sin(b)-math.sin(a))+radius*center[1]*(math.cos(a)-math.cos(b))+radius*radius*(b-a))/2
        else:
            if not 0<=a<b<=1 or math.dist(start,end)<=EPS:
                raise ValueError('Trimmed extrusion Line frame/window is unsupported')
            geometry=dict(start_cm=start,end_cm=end)
            def evaluate(t):return [x+t*(y-x) for x,y in zip(start,end)]
            ends=[evaluate(a),evaluate(b)];midpoint=evaluate((a+b)/2)
            perimeter=math.dist(*ends);integral=_cross2(*ends)/2
        if _close(*ends):raise ValueError('Trimmed extrusion source window has coincident endpoints')
        if identity in sources and sources[identity]!=(kind,geometry):
            raise ValueError('Trimmed extrusion repeated source identity has inconsistent coefficients')
        sources[identity]=(kind,geometry)
        rows.append(dict(role_key=role,source_primitive_id=identity,kind=kind,source_geometry=geometry,
            parameter_interval=[a,b],_ends=ends,_midpoint=midpoint,_length=perimeter,_integral=integral))
    return rows


def derive_trimmed_extrusion(portions,sketch_to_component_matrix,controls):
    rows=_prepare(portions);matrix=rigid_matrix(sketch_to_component_matrix)
    if any(not math.isfinite(v) for v in matrix):raise ValueError('Trimmed extrusion frame is nonfinite')
    stations=extrusion_stations(controls)
    if any(s['taper_angle_radians'] for s in stations):raise ValueError('Trimmed extrusion taper is unsupported')
    low,high=[s['axial_distance_cm'] for s in stations];length=_number(high-low)
    axis=[matrix[2],matrix[6],matrix[10]];u=[matrix[0],matrix[4],matrix[8]];v=[matrix[1],matrix[5],matrix[9]]
    def transform(point,height=0.):
        return [_number(sum(matrix[4*i+j]*point[j] for j in range(3))+matrix[4*i+3]+height*axis[i]) for i in range(3)]
    vertices=[];end_roles={}
    for row in rows:
        ids=[]
        for point in row['_ends']:
            matches=[i for i,p in enumerate(vertices) if _close(p,point)]
            if len(matches)>1:raise ValueError('Trimmed extrusion mathematical endpoint join is ambiguous')
            if not matches:matches=[len(vertices)];vertices.append(point)
            ids.append(matches[0])
        end_roles[row['role_key']]=ids
    adjacency={i:[] for i in range(len(vertices))}
    for role,pair in end_roles.items():
        for i in pair:adjacency[i].append(role)
    if len(vertices)!=len(rows) or any(len(edges)!=2 for edges in adjacency.values()):
        raise ValueError('Trimmed extrusion source endpoints do not form a simple degree-two boundary')
    for index,a in enumerate(rows):
        for b in rows[index+1:]:
            for point in _intersections(a,b):
                if _contains(a,point,True) or _contains(b,point,True):
                    raise ValueError('Trimmed extrusion boundary self-intersects or touches at an interior point')
                if not any(_close(point,p) and any(_close(p,q) for q in b['_ends']) for p in a['_ends']):
                    raise ValueError('Trimmed extrusion intersection is not a shared mathematical endpoint')
    cycle=[];current=min(end_roles);vertex=end_roles[current][0];start_vertex=vertex;used=set()
    while current not in used:
        used.add(current);pair=end_roles[current];direction=1 if pair[0]==vertex else -1
        cycle.append(dict(role_key=current,direction=direction));vertex=pair[1] if direction==1 else pair[0]
        choices=[role for role in adjacency[vertex] if role!=current]
        if len(choices)!=1:raise ValueError('Trimmed extrusion source cycle is ambiguous')
        current=choices[0]
    if current!=cycle[0]['role_key'] or vertex!=start_vertex or len(used)!=len(rows):
        raise ValueError('Trimmed extrusion source boundary contains disconnected cycles')
    by={r['role_key']:r for r in rows}
    area=_number(sum(by[c['role_key']]['_integral']*c['direction'] for c in cycle))
    if abs(area)<=EPS:raise ValueError('Trimmed extrusion profile area degenerates')
    if area<0:
        area=-area;cycle=[dict(role_key=c['role_key'],direction=-c['direction']) for c in reversed(cycle)]
    directions={c['role_key']:c['direction'] for c in cycle}
    curves=[];extrema=[]
    for row in rows:
        kind,geometry=row['kind'],row['source_geometry'];a,b=row['parameter_interval'];layers=[]
        if kind=='CircleArc':
            center=transform(geometry['center_cm']);radius=geometry['radius_cm']
            component=dict(center_cm=center,radius_cm=radius,unit_axis=axis,reference_u=u,reference_v=v)
            for layer,height in enumerate((low,high)):
                layers.append(dict(layer=layer,axial_distance_cm=height,geometry=dict(kind=kind,
                    center_cm=transform(geometry['center_cm'],height),radius_cm=radius,unit_axis=axis,
                    reference_u=u,reference_v=v,angle_interval_radians=[a,b])))
                angles=[a,b]
                for i in range(3):
                    extremum=math.atan2(v[i],u[i])
                    for angle in (extremum,extremum+math.pi):
                        if _angle_on(angle,a,b):angles.append(angle)
                extrema.extend([[center[i]+height*axis[i]+radius*(math.cos(angle)*u[i]+math.sin(angle)*v[i]) for i in range(3)] for angle in angles])
            carrier=dict(kind='Cylinder',axis_origin_cm=center,unit_axis=axis,radius_cm=radius,
                reference_u=u,reference_v=v,angle_interval_radians=[a,b],axial_domain_cm=[low,high],
                chosen_mathematical_radial_normal_multiplier=directions[row['role_key']])
        else:
            component=dict(start_cm=transform(geometry['start_cm']),end_cm=transform(geometry['end_cm']))
            for layer,height in enumerate((low,high)):
                endpoints=[transform(p,height) for p in row['_ends']];extrema.extend(endpoints)
                layers.append(dict(layer=layer,axial_distance_cm=height,geometry=dict(kind=kind,start_cm=endpoints[0],end_cm=endpoints[1])))
            tangent=[directions[row['role_key']]*(y-x) for x,y in zip(layers[0]['geometry']['start_cm'],layers[0]['geometry']['end_cm'])]
            normal=_cross(tangent,axis);magnitude=math.hypot(*normal);normal=[x/magnitude for x in normal]
            origin=layers[0]['geometry']['start_cm']
            carrier=dict(kind='Plane',origin_cm=origin,unit_normal=normal,plane_constant_cm=_dot(normal,origin),axial_domain_cm=[low,high])
        curves.append(dict(role_key=row['role_key'],source_primitive_id=row['source_primitive_id'],kind=kind,
            parameter_interval=row['parameter_interval'],source_geometry=geometry,component_source_geometry=component,
            sketch_local_points_cm=dict(start=row['_ends'][0],midpoint=row['_midpoint'],end=row['_ends'][1]),
            mathematical_endpoint_roles=end_roles[row['role_key']],layer_curves=layers,side_carrier=carrier,
            arc_or_segment_length_cm=row['_length'],native_ENTITY_identity=None,native_UV=None))
    perimeter=_number(sum(r['_length'] for r in rows));volume=_number(area*length)
    bounds=dict(minimum=[_number(min(p[i] for p in extrema)) for i in range(3)],maximum=[_number(max(p[i] for p in extrema)) for i in range(3)])
    caps=[]
    for layer,height in enumerate((low,high)):
        normal=[(-1 if layer==0 else 1)*n for n in axis]
        boundary=cycle if layer else [dict(role_key=c['role_key'],direction=-c['direction']) for c in reversed(cycle)]
        caps.append(dict(layer=layer,unit_outward_normal=normal,plane_constant_cm=_dot(normal,transform([0.,0.,0.],height)),
            boundary_cycle=boundary,native_FACE_identity=None,native_traversal_semantics=None))
    return dict(profile=dict(mathematical_positive_boundary_cycle=cycle,area_cm2=area,perimeter_cm=perimeter,
            mathematical_vertices_local_cm=vertices,native_traversal_semantics=None),axial_stations=stations,
        boundary_curves=curves,connector_segments=[dict(mathematical_vertex_role=i,lower_cm=transform(p,low),upper_cm=transform(p,high),native_EDGE_identity=None)
            for i,p in enumerate(vertices)],caps=caps,volume_cm3=volume,lateral_area_cm2=_number(perimeter*length),
        total_area_cm2=_number(perimeter*length+2*area),component_axis_aligned_bounds_cm=bounds,
        source_to_cache_entity_mapping=None,scope=SCOPE)
