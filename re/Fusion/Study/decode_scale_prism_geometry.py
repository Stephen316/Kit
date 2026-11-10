"""Pure native-operand prism construction and diagonal Scale mathematics.

The caller must fix native identities and derive the eight source positions
from Sketch/Extrude records before calling. No cache points, fitting, matching,
API state, native UV conventions or journal chronology enter this helper.
"""
import math

TOLERANCE = 1e-9
SCOPE = ('Derived convex four-Line prism with eight native-Sketch/Extrude vertices, '
         'twelve straight segments and six planar quadrilateral boundaries, followed '
         'by positive component-frame diagonal Scale; mathematical carrier frames '
         'and outward normals only, no native UV, cache lifecycle or native writing')


def _number(x):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x):
        raise ValueError('Prism construction requires finite numeric operands')
    return x


def _vector(v):
    if not isinstance(v,(tuple,list)) or len(v)!=3:
        raise ValueError('Prism construction requires three-vector operands')
    return [_number(x) for x in v]


def _id(x):
    if type(x) is not int or x<0:
        raise ValueError('Prism construction requires nonnegative integer identities')
    return x


def _sub(a,b):return _vector([x-y for x,y in zip(a,b)])
def _dot(a,b):return _number(sum(x*y for x,y in zip(a,b)))
def _cross(a,b):return _vector([a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]])
def _length(v):return _number(math.hypot(*v))
def _pair(a,b):return tuple(sorted((a,b)))


def _face(cycle,positions,centroid):
    points=[positions[v] for v in cycle]
    u,v=_sub(points[1],points[0]),_sub(points[3],points[0])
    normal=_cross(u,v);length=_length(normal)
    if length<=TOLERANCE:raise ValueError('Derived prism quad is degenerate')
    normal=[x/length for x in normal]
    if any(abs(_dot(normal,_sub(p,points[0])))>TOLERANCE for p in points):
        raise ValueError('Derived prism quad is not planar')
    turns=[_dot(_cross(_sub(points[(i+1)%4],points[i]),
        _sub(points[(i+2)%4],points[(i+1)%4])),normal) for i in range(4)]
    if any(t<=TOLERANCE for t in turns):
        raise ValueError('Derived prism quad is not a simple strictly convex boundary')
    side=_dot(normal,_sub(centroid,points[0]))
    if abs(side)<=TOLERANCE:raise ValueError('Derived prism has no strict interior')
    outward_cycle=list(cycle)
    if side>0:
        normal=[-x for x in normal];outward_cycle.reverse()
    constant=_dot(normal,points[0])
    if any(_dot(normal,p)-constant>TOLERANCE for p in positions.values()):
        raise ValueError('Derived prism boundary does not enclose a convex solid')
    return dict(vertex_cycle=list(cycle),outward_mathematical_vertex_cycle=outward_cycle,
        corner_positions_cm=points,carrier_origin_cm=points[0],carrier_u_vector_cm=u,
        carrier_v_vector_cm=v,outward_mathematical_unit_normal=normal,
        plane_constant_cm=constant,
        carrier_definition='P(u,v)=origin+u*U+v*V for all real u,v; bounded region is the explicit quadrilateral, not a claimed native parameter rectangle',
        normal_scope='Chosen outward mathematical normal from derived solid centroid; native FACE sense and UV conventions are not inferred')


def _geometry(positions,edges,faces):
    centroid=[_number(sum(p[i] for p in positions.values())/8) for i in range(3)]
    boundary=[];volume6=0.
    for face in faces:
        carrier=_face(face['vertex_cycle'],positions,centroid)
        cycle=carrier['outward_mathematical_vertex_cycle'];p=[positions[v] for v in cycle]
        # Translation-invariant triangulated signed volume about a derived
        # interior point, using the independently fixed polygon incidence.
        for i in (1,2):
            volume6=_number(volume6+_dot(_sub(p[0],centroid),
                _cross(_sub(p[i],centroid),_sub(p[i+1],centroid))))
        boundary.append(dict(face_index=face['face_index'],**carrier))
    volume=_number(volume6/6)
    if volume<=TOLERANCE:raise ValueError('Derived prism has no positive finite volume')
    segments=[]
    for edge in edges:
        a,b=edge['vertex_indices'];start,end=positions[a],positions[b];direction=_sub(end,start)
        if _length(direction)<=TOLERANCE:raise ValueError('Derived prism has a zero-length segment')
        segments.append(dict(edge_index=edge['edge_index'],vertex_indices=[a,b],
            start_position_cm=start,end_position_cm=end,direction_cm=direction,
            mathematical_parameter_domain=[0.,1.],
            definition='P(t)=start+t*(end-start), 0<=t<=1; native EDGE parameterization remains separate'))
    return dict(centroid_cm=centroid,segments=segments,planar_quadrilateral_boundaries=boundary,
        volume_cm3=volume,axis_aligned_bounds_cm=dict(minimum=[min(p[i] for p in positions.values()) for i in range(3)],
            maximum=[max(p[i] for p in positions.values()) for i in range(3)]))


