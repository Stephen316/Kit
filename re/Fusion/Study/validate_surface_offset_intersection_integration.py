"""Fixed ten-file Offset intersection-source integration against cf0ffb9."""
import argparse
import copy
import json
import struct
from functools import lru_cache
from pathlib import Path

from validate_rectangular_cache_evidence_integration import sha,digest,differences

ROOT=Path(__file__).resolve().parent
BASELINE='cf0ffb9'
FILES=tuple('rulefilletsurfaces-7b26b40f98f7/'+name+'.f3d' for name in (
    'offsets_one_two_witnesses','offsets_one_three_witnesses','offsets_one_two','offsets_one_three'))+tuple(
    'surfacetools-856ca50cf4c7/offset_'+name+'.f3d' for name in ('positive','negative','rounded'))+(
    'specialfillets-d50f7a4f04e0/rule_asymmetric.f3d','surfacebounds-ac801bb00fae/untrim_all.f3d',
    'surfacebounds-ac801bb00fae/extend_natural.f3d')
TARGETS=frozenset(FILES[:2])
SUMMARY='surface_offset_sources'
EVIDENCE='surface-offset-intersection-decoding.json'
SOURCE_EVIDENCE='surface-offset-source-variant-decoding.json'
COUNT_KEYS=('refined_source_summaries','recovered_source_associations','removed_support_unresolved_rows',
            'receiving_feature_annotation_lists','boundary_edges','endpoint_operands','complete_FACE_name_groups',
            'immediate_source_parent_role_checks','independent_default_summary_checks',
            'independent_support_provenance_checks','support_count2_owners','support_count3_owners','retained_XYZ_diagnostics','retained_UV_diagnostics')


def evidence():
    rows={}
    for sample in json.loads((ROOT/EVIDENCE).read_text())['samples']:
        if sample['archive'] not in FILES:continue
        assert sample['archive'] not in rows
        rows[sample['archive']]=sample['expected_summary']
    assert set(rows)==set(FILES)
    source=json.loads((ROOT/SOURCE_EVIDENCE).read_text())
    defaults={r['archive']:r['expected_default'] for r in source['default_controls']}
    supports={r['archive']:{p['owner_object_id']:p for p in r['native_owner_proofs']} for r in source['variant_samples']}
    assert set(supports)==TARGETS
    return rows,defaults,supports


