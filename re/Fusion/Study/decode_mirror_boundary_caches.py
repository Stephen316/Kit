"""Bounded Mirror planar/straight boundary correspondence and parameter proofs.

Every FACE/EDGE/COEDGE/LOOP identity is fixed by the freshly qualified native
BODY/name/vertex correspondence before line or plane arithmetic. Mathematical
plane coordinates are explicit U/reference and V=N-cross-U choices, not native
UV or API parameter conventions. Pointer heads and literal flags remain facts.
"""
import math
import struct

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_circular_feature_caches import _face_names
from decode_mirror_cache_reflections import decode_mirror_cache_reflections

SCOPE=('Observed initial Mirror six-plane/eight-vertex/twelve-straight-edge BODY boundary '
       'correspondence, reciprocal quad-loop/coedge maps and full line/mathematical-plane '
       'coefficient transport; no native/API UV convention, blanket pointer isomorphism, '
       'current/history placement, arbitrary BRep reconstruction or regeneration')
TOLERANCE=1e-9


def _vector(value):
    if (not isinstance(value,(list,tuple)) or len(value)!=3
            or any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) for v in value)):
        raise ValueError('Mirror boundary requires finite stored/derived three-vectors')
    return list(value)


def _scalar(value):
    if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value):
        raise ValueError('Mirror boundary scalar/parameter is not finite')
    return value


def _dot(left,right):
    return _scalar(sum(a*b for a,b in zip(left,right)))


def _cross(a,b):
    return _vector([a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]])


def _distance(a,b):
    value=math.dist(_vector(a),_vector(b))
    if not math.isfinite(value):raise ValueError('Mirror boundary derived residual is not finite')
    return value


def _linear_combination(a,x,b,y):
    return _vector([a*p+b*q for p,q in zip(x,y)])


def _frame(surface):
    if surface['kind']!='plane-surface':
        raise ValueError('Mirror boundary FACE surface is not an explicit typed plane')
    origin=_vector(surface['raw_origin']);normal=_vector(surface['normal']);u=_vector(surface['stored_reference_axis'])
    for axis in (normal,u):
        length=math.hypot(*axis)
        if not math.isfinite(length) or not math.isclose(length,1.,rel_tol=0.,abs_tol=TOLERANCE):
            raise ValueError('Mirror boundary mathematical plane frame requires observed unit stored N/U')
    if abs(_dot(normal,u))>TOLERANCE:
        raise ValueError('Mirror boundary stored plane N/U are not orthogonal')
    v=_cross(normal,u)
    if not math.isclose(math.hypot(*v),1.,rel_tol=0.,abs_tol=TOLERANCE):
        raise ValueError('Mirror boundary derived mathematical plane V is not unit')
    for interval in (surface['u_interval'],surface['v_interval']):
        if len(interval)!=2:raise ValueError('Mirror boundary stored plane interval extent differs')
        for bound in interval:
            if bound is not None:_scalar(bound)
    return dict(origin=origin,U=u,V=v,N=normal,
        definition='Mathematical coordinates P(u,v)=origin+u*stored_reference_axis+v*(N cross stored_reference_axis); native/API UV mapping unresolved')


