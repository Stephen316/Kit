"""Native selected portions -> straight solid, with identity-first bounded cache proof.

Coordinates never select native entities. Complete native tuples fix base EDGEs;
reciprocal incidence fixes caps, side FACEs and top EDGEs before coefficients are
compared. Ambiguous endpoint roles remain unassigned geometric sets.
"""
import math
import struct

from asm_records import inspect_asm
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_brep import decode_topology
from decode_extrusion_source_operands import EXTRUDE, qualify_extrusion_source_operands
from decode_extrusion_reconstruction import _near, _finite, _dot, _cross, _compare_bundle
from decode_profiles import PROFILE_DESCRIPTOR_GUID, PROFILE_LOOP_GUID
from decode_sketch import reference
from decode_trimmed_extrusion_geometry import derive_trimmed_extrusion

SCOPE=('Native complete selected Line/Circle portion tuples and Sketch/frame/Distance '
    'controls construct a straight zero-taper solid independently of cached geometry. '
    'Full tuple naming and reciprocal incidence fix bounded cache carriers before '
    'complete coefficient/domain corroboration. Mathematical angle/phase relations '
    'are not native/API UV or traversal. Unassigned endpoint/connector geometric '
    'sets choose no ENTITY identity; chronology, current/final, persistent and API '
    'handle identities and general regeneration remain unresolved.')


def _candidates(data,records):
    """Counted native tuple probe only; framed unsupported literal variants stay candidates."""
    primary={}
    for record in records:
        if record.is_primary:primary.setdefault(record.object_id,[]).append(record)
    owners=set()
    for record in records:
        if not record.is_primary or record.class_guid!=PROFILE_DESCRIPTOR_GUID:continue
        try:
            payload=data[record.body:record.end];owner=reference(payload,len(payload)-11)
            definitions=primary[reference(payload,2)]
            if len(definitions)!=1 or definitions[0].class_guid!=PROFILE_LOOP_GUID:continue
            definition=definitions[0];body=data[definition.body:definition.end]
            if body[:2]!=bytes(2) or reference(body,2)!=record.object_id or struct.unpack_from('<I',body,13)[0]!=1:continue
            count=struct.unpack_from('<I',body,17)[0]
            if not 1<=count<=32:continue
            cursor=21;variant=False
            for _ in range(count):
                size=struct.unpack_from('<I',body,cursor)[0];cursor+=4
                if not 1<=size<=128 or cursor+40*size+1>len(body):raise ValueError('Unframed tuple probe')
                for _ in range(size):
                    fields=struct.unpack_from('<IQQIIIQ',body,cursor);cursor+=40
                    variant|=fields[4:6]!=(1,1)
                cursor+=1
            if body[cursor:]==bytes(4) and variant:owners.add(owner)
        except (ValueError,KeyError,IndexError,struct.error):continue
    return owners