@lru_cache(maxsize=2)
def native_context(filename,zstd):
    from fusion_archive import read_members
    from fusion_metadata import design_records
    members=read_members(filename,zstd)
    member=next(n for n in members if n.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
    data=members[member]
    records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    assert all(len(rs)==1 for rs in grouped.values())
    return data,{i:rs[0] for i,rs in grouped.items()},members


def qualify(row,old,zstd):
    from decode_sketch import reference
    from decode_recipe_components import decode_counted_recipe
    from decode_asm_recipe_tags import match_recipe_tag_names
    data,primary,members=native_context(old['file'],zstd)
    def payload(identity):
        r=primary[identity];return data[r.body:r.end]
    owner=row['owner_object_id'];feature=next(f for f in old['streams'][0]['features'] if f['object_id']==owner)
    assert feature['kind']=='SurfaceOffset'
    settings=feature['tool_settings']
    assert settings['distance_cm']==0 and settings['is_chain_selection'] is False
    assert settings['selection']['selection_record_object_id']==row['selection_record_object_id']
    assert settings['selection']['descriptor_object_ids']==[row['descriptor_object_id']]
    assert settings['result_record_object_ids']==[row['result_anchor_object_id']]
    assert row['feature_payload_hex']==payload(owner).hex()
    metadata=row['stored_metadata_uint32']
    assert 143<=metadata<=150 and row['stored_metadata_semantics'] is None
    assert struct.unpack_from('<I',payload(owner),row['stored_metadata_relative_offset'])[0]==metadata
    assert reference(payload(owner),46)==row['selection_record_object_id']
    descriptor=row['descriptor_object_id'];db=payload(descriptor)
    assert row['descriptor_payload_hex']==db.hex() and reference(db,265)==owner
    assert reference(db,253)==row['descriptor_support_object_id']
    proof=row['support_source_provenance'];support=payload(row['descriptor_support_object_id'])
    count=struct.unpack_from('<I',support,8)[0]
    assert count in (2,3) and len(support)==39+19*count and proof['stored_source_count']==count
    assert support.hex()==row['descriptor_support_payload_hex']==proof['exact_support_payload_hex']
    assert proof['descriptor_support_object_id']==row['descriptor_support_object_id']
    assert reference(support,12+19*count)==descriptor==proof['descriptor_backlink_object_id']
    sources=proof['support_sources'];source_ids=[s['source_feature_object_id'] for s in sources]
    assert source_ids==([344,385] if count==2 else [243,344,385])
    assert [reference(support,12+19*i) for i in range(count)]==source_ids
    assert row['historical_source_owner_object_id']==proof['historical_anchor_owner_object_id']==243
    for ordinal,s in enumerate(sources):
        identity=s['source_feature_object_id'];native=primary[identity]
        assert s['stored_support_ordinal']==ordinal and s['support_reference_offset']==12+19*ordinal
        assert s['source_feature_class_guid']==native.class_guid
        assert s['record_offset']==native.start and s['payload_hex']==payload(identity).hex()
        f=next(f for f in old['streams'][0]['features'] if f['object_id']==identity)
        assert f['record_offset']==native.start and f['class_guid']==native.class_guid
    assert len({owner,243,344,385})==4 and proof['component_object_id']==3
    anchors={a['object_id']:a for a in old['streams'][0]['body_selections']['body_anchors']}
    source=anchors[row['body_anchor_object_id']];result=anchors[row['result_anchor_object_id']]
    assert source['source_owner_object_id']==243 and source['native_body_object_id']==row['native_body_object_id']
    assert result['source_owner_object_id']==owner and result['native_body_object_id']!=row['native_body_object_id']
    assert reference(payload(source['object_id']),80)==source['native_body_object_id']
    assert reference(payload(result['object_id']),80)==result['native_body_object_id']
    for origin in row['native_record_origins']:
        r=primary[origin['object_id']]
        assert origin==dict(object_id=r.object_id,class_guid=r.class_guid,record_offset=r.start,body_offset=r.body,end_offset=r.end)
    recipe=decode_counted_recipe(data,primary[row['recipe_object_id']],primary)
    assert recipe==row['recipe'] and row['full_counted_recipe_payload_hex']==payload(row['recipe_object_id']).hex()
    assert row['exact_full_counted_recipe_replay'] is True and recipe['payload_length']==1476
    for key in ('exact_selected_source_identity','API_handle_identity','current_source_identity',
                'persistent_source_identity','qualified_historical_state','traversal','future_zero_offset_VBL_witness_binding'):
        assert row[key] is None
    parsed,topology,tags=asm_context(old['file'],zstd,row['history_blob_member'])
    naming=match_recipe_tag_names(recipe,tags,parsed=parsed)
    assert naming==row['naming_correspondence']
    entries=naming['name_entries'];assert len(entries)==7
    mapping=next(m for m in old['streams'][0]['body_blob_bindings']['decoded'] if m['mapping_record_object_id']==row['mapping_record_object_id'])
    binding,=[b for b in mapping['bindings'] if b['native_body_object_id']==row['native_body_object_id']]
    assert binding['asm_body_index']==row['explicit_asm_body_index'] and binding['stored_handle']==row['native_stored_body_identifier']
    assert mapping['history_blob_member']==row['history_blob_member']
    raw_mapping=payload(row['mapping_record_object_id']);mapping_count=struct.unpack_from('<I',raw_mapping,2)[0]
    raw_pairs=[struct.unpack_from('<QQ',raw_mapping,6+16*i) for i in range(mapping_count)]
    assert raw_pairs.count((binding['stored_handle'],row['native_body_object_id']))==1
    graph=next(g for g in topology['body_graphs'] if g['body_index']==row['explicit_asm_body_index'])
    nodes={n['index']:n for n in topology['nodes']}
    names={}
    for entry in entries:
        candidate,=entry['candidates']
        assert entry['candidate_count']==1 and candidate['owner_kind']=='face'
        assert candidate['body_graph_membership']==[graph['body_index']]
        names[entry['name_table_index']]=candidate['owner_record_index']
    assert len(set(names.values()))==7
    operation=row['operation_operands'];assert operation['stored_boundary_edge_count']==6
    assert operation['full_selection_procedure_evaluated'] is False and operation['opaque_endpoint_tail_int32_count']==17
    face=names[operation['stored_direct_face_name_index']]
    assert row['cached_face']['face_record_index']==face and face in graph['face_indices']
    edge_faces={};vertex_faces={}
    for cid in graph['coedge_indices']:
        c=nodes[cid];loop=nodes[c['loop_index']];edge=nodes[c['edge_index']]
        assert nodes[c['next_coedge_index']]['previous_coedge_index']==cid
        assert nodes[c['previous_coedge_index']]['next_coedge_index']==cid
        edge_faces.setdefault(edge['index'],set()).add(loop['face_index'])
        for v in (edge['start_vertex_index'],edge['end_vertex_index']):vertex_faces.setdefault(v,set()).add(loop['face_index'])
    boundary=row['boundary_incidence'];assert len(boundary)==6
    assert len({b['edge_record_index'] for b in boundary})==len({b['coedge_record_index'] for b in boundary})==6
    assert len({b['loop_record_index'] for b in boundary})==1
    for child,b in zip(operation['boundary_edges'],boundary):
        faces={names[n] for n in child['face_name_indices']}
        assert len(faces)==2 and face in faces and set(b['face_operand_record_indices'])==faces
        selected=[e for e,fs in edge_faces.items() if fs==faces];assert selected==[b['edge_record_index']]
        edge=nodes[selected[0]];coedge=nodes[b['coedge_record_index']]
        assert coedge['edge_index']==edge['index'] and coedge['loop_index']==b['loop_record_index']
        assert nodes[coedge['loop_index']]['face_index']==face
        assert len(child['endpoint_operands'])==len(b['endpoint_incidence'])==2
        vertices=[]
        for endpoint,e in zip(child['endpoint_operands'],b['endpoint_incidence']):
            assert len(endpoint['opaque_tail_int32'])==17 and endpoint['opaque_tail_semantics'] is None
            assert e['opaque_tail_int32']==endpoint['opaque_tail_int32'] and e['opaque_tail_semantics'] is None
            faces={names[n] for n in endpoint['face_name_indices']}
            assert len(faces)==3 and set(e['face_operand_record_indices'])==faces
            selected=[v for v,fs in vertex_faces.items() if fs==faces];assert selected==[e['vertex_record_index']]
            vertex=nodes[selected[0]];point=nodes[vertex['point_index']]
            assert point['kind']=='point' and e['point_record_index']==point['index'] and e['raw_point']==point['raw_origin']
            assert e['stored_edge_endpoint_role']==('Start' if vertex['index']==edge['start_vertex_index'] else 'End')
            vertices.append(vertex['index'])
        assert set(vertices)=={edge['start_vertex_index'],edge['end_vertex_index']}
    loop=nodes[boundary[0]['loop_record_index']];head=loop['first_coedge_index'];cycle=[];current=head
    while not cycle or current!=head:
        assert current not in cycle and len(cycle)<6
        cycle.append(current);current=nodes[current]['next_coedge_index']
    assert len(cycle)==6 and set(cycle)=={b['coedge_record_index'] for b in boundary}
    assert row['source_geometry_diagnostics']==topology['unresolved'] and len(topology['unresolved'])==64
    for origin in row['source_record_origins']:
        r=parsed['records'][origin['record_index']]
        assert origin==dict(record_index=r['index'],kind=r['name'],section=r['section'],record_offset=r['offset'],record_end_offset=r['end_offset'])
        assert r['section']=='geometry'
    return dict(boundary_edges=6,endpoint_operands=12,complete_FACE_name_groups=7,immediate_source_parent_role_checks=1,support_count2_owners=int(count==2),support_count3_owners=int(count==3))


@lru_cache(maxsize=2)
def asm_context(filename,zstd,member):
    from asm_records import inspect_asm
    from decode_asm_subtypes import decode_asm_subtypes
    from decode_brep import decode_topology
    from decode_asm_recipe_tags import decode_asm_generic_tags
    _,_,members=native_context(filename,zstd);blob=members[member];parsed=inspect_asm(blob)
    return parsed,decode_topology(parsed,subtype_catalog=decode_asm_subtypes(blob,parsed=parsed)),decode_asm_generic_tags(blob,parsed,allow_fpm_tracking=True)

def compare(before,current,filename,goldens,defaults,supports,zstd):
    after=copy.deepcopy(current);expected=goldens[filename]
    assert len(before['streams'])==len(after['streams'])==1
    old,stream=before['streams'][0],after['streams'][0]
    assert old['member']==stream['member']
    counts=dict.fromkeys(COUNT_KEYS,0)
    if filename in defaults:
        default=defaults[filename]
        if default['associations'] or default['unresolved']:assert old[SUMMARY]==default
        else:assert SUMMARY not in old
        counts['independent_default_summary_checks']=1
    if filename in TARGETS:
        previous=old[SUMMARY]
        assert previous['associations']==[] and len(previous['unresolved'])==8
        assert all(r['reason']=='Offset descriptor/source support reciprocity differs' for r in previous['unresolved'])
        assert stream[SUMMARY]==expected
        assert not expected['unresolved'] and len(expected['associations'])==8
        owners={r['owner_object_id']:r for r in expected['associations']}
        assert len(owners)==8 and set(owners)=={r['owner_object_id'] for r in previous['unresolved']}
        old_features={f['object_id']:f for f in old['features']}
        attached=set()
        for feature in stream['features']:
            identity=feature['object_id'];prior=old_features[identity]
            if identity in owners:
                assert prior['kind']==feature['kind']=='SurfaceOffset' and SUMMARY not in prior
                assert feature.pop(SUMMARY)==[owners[identity]]
                independent=supports[filename][identity]
                row=owners[identity]
                assert row['support_source_provenance']==independent['expected_support_source_provenance']
                assert row['stored_metadata_uint32']==independent['stored_metadata_uint32']
                assert row['stored_metadata_relative_offset']==independent['stored_metadata_relative_offset']
                counts['independent_support_provenance_checks']+=1
                stats=qualify(row,before,zstd)
                for key,value in stats.items():counts[key]+=value
                attached.add(identity)
            else:
                assert feature.get(SUMMARY)==prior.get(SUMMARY)
        assert attached==set(owners)
        history=next(s for s in before['asm_decoding']['streams'] if s['member']==expected['associations'][0]['history_blob_member'])
        diagnostics=history['topology']['unresolved']
        xyz=[d for d in diagnostics if d['kind']=='spline-surface']
        uv=[d for d in diagnostics if d['kind']=='pcurve']
        assert len(xyz)==16 and len(uv)==48 and len(diagnostics)==64
        assert all(d['reason']=='VBL component definitions decoded; standalone XYZ surface evaluator remains unsupported' for d in xyz)
        assert all(d['reason']=='Unobserved explicit UV pcurve subtype' for d in uv)
        counts.update(retained_XYZ_diagnostics=16,retained_UV_diagnostics=48)
        stream[SUMMARY]=copy.deepcopy(previous)
        counts.update(refined_source_summaries=1,recovered_source_associations=8,
                      removed_support_unresolved_rows=8,receiving_feature_annotation_lists=8)
    else:
        if expected['associations'] or expected['unresolved']:assert stream[SUMMARY]==old[SUMMARY]==expected
        else:assert SUMMARY not in stream and SUMMARY not in old
    assert after==before,(filename,'Unexpected old-output change',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),**counts,
        whole_output_unchanged=before==current,
        whole_output_exact_after_restoring_only_qualified_source_summary_and_owner_lists=True,
        old_tools_warnings_classifications_geometry_topology_placement_and_ASM_exact=True,
        baseline_output_sha256=digest(before),current_output_sha256=digest(current),
        qualified_difference_paths=differences(before,current))


