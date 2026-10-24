"""Fixed selected construction-plane Extrude reconstruction integration."""
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASELINE='f33f478'
FILES=(
    'extents-f0f33a9a605f/to_plane.f3d',
    'extents-f0f33a9a605f/to_plane_offset.f3d',
    'extents-f0f33a9a605f/from_plane.f3d',
    'extents-f0f33a9a605f/distance_positive.f3d',
    'extents-f0f33a9a605f/offset_negative.f3d',
    'extents-f0f33a9a605f/two_sided_mixed.f3d',
    'holes-926347c1eaa8/to_bottom.f3d',
    'placement-c6ad25e75d60/placement.f3d',
)

from validate_extrusion_reconstruction_integration import _near


def plane_reference(before,feature_id):
    """Intersect the selected typed plane with the native Circle axis, without cache input."""
    import math
    features=[f for s in before['streams'] for f in s.get('features',[])]
    feature,=[f for f in features if f['object_id']==feature_id]
    assert feature['kind']=='Extrude' and feature['operation']['kind']=='NewBody'
    assert feature['extent']['mode']=='OneSided'
    side=feature['extent']['side_one'];assert side['taper_angle_radians']==0
    if feature['start']['kind']=='FromEntity':
        role='FromEntity';operand=feature['start'];assert side['condition']=='Distance'
    else:
        assert feature['start']['kind']=='ProfilePlane' and side['condition']=='ToEntity'
        role='ToEntity';operand=side
    selection=operand['selection'];assert selection['selection_object_id']==operand['selection_record_object_id']
    entity=selection['entity'];assert entity['kind']=='ConstructionPlane'
    plane,=[p for p in features if p['object_id']==entity['feature_object_id']]
    assert plane['kind']=='ConstructionPlane' and plane['plane_object_id']==entity['object_id']
    assert plane['component_object_id']==feature['component_object_id']
    assert plane['origin_cm']==entity['origin_cm'] and plane['normal']==entity['normal']
    profile,=feature['profile_selection'];loop,=profile['loops'];curve_ref,=loop['curve_references']
    assert loop['is_outer'] is True and curve_ref['entity_kind']=='Circle'
    sketch,=[s for s in features if s['kind']=='Sketch' and s['sketch_object_id']==profile['sketch_object_id']]
    assert sketch['component_object_id']==plane['component_object_id']
    circle,=[g for g in sketch['geometry'] if g['object_id']==curve_ref['entity_id']]
    assert circle['kind']=='Circle' and circle['entity_tag']==curve_ref['entity_tag'] and curve_ref['secondary_tag']==0
    matrix=sketch['placement']['sketch_to_component_matrix'];assert len(matrix)==16
    axis=[matrix[2],matrix[6],matrix[10]]
    center=[sum(matrix[4*i+j]*circle['center_cm'][j] for j in range(3))+matrix[4*i+3] for i in range(3)]
    _near(axis,feature['extent']['stored_direction_vector']);_near(math.hypot(*axis),1.)
    normal=plane['normal'];origin=plane['origin_cm'];_near(math.hypot(*normal),1.)
    alignment=sum(n*d for n,d in zip(normal,axis));_near(alignment,1.)
    # Identity and plane role are already fixed by native refs; coordinates solve only the crossing.
    crossing=sum(n*(p-c) for n,p,c in zip(normal,origin,center))/alignment
    offset=operand['offset_cm']
    stations=[crossing+offset,crossing+offset+side['distance_cm']] if role=='FromEntity' else [0.,crossing+offset]
    assert stations[1]>stations[0]
    radius=circle['radius_cm'];assert radius>0
    centers=[[c+t*n for c,n in zip(center,axis)] for t in stations]
    radial=[math.sqrt(max(0.,1-n*n)) for n in axis]
    bounds=[[min(p[i]-radius*radial[i] for p in centers) for i in range(3)],
            [max(p[i]+radius*radial[i] for p in centers) for i in range(3)]]
    return dict(feature_object_id=feature_id,selection_role=role,
        selection_record_object_id=selection['selection_object_id'],descriptor_object_id=selection['descriptor_object_id'],
        terminal_object_id=selection['terminal_object_id'],plane_object_id=entity['object_id'],plane_feature_object_id=plane['object_id'],
        native_sketch_object_id=sketch['sketch_object_id'],native_Circle_object_id=circle['object_id'],
        component_object_id=plane['component_object_id'],plane_origin_cm=origin,plane_normal=normal,
        profile_center_component_cm=center,axis_direction_component=axis,radius_cm=radius,
        independent_plane_crossing_cm=crossing,selected_offset_cm=offset,axial_stations_cm=stations,
        cap_centers_component_cm=centers,independent_bounds_cm=bounds,
        independent_volume_cm3=math.pi*radius*radius*(stations[1]-stations[0]),
        geometry_selects_identity=False,API_ENTITY_assignment=None)


