"""Focused native RigidGroup membership/cache proof and negative API controls."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct

from decode_asbuilt_joints import decode_asbuilt_joints,make_asbuilt_context_readers
from decode_basics import decode_basics
from decode_rigid_groups import decode_rigid_groups
from decode_sketch import same
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
CAPTURE='rigidgroups-0784a68632cd'
NESTED_ERRORS=('requested_child_native.entityToken','requested_child_native.nativeObject.entityToken',
 'requested_child_native.bodies[0].entityToken','all_before[1].nativeObject.entityToken',
 'group_initial.occurrences[2].nativeObject.entityToken','all_immediately_after[1].nativeObject.entityToken',
 'group_final.occurrences[2].nativeObject.entityToken','all_after[1].nativeObject.entityToken')


def validate(root=ROOT,zstd_library=None):
    root=Path(root);folder=root/CAPTURE
    truth=json.loads((folder/'ground_truth.json').read_text())
    assert truth['terminal_status']=='complete' and truth['exported_sample_count']==3 and not truth['errors']
    assert hashlib.sha256((folder/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256']
    report=dict(scope='Three actual native type11 RigidGroups: root membership plus explicit two-level nested membership; independent API contrasts and stored matrix copies, no solved assembly state',
        interface='decode_rigid_groups(data, records, assembly, features) -> decoded/unresolved/scope/placement_limitation',
        shared_factory='make_asbuilt_context_readers(data, records, assembly, *, allow_nested=False); mode2 requires explicit opt-in and typed parent/child collection proof',
        provenance=dict(capture_directory=CAPTURE,ground_truth_sha256=hashlib.sha256((folder/'ground_truth.json').read_bytes()).hexdigest(),
            journal_sha256=hashlib.sha256((folder/'journal.jsonl').read_bytes()).hexdigest(),
            actual_executed_generator_sha256=truth['executed_generator_sha256'],executed_source_snapshot_verified=True,
            source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
                'GenerateRigidGroupContrasts.py','decode_rigid_groups.py','validate_rigid_groups.py',
                'decode_asbuilt_joints.py','decode_assembly.py','decode_dependencies.py')}),
        integration='Publish rigid_groups separately; qualify successful feature_object_id as RigidGroup and matching object_id as native group JOINT. Preserve old strict AsBuilt diagnostics and all solved-placement warnings. No new feature GUID is inferred: actual AA8B As-built feature +7F5A common JOINT type11 establishes the subtype.',
        samples=[],malformed_guards=[],old_AsBuilt_exact_controls=[],
        suppression_negative_control={},limitations=[
            'Native expanded occurrence membership is explicit. The public API has no includeChildren getter; the true request and expanded child result do not map a native includeChildren flag.',
            'The requested suppressionTrue setter completes without exception but actual getter remainsFalse; neither requestedTrue nor actualFalse alone qualifies native suppression bits.',
            'Stored relative matrices equal owned context copies. These translated examples are not evidence of generalized basis semantics or a kinematic solve.',
            'Nested API token getter failures are retained. Native membership uses typed UUID paths and reciprocal collection ownership; opaque token equality/absence and geometry coordinates do not choose native IDs.',
            'Only two root members or two root members plus one explicitly routed child are admitted. Repeated component instances, deeper contexts, other group layouts/lifecycle/native writing remain unsupported.',
            'The AsBuilt common-context factory default outputs and mode2 rejection remain exact; nested support is opt-in for this group stage.'])
    fixtures=[]
    for sample in truth['samples']:
        assert sample['close_owned_document_returned'] is True and not sample['setter_errors']
        assert sample['compute_before'] is sample['compute_after'] is True
        if sample['case']=='nested_include_children':assert tuple(e['field'] for e in sample['getter_errors'])==NESTED_ERRORS
        else:assert not sample['getter_errors']
        p=folder/sample['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==sample['export']['sha256']
        stream=decode_basics(p,zstd_library)['streams'][0]
        members=read_members(p,zstd_library);data=members[stream['member']]
        records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')])
        before=deepcopy(stream)
        result=decode_rigid_groups(data,records,stream['assembly_decoding'],stream['features'])
        assert stream==before and len(result['decoded'])==1 and not result['unresolved']
        row=result['decoded'][0];api=sample['actual_group_final'];initial=sample['actual_group_initial']
        assert row['name']==api['name'] and sample['rigid_group_names']==[row['name']] and sample['rigid_group_count']==1
        assert initial['is_suppressed'] is api['is_suppressed'] is False
        assert row['include_children'] is row['is_suppressed'] is None
        assert row['stored_constraint_type_code']==11
        paths={r['native_occurrence_object_id']:r for r in stream['assembly_decoding']['occurrence_paths']}
        names=[paths[i]['path'] for i in row['stored_occurrence_member_object_ids']]
        assert names==[p['full_path_name'] for p in api['occurrences']]
        assert row['occurrence_count']==api['occurrence_count']==len(api['occurrences'])
        assert [p['full_path_name'] for p in initial['occurrences']]==names
        assert len(row['stored_relative_matrices'])==row['occurrence_count']-1
        for matrix,context in zip(row['stored_relative_matrices'],row['ordered_occurrence_contexts']):assert same(matrix,context['stored_context_matrix'])
        snapshots=[{p['full_path_name']:p for p in sample[key]} for key in (
            'all_occurrences_before','all_occurrences_immediately_after_add','all_occurrences_after')]
        assert all(set(s)==set(snapshots[0]) for s in snapshots)
        for name in snapshots[0]:
            assert same(snapshots[0][name]['transform'],snapshots[1][name]['transform'])
            assert same(snapshots[0][name]['transform'],snapshots[2][name]['transform'])
        selected=[p['full_path_name'] for p in sample['selected_occurrences_before']]
        if sample['case']=='nested_include_children':
            assert len(selected)==2 and len(names)==3 and names[:2]==selected
            assert sample['requested_include_children'] is True
            nested=row['ordered_occurrence_contexts'][2]
            assert nested['stored_route_mode']==2 and nested['native_occurrence_object_id_path']==row['stored_occurrence_member_object_ids'][1:]
        else:
            assert names==selected and sample['requested_include_children'] is False
        legacy=decode_asbuilt_joints(data,records,stream['assembly_decoding'],stream['features'])
        assert not legacy['decoded'] and len(legacy['unresolved'])==1
        report['samples'].append(dict(file=str(p.relative_to(root)),archive_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            expected_decoded=result,actual_requested_include_children=sample['requested_include_children'],
            actual_include_children_getter=None,actual_selected_occurrences=sample['selected_occurrences_before'],
            actual_group_initial=initial,actual_group_final=api,actual_getter_errors=sample['getter_errors'],
            actual_health_state=sample['health_state'],actual_warning=sample['warning'],
            exact_native_order_matches_actual_returned_members=True,before_immediate_after_final_placements_unchanged=True,
            stored_relative_matrix_context_copies_exact=True,decoder_input_unchanged=True,
            retained_strict_AsBuilt_diagnostics=legacy['unresolved']))
        fixtures.append((sample['case'],data,records,stream,row))
        if sample['case']=='root_suppressed':
            assert sample['requested_is_suppressed'] is True and sample['suppression_setter_success'] is True
            assert sample['observed_suppression_matches_request'] is False
            report['suppression_negative_control']=dict(file=str(p.relative_to(root)),requested=True,
                setter_no_exception=True,actual_initial=False,actual_final=False,
                decoder_is_suppressed=None,native_true_false_contrast_established=False)
    _,data,records,stream,row=next(f for f in fixtures if f[0]=='nested_include_children')
    primary={r.object_id:r for r in records if r.is_primary}
    nested=row['ordered_occurrence_contexts'][2]
    # Default factory must preserve its old rejection of a nested route.
    default=make_asbuilt_context_readers(data,records,stream['assembly_decoding'])
    try:default['frame'](nested['object_id'],row['feature_object_id'],2)
    except ValueError as error:report['default_nested_route_control']=dict(rejected=True,reason=str(error))
    else:raise AssertionError('Nested route accepted without explicit opt-in')
    native_occurrences={r['object_id']:r for r in stream['assembly_decoding']['native_occurrences']}
    wrong_parent=native_occurrences[row['stored_occurrence_member_object_ids'][0]]['instance_guid_text'].encode('utf-16le')
    mods=(
        ('Nested parent UUID selects another valid root occurrence',nested['route_object_id'],10,wrong_parent),
        ('Nested route count is unsupported',nested['route_object_id'],2,struct.pack('<I',3)),
        ('Member frame reciprocal owner differs',nested['object_id'],50,struct.pack('<Q',999999)),
        ('Repeated matrix-copy trailer differs',row['object_id'],218,b'\1'),
        ('Expanded context/native member order differs',row['object_id'],6,struct.pack('<Q',row['stored_occurrence_member_object_ids'][1])),
        ('Group terminal counted table value differs',row['object_id'],439,struct.pack('<I',9)),
        ('Group joint collection no longer selects this native group',row['collection_object_id'],17,struct.pack('<Q',999999)))
    for label,identity,offset,payload in mods:
        changed=bytearray(data);pos=primary[identity].body+offset;changed[pos:pos+len(payload)]=payload
        value=decode_rigid_groups(bytes(changed),records,stream['assembly_decoding'],stream['features'])
        assert not value['decoded'] and len(value['unresolved'])==1,label
        report['malformed_guards'].append(dict(control=label,rejected=True,reason=value['unresolved'][0]['reason']))
    golden=json.loads((root/'asbuilt-joint-decoding.json').read_text())
    for old in golden['samples']:
        p=root/old['file'];s=decode_basics(p,zstd_library)['streams'][0];m=read_members(p,zstd_library);d=m[s['member']]
        rs,_=design_records(d,m[s['member'].replace('BulkStream.dat','MetaStream.dat')])
        actual=decode_asbuilt_joints(d,rs,s['assembly_decoding'],s['features'])
        assert actual==old['expected_decoded'],old['file']
        no_group=decode_rigid_groups(d,rs,s['assembly_decoding'],s['features'])
        assert not no_group['decoded'] and not no_group['unresolved']
        report['old_AsBuilt_exact_controls'].append(dict(file=old['file'],refactored_summary_exact_committed_golden=True,
            new_group_helper_does_not_recover_or_reject=True))
    report['validation']=dict(actual_RigidGroup_files=3,decoded_native_groups=3,expanded_member_associations=7,
        stored_matrix_context_copy_comparisons=4,nested_parent_child_relationships=1,malformed_guards=len(mods),
        old_AsBuilt_exact_golden_controls=3,default_nested_route_rejection_preserved=True,
        retained_API_token_getter_errors=8,successful_suppression_contrasts=0,
        live_Fusion_calls_by_validator=0,solved_placement_claim=False,all_checks_passed=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--zstd-library')
    parser.add_argument('--output',type=Path,default=ROOT/'rigid-group-decoding.json')
    args=parser.parse_args();result=validate(args.root,args.zstd_library)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['validation'],sort_keys=True))
