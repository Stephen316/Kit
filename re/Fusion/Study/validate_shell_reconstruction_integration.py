"""Fixed saved Shell source/reconstruction integration; cached comparison only after freeze."""
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASELINE='ddc57a8'
FILES=(
    'tools-fda3948848f4/Shell.f3d',
    'bodymodes-405fbd002680/shell_inside.f3d',
    'bodymodes-405fbd002680/shell_outside.f3d',
    'bodymodes-405fbd002680/shell_both.f3d',
    'bodymodes-405fbd002680/shell_rounded.f3d',
    'bodymodes-df9b7113539f/shell_inside.f3d',
    'bodymodes-df9b7113539f/shell_outside.f3d',
    'bodymodes-df9b7113539f/shell_both.f3d',
    'bodymodes-df9b7113539f/shell_rounded.f3d',
    'bodyselections-62e42366c722/shell_body.f3d',
    'bodyselections-62e42366c722/shell_two_faces.f3d',
    'scaleshellinputs-97ef1cfd19e4/shell_two_bodies.f3d',
    'scaleshellinputs-97ef1cfd19e4/shell_body_and_other_face.f3d',
    'tools-fda3948848f4/Scale.f3d',
    'surfacetools-856ca50cf4c7/offset_positive.f3d',
)


def native_extrude_box(before,source_feature_id):
    """Independent box construction from prior typed Sketch/Extrude controls only."""
    import math
    features=before['streams'][0]['features']
    source,=[f for f in features if f['object_id']==source_feature_id]
    assert source['kind']=='Extrude' and source['operation']['kind']=='NewBody'
    assert source['start']['kind']=='ProfilePlane' and source['extent']['mode']=='OneSided'
    extent=source['extent']['side_one']
    assert extent['condition']=='Distance' and extent['taper_angle_radians']==0
    assert source['extent']['stored_direction_vector']==[0.,0.,1.] and extent['distance_cm']>0
    profile,=source['profile_selection'];loop,=profile['loops']
    assert loop['is_outer'] is True and len(loop['curve_references'])==4
    sketch,=[f for f in features if f['kind']=='Sketch' and f['sketch_object_id']==profile['sketch_object_id']]
    geometry={g['object_id']:g for g in sketch['geometry']}
    matrix=sketch['placement']['sketch_to_component_matrix']
    assert matrix==[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]
    line_ids=[];point_degree={};line_edges=[]
    for reference in loop['curve_references']:
        line=geometry[reference['entity_id']]
        assert line['kind']=='Line' and not line['is_construction']
        assert line['entity_tag']==reference['entity_tag'] and reference['secondary_tag']==0
        a,b=line['start_point_id'],line['end_point_id'];assert a!=b
        line_ids.append(line['object_id']);line_edges.append((a,b))
        for identity in (a,b):point_degree[identity]=point_degree.get(identity,0)+1
    assert len(set(line_ids))==4 and len(point_degree)==4 and set(point_degree.values())=={2}
    points={identity:geometry[identity]['position_cm'] for identity in point_degree}
    assert all(geometry[identity]['kind']=='Point' and all(math.isfinite(v) for v in p) for identity,p in points.items())
    assert len({p[2] for p in points.values()})==1
    minimum=[min(p[i] for p in points.values()) for i in range(3)]
    maximum=[max(p[i] for p in points.values()) for i in range(3)]
    assert minimum[0]<maximum[0] and minimum[1]<maximum[1]
    assert {tuple(p) for p in points.values()}=={(x,y,minimum[2]) for x in (minimum[0],maximum[0]) for y in (minimum[1],maximum[1])}
    for a,b in line_edges:assert sum(x!=y for x,y in zip(points[a],points[b]))==1
    maximum[2]+=extent['distance_cm']
    vertices={(identity,layer):[p[0],p[1],p[2]+layer*extent['distance_cm']] for identity,p in points.items() for layer in (0,1)}
    return dict(source_feature_object_id=source_feature_id,native_sketch_object_id=profile['sketch_object_id'],
        native_line_object_ids=line_ids,native_point_object_ids=sorted(points),minimum_cm=minimum,maximum_cm=maximum,
        POINT_layer_positions_cm=vertices)