def saved_API_bounds(archive,feature,reference):
    import json
    truth_file='extents-f0f33a9a605f/ground_truth.json'
    truth=json.loads((ROOT/truth_file).read_text());sample,=[s for s in truth['samples'] if s['file']==Path(archive).name]
    assert sample['name']==feature['name']
    _near(sample['body_bounds_cm'],reference['independent_bounds_cm'])
    actual=sample['start'] if reference['selection_role']=='FromEntity' else sample['extent_one']
    assert actual['entity_name']=='TargetPlane' and actual['offset']==reference['selected_offset_cm']
    return dict(truth_file=truth_file,actual_API_body_bounds_cm=sample['body_bounds_cm'],
        independently_derived_bounds_cm=reference['independent_bounds_cm'],
        actual_API_selected_entity_name=actual['entity_name'],actual_API_offset_cm=actual['offset'],
        native_ID_joins_precede_numerical_comparison=True,API_ENTITY_assignment=None,
        scope='Actual complete result bounds and selected limit controls corroborate after native feature/Sketch/plane/BODY joins; no API entity assigned by geometry or label')


def qualify(row,before,independent_source,archive,zstd):
    """Check native plane/Sketch/BODY identities before analytic equations."""
    import math
    from fusion_archive import read_members
    from fusion_metadata import design_records
    from asm_records import inspect_asm
    from decode_brep import decode_topology
    assert row['native_source_provenance']==independent_source
    source=independent_source;feature_id=row['feature_object_id'];reference=plane_reference(before,feature_id)
    stream,=before['streams'];feature,=[f for f in stream['features'] if f['object_id']==feature_id]
    assert source['feature_object_id']==feature_id
    assert row['original_native_control_kinds']==dict(start=feature['start']['kind'],side_one=feature['extent']['side_one']['condition'])
    assert source['settings']['start']['kind']==feature['start']['kind']
    assert source['settings']['extent']['side_one']['condition']==feature['extent']['side_one']['condition']
    assert source['settings']['extent']['side_one']['uninterpreted_flags']==feature['extent']['side_one']['uninterpreted_flags']
    group,=source['source_groups'];assert source['source_group_count']==1
    assert group['source_feature_object_id']==feature_id and group['native_profile_kind']=='Circle'
    assert group['native_profile_selection']['native_sketch_object_id']==reference['native_sketch_object_id']
    circle,=group['native_profile_circles'];assert circle['circle_object_id']==reference['native_Circle_object_id']
    body=group['native_body_object_id'];anchor,=[a for a in stream['body_selections']['body_anchors'] if a['object_id']==group['body_anchor_object_id']]
    assert anchor['source_owner_object_id']==feature_id and anchor['native_body_object_id']==body
    mapping,=[m for m in stream['body_blob_bindings']['decoded'] if m['mapping_record_object_id']==group['mapping_record_object_id']]
    binding,=[b for b in mapping['bindings'] if b['native_body_object_id']==body]
    assert binding['stored_handle']==group['binding']['stored_handle'] and binding['asm_body_index']==group['asm_body_index']
    assert row['source_native_body_object_id']==body and row['binding']==group['binding']
    assert row['asm_body_index']==group['asm_body_index'] and row['history_blob_member']==mapping['history_blob_member']==group['history_blob_member']
    plane_proof=source['plane_limit_provenance'];assert plane_proof==group['plane_limit_provenance']
    assert plane_proof['native_controls_unchanged'] is True and plane_proof['derived_distance_controls'] is None
    limit,=plane_proof['limits']
    assert limit['native_selection_record_object_id']==reference['selection_record_object_id']
    assert limit['descriptor_object_id']==reference['descriptor_object_id']
    selected=limit['selection']
    assert selected['terminal_object_id']==reference['terminal_object_id'] and selected['entity']['object_id']==reference['plane_object_id']
    assert selected['entity']['feature_object_id']==reference['plane_feature_object_id']
    assert plane_proof['component_provenance']['component_object_id']==reference['component_object_id']
    _near(limit['plane_native_geometry']['origin_cm'],reference['plane_origin_cm'])
    _near(limit['plane_native_geometry']['normal'],reference['plane_normal'])
    _near(limit['frame_relation']['derived_forward_plane_separation_cm'],reference['independent_plane_crossing_cm'])
    _near(limit['native_selected_offset_cm'],reference['selected_offset_cm'])
    members=read_members(ROOT/archive,zstd);member=stream['member'];data=members[member]
    records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')]);primary={}
    for record in records:
        if record.is_primary:primary.setdefault(record.object_id,[]).append(record)
    raw_verified=set()
    def verify_native(value):
        if isinstance(value,dict):
            fields={'object_id','class_guid','record_offset','body_offset','end_offset','payload_hex'}
            if fields<=value.keys():
                record,=primary[value['object_id']]
                assert (record.class_guid,record.start,record.body,record.end)==(value['class_guid'],value['record_offset'],value['body_offset'],value['end_offset'])
                assert data[record.body:record.end].hex()==value['payload_hex'];raw_verified.add(record.object_id)
            for v in value.values():verify_native(v)
        elif isinstance(value,list):
            for v in value:verify_native(v)
    verify_native(source)
    assert {reference[k] for k in ('selection_record_object_id','descriptor_object_id','terminal_object_id','plane_object_id','plane_feature_object_id')}<=raw_verified
    # All object/role joins and literal native payload checks above precede arithmetic.
    model=row['derived_geometry'];derivation=model['plane_limit_derivation']
    _near(derivation['selected_plane_intersection_distance_cm'],reference['independent_plane_crossing_cm'])
    _near(derivation['derived_axial_interval_cm'],reference['axial_stations_cm'])
    assert derivation['mathematical_equivalent_controls_are_native_records'] is False
    assert derivation['native_start_kind']==feature['start']['kind'] and derivation['native_end_kind']==feature['extent']['side_one']['condition']
    assert derivation['native_uninterpreted_side_flags']==feature['extent']['side_one']['uninterpreted_flags']
    equivalent=model['mathematical_equivalent_distance_controls']
    assert equivalent['extent']['side_one']['condition']=='Distance'
    _near(equivalent['extent']['side_one']['distance_cm'],reference['axial_stations_cm'][1]-reference['axial_stations_cm'][0])
    _near([s['axial_distance_cm'] for s in model['axial_stations']],reference['axial_stations_cm'])
    _near([s['center_cm'] for s in model['axial_stations']],reference['cap_centers_component_cm'])
    _near([s['radius_cm'] for s in model['axial_stations']],[reference['radius_cm']]*2)
    _near([model['component_axis_aligned_bounds_cm']['minimum'],model['component_axis_aligned_bounds_cm']['maximum']],reference['independent_bounds_cm'])
    _near(model['volume_cm3'],reference['independent_volume_cm3'])
    for key in ('source_to_cache_entity_mapping','exact_API_handle_identity','qualified_historical_state','current_or_final_geometry_identity'):assert row[key] is None
    topology=decode_topology(inspect_asm(members[row['history_blob_member']]))
    nodes={n['index']:n for n in topology['nodes']};graph,=[g for g in topology['body_graphs'] if g['body_index']==row['asm_body_index']]
    assert graph['body_transform_is_identity'] is True and nodes[graph['body_index']]['stored_entity_id']==binding['stored_handle']
    assert graph['counts']==dict(lump=1,shell=1,face=3,loop=4,coedge=4,edge=2,vertex=2)
    cache=row['native_cache_geometry_corroboration'];assert cache['counts']==graph['counts']
    assert cache['semantic_cap_to_native_ENTITY_mapping'] is None
    axis=reference['axis_direction_component'];center=reference['profile_center_component_cm'];radius=reference['radius_cm']
    def parallel(vector):
        _near(math.hypot(*vector),1.);sign=1 if sum(a*b for a,b in zip(vector,axis))>0 else -1
        _near([sign*x for x in vector],axis)
    cap_ids={f for f in graph['face_indices'] if nodes[nodes[f]['surface_index']]['kind']=='plane-surface'}
    side_id,=set(graph['face_indices'])-cap_ids;assert len(cap_ids)==2
    circles=[];endpoint_checks=0;seen_coedges=set();seen_loops=set()
    for boundary in cache['native_boundary_circles']:
        edge=nodes[boundary['native_EDGE']['index']];curve=nodes[edge['curve_index']]
        assert boundary['native_EDGE']==edge and boundary['native_Circle']==curve
        assert curve['kind']=='ellipse-curve' and edge['start_vertex_index']==edge['end_vertex_index']
        parallel(curve['normal']);_near(curve['raw_major_radius'],radius);_near(curve['raw_minor_radius'],radius)
        u=curve['stored_reference_axis'];_near(math.hypot(*u),radius)
        _near(sum(n*x for n,x in zip(curve['normal'],u)),0.)
        _near(abs(edge['end_parameter']-edge['start_parameter']),2*math.pi)
        v=[curve['normal'][1]*u[2]-curve['normal'][2]*u[1],curve['normal'][2]*u[0]-curve['normal'][0]*u[2],curve['normal'][0]*u[1]-curve['normal'][1]*u[0]]
        point=nodes[nodes[edge['start_vertex_index']]['point_index']]['raw_origin']
        for t in (edge['start_parameter'],edge['end_parameter']):
            _near([o+math.cos(t)*a+math.sin(t)*b for o,a,b in zip(curve['raw_origin'],u,v)],point);endpoint_checks+=1
        cap=nodes[boundary['native_cap_FACE']['index']];plane=nodes[cap['surface_index']]
        assert cap['index'] in cap_ids and boundary['native_cap_FACE']==cap and boundary['native_cap_Plane']==plane
        parallel(plane['normal']);_near(sum(n*(p-o) for n,p,o in zip(plane['normal'],curve['raw_origin'],plane['raw_origin'])),0.)
        uses=boundary['native_COEDGEs'];assert len(uses)==2
        assert {nodes[nodes[c['index']]['loop_index']]['face_index'] for c in uses}=={cap['index'],side_id}
        for c in uses:
            assert c==nodes[c['index']] and c['index'] not in seen_coedges;seen_coedges.add(c['index'])
            assert c['edge_index']==edge['index'] and c['next_coedge_index']==c['previous_coedge_index']==c['index']
            assert nodes[c['partner_index']]['partner_index']==c['index'] and c['partner_index']!=c['index']
            loop=nodes[c['loop_index']];assert loop['first_coedge_index']==c['index'];seen_loops.add(loop['index'])
        circles.append(curve['raw_origin']+[radius])
    assert seen_coedges==set(graph['coedge_indices']) and seen_loops==set(graph['loop_indices'])
    _near(sorted(circles),sorted(c+[radius] for c in reference['cap_centers_component_cm']))
    side=nodes[nodes[side_id]['surface_index']];analytic=side['analytic_surface'];assert analytic['kind']=='Cylinder'
    assert cache['native_lateral_FACE']==nodes[side_id] and cache['native_lateral_carrier']==side
    parallel(analytic['axis']);_near(analytic['raw_radius'],radius)
    delta=[x-c for x,c in zip(analytic['raw_origin'],center)];height=sum(x*a for x,a in zip(delta,axis))
    _near([x-height*a for x,a in zip(delta,axis)],[0.,0.,0.])
    API=saved_API_bounds(archive,feature,reference)
    return dict(feature_object_id=feature_id,native_body_object_id=body,source_plane_reference=reference,
        raw_native_provenance_records=len(raw_verified),original_native_controls_and_flags_preserved=True,
        mathematical_distance_controls_are_separate=True,complete_cylinder_coefficient_proofs=1,
        complete_cap_circle_proofs=2,native_endpoint_evaluations=endpoint_checks,
        native_cache_counts=graph['counts'],saved_API_bounds=API,
        native_ID_joins_precede_arithmetic=True,semantic_to_native_ENTITY_assignment=None)


