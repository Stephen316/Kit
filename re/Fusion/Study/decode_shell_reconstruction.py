"""Native Sketch/Extrude-derived rectangular Shell material and cache proof.

Source identities precede coordinates. Target geometry is compared as complete
unordered bundles; semantic inner/outer roles are never assigned to ASM IDs by
coordinate matching. Literal paired views carry no chronological meaning.
"""
import copy
import math
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_brep import decode_topology
from decode_one_face_edge_sources import _replay_recipe
from decode_scale_reconstruction import (_prism_identities, _whole_prism_topology,
    _line_geometry, _plane_geometry)
from decode_scale_prism_geometry import derive_scaled_prism
from decode_shell_box_geometry import derive_box_shell
from decode_shell_source_operands import SHELL, qualify_shell_source_operands
from materialize_asm_literal_view import materialize_asm_literal_view

TOLERANCE=1e-8
SCOPE=('Derived native four-Line Sketch/untapered Extrude box and Shell thickness '
       'material with closed, one-face or opposite-face openings. Source FACE '
       'operands are fixed through complete names and reciprocal literal-view '
       'incidence before geometry. Complete initial serialized BODY geometry is '
       'corroborated collectively without coordinate-selected entity identities. '
       'No chronology, current/final/API/persistent identity, native UV or general '
       'Shell algorithm is established; RoundedOffset is a retained control only.')


def _finite(values,label):
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in values):
        raise ValueError('Shell reconstruction nonfinite '+label)


def _near(a,b,label):
    _finite(list(a)+list(b),label)
    if len(a)!=len(b):raise ValueError('Shell reconstruction vector extent differs')
    residual=max((abs(x-y) for x,y in zip(a,b)),default=0.)
    if not math.isfinite(residual) or residual>TOLERANCE:
        raise ValueError('Shell reconstruction '+label+' corroboration differs')
    return residual


def decode_shell_face_operands(recipe):
    """Exact observed 476-byte FACE + four two-FACE/three-FACE EDGE operands."""
    _replay_recipe(recipe)
    raw=bytes.fromhex(recipe['payload_hex'])
    names=recipe['name_table']
    if recipe['payload_kind']!='bounded_face_recipe_data' or len(raw)!=476 or len(names)!=5:
        raise ValueError('Shell reconstruction requires observed 476-byte five-name FACE recipe')
    words=list(struct.unpack('<119i',raw))
    face,secondary,count=words[:3]
    if secondary!=-1 or count!=4 or not 0<=face<5:
        raise ValueError('Shell reconstruction FACE operation prefix differs')
    edges=[];used={face}
    def refs(values):
        if len(values)%2 or any(values[i+1]!=-1 or not 0<=values[i]<5 for i in range(0,len(values),2)):
            raise ValueError('Shell reconstruction FACE reference/sentinel differs')
        result=values[::2]
        if len(set(result))!=len(result):raise ValueError('Shell reconstruction repeated FACE operand')
        used.update(result);return result
    for ordinal in range(4):
        block=words[3+29*ordinal:3+29*(ordinal+1)]
        if block[:3]!=[-1,-1,2] or block[7]!=2 or block[-1]!=-1:
            raise ValueError('Shell reconstruction two-FACE EDGE framing differs')
        adjacent=refs(block[3:7]);vertices=[]
        if face not in adjacent:raise ValueError('Shell reconstruction boundary EDGE omits outer FACE')
        for offset in (8,18):
            vertex=block[offset:offset+10]
            if vertex[:2]!=[-1,3] or vertex[8:]!=[0,0]:
                raise ValueError('Shell reconstruction three-FACE VERTEX framing differs')
            vertex_refs=refs(vertex[2:8])
            if not set(adjacent)<=set(vertex_refs):
                raise ValueError('Shell reconstruction endpoint FACE operands omit EDGE operands')
            vertices.append(dict(face_name_indices=vertex_refs,stored_tail_int32=[0,0]))
        if set(vertices[0]['face_name_indices'])==set(vertices[1]['face_name_indices']):
            raise ValueError('Shell reconstruction endpoint operands repeat')
        edges.append(dict(operand_ordinal=ordinal,face_name_indices=adjacent,
            endpoint_operands=vertices,stored_edge_tail_int32=-1,
            payload_hex=struct.pack('<29i',*block).hex()))
    if used!=set(range(5)) or struct.pack('<119i',*words)!=raw:
        raise ValueError('Shell reconstruction whole operation replay/name coverage differs')
    return dict(face_name_index=face,boundary_edge_operands=edges,
        payload_hex=raw.hex(),payload_length=len(raw),whole_operation_replay_exact=True,
        qualifiers_scope='All sentinels/tails literal; general recipe evaluation and traversal unresolved')