def _plane_transport(source,target,point,vector):
    sf,tf=_frame(source),_frame(target)
    ru,rv=vector(sf['U']),vector(sf['V']);ro=point(sf['origin'])
    shift=_vector([a-b for a,b in zip(ro,tf['origin'])])
    matrix=[[_dot(ru,tf['U']),_dot(rv,tf['U'])],[_dot(ru,tf['V']),_dot(rv,tf['V'])]]
    offset=[_dot(shift,tf['U']),_dot(shift,tf['V'])]
    cu=_linear_combination(matrix[0][0],tf['U'],matrix[1][0],tf['V'])
    cv=_linear_combination(matrix[0][1],tf['U'],matrix[1][1],tf['V'])
    const=_vector([o+x for o,x in zip(tf['origin'],_linear_combination(offset[0],tf['U'],offset[1],tf['V']))])
    residuals=dict(U_coefficient=_distance(ru,cu),V_coefficient=_distance(rv,cv),origin_coefficient=_distance(ro,const))
    determinant=_scalar(matrix[0][0]*matrix[1][1]-matrix[0][1]*matrix[1][0])
    if max(residuals.values())>TOLERANCE or not math.isclose(abs(determinant),1.,rel_tol=0.,abs_tol=TOLERANCE):
        raise ValueError('Mirror boundary whole mathematical plane coefficients disagree')
    return dict(source_frame=sf,target_frame=tf,matrix_2x2=matrix,offset_2d=offset,
        determinant_2d=determinant,coefficient_residuals_raw=residuals,
        maximum_coefficient_residual_raw=max(residuals.values()),
        reflected_source_normal_dot_target_normal=_dot(vector(sf['N']),tf['N']),
        raw_source_u_interval=source['u_interval'],raw_source_v_interval=source['v_interval'],
        raw_target_u_interval=target['u_interval'],raw_target_v_interval=target['v_interval'],
        stored_source_is_v_reversed=source['is_v_reversed'],stored_target_is_v_reversed=target['is_v_reversed'],
        stored_v_flags_differ=source['is_v_reversed']!=target['is_v_reversed'],
        scope='Full affine equality of the two explicitly defined mathematical planes for all real u/v; stored plane flags are retained without native/API UV interpretation')


def _plane_boundary_point(source,target,transport):
    sf,tf=transport['source_frame'],transport['target_frame']
    source,target=_vector(source),_vector(target)
    sd=_vector([p-o for p,o in zip(source,sf['origin'])]);td=_vector([p-o for p,o in zip(target,tf['origin'])])
    suv=[_dot(sd,sf['U']),_dot(sd,sf['V'])];tuv=[_dot(td,tf['U']),_dot(td,tf['V'])]
    def evaluate(frame,uv):
        return _vector([o+x for o,x in zip(frame['origin'],_linear_combination(uv[0],frame['U'],uv[1],frame['V']))])
    source_evaluated=evaluate(sf,suv);target_evaluated=evaluate(tf,tuv)
    a,b=transport['matrix_2x2'],transport['offset_2d']
    mapped=[_scalar(sum(x*y for x,y in zip(r,suv))+v) for r,v in zip(a,b)]
    mapped_evaluated=evaluate(tf,mapped)
    residuals=dict(source_plane_reconstruction=_distance(source_evaluated,source),
        target_plane_reconstruction=_distance(target_evaluated,target),
        transported_coordinate=_scalar(math.dist(mapped,tuv)),transported_target_point=_distance(mapped_evaluated,target))
    if max(residuals.values())>TOLERANCE:
        raise ValueError('Mirror boundary typed FACE vertex points disagree with stored mathematical plane/transport')
    return dict(source_raw_position=source,target_raw_position=target,
        source_mathematical_coordinates=suv,target_mathematical_coordinates=tuv,
        transported_source_mathematical_coordinates=mapped,
        source_reconstructed_raw_position=source_evaluated,target_reconstructed_raw_position=target_evaluated,
        transported_target_evaluation_raw_position=mapped_evaluated,residuals_raw=residuals,
        maximum_residual_raw=max(residuals.values()),
        scope='Identity-fixed incident FACE vertices projected/evaluated in the explicitly chosen mathematical frames; no native/API UV convention')