def hollow_box_reference(source,inside,outside,open_sides):
    """Mathematical planes/corners from source controls; no cache coordinate input."""
    import itertools
    import math
    inside=0. if inside is None else inside;outside=0. if outside is None else outside
    assert all(math.isfinite(v) and v>=0 for v in (inside,outside)) and inside+outside>0
    opened=set(map(tuple,open_sides))
    assert len(opened)==len(open_sides) and len(opened)<=2
    assert all(axis in (0,1,2) and side in (0,1) for axis,side in opened)
    assert len(opened)!=2 or len({axis for axis,side in opened})==1
    low,high=source['minimum_cm'],source['maximum_cm']
    outer_low=[];outer_high=[];inner_low=[];inner_high=[]
    for i in range(3):
        outer_low.append(low[i] if (i,0) in opened else low[i]-outside)
        outer_high.append(high[i] if (i,1) in opened else high[i]+outside)
        inner_low.append(low[i] if (i,0) in opened else low[i]+inside)
        inner_high.append(high[i] if (i,1) in opened else high[i]-inside)
        assert outer_low[i]<=inner_low[i]<inner_high[i]<=outer_high[i]
    corners={}
    for layer,lower,upper in (('Outer',outer_low,outer_high),('Inner',inner_low,inner_high)):
        for signs in itertools.product((0,1),repeat=3):
            corners[(layer,signs)]=[(upper if sign else lower)[i] for i,sign in enumerate(signs)]
    volume=math.prod(b-a for a,b in zip(outer_low,outer_high))-math.prod(b-a for a,b in zip(inner_low,inner_high))
    return dict(source_bounds_cm=[low,high],outer_bounds_cm=[outer_low,outer_high],inner_bounds_cm=[inner_low,inner_high],
        corner_positions_cm=corners,removed_sides=sorted(opened),volume_cm3=volume,
        planar_face_count=12-len(opened),straight_edge_count=24,vertex_count=16)


def saved_API_controls(before,archive):
    """Recorded getter/parameter corroboration, without API entity assignment."""
    import json
    folder,filename=archive.split('/',1)
    truth_path=ROOT/folder/'ground_truth.json'
    truth=json.loads(truth_path.read_text())
    sample,=[s for s in truth['samples'] if s['file']==filename]
    feature,=[f for f in before['streams'][0]['features'] if f['kind']=='Shell']
    settings=feature['tool_settings'];api=sample.get('settings',{})
    report=dict(truth_file=str(truth_path.relative_to(ROOT)),parameter_roles=[],settings_fields=[],
        source_entity_assignment=None,numerical_API_geometry_corroboration=None)
    for api_key,native_key in (('inside_cm','inside_thickness_cm'),('outside_cm','outside_thickness_cm'),
            ('inside_thickness_cm','inside_thickness_cm'),('outside_thickness_cm','outside_thickness_cm'),
            ('shell_type','stored_shell_type'),('is_tangent_chain','is_tangent_chain')):
        if api_key in api:
            assert api[api_key]==settings[native_key]
            report['settings_fields'].append(api_key)
    for parameter in sample.get('parameters',[]):
        role=parameter['role']
        if role not in ('innerThickness','outerThickness'):continue
        native='inside_thickness_cm' if role=='innerThickness' else 'outside_thickness_cm'
        assert parameter['value']==settings[native]
        report['parameter_roles'].append(role)
    assert report['parameter_roles'] or report['settings_fields']
    if 'actual_inputs' in sample:
        assert not sample['getter_errors']
        native_types=['adsk::fusion::BRep'+i['kind'] for i in settings['input_selections']]
        assert native_types==[i['entity_type'] for i in sample['actual_inputs']]
        report.update(actual_ordered_input_types=native_types,
            API_input_handle_or_face_identity_assignment=None)
    report['scope']='Saved Shell controls and input-kind sequence only; native topology identities are qualified separately, with no numerical API shape or entity-handle assignment'
    return report


def qualify_native_sources(row,before,source):
    """Recheck source IDs/controls from the preserved native baseline, before math."""
    assert row['native_source_provenance']==source
    stream=before['streams'][0]
    feature,=[f for f in stream['features'] if f['object_id']==row['feature_object_id']]
    assert feature['kind']=='Shell' and feature['object_id']==source['feature_object_id']
    for key,value in feature['tool_settings'].items():assert source['settings'][key]==value
    assert source['shell_owned_result_anchors']==[]
    for key in ('source_to_result_pairing','API_handle_identity','persistent_identity','qualified_historical_state'):
        assert source[key] is None
    inputs=feature['tool_settings']['input_selections'];independent=source['selected_inputs']
    assert len(inputs)==len(independent)
    keys=('kind','native_body_object_id','body_anchor_object_id','source_owner_object_id','descriptor_object_id')
    for ordinal,(native,proof) in enumerate(zip(inputs,independent)):
        assert all(native[k]==proof[k] for k in keys) and proof['operand_index']==ordinal
        assert proof['native_descriptor']['object_id']==native['descriptor_object_id']
        if native['kind']=='Face':
            recipe=proof['counted_recipe']
            assert recipe['object_id']==native['recipe']['object_id']
            assert recipe['payload_length']==476 and proof['exact_counted_recipe_payload_replay'] is True
            assert proof['removed_face_cache_identity'] is None
    groups={g['native_body_object_id']:g for g in source['source_groups']}
    assert len(groups)==source['source_group_count'] and set(groups)=={i['native_body_object_id'] for i in inputs}
    result={}
    for body,group in groups.items():
        chosen=[i for i in inputs if i['native_body_object_id']==body]
        assert {i['source_owner_object_id'] for i in chosen}=={group['source_feature_object_id']}
        assert {i['body_anchor_object_id'] for i in chosen}=={group['body_anchor_object_id']}
        assert group['selected_input_indices']==[i for i,entry in enumerate(inputs) if entry['native_body_object_id']==body]
        anchor,=[a for a in stream['body_selections']['body_anchors'] if a['object_id']==group['body_anchor_object_id']]
        assert anchor['native_body_object_id']==body and anchor['source_owner_object_id']==group['source_feature_object_id']
        mapping,=[m for m in stream['body_blob_bindings']['decoded'] if m['mapping_record_object_id']==group['mapping_record_object_id']]
        binding,=[b for b in mapping['bindings'] if b['native_body_object_id']==body]
        assert binding['stored_handle']==group['binding']['stored_handle']
        assert mapping['history_blob_member']==group['history_blob_member']
        assert binding['asm_body_index']==group['asm_body_index']
        box=native_extrude_box(before,group['source_feature_object_id'])
        assert set(box['native_line_object_ids'])=={line['line_object_id'] for line in group['native_profile_lines']}
        assert set(box['native_point_object_ids'])=={point['point_object_id'] for point in group['native_profile_points']}
        result[body]=box
    return result