def _ring(loop,nodes,allowed):
    cycle=[];pairs=[];current=loop['first_coedge_index']
    while current not in cycle:
        if current not in allowed or len(cycle)>=4:
            raise ValueError('Shell reconstruction requires complete four-EDGE loops')
        coedge=nodes[current]
        if (coedge['loop_index']!=loop['index']
                or nodes[coedge['next_coedge_index']]['previous_coedge_index']!=current
                or nodes[coedge['previous_coedge_index']]['next_coedge_index']!=current):
            raise ValueError('Shell reconstruction loop reciprocity differs')
        edge=nodes[coedge['edge_index']]
        pair=[edge['start_vertex_index'],edge['end_vertex_index']]
        if coedge['is_reversed']:pair.reverse()
        if pairs and pairs[-1][1]!=pair[0]:raise ValueError('Shell reconstruction loop endpoint continuity differs')
        cycle.append(current);pairs.append(pair);current=coedge['next_coedge_index']
    if current!=cycle[0] or len(cycle)!=4 or pairs[-1][1]!=pairs[0][0] or len({p[0] for p in pairs})!=4:
        raise ValueError('Shell reconstruction loop is not one reciprocal quadrilateral')
    return dict(loop_index=loop['index'],coedge_cycle=cycle,
        edge_indices=[nodes[i]['edge_index'] for i in cycle],vertex_cycle=[p[0] for p in pairs])


