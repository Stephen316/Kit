"""Fixed saved primitive Extrude reconstruction integration."""
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASELINE='b8a24f1'
FILES=(
    'extents-f0f33a9a605f/distance_positive.f3d',
    'extents-f0f33a9a605f/distance_negative.f3d',
    'extents-f0f33a9a605f/offset_positive.f3d',
    'extents-f0f33a9a605f/offset_negative.f3d',
    'extents-f0f33a9a605f/to_plane.f3d',
    'extents-f0f33a9a605f/to_plane_offset.f3d',
    'extents-f0f33a9a605f/from_plane.f3d',
    'extents-f0f33a9a605f/through_positive.f3d',
    'extents-f0f33a9a605f/through_negative.f3d',
    'extents-f0f33a9a605f/two_sided_mixed.f3d',
    'extents-f0f33a9a605f/taper.f3d',
    'models-b8a640dbddc6/symmetric_full.f3d',
    'models-b8a640dbddc6/symmetric_half.f3d',
    'models-b8a640dbddc6/two_sided.f3d',
    'holdouts-f8c508a73323/two_extrusions.f3d',
    'holdouts-f8c508a73323/drafted_extrusion.f3d',
    'thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d',
    'assembly-acc48a9dc05d/assembly.f3d',
    'placedprofiletrims-037ed41056a4/offset_xy_circle_lens.f3d',
    'placedprofiletrims-037ed41056a4/origin_xz_mixed_segment.f3d',
    'placedprofiletrims-037ed41056a4/angled_rectangle_overlap.f3d',
    'placement-c6ad25e75d60/placement.f3d',
    'meshseparates-41126250c03f/two_shells.f3d',
)