def _point_key(point):
    return tuple(round(x,8) for x in point)


def _segment_key(a,b):
    return tuple(sorted((_point_key(a),_point_key(b))))


def _plane_key(normal,constant):
    import math
    length=math.hypot(*normal);assert math.isclose(length,1.,abs_tol=1e-9)
    sign=next(1 if v>0 else -1 for v in normal if abs(v)>1e-9)
    return tuple(round(sign*x,8) for x in (*normal,constant))


def native_cache_bundle(topology,body_index):
    """Complete already-BODY-scoped geometry bundle; no entity assignment by geometry."""
    import math
    nodes={n['index']:n for n in topology['nodes']}
    graph,=[g for g in topology['body_graphs'] if g['body_index']==body_index]
    assert graph['body_transform_is_identity'] is True
    vertices={i:nodes[nodes[i]['point_index']]['raw_origin'] for i in graph['vertex_indices']}
    assert len(vertices)==16 and len(set(map(_point_key,vertices.values())))==16
    edges={};parameter_proofs=[]
    for index in graph['edge_indices']:
        edge=nodes[index];assert edge['kind']=='edge'
        a,b=(vertices[edge[k]] for k in ('start_vertex_index','end_vertex_index'))
        curve=nodes[edge['curve_index']];assert curve['kind']=='straight-curve'
        sign=-1 if edge['is_reversed'] else 1
        raw_parameters=[edge['start_parameter'],edge['end_parameter']]
        evaluations=[]
        for p,parameter in zip((a,b),raw_parameters):
            computed=[o+sign*parameter*d for o,d in zip(curve['raw_origin'],curve['direction'])]
            assert math.dist(p,computed)<1e-9
            evaluations.append(dict(raw_parameter=parameter,effective_parameter=sign*parameter,
                raw_ENDPOINT_position=p,evaluated_position=computed,residual_raw=math.dist(p,computed)))
        parameter_proofs.append(dict(EDGE_record_index=index,curve_record_index=edge['curve_index'],
            stored_EDGE_is_reversed=edge['is_reversed'],raw_parameters=raw_parameters,
            observed_parameter_sign=sign,endpoint_evaluations=evaluations,
            scope='Bounded saved Shell cache Line-parameter consistency only; no global EDGE sense or traversal convention'))
        edges[index]=_segment_key(a,b)
    assert len(edges)==24 and len(set(edges.values()))==24
    faces=[];loop_ids=set();coedge_ids=set();face_point_checks=0
    for index in graph['face_indices']:
        face=nodes[index];plane=nodes[face['surface_index']];assert plane['kind']=='plane-surface'
        normal=plane['normal'];origin=plane['raw_origin'];constant=sum(n*p for n,p in zip(normal,origin))
        loops=[];loop_id=face['first_loop_index']
        while loop_id is not None:
            assert loop_id not in loop_ids;loop_ids.add(loop_id)
            loop=nodes[loop_id];assert loop['face_index']==index
            initial=loop['first_coedge_index'];current=initial;uses=[]
            while True:
                assert current not in coedge_ids;coedge_ids.add(current)
                coedge=nodes[current];assert coedge['loop_index']==loop_id
                assert nodes[coedge['next_coedge_index']]['previous_coedge_index']==current
                edge=nodes[coedge['edge_index']];uses.append(edges[coedge['edge_index']])
                for v in (edge['start_vertex_index'],edge['end_vertex_index']):
                    assert abs(sum(n*(p-o) for n,p,o in zip(normal,vertices[v],origin)))<1e-9
                    face_point_checks+=1
                current=coedge['next_coedge_index']
                if current==initial:break
            assert len(uses)==len(set(uses))==4
            loops.append(tuple(sorted(uses)));loop_id=loop['next_loop_index']
        assert len(loops) in (1,2)
        faces.append((_plane_key(normal,constant),tuple(sorted(loops))))
    assert loop_ids==set(graph['loop_indices']) and coedge_ids==set(graph['coedge_indices'])
    assert len(loop_ids)==12 and len(coedge_ids)==48
    return dict(vertices=sorted(map(_point_key,vertices.values())),segments=sorted(edges.values()),
        faces=sorted(faces),counts=dict(vertices=16,edges=24,FACEs=len(faces),loops=12,COEDGEs=48),
        endpoint_evaluations=48,FACE_endpoint_plane_evaluations=face_point_checks,
        scoped_Line_parameter_proofs=parameter_proofs)