def _literal_source(blob,parsed,group):
    view=materialize_asm_literal_view(blob,parsed=parsed,state_slot=0,pointer_side=0)
    aliases=view['literal_pair_aliases'];origins=view['origin_map']
    def mapped(identity,kind,required=True):
        pairs=[r for r in aliases if r['kind']==kind and r['side1_inspection_record_index']==identity]
        if len(pairs)>1:raise ValueError('Shell reconstruction literal alias is ambiguous')
        target=pairs[0]['side0_inspection_record_index'] if pairs else identity
        found=[o for o in origins if o['inspection_record_index']==target and o['kind']==kind]
        if not found and not required:return None
        if len(found)!=1:raise ValueError('Shell reconstruction literal origin correspondence absent or ambiguous')
        return dict(initial_record_index=identity,view_record_index=found[0]['view_record_index'],
            literal_pair=pairs[0] if pairs else None,view_origin=found[0])
    body=mapped(group['asm_body_index'],'body')
    if body['literal_pair'] is None:raise ValueError('Shell reconstruction needs explicit paired source BODY')
    topology=decode_topology(view['view_parsed'])
    if topology['unresolved']:raise ValueError('Shell reconstruction literal view topology unresolved')
    nodes={n['index']:n for n in topology['nodes']}
    graphs=[g for g in topology['body_graphs'] if g['body_index']==body['view_record_index']]
    if len(graphs)!=1:raise ValueError('Shell reconstruction literal source BODY missing')
    graph=graphs[0];_whole_prism_topology(graph,nodes)
    if nodes[graph['body_index']]['stored_entity_id']!=group['binding']['stored_handle']:
        raise ValueError('Shell reconstruction literal BODY stored identifier changes')
    adapted=copy.deepcopy(group);curve_proofs=[]
    for curve in adapted['profile_cache_correspondence']['source_curves']:
        proofs=[mapped(i,'edge',False) for i in sorted({c['edge_record_index'] for c in curve['cached_coedge_candidates']})]
        proofs=[p for p in proofs if p and p['view_record_index'] in graph['edge_indices']]
        edges={p['view_record_index'] for p in proofs}
        if len(edges)!=1:raise ValueError('Shell reconstruction native profile tag lacks unique literal source EDGE')
        edge=next(iter(edges));uses=[nodes[c] for c in graph['coedge_indices'] if nodes[c]['edge_index']==edge]
        curve['cached_coedge_candidates']=[dict(edge_record_index=edge,coedge_record_index=c['index'],
            face_record_index=nodes[c['loop_index']]['face_index']) for c in uses]
        curve_proofs.append(dict(native_line_object_id=curve['native_entity_object_id'],
            native_curve_tag=curve['native_entity_tag'],initial_to_literal_edge_origins=proofs,
            literal_edge_record_index=edge,literal_coedge_record_indices=[c['index'] for c in uses]))
    identities=_prism_identities(adapted,graph,nodes)
    placement=group['source_sketch']['placement']['sketch_to_component_matrix']
    distance=group['extrude_controls']['extent']['side_one']['distance_cm']
    translation=[distance*v for v in group['extrude_direction_component']]
    points={p['point_object_id']:p['position_cm'] for p in group['native_profile_points']}
    vertices=[]
    for point,bottom in sorted(identities['bottom'].items()):
        raw=points[point];base=[sum(placement[4*i+j]*raw[j] for j in range(3))+placement[4*i+3] for i in range(3)]
        for layer,identity in ((0,bottom),(1,identities['opposite'][point])):
            vertices.append(dict(vertex_index=identity,native_sketch_point_object_id=point,layer=layer,
                derived_position_cm=[x+layer*y for x,y in zip(base,translation)]))
    prism=derive_scaled_prism(vertices,identities['edge_vertex_pairs'],identities['face_vertex_cycles'],[0.,0.,0.],[1.,1.,1.])['source_prism']
    positions={v['vertex_index']:v['derived_position_cm'] for v in vertices}
    bounds=prism['axis_aligned_bounds_cm'];axis_faces={}
    for face in identities['face_vertex_cycles']:
        values=[positions[v] for v in face['vertex_cycle']]
        choices=[(axis,side) for axis in range(3) for side,key in ((0,'minimum'),(1,'maximum'))
            if all(abs(p[axis]-bounds[key][axis])<=TOLERANCE for p in values)]
        if len(choices)!=1:raise ValueError('Shell reconstruction native-derived source FACE is not a unique axis side')
        axis_faces[face['face_index']]=dict(axis=choices[0][0],side=choices[0][1])
    if len({(v['axis'],v['side']) for v in axis_faces.values()})!=6:
        raise ValueError('Shell reconstruction source prism is not an axis-aligned complete box')
    lines=[_line_geometry(segment,nodes[segment['edge_index']],nodes) for segment in prism['segments']]
    planes=[_plane_geometry(face,nodes[face['face_index']],nodes) for face in prism['planar_quadrilateral_boundaries']]
    tags=decode_asm_generic_tags(blob,view['view_parsed'],allow_fpm_tracking=True)
    if tags['unresolved']:raise ValueError('Shell reconstruction complete literal generic naming unresolved')
    proof=dict(provenance={k:v for k,v in view.items() if k!='view_parsed'},qualified_body_origin=body,
        qualified_body_view_record_index=graph['body_index'],native_profile_edge_correspondence=curve_proofs,
        identity_provenance=identities,derived_source_prism=prism,
        native_derived_vertices=vertices,source_FACE_axis_sides=[dict(face_index=i,**v) for i,v in axis_faces.items()],
        literal_straight_carrier_corroboration=lines,literal_planar_boundary_corroboration=planes,
        qualified_historical_state=None,source_before_Shell_identity=None,
        scope='Explicit same-ID literal source-box view corroborates native-derived geometry; no chronology')
    return proof,view,topology,graph,nodes,tags,axis_faces