def _closed(graph,nodes,n):
    expected=dict(lump=1,shell=1,face=n+2,loop=n+2,coedge=6*n,edge=3*n,vertex=2*n)
    if graph['body_transform_is_identity'] is not True:raise ValueError('Trimmed cache BODY frame is not identity')
    for kind,count in expected.items():
        ids=graph[kind+'_indices']
        if len(ids)!=count or len(set(ids))!=count or any(nodes[i]['kind']!=kind for i in ids):
            raise ValueError('Trimmed cache complete BODY topology count/type differs: '+kind)
    body=nodes[graph['body_index']];lump=nodes[graph['lump_indices'][0]];shell=nodes[graph['shell_indices'][0]]
    if (body['first_lump_index']!=lump['index'] or body['first_wire_index'] is not None or lump['body_index']!=body['index']
            or lump['next_lump_index'] is not None or lump['first_shell_index']!=shell['index']
            or shell['lump_index']!=lump['index'] or shell['next_shell_index'] is not None
            or shell['subshell_index'] is not None or shell['first_wire_index'] is not None):
        raise ValueError('Trimmed cache reciprocal single lump/shell/no-wire framing differs')
    seen=set();current=shell['first_face_index']
    while current is not None:
        if current not in graph['face_indices'] or current in seen or nodes[current]['shell_index']!=shell['index']:
            raise ValueError('Trimmed cache FACE chain differs')
        seen.add(current);current=nodes[current]['next_face_index']
    if seen!=set(graph['face_indices']):raise ValueError('Trimmed cache FACE chain incomplete')
    loops=[];all_coedges=set()
    for f in graph['face_indices']:
        loop_id=nodes[f]['first_loop_index']
        if loop_id not in graph['loop_indices'] or nodes[loop_id]['face_index']!=f or nodes[loop_id]['next_loop_index'] is not None:
            raise ValueError('Trimmed cache one reciprocal loop per FACE differs')
        cycle=[];pairs=[];current=nodes[loop_id]['first_coedge_index']
        while current not in cycle:
            if current not in graph['coedge_indices'] or current in all_coedges or len(cycle)>4:
                raise ValueError('Trimmed cache loop cycle framing differs')
            coedge=nodes[current];next_id=coedge['next_coedge_index'];previous=coedge['previous_coedge_index']
            if (coedge['loop_index']!=loop_id or next_id not in graph['coedge_indices'] or previous not in graph['coedge_indices']
                    or nodes[next_id]['previous_coedge_index']!=current or nodes[previous]['next_coedge_index']!=current
                    or coedge['edge_index'] not in graph['edge_indices']):
                raise ValueError('Trimmed cache reciprocal COEDGE loop differs')
            edge=nodes[coedge['edge_index']];pair=[edge['start_vertex_index'],edge['end_vertex_index']]
            if coedge['is_reversed']:pair.reverse()
            if pairs and pairs[-1][1]!=pair[0]:raise ValueError('Trimmed cache loop endpoint continuity differs')
            cycle.append(current);pairs.append(pair);current=next_id
        if current!=cycle[0] or pairs[-1][1]!=pairs[0][0] or len(cycle) not in (n,4):
            raise ValueError('Trimmed cache complete loop closure differs')
        all_coedges.update(cycle)
        loops.append(dict(face_index=f,loop_index=loop_id,coedge_cycle=cycle,
            edge_indices=[nodes[c]['edge_index'] for c in cycle],vertex_cycle=[p[0] for p in pairs],
            native_LOOP=nodes[loop_id],native_COEDGEs=[nodes[c] for c in cycle]))
    if all_coedges!=set(graph['coedge_indices']):raise ValueError('Trimmed cache coedge exhaustion differs')
    for e in graph['edge_indices']:
        edge=nodes[e];uses=[nodes[c] for c in all_coedges if nodes[c]['edge_index']==e]
        if (len(uses)!=2 or len({nodes[c['loop_index']]['face_index'] for c in uses})!=2
                or edge['first_coedge_index'] not in {c['index'] for c in uses}
                or any(a['partner_index']!=b['index'] for a,b in ((uses[0],uses[1]),(uses[1],uses[0])))):
            raise ValueError('Trimmed cache EDGE head/two-FACE/other-use partner reciprocity differs')
        if edge['start_vertex_index']==edge['end_vertex_index'] or any(v not in graph['vertex_indices'] for v in (edge['start_vertex_index'],edge['end_vertex_index'])):
            raise ValueError('Trimmed cache distinct typed EDGE endpoints differ')
    for v in graph['vertex_indices']:
        vertex=nodes[v];edges=[e for e in graph['edge_indices'] if v in (nodes[e]['start_vertex_index'],nodes[e]['end_vertex_index'])]
        if len(edges)!=3 or vertex['first_edge_index'] not in edges or nodes[vertex['point_index']]['kind']!='point':
            raise ValueError('Trimmed cache VERTEX degree/head/POINT differs')
        _finite(nodes[vertex['point_index']]['raw_origin'],'trimmed cache POINT')
    return loops