def derive_scaled_prism(vertices,edge_vertex_pairs,face_vertex_cycles,center,factors):
    """Construct a bounded prism from fixed identities and source positions."""
    center,factors=_vector(center),_vector(factors)
    if any(f<=0 for f in factors):raise ValueError('Only positive diagonal Scale factors are qualified')
    if len(vertices)!=8 or len(edge_vertex_pairs)!=12 or len(face_vertex_cycles)!=6:
        raise ValueError('Prism construction requires eight vertices, twelve edges and six quads')
    positions={};layers={0:{},1:{}};rows=[]
    for row in vertices:
        identity=_id(row['vertex_index']);point=_id(row['native_sketch_point_object_id']);layer=row['layer']
        if type(layer) is not int or layer not in (0,1) or identity in positions or point in layers[layer]:
            raise ValueError('Prism source vertex/point/layer identities are ambiguous')
        p=_vector(row['derived_position_cm']);positions[identity]=p;layers[layer][point]=identity
        rows.append(dict(vertex_index=identity,native_sketch_point_object_id=point,layer=layer,source_position_cm=p))
    if len(layers[0])!=4 or set(layers[0])!=set(layers[1]):
        raise ValueError('Prism layers do not contain the same four native Sketch points')
    translations=[_sub(positions[layers[1][p]],positions[layers[0][p]]) for p in sorted(layers[0])]
    translation=translations[0]
    if _length(translation)<=TOLERANCE or any(math.dist(t,translation)>TOLERANCE for t in translations):
        raise ValueError('Source positions do not form a single nonzero Extrude translation')
    edges=[];edge_ids=set();pairs=set();degree={v:0 for v in positions}
    for row in edge_vertex_pairs:
        identity=_id(row['edge_index']);pair=list(row['vertex_indices'])
        if len(pair)!=2 or any(type(v) is not int or v not in positions for v in pair) or pair[0]==pair[1]:
            raise ValueError('Prism EDGE has invalid endpoint identities')
        key=_pair(*pair)
        if identity in edge_ids or key in pairs:raise ValueError('Prism EDGE identities/endpoints repeat')
        edge_ids.add(identity);pairs.add(key)
        for v in pair:degree[v]+=1
        edges.append(dict(edge_index=identity,vertex_indices=pair))
    if set(degree.values())!={3}:raise ValueError('Prism vertex degree is not three')
    faces=[];face_ids=set();face_sets=set();uses={p:0 for p in pairs}
    for row in face_vertex_cycles:
        identity=_id(row['face_index']);cycle=list(row['vertex_cycle'])
        if len(cycle)!=4 or len(set(cycle))!=4 or any(type(v) is not int or v not in positions for v in cycle):
            raise ValueError('Prism FACE has invalid quadrilateral vertex identities')
        key=frozenset(cycle)
        if identity in face_ids or key in face_sets:raise ValueError('Prism FACE identities/membership repeat')
        face_ids.add(identity);face_sets.add(key)
        for a,b in zip(cycle,cycle[1:]+cycle[:1]):
            if _pair(a,b) not in pairs:raise ValueError('Prism FACE boundary leaves fixed EDGE incidence')
            uses[_pair(a,b)]+=1
        faces.append(dict(face_index=identity,vertex_cycle=cycle))
    if set(uses.values())!={2}:raise ValueError('Prism boundary is not a closed two-FACE-per-EDGE manifold')
    if frozenset(layers[0].values()) not in face_sets or frozenset(layers[1].values()) not in face_sets:
        raise ValueError('Prism cap FACE identities do not exhaust the source point layers')
    for point in layers[0]:
        if _pair(layers[0][point],layers[1][point]) not in pairs:
            raise ValueError('Prism lacks an explicit layer-connecting EDGE for a native Sketch point')
    transformed={i:_vector([c+f*(p-c) for p,c,f in zip(pos,center,factors)]) for i,pos in positions.items()}
    source=_geometry(positions,edges,faces);scaled=_geometry(transformed,edges,faces)
    determinant=_number(math.prod(factors));expected_volume=_number(source['volume_cm3']*determinant)
    if not math.isclose(scaled['volume_cm3'],expected_volume,rel_tol=1e-10,abs_tol=TOLERANCE):
        raise ValueError('Derived Scale solid volume disagrees with its affine determinant')
    for row in rows:row['scaled_position_cm']=transformed[row['vertex_index']]
    return dict(vertices=rows,source_prism=source,scaled_prism=scaled,
        source_extrude_translation_cm=translation,center_cm=center,factors=factors,
        affine_matrix_4x4=[[factors[0],0.,0.,_number(center[0]*(1-factors[0]))],
            [0.,factors[1],0.,_number(center[1]*(1-factors[1]))],
            [0.,0.,factors[2],_number(center[2]*(1-factors[2]))],[0.,0.,0.,1.]],
        determinant=determinant,expected_scaled_volume_cm3=expected_volume,
        volume_residual_cm3=abs(scaled['volume_cm3']-expected_volume),
        position_definition='scaled = center + diag(factors) * (source - center)',scope=SCOPE)