def native_reference(before,feature_id):
    """Construct selected native primitive and signed distances without cache input."""
    import math
    features=[f for s in before['streams'] for f in s.get('features',[])]
    feature,=[f for f in features if f['object_id']==feature_id]
    assert feature['kind']=='Extrude' and feature['operation']['kind']=='NewBody'
    profile,=feature['profile_selection'];loop,=profile['loops'];assert loop['is_outer'] is True
    sketch,=[s for s in features if s['kind']=='Sketch' and s['sketch_object_id']==profile['sketch_object_id']]
    matrix=sketch['placement']['sketch_to_component_matrix']
    assert len(matrix)==16 and matrix[12:]==[0.,0.,0.,1.]
    axes=[[matrix[4*i+j] for i in range(3)] for j in range(3)]
    for axis in axes:assert math.isclose(math.hypot(*axis),1,abs_tol=1e-9)
    for i,j in ((0,1),(0,2),(1,2)):assert abs(sum(a*b for a,b in zip(axes[i],axes[j])))<1e-9
    normal=axes[2]
    def transform(p):return [sum(matrix[4*i+j]*p[j] for j in range(3))+matrix[4*i+3] for i in range(3)]
    start=feature['start']
    if start['kind']=='ProfilePlane':offset=0.
    elif start['kind']=='Offset':offset=start['offset_cm']
    else:raise ValueError('Independent reference has no qualified FromEntity start')
    extent=feature['extent'];one=extent['side_one']
    if one['condition']!='Distance':raise ValueError('Independent reference requires Distance extent')
    distance=one['distance_cm'];taper=one['taper_angle_radians']
    if extent['mode']=='OneSided':low,high=sorted((offset,offset+distance))
    elif extent['mode']=='TwoSided':
        two=extent['side_two']
        assert two['condition']=='Distance' and two['taper_angle_radians']==0 and taper==0
        low,high=offset-two['distance_cm'],offset+distance
    elif extent['mode']=='Symmetric':
        assert taper==0
        half=distance/2 if extent['distance_convention']=='FullLength' else distance
        assert extent['distance_convention'] in ('FullLength','HalfLength')
        low,high=offset-half,offset+half
    else:raise ValueError('Independent reference extent mode unsupported')
    assert math.isfinite(low) and math.isfinite(high) and high>low
    geometry={g['object_id']:g for g in sketch['geometry']}
    selected=[geometry[c['entity_id']] for c in loop['curve_references']]
    for reference,curve in zip(loop['curve_references'],selected):
        assert curve['entity_tag']==reference['entity_tag'] and reference['secondary_tag']==0
        if 'opaqueTrimSelector' in reference:raise ValueError('Independent reference does not admit trimmed portions')
    common=dict(feature_object_id=feature_id,sketch_object_id=profile['sketch_object_id'],
        descriptor_object_id=profile['descriptor_object_id'],native_curve_ids=[c['object_id'] for c in selected],
        canonical_sketch_to_component_matrix=matrix,stored_direction_vector=extent['stored_direction_vector'],
        signed_start_offset_cm=offset,axial_interval_cm=[low,high],axis_direction_component=normal,
        current_or_historical_cache_identity=None,API_entity_assignment=None)
    if len(selected)==1 and selected[0]['kind']=='Circle':
        circle=selected[0];center=transform(circle['center_cm']);radius=circle['radius_cm']
        assert radius>0 and math.isfinite(radius)
        if taper:
            assert extent['mode']=='OneSided' and start['kind']=='ProfilePlane' and distance>0
        radii=[radius+(t-offset)*math.tan(taper) for t in (low,high)]
        assert min(radii)>0
        centers=[[c+t*n for c,n in zip(center,normal)] for t in (low,high)]
        bounds=[[],[]]
        for i in range(3):
            radial_factor=math.sqrt(max(0.,1-normal[i]**2))
            bounds[0].append(min(c[i]-r*radial_factor for c,r in zip(centers,radii)))
            bounds[1].append(max(c[i]+r*radial_factor for c,r in zip(centers,radii)))
        volume=math.pi*(high-low)*(radii[0]**2+radii[0]*radii[1]+radii[1]**2)/3
        return dict(**common,kind='Circle',center_component_cm=center,source_radius_cm=radius,
            end_centers_component_cm=centers,end_radii_cm=radii,axis_aligned_bounds_cm=bounds,volume_cm3=volume)
    if len(selected)!=4 or any(c['kind']!='Line' for c in selected) or taper:
        raise ValueError('Independent reference supports a whole Circle or untapered four-Line profile')
    pairs=[(c['start_point_id'],c['end_point_id']) for c in selected];point_ids=set(sum(([a,b] for a,b in pairs),[]))
    assert len(point_ids)==4
    adjacency={i:[b if a==i else a for a,b in pairs if i in (a,b)] for i in point_ids}
    assert set(map(len,adjacency.values()))=={2}
    cycle=[min(point_ids)]
    while len(cycle)<4:
        choices=[i for i in adjacency[cycle[-1]] if i not in cycle];assert choices
        cycle.append(min(choices))
    assert cycle[0] in adjacency[cycle[-1]]
    points={i:geometry[i]['position_cm'] for i in point_ids}
    assert all(geometry[i]['kind']=='Point' and points[i][2]==0 for i in point_ids)
    area=abs(sum(points[a][0]*points[b][1]-points[b][0]*points[a][1] for a,b in zip(cycle,cycle[1:]+cycle[:1])))/2
    assert area>0
    layer_vertices={(identity,layer):[v+t*n for v,n in zip(transform(p),normal)] for identity,p in points.items() for layer,t in enumerate((low,high))}
    bounds=[[min(p[i] for p in layer_vertices.values()) for i in range(3)],[max(p[i] for p in layer_vertices.values()) for i in range(3)]]
    return dict(**common,kind='FourLine',native_POINT_ids=sorted(points),native_POINT_cycle=cycle,
        POINT_layer_vertices_cm=layer_vertices,axis_aligned_bounds_cm=bounds,volume_cm3=area*(high-low))


def _near(left,right):
    import math
    if isinstance(left,(list,tuple)):
        assert isinstance(right,(list,tuple)) and len(left)==len(right)
        for a,b in zip(left,right):_near(a,b)
    else:assert math.isfinite(left) and math.isfinite(right) and math.isclose(left,right,rel_tol=0,abs_tol=1e-8),(left,right)


def qualify_sources(row,before,source):
    """Typed feature/Sketch/profile/anchor/map joins independently precede math."""
    assert row['native_source_provenance']==source
    features=[f for s in before['streams'] for f in s.get('features',[])]
    feature,=[f for f in features if f['object_id']==row['feature_object_id']]
    assert feature['kind']=='Extrude' and feature['object_id']==source['feature_object_id']
    for key in ('operation','start','extent'):assert source['settings'][key]==feature[key]
    assert source['settings']['is_solid'] is True
    for key in ('API_handle_identity','persistent_identity','qualified_historical_state'):assert source[key] is None
    native_groups=source['source_groups'];assert len(native_groups)==source['source_group_count']==1
    references={}
    for group in native_groups:
        assert group['source_feature_object_id']==feature['object_id']
        stream,=[s for s in before['streams'] if any(f['object_id']==feature['object_id'] for f in s.get('features',[]))]
        body=group['native_body_object_id']
        anchor,=[a for a in stream['body_selections']['body_anchors'] if a['object_id']==group['body_anchor_object_id']]
        assert anchor['source_owner_object_id']==feature['object_id'] and anchor['native_body_object_id']==body
        mapping,=[m for m in stream['body_blob_bindings']['decoded'] if m['mapping_record_object_id']==group['mapping_record_object_id']]
        binding,=[b for b in mapping['bindings'] if b['native_body_object_id']==body]
        assert binding['stored_handle']==group['binding']['stored_handle']
        assert binding['asm_body_index']==group['asm_body_index']
        assert mapping['history_blob_member']==group['history_blob_member']
        profile,=feature['profile_selection']
        assert group['native_profile_selection']['profile_descriptor_object_id']==profile['descriptor_object_id']
        sketch,=[s for s in features if s['kind']=='Sketch' and s['sketch_object_id']==profile['sketch_object_id']]
        assert group['source_sketch_frame_provenance']['canonical_placement']==sketch['placement']
        assert group['stored_direction_vector']==feature['extent']['stored_direction_vector']
        reference=native_reference(before,feature['object_id'])
        assert group['native_profile_kind']==reference['kind']
        if reference['kind']=='Circle':
            circle,=group['native_profile_circles']
            assert circle['circle_object_id']==reference['native_curve_ids'][0]
        else:assert {line['line_object_id'] for line in group['native_profile_lines']}==set(reference['native_curve_ids'])
        references[body]=reference
    return references