def _identities(group,graph,nodes,loops):
    """All source/target FACE/EDGE roles are fixed without geometric coefficients."""
    q=group['profile_portion_cache_corroboration']['qualified_profile_cache'];rows=[];faces=[]
    for portion in group['derived_source_portions']:
        identity=portion['source_primitive_id'];fields=portion['stored_profile_reference']['stored_coedge_text_fields']
        matches=[c for source in q['source_curves'] if source['native_entity_object_id']==identity
            for c in source['cached_coedge_candidates'] if c['stored_decimal_text_fields']==fields]
        edge_ids={c['edge_record_index'] for c in matches};coedges={c['coedge_record_index'] for c in matches}
        if len(matches)!=2 or len(edge_ids)!=1 or len(coedges)!=2:
            raise ValueError('Trimmed cache complete tuple does not uniquely name two uses of one base EDGE')
        edge_id=next(iter(edge_ids))
        if edge_id not in graph['edge_indices'] or coedges!={c for c in graph['coedge_indices'] if nodes[c]['edge_index']==edge_id}:
            raise ValueError('Trimmed cache full tuple EDGE/COEDGE graph membership differs')
        incident={nodes[nodes[c]['loop_index']]['face_index'] for c in coedges};faces.append(incident)
        rows.append(dict(role_key=portion['role_key'],source_primitive_id=identity,stored_full_tuple=portion['stored_profile_reference'],
            full_tuple_COEDGE_matches=matches,base_edge_index=edge_id))
    base_edges={r['base_edge_index'] for r in rows}
    common=set.intersection(*faces)
    if len(base_edges)!=len(rows) or len(common)!=1:raise ValueError('Trimmed cache unique common base cap differs')
    base=next(iter(common));side_ids=[next(iter(f-{base})) for f in faces]
    top=set(graph['face_indices'])-{base}-set(side_ids)
    if len(set(side_ids))!=len(rows) or len(top)!=1:raise ValueError('Trimmed cache side/top FACE incidence bijection differs')
    top=next(iter(top));by_face={r['face_index']:r for r in loops}
    if set(by_face[base]['edge_indices'])!=base_edges:raise ValueError('Trimmed cache base cap boundary does not exhaust named portions')
    for row,side in zip(rows,side_ids):
        side_edges=set(by_face[side]['edge_indices']);top_edges=side_edges&set(by_face[top]['edge_indices'])
        if len(side_edges)!=4 or len(top_edges)!=1:raise ValueError('Trimmed cache unique side/top EDGE incidence differs')
        top_edge=next(iter(top_edges));connectors=side_edges-{row['base_edge_index'],top_edge}
        if len(connectors)!=2:raise ValueError('Trimmed cache side connector incidence differs')
        base_vertices={nodes[row['base_edge_index']][k] for k in ('start_vertex_index','end_vertex_index')}
        top_vertices={nodes[top_edge][k] for k in ('start_vertex_index','end_vertex_index')}
        pairs=[]
        for e in sorted(connectors):
            pair={nodes[e]['start_vertex_index'],nodes[e]['end_vertex_index']}
            if len(pair&base_vertices)!=1 or len(pair&top_vertices)!=1:
                raise ValueError('Trimmed cache connector does not join fixed base/top boundary vertices')
            pairs.append(dict(edge_index=e,base_vertex_index=next(iter(pair&base_vertices)),top_vertex_index=next(iter(pair&top_vertices))))
        row.update(side_face_index=side,top_edge_index=top_edge,connector_incidence=pairs)
    if {r['top_edge_index'] for r in rows}!=set(by_face[top]['edge_indices']):raise ValueError('Trimmed cache top boundary exhaustion differs')
    if base_edges|{r['top_edge_index'] for r in rows}|{c['edge_index'] for r in rows for c in r['connector_incidence']}!=set(graph['edge_indices']):
        raise ValueError('Trimmed cache all EDGE role exhaustion differs')
    return dict(base_cap_face_index=base,top_cap_face_index=top,portion_incidence=rows,loops=loops,
        endpoint_role_to_native_VERTEX=None,scope='Complete full-tuple and reciprocal incidence identity before geometric corroboration; no coordinate ENTITY assignment')


def _positions(edge,nodes):return [nodes[nodes[edge[k]]['point_index']]['raw_origin'] for k in ('start_vertex_index','end_vertex_index')]
def _plane(plane,normal,constant,label):
    if plane['kind']!='plane-surface':raise ValueError('Trimmed cache '+label+' is not Plane')
    _finite(plane['raw_origin']+plane['normal']+plane['stored_reference_axis'],label)
    _near([_dot(plane['normal'],plane['normal'])],[1.],label+' unit normal')
    sign=1 if _dot(plane['normal'],normal)>=0 else -1
    a=_near(plane['normal'],[sign*x for x in normal],label+' full normal coefficients')
    b=_near([_dot(plane['normal'],plane['raw_origin'])],[sign*constant],label+' plane constant')
    return dict(normal_sign=sign,normal_residual_raw=a,constant_residual_raw=b,native_Plane=plane)