def derived_geometry_bundle(derived):
    """Same complete bundle representation, retaining no native/semantic assignment."""
    vertices={v['key']:v['position_cm'] for v in derived['vertices']}
    assert len(vertices)==len(derived['vertices'])==16
    segments=[_segment_key(vertices[a],vertices[b]) for a,b in (e['vertex_keys'] for e in derived['segments'])]
    assert len(segments)==len(set(segments))==24
    faces=[]
    for face in derived['planar_boundaries']:
        loops=[]
        for loop in face['loops']:
            cycle=loop['vertex_keys'];assert len(cycle)==len(set(cycle))==4
            assert loop['corner_positions_cm']==[vertices[k] for k in cycle]
            loops.append(tuple(sorted(_segment_key(vertices[a],vertices[b]) for a,b in zip(cycle,cycle[1:]+cycle[:1]))))
        faces.append((_plane_key(face['outward_material_mathematical_normal'],face['plane_constant_cm']),tuple(sorted(loops))))
    return dict(vertices=sorted(map(_point_key,vertices.values())),segments=sorted(segments),faces=sorted(faces))


def _near(left,right):
    import math
    if isinstance(left,(list,tuple)):
        assert isinstance(right,(list,tuple)) and len(left)==len(right)
        for a,b in zip(left,right):_near(a,b)
    else:
        assert math.isfinite(left) and math.isfinite(right) and math.isclose(left,right,rel_tol=0,abs_tol=1e-8),(left,right)