def _removed_face(recipe,blob,view,topology,graph,nodes,tags,axis_faces):
    operands=decode_shell_face_operands(recipe)
    matches=match_recipe_tag_names(recipe,tags,parsed=view['view_parsed'])
    named={}
    for entry in matches['name_entries']:
        candidates=entry['candidates']
        if len(candidates)!=1 or candidates[0]['owner_kind']!='face' or candidates[0]['body_graph_membership']!=[graph['body_index']]:
            raise ValueError('Shell reconstruction complete recipe FACE name is absent, ambiguous or outside source BODY')
        named[entry['name_table_index']]=candidates[0]['owner_record_index']
    if len(set(named.values()))!=5:raise ValueError('Shell reconstruction recipe FACE names alias')
    face=named[operands['face_name_index']];routes=[]
    edge_faces={};vertex_faces={}
    for c in graph['coedge_indices']:
        coedge=nodes[c];f=nodes[coedge['loop_index']]['face_index'];e=nodes[coedge['edge_index']]
        edge_faces.setdefault(e['index'],set()).add(f)
        for vertex in (e['start_vertex_index'],e['end_vertex_index']):vertex_faces.setdefault(vertex,set()).add(f)
    for operand in operands['boundary_edge_operands']:
        faces={named[i] for i in operand['face_name_indices']}
        edges=[e for e,fs in edge_faces.items() if fs==faces]
        if len(edges)!=1:raise ValueError('Shell reconstruction two FACE operands do not fix a unique source EDGE')
        edge=nodes[edges[0]];endpoints=[]
        for vertex in operand['endpoint_operands']:
            faces={named[i] for i in vertex['face_name_indices']}
            found=[i for i,fs in vertex_faces.items() if fs==faces]
            if len(found)!=1:raise ValueError('Shell reconstruction three FACEs do not fix a unique source VERTEX')
            endpoints.append(found[0])
        if len(set(endpoints))!=2 or set(endpoints)!={edge['start_vertex_index'],edge['end_vertex_index']}:
            raise ValueError('Shell reconstruction endpoint operands do not exhaust source EDGE')
        routes.append(dict(operand_ordinal=operand['operand_ordinal'],edge_index=edge['index'],
            literal_endpoint_vertex_indices=endpoints,stored_start_end_vertex_indices=[edge['start_vertex_index'],edge['end_vertex_index']],
            FACE_indices=sorted(edge_faces[edge['index']]),raw_EDGE=edge))
    loops=[_ring(nodes[i],nodes,set(graph['coedge_indices'])) for i in graph['loop_indices'] if nodes[i]['face_index']==face]
    if len(loops)!=1 or {r['edge_index'] for r in routes}!=set(loops[0]['edge_indices']):
        raise ValueError('Shell reconstruction recipe boundary does not exhaust selected source FACE loop')
    return dict(recipe=recipe,operands=operands,complete_name_correspondence=matches,
        selected_literal_FACE_index=face,source_axis_side=axis_faces[face],boundary_incidence=routes,
        selected_source_loop=loops[0],exact_API_handle_identity=None,qualified_historical_state=None,
        scope='Complete literal FACE names and reciprocal source-box incidence; not a chronological removed FACE assertion')


def _geometry_sort_key(value):
    if isinstance(value,(int,float)):return round(value,9)
    return tuple(_geometry_sort_key(x) for x in value)


def _canonical_corner_cycle(points):
    # Rotation and reversal are ignored only for collective geometric equality;
    # all four consecutive segment incidences remain represented.
    cycles=[]
    for sequence in (points,list(reversed(points))):
        cycles.extend(sequence[i:]+sequence[:i] for i in range(len(sequence)))
    return min(cycles,key=_geometry_sort_key)


