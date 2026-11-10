"""Fixed twelve-file Sketch/Extrude/Scale reconstruction integration."""
import argparse
import copy
import json
import math
from pathlib import Path

from validate_rectangular_cache_evidence_integration import sha,digest,differences

ROOT=Path(__file__).resolve().parent
BASELINE='fb2865a'
FILES=('tools-fda3948848f4/Scale.f3d','bodymodes-df9b7113539f/scale_uniform.f3d',
       'bodymodes-df9b7113539f/scale_nonuniform.f3d','bodymodes-d696a14d5f0b/scale_holdout.f3d',
       'bodyselections-62e42366c722/scale_two_bodies_point.f3d',
       'scaleshellinputs-97ef1cfd19e4/scale_vertex.f3d',
       'scaleshellinputs-97ef1cfd19e4/scale_construction_point.f3d',
       'scaleshellinputs-97ef1cfd19e4/scale_sketch.f3d',
       'remainingbodyinputs-7b3357274e85/scale_two_sketches.f3d',
       'namedvertexprobe-8d81619f74e6/scale_rational_vertex2.f3d',
       'circularmodes-45f859c1f1b6/body_full.f3d','surfacetools-856ca50cf4c7/offset_positive.f3d')
POSITIVES=frozenset(FILES[:7]);UNSUPPORTED=frozenset(FILES[7:10]);CONTROLS=frozenset(FILES[10:])
SUMMARY=ATTACHMENT='scale_reconstruction'
EVIDENCE='scale-reconstruction-decoding.json'
SOURCE_EVIDENCE='scale-reconstruction-source-decoding.json'
API_TRUTH='bodycoords-2c2aa8982ad4/ground_truth.json'
FROZEN_PRODUCTION={
    'decode_scale_reconstruction_sources.py':'c788206817af9fcb0431c8ff34822ada0f7af35ed3e9c22c7c393280cfbbadf9',
    'decode_scale_reconstruction.py':'342974414ebaf1e97f40559103b48756c52ea638c70ad5d90456e021c042e112',
    'decode_scale_prism_geometry.py':'4a17d115d2d6dace311901c1bf113b8ea611c706f0375d3f2d195adbdc9b54eb'}
FROZEN_EVIDENCE={
    EVIDENCE:'4175b8051985ea1929a1e9bb85409d36b0e69d21bcf2422fa6d6b7c6dedfcb13',
    SOURCE_EVIDENCE:'72f5203e0449880e4dd87b209d152d1e16a2299bb6904eab81ee625bc5434c65'}
COUNT_KEYS=('qualified_Scale_features','receiving_feature_annotations','qualified_prism_groups',
            'source_prism_vertices','scaled_prism_vertices','native_cache_vertex_pairs',
            'source_line_segments','scaled_line_segments','source_planar_boundaries','scaled_planar_boundaries',
            'native_Scale_parameter_sets','selected_centre_controls','independent_native_source_dictionary_checks',
            'same_ID_literal_view_proofs','literal_source_vertex_pairs','complete_signed_FACE_names',
            'native_Line_equation_checks','native_Plane_equation_checks','native_EDGE_endpoint_evaluations','independent_API_vertex_set_controls',
            'independent_API_vertices','selected_vertex_centre_native_source_proofs','explicit_unsupported_Scale_controls')


def evidence():
    for filename,expected in {**FROZEN_PRODUCTION,**FROZEN_EVIDENCE}.items():
        assert sha(ROOT/filename)==expected,('Frozen source or focused evidence changed',filename)
    for filename in (EVIDENCE,SOURCE_EVIDENCE):
        report=json.loads((ROOT/filename).read_text())
        for source,expected in report['source_sha256'].items():
            assert sha(ROOT/source)==expected,(filename,'Stale focused source hash',source)
    rows={}
    for sample in json.loads((ROOT/EVIDENCE).read_text())['samples']:
        if sample['archive'] not in FILES:continue
        assert sample['archive'] not in rows
        rows[sample['archive']]=sample['expected_summary']
    assert set(rows)==set(FILES)
    source=json.loads((ROOT/SOURCE_EVIDENCE).read_text())
    samples={s['archive']:s for s in source['samples'] if s['archive'] in FILES}
    assert set(samples)==set(FILES)
    sources={name:s['expected_sources'] for name,s in samples.items()}
    for name in FILES:
        if name in POSITIVES:
            independent,=sources[name];decoded,=rows[name]['decoded']
            assert decoded['native_source_provenance']==independent and not samples[name]['expected_unresolved']
        else:
            assert not sources[name] and rows[name]['decoded']==[]
            assert rows[name]['unresolved']==samples[name]['expected_unresolved']
    return rows,sources


