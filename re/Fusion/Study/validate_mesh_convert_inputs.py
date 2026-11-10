"""Two-input parametric Convert proof; BaseFeature cases excluded, old outputs exact."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from validate_mesh_repair import context
from decode_mesh_convert import CONVERT,decode_mesh_convert
from decode_mesh_convert_inputs import decode_mesh_convert_inputs
from decode_mesh_geometry_variants import decode_mesh_contents_variants

ROOT=Path(__file__).resolve().parent
DIRECTORY='meshconvertoperations-5af73924aa60'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_source_arrays(geometry,actual):
    assert [v for p in geometry['component_node_coordinates_cm'] for v in p]==actual['original_polygon_mesh']['nodeCoordinatesAsDouble']
    assert geometry['triangle_node_indices']==actual['original_polygon_mesh']['triangleNodeIndices']
    assert geometry['node_count']==actual['original_polygon_mesh']['nodeCount']==4
    assert geometry['triangle_count']==actual['original_polygon_mesh']['triangleCount']==4


def validate(zstd):
    folder=ROOT/DIRECTORY
    truth=json.loads((folder/'ground_truth.json').read_text())
    assert len(truth['samples'])==3 and not truth['errors'] and (folder/'complete.txt').is_file()
    progress=json.loads((folder/'progress.json').read_text())
    assert progress['phase']=='batch_complete' and progress['sample_count']==progress['exported_sample_count']==3 and progress['error_count']==0
    assert 'terminal_status' not in truth
    assert digest(folder/'executed-generator-source.txt')==truth['executed_generator_sha256']
    assert digest(folder/'executed-mesh-source-helper.txt')==truth['mesh_source_helper_sha256']
    assert digest(folder/'executed-sdk-surface.txt')==truth['executed_sdk_surface_sha256']
    events=[json.loads(s) for s in (folder/'journal.jsonl').read_text().splitlines()]
    closes=[s for s in events if s['phase']=='owned_document_close_returned']
    assert len(closes)==3 and all(s['returned'] is True and s['save'] is False for s in closes)
    report=dict(scope='One actual two-input Faceted parametric Convert definition plus two actual BaseFeature-operation captures excluded from this helper. Native source/result/controller/history routes only; no source/result pairing or conversion regeneration.',
        interface='decode_mesh_convert_inputs(data,records,features,member,members)->decoded/unresolved/scope; rows feature_object_id/kindMeshConvert/name/class_guid/settings',
        integration=dict(order='Call after old decode_mesh_convert; append only successful multi-input rows, carry multi_input_variant_scope, remove only same-feature exact old singleton-header rejection.',
            cleared_old_reason='Only captured Faceted parametric Convert header supported',
            preserved='All generic retained source mesh prefix diagnostics, old Convert dictionaries and unrelated BaseFeature diagnostics remain separate.'),
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(folder/'ground_truth.json'),
            complete_marker=DIRECTORY+'/complete.txt',progress_phase='batch_complete',terminal_status_field_present=False,
            executed_generator_sha256=truth['executed_generator_sha256'],mesh_source_helper_sha256=truth['mesh_source_helper_sha256'],
            executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],sdk_runtime_sha256=truth['sdk_runtime_sha256']),
        native_schema=dict(class_guid=CONVERT,source_count_uint32_offset=10,source_list_reference_offsets=[14,25],
            source_list_class_guid='D6FB6F05-98CD-4BFF-BF90-594F77725DC1',source_list_payload_extent=20,
            result_anchor_count_uint32_offset=46,result_anchor_reference_offsets=[50,61],nil_uuid_string_offset=80,
            repeated_selection_count_uint32_offset=159,repeated_selection_ref_offset=163,
            repeated_order=['source1 proxy','source1 descriptor','source2 proxy','source2 descriptor'],
            state_count=2,state_extent=52,state_controller_reference_offsets=[6,25],
            state_literal_uint64_offsets=[17,36,44],state_literal_uint64_values=[1,2,3],
            controller_class_guid='ABA79BE7-D8D2-4C17-B59B-C2035E111F77',controller_payload_extent=134,
            controller_UUID_scope='Exact unique UUID equality joins controller to owned result anchor; no source mesh correspondence inferred',
            invariant_controls_scope='Native header words0/3 and literal labels are preserved without uncontrasted method/operation enum or topology-ID meanings.'),
        samples=[],malformed_guards=[],legacy_controls=[],
        limitations=['Two source lists and two result anchors are explicit independent native lists. source_to_result_pairing stays None; ordinal, name and geometry matches do not pair them.',
            'Only observed two-input Faceted parametric schema admitted. Three or more inputs, mixed/open inputs, Prismatic/Organic and other state/controller layouts remain unsupported.',
            'BaseFeature add returns null in both captures while independent mesh/BRep/history collections change. This helper neither calls null failure nor relabels BaseFeature300 as MeshConvert.',
            'Native retained source owner/BaseMesh/asset routes do not promote source current membership, hidden/deleted flags or API BaseFeature ownership.',
            'Controller literal labels1234, table0..4, leading words1/2 and opaque uint64 are not face IDs, global indices or replay instructions.',
            'Native BODY stored-ID joins precede independent geometry corroboration; no coordinates, bounds, default names or array order choose native identities.',
            'Current collection membership and result anchor ownership do not establish general lifetime, final-state identity or persistent topology. No native writer or conversion algorithm implemented.'])
    positive=None;source_checks=controller_checks=0
    for actual in truth['samples']:
        filename=DIRECTORY+'/'+actual['file']
        assert actual['close_owned_document_returned'] is True and not actual['getter_errors']
        assert actual['export']['sha256']==digest(ROOT/filename) and actual['export']['size_bytes']==(ROOT/filename).stat().st_size
        assert actual['timeline_count']==actual['timeline_marker_position']
        data,records,features,member,members=context(filename,zstd)
        before=copy.deepcopy(features)
        old=decode_mesh_convert(data,records,features,member,members)
        mesh_summary=decode_mesh_contents_variants(data,records,member,members)
        decoded=decode_mesh_convert_inputs(data,records,features,member,members)
        assert before==features
        if actual['case']!='two_mesh_parametric':
            assert not any(r.is_primary and r.class_guid==CONVERT for r in records)
            assert not decoded['decoded'] and not decoded['unresolved'] and not old['decoded'] and not old['unresolved']
            assert actual['add_returned_nonnull'] is False and actual['actual_returned_identity'] is None
            assert actual['component_meshes_after_convert']['count']==actual['component_brep_after_convert']['count']==1
            assert actual['convert_collection_count_after']==0
            report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=decoded,
                prior_convert_summary=old,expected_mesh_contents=mesh_summary,
                API_add_returned_null=True,actual_current_mesh_count=1,actual_current_BRep_count=1,
                actual_Convert_collection_count=0,native_Convert_class_record_count=0,
                scope='BaseFeature operation actual effects retained independently; excluded from parametric Convert helper, not assumed failed or assigned a source-result operation from null return.'))
            continue
        assert not decoded['unresolved'] and len(decoded['decoded'])==1
        row,=decoded['decoded'];settings=row['settings']
        assert old['decoded']==[] and len(old['unresolved'])==1 and old['unresolved'][0]['feature_object_id']==row['feature_object_id']
        assert old['unresolved'][0]['reason']=='Only captured Faceted parametric Convert header supported'
        assert actual['add_returned_nonnull'] is True and actual['convert_collection_count_after']==1
        assert actual['component_meshes_after_convert']['count']==0 and actual['component_brep_after_convert']['count']==2
        assert actual['input_body_equals_import_handles'] is True and actual['roll_before_feature_returned'] is True
        api=actual['returned_at_timeline_end']['snapshot'];rolled=actual['returned_before_node']['snapshot']
        assert actual['input_before_add']['meshConvertMethodType']==api['meshConvertMethodType']==rolled['meshConvertMethodType']==0
        assert actual['input_before_add']['meshConvertOperationType']==0 and api['isParametric'] is True
        assert api['healthState']==0 and api['errorOrWarningMessage']=='' and row['name']==api['name']
        assert len(settings['source_mesh_selections'])==len(settings['qualified_source_meshes'])==len(rolled['inputBodies'])==2
        sources=[]
        for selection,source,actual_identity,actual_source in zip(settings['source_mesh_selections'],settings['qualified_source_meshes'],rolled['inputBodies'],actual['selected_meshes_before_convert']):
            assert source['mesh_object_id']==selection['mesh_object_id']
            assert source['name']==actual_identity['name']==actual_source['name']
            assert source['retained_membership_status']=='NotInCountedMembers' and source['retained_owner_collection_member_ids']==[]
            assert actual_source['baseOrFormFeature'] is None
            check_source_arrays(source['geometry'],actual_source)
            source_checks+=1
            sources.append(dict(native_mesh_object_id=source['mesh_object_id'],source_custom_name=source['name'],
                exact_arrays_match_actual_before_add_mesh=True,rolled_getter_identity_custom_name=actual_identity['name'],retained_source_not_in_current_members=True,
                API_baseOrFormFeature=None,native_BaseMesh_feature_id=source['base_mesh_feature_object_id']))
        assert settings['source_to_result_pairing'] is None
        assert len(set(settings['result_native_body_object_ids']))==len(settings['result_body_anchors'])==2
        assert all(a['source_owner_object_id']==row['feature_object_id'] for a in settings['result_body_anchors'])
        assert len(settings['history_controllers'])==2
        for c in settings['history_controllers']:
            anchors=[a for a in settings['result_body_anchors'] if a['native_uuid_text']==c['native_uuid_text']]
            assert len(anchors)==1 and anchors[0]['object_id']==c['matched_result_anchor_object_id']
            assert anchors[0]['native_body_object_id']==c['matched_native_body_object_id']
            assert c['exact_payload_replay'] is True and c['controller_literal_labels']=='1234'
            assert c['controller_stored_table']==list(range(5))
            controller_checks+=1
        layout=settings['layout']
        assert layout['exact_full_payload_replay'] is layout['exact_state_payload_replay'] is True
        assert bytes.fromhex(layout['feature_body_hex'])==data[layout['feature_body_offset']:layout['feature_body_end_offset']]
        assert len(mesh_summary['unresolved'])==2 and all(r['reason']=='Unobserved opt-in native mesh prefix' for r in mesh_summary['unresolved'])
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=decoded,
            prior_convert_summary=old,expected_mesh_contents=mesh_summary,source_API_corroboration=sources,
            native_result_body_ids=settings['result_native_body_object_ids'],actual_current_BRep_count=2,
            actual_current_mesh_count=0,actual_returned_object_type=actual['actual_returned_identity']['objectType'],
            source_to_result_pairing=None,full_feature_state_and_controller_payload_replays=True,owned_document_closed_true=True))
        positive=data,records,features,member,members,row
    data,records,features,member,members,row=positive
    settings=row['settings'];fid=row['feature_object_id'];by_id={r.object_id:r for r in records if r.is_primary};feature_record=by_id[fid]
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    def reject(label,offset,payload):
        damaged=bytearray(data);damaged[offset:offset+len(payload)]=payload
        answer=decode_mesh_convert_inputs(bytes(damaged),records,features,member,members)
        assert not answer['decoded'] and len(answer['unresolved'])==1 and answer['unresolved'][0]['class_guid']==CONVERT
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offset=offset,rejected=True,reason=answer['unresolved'][0]['reason']))
    reject('unsupported source count3',feature_record.body+10,struct.pack('<I',3))
    reject('duplicate source list references',feature_record.body+25,ref(settings['source_list_object_ids'][0]))
    proxy=by_id[settings['source_mesh_selections'][0]['proxy_object_id']]
    reject('source proxy owned by unrelated BaseMesh',proxy.end-11,ref(218))
    reject('result anchor count differs from observed2',feature_record.body+46,struct.pack('<I',1))
    anchor=by_id[settings['result_anchor_object_ids'][0]]
    reject('result anchor owned by import BaseFeature',anchor.body+91,ref(204))
    state=by_id[settings['state_object_id']]
    reject('state controller count differs from observed2',state.body+2,struct.pack('<I',1))
    controller=by_id[settings['history_controllers'][0]['controller_object_id']]
    existing=data[controller.body+7:controller.body+9]
    reject('controller UUID does not match an owned result anchor',controller.body+7,('1' if existing!='1'.encode('utf-16le') else '2').encode('utf-16le'))
    reject('dependency descriptor replaced by typed BaseMesh',feature_record.body+174,ref(218))
    old=json.loads((ROOT/'mesh-convert-decoding.json').read_text())
    for saved in old['samples']:
        d,rs,fs,n,m=context(saved['archive'],zstd)
        original=decode_mesh_convert(d,rs,fs,n,m)
        assert original==saved['expected_decoded']
        empty=decode_mesh_convert_inputs(d,rs,fs,n,m)
        assert not empty['decoded'] and not empty['unresolved']
        report['legacy_controls'].append(dict(archive=saved['archive'],old_Convert_full_summary_exact=True,new_helper_no_candidate=True))
    report['summary']=dict(actual_capture_archives=3,decoded_multi_input_features=1,BaseFeature_cases_excluded=2,
        exact_retained_source_API_array_checks=source_checks,exact_controller_UUID_result_correspondences=controller_checks,
        full_feature_payload_replays=1,full_state_payload_replays=1,full_controller_payload_replays=2,
        malformed_guards=len(report['malformed_guards']),old_Convert_full_summaries_exact=len(report['legacy_controls']),
        common_parser_changes=0,main_runs=0,live_calls=0)
    report['runtime_source_sha256']={f:digest(ROOT/f) for f in ('decode_mesh_convert_inputs.py','validate_mesh_convert_inputs.py',
        'decode_mesh_convert.py','decode_mesh_convert_result_bodies.py','decode_retained_mesh_sources.py','decode_body_asm_identifiers.py')}
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default=str(ROOT/'mesh-convert-input-decoding.json'))
    args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd)
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':main()