def qualify_geometry(row,before,source,archive,zstd):
    """Independent construction and complete native bundle comparison after IDs."""
    import math
    from fusion_archive import read_members
    from asm_records import inspect_asm
    from decode_brep import decode_topology
    from materialize_asm_literal_view import materialize_asm_literal_view
    boxes=qualify_native_sources(row,before,source)
    members=read_members(ROOT/archive,zstd);topologies={};literal_views={}
    groups={g['source_native_body_object_id']:g for g in row['source_groups']}
    assert len(groups)==row['source_group_count']==len(boxes) and set(groups)==set(boxes)
    sources={g['native_body_object_id']:g for g in source['source_groups']}
    output=[]
    for body,group in groups.items():
        native=sources[body];box=boxes[body]
        assert group['source_feature_object_id']==native['source_feature_object_id']
        assert group['history_blob_member']==native['history_blob_member'] and group['asm_body_index']==native['asm_body_index']
        for field in ('Shell_owned_result_anchor','qualified_historical_state','exact_API_handle_identity','current_or_final_geometry_identity'):
            assert group[field] is None
        proof=group['literal_source_prism'];origin=proof['qualified_body_origin']
        assert origin['initial_record_index']==group['asm_body_index']
        pair=origin['literal_pair'];assert pair['kind']=='body' and pair in proof['provenance']['literal_pair_aliases']
        assert pair['side1_inspection_record_index']==group['asm_body_index']
        assert origin['view_origin']['view_record_index']==proof['qualified_body_view_record_index']
        assert proof['qualified_historical_state'] is None and proof['source_before_Shell_identity'] is None
        member=native['history_blob_member']
        if member not in literal_views:
            literal_views[member]=materialize_asm_literal_view(members[member],parsed=inspect_asm(members[member]),state_slot=0,pointer_side=0)
        view=literal_views[member]
        assert proof['provenance']=={k:v for k,v in view.items() if k!='view_parsed'}
        source_topology=decode_topology(view['view_parsed'])
        source_nodes={n['index']:n for n in source_topology['nodes']}
        source_graph,=[g for g in source_topology['body_graphs'] if g['body_index']==proof['qualified_body_view_record_index']]
        assert len(source_graph['vertex_indices'])==8 and len(source_graph['edge_indices'])==12 and len(source_graph['face_indices'])==6
        assert source_nodes[source_graph['body_index']]['stored_entity_id']==native['binding']['stored_handle']
        positions=box['POINT_layer_positions_cm'];identity=proof['identity_provenance']
        bottom={int(k):v for k,v in identity['bottom'].items()};opposite={int(k):v for k,v in identity['opposite'].items()}
        assert set(bottom)==set(opposite)==set(box['native_point_object_ids'])
        assert set(bottom.values())|set(opposite.values())==set(source_graph['vertex_indices'])
        profile={r['native_entity_object_id']:r for r in native['profile_cache_correspondence']['source_curves']}
        source_lines={r['line_object_id']:r for r in native['native_profile_lines']}
        point_edges={}
        for curve in proof['native_profile_edge_correspondence']:
            line=source_lines[curve['native_line_object_id']]
            assert curve['native_curve_tag']==line['entity_tag']
            edge_id=curve['literal_edge_record_index']
            assert edge_id in source_graph['edge_indices']
            initial_edges={c['edge_record_index'] for c in profile[line['line_object_id']]['cached_coedge_candidates']}
            assert all(o['initial_record_index'] in initial_edges and o['view_record_index']==edge_id
                and o['view_origin'] in view['origin_map'] for o in curve['initial_to_literal_edge_origins'])
            for point in (line['start_point_id'],line['end_point_id']):point_edges.setdefault(point,[]).append(edge_id)
        assert set(point_edges)==set(bottom)
        for point,edge_ids in point_edges.items():
            assert len(edge_ids)==len(set(edge_ids))==2
            endpoint_sets=[{source_nodes[i]['start_vertex_index'],source_nodes[i]['end_vertex_index']} for i in edge_ids]
            assert endpoint_sets[0]&endpoint_sets[1]=={bottom[point]}
            connector=source_nodes[identity['connectors'].get(str(point),identity['connectors'].get(point))]
            assert {connector['start_vertex_index'],connector['end_vertex_index']}=={bottom[point],opposite[point]}
        fixed={}
        for vertex in proof['native_derived_vertices']:
            key=(vertex['native_sketch_point_object_id'],vertex['layer'])
            assert vertex['vertex_index']==(bottom if key[1]==0 else opposite)[key[0]]
            assert vertex['vertex_index'] not in fixed
            _near(vertex['derived_position_cm'],positions[key]);fixed[vertex['vertex_index']]=positions[key]
        assert len(fixed)==8
        _near(proof['derived_source_prism']['axis_aligned_bounds_cm']['minimum'],box['minimum_cm'])
        _near(proof['derived_source_prism']['axis_aligned_bounds_cm']['maximum'],box['maximum_cm'])
        face_cycles={f['face_index']:f['vertex_cycle'] for f in identity['face_vertex_cycles']}
        assert len(face_cycles)==6
        axis_by_face={}
        for face_id,cycle in face_cycles.items():
            choices=[(axis,side) for axis in range(3) for side,bounds in ((0,box['minimum_cm']),(1,box['maximum_cm']))
                if all(abs(fixed[v][axis]-bounds[axis])<1e-9 for v in cycle)]
            assert len(choices)==1;axis_by_face[face_id]=choices[0]
        assert {(r['face_index'],r['axis'],r['side']) for r in proof['source_FACE_axis_sides']}=={(f,*s) for f,s in axis_by_face.items()}
        selected=[source['selected_inputs'][i] for i in native['selected_input_indices']]
        faces=[s for s in selected if s['kind']=='Face'];removed=group['removed_face_operands']
        assert len(removed)==len(faces)
        source_edges={r['edge_index']:r['native_EDGE'] for r in proof['literal_straight_carrier_corroboration']}
        openings=[]
        for face in removed:
            selection=source['selected_inputs'][face['selected_input_index']]
            assert selection in faces and selection['counted_recipe']==face['recipe']
            assert face['operands']['whole_operation_replay_exact'] is True
            naming=face['complete_name_correspondence'];names={}
            for entry in naming['name_entries']:
                candidate,=entry['candidates']
                assert candidate['owner_kind']=='face' and candidate['body_graph_membership']==[proof['qualified_body_view_record_index']]
                names[entry['name_table_index']]=candidate['owner_record_index']
            assert len(names)==len(set(names.values()))==5
            chosen=names[face['operands']['face_name_index']]
            assert chosen==face['selected_literal_FACE_index']
            axis_side=axis_by_face[chosen]
            assert axis_side==(face['source_axis_side']['axis'],face['source_axis_side']['side'])
            openings.append(axis_side)
            boundaries=face['boundary_incidence'];assert len(boundaries)==4
            assert {r['edge_index'] for r in boundaries}==set(face['selected_source_loop']['edge_indices'])
            for route,operand in zip(boundaries,face['operands']['boundary_edge_operands']):
                assert route['operand_ordinal']==operand['operand_ordinal']
                assert set(route['FACE_indices'])=={names[i] for i in operand['face_name_indices']}
                edge=source_edges[route['edge_index']]
                assert route['raw_EDGE']==edge
                assert set(route['literal_endpoint_vertex_indices'])=={edge['start_vertex_index'],edge['end_vertex_index']}
                for vertex,endpoint in zip(route['literal_endpoint_vertex_indices'],operand['endpoint_operands']):
                    face_ids={names[i] for i in endpoint['face_name_indices']}
                    assert len(face_ids)==3 and all(vertex in face_cycles[f] for f in face_ids)
        reference=hollow_box_reference(box,source['settings']['inside_thickness_cm'],source['settings']['outside_thickness_cm'],openings)
        derived=group['derived_shell']
        for key,expected in (('source_bounds_cm',reference['source_bounds_cm']),('outer_bounds_cm',reference['outer_bounds_cm']),('cavity_bounds_cm',reference['inner_bounds_cm'])):
            _near([derived[key]['minimum'],derived[key]['maximum']],expected)
        assert derived['removed_source_axis_sides']==[dict(axis=a,side=s) for a,s in sorted(openings)]
        _near(derived['material_volume_cm3'],reference['volume_cm3'])
        _near(derived['boundary_integral_volume_cm3'],reference['volume_cm3'])
        for vertex in derived['vertices']:
            key=(vertex['role'].title(),tuple(vertex['corner_bits']))
            _near(vertex['position_cm'],reference['corner_positions_cm'][key])
        assert derived['counts']==dict(vertices=16,segments=24,planar_faces=reference['planar_face_count'],loops=12,
            connected_boundary_shells=1 if openings else 2)
        assert len(derived['semantic_edge_uses'])==24
        for uses in derived['semantic_edge_uses'].values():
            assert len(uses)==2 and uses[0]['start_vertex_key']==uses[1]['end_vertex_key'] and uses[0]['end_vertex_key']==uses[1]['start_vertex_key']
        member=native['history_blob_member']
        if member not in topologies:topologies[member]=decode_topology(inspect_asm(members[member]))
        topology=topologies[member];nodes={n['index']:n for n in topology['nodes']}
        bundle=native_cache_bundle(topology,native['asm_body_index']);mathematical=derived_geometry_bundle(derived)
        assert {key:bundle[key] for key in ('vertices','segments','faces')}==mathematical
        cache=group['collective_cache_geometry_corroboration']
        assert cache['semantic_role_to_native_entity_mapping'] is None
        for vertex in cache['native_vertices']:
            assert vertex['native_VERTEX']==nodes[vertex['vertex_index']]
            assert vertex['native_POINT']==nodes[vertex['native_VERTEX']['point_index']]
        for edge in cache['native_straight_segments']:
            assert edge['native_EDGE']==nodes[edge['edge_index']]
            assert edge['native_Line']==nodes[edge['native_EDGE']['curve_index']]
            assert edge['literal_parameter_multiplier']==(-1 if edge['native_EDGE']['is_reversed'] else 1)
        for face in cache['native_planar_boundaries']:
            assert face['native_FACE']==nodes[face['face_index']]
            assert face['native_Plane']==nodes[face['native_FACE']['surface_index']]
        output.append(dict(native_body_object_id=body,source_feature_object_id=native['source_feature_object_id'],
            history_blob_member=member,asm_body_index=native['asm_body_index'],
            native_ID_joins_before_arithmetic=True,source_vertices=8,derived_vertices=16,
            derived_segments=24,derived_planar_boundaries=reference['planar_face_count'],
            source_Line_count=4,source_POINT_count=4,removed_FACE_operands=len(removed),complete_FACE_names=5*len(removed),
            independent_source_bounds_cm=[box['minimum_cm'],box['maximum_cm']],
            independent_outer_bounds_cm=reference['outer_bounds_cm'],independent_cavity_bounds_cm=reference['inner_bounds_cm'],
            independently_derived_material_volume_cm3=reference['volume_cm3'],native_cache_counts=bundle['counts'],
            native_Line_endpoint_evaluations=bundle['endpoint_evaluations'],
            native_FACE_endpoint_plane_evaluations=bundle['FACE_endpoint_plane_evaluations'],
            scoped_Line_parameter_proofs=bundle['scoped_Line_parameter_proofs'],
            complete_nested_FACE_LOOP_segment_point_bundles_equal=True,
            semantic_role_to_native_entity_assignment=None,numerical_API_shape_corroboration=None))
    return output