def native_prism(before,source_feature_id,settings):
    """Construct from typed profile member IDs and native controls, never cache coordinates."""
    features=before['streams'][0]['features']
    source=next(f for f in features if f['object_id']==source_feature_id)
    assert source['kind']=='Extrude' and source['operation']['kind']=='NewBody'
    assert source['start']['kind']=='ProfilePlane' and source['extent']['mode']=='OneSided'
    extent=source['extent']['side_one']
    assert extent['condition']=='Distance' and extent['taper_angle_radians']==0
    distance=extent['distance_cm'];direction=source['extent']['stored_direction_vector']
    profile,=source['profile_selection'];loop,=profile['loops']
    assert loop['is_outer'] is True and len(loop['curve_references'])==4
    sketch=next(f for f in features if f['kind']=='Sketch' and f['sketch_object_id']==profile['sketch_object_id'])
    geometry={g['object_id']:g for g in sketch['geometry']}
    matrix=sketch['placement']['sketch_to_component_matrix']
    selected=[geometry[r['entity_id']] for r in loop['curve_references']]
    assert all(g['kind']=='Line' and not g['is_construction'] for g in selected)
    for reference,line in zip(loop['curve_references'],selected):
        assert reference['entity_tag']==line['entity_tag'] and reference['secondary_tag']==0
    point_ids={g[k] for g in selected for k in ('start_point_id','end_point_id')}
    assert len(point_ids)==4
    def component(point):return [sum(matrix[4*i+j]*point[j] for j in range(3))+matrix[4*i+3] for i in range(3)]
    points={identity:component(geometry[identity]['position_cm']) for identity in point_ids}
    assert all(geometry[identity]['kind']=='Point' for identity in point_ids)
    point=settings['point'];centre=point.get('cached_position_cm',point['entity'].get('position_cm'))
    assert len(centre)==3
    factors=[settings['factor']]*3 if settings['is_uniform'] else settings['factors']
    result={}
    for identity,base in points.items():
        for layer in (0,1):
            unscaled=[v+layer*distance*d for v,d in zip(base,direction)]
            scaled=[c+f*(v-c) for c,f,v in zip(centre,factors,unscaled)]
            result[(identity,layer)]=dict(source_point_object_id=identity,layer=layer,
                unscaled_component_position_cm=unscaled,scaled_component_position_cm=scaled)
    return result