def read_cache(path,side):
    value=json.loads(Path(path).read_text())
    assert value['files']==list(FILES) and value['baseline_commit']==BASELINE
    assert value['acquisition_main_calls']==10 and value['acquisition_passes']==1
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
    assert len(before)==len(current)==len(FILES)==10
    assert [o['file'] for o in before]==[str(ROOT/f) for f in FILES]==[o['file'] for o in current]
    goldens,defaults,supports=evidence()
    rows=[compare(b,a,f,goldens,defaults,supports,zstd) for b,a,f in zip(before,current,FILES)]
    totals={key:sum(r[key] for r in rows) for key in COUNT_KEYS}
    totals.update(saved_files=10,whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),
        unexpected_changes=0,comparator_baseline_main_calls=0 if baseline_cache else 10,
        comparator_current_main_calls=0 if current_cache else 10,live_API_calls=0)
    assert (totals['recovered_source_associations'],totals['boundary_edges'],totals['endpoint_operands'],
            totals['complete_FACE_name_groups'],totals['whole_output_unchanged_controls'])==(16,96,192,112,8)
    assert totals['support_count2_owners']==totals['support_count3_owners']==8
    assert totals['independent_default_summary_checks']==8 and totals['independent_support_provenance_checks']==16
    sources=('validate_surface_offset_intersection_integration.py','decode_surface_offset_sources.py',
             'decode_surface_offset_source_variants.py','decode_surface_offset_intersections.py','decode_basics.py')
    source_proof=json.loads((ROOT/SOURCE_EVIDENCE).read_text())
    codec_proof=json.loads((ROOT/EVIDENCE).read_text())
    frozen=('decode_surface_offset_sources.py','decode_surface_offset_source_variants.py','decode_surface_offset_intersections.py')
    for name in frozen:
        assert source_proof['source_sha256'][name]==sha(ROOT/name)
        assert codec_proof['source_sha256'][name]==sha(ROOT/name)
    return dict(scope='Two actual Rule witness archives recover exact bounded intersection FACE/EDGE/vertex source operands; eight previous controls and all unrelated outputs remain exact',
        baseline_commit=BASELINE,files=list(FILES),summary=totals,samples=rows,
        fixed_manifest_acquisition=dict(baseline_main_calls=10,current_main_calls=10,baseline_passes=1,current_passes=1,
            interpreter='/usr/bin/python3',baseline_call="baseline_outputs(FILES,zstd,revision='cf0ffb9')",
            current_call='for name in FILES: after.append(decode_basics(ROOT/name,z))',
            current_execution='One /usr/bin/python3 heredoc sequential pass; JSON-normalized full outputs saved to current cache',
            scope='Original fixed acquisition, distinct from cached comparator zero-main execution'),
        cache_provenance={side:dict(path=str(Path(p).resolve()),sha256=sha(p)) for side,p in (
            ('baseline',baseline_cache),('current',current_cache)) if p},
        frozen_production_sources_confirmed_against_both_independent_reports=list(frozen),
        evidence_sha256={f:sha(ROOT/f) for f in (EVIDENCE,SOURCE_EVIDENCE)},source_sha256={f:sha(ROOT/f) for f in sources},
        limitations=['Typed native source roles, explicit BODY mapping and full naming/incidence precede numerical geometry.',
            'Immediate support parent is retained separately from historical anchor owner; no persistent/current/API face identity is inferred.',
            'Existing XYZ/UV evaluator diagnostics and tool operation warnings remain unchanged.',
            'Independent focused full goldens qualify refinements; cached main outputs do not supply their own expected values.',
            'No live calls, whole corpus decoding, native regeneration or traversal semantics are claimed.'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache');p.add_argument('--current-cache');p.add_argument('--zstd-library')
    p.add_argument('--output',default='surface-offset-intersection-integration.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z,a.baseline_cache,a.current_cache);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