def _curve(edge,curve,nodes,model):
    positions=_positions(edge,nodes);parameters=[edge['start_parameter'],edge['end_parameter']]
    _finite(parameters,'trimmed finite EDGE domain')
    if model['kind']=='CircleArc':
        if curve['kind']!='ellipse-curve':raise ValueError('Trimmed cache selected arc lacks ellipse carrier')
        radius=curve['raw_major_radius'];normal=curve['normal'];reference=curve['stored_reference_axis'];origin=curve['raw_origin']
        _finite(origin+normal+reference+[radius,curve['raw_minor_radius']],'trimmed ellipse coefficients')
        if radius<=0:raise ValueError('Trimmed cache ellipse radius nonpositive')
        u=[v/radius for v in reference];v=_cross(normal,u)
        _near([radius,curve['raw_minor_radius']],[model['radius_cm']]*2,'trimmed full circular radii')
        _near(origin,model['center_cm'],'trimmed full circle center')
        _near([_dot(normal,normal),_dot(u,u),_dot(normal,u)],[1.,1.,0.],'trimmed circle orthonormal frame')
        sign=1 if _dot(normal,model['unit_axis'])>=0 else -1
        _near(normal,[sign*x for x in model['unit_axis']],'trimmed full circle normal coefficients')
        phase=math.atan2(_dot(v,model['reference_u']),_dot(u,model['reference_u']))
        _near([math.cos(phase)*x+math.sin(phase)*y for x,y in zip(u,v)],model['reference_u'],'trimmed full cosine coefficient')
        _near([sign*(-math.sin(phase)*x+math.cos(phase)*y) for x,y in zip(u,v)],model['reference_v'],'trimmed full sine coefficient')
        a,b=model['angle_interval_radians'];p,q=parameters
        span_error=_near([abs(q-p)],[b-a],'trimmed complete bounded arc span')
        expected_mid=sign*(a+b)/2+phase;native_mid=(p+q)/2
        phase_error=_near([math.cos(native_mid),math.sin(native_mid)],[math.cos(expected_mid),math.sin(expected_mid)],'trimmed complete bounded arc midpoint phase')
        evaluations=[[o+radius*(math.cos(t)*x+math.sin(t)*y) for o,x,y in zip(origin,u,v)] for t in parameters]
        endpoint_error=_compare_bundle(evaluations,positions,'trimmed native arc domain endpoints')
        return dict(native_EDGE=edge,native_curve=curve,native_endpoint_positions_cm=positions,
            native_endpoint_evaluations_cm=evaluations,source_angle_to_mathematical_native_ellipse_parameter=dict(scale=sign,phase_radians=phase),
            whole_window_proof=dict(span_residual_raw=span_error,midpoint_phase_residual_raw=phase_error,endpoint_residual_raw=endpoint_error),
            native_API_parameter_or_traversal_meaning=None)
    if curve['kind']!='straight-curve':raise ValueError('Trimmed cache selected segment lacks straight carrier')
    origin=curve['raw_origin'];direction=curve['direction'];_finite(origin+direction,'trimmed Line coefficients')
    _near([_dot(direction,direction)],[1.],'trimmed native Line unit direction')
    start,end=model['start_cm'],model['end_cm'];delta=[y-x for x,y in zip(start,end)];length=math.hypot(*delta)
    if length<=1e-10:raise ValueError('Trimmed derived segment degenerates')
    d=[x/length for x in delta];sign=1 if _dot(direction,d)>=0 else -1
    _near(direction,[sign*x for x in d],'trimmed whole Line direction coefficients')
    relative=[x-o for x,o in zip(start,origin)];along=_dot(relative,direction)
    _near([x-along*y for x,y in zip(relative,direction)],[0.,0.,0.],'trimmed whole Line locus')
    evaluations=[[o+t*d for o,d in zip(origin,direction)] for t in parameters]
    endpoint_error=_compare_bundle(evaluations,positions,'trimmed native Line domain endpoints')
    model_error=_compare_bundle(evaluations,[start,end],'trimmed complete bounded segment endpoints')
    return dict(native_EDGE=edge,native_curve=curve,native_endpoint_positions_cm=positions,native_endpoint_evaluations_cm=evaluations,
        full_direction_sign=sign,endpoint_residual_raw=endpoint_error,complete_segment_residual_raw=model_error,
        native_API_parameter_or_traversal_meaning=None)