def _collective_geometry(graph,nodes,derived):
    expected=derived['counts']
    counts={'face_indices':expected['planar_faces'],'shell_indices':expected['connected_boundary_shells'],
        'loop_indices':12,'coedge_indices':48,'edge_indices':24,'vertex_indices':16,'lump_indices':1}
    if not graph['body_transform_is_identity'] or any(len(graph[k])!=n or len(set(graph[k]))!=n for k,n in counts.items()):
        raise ValueError('Shell reconstruction complete target BODY counts/frame differ')
    body=nodes[graph['body_index']];lump=nodes[graph['lump_indices'][0]]
    if body['first_lump_index']!=lump['index'] or body['first_wire_index'] is not None or lump['next_lump_index'] is not None or lump['body_index']!=body['index']:
        raise ValueError('Shell reconstruction target BODY/lump ownership differs')
    for sid in graph['shell_indices']:
        shell=nodes[sid]
        if shell['lump_index']!=lump['index'] or shell['subshell_index'] is not None or shell['first_wire_index'] is not None:
            raise ValueError('Shell reconstruction target shell ownership/wires differ')
    seen=set();current=lump['first_shell_index']
    while current is not None:
        if current not in graph['shell_indices'] or current in seen:
            raise ValueError('Shell reconstruction target shell chain differs')
        seen.add(current);current=nodes[current]['next_shell_index']
    if seen!=set(graph['shell_indices']):raise ValueError('Shell reconstruction target shell chain incomplete')
    for sid in graph['shell_indices']:
        owned={i for i in graph['face_indices'] if nodes[i]['shell_index']==sid}
        seen=set();current=nodes[sid]['first_face_index']
        while current is not None:
            if current not in owned or current in seen:
                raise ValueError('Shell reconstruction target shell FACE chain differs')
            seen.add(current);current=nodes[current]['next_face_index']
        if not owned or seen!=owned:raise ValueError('Shell reconstruction target shell FACE chain incomplete')
    vertex_rows=[];positions={}
    for identity in graph['vertex_indices']:
        vertex=nodes[identity];point=nodes[vertex['point_index']]
        incident=[e for e in graph['edge_indices'] if identity in (nodes[e]['start_vertex_index'],nodes[e]['end_vertex_index'])]
        if point['kind']!='point' or len(incident)!=3 or vertex['first_edge_index'] not in incident:
            raise ValueError('Shell reconstruction target VERTEX head/degree/POINT differs')
        _finite(point['raw_origin'],'target POINT');positions[identity]=point['raw_origin']
        vertex_rows.append(dict(vertex_index=identity,native_VERTEX=vertex,native_POINT=point))
    segments=[]
    for identity in graph['edge_indices']:
        edge=nodes[identity];uses=[nodes[c] for c in graph['coedge_indices'] if nodes[c]['edge_index']==identity]
        if len(uses)!=2 or len({nodes[c['loop_index']]['face_index'] for c in uses})!=2 or edge['first_coedge_index'] not in {c['index'] for c in uses}:
            raise ValueError('Shell reconstruction target EDGE uses/head differ')
        if any(c['partner_index']!=other['index'] for c,other in ((uses[0],uses[1]),(uses[1],uses[0]))):
            raise ValueError('Shell reconstruction target partner is not reciprocal other use')
        segment=dict(edge_index=identity,vertex_indices=[edge['start_vertex_index'],edge['end_vertex_index']],
            start_position_cm=positions[edge['start_vertex_index']],end_position_cm=positions[edge['end_vertex_index']])
        curve=nodes[edge['curve_index']]
        if curve['kind']!='straight-curve':raise ValueError('Shell reconstruction target EDGE requires a straight carrier')
        origin,direction=curve['raw_origin'],curve['direction']
        _finite(origin+direction,'target Line')
        norm=sum(x*x for x in direction)
        if not math.isfinite(norm) or norm<=0:raise ValueError('Shell reconstruction target Line direction degenerates')
        literal=[edge['start_parameter'],edge['end_parameter']]
        _finite(literal,'target EDGE parameters')
        sign=-1. if edge['is_reversed'] else 1.
        evaluations=[]
        for vertex,position,parameter in zip(segment['vertex_indices'],
                (segment['start_position_cm'],segment['end_position_cm']),literal):
            derived_parameter=sum((p-o)*v for p,o,v in zip(position,origin,direction))/norm
            _finite([derived_parameter],'target endpoint carrier parameter')
            reconstructed=[o+derived_parameter*v for o,v in zip(origin,direction)]
            residual=_near(position,reconstructed,'target Line endpoint carrier')
            parameter_residual=_near([derived_parameter],[sign*parameter],'target literal reversed-parameter correspondence')
            evaluations.append(dict(vertex_index=vertex,stored_endpoint_parameter=parameter,
                independently_derived_carrier_parameter=derived_parameter,
                evaluated_raw_position=reconstructed,stored_raw_position=position,
                residual_raw=residual,parameter_residual_raw=parameter_residual))
        segments.append(dict(edge_index=identity,native_EDGE=edge,native_Line=curve,native_endpoint_segment=segment,
            endpoint_evaluations=evaluations,literal_parameter_multiplier=sign,
            native_traversal_semantics=None,
            scope='Straight carrier and typed endpoints; observed literal reversal-conditioned parameter sign, no API traversal convention'))
    faces=[];actual_bundles=[]
    for identity in graph['face_indices']:
        face=nodes[identity];plane=nodes[face['surface_index']]
        if plane['kind']!='plane-surface':raise ValueError('Shell reconstruction target requires typed planar carriers')
        _finite(plane['raw_origin']+plane['normal']+plane['stored_reference_axis'],'target Plane')
        if abs(sum(v*v for v in plane['normal'])-1)>TOLERANCE:raise ValueError('Shell reconstruction target Plane normal is not unit')
        loops=[_ring(nodes[i],nodes,set(graph['coedge_indices'])) for i in graph['loop_indices'] if nodes[i]['face_index']==identity]
        if len(loops) not in (1,2) or face['first_loop_index'] not in {l['loop_index'] for l in loops}:
            raise ValueError('Shell reconstruction target FACE loop ownership differs')
        loop_ids={l['loop_index'] for l in loops};seen=set();current=face['first_loop_index']
        while current is not None:
            if current not in loop_ids or current in seen:raise ValueError('Shell reconstruction target FACE loop chain differs')
            seen.add(current);current=nodes[current]['next_loop_index']
        if seen!=loop_ids:raise ValueError('Shell reconstruction target FACE loop chain incomplete')
        bundles=[]
        for loop in loops:
            corners=[positions[v] for v in loop['vertex_cycle']]
            for point in corners:
                residual=sum(n*(x-o) for n,x,o in zip(plane['normal'],point,plane['raw_origin']))
                if not math.isfinite(residual) or abs(residual)>TOLERANCE:raise ValueError('Shell reconstruction target boundary leaves native Plane')
            bundles.append(_canonical_corner_cycle([tuple(p) for p in corners]))
        actual_bundles.append(sorted(bundles,key=_geometry_sort_key))
        faces.append(dict(face_index=identity,native_FACE=face,native_Plane=plane,loops=loops,
            loop_corner_positions_cm=[[positions[v] for v in l['vertex_cycle']] for l in loops]))
    def compare(a,b,label):
        def recursive(left,right):
            if isinstance(left,(int,float)) and isinstance(right,(int,float)):
                return _near([left],[right],label)
            if not isinstance(left,(list,tuple)) or not isinstance(right,(list,tuple)) or len(left)!=len(right):
                raise ValueError('Shell reconstruction '+label+' nested framing differs')
            return max((recursive(x,y) for x,y in zip(left,right)),default=0.)
        return recursive(sorted(a,key=_geometry_sort_key),sorted(b,key=_geometry_sort_key))
    vertex_error=compare(list(positions.values()),[v['position_cm'] for v in derived['vertices']],'complete unordered POINT bundle')
    segment_error=compare([sorted((r['native_endpoint_segment']['start_position_cm'],r['native_endpoint_segment']['end_position_cm']),key=_geometry_sort_key) for r in segments],
        [sorted((e['start_position_cm'],e['end_position_cm']),key=_geometry_sort_key) for e in derived['segments']],'complete unordered straight segment bundle')
    face_error=compare(actual_bundles,[sorted((_canonical_corner_cycle([tuple(p) for p in loop['corner_positions_cm']]) for loop in f['loops']),key=_geometry_sort_key) for f in derived['planar_boundaries']],
        'complete unordered planar FACE loop bundle')
    return dict(native_vertices=vertex_rows,native_straight_segments=segments,native_planar_boundaries=faces,
        counts=dict(vertices=16,edges=24,coedges=48,loops=12,faces=len(faces),shells=len(graph['shell_indices'])),
        collective_residuals_raw=dict(vertices=vertex_error,segments=segment_error,planar_loop_bundles=face_error),
        semantic_role_to_native_entity_mapping=None,
        scope='Complete unordered geometry bundles after native BODY/source identity; coordinate sorting is corroboration only and assigns no ENTITY identity')