def saved_API_bounds(archive,feature,reference):
    """Compare captured single-feature complete result bounds after native joins."""
    import json
    rectangle=archive=='thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d'
    if rectangle:
        truth_path='thinextrudes-c1632bcb5efe/ground_truth.json'
        truth=json.loads((ROOT/truth_path).read_text());sample,=[s for s in truth['samples'] if s['file']==Path(archive).name]
        body,=sample['result_bodies'];bounds=[body['bounds_min_cm'],body['bounds_max_cm']]
        _near(reference['axis_aligned_bounds_cm'],bounds);_near(reference['volume_cm3'],body['volume_cm3'])
        assert (body['face_count'],body['edge_count'],body['vertex_count'])==(6,12,8)
        return dict(truth_file=truth_path,feature_object_id=feature['object_id'],actual_API_body_bounds_cm=bounds,
            independently_derived_bounds_cm=reference['axis_aligned_bounds_cm'],actual_API_volume_cm3=body['volume_cm3'],
            independently_derived_volume_cm3=reference['volume_cm3'],native_identity_joins_precede_comparison=True,
            API_BODY_entity_assignment=None,scope='Complete result bounds/volume/counts corroborated after native joins; no API ENTITY assigned by coordinates')
    if archive not in {'extents-f0f33a9a605f/'+name+'.f3d' for name in (
            'distance_positive','distance_negative','offset_positive','offset_negative','taper')}:return None
    truth_path='extents-f0f33a9a605f/ground_truth.json'
    truth=json.loads((ROOT/truth_path).read_text());sample,=[s for s in truth['samples'] if s['file']==Path(archive).name]
    assert feature['name']==sample['name'] and feature['operation']['kind']=='NewBody'
    _near(reference['axis_aligned_bounds_cm'],sample['body_bounds_cm'])
    return dict(truth_file=truth_path,feature_object_id=feature['object_id'],actual_API_body_bounds_cm=sample['body_bounds_cm'],
        independently_derived_bounds_cm=reference['axis_aligned_bounds_cm'],
        native_identity_joins_precede_comparison=True,API_BODY_entity_assignment=None,
        scope='Complete independently captured root result bounds corroborated after native feature/BODY/Sketch joins; bounds never select identity')


SUMMARY=ATTACHMENT='extrusion_reconstruction'
EVIDENCE='extrusion-reconstruction-decoding.json'
SOURCE_EVIDENCE='extrusion-source-operand-decoding.json'
FROZEN_PRODUCTION={
    'decode_extrusion_source_operands.py':'9f45976340deef3a4d71f6c999e360841c88d82e129c9754e00e38e535b74b40',
    'decode_extrusion_reconstruction.py':'95647f20dd3e5d599c9567922facee5f021568e21c7d5474a222500929c5496f',
    'decode_circular_extrusion_geometry.py':'77fe57a5a7b50cb7b2d3add0dd738b84b13b3501cf87893cd60205fc00ffe6d1'}
FROZEN_EVIDENCE={EVIDENCE:'0fc5600236c9fe94ea5b319417175fa097626d680d6deb9dc1ad47741b588ab7',SOURCE_EVIDENCE:'634d388bf69a289f15339b97eb035a5769e32eb9908446d46ebf62a6eda864bc'}


