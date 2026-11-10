"""Actual AsBuilt Joint controls/provenance and ordinary-motion regression goldens."""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_asbuilt_joints import decode_asbuilt_joints, ASBUILT
from decode_basics import decode_basics
from decode_joints import decode_joints
from decode_placement import IDENTITY
from decode_sketch import reference,same
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
CAPTURE='asbuiltjoints-790406c4498b'


def validate(root=ROOT,zstd_library=None):
    root=Path(root);folder=root/CAPTURE
    truth=json.loads((folder/'ground_truth.json').read_text())
    assert truth['terminal_status']=='complete' and truth['exported_sample_count']==3 and not truth['errors']
    executed=(folder/'executed-generator-source.txt').read_bytes()
    assert hashlib.sha256(executed).hexdigest()==truth['executed_generator_sha256']
    report=dict(scope='Three actual owned root As-built rigid/revolute/slider captures; explicit occurrence/point geometry provenance and shared cached motion semantics, without assembly solving',
        interface='decode_asbuilt_joints(data, records, assembly, features) -> decoded/unresolved/scope/placement_limitation',
        provenance=dict(capture_directory=CAPTURE,ground_truth_sha256=hashlib.sha256((folder/'ground_truth.json').read_bytes()).hexdigest(),
            journal_sha256=hashlib.sha256((folder/'journal.jsonl').read_bytes()).hexdigest(),
            actual_executed_generator_sha256=truth['executed_generator_sha256'],executed_generator_snapshot_replayed=True,
            source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
                'GenerateAsBuiltJointContrasts.py','decode_asbuilt_joints.py','validate_asbuilt_joints.py',
                'decode_joints.py','decode_assembly.py','decode_dependencies.py','decode_selection.py')}),
        integration=dict(summary='asbuilt_joints',feature_identity_key='feature_object_id',native_joint_identity_key='object_id',
            feature_class_guid=ASBUILT,
            classification='Classify only fully decoded AsBuilt feature identities. Clear only matching NativeJoint unresolved identity after qualified success. Preserve unrelated unsupported features and all solved-placement limitations.',
            placement_guard='AsBuilt feature AA8B3D40... is assembly-unsolved even if its common JOINT reference is absent/corrupt; actual three captures additionally contain existing JOINT7F5A0426...'),
        samples=[],malformed_guards=[],ordinary_joint_goldens=[],
        limitations=['Only same-root direct occurrences, one joint collection member, principal Rigid/Revolute/Slider and nonrigid native component-origin point input are admitted.',
            'Native context matrices and member ordering remain stored caches/associations. Feature ordered input contexts Moving/Fixed differ from common joint member order Fixed/Moving; no ordinal shortcut bridges them.',
            'Marker1 matrix branch preserves exact forty-byte prefix and39-byte opaque footer. Their numeric/reference-looking fields have no invented semantics.',
            'Rigid geometry is explicitly absent in native/API controls. Its API joint.transform remains an independent getter observation; it is not supplied as a decoded geometric origin.',
            'Native point-provider sentinel vector [-1,-1,-1] is literal, not a source point position. Typed native leaf/component origin and owned context/backend cache establish point provenance.',
            'As-built native suppression flags, ordinary-Joint alignment controls, arbitrary source geometry, custom directions, nested contexts, lifecycle replay and native writing remain unresolved.',
            'Unchanged before/after occurrence getters in these three cases do not establish a general joint solver or solved world placement.'])
    fixtures=[]
    for sample in truth['samples']:
        assert not sample['getter_errors'] and not sample['setter_errors'] and sample['close_owned_document_returned'] is True
        assert sample['motion_input_setter_returned'] is True and sample['compute_before'] is sample['compute_after'] is True
        p=folder/sample['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==sample['export']['sha256']
        stream=decode_basics(p,zstd_library)['streams'][0]
        members=read_members(p,zstd_library);data=members[stream['member']]
        records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')])
        before=deepcopy(stream)
        result=decode_asbuilt_joints(data,records,stream['assembly_decoding'],stream['features'])
        assert stream==before and len(result['decoded'])==1 and not result['unresolved']
        row=result['decoded'][0];api=sample['actual_motion']
        assert row['joint_type'].lower()==sample['case'] and row['api_joint_type_code']==api['joint_type']
        assert row['direction_codes']==api['directions'] and row['is_suppressed'] is None and sample['is_suppressed'] is False
        assert sample['as_built_joint_count']==1 and sample['as_built_joint_names']==[row['name']]
        occurrences={o['object_id']:o for o in stream['assembly_decoding']['native_occurrences']}
        paths={o['native_occurrence_object_id']:o for o in stream['assembly_decoding']['occurrence_paths']}
        names=[paths[c['native_occurrence_object_id']]['path'] for c in row['ordered_occurrence_contexts']]
        assert names==[sample['actual_occurrence_one']['full_path_name'],sample['actual_occurrence_two']['full_path_name']]
        stored_member_names=[paths[i]['path'] for i in row['stored_occurrence_member_object_ids']]
        assert stored_member_names==list(reversed(names))
        for previous,immediate,after in zip(sample['occurrences_before'],sample['occurrences_immediately_after_add'],sample['occurrences_after']):
            assert previous['name']==immediate['name']==after['name']
            assert same(previous['transform'],immediate['transform']) and same(previous['transform'],after['transform'])
            native,=[o for o in occurrences.values() if o['component_object_id'] in {c['object_id'] for c in stream['assembly_decoding']['components'] if c['name']==after['component_name']}]
            assert same(native['local_transform'],after['transform'])
        for item in row['motion_limits']:
            actual=api['limits'][item['limit_kind']]
            for field in ('minimum','maximum','rest'):
                assert math.isclose(item[field+'_value'],actual[field+'Value'],abs_tol=1e-12)
                assert item[field+'_enabled']==actual['is'+field.title()+'ValueEnabled']
            current='rotationValue' if item['limit_kind']=='rotationLimits' else 'slideValue'
            assert math.isclose(item['current_value'],api['current_values'][current],abs_tol=1e-12)
        expected_binding_roles=sorted(p['role'] for p in row['enabled_limit_bindings'])
        assert expected_binding_roles=={'rigid':[],'revolute':['RotateMaximum','RotateMinimum'],'slider':['SlideMinimum']}[sample['case']]
        geometry=row['source_geometry']
        if sample['case']=='rigid':
            assert geometry is None and sample['requested_joint_geometry']==sample['actual_joint_geometry']==dict(status='returned_null')
        else:
            actual=sample['actual_joint_geometry'];source=sample['requested_geometry_source']
            assert actual['status']=='returned_geometry' and actual['geometry_type']==0
            assert source['component_name']==actual['entity_one']['component_name']=='AsBuiltMoving'
            assert actual['entity_one']['assembly_context_path']==sample['actual_occurrence_one']['full_path_name']
            assert geometry['native_origin_point']['name']==actual['entity_one']['name']=='O'
            assert same(geometry['cached_origin_from_source_point'],actual['origin_cm'])
            assert same(geometry['cached_origin_from_source_point'],actual['entity_one']['point_cm'])
            assert same(geometry['stored_geometry_transform'],sample['actual_joint_transform'])
            assert not same(geometry['uninterpreted_point_provider_vector'],actual['origin_cm'])
            vector_key='rotationAxisVector' if sample['case']=='revolute' else 'slideDirectionVector'
            code=next(iter(row['direction_codes'].values()))
            assert same(api['vectors'][vector_key],[float(i==code) for i in range(3)])
        report['samples'].append(dict(file=str(p.relative_to(root)),archive_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            expected_decoded=result,actual_motion=api,actual_requested_limits=sample['requested_motion_limits'],
            actual_requested_geometry_source=sample['requested_geometry_source'],actual_joint_geometry=sample['actual_joint_geometry'],
            actual_joint_transform=sample['actual_joint_transform'],actual_health_state=sample['health_state'],actual_warning=sample['warning'],
            native_ordered_context_names=names,raw_native_member_names=stored_member_names,
            actual_occurrences_before=sample['occurrences_before'],actual_occurrences_after=sample['occurrences_after'],
            captured_before_immediate_after_final_placements_unchanged=True,native_placements_match_actual_snapshots=True,
            native_motion_limits_match_actual_getters=True,enabled_limit_roles=expected_binding_roles,
            point_geometry_API_corroborated=geometry is not None,decoder_does_not_mutate_input=True))
        fixtures.append((sample['case'],data,records,stream,row))
    case,data,records,stream,row=next(f for f in fixtures if f[0]=='revolute')
    primary={r.object_id:r for r in records if r.is_primary}
    first_context=row['ordered_occurrence_contexts'][0]
    mods=(
        ('Native joint collection member count unsupported',row['collection_object_id'],12,struct.pack('<I',2)),
        ('Common joint members alias',row['object_id'],6,struct.pack('<Q',row['stored_occurrence_member_object_ids'][1])),
        ('Owned ordered context frame backlink differs',first_context['object_id'],50,struct.pack('<Q',999999)),
        ('Occurrence UUID loses explicit same-asset match',first_context['route_object_id'],10,b'f\0'),
        ('Marker1 opaque prefix is unobserved',row['object_id'],126,b'\1'),
        ('Point geometry backend owner is wrong',row['source_geometry']['backend_object_id'],322,struct.pack('<Q',999999)),
        ('Typed native point becomes unknown leaf identity',row['source_geometry']['terminal_object_id'],2,struct.pack('<Q',999999)),
        ('Enabled limit binding disagrees with native parameter cache',row['enabled_limit_binding_object_ids'][0],21,struct.pack('<d',.75)),
        ('Shared native motion entry self-owner is wrong',row['object_id'],49,struct.pack('<Q',999999)))
    for label,identity,offset,payload in mods:
        changed=bytearray(data);position=primary[identity].body+offset;changed[position:position+len(payload)]=payload
        value=decode_asbuilt_joints(bytes(changed),records,stream['assembly_decoding'],stream['features'])
        assert not value['decoded'] and len(value['unresolved'])==1,label
        report['malformed_guards'].append(dict(control=label,rejected=True,reason=value['unresolved'][0]['reason']))
    old=json.loads((root/'joint-decoding.json').read_text())
    assert len(old['samples'])==8
    for sample in old['samples']:
        p=root/sample['archive'];stream=decode_basics(p,zstd_library)['streams'][0]
        m=read_members(p,zstd_library);d=m[stream['member']]
        rs,_=design_records(d,m[stream['member'].replace('BulkStream.dat','MetaStream.dat')])
        ordinary=decode_joints(d,rs,stream['assembly_decoding'],stream['features'])
        assert ordinary==sample['decoding'],sample['archive']
        absent=decode_asbuilt_joints(d,rs,stream['assembly_decoding'],stream['features'])
        assert not absent['decoded'] and not absent['unresolved']
        report['ordinary_joint_goldens'].append(dict(file=sample['archive'],shared_refactor_output_exact_prior_golden=True,
            new_AsBuilt_helper_does_not_recover_or_reject=True))
    report['validation']=dict(actual_AsBuilt_files=3,decoded_AsBuilt_features=3,decoded_common_native_joints=3,
        ordinary_joint_golden_controls=8,malformed_guards=len(mods),nonrigid_point_geometry_API_comparisons=2,
        actual_source_placement_snapshots=6,actual_all_getter_errors=0,actual_all_setter_errors=0,all_owned_closeFalse_returns=True,
        shared_motion_parser_reused=True,solved_world_placement_claim=False,live_Fusion_calls_by_validator=0,all_checks_passed=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--zstd-library')
    parser.add_argument('--output',type=Path,default=ROOT/'asbuilt-joint-decoding.json')
    args=parser.parse_args();result=validate(args.root,args.zstd_library)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['validation'],sort_keys=True))