def qualify(row,before,filename,independent_source):
    stream=before['streams'][0];features=stream['features']
    feature=next(f for f in features if f['object_id']==row['feature_object_id'])
    settings=feature['tool_settings'];source=row['native_source_provenance']
    assert source==independent_source and source['feature_object_id']==feature['object_id']
    centre=settings['point'].get('cached_position_cm',settings['point']['entity'].get('position_cm'))
    factors=[settings['factor']]*3 if settings['is_uniform'] else settings['factors']
    assert source['settings']['reconstruction_center_cm']==centre and source['settings']['factors_xyz']==factors
    matrix=[[factors[0],0.,0.,centre[0]*(1-factors[0])],
            [0.,factors[1],0.,centre[1]*(1-factors[1])],
            [0.,0.,factors[2],centre[2]*(1-factors[2])],[0.,0.,0.,1.]]
    def close(a,b):
        if isinstance(a,(list,tuple)):
            assert len(a)==len(b)
            for x,y in zip(a,b):close(x,y)
        else:assert math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=0,abs_tol=1e-9),(a,b)
    close(row['computed_affine_matrix_4x4'],matrix)
    assert row['scale_owned_result_anchor_object_ids']==[] and row['same_native_BODY_source_and_cache_route'] is True
    assert not any(a['source_owner_object_id']==feature['object_id'] for a in stream['body_selections']['body_anchors'])
    for key in ('exact_current_or_historical_state','persistent_topology_identity','API_handle_identity'):assert row[key] is None
    selected={i['native_body_object_id']:i for i in settings['input_selections']}
    sources={g['native_body_object_id']:g for g in source['source_groups']}
    groups={g['source_native_body_object_id']:g for g in row['derived_prism_groups']}
    assert len(groups)==len(row['derived_prism_groups']) and set(groups)==set(sources)==set(selected)
    totals=dict(qualified_prism_groups=len(groups),source_prism_vertices=0,scaled_prism_vertices=0,
        native_cache_vertex_pairs=0,source_line_segments=0,scaled_line_segments=0,
        source_planar_boundaries=0,scaled_planar_boundaries=0,native_Scale_parameter_sets=1,selected_centre_controls=1,
        independent_API_vertex_set_controls=0,independent_API_vertices=0,
        independent_native_source_dictionary_checks=1,same_ID_literal_view_proofs=0,
        literal_source_vertex_pairs=0,complete_signed_FACE_names=0,native_Line_equation_checks=0,
        native_Plane_equation_checks=0,native_EDGE_endpoint_evaluations=0,selected_vertex_centre_native_source_proofs=0)
    all_predictions=[]
    for native_id,group in groups.items():
        native=sources[native_id];chosen=selected[native_id]
        assert group['source_feature_object_id']==native['source_feature_object_id']==chosen['source_owner_object_id']
        assert native['body_anchor_object_id']==chosen['body_anchor_object_id']
        expected=native_prism(before,group['source_feature_object_id'],settings)
        mapping,= [m for m in stream['body_blob_bindings']['decoded'] if m['mapping_record_object_id']==native['mapping_record_object_id']]
        binding,= [b for b in mapping['bindings'] if b['native_body_object_id']==native_id]
        assert binding['asm_body_index']==group['asm_body_index'] and binding['stored_handle']==group['body_binding']['stored_handle']
        assert mapping['history_blob_member']==group['history_blob_member']
        asm,=[s for s in before['asm_decoding']['streams'] if s['member']==group['history_blob_member']]
        graph,=[g for g in asm['topology']['body_graphs'] if g['body_index']==group['asm_body_index']]
        assert graph['body_transform_is_identity'] is True
        identities=group['identity_provenance']
        bottom={int(k):v for k,v in identities['bottom'].items()};opposite={int(k):v for k,v in identities['opposite'].items()}
        connectors={int(k):v for k,v in identities['connectors'].items()}
        assert len(bottom)==len(opposite)==4 and set(bottom)==set(opposite)=={p for p,layer in expected}
        assert set(bottom.values())|set(opposite.values())==set(graph['vertex_indices'])
        carriers={l['edge_index']:l for l in group['native_straight_carrier_correspondence']}
        assert len(carriers)==12 and set(carriers)==set(graph['edge_indices'])
        edge_nodes={i:c['native_EDGE'] for i,c in carriers.items()}
        native_lines={g['object_id']:g for g in native['source_sketch']['geometry'] if g['kind']=='Line'}
        profile=native['profile_cache_correspondence'];profile_curves={c['native_entity_object_id']:c for c in profile['source_curves']}
        point_edges={};profile_edges=set()
        for proof in identities['profile_line_edge_proofs']:
            line=native_lines[proof['native_line_object_id']];cached=profile_curves[line['object_id']]
            assert proof['native_curve_tag']==line['entity_tag']==cached['native_entity_tag']
            assert proof['native_endpoint_object_ids']==[line['start_point_id'],line['end_point_id']]
            eid=proof['cached_profile_edge_record_index'];profile_edges.add(eid)
            assert {c['edge_record_index'] for c in cached['cached_coedge_candidates']}=={eid}
            assert set(proof['profile_coedge_record_indices'])=={c['coedge_record_index'] for c in cached['cached_coedge_candidates']}
            for p in (line['start_point_id'],line['end_point_id']):point_edges.setdefault(p,[]).append(eid)
        assert set(point_edges)==set(bottom) and len(profile_edges)==4
        for p,edges in point_edges.items():
            assert len(set(edges))==2
            endpoints=[{edge_nodes[e]['start_vertex_index'],edge_nodes[e]['end_vertex_index']} for e in edges]
            assert endpoints[0]&endpoints[1]=={bottom[p]}
            connector=edge_nodes[connectors[p]]
            assert connectors[p] not in profile_edges and {connector['start_vertex_index'],connector['end_vertex_index']}=={bottom[p],opposite[p]}
        # The POINT/layer -> cache VERTEX map is fixed above, before arithmetic.
        derived=group['derived_prism'];vertices=group['vertex_correspondence']
        assert len(vertices)==len(derived['vertices'])==8
        expected_cache={}
        for vertex in vertices:
            key=(vertex['native_sketch_point_object_id'],vertex['layer']);control=expected[key]
            expected_id=(bottom if vertex['layer']==0 else opposite)[key[0]]
            assert vertex['vertex_index']==expected_id and expected_id not in expected_cache
            close(vertex['source_position_cm'],control['unscaled_component_position_cm'])
            close(vertex['scaled_position_cm'],control['scaled_component_position_cm'])
            close(vertex['stored_raw_position'],control['scaled_component_position_cm'])
            close(vertex['residual_raw'],max(abs(x-y) for x,y in zip(vertex['scaled_position_cm'],vertex['stored_raw_position'])))
            expected_cache[expected_id]=control;all_predictions.append(control['scaled_component_position_cm'])
        assert set(expected_cache)==set(graph['vertex_indices'])
        assert {tuple(v['stored_raw_position']) for v in vertices}==set(map(tuple,graph['raw_vertex_positions']))
        close(derived['affine_matrix_4x4'],matrix);close(derived['center_cm'],centre);close(derived['factors'],factors)
        close(derived['determinant'],math.prod(factors))
        close(derived['scaled_prism']['volume_cm3'],derived['source_prism']['volume_cm3']*math.prod(factors))
        for geometry,label in ((derived['source_prism'],'unscaled_component_position_cm'),(derived['scaled_prism'],'scaled_component_position_cm')):
            segments=geometry['segments'];faces=geometry['planar_quadrilateral_boundaries']
            assert len(segments)==12 and len(faces)==6
            for segment in segments:
                edge=edge_nodes[segment['edge_index']]
                assert segment['vertex_indices']==[edge['start_vertex_index'],edge['end_vertex_index']]
                a,b=[expected_cache[i][label] for i in segment['vertex_indices']]
                close(segment['start_position_cm'],a);close(segment['end_position_cm'],b)
                close(segment['direction_cm'],[y-x for x,y in zip(a,b)])
                assert segment['mathematical_parameter_domain']==[0.,1.]
            face_ids=set()
            for face in faces:
                assert face['face_index'] in graph['face_indices'];face_ids.add(face['face_index'])
                assert len(set(face['vertex_cycle']))==4
                expected_points=[expected_cache[v][label] for v in face['vertex_cycle']]
                close(face['corner_positions_cm'],expected_points)
                normal=face['outward_mathematical_unit_normal'];close(math.hypot(*normal),1)
                for p in expected_points:close(sum(n*x for n,x in zip(normal,p)),face['plane_constant_cm'])
                assert sum(n*(c-o) for n,c,o in zip(normal,geometry['centroid_cm'],expected_points[0]))<0
            assert face_ids==set(graph['face_indices'])
        for eid,carrier in carriers.items():
            edge=carrier['native_EDGE'];line=carrier['native_Line']
            a,b=[expected_cache[edge[k]]['scaled_component_position_cm'] for k in ('start_vertex_index','end_vertex_index')]
            parameter=carrier['mathematical_segment_to_native_Line_parameter']
            scale,offset=parameter['scale'],parameter['offset']
            close([scale*d for d in line['direction']],[y-x for x,y in zip(a,b)])
            close([o+offset*d for o,d in zip(line['raw_origin'],line['direction'])],a)
            close([offset,offset+scale],[edge['start_parameter'],edge['end_parameter']])
            for point,t in zip((a,b),(edge['start_parameter'],edge['end_parameter'])):
                close([o+t*d for o,d in zip(line['raw_origin'],line['direction'])],point)
        planes=group['native_planar_boundary_correspondence'];assert len(planes)==6
        assert {p['face_index'] for p in planes}==set(graph['face_indices'])
        for plane in planes:
            normal=plane['native_Plane']['normal'];origin=plane['native_Plane']['raw_origin']
            for vertex in plane['derived_planar_quad']['vertex_cycle']:
                point=expected_cache[vertex]['scaled_component_position_cm']
                close(sum(n*(p-o) for n,p,o in zip(normal,point,origin)),0.)
        totals['native_Line_equation_checks']+=12;totals['native_Plane_equation_checks']+=6
        totals['native_EDGE_endpoint_evaluations']+=24
        literal=group['literal_source_like_cache_corroboration']
        assert literal['qualified_historical_state'] is None and literal['source_before_Scale_identity'] is None
        pair=literal['literal_source_body_pair']
        assert pair['kind']=='body' and pair['side1_inspection_record_index']==group['asm_body_index']
        assert pair in literal['provenance']['literal_pair_aliases']
        assert literal['same_stored_BODY_identifier']==binding['stored_handle']
        assert literal['qualified_body_origin']['initial_record_index']==group['asm_body_index']
        assert literal['qualified_body_origin']['view_origin']['view_record_index']==literal['qualified_body_view_record_index']
        points=literal['derived_source_vertex_correspondence']
        assert len(points)==8 and {p['initial_vertex_index'] for p in points}==set(graph['vertex_indices'])
        assert len({p['view_vertex_index'] for p in points})==8
        for p in points:
            expected_point=expected_cache[p['initial_vertex_index']]['unscaled_component_position_cm']
            close(p['derived_source_position_cm'],expected_point);close(p['literal_view_raw_position'],expected_point)
        vertex_center=group['vertex_center_literal_view_correspondence']
        if vertex_center is not None:
            assert filename=='scaleshellinputs-97ef1cfd19e4/scale_vertex.f3d'
            key=(vertex_center['source_native_sketch_point_object_id'],vertex_center['source_extrude_layer'])
            independently_derived=expected[key]['unscaled_component_position_cm']
            close(vertex_center['independently_derived_source_center_cm'],independently_derived)
            close(independently_derived,centre)
            close(vertex_center['independently_selected_backend_center_cm'],centre)
            match=vertex_center['initial_cache_vertex_literal_correspondence']
            assert match in points
            assert match['initial_vertex_index']==(bottom if key[1]==0 else opposite)[key[0]]
            assert vertex_center['view_vertex_index']==match['view_vertex_index']
            assert len(set(vertex_center['view_FACE_indices']))==3
            totals['selected_vertex_centre_native_source_proofs']+=1
        names=group['complete_signed_FACE_naming'];assert len(names)==6
        assert {n['face_record_index'] for n in names}==set(graph['face_indices'])
        assert len({json.dumps(n['complete_terms'],sort_keys=True) for n in names})==6
        assert all(n['signed_component_semantics'] is None for n in names)
        observations=literal['full_FACE_name_observations'];assert len(observations)==6
        assert {o['initial_FACE']['face_record_index'] for o in observations}==set(graph['face_indices'])
        assert all(o['numeric_component_identity'] is None for o in observations)
        assert group['current_or_historical_or_API_BODY_identity'] is None
        totals['same_ID_literal_view_proofs']+=1;totals['literal_source_vertex_pairs']+=8;totals['complete_signed_FACE_names']+=6
        totals['source_prism_vertices']+=8;totals['scaled_prism_vertices']+=8;totals['native_cache_vertex_pairs']+=8
        totals['source_line_segments']+=12;totals['scaled_line_segments']+=12
        totals['source_planar_boundaries']+=6;totals['scaled_planar_boundaries']+=6
    assert row['counts']==dict(BODY_groups=len(groups),vertices=8*len(groups),straight_segments=12*len(groups),planar_quadrilateral_boundaries=6*len(groups))
    truth=json.loads((ROOT/API_TRUTH).read_text())
    measured=[s for s in truth['samples'] if s['source']==filename]
    totals['API_vertex_corroboration']=None
    if measured:
        assert filename in ('bodymodes-df9b7113539f/scale_uniform.f3d','bodymodes-df9b7113539f/scale_nonuniform.f3d')
        placement,=measured[0]['placements'];assert placement['path']==''
        api=placement['world_vertex_positions_cm']
        assert len(all_predictions)==len(api)==8 and len(set(map(tuple,api)))==8
        # Complete result-set corroboration only, never an API entity assignment.
        for a,b in zip(sorted(map(tuple,all_predictions)),sorted(map(tuple,api))):close(a,b)
        api_corroboration=dict(truth_file=API_TRUTH,API_root_body_name=placement['name'],
            component_occurrence_path=placement['path'],actual_root_vertices_cm=api,
            native_derived_scaled_vertices_cm=all_predictions,complete_native_ID_joins_precede_comparison=True,
            API_vertex_assignment=None,
            maximum_point_residual_cm=max(math.dist(a,b) for a,b in zip(sorted(map(tuple,all_predictions)),sorted(map(tuple,api)))),
            scope='Complete root vertex sets compared collectively after native source/BODY/POINT-layer joins; no API entity assigned by coordinates')
        totals.update(independent_API_vertex_set_controls=1,independent_API_vertices=8,
            API_vertex_corroboration=api_corroboration)
    return totals