def focused_evidence():
    import json
    from validate_rectangular_cache_evidence_integration import sha
    for name,expected in {**FROZEN_PRODUCTION,**FROZEN_EVIDENCE}.items():assert sha(ROOT/name)==expected
    reports=[json.loads((ROOT/name).read_text()) for name in (EVIDENCE,SOURCE_EVIDENCE)]
    for report in reports:
        for name,expected in report['source_sha256'].items():assert sha(ROOT/name)==expected,(name,'Stale focused source evidence')
    summaries={s['archive']:s['expected_summary'] for s in reports[0]['samples'] if s['archive'] in FILES}
    sources={s['archive']:s for s in reports[1]['samples'] if s['archive'] in FILES}
    assert set(summaries)==set(sources)==set(FILES)
    for archive in FILES:
        for row in summaries[archive]['decoded']:
            independent,=[s for s in sources[archive]['expected_sources'] if s['feature_object_id']==row['feature_object_id']]
            assert row['native_source_provenance']==independent
    return summaries,sources


def _point_key(p):
    assert len(p)==3
    return tuple(round(x,8) for x in p)


def _edge_key(a,b):return tuple(sorted((_point_key(a),_point_key(b))))


def qualify_geometry(row,before,source,archive,zstd):
    """Independent whole native primitive equations after typed BODY joins."""
    import math
    from fusion_archive import read_members
    from asm_records import inspect_asm
    from decode_brep import decode_topology
    references=qualify_sources(row,before,source)
    group,=source['source_groups'];reference=references[group['native_body_object_id']]
    assert row['source_native_body_object_id']==group['native_body_object_id']
    assert row['history_blob_member']==group['history_blob_member'] and row['asm_body_index']==group['asm_body_index']
    assert row['binding']==group['binding']
    for key in ('source_to_cache_entity_mapping','exact_API_handle_identity','qualified_historical_state','current_or_final_geometry_identity'):
        assert row[key] is None
    _near(reference['axis_direction_component'],group['stored_direction_vector'])
    members=read_members(ROOT/archive,zstd);topology=decode_topology(inspect_asm(members[group['history_blob_member']]))
    nodes={n['index']:n for n in topology['nodes']};graph,=[g for g in topology['body_graphs'] if g['body_index']==group['asm_body_index']]
    assert graph['body_transform_is_identity'] is True
    assert nodes[graph['body_index']]['stored_entity_id']==group['binding']['stored_handle']
    circular=reference['kind']=='Circle'
    expected=dict(lump=1,shell=1,face=3,loop=4,coedge=4,edge=2,vertex=2) if circular else dict(lump=1,shell=1,face=6,loop=6,coedge=24,edge=12,vertex=8)
    assert graph['counts']==expected
    assert all(len(graph[k+'_indices'])==len(set(graph[k+'_indices']))==v for k,v in expected.items())
    # Retain nested ownership and complete coedge cycles, rather than flattening coordinates.
    loops={};all_coedges=set()
    for fid in graph['face_indices']:
        face=nodes[fid];lid=face['first_loop_index'];owned=[]
        while lid is not None:
            assert lid not in loops and nodes[lid]['face_index']==fid
            loop=nodes[lid];first=loop['first_coedge_index'];cid=first;cycle=[]
            while True:
                assert cid not in all_coedges;all_coedges.add(cid);cycle.append(cid)
                c=nodes[cid];assert c['loop_index']==lid and c['edge_index'] in graph['edge_indices']
                assert nodes[c['next_coedge_index']]['previous_coedge_index']==cid
                assert nodes[c['previous_coedge_index']]['next_coedge_index']==cid
                partner=nodes[c['partner_index']]
                assert partner['partner_index']==cid and partner['index']!=cid and partner['edge_index']==c['edge_index']
                cid=c['next_coedge_index']
                if cid==first:break
            assert len(cycle)==(1 if circular else 4)
            loops[lid]=cycle;owned.append(lid);lid=loop['next_loop_index']
        assert len(owned) in ((1,2) if circular else (1,))
    assert set(loops)==set(graph['loop_indices']) and all_coedges==set(graph['coedge_indices'])
    positions={v:nodes[nodes[v]['point_index']]['raw_origin'] for v in graph['vertex_indices']}
    for eid in graph['edge_indices']:
        e=nodes[eid];uses=[c for c in all_coedges if nodes[c]['edge_index']==eid]
        assert len(uses)==2 and e['first_coedge_index'] in uses
        assert len({nodes[nodes[c]['loop_index']]['face_index'] for c in uses})==2
        for v in (e['start_vertex_index'],e['end_vertex_index']):
            assert v in positions and nodes[v]['first_edge_index'] in [i for i in graph['edge_indices'] if v in (nodes[i]['start_vertex_index'],nodes[i]['end_vertex_index'])]
    model=row['derived_geometry'];cache=row['native_cache_geometry_corroboration']
    assert cache['counts']==graph['counts']
    endpoint_checks=cap_checks=lateral_checks=line_checks=plane_checks=0
    if circular:
        _near(model['source_circle']['center_cm'],reference['center_component_cm'])
        _near(model['source_circle']['radius_cm'],reference['source_radius_cm'])
        _near(model['source_circle']['unit_axis'],reference['axis_direction_component'])
        _near([s['axial_distance_cm'] for s in model['axial_stations']],reference['axial_interval_cm'])
        _near([s['center_cm'] for s in model['axial_stations']],reference['end_centers_component_cm'])
        _near([s['radius_cm'] for s in model['axial_stations']],reference['end_radii_cm'])
        _near([model['component_axis_aligned_bounds_cm']['minimum'],model['component_axis_aligned_bounds_cm']['maximum']],reference['axis_aligned_bounds_cm'])
        _near(model['volume_cm3'],reference['volume_cm3'])
        assert model['source_to_cache_entity_mapping'] is None and cache['semantic_cap_to_native_ENTITY_mapping'] is None
        center=reference['center_component_cm'];axis=reference['axis_direction_component']
        cap_faces={i for i in graph['face_indices'] if nodes[nodes[i]['surface_index']]['kind']=='plane-surface'}
        lateral_faces=set(graph['face_indices'])-cap_faces;assert len(cap_faces)==2 and len(lateral_faces)==1
        lateral_id,=lateral_faces;side=nodes[nodes[lateral_id]['surface_index']]
        assert side['kind']=='cone-surface'
        curves=[]
        for e in graph['edge_indices']:
            edge=nodes[e];curve=nodes[edge['curve_index']]
            assert curve['kind']=='ellipse-curve' and edge['start_vertex_index']==edge['end_vertex_index']
            origin=curve['raw_origin'];normal=curve['normal'];u=curve['stored_reference_axis'];radius=curve['raw_major_radius']
            _near(radius,curve['raw_minor_radius']);assert radius>0
            _near(math.hypot(*normal),1.);_near(math.hypot(*u),radius)
            _near(sum(a*b for a,b in zip(normal,u)),0.)
            _near(abs(sum(a*b for a,b in zip(normal,axis))),1.)
            _near(abs(edge['end_parameter']-edge['start_parameter']),2*math.pi)
            v=[normal[1]*u[2]-normal[2]*u[1],normal[2]*u[0]-normal[0]*u[2],normal[0]*u[1]-normal[1]*u[0]]
            for t in (edge['start_parameter'],edge['end_parameter']):
                _near([o+math.cos(t)*a+math.sin(t)*b for o,a,b in zip(origin,u,v)],positions[edge['start_vertex_index']]);endpoint_checks+=1
            uses=[nodes[c] for c in all_coedges if nodes[c]['edge_index']==e]
            incident={nodes[c['loop_index']]['face_index'] for c in uses};cap,=incident&cap_faces
            assert lateral_id in incident
            plane=nodes[nodes[cap]['surface_index']]
            _near(math.hypot(*plane['normal']),1.)
            _near(abs(sum(n*p for n,p in zip(plane['normal'],normal))),1.)
            _near(sum(n*(p-o) for n,p,o in zip(plane['normal'],origin,plane['raw_origin'])),0.);cap_checks+=1
            curves.append(origin+[radius])
        expected_caps=[c+[r] for c,r in zip(reference['end_centers_component_cm'],reference['end_radii_cm'])]
        _near(sorted(curves),sorted(expected_caps))
        analytic=side['analytic_surface'];assert analytic['kind'] in ('Cylinder','Cone')
        native_axis=analytic['axis'];_near(math.hypot(*native_axis),1.)
        axis_sign=sum(a*b for a,b in zip(native_axis,axis));_near(abs(axis_sign),1.)
        delta=[p-c for p,c in zip(analytic['raw_origin'],center)];height=sum(p*n for p,n in zip(delta,axis))
        _near([p-height*n for p,n in zip(delta,axis)],[0.,0.,0.])
        slope=math.tan(analytic.get('stored_signed_half_angle_radians',0.))*axis_sign
        for station,radius in zip(reference['axial_interval_cm'],reference['end_radii_cm']):
            _near(analytic['raw_radius']+slope*(station-height),radius);lateral_checks+=1
        expected_kind='Cylinder' if reference['end_radii_cm'][0]==reference['end_radii_cm'][1] else 'Cone'
        assert analytic['kind']==model['lateral_carrier']['kind']==expected_kind
        assert cache['native_lateral_FACE']==nodes[lateral_id] and cache['native_lateral_carrier']==side
        for native in cache['native_boundary_circles']:
            assert native['native_EDGE']==nodes[native['native_EDGE']['index']]
            assert native['native_Circle']==nodes[native['native_EDGE']['curve_index']]
            assert native['native_cap_FACE']==nodes[native['native_cap_FACE']['index']]
            assert native['native_cap_Plane']==nodes[native['native_cap_FACE']['surface_index']]
    else:
        assert model['kind']=='RectangularPrism' and model['source_to_cache_entity_mapping'] is None
        _near(model['axial_stations_cm'],reference['axial_interval_cm'])
        assert model['native_profile_point_cycle']==reference['native_POINT_cycle']
        for vertex in model['constructed_vertices']:
            key=(vertex['native_sketch_point_object_id'],vertex['layer'])
            _near(vertex['derived_position_cm'],reference['POINT_layer_vertices_cm'][key])
        prism=model['prism'];_near(prism['volume_cm3'],reference['volume_cm3'])
        _near([prism['axis_aligned_bounds_cm']['minimum'],prism['axis_aligned_bounds_cm']['maximum']],reference['axis_aligned_bounds_cm'])
        assert sorted(map(_point_key,positions.values()))==sorted(map(_point_key,reference['POINT_layer_vertices_cm'].values()))
        native_segments={}
        for eid in graph['edge_indices']:
            edge=nodes[eid];curve=nodes[edge['curve_index']];assert curve['kind']=='straight-curve'
            sign=-1 if edge['is_reversed'] else 1
            for name in ('start','end'):
                _near([o+sign*edge[name+'_parameter']*d for o,d in zip(curve['raw_origin'],curve['direction'])],positions[edge[name+'_vertex_index']]);endpoint_checks+=1
            native_segments[eid]=_edge_key(positions[edge['start_vertex_index']],positions[edge['end_vertex_index']]);line_checks+=1
        assert sorted(native_segments.values())==sorted(_edge_key(s['start_position_cm'],s['end_position_cm']) for s in prism['segments'])
        actual_faces=[]
        for fid in graph['face_indices']:
            face=nodes[fid];plane=nodes[face['surface_index']];assert plane['kind']=='plane-surface'
            lid,=[i for i in loops if nodes[i]['face_index']==fid]
            edges=[nodes[nodes[c]['edge_index']] for c in loops[lid]]
            corners={v for e in edges for v in (e['start_vertex_index'],e['end_vertex_index'])}
            assert len(corners)==4
            for v in corners:_near(sum(n*(p-o) for n,p,o in zip(plane['normal'],positions[v],plane['raw_origin'])),0.)
            actual_faces.append(tuple(sorted(native_segments[e['index']] for e in edges)));plane_checks+=1
        expected_faces=[]
        for f in prism['planar_quadrilateral_boundaries']:
            cycle=f['corner_positions_cm'];assert len(cycle)==4
            expected_faces.append(tuple(sorted(_edge_key(a,b) for a,b in zip(cycle,cycle[1:]+cycle[:1]))))
        assert sorted(actual_faces)==sorted(expected_faces)
        assert cache['semantic_role_to_native_ENTITY_mapping'] is None
        for e in cache['native_straight_segments']:
            assert e['native_EDGE']==nodes[e['native_EDGE']['index']]
            assert e['native_Line']==nodes[e['native_EDGE']['curve_index']]
    return dict(feature_object_id=row['feature_object_id'],native_body_object_id=group['native_body_object_id'],
        native_profile_kind=reference['kind'],derived_primitive_kind=expected_kind if circular else 'RectangularPrism',
        native_ID_joins_precede_arithmetic=True,cache_counts=expected,independent_axial_interval_cm=reference['axial_interval_cm'],
        independent_bounds_cm=reference['axis_aligned_bounds_cm'],independent_volume_cm3=reference['volume_cm3'],
        native_endpoint_evaluations=endpoint_checks,complete_cap_circle_equations=cap_checks,
        lateral_station_radius_equations=lateral_checks,native_Line_equations=line_checks,native_Plane_equations=plane_checks,
        complete_nested_topology_and_geometry_bundles_corroborated=True,
        semantic_to_native_ENTITY_assignment=None,API_ENTITY_assignment=None)