SUMMARY=ATTACHMENT='shell_reconstruction'
EVIDENCE='shell-reconstruction-decoding.json'
SOURCE_EVIDENCE='shell-source-operand-decoding.json'
FROZEN_PRODUCTION={
    'decode_shell_source_operands.py':'e2d814c236805bf28ceff7b722c1bc2e79be807940238e1c36843bee5a36e5c0',
    'decode_shell_reconstruction.py':'d6029b18efab07bddd15fd981f254dbdba318fc3fbe32f57294e5a3dd1df1088',
    'decode_shell_box_geometry.py':'0ba1e856e74a4b4be1789903fd6a67654d4f7cdb8f30bbf0425932f2cb326429'}
FROZEN_EVIDENCE={
    EVIDENCE:'e5dd9ba4eed6024d076b45f315e22e7b811e086d5b8b2edcdd9c966890059111',
    SOURCE_EVIDENCE:'7e37f720b0fea39f41ec39f7458494670850e644ef17967ebe28682d1a404f04'}


def focused_evidence():
    import json
    from validate_rectangular_cache_evidence_integration import sha
    for name,expected in {**FROZEN_PRODUCTION,**FROZEN_EVIDENCE}.items():assert sha(ROOT/name)==expected
    reports=[json.loads((ROOT/name).read_text()) for name in (EVIDENCE,SOURCE_EVIDENCE)]
    for report in reports:
        for filename,expected in report['source_sha256'].items():assert sha(ROOT/filename)==expected,(filename,'Stale source evidence')
    current={s['archive']:s['expected_summary'] for s in reports[0]['samples'] if s['archive'] in FILES}
    source={s['archive']:s['expected_sources'] for s in reports[1]['samples'] if s['archive'] in FILES}
    assert set(current)==set(source)==set(FILES)
    for name in FILES:
        if name in FILES[:13]:
            one,=source[name]
            for row in current[name]['decoded']:assert row['native_source_provenance']==one
        else:
            assert not source[name] and not current[name]['decoded'] and not current[name]['unresolved']
    return current,source