def _line_transport(source_edge,target_edge,source_curve,target_curve,source_points,target_points,
                    endpoint_order,point,vector):
    if source_curve['kind']!='straight-curve' or target_curve['kind']!='straight-curve':
        raise ValueError('Mirror boundary only captured typed straight-curve EDGE geometry is supported')
    so,to=_vector(source_curve['raw_origin']),_vector(target_curve['raw_origin'])
    sd,td=_vector(source_curve['direction']),_vector(target_curve['direction'])
    for direction in (sd,td):
        length=math.hypot(*direction)
        if not math.isfinite(length) or length<=0:
            raise ValueError('Mirror boundary line direction is not finite and nondegenerate')
    ro,rd=point(so),vector(sd);difference=_vector([x-y for x,y in zip(ro,to)])
    pivot=max(range(3),key=lambda i:abs(td[i]))
    a=_scalar(rd[pivot]/td[pivot]);b=_scalar(difference[pivot]/td[pivot])
    if a==0:raise ValueError('Mirror boundary affine line parameter scale is degenerate')
    expected_direction=_vector([a*v for v in td]);expected_origin=_vector([p+b*v for p,v in zip(to,td)])
    direction_error=_distance(rd,expected_direction);origin_error=_distance(ro,expected_origin)
    if max(direction_error,origin_error)>TOLERANCE:
        raise ValueError('Mirror boundary full reflected Line origin/direction coefficients disagree')
    source_bounds=[_scalar(source_edge[k]) for k in ('start_parameter','end_parameter')]
    target_bounds=[_scalar(target_edge[k]) for k in ('start_parameter','end_parameter')]
    if source_bounds[0]==source_bounds[1] or target_bounds[0]==target_bounds[1]:
        raise ValueError('Mirror boundary finite EDGE parameter interval is degenerate')
    mapped_bounds=[_scalar(a*t+b) for t in source_bounds]
    matching_bounds=target_bounds if endpoint_order=='PreservedStoredEndpointOrder' else list(reversed(target_bounds))
    bound_errors=[_scalar(abs(x-y)) for x,y in zip(mapped_bounds,matching_bounds)]
    if max(bound_errors)>TOLERANCE:
        raise ValueError('Mirror boundary affine parameters disagree with identity-fixed target EDGE endpoints')
    evaluations=[]
    for label,origin,direction,bounds,points in (
            ('source',so,sd,source_bounds,source_points),('target',to,td,target_bounds,target_points)):
        for which,t,stored in zip(('start','end'),bounds,points):
            evaluated=_vector([o+t*d for o,d in zip(origin,direction)])
            error=_distance(evaluated,stored)
            if error>TOLERANCE:
                raise ValueError('Mirror boundary native EDGE finite parameter does not evaluate to its typed endpoint')
            evaluations.append(dict(side=label,endpoint=which,parameter=t,evaluated_raw_position=evaluated,
                stored_raw_position=stored,residual_raw=error))
    for curve in (source_curve,target_curve):
        if len(curve['parameter_interval'])!=2:
            raise ValueError('Mirror boundary raw curve interval extent differs')
        for t in curve['parameter_interval']:
            if t is not None:_scalar(t)
    affine=dict(scale=a,offset=b,source_curve_parameter='t',target_curve_parameter='q=a*t+b',
        reflected_source_direction=rd,reflected_source_origin=ro,
        target_direction_coefficient=expected_direction,target_origin_coefficient=expected_origin,
        direction_coefficient_residual_raw=direction_error,origin_coefficient_residual_raw=origin_error,
        maximum_coefficient_residual_raw=max(direction_error,origin_error),
        scope='Full equality of reflected source/target infinite Line coefficients; no fitting, native EDGE/coedge flag sign or API parameter convention applied')
    domain=dict(source_literal_EDGE_parameters=source_bounds,target_literal_EDGE_parameters=target_bounds,
        source_EDGE_parameters_in_target_curve=mapped_bounds,target_parameters_for_mapped_source_vertices=matching_bounds,
        parameter_endpoint_residuals=bound_errors,native_endpoint_evaluations=evaluations,
        raw_source_curve_interval=source_curve['parameter_interval'],raw_target_curve_interval=target_curve['parameter_interval'],
        scope='Finite EDGE endpoint parameters/evaluations are qualified independently from the preserved raw curve intervals')
    return affine,domain,max(direction_error,origin_error,*bound_errors,*(e['residual_raw'] for e in evaluations))