def compare(before,current,archive,expected,source_evidence,zstd):
    import copy
    from validate_rectangular_cache_evidence_integration import sha,digest,differences
    after=copy.deepcopy(current);old,=before['streams'];stream,=after['streams']
    assert old['member']==stream['member'] and SUMMARY not in old
    native_features={f['object_id']:f for f in old.get('features',[]) if f['kind']=='Extrude'}
    source_rows={r['feature_object_id']:r for r in source_evidence['expected_sources']}
    source_failures={r['feature_object_id']:r for r in source_evidence['expected_unresolved']}
    assert len(source_rows)==len(source_evidence['expected_sources'])
    assert len(source_failures)==len(source_evidence['expected_unresolved'])
    decoded={r['feature_object_id']:r for r in expected['decoded']};failures={r['feature_object_id']:r for r in expected['unresolved']}
    assert len(decoded)==len(expected['decoded']) and len(failures)==len(expected['unresolved'])
    assert not (set(decoded)&set(failures)) and set(decoded)|set(failures)==set(native_features)
    assert not (set(source_rows)&set(source_failures)) and set(source_rows)|set(source_failures)==set(native_features)
    assert set(decoded)<=set(source_rows)
    for identity,failure in source_failures.items():assert failures[identity]==failure
    if native_features:assert stream.pop(SUMMARY)==expected
    else:assert SUMMARY not in stream and not expected['decoded'] and not expected['unresolved']
    independent_sources={}
    for identity,source in source_rows.items():
        references=qualify_sources(dict(feature_object_id=identity,native_source_provenance=source),before,source)
        independent_sources[identity]=references
    proofs=[];API=[]
    for identity,row in decoded.items():
        feature,=[f for f in stream['features'] if f['object_id']==identity]
        assert feature['kind']=='Extrude' and ATTACHMENT not in native_features[identity]
        assert feature.pop(ATTACHMENT)==row
        proof=qualify_geometry(row,before,source_rows[identity],archive,zstd);proofs.append(proof)
        reference,=independent_sources[identity].values()
        observed=saved_API_bounds(archive,native_features[identity],reference)
        if observed is not None:API.append(observed)
    assert all(ATTACHMENT not in f for f in stream.get('features',[]))
    assert after==before,(archive,'Unexpected prior-output change',differences(before,after))
    return dict(archive=archive,archive_sha256=sha(ROOT/archive),
        decoded_Extrude_features=len(decoded),unresolved_Extrude_features=len(failures),
        receiving_feature_annotations=len(decoded),independent_native_source_candidates=len(source_rows),
        source_operand_failures=len(source_failures),source_candidates_without_successful_cache_corroboration=sorted(set(source_rows)-set(decoded)),
        successful_primitive_geometry_proofs=proofs,saved_API_geometry_controls=API,
        whole_output_unchanged=before==current,
        whole_output_exact_after_removing_only_new_summary_and_successful_owner_annotations=True,
        all_previous_settings_warnings_kinds_timeline_ASM_geometry_topology_and_placement_exact=True,
        baseline_output_sha256=digest(before),current_output_sha256=digest(current),
        qualified_difference_paths=differences(before,current))