def _corroborate(group,graph,nodes,model):
    loops=_closed(graph,nodes,len(model['boundary_curves']));identity=_identities(group,graph,nodes,loops)
    curves={r['role_key']:r for r in model['boundary_curves']};rows=[];connectors={}
    for role in identity['portion_incidence']:
        derived=curves[role['role_key']];layer_rows=[]
        for edge_id,layer in zip((role['base_edge_index'],role['top_edge_index']),derived['layer_curves']):
            edge=nodes[edge_id];layer_rows.append(dict(layer=layer['layer'],**_curve(edge,nodes[edge['curve_index']],nodes,layer['geometry'])))
        face=nodes[role['side_face_index']];surface=nodes[face['surface_index']];carrier=derived['side_carrier']
        if carrier['kind']=='Plane':
            carrier_proof=_plane(surface,carrier['unit_normal'],carrier['plane_constant_cm'],'trimmed side Plane')
        else:
            analytic=surface.get('analytic_surface',{})
            if analytic.get('kind')!='Cylinder':raise ValueError('Trimmed cache arc side is not Cylinder')
            axis=analytic['axis'];origin=analytic['raw_origin'];radius=analytic['raw_radius']
            _finite(axis+origin+[radius],'trimmed Cylinder coefficients')
            _near([radius],[carrier['radius_cm']],'trimmed whole Cylinder radius')
            sign=1 if _dot(axis,carrier['unit_axis'])>=0 else -1
            _near(axis,[sign*x for x in carrier['unit_axis']],'trimmed whole Cylinder axis coefficients')
            delta=[x-y for x,y in zip(origin,carrier['axis_origin_cm'])];along=_dot(delta,axis)
            residual=_near([x-along*y for x,y in zip(delta,axis)],[0.,0.,0.],'trimmed whole Cylinder axis line')
            carrier_proof=dict(native_Cylinder=surface,axis_line_residual_raw=residual,
                bounded_domain_scope='Fixed base/top full arc windows and two reciprocal connector edges bound this selected cylindrical patch; no native UV assignment')
        for c in role['connector_incidence']:
            edge=nodes[c['edge_index']];start=nodes[nodes[c['base_vertex_index']]['point_index']]['raw_origin']
            end=nodes[nodes[c['top_vertex_index']]['point_index']]['raw_origin']
            connectors[c['edge_index']]=dict(incidence=c,geometry=_curve(edge,nodes[edge['curve_index']],nodes,
                dict(kind='LineSegment',start_cm=start,end_cm=end)),base_position_cm=start,top_position_cm=end,
                scope='Native Line endpoint consistency only; independent model connector bundle is compared separately')
        rows.append(dict(role_key=role['role_key'],identity=role,layer_boundaries=layer_rows,native_side_FACE=face,
            side_carrier_corroboration=carrier_proof))
    connector_error=_compare_bundle([[r['base_position_cm'],r['top_position_cm']] for r in connectors.values()],
        [[r['lower_cm'],r['upper_cm']] for r in model['connector_segments']],'trimmed complete directed connector geometric bundle')
    caps=[]
    for face_id,cap in zip((identity['base_cap_face_index'],identity['top_cap_face_index']),model['caps']):
        face=nodes[face_id];proof=_plane(nodes[face['surface_index']],cap['unit_outward_normal'],cap['plane_constant_cm'],'trimmed cap Plane')
        caps.append(dict(layer=cap['layer'],native_FACE=face,plane_corroboration=proof,
            boundary_loop=next(l for l in loops if l['face_index']==face_id),
            scope='Complete named portion boundary is exhausted by this reciprocal cap loop; chosen mathematical normal is not FACE sense'))
    origin_ids=set(i for k in ('lump','shell','face','loop','coedge','edge','vertex') for i in graph[k+'_indices'])
    origin_ids.add(graph['body_index'])
    origin_ids.update(nodes[v]['point_index'] for v in graph['vertex_indices'])
    origin_ids.update(nodes[e]['curve_index'] for e in graph['edge_indices'])
    origin_ids.update(nodes[f]['surface_index'] for f in graph['face_indices'])
    return dict(kind='CompleteSelectedPortionStraightSolidCache',counts=graph['counts'],identity_provenance=identity,
        source_record_origins=[dict(record_index=i,kind=nodes[i]['kind'],record_offset=nodes[i]['offset'],section='initial') for i in sorted(origin_ids)],
        portion_boundaries=rows,connector_edges=list(connectors.values()),caps=caps,
        complete_connector_bundle_residual_raw=connector_error,endpoint_role_to_native_VERTEX=None,
        source_to_cache_entity_mapping=None,scope=SCOPE)