def _boundary_copy(copy,row,blob,parsed,topology):
    nodes={n['index']:n for n in topology['nodes']};graphs={g['body_index']:g for g in topology['body_graphs']}
    source_body,target_body=copy['source_body_binding']['asm_body_index'],copy['result_body_binding']['asm_body_index']
    sg,tg=graphs[source_body],graphs[target_body]
    for graph in (sg,tg):
        if (not graph['body_transform_is_identity'] or graph['counts']!={'lump':1,'shell':1,'face':6,'loop':6,'coedge':24,'edge':12,'vertex':8}
                or not graph['all_coedges_have_partners']):
            raise ValueError('Mirror boundary requires complete identity BODY six-face/eight-vertex/twelve-edge quad topology')
    sn=_face_names(blob,parsed,sg)['names'];tn=_face_names(blob,parsed,tg)['names']
    source_components=tuple(copy['stored_source_naming_prefix']);target_components=tuple(copy['stored_result_face_naming_components'])
    if ({n['components'] for n in sn.values()}!={source_components}
            or {n['components'] for n in tn.values()}!={target_components}):
        raise ValueError('Mirror boundary complete inherited naming components differ from fresh BODY correspondence')
    face_map={}
    for identity,name in sn.items():
        candidates=[i for i,n in tn.items() if n['name_key']==name['name_key'] and n['components']==target_components]
        if len(candidates)!=1:raise ValueError('Mirror boundary full inherited FACE name is missing or ambiguous')
        face_map[identity]=candidates[0]
    if len(set(face_map.values()))!=6:raise ValueError('Mirror boundary FACE name map is not a bijection')
    vertex_map={p['source']['vertex_index']:p['target']['vertex_index'] for p in copy['vertex_correspondence']}
    if set(vertex_map)!=set(sg['vertex_indices']) or set(vertex_map.values())!=set(tg['vertex_indices']) or len(vertex_map)!=8:
        raise ValueError('Mirror boundary prerequisite typed vertex map is not complete/bijective')

    def incident(graph,edge_id):
        cs=[nodes[c] for c in graph['coedge_indices'] if nodes[c]['edge_index']==edge_id]
        if (len(cs)!=2 or nodes[cs[0]['partner_index']]['index']!=cs[1]['index']
                or nodes[cs[1]['partner_index']]['index']!=cs[0]['index']):
            raise ValueError('Mirror boundary EDGE lacks exactly two reciprocal partner coedges')
        faces=[nodes[c['loop_index']]['face_index'] for c in cs]
        if len(set(faces))!=2:raise ValueError('Mirror boundary EDGE incident FACE identities are not distinct')
        return faces

    edge_map={};edge_faces={};endpoint_orders={}
    for identity in sg['edge_indices']:
        edge=nodes[identity];mapped=[vertex_map[edge[k]] for k in ('start_vertex_index','end_vertex_index')]
        faces=incident(sg,identity);expected={face_map[f] for f in faces}
        candidates=[i for i in tg['edge_indices'] if {nodes[i]['start_vertex_index'],nodes[i]['end_vertex_index']}==set(mapped)
            and set(incident(tg,i))==expected]
        if len(candidates)!=1:raise ValueError('Mirror boundary endpoint/full incident FACE EDGE match is missing or ambiguous')
        target=candidates[0];edge_map[identity]=target;edge_faces[identity]=faces
        actual=[nodes[target][k] for k in ('start_vertex_index','end_vertex_index')]
        if actual==mapped:endpoint_orders[identity]='PreservedStoredEndpointOrder'
        elif actual==list(reversed(mapped)):endpoint_orders[identity]='ReversedStoredEndpointOrder'
        else:raise ValueError('Mirror boundary target EDGE endpoint order does not cover mapped vertices')
    if set(edge_map.values())!=set(tg['edge_indices']):raise ValueError('Mirror boundary EDGE map is not a bijection')
    coedge_map={}
    for identity in sg['coedge_indices']:
        coedge=nodes[identity];face=nodes[coedge['loop_index']]['face_index']
        candidates=[i for i in tg['coedge_indices'] if nodes[i]['edge_index']==edge_map[coedge['edge_index']]
            and nodes[nodes[i]['loop_index']]['face_index']==face_map[face]]
        if len(candidates)!=1:raise ValueError('Mirror boundary owned FACE/EDGE COEDGE match is missing or ambiguous')
        coedge_map[identity]=candidates[0]
    if set(coedge_map.values())!=set(tg['coedge_indices']):raise ValueError('Mirror boundary COEDGE map is not a bijection')
    loop_map={};source_cycles={};target_cycles={}

    def cycle(graph,loop_id):
        loop=nodes[loop_id];expected={c for c in graph['coedge_indices'] if nodes[c]['loop_index']==loop_id}
        if len(expected)!=4 or loop['first_coedge_index'] not in expected:
            raise ValueError('Mirror boundary named FACE does not own one complete four-coedge LOOP')
        visited=[];current=loop['first_coedge_index']
        while current not in visited:
            if current not in expected:raise ValueError('Mirror boundary LOOP cycle leaves its typed owned coedges')
            visited.append(current);c=nodes[current]
            if (nodes[c['next_coedge_index']]['previous_coedge_index']!=current
                    or nodes[c['previous_coedge_index']]['next_coedge_index']!=current):
                raise ValueError('Mirror boundary LOOP next/previous links are not reciprocal')
            current=c['next_coedge_index']
        if current!=visited[0] or set(visited)!=expected:
            raise ValueError('Mirror boundary LOOP ring is incomplete or closes at a different head')
        return visited

    for source_face,target_face in face_map.items():
        sl=[i for i in sg['loop_indices'] if nodes[i]['face_index']==source_face]
        tl=[i for i in tg['loop_indices'] if nodes[i]['face_index']==target_face]
        if (len(sl)!=1 or len(tl)!=1 or nodes[source_face]['first_loop_index']!=sl[0]
                or nodes[target_face]['first_loop_index']!=tl[0]):
            raise ValueError('Mirror boundary requires one reciprocal quad LOOP per matched FACE')
        source_cycles[sl[0]]=cycle(sg,sl[0]);target_cycles[tl[0]]=cycle(tg,tl[0])
        mapped={coedge_map[c] for c in source_cycles[sl[0]]}
        if mapped!=set(target_cycles[tl[0]]):raise ValueError('Mirror boundary LOOP owned coedge-set correspondence differs')
        loop_map[sl[0]]=tl[0]
    if set(loop_map.values())!=set(tg['loop_indices']):raise ValueError('Mirror boundary LOOP map is not bijective')
    face_vertices={}
    for source_face,target_face in face_map.items():
        source_loop=nodes[source_face]['first_loop_index'];target_loop=nodes[target_face]['first_loop_index']
        source_edges={nodes[c]['edge_index'] for c in source_cycles[source_loop]}
        target_edges={nodes[c]['edge_index'] for c in target_cycles[target_loop]}
        sv={nodes[e][k] for e in source_edges for k in ('start_vertex_index','end_vertex_index')}
        tv={nodes[e][k] for e in target_edges for k in ('start_vertex_index','end_vertex_index')}
        if len(source_edges)!=4 or len(target_edges)!=4 or len(sv)!=4 or {vertex_map[v] for v in sv}!=tv:
            raise ValueError('Mirror boundary quad FACE does not own four distinct matched endpoint vertices')
        face_vertices[source_face]=sorted(sv)
    # Every topological identity above is fixed before frame/coordinate arithmetic.
    coedge_pairs=[]
    for identity,target in coedge_map.items():
        sc,tc=nodes[identity],nodes[target]
        if (coedge_map[sc['partner_index']]!=tc['partner_index']
                or coedge_map[sc['next_coedge_index']]!=tc['previous_coedge_index']
                or coedge_map[sc['previous_coedge_index']]!=tc['next_coedge_index']):
            raise ValueError('Mirror boundary partner map or observed reversed stored cycle differs')
        coedge_pairs.append(dict(source_coedge_index=identity,target_coedge_index=target,source_coedge=sc,target_coedge=tc,
            mapped_source_next=coedge_map[sc['next_coedge_index']],mapped_source_previous=coedge_map[sc['previous_coedge_index']],
            mapped_source_partner=coedge_map[sc['partner_index']],next_maps_to_target_previous=True,
            previous_maps_to_target_next=True,partner_maps_to_target_partner=True,
            stored_reversal_flags_differ=sc['is_reversed']!=tc['is_reversed'],
            scope='Literal reciprocal topology/flag observation only; no UV or curve-parameter sign inference'))
    loop_pairs=[]
    for identity,target in loop_map.items():
        mapped=[coedge_map[c] for c in source_cycles[identity]];target_cycle=target_cycles[target]
        reverse=list(reversed(mapped))
        offsets=[i for i in range(4) if reverse[i:]+reverse[:i]==target_cycle]
        if len(offsets)!=1:raise ValueError('Mirror boundary reversed LOOP cycle has no unique rotation correspondence')
        loop_pairs.append(dict(source_loop_index=identity,target_loop_index=target,source_loop=nodes[identity],target_loop=nodes[target],
            source_stored_cycle=source_cycles[identity],target_stored_cycle=target_cycle,mapped_source_cycle=mapped,
            reversed_cycle=True,reverse_cycle_rotation_offset=offsets[0],
            mapped_source_first_coedge=coedge_map[nodes[identity]['first_coedge_index']],
            target_first_coedge=nodes[target]['first_coedge_index']))
    edge_heads=[];vertex_heads=[]
    for identity,target in edge_map.items():
        sh,th=nodes[identity]['first_coedge_index'],nodes[target]['first_coedge_index']
        if sh not in coedge_map or nodes[sh]['edge_index']!=identity or nodes[th]['edge_index']!=target:
            raise ValueError('Mirror boundary EDGE first-coedge is not an owned incident coedge')
        mapped=coedge_map[sh]
        relation='MappedSameCoedge' if th==mapped else 'MappedPartnerCoedge' if th==nodes[mapped]['partner_index'] else None
        if relation is None:raise ValueError('Mirror boundary EDGE head is neither matched incident coedge')
        edge_heads.append(dict(source_edge_index=identity,target_edge_index=target,source_first_coedge=sh,
            mapped_source_first_coedge=mapped,target_first_coedge=th,observation=relation))
    for identity,target in vertex_map.items():
        sh,th=nodes[identity]['first_edge_index'],nodes[target]['first_edge_index']
        if (sh not in edge_map or identity not in (nodes[sh]['start_vertex_index'],nodes[sh]['end_vertex_index'])
                or th not in tg['edge_indices'] or target not in (nodes[th]['start_vertex_index'],nodes[th]['end_vertex_index'])):
            raise ValueError('Mirror boundary VERTEX first-edge does not reference an incident owned EDGE')
        mapped=edge_map[sh]
        vertex_heads.append(dict(source_vertex_index=identity,target_vertex_index=target,source_first_edge=sh,
            mapped_source_first_edge=mapped,target_first_edge=th,
            observation='MappedSameEdge' if th==mapped else 'DifferentIncidentEdge'))
    matrix=row['computed_householder_matrix']
    if len(matrix)!=16 or any(not math.isfinite(v) for v in matrix):raise ValueError('Mirror boundary prerequisite matrix is not finite')
    rotation=[matrix[4*i:4*i+3] for i in range(3)];translation=[matrix[4*i+3] for i in range(3)]
    def vector(p):return _vector([_dot(r,_vector(p)) for r in rotation])
    def point(p):return _vector([v+t for v,t in zip(vector(p),translation)])
    face_pairs=[];edge_pairs=[];maximum=0.
    for identity,target in face_map.items():
        sf,tf=nodes[identity],nodes[target];ss,ts=nodes[sf['surface_index']],nodes[tf['surface_index']]
        transport=_plane_transport(ss,ts,point,vector);maximum=max(maximum,transport['maximum_coefficient_residual_raw'])
        boundary=[]
        for vertex in face_vertices[identity]:
            target_vertex=vertex_map[vertex]
            source_point=nodes[vertex]['point_index'];target_point=nodes[target_vertex]['point_index']
            if nodes[source_point]['kind']!='point' or nodes[target_point]['kind']!='point':
                raise ValueError('Mirror boundary incident FACE vertices lack typed point geometry')
            evidence=_plane_boundary_point(nodes[source_point]['raw_origin'],nodes[target_point]['raw_origin'],transport)
            maximum=max(maximum,evidence['maximum_residual_raw'])
            boundary.append(dict(source_vertex_index=vertex,target_vertex_index=target_vertex,
                source_point_index=source_point,target_point_index=target_point,**evidence))
        face_pairs.append(dict(source_face_index=identity,target_face_index=target,name_key=list(sn[identity]['name_key']),
            source_components=list(source_components),target_components=list(target_components),source_face=sf,target_face=tf,
            source_surface=ss,target_surface=ts,stored_FACE_flags_equal=sf['is_reversed']==tf['is_reversed'],
            mathematical_plane_transport=transport,boundary_point_correspondence=boundary,
            maximum_boundary_point_residual_raw=max(p['maximum_residual_raw'] for p in boundary)))
    for identity,target in edge_map.items():
        se,te=nodes[identity],nodes[target];sc,tc=nodes[se['curve_index']],nodes[te['curve_index']]
        sp=[_vector(nodes[nodes[se[k]]['point_index']]['raw_origin']) for k in ('start_vertex_index','end_vertex_index')]
        tp=[_vector(nodes[nodes[te[k]]['point_index']]['raw_origin']) for k in ('start_vertex_index','end_vertex_index')]
        affine,domain,residual=_line_transport(se,te,sc,tc,sp,tp,endpoint_orders[identity],point,vector)
        maximum=max(maximum,residual)
        edge_pairs.append(dict(source_edge_index=identity,target_edge_index=target,source_edge=se,target_edge=te,
            source_curve=sc,target_curve=tc,mapped_endpoint_vertex_indices=[vertex_map[se[k]] for k in ('start_vertex_index','end_vertex_index')],
            stored_endpoint_order=endpoint_orders[identity],
            incident_face_name_keys=[list(sn[f]['name_key']) for f in sorted(edge_faces[identity])],
            incident_complete_FACE_pairs=[dict(source_face_index=f,target_face_index=face_map[f],
                name_key=list(sn[f]['name_key']),source_components=list(source_components),target_components=list(target_components))
                for f in sorted(edge_faces[identity])],
            stored_EDGE_flags_equal=se['is_reversed']==te['is_reversed'],affine_parameter_transport=affine,domain_evidence=domain))
    return dict(source_native_body_object_id=copy['source_native_body_object_id'],result_native_body_object_id=copy['result_native_body_object_id'],
        source_body_binding=copy['source_body_binding'],result_body_binding=copy['result_body_binding'],
        face_pairs=face_pairs,edge_pairs=edge_pairs,coedge_pairs=coedge_pairs,loop_pairs=loop_pairs,
        head_observations=dict(edge_first_coedge=edge_heads,vertex_first_edge=vertex_heads,
            scope='Stored incident head choices retained as observations; no blanket pointer isomorphism required'),
        counts=dict(face_pairs=len(face_pairs),edge_pairs=len(edge_pairs),coedge_pairs=len(coedge_pairs),loop_pairs=len(loop_pairs),
            incident_FACE_vertex_pairs=4*len(face_pairs),native_endpoint_evaluations=4*len(edge_pairs),transported_parameter_endpoints=2*len(edge_pairs)),
        complete_topology_identity_bijections=True,maximum_residual_raw=maximum,scope=SCOPE)