def read_cache(path,side):
    import json
    from validate_rectangular_cache_evidence_integration import sha
    data=json.loads(Path(path).read_text())
    assert data['baseline_commit']==BASELINE and data['files']==list(FILES)
    assert data['acquisition_main_calls']==23 and data['acquisition_passes']==1
    assert len(data[side])==23
    if side=='after':
        assert data['production_source_sha256']==FROZEN_PRODUCTION
        assert data['main_source_sha256']==sha(ROOT/'decode_basics.py')
    return data[side]


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
    assert len(before)==len(current)==23
    assert [r['file'] for r in before]==[str(ROOT/f) for f in FILES]==[r['file'] for r in current]
    rows=[compare(a,b,f,expected[f],sources[f],zstd) for a,b,f in zip(before,current,FILES)]
    proofs=[p for r in rows for p in r['successful_primitive_geometry_proofs']]
    API=[p for r in rows for p in r['saved_API_geometry_controls']]
    summary=dict(saved_files=23,decoded_Extrude_features=sum(r['decoded_Extrude_features'] for r in rows),
        unresolved_Extrude_features=sum(r['unresolved_Extrude_features'] for r in rows),
        receiving_feature_annotations=sum(r['receiving_feature_annotations'] for r in rows),
        independent_native_source_candidates=sum(r['independent_native_source_candidates'] for r in rows),
        source_operand_failures=sum(r['source_operand_failures'] for r in rows),
        source_candidates_without_successful_cache_corroboration=sum(len(r['source_candidates_without_successful_cache_corroboration']) for r in rows),
        reconstructed_cylinders=sum(p['derived_primitive_kind']=='Cylinder' for p in proofs),
        reconstructed_frusta=sum(p['derived_primitive_kind']=='Cone' for p in proofs),
        reconstructed_rectangular_prisms=sum(p['derived_primitive_kind']=='RectangularPrism' for p in proofs),
        native_BODY_groups=len(proofs),native_FACE_count=sum(p['cache_counts']['face'] for p in proofs),
        native_LOOP_count=sum(p['cache_counts']['loop'] for p in proofs),
        native_COEDGE_count=sum(p['cache_counts']['coedge'] for p in proofs),
        native_EDGE_count=sum(p['cache_counts']['edge'] for p in proofs),
        native_VERTEX_count=sum(p['cache_counts']['vertex'] for p in proofs),
        native_endpoint_evaluations=sum(p['native_endpoint_evaluations'] for p in proofs),
        complete_cap_circle_equations=sum(p['complete_cap_circle_equations'] for p in proofs),
        lateral_station_radius_equations=sum(p['lateral_station_radius_equations'] for p in proofs),
        native_Line_equations=sum(p['native_Line_equations'] for p in proofs),
        native_Plane_equations=sum(p['native_Plane_equations'] for p in proofs),
        independent_saved_API_bound_controls=len(API),independent_saved_API_volume_controls=sum('actual_API_volume_cm3' in p for p in API),
        whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),unexpected_changes=0,
        comparator_baseline_main_calls=0 if baseline_cache else 23,
        comparator_current_main_calls=0 if current_cache else 23,live_API_calls=0)
    assert summary['decoded_Extrude_features']==summary['receiving_feature_annotations']==13
    assert summary['unresolved_Extrude_features']==14 and summary['independent_native_source_candidates']==18
    assert summary['source_operand_failures']==9 and summary['source_candidates_without_successful_cache_corroboration']==5
    assert summary['reconstructed_cylinders']==10 and summary['reconstructed_frusta']==2 and summary['reconstructed_rectangular_prisms']==1
    assert summary['native_FACE_count']==42 and summary['native_LOOP_count']==54 and summary['native_COEDGE_count']==72
    assert summary['native_EDGE_count']==36 and summary['native_VERTEX_count']==32
    assert summary['native_endpoint_evaluations']==72 and summary['complete_cap_circle_equations']==24
    assert summary['lateral_station_radius_equations']==24 and summary['native_Line_equations']==12 and summary['native_Plane_equations']==6
    assert summary['independent_saved_API_bound_controls']==6 and summary['independent_saved_API_volume_controls']==1
    assert summary['whole_output_unchanged_controls']==2
    return dict(scope='Fixed ordinary solid Extrude reconstruction with independently derived native primitive controls and complete typed stored-cache corroboration; unsupported controls, modified caches and frames remain explicit',
        baseline_commit=BASELINE,files=list(FILES),summary=summary,samples=rows,
        fixed_manifest_acquisition=dict(baseline_main_calls=23,current_main_calls=23,baseline_passes=1,current_passes=1,
            interpreter='/usr/bin/python3',entrypoint='decode_basics.decode_basics(ROOT / filename, zstd_library)',
            fixed_order=list(FILES),scope='Original fixed acquisition, distinct from cached comparator zero-main execution'),
        cache_provenance={side:dict(path=str(Path(p).resolve()),sha256=sha(p)) for side,p in (
            ('baseline',baseline_cache),('current',current_cache)) if p},
        frozen_production_sha256=FROZEN_PRODUCTION,
        evidence_sha256={name:sha(ROOT/name) for name in (EVIDENCE,SOURCE_EVIDENCE)},
        saved_API_truth_sha256={name:sha(ROOT/name) for name in (
            'extents-f0f33a9a605f/ground_truth.json','thinextrudes-c1632bcb5efe/ground_truth.json')},
        source_sha256={name:sha(ROOT/name) for name in ('validate_extrusion_reconstruction_integration.py',
            'decode_extrusion_source_operands.py','decode_extrusion_reconstruction.py','decode_circular_extrusion_geometry.py','decode_basics.py')},
        limitations=['Source profile/Sketch/feature/anchor/BODY/mapping identities are fixed before numerical primitive/cache comparison.',
            'Complete analytic coefficients and nested finite boundary topology corroborate geometry collectively; no mathematical role selects or assigns native ENTITY identity.',
            'Six saved complete result bounds and one volume corroborate after native joins; no API handle or vertex assignment by coordinates.',
            'Five qualified source candidates lack successful cache/frame corroboration and remain unresolved; deriving their source primitive is not counted as reconstruction success.',
            'From/ToEntity, Boolean operations, trimmed source portions and unqualified assembly-frame direction relationships remain explicit unsupported cases.',
            'No current/final/historical/persistent geometry identity or native regeneration is established. Separate root translated-source holdout is outside this fixed manifest and all acquisition counts.'])


def main():
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache');p.add_argument('--current-cache');p.add_argument('--zstd-library')
    p.add_argument('--output',default='extrusion-reconstruction-integration.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z,a.baseline_cache,a.current_cache);Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['summary'],sort_keys=True))

if __name__=='__main__':main()
