"""Focused actual API/full-frame contrasts and strict custom-support guards."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_datum_mirror_supports import decode_datum_mirror_supports
from decode_mirror_datum_reflections import decode_mirror_datum_reflections
from decode_parameters import read_string
from decode_sketch import attributes, same
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
CAPTURE='datummirrorsupport-3a854f334428'
OLD_FILES=('mirrorassemblydatum-65c867cc41d9/plane_xy_positive_offset.f3d',
           'mirrorassemblydatum-65c867cc41d9/plane_xz_negative_offset.f3d',
           'remainingbodyinputs-7b3357274e85/mirror_construction_plane.f3d')


def validate(root=ROOT,zstd_library=None):
    root=Path(root)
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text())
    assert truth['terminal_status']=='complete' and truth['exported_sample_count']==2 and not truth['errors']
    report=dict(scope='Two actual custom-support datum Mirrors; typed reciprocal provenance and full-frame Householder/cache/API corroboration, not general feature regeneration',
        interface='decode_datum_mirror_supports(data, records, features, assembly) -> decoded/unresolved/scope',
        provenance=dict(capture_directory=CAPTURE,
            ground_truth_sha256=hashlib.sha256((root/CAPTURE/'ground_truth.json').read_bytes()).hexdigest(),
            journal_sha256=hashlib.sha256((root/CAPTURE/'journal.jsonl').read_bytes()).hexdigest(),
            source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
                'GenerateDatumMirrorSupportContrasts.py','decode_datum_mirror_supports.py','validate_datum_mirror_supports.py',
                'decode_mirror_datum_outputs.py','decode_mirror_datum_reflections.py','decode_plane_definitions.py',
                'decode_dependencies.py','decode_selection.py')}),
        samples=[],malformed_guards=[],prior_origin_controls=[],prior_body_control={},
        integration='Publish separate datum_mirror_supports summary and attach successful feature evidence. Preserve old origin-only helper and its scope; unavailable datum controls and output API getter diagnostics remain explicit.',
        limitations=['Only actual Offset source and Offset/Angle selected supports with exact three-member repeated collection are admitted.',
            'The selected support origin is the actual stored/API origin, including the tilted support in-plane displacement; it is not replaced with a guessed zero.',
            'Collection/member and feature identities come from native typed references. API entity-token set differences independently isolate the newly appearing plane for geometry validation only.',
            'The reflection is an orientation-reversing computed transform, not a stored matrix, proper rigid occurrence placement, general construction-plane regeneration or feature history replay.',
            'resultFeatures and mirrorPlane actually returnNone; output timeline/definition getter failures are retained rather than invented.',
            'Combine/stitch settings, arbitrary supports, cross-component datum contexts, native writing and general lifecycle remain unresolved.'])
    fixtures=[]
    for sample in truth['samples']:
        p=root/CAPTURE/sample['file']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==sample['export']['sha256']
        assert sample['close_owned_document_returned'] is True
        assert sample['compute_before'] is sample['compute_after'] is True
        assert sample['source_setter']['returned'] is sample['support_setter']['returned'] is True
        assert [e['field'] for e in sample['getter_errors']]==['after_planes[2].timelineObject','after_planes[2].definition.objectType']
        assert sample['mirror_plane_getter_status']=='returned_null' and sample['actual_mirror_plane'] is None
        assert sample['api_result_features']==dict(status='returned_null',entities=[])
        stream=decode_basics(p,zstd_library)['streams'][0]
        members=read_members(p,zstd_library);data=members[stream['member']]
        records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')])
        before=deepcopy(stream)
        result=decode_datum_mirror_supports(data,records,stream['features'],stream['assembly_decoding'])
        assert stream==before and len(result['decoded'])==1 and not result['unresolved']
        row=result['decoded'][0];native=row['source_output_provenance']
        source=native['source_plane'];output=native['output_plane'];support=row['selected_support_definition']['cached_geometry']
        assert row['native_component_evidence']['stored_plane_object_ids']==[row['source_plane_object_id'],row['support_plane_object_id'],row['output_plane_object_id']]
        assert len(row['native_component_evidence']['dependency_scopes'])==3
        assert all(s['component_object_id']==row['component_object_id'] for s in row['native_component_evidence']['dependency_scopes'])
        assert row['is_combine'] is row['stitch_tolerance_cm'] is None
        actual_source=sample['requested_source'];actual_support=sample['requested_mirror_plane']
        assert len(sample['actual_inputs'])==1 and sample['actual_inputs'][0]['entity_token']==actual_source['entity_token']
        assert sample['construction_plane_count_before']==len(sample['construction_planes_before'])==2
        assert sample['construction_plane_count_after']==len(sample['construction_planes_after'])==3
        before_tokens={p['entity_token'] for p in sample['construction_planes_before']}
        after_tokens={p['entity_token'] for p in sample['construction_planes_after']}
        assert len(before_tokens)==2 and len(after_tokens)==3 and before_tokens<after_tokens
        actual_output,=[p for p in sample['construction_planes_after'] if p['entity_token'] not in before_tokens]
        for native_plane,api_plane,frame in (
            (source,actual_source,source['cached_plane_to_component_matrix']),
            (support,actual_support,support['plane_to_component_matrix']),
            (output,actual_output,output['cached_plane_to_component_matrix'])):
            assert same(native_plane['origin_cm'],api_plane['origin_cm'])
            assert same(native_plane['normal'],api_plane['normal']) and same(frame,api_plane['transform'])
        for handle,original in ((sample['source_handle_after'],actual_source),(sample['support_handle_after'],actual_support)):
            assert handle['entity_token']==original['entity_token']
            assert same(handle['transform'],original['transform'])
        matrix=row['computed_reflection_matrix']
        square=[sum(matrix[4*r+k]*matrix[4*k+c] for k in range(4)) for r in range(4) for c in range(4)]
        assert same(square,[float(r==c) for r in range(4) for c in range(4)])
        assert same(row['computed_output_plane_frame'],actual_output['transform'])
        wrong_origin_control=None
        if sample['case']=='offset_selected_support':
            assert support['origin_cm']==[0.,0.,1.] and output['origin_cm']==[0.,0.,-1.]
            # A support through the origin would produce z=-3 instead of z=-1.
            wrong_origin_control=dict(output_origin_if_support_incorrectly_at_origin=[0.,0.,-3.],
                actual_output_origin_cm=output['origin_cm'],rejected_by_frame_correspondence=True)
        else:
            assert same(support['origin_cm'],[0.,1.2125,0.])
            assert row['selected_support_definition']['definition_kind']=='Angle'
            assert same(support['normal'],[.5,0.,3**.5/2])
        old=decode_mirror_datum_reflections(data,records,stream['features'],stream['assembly_decoding'])
        assert not old['decoded'] and len(old['unresolved'])==1
        assert old['unresolved'][0]['reason']=='Unobserved datum Mirror two-plane collection framing'
        report['samples'].append(dict(file=str(p.relative_to(root)),archive_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            expected_decoded=result,actual_source=actual_source,actual_support=actual_support,
            independent_actual_output=actual_output,actual_getter_errors=sample['getter_errors'],
            actual_result_features=sample['api_result_features'],actual_mirror_plane_status=sample['mirror_plane_getter_status'],
            source_support_handles_unchanged=True,API_collection_new_token_identified_independently=True,
            full_source_support_output_API_frames_match=True,reflection_involution=True,
            old_origin_helper_rejection_preserved=old['unresolved'],wrong_origin_negative_control=wrong_origin_control,
            maximum_API_output_frame_difference=max(abs(a-b) for a,b in zip(row['computed_output_plane_frame'],actual_output['transform']))))
        fixtures.append((data,records,stream,row))
    data,records,stream,row=fixtures[0]
    primary={r.object_id:r for r in records if r.is_primary}
    support=primary[row['support_plane_object_id']];sb=data[support.body:support.end]
    _,cursor=attributes(sb,2);_,tag_end=read_string(sb,cursor+109)
    output=primary[row['output_plane_object_id']];_,output_cursor=attributes(data[output.body:output.end],2)
    collection_id=row['native_component_evidence']['plane_collection_object_id']
    collection=primary[collection_id]
    mods=(
        ('Collection count is not observed3',collection_id,2,struct.pack('<I',2)),
        ('Repeated output membership differs',collection_id,96,struct.pack('<Q',999999)),
        ('Selected support cache collection disagrees',support.object_id,tag_end+1,struct.pack('<Q',999999)),
        ('Selected support owner differs from WorkPlane',support.object_id,tag_end+21,struct.pack('<Q',999999)),
        ('Mirror selector aliases source instead of independent support',row['source_output_provenance']['mirror_plane']['terminal_object_id'],2,struct.pack('<Q',row['source_plane_object_id'])),
        ('Output cache fails full-frame reflection',output.object_id,output_cursor+21,struct.pack('<d',.25)),
        ('Native dependency scope component changes',row['native_component_evidence']['dependency_scopes'][0]['scope_object_id'],4,struct.pack('<Q',999999)))
    for label,identity,offset,payload in mods:
        changed=bytearray(data);position=primary[identity].body+offset;changed[position:position+len(payload)]=payload
        value=decode_datum_mirror_supports(bytes(changed),records,stream['features'],stream['assembly_decoding'])
        assert not value['decoded'] and len(value['unresolved'])==1,label
        report['malformed_guards'].append(dict(control=label,rejected=True,reason=value['unresolved'][0]['reason']))
    old_report=json.loads((root/'mirror-datum-reflection-decoding.json').read_text())
    for filename in OLD_FILES:
        s=decode_basics(root/filename,zstd_library)['streams'][0];members=read_members(root/filename,zstd_library);d=members[s['member']]
        rs,_=design_records(d,members[s['member'].replace('BulkStream.dat','MetaStream.dat')])
        value=decode_datum_mirror_supports(d,rs,s['features'],s['assembly_decoding'])
        original=decode_mirror_datum_reflections(d,rs,s['features'],s['assembly_decoding'])
        golden=next(r['expected_summary'] for r in old_report['samples'] if r['file']==filename)
        assert not value['decoded'] and not value['unresolved'] and original==golden
        report['prior_origin_controls'].append(dict(file=filename,new_helper_does_not_recover_or_reject=True,
            original_origin_reflection_output_byte_equivalent_JSON=True))
    filename='bodyselections-62e42366c722/mirror_two_bodies_plane.f3d'
    s=decode_basics(root/filename,zstd_library)['streams'][0];m=read_members(root/filename,zstd_library);d=m[s['member']]
    rs,_=design_records(d,m[s['member'].replace('BulkStream.dat','MetaStream.dat')])
    value=decode_datum_mirror_supports(d,rs,s['features'],s['assembly_decoding'])
    assert not value['decoded'] and not value['unresolved']
    f=next(f for f in s['features'] if f['kind']=='Mirror')
    assert f['tool_settings']['plane']['entity']['origin_cm']==[.5,0.,0.]
    report['prior_body_control']=dict(file=filename,new_helper_does_not_recover_or_reject=True,
        existing_non_origin_body_plane_selection_preserved=True)
    report['validation']=dict(actual_new_files=2,source_support_output_API_frame_comparisons=6,
        independent_new_output_token_differences=2,computed_reflection_involutions=2,malformed_guards=len(mods),
        prior_origin_controls=3,prior_non_origin_body_control=1,new_helper_mutates_input=False,
        maximum_frame_difference=max(x['maximum_API_output_frame_difference'] for x in report['samples']),live_Fusion_calls_by_validator=0,
        all_checks_passed=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--zstd-library')
    parser.add_argument('--output',type=Path,default=ROOT/'datum-mirror-support-decoding.json')
    args=parser.parse_args();result=validate(args.root,args.zstd_library)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['validation'],sort_keys=True))