def decode_mirror_boundary_caches(data,records,features,member,members,body_blob_bindings):
    """Fresh native/name/vertex reflection prerequisite, then separate boundaries."""
    prerequisite=decode_mirror_cache_reflections(data,records,features,member,members,body_blob_bindings)
    result=dict(decoded=[],unresolved=[dict(feature_object_id=r['feature_object_id'],
        reason='Mirror boundary prerequisite unresolved: '+r['reason']) for r in prerequisite['unresolved']],scope=SCOPE)
    cached={}
    for row in prerequisite['decoded']:
        try:
            member_name=row['history_blob_member']
            if member_name not in cached:
                blob=members[member_name];parsed=inspect_asm(blob);topology=decode_topology(parsed)
                if topology['unresolved']:raise ValueError('Mirror boundary initial topology has unresolved fields')
                cached[member_name]=blob,parsed,topology
            blob,parsed,topology=cached[member_name]
            copies=[_boundary_copy(c,row,blob,parsed,topology) for c in row['cache_body_copies']]
            keys=('face_pairs','edge_pairs','coedge_pairs','loop_pairs','incident_FACE_vertex_pairs','native_endpoint_evaluations','transported_parameter_endpoints')
            result['decoded'].append(dict(feature_object_id=row['feature_object_id'],history_blob_member=member_name,
                mapping_record_object_id=row['mapping_record_object_id'],source_native_body_object_ids=row['source_native_body_object_ids'],
                owned_result_anchor_object_ids=row['owned_result_anchor_object_ids'],computed_householder_matrix=row['computed_householder_matrix'],
                body_boundary_copies=copies,counts={k:sum(c['counts'][k] for c in copies) for k in keys},
                maximum_residual_raw=max(c['maximum_residual_raw'] for c in copies),
                topology_identity_source='Fresh native Mirror source/result/full-name/typed-vertex prerequisite followed by complete FACE/EDGE/COEDGE/LOOP bijections before boundary arithmetic',
                scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
            result['unresolved'].append(dict(feature_object_id=row['feature_object_id'],reason=str(error)))
    return result
