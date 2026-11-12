"""Pure rectangular box offsets with closed or opposite-face openings.

Source bounds must come from independently qualified native Sketch/Extrude
operands; opening axes from native source FACE identity. Semantic role keys are
constructed identities, never native ASM IDs or matches selected by geometry.
"""
import itertools
import math

TOLERANCE=1e-9
SCOPE=('Derived axis-aligned rectangular box material between outer and inner '
       'offset bounds with zero, one or two opposite planar openings; explicit '
       'semantic-role vertices, segments, planar patches and annular rim loops. '
       'No native entity assignment, UV, FACE sense, history or general Shell algorithm.')


def _scalar(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError('Box Shell requires finite numeric operands')
    return value


def _vector(value):
    if not isinstance(value,(list,tuple)) or len(value)!=3:
        raise ValueError('Box Shell requires three-vector source bounds')
    return [_scalar(x) for x in value]


def _key(role,bits):return role+':'+''.join(map(str,bits))
def _sub(a,b):return [_scalar(x-y) for x,y in zip(a,b)]
def _dot(a,b):return _scalar(sum(x*y for x,y in zip(a,b)))
def _cross(a,b):return [_scalar(a[1]*b[2]-a[2]*b[1]),_scalar(a[2]*b[0]-a[0]*b[2]),_scalar(a[0]*b[1]-a[1]*b[0])]


def _cycle(role,axis,side):
    other=[i for i in range(3) if i!=axis]
    result=[]
    for a,b in ((0,0),(1,0),(1,1),(0,1)):
        bits=[0,0,0];bits[axis]=side;bits[other[0]]=a;bits[other[1]]=b
        result.append(_key(role,bits))
    return result


def _oriented(cycle,positions,normal):
    points=[positions[k] for k in cycle]
    cross=_cross(_sub(points[1],points[0]),_sub(points[2],points[1]))
    if abs(_dot(cross,normal))<=TOLERANCE:raise ValueError('Box Shell planar loop is degenerate')
    return list(cycle) if _dot(cross,normal)>0 else list(reversed(cycle))


def derive_box_shell(source_bounds,inside,outside,removed_faces):
    """Construct offset material with semantic incidence, without cache data."""
    low,high=_vector(source_bounds['minimum']),_vector(source_bounds['maximum'])
    if any(b-a<=TOLERANCE for a,b in zip(low,high)):
        raise ValueError('Box Shell source bounds require positive dimensions')
    inner=_scalar(0. if inside is None else inside);outer=_scalar(0. if outside is None else outside)
    if inner<0 or outer<0 or inner+outer<=TOLERANCE:
        raise ValueError('Box Shell requires positive total, nonnegative active thicknesses')
    openings=set()
    for face in removed_faces:
        axis,side=face['axis'],face['side']
        if type(axis) is not int or axis not in (0,1,2) or type(side) is not int or side not in (0,1):
            raise ValueError('Box Shell opening must name a source axis and low/high side')
        if (axis,side) in openings:raise ValueError('Box Shell opening identity repeats')
        openings.add((axis,side))
    if len(openings)>2 or len(openings)==2 and len({a for a,s in openings})!=1:
        raise ValueError('Box Shell only closed, one-face or two-opposite-face openings are qualified')
    ol=[_scalar(x-outer) for x in low];oh=[_scalar(x+outer) for x in high]
    il=[_scalar(x+inner) for x in low];ih=[_scalar(x-inner) for x in high]
    for axis,side in openings:
        (ol if side==0 else oh)[axis]=(low if side==0 else high)[axis]
        (il if side==0 else ih)[axis]=(low if side==0 else high)[axis]
    if any(b-a<=TOLERANCE for a,b in zip(il,ih)):
        raise ValueError('Box Shell inner offset collapses its rectangular cavity')
    positions={};vertices=[]
    for role,left,right in (('outer',ol,oh),('inner',il,ih)):
        for bits in itertools.product((0,1),repeat=3):
            key=_key(role,bits);point=[(right if bit else left)[axis] for axis,bit in enumerate(bits)]
            positions[key]=point
            vertices.append(dict(key=key,role=role,corner_bits=list(bits),position_cm=point))
    if len({tuple(p) for p in positions.values()})!=16:
        raise ValueError('Box Shell role corners are not sixteen distinct points')
    edges=[];pair_keys={}
    for role in ('outer','inner'):
        for bits in itertools.product((0,1),repeat=3):
            for axis in range(3):
                if bits[axis]:continue
                opposite=list(bits);opposite[axis]=1
                a,b=_key(role,bits),_key(role,opposite);key=role+':'+a.split(':')[1]+'-'+b.split(':')[1]
                pair_keys[frozenset((a,b))]=key
                edges.append(dict(key=key,role=role,axis=axis,vertex_keys=[a,b],start_position_cm=positions[a],
                    end_position_cm=positions[b],direction_cm=_sub(positions[b],positions[a]),
                    mathematical_parameter_domain=[0.,1.],definition='P(t)=start+t*direction for 0<=t<=1; no native parameter interpretation'))
    faces=[]
    for axis in range(3):
        for side in (0,1):
            normal=[0.,0.,0.];normal[axis]=-1. if side==0 else 1.
            if (axis,side) in openings:
                specifications=[('rim',normal,[('outer',True),('inner',False)])]
            else:
                specifications=[('outer',normal,[('outer',True)]),('inner',[-x for x in normal],[('inner',True)])]
            for role,n,loop_roles in specifications:
                loops=[]
                for loop_role,is_outer in loop_roles:
                    wanted=n if is_outer else [-x for x in n]
                    cycle=_oriented(_cycle(loop_role,axis,side),positions,wanted)
                    edge_keys=[pair_keys[frozenset((a,b))] for a,b in zip(cycle,cycle[1:]+cycle[:1])]
                    loops.append(dict(role=loop_role,is_outer=is_outer,vertex_keys=cycle,edge_keys=edge_keys,
                        corner_positions_cm=[positions[k] for k in cycle],mathematical_orientation='Positive relative to chosen material normal' if is_outer else 'Negative relative to chosen material normal'))
                origin=positions[loops[0]['vertex_keys'][0]];constant=_dot(n,origin)
                faces.append(dict(key=role+':'+str(axis)+':'+str(side),role=role,source_axis=axis,source_side=side,
                    outward_material_mathematical_normal=n,plane_constant_cm=constant,
                    carrier_origin_cm=origin,loops=loops,
                    carrier_definition='normal dot X = plane_constant; bounded planar material is outer loop minus any hole',
                    native_FACE_sense=None,native_UV=None))
    # Every semantic EDGE has two opposite uses. This is a complete closed
    # material boundary even when its void touches one or both source cap planes.
    uses={edge['key']:[] for edge in edges}
    for face in faces:
        for loop in face['loops']:
            cycle=loop['vertex_keys']
            for key,a,b in zip(loop['edge_keys'],cycle,cycle[1:]+cycle[:1]):
                uses[key].append(dict(face_key=face['key'],start_vertex_key=a,end_vertex_key=b))
    for key,rows in uses.items():
        if len(rows)!=2 or rows[0]['start_vertex_key']!=rows[1]['end_vertex_key'] or rows[0]['end_vertex_key']!=rows[1]['start_vertex_key']:
            raise ValueError('Derived Box Shell is not a closed consistently oriented material boundary')
    volumes=dict(source=math.prod(_sub(high,low)),outer=math.prod(_sub(oh,ol)),cavity=math.prod(_sub(ih,il)))
    for v in volumes.values():_scalar(v)
    volume=_scalar(volumes['outer']-volumes['cavity'])
    if volume<=TOLERANCE:raise ValueError('Box Shell has no positive finite material volume')
    # Independently sum oriented planar polygon volumes. Hole loops contribute
    # their opposite winding, rather than becoming four guessed rim rectangles.
    origin=[_scalar((a+b)/2) for a,b in zip(low,high)]
    determinant_sum=0.
    for face in faces:
        for loop in face['loops']:
            p=[_sub(positions[k],origin) for k in loop['vertex_keys']]
            for i in (1,2):determinant_sum=_scalar(determinant_sum+_dot(p[0],_cross(p[i],p[i+1])))
    boundary_volume=_scalar(determinant_sum/6)
    if not math.isclose(boundary_volume,volume,rel_tol=1e-9,abs_tol=TOLERANCE):
        raise ValueError('Derived Box Shell boundary integral and offset-box volume disagree')
    return dict(source_bounds_cm=dict(minimum=low,maximum=high),inside_thickness_cm=inside,
        outside_thickness_cm=outside,active_inside_cm=inner,active_outside_cm=outer,
        removed_source_axis_sides=[dict(axis=a,side=s) for a,s in sorted(openings)],
        outer_bounds_cm=dict(minimum=ol,maximum=oh),cavity_bounds_cm=dict(minimum=il,maximum=ih),
        vertices=vertices,segments=edges,planar_boundaries=faces,semantic_edge_uses=uses,
        box_volumes_cm3=volumes,material_volume_cm3=volume,boundary_integral_volume_cm3=boundary_volume,
        volume_residual_cm3=abs(volume-boundary_volume),
        counts=dict(vertices=16,segments=24,planar_faces=len(faces),loops=sum(len(f['loops']) for f in faces),
            connected_boundary_shells=2 if not openings else 1),
        role_key_scope='Constructed outer/inner/rim semantic roles only, not native entity IDs or inferred matches',scope=SCOPE)