def _group_selections(source,group):
    indices=group['selected_input_indices']
    if not indices or len(set(indices))!=len(indices):
        raise ValueError('Shell reconstruction source group input indices absent or repeated')
    selected=[source['selected_inputs'][i] for i in indices]
    kinds=[s['kind'] for s in selected]
    if any(k not in ('Body','Face') for k in kinds):
        raise ValueError('Shell reconstruction source input kind unsupported')
    if kinds.count('Body')>1 or 'Body' in kinds and 'Face' in kinds:
        raise ValueError('Shell reconstruction one BODY cannot mix whole-Body and Face operands or repeat whole-Body operands')
    return list(zip(indices,selected))


def decode_shell_reconstruction(data,records,features,member,members,body_blob_bindings,body_selections=None):
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    candidates=[f for f in features if f.get('class_guid')==SHELL]
    if not candidates:return result
    joined=None;cache={}
    for feature in candidates:
        try:
            source=qualify_shell_source_operands(data,records,features,member,members,body_blob_bindings,feature)
            if source is None:raise ValueError('Shell reconstruction native source qualification absent')
            if joined is None:
                native_bindings=dict(decoded=[dict(mapping_record_object_id=m['mapping_record_object_id'],
                    owner_object_id=m['owner_object_id'],history_blob_member=m['history_blob_member'],body_count=m['body_count'],
                    bindings=[dict(stored_handle=b['stored_handle'],native_body_object_id=b['native_body_object_id'])
                        for b in m['bindings']]) for m in body_blob_bindings.get('decoded',[])])
                joined=decode_body_asm_identifiers(data,records,member,members,native_bindings)
            groups=[]
            for group in source['source_groups']:
                found=[(m,b) for m in joined['decoded'] for b in m['bindings'] if b['native_body_object_id']==group['native_body_object_id']]
                if len(found)!=1:raise ValueError('Shell reconstruction source BODY mapping ambiguous')
                mapping,binding=found[0]
                if binding!=group['binding'] or mapping['history_blob_member']!=group['history_blob_member']:
                    raise ValueError('Shell reconstruction source mapping revalidation differs')
                name=group['history_blob_member'];blob=members[name]
                if name not in cache:
                    parsed=inspect_asm(blob);topology=decode_topology(parsed)
                    if topology['unresolved']:raise ValueError('Shell reconstruction serialized topology unresolved')
                    cache[name]=(parsed,topology)
                parsed,topology=cache[name];nodes={n['index']:n for n in topology['nodes']}
                graphs=[g for g in topology['body_graphs'] if g['body_index']==group['asm_body_index']]
                if len(graphs)!=1:raise ValueError('Shell reconstruction mapped cache BODY absent')
                proof,view,vt,vg,vn,tags,axes=_literal_source(blob,parsed,group)
                removed=[]
                for index,selection in _group_selections(source,group):
                    if selection.get('counted_recipe'):
                        row=_removed_face(selection['counted_recipe'],blob,view,vt,vg,vn,tags,axes)
                        row['selected_input_index']=index;removed.append(row)
                derived=derive_box_shell(proof['derived_source_prism']['axis_aligned_bounds_cm'],
                    source['settings']['inside_thickness_cm'],source['settings']['outside_thickness_cm'],
                    [r['source_axis_side'] for r in removed])
                corroboration=_collective_geometry(graphs[0],nodes,derived)
                groups.append(dict(source_native_body_object_id=group['native_body_object_id'],
                    source_feature_object_id=group['source_feature_object_id'],history_blob_member=name,
                    asm_body_index=group['asm_body_index'],binding=binding,literal_source_prism=proof,
                    removed_face_operands=removed,derived_shell=derived,
                    collective_cache_geometry_corroboration=corroboration,
                    Shell_owned_result_anchor=None,qualified_historical_state=None,
                    exact_API_handle_identity=None,current_or_final_geometry_identity=None))
            result['decoded'].append(dict(feature_object_id=feature['object_id'],native_source_provenance=source,
                source_groups=groups,source_group_count=len(groups),scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,struct.error,OverflowError) as error:
            result['unresolved'].append(dict(feature_object_id=feature['object_id'],reason=str(error)))
    return result