def decode_trimmed_extrusion_reconstruction(data,records,features,member,members,body_blob_bindings,body_selections=None):
    result=dict(decoded=[],unresolved=[],scope=SCOPE);owners=_candidates(data,records)
    if not owners:return result
    from decode_basics import named_features
    fresh=named_features(data,records);candidates=[f for f in fresh if f.get('class_guid')==EXTRUDE and f['object_id'] in owners]
    mapping_input=dict(decoded=[dict(mapping_record_object_id=m['mapping_record_object_id'],owner_object_id=m['owner_object_id'],
        history_blob_member=m['history_blob_member'],body_count=m['body_count'],bindings=[dict(stored_handle=b['stored_handle'],
        native_body_object_id=b['native_body_object_id']) for b in m['bindings']]) for m in body_blob_bindings.get('decoded',[])])
    joined=None;cache={}
    # The source factory independently compares supplied receiver parameters with
    # fresh native metadata; use caller feature only for that additional guard.
    for native in candidates:
        try:
            matches=[f for f in features if f['object_id']==native['object_id']]
            if len(matches)!=1:raise ValueError('Trimmed extrusion receiver metadata missing or duplicated')
            feature=matches[0];source=qualify_extrusion_source_operands(data,records,features,member,members,body_blob_bindings,feature,allow_trimmed_profiles=True)
            if source is None or len(source['source_groups'])!=1:raise ValueError('Trimmed extrusion needs one fresh owned native source')
            group=source['source_groups'][0]
            if not group['native_profile_kind'].startswith('Trimmed'):raise ValueError('Trimmed extrusion native selected portion family differs')
            if joined is None:joined=decode_body_asm_identifiers(data,records,member,members,mapping_input)
            matches=[(m,b) for m in joined['decoded'] for b in m['bindings'] if b['native_body_object_id']==group['native_body_object_id']]
            if len(matches)!=1 or matches[0][1]!=group['binding'] or matches[0][0]['history_blob_member']!=group['history_blob_member']:
                raise ValueError('Trimmed extrusion fresh same-asset source BODY mapping differs')
            matrix=group['source_sketch']['placement']['sketch_to_component_matrix']
            _near(group['stored_direction_vector'],[matrix[2],matrix[6],matrix[10]],'trimmed native component direction/frame')
            model=derive_trimmed_extrusion(group['mathematical_inputs'],matrix,group['extrude_controls'])
            name=group['history_blob_member']
            if name not in cache:
                parsed=inspect_asm(members[name]);cache[name]=(parsed,decode_topology(parsed))
            parsed,topology=cache[name];nodes={n['index']:n for n in topology['nodes']}
            graphs=[g for g in topology['body_graphs'] if g['body_index']==group['asm_body_index']]
            if len(graphs)!=1:raise ValueError('Trimmed extrusion mapped BODY graph missing or duplicated')
            corroboration=_corroborate(group,graphs[0],nodes,model)
            result['decoded'].append(dict(feature_object_id=native['object_id'],native_source_provenance=source,
                source_native_body_object_id=group['native_body_object_id'],binding=group['binding'],history_blob_member=name,
                asm_body_index=group['asm_body_index'],derived_geometry=model,native_cache_geometry_corroboration=corroboration,
                exact_API_handle_identity=None,qualified_historical_state=None,current_or_final_geometry_identity=None,scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,struct.error,OverflowError) as error:
            result['unresolved'].append(dict(feature_object_id=native['object_id'],reason=str(error)))
    return result