def compare(before,current,filename,goldens,sources):
    after=copy.deepcopy(current);counts=dict.fromkeys(COUNT_KEYS,0)
    assert len(before['streams'])==len(after['streams'])==1
    old,stream=before['streams'][0],after['streams'][0]
    assert old['member']==stream['member'] and SUMMARY not in old
    expected=goldens[filename]
    assert set(expected)=={'decoded','unresolved','scope'}
    if filename in POSITIVES:
        assert stream.pop(SUMMARY)==expected and len(expected['decoded'])==1 and not expected['unresolved']
        row=expected['decoded'][0];identity=row['feature_object_id']
        prior=next(f for f in old['features'] if f['object_id']==identity)
        feature=next(f for f in stream['features'] if f['object_id']==identity)
        assert prior['kind']==feature['kind']=='Scale' and ATTACHMENT not in prior
        assert feature.pop(ATTACHMENT)==row
        independent,=[s for s in sources[filename] if s['feature_object_id']==identity]
        counts.update(qualify(row,before,filename,independent))
        counts.update(qualified_Scale_features=1,receiving_feature_annotations=1)
    elif filename in UNSUPPORTED:
        assert stream.pop(SUMMARY)==expected and not expected['decoded'] and len(expected['unresolved'])==1
        failure=expected['unresolved'][0]
        assert next(f for f in old['features'] if f['object_id']==failure['feature_object_id'])['kind']=='Scale'
        assert all(ATTACHMENT not in f for f in stream['features'])
        counts['explicit_unsupported_Scale_controls']=1
    else:
        assert filename in CONTROLS and not expected['decoded'] and not expected['unresolved']
        assert SUMMARY not in stream and all(ATTACHMENT not in f for f in stream['features'])
    assert after==before,(filename,'Unexpected previous-output change',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),**counts,
        whole_output_unchanged=before==current,
        whole_output_exact_after_removing_only_new_summary_and_successful_owner_annotation=True,
        all_previous_settings_warnings_kinds_timeline_ASM_geometry_topology_and_placement_exact=True,
        baseline_output_sha256=digest(before),current_output_sha256=digest(current),
        qualified_difference_paths=differences(before,current))