def compare(before,current,archive,expected,sources,zstd):
    import copy
    from validate_rectangular_cache_evidence_integration import sha,digest,differences
    after=copy.deepcopy(current);old,=before['streams'];stream,=after['streams']
    assert old['member']==stream['member'] and SUMMARY not in old
    qualified=[];API=None
    if expected['decoded'] or expected['unresolved']:
        assert stream.pop(SUMMARY)==expected
        assert archive in FILES[:13]
        API=saved_API_controls(before,archive)
        for row in expected['decoded']:
            identity=row['feature_object_id']
            feature,=[f for f in stream['features'] if f['object_id']==identity]
            prior,=[f for f in old['features'] if f['object_id']==identity]
            assert feature['kind']==prior['kind']=='Shell' and ATTACHMENT not in prior
            assert feature.pop(ATTACHMENT)==row
            independent,=[s for s in sources if s['feature_object_id']==identity]
            qualified.extend(qualify_geometry(row,before,independent,archive,zstd))
        assert all(ATTACHMENT not in f for f in stream['features'])
    else:
        assert archive in FILES[13:] and SUMMARY not in stream
        assert all(ATTACHMENT not in f for f in stream['features'])
    assert after==before,(archive,'Unexpected prior-field change',differences(before,after))
    return dict(archive=archive,archive_sha256=sha(ROOT/archive),
        decoded_Shell_features=len(expected['decoded']),unresolved_Shell_features=len(expected['unresolved']),
        receiving_feature_annotations=len(expected['decoded']),source_BODY_groups=len(qualified),
        independent_groups=qualified,saved_API_controls=API,
        whole_output_unchanged=current==before,
        whole_output_exact_after_removing_only_new_summary_and_successful_owner_annotation=True,
        all_previous_settings_warnings_kinds_timeline_ASM_geometry_topology_and_placement_exact=True,
        baseline_output_sha256=digest(before),current_output_sha256=digest(current),
        qualified_difference_paths=differences(before,current))


def read_cache(path,side):
    import json
    value=json.loads(Path(path).read_text())
    assert value['baseline_commit']==BASELINE and value['files']==list(FILES)
    assert value['acquisition_main_calls']==15 and value['acquisition_passes']==1
    assert len(value[side])==15
    if side=='after':
        from validate_rectangular_cache_evidence_integration import sha
        assert value['production_source_sha256']==FROZEN_PRODUCTION
        assert value['main_source_sha256']==sha(ROOT/'decode_basics.py')
    return value[side]


