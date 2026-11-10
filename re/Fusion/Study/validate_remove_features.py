"""Public RemoveFeature actual target/owner proof and historical-reader controls."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_direct_body_features import decode_direct_body_features
from decode_remove_features import decode_remove_features
from decode_sketch import same
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
CAPTURE='removecontrasts-9c5f83456a0e'
NESTED_ERRORS=('requested_native_child_before.entityToken','requested_native_child_before.nativeObject.entityToken',
 'requested_native_child_before.bodies[0].entityToken','requested_target_before.nativeObject.entityToken',
 'before.all_occurrences[0].nativeObject.entityToken','actual_item_to_remove.entityToken',
 'actual_item_to_remove.nativeObject.entityToken','actual_item_to_remove.bodies[0].entityToken',
 'rolled_back.all_occurrences[0].nativeObject.entityToken','source_component_after.bodies[0].entityToken')


def validate(root=ROOT,zstd_library=None):
    root=Path(root);folder=root/CAPTURE;truth=json.loads((folder/'ground_truth.json').read_text())
    assert truth['terminal_status']=='complete' and truth['exported_sample_count']==3 and not truth['errors']
    assert hashlib.sha256((folder/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256']
    report=dict(scope='Three actual public RemoveFeatures.add captures with independently rolled-back itemToRemove and collection observations; target identity/owner decoding, not general lifecycle replay',
        interface='decode_remove_features(data, records, features, assembly, *, body_selections=None, component_creations=None) -> decoded/unresolved/scope',
        provenance=dict(capture_directory=CAPTURE,ground_truth_sha256=hashlib.sha256((folder/'ground_truth.json').read_bytes()).hexdigest(),
            journal_sha256=hashlib.sha256((folder/'journal.jsonl').read_bytes()).hexdigest(),actual_executed_generator_sha256=truth['executed_generator_sha256'],
            source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
                'GenerateRemoveContrasts.py','decode_remove_features.py','validate_remove_features.py',
                'decode_component_creation.py','decode_body_selections.py','decode_direct_body_features.py',
                'decode_asbuilt_joints.py','decode_dependencies.py','decode_timeline.py')}),
        integration='Classify only decoded feature_object_id as reported kind RemoveBody/RemoveInstance and attach remove_feature_settings. Preserve old strict direct-body failures and current occurrence collection diagnostics. Do not restore paths or change visibility/body lifetime based on this summary.',
        samples=[],malformed_guards=[],prior_direct_body_controls=[],limitations=[
            'Root public RemoveBody has existing owned body proxy/descriptor/anchor grammar and a66-byte ordinary feature footer. BoundaryFill children retain their separate explicit typed parent route.',
            'RemoveInstance selects a typed occurrence datum from the independently decoded CreateComponent/snapshot chain. Historical source placements are not final geometry or a native replay.',
            'Nested root API call normalizes to a parent-owned native RemoveInstance. Its actual itemToRemove getter returns the native child with local transform and no assemblyContext; the original requested proxy path is a separate observation.',
            'Declared-parent route labels follow explicit collection/owner/native-occurrence links only when unique. They are not restored current paths; removed targets remain absent from current member lists.',
            'Actual feature bodies/collection counts and post-removal component definitions are getter evidence, not claims of body destruction or final visibility.',
            'Current assembly diagnostics remain unchanged; ambiguity, repeated parent component instances, deeper contexts, mesh/surface variants and general lifecycle are unsupported.',
            'Eleven API token failures are retained; native target identity does not use token contents or coordinate matching.'])
    fixtures={}
    for sample in truth['samples']:
        assert sample['close_owned_document_returned'] is True and sample['health_state']==0 and sample['warning']==''
        assert sample['compute_before'] is sample['compute_after'] is True and sample['is_suppressed'] is False
        expected_errors=() if sample['case']=='root_body' else (('source_component_after.bodies[0].entityToken',) if sample['case']=='root_occurrence' else NESTED_ERRORS)
        assert tuple(e['field'] for e in sample['getter_errors'])==expected_errors
        p=folder/sample['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==sample['export']['sha256']
        stream=decode_basics(p,zstd_library)['streams'][0]
        members=read_members(p,zstd_library);data=members[stream['member']]
        records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')])
        before=deepcopy(stream)
        result=decode_remove_features(data,records,stream['features'],stream['assembly_decoding'],
            body_selections=stream['body_selections'],component_creations=stream['component_creations'])
        assert stream==before and len(result['decoded'])==1 and not result['unresolved']
        row=result['decoded'][0];target=row['target'];actual=sample['actual_item_to_remove'];requested=sample['requested_target_before']
        assert row['name']==sample['feature_identity']['name']
        assert row['component_name']==sample['feature_identity']['parent_component_name']
        assert row['state']['is_suppressed']==sample['is_suppressed']
        assert row['state']['is_rolled_back'] is False
        before_counts=sample['collections_before'];rollback_counts=sample['collections_rolled_back'];after_counts=sample['collections_after']
        before_tuple=(before_counts['root']['body_count'],before_counts['root']['occurrence_count'],before_counts['all_occurrence_count'])
        rollback_tuple=(rollback_counts['root']['body_count'],rollback_counts['root']['occurrence_count'],rollback_counts['all_occurrence_count'])
        after_tuple=(after_counts['root']['body_count'],after_counts['root']['occurrence_count'],after_counts['all_occurrence_count'])
        assert before_tuple==rollback_tuple
        if sample['case']=='root_body':
            assert row['kind']=='RemoveBody' and target['kind']=='Body'
            assert actual['name']==requested['name']==target['body_descriptor']['body_properties']['name']=='RemoveTargetBody'
            assert before_tuple==(2,0,0) and after_tuple==(1,0,0)
            assert target['native_body_object_id']==275 and target['source_owner_object_id']==243
            assert any(e['feature_object_id']==row['feature_object_id'] and e['reason']=='Unobserved RemoveBody framing' for e in stream['direct_body_features']['unresolved'])
        else:
            assert row['kind']=='RemoveInstance' and target['kind']=='Occurrence'
            assert target['component_name']==actual['component_name']
            assert actual['name']==target['component_name']+':'+str(target['instance_number'])
            assert same(target['stored_native_occurrence']['local_transform'],actual['transform'])
            assert same(target['source_creation']['snapshot_transform'],actual['transform'])
            assert target['is_listed_in_stored_parent_collection'] is False
            assert any(e.get('reason')=='Occurrence is absent from its declared parent collection' for e in stream['assembly_decoding']['unresolved'])
            assert not target['source_creation']['occurrence_paths']
            assert target['declared_parent_path_label']==requested['full_path_name']
            assert sample['source_component_after']['body_count']==1
            if sample['case']=='root_occurrence':
                assert before_tuple==(0,2,2) and after_tuple==(0,1,1)
                assert row['component_name']=='(Unsaved)' and len(target['declared_parent_route'])==1
                assert actual['full_path_name']==requested['full_path_name']
            else:
                assert before_tuple==(0,2,3) and after_tuple==(0,2,2)
                assert row['component_name']=='RemoveParentComponent' and len(target['declared_parent_route'])==2
                assert actual['assembly_context_path'] is None and requested['assembly_context_path']=='RemoveParentComponent:1'
                assert actual['full_path_name']=='RemoveTargetChild:1' and '+' in requested['full_path_name']
                assert sample['remove_feature_count']==0 and sample['parent_component_after']['occurrence_count']==0
        report['samples'].append(dict(file=str(p.relative_to(root)),archive_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            expected_decoded=result,actual_requested_target=requested,actual_rolled_back_item_to_remove=actual,
            actual_feature_identity=sample['feature_identity'],actual_feature_bodies=sample['actual_feature_bodies'],
            actual_collection_counts=dict(before=list(before_tuple),rolled_back=list(rollback_tuple),after=list(after_tuple)),
            actual_getter_errors=sample['getter_errors'],actual_root_remove_feature_count=sample['remove_feature_count'],
            actual_source_component_after=sample['source_component_after'],
            native_target_matches_independent_API=True,decoder_does_not_mutate_inputs=True,
            retained_assembly_diagnostics=stream['assembly_decoding']['unresolved'],
            retained_strict_direct_body_diagnostics=stream['direct_body_features']['unresolved']))
        fixtures[sample['case']]=(data,records,stream,row)
    data,records,stream,row=fixtures['root_body'];primary={r.object_id:r for r in records if r.is_primary}
    body_mods=(('Public body repeated proxy differs',row['feature_object_id'],97,struct.pack('<Q',999999)),
        ('Public body proxy owner differs',row['target']['selection_record_object_id'],95,struct.pack('<Q',999999)),
        ('Historical selected body anchor differs',row['target']['descriptor_object_id'],202,struct.pack('<Q',999999)))
    def guard(label,identity,offset,payload,fixture):
        d,rs,s,_=fixture;by={r.object_id:r for r in rs if r.is_primary};changed=bytearray(d);pos=by[identity].body+offset;changed[pos:pos+len(payload)]=payload
        value=decode_remove_features(bytes(changed),rs,s['features'],s['assembly_decoding'],
            body_selections=s['body_selections'],component_creations=s['component_creations'])
        assert not value['decoded'] and len(value['unresolved'])==1,label
        report['malformed_guards'].append(dict(control=label,rejected=True,reason=value['unresolved'][0]['reason']))
    for mod in body_mods:guard(*mod,fixtures['root_body'])
    data,records,stream,row=fixtures['nested_occurrence'];target=row['target']
    mods=(('Instance target datum is absent',row['feature_object_id'],15,struct.pack('<Q',999999)),
        ('Occurrence datum bookkeeping backlink differs',target['datum_bookkeeping_object_id'],13,struct.pack('<Q',999999)),
        ('Creation snapshot matrix differs from native occurrence cache',target['snapshot_object_id'],43,struct.pack('<d',9.)),
        ('Removal feature component scope differs from target declared parent',row['component_scope_object_id'],4,struct.pack('<Q',3)),
        ('Selected occurrence datum aliases another existing target',target['occurrence_datum_object_id'],3,struct.pack('<Q',459)))
    for mod in mods:guard(*mod,fixtures['nested_occurrence'])
    old=json.loads((root/'direct-body-feature-decoding.json').read_text())
    for sample in old['samples']:
        p=root/sample['file'];s=decode_basics(p,zstd_library)['streams'][0];m=read_members(p,zstd_library);d=m[s['member']]
        rs,_=design_records(d,m[s['member'].replace('BulkStream.dat','MetaStream.dat')])
        direct=decode_direct_body_features(d,rs,s['body_selections']);assert direct==sample['expected_summary']
        separate=decode_remove_features(d,rs,s['features'],s['assembly_decoding'],body_selections=s['body_selections'],component_creations=s['component_creations'])
        assert not separate['decoded'] and not separate['unresolved']
        report['prior_direct_body_controls'].append(dict(file=sample['file'],old_summary_exact_golden=True,
            new_public_remove_helper_does_not_recover_or_reject=True))
    report['validation']=dict(actual_public_remove_files=3,decoded_removal_targets=3,root_body_targets=1,occurrence_targets=2,
        independently_scoped_parent_owned_nested_target=1,retained_current_collection_absence_diagnostics=2,
        malformed_guards=len(report['malformed_guards']),old_BaseFeature_BoundaryFill_golden_controls=3,
        retained_API_token_getter_errors=11,live_Fusion_calls_by_validator=0,final_visibility_or_replay_claim=False,all_checks_passed=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--zstd-library')
    parser.add_argument('--output',type=Path,default=ROOT/'remove-feature-decoding.json')
    args=parser.parse_args();r=validate(args.root,args.zstd_library)
    args.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['validation'],sort_keys=True))