SUMMARY=ATTACHMENT='plane_extrusion_reconstruction'
EVIDENCE='plane-extrusion-reconstruction-decoding.json'
SOURCE_EVIDENCE='extrusion-plane-limit-source-decoding.json'
MATH_EVIDENCE='plane-extrusion-geometry-decoding.json'
FROZEN_PRODUCTION={
    'decode_extrusion_plane_limits.py':'66a697e7cc88884caa68066252aa533d360d37d570cd257b1f494ea95ad43497',
    'decode_extrusion_source_operands.py':'e1fda3565f5a8a4f2d3b5881325383d63f44642a2136b3baca3d421cb0e7613f',
    'decode_plane_extrusion_reconstruction.py':'8eebab305d044e67086dfc50712f2892bd7191f5f8f90c73fc2465e607118c34',
    'decode_plane_extrusion_geometry.py':'1c695e5513fc85af2df9542824b4745319fae1b380991214a8f467d9fdf3a590',
    'decode_extrusion_reconstruction.py':'4bcf4e5326fc2fafc9dcb17b7c870e6e39a97ea8fc8c86a4c26ad739779902f8'}
FROZEN_EVIDENCE={
    EVIDENCE:'fe0aaef181442bb826b81ca1624a32bed8073a1bf33c432424d7d61dbbc448e7',
    SOURCE_EVIDENCE:'1e32c623aadab871b356c115ef63ba3bc82d64edf39aa21e1d292083778192a2',
    MATH_EVIDENCE:'3a838cbbf5af15d941ac3ec338b7f4cb64a03729197a74e15564e2a9bb2d59a3'}