def read_cache(path,side):
    value=json.loads(Path(path).read_text())
    assert value['files']==list(FILES) and value['baseline_commit']==BASELINE
    assert value['acquisition_main_calls']==12 and value['acquisition_passes']==1
    assert len(value[side])==12
    if side=='after':
        assert value['production_source_sha256']==FROZEN_PRODUCTION
        assert value['main_source_sha256']==sha(ROOT/'decode_basics.py')
    return value[side]


def validate(zstd,baseline_cache=None,current_cache=None):
    if baseline_cache:before=read_cache(baseline_cache,'before')
    else:
        from validate_history_cache_integration import baseline_outputs
        before=baseline_outputs(FILES,zstd,revision=BASELINE)
    if current_cache:current=read_cache(current_cache,'after')
    else:
        from decode_basics import decode_basics
        current=json.loads(json.dumps([decode_basics(ROOT/name,zstd) for name in FILES]))
    assert len(before)==len(current)==len(FILES)==12
    assert [o['file'] for o in before]==[str(ROOT/f) for f in FILES]==[o['file'] for o in current]
    proof,sources=evidence();rows=[compare(b,a,f,proof,sources) for b,a,f in zip(before,current,FILES)]
    totals={key:sum(r[key] for r in rows) for key in COUNT_KEYS}
    totals.update(saved_files=12,whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),
        unexpected_changes=0,comparator_baseline_main_calls=0 if baseline_cache else 12,
        comparator_current_main_calls=0 if current_cache else 12,live_API_calls=0)
    assert totals['qualified_Scale_features']==7 and totals['qualified_prism_groups']==8
    assert totals['native_cache_vertex_pairs']==64 and totals['explicit_unsupported_Scale_controls']==3
    assert totals['whole_output_unchanged_controls']==2
    assert all(totals[k]==7 for k in ('receiving_feature_annotations','native_Scale_parameter_sets',
        'selected_centre_controls','independent_native_source_dictionary_checks'))
    assert all(totals[k]==64 for k in ('source_prism_vertices','scaled_prism_vertices','literal_source_vertex_pairs'))
    assert all(totals[k]==96 for k in ('source_line_segments','scaled_line_segments','native_Line_equation_checks'))
    assert all(totals[k]==48 for k in ('source_planar_boundaries','scaled_planar_boundaries',
        'native_Plane_equation_checks','complete_signed_FACE_names'))
    assert totals['same_ID_literal_view_proofs']==8 and totals['native_EDGE_endpoint_evaluations']==192
    assert totals['selected_vertex_centre_native_source_proofs']==1
    assert totals['independent_API_vertex_set_controls']==2 and totals['independent_API_vertices']==16
    return dict(scope='Seven saved BODY Scale reconstructions from typed Sketch/Extrude inputs; three explicit unsupported Scale summaries and two whole unchanged unrelated controls',
        baseline_commit=BASELINE,files=list(FILES),summary=totals,samples=rows,
        fixed_manifest_acquisition=dict(baseline_main_calls=12,current_main_calls=12,baseline_passes=1,current_passes=1,
            interpreter='/usr/bin/python3',entrypoint='decode_basics.decode_basics(ROOT / filename, zstd_library)',
            fixed_order=list(FILES),scope='Original fixed acquisition, distinct from cached comparator zero-main execution'),
        cache_provenance={side:dict(path=str(Path(p).resolve()),sha256=sha(p)) for side,p in (
            ('baseline',baseline_cache),('current',current_cache)) if p},
        evidence_sha256={f:sha(ROOT/f) for f in (EVIDENCE,SOURCE_EVIDENCE,API_TRUTH)},
        frozen_production_sha256=FROZEN_PRODUCTION,
        source_sha256={f:sha(ROOT/f) for f in ('validate_scale_reconstruction_integration.py',
            'decode_scale_reconstruction.py','decode_scale_prism_geometry.py','decode_scale_reconstruction_sources.py','decode_basics.py')},
        limitations=['Typed source routes and source POINT/layer, EDGE/FACE identities precede numerical cache corroboration.',
            'Actual API root vertex sets corroborate two complete results collectively after native joins; no API entity assignment by geometry.',
            'Other five BODY captures supply API settings and point/source controls, without new API geometry claims.',
            'Three unsupported cases retain every old warning and setting; no current/history/persistent identity or native regeneration claim.',
            'No live API calls or whole-corpus decoding; exact full previous outputs are preserved.'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache');p.add_argument('--current-cache');p.add_argument('--zstd-library')
    p.add_argument('--output',default='scale-reconstruction-integration.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z,a.baseline_cache,a.current_cache);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