def validate(zstd,baseline_cache=None,current_cache=None):
    import json
    from validate_rectangular_cache_evidence_integration import sha
    if baseline_cache:before=read_cache(baseline_cache,'before')
    else:
        from validate_history_cache_integration import baseline_outputs
        before=baseline_outputs(FILES,zstd,revision=BASELINE)
    if current_cache:current=read_cache(current_cache,'after')
    else:
        from decode_basics import decode_basics
        current=json.loads(json.dumps([decode_basics(ROOT/f,zstd) for f in FILES]))
    expected,sources=focused_evidence()
    assert len(before)==len(current)==15
    assert [r['file'] for r in before]==[str(ROOT/f) for f in FILES]==[r['file'] for r in current]
    rows=[compare(a,b,f,expected[f],sources[f],zstd) for a,b,f in zip(before,current,FILES)]
    groups=[g for r in rows for g in r['independent_groups']]
    summary=dict(saved_files=15,decoded_Shell_features=sum(r['decoded_Shell_features'] for r in rows),
        unresolved_Shell_features=sum(r['unresolved_Shell_features'] for r in rows),
        receiving_feature_annotations=sum(r['receiving_feature_annotations'] for r in rows),
        qualified_BODY_groups=len(groups),source_prism_vertices=sum(g['source_vertices'] for g in groups),
        derived_hollow_vertices=sum(g['derived_vertices'] for g in groups),
        derived_straight_segments=sum(g['derived_segments'] for g in groups),
        derived_planar_boundaries=sum(g['derived_planar_boundaries'] for g in groups),
        native_Line_endpoint_evaluations=sum(g['native_Line_endpoint_evaluations'] for g in groups),
        native_FACE_endpoint_plane_evaluations=sum(g['native_FACE_endpoint_plane_evaluations'] for g in groups),
        removed_FACE_operands=sum(g['removed_FACE_operands'] for g in groups),
        complete_FACE_name_groups=sum(g['complete_FACE_names'] for g in groups),
        native_FACE_loop_bundles=sum(g['native_cache_counts']['FACEs'] for g in groups),
        native_LOOP_bundles=sum(g['native_cache_counts']['loops'] for g in groups),
        native_COEDGE_uses=sum(g['native_cache_counts']['COEDGEs'] for g in groups),
        native_source_Lines=sum(g['source_Line_count'] for g in groups),native_source_POINTs=sum(g['source_POINT_count'] for g in groups),
        observed_negated_Line_parameter_edges=sum(p['observed_parameter_sign']==-1 for g in groups for p in g['scoped_Line_parameter_proofs']),
        observed_literal_Line_parameter_edges=sum(p['observed_parameter_sign']==1 for g in groups for p in g['scoped_Line_parameter_proofs']),
        saved_API_control_sets=sum(r['saved_API_controls'] is not None for r in rows),
        numerical_API_shape_controls=0,whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),
        unexpected_changes=0,comparator_baseline_main_calls=0 if baseline_cache else 15,
        comparator_current_main_calls=0 if current_cache else 15,live_API_calls=0)
    assert summary['decoded_Shell_features']==summary['receiving_feature_annotations']==13
    assert summary['unresolved_Shell_features']==0 and summary['qualified_BODY_groups']==15
    assert summary['source_prism_vertices']==120 and summary['derived_hollow_vertices']==240
    assert summary['derived_straight_segments']==360 and summary['derived_planar_boundaries']==168
    assert summary['native_FACE_loop_bundles']==168 and summary['native_LOOP_bundles']==180 and summary['native_COEDGE_uses']==720
    assert summary['native_Line_endpoint_evaluations']==720 and summary['native_FACE_endpoint_plane_evaluations']==1440
    assert summary['removed_FACE_operands']==12 and summary['complete_FACE_name_groups']==60
    assert summary['native_source_Lines']==summary['native_source_POINTs']==60
    assert summary['observed_negated_Line_parameter_edges']==133 and summary['observed_literal_Line_parameter_edges']==227
    assert summary['saved_API_control_sets']==13 and summary['whole_output_unchanged_controls']==2
    return dict(scope='Fixed saved Shell reconstruction integration, independent native source construction and complete collectively corroborated cache geometry; prior outputs preserved exactly',
        baseline_commit=BASELINE,files=list(FILES),summary=summary,samples=rows,
        fixed_manifest_acquisition=dict(baseline_main_calls=15,current_main_calls=15,baseline_passes=1,current_passes=1,
            interpreter='/usr/bin/python3',entrypoint='decode_basics.decode_basics(ROOT / filename, zstd_library)',
            fixed_order=list(FILES),scope='Original fixed acquisition, distinct from cached comparator zero-main execution'),
        cache_provenance={side:dict(path=str(Path(p).resolve()),sha256=sha(p)) for side,p in (
            ('baseline',baseline_cache),('current',current_cache)) if p},
        frozen_production_sha256=FROZEN_PRODUCTION,
        evidence_sha256={name:sha(ROOT/name) for name in (EVIDENCE,SOURCE_EVIDENCE)},
        saved_API_truth_sha256={name:sha(ROOT/name) for name in sorted({str(Path(f).parent/'ground_truth.json') for f in FILES[:13]})},
        source_sha256={name:sha(ROOT/name) for name in ('validate_shell_reconstruction_integration.py',
            'decode_shell_source_operands.py','decode_shell_reconstruction.py','decode_shell_box_geometry.py','decode_basics.py')},
        limitations=['Native source IDs and removed-FACE names/incidence precede source-derived geometric arithmetic.',
            'Complete native BODY geometry is compared collectively with nested FACE/LOOP/EDGE endpoint bundles; no semantic role is assigned to native ENTITY IDs by coordinates.',
            'The reversal-conditioned Line-parameter sign is observed only in the bounded saved Shell caches; no global EDGE traversal or API convention is inferred.',
            'Recorded API controls corroborate settings and source kind sequences; no numerical API Shell geometry or handle assignment was saved for these fixtures.',
            'RoundedOffset is retained as a literal setting; the actual bounded caches remain planar, with no assumed corner rounding.',
            'Literal views are not chronological source/current/final states; persistent topology and general Shell regeneration remain unresolved.'])


def main():
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache');p.add_argument('--current-cache');p.add_argument('--zstd-library')
    p.add_argument('--output',default='shell-reconstruction-integration.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z,a.baseline_cache,a.current_cache);Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['summary'],sort_keys=True))

if __name__=='__main__':main()