def focused_evidence():
    import json
    from validate_rectangular_cache_evidence_integration import sha
    for filename,expected in {**FROZEN_PRODUCTION,**FROZEN_EVIDENCE}.items():assert sha(ROOT/filename)==expected
    reports=[json.loads((ROOT/f).read_text()) for f in (EVIDENCE,SOURCE_EVIDENCE)]
    for report in reports+[json.loads((ROOT/MATH_EVIDENCE).read_text())]:
        for filename,expected in report['source_sha256'].items():assert sha(ROOT/filename)==expected,(filename,'Stale focused source evidence')
    summaries={s['archive']:s['expected_summary'] for s in reports[0]['samples'] if s['archive'] in FILES}
    sources={s['archive']:s['expected_sources'] for s in reports[1]['samples'] if s['archive'] in FILES}
    assert set(summaries)==set(sources)==set(FILES)
    for f in FILES:
        summary=summaries[f];assert set(summary)=={'decoded','unresolved','scope'}
        if f in FILES[:3]:
            row,=summary['decoded'];source,=sources[f]
            assert not summary['unresolved'] and row['native_source_provenance']==source
        else:assert not summary['decoded'] and not summary['unresolved'] and not sources[f]
    return summaries,sources


def compare(before,current,archive,expected,sources,zstd):
    import copy
    from validate_rectangular_cache_evidence_integration import sha,digest,differences
    after=copy.deepcopy(current);old,=before['streams'];stream,=after['streams']
    assert old['member']==stream['member'] and SUMMARY not in old
    proofs=[]
    if archive in FILES[:3]:
        assert stream.pop(SUMMARY)==expected
        row,=expected['decoded'];identity=row['feature_object_id']
        feature,=[f for f in stream['features'] if f['object_id']==identity]
        prior,=[f for f in old['features'] if f['object_id']==identity]
        assert prior['kind']==feature['kind']=='Extrude' and ATTACHMENT not in prior
        assert feature.pop(ATTACHMENT)==row
        source,=sources;proofs.append(qualify(row,before,source,archive,zstd))
    else:
        assert SUMMARY not in stream and not expected['decoded'] and not expected['unresolved']
    assert all(ATTACHMENT not in f for f in stream.get('features',[]))
    assert after==before,(archive,'Unexpected prior-output change',differences(before,after))
    return dict(archive=archive,archive_sha256=sha(ROOT/archive),decoded_plane_limited_Extrudes=len(expected['decoded']),
        receiving_feature_annotations=len(expected['decoded']),independent_geometry_proofs=proofs,
        whole_output_unchanged=current==before,
        whole_output_exact_after_removing_only_new_summary_and_successful_owner_annotation=True,
        all_previous_settings_warnings_kinds_timeline_ASM_geometry_topology_and_placement_exact=True,
        baseline_output_sha256=digest(before),current_output_sha256=digest(current),
        qualified_difference_paths=differences(before,current))


def read_cache(path,side):
    import json
    from validate_rectangular_cache_evidence_integration import sha
    value=json.loads(Path(path).read_text())
    assert value['baseline_commit']==BASELINE and value['files']==list(FILES)
    assert value['acquisition_main_calls']==8 and value['acquisition_passes']==1 and len(value[side])==8
    if side=='after':
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
    assert len(before)==len(current)==8
    assert [r['file'] for r in before]==[str(ROOT/f) for f in FILES]==[r['file'] for r in current]
    rows=[compare(a,b,f,expected[f],sources[f],zstd) for a,b,f in zip(before,current,FILES)]
    proofs=[p for r in rows for p in r['independent_geometry_proofs']]
    summary=dict(saved_files=8,decoded_plane_limited_Extrudes=len(proofs),new_summaries=3,
        receiving_feature_annotations=sum(r['receiving_feature_annotations'] for r in rows),
        ToEntity_plane_limits=sum(p['source_plane_reference']['selection_role']=='ToEntity' for p in proofs),
        FromEntity_plane_limits=sum(p['source_plane_reference']['selection_role']=='FromEntity' for p in proofs),
        raw_native_provenance_records=sum(p['raw_native_provenance_records'] for p in proofs),
        complete_cylinder_coefficient_proofs=sum(p['complete_cylinder_coefficient_proofs'] for p in proofs),
        complete_cap_circle_proofs=sum(p['complete_cap_circle_proofs'] for p in proofs),
        native_endpoint_evaluations=sum(p['native_endpoint_evaluations'] for p in proofs),
        native_FACE_count=sum(p['native_cache_counts']['face'] for p in proofs),
        native_LOOP_count=sum(p['native_cache_counts']['loop'] for p in proofs),
        native_COEDGE_count=sum(p['native_cache_counts']['coedge'] for p in proofs),
        native_EDGE_count=sum(p['native_cache_counts']['edge'] for p in proofs),
        native_VERTEX_count=sum(p['native_cache_counts']['vertex'] for p in proofs),
        independent_saved_API_bound_controls=len(proofs),
        whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),
        unexpected_changes=0,comparator_baseline_main_calls=0 if baseline_cache else 8,
        comparator_current_main_calls=0 if current_cache else 8,live_API_calls=0)
    assert summary['decoded_plane_limited_Extrudes']==summary['receiving_feature_annotations']==3
    assert summary['raw_native_provenance_records']==69
    assert summary['ToEntity_plane_limits']==2 and summary['FromEntity_plane_limits']==1
    assert summary['complete_cylinder_coefficient_proofs']==3 and summary['complete_cap_circle_proofs']==6
    assert summary['native_endpoint_evaluations']==12 and summary['native_FACE_count']==9
    assert summary['native_LOOP_count']==12 and summary['native_COEDGE_count']==12
    assert summary['native_EDGE_count']==summary['native_VERTEX_count']==6
    assert summary['whole_output_unchanged_controls']==5
    return dict(scope='Three selected construction-plane Extrude reconstructions with independent native plane/Sketch/BODY joins, analytic cache equations and actual API bounds; all prior outputs preserved exactly',
        baseline_commit=BASELINE,files=list(FILES),summary=summary,samples=rows,
        fixed_manifest_acquisition=dict(baseline_main_calls=8,current_main_calls=8,baseline_passes=1,current_passes=1,
            interpreter='/usr/bin/python3',entrypoint='decode_basics.decode_basics(ROOT / filename, zstd_library)',
            fixed_order=list(FILES),scope='Original fixed acquisition, distinct from cached comparator zero-main execution'),
        cache_provenance={side:dict(path=str(Path(p).resolve()),sha256=sha(p)) for side,p in (
            ('baseline',baseline_cache),('current',current_cache)) if p},
        frozen_production_sha256=FROZEN_PRODUCTION,
        evidence_sha256={name:sha(ROOT/name) for name in (EVIDENCE,SOURCE_EVIDENCE,MATH_EVIDENCE)},
        saved_API_truth_sha256={'extents-f0f33a9a605f/ground_truth.json':sha(ROOT/'extents-f0f33a9a605f/ground_truth.json')},
        source_sha256={name:sha(ROOT/name) for name in ('validate_plane_extrusion_reconstruction_integration.py',
            'validate_extrusion_reconstruction_integration.py','decode_extrusion_plane_limits.py',
            'decode_extrusion_source_operands.py','decode_plane_extrusion_reconstruction.py',
            'decode_plane_extrusion_geometry.py','decode_extrusion_reconstruction.py','decode_basics.py')},
        limitations=['Selected source/plane proxy, descriptor, leaf, creator, component and BODY identities precede numerical intersection and cache comparison.',
            'Original native ToEntity/FromEntity kinds and flags remain literal; constructed equivalent Distance controls exist only in derived mathematical geometry.',
            'Only observed co-directed parallel +Z planes and nonnegative selected offsets are covered; reversed/oblique selected-plane conventions remain unresolved.',
            'Three complete saved API bound sets corroborate results after native joins; no API ENTITY assignment, chronological/current/final or persistent identity is established.',
            'No saved Extrude BRepFace target contrast exists. Hole to_bottom is an actual BRepFace ToEntity limit in another feature family, used only to check non-admission.',
            'Five controls remain whole-output exact. Existing ordinary extrusion reconstruction warnings, all prior ASM geometry/topology and placement stay unchanged.'])


def main():
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache');p.add_argument('--current-cache');p.add_argument('--zstd-library')
    p.add_argument('--output',default='plane-extrusion-reconstruction-integration.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z,a.baseline_cache,a.current_cache);Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['summary'],sort_keys=True))

if __name__=='__main__':main()
