"""Actual Thin Boolean controls, old dictionaries exact, bounded native guards."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_basics import named_features,attach_parameters,sketch_references
from decode_extrude import decode_extrude
from decode_parameters import decode_stream
from decode_sketch import decode_sketches
from decode_thin_extrudes import EXTRUDE,decode_thin_extrudes,inspect_thin_extrude
from decode_thin_extrude_operations import decode_thin_extrude_operations
from discover_features import discover_features
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
DIRECTORY='thinextrudeoperations-edb76642a509'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def context(filename,zstd):
    members=read_members(ROOT/filename,zstd)
    member,=[n for n in members if n.endswith('/FusionDesignSegmentType1/BulkStream.dat')]
    data=members[member]
    records,registry=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
    features=named_features(data,records)
    discover_features(data,records,features,registry)
    parameters,_=decode_stream(data,records)
    attach_parameters(data,records,features,parameters)
    sketch_references(data,records,features)
    decode_sketches(data,records,features)
    return data,records,features,member,members


def validate(zstd):
    folder=ROOT/DIRECTORY
    truth=json.loads((folder/'ground_truth.json').read_text())
    assert truth['terminal_status']=='complete' and not truth['errors'] and len(truth['samples'])==3
    assert (folder/'complete.txt').is_file() and json.loads((folder/'progress.json').read_text())['phase']=='batch_complete'
    assert digest(folder/'executed-generator-source.txt')==truth['executed_generator_sha256']
    assert digest(folder/truth['source_helper_snapshot'])==truth['source_helper_sha256']
    assert digest(folder/truth['sdk_surface_snapshot'])==truth['sdk_surface_snapshot_sha256']
    report=dict(scope='Three actual owned one-sided Side1 thin rectangle operations: Join/Cut/Intersect with typed historical target/new anchor/current collection evidence. Controls/profile/body metadata only; independent geometry corroboration is separate.',
        interface='decode_thin_extrude_operations(data,records,features)->decoded/unresolved/scope; rows reuse unchanged common_extrusion_controls/thin_metadata/profile and add body_list_evidence',
        shared_opt_ins='inspect_thin_extrude(...,allowed_operations=(NewBody,),body_list_resolver=None). Defaults remain unchanged; approved callback receives(data,records,body,feature,cursor) immediately after profile list.',
        integration=dict(merged_family='thin_extrudes',variant_scope_key='operation_variant_scope',
            cleared_old_reason='Only observed solid NewBody untapered distance Thin Extrude family supported',
            scope='Append only successful rows and remove only corresponding same-feature family rejection; ordinary extrusion controls/warnings and unrelated errors remain exact.'),
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(folder/'ground_truth.json'),
            executed_generator_sha256=truth['executed_generator_sha256'],source_helper_sha256=truth['source_helper_sha256'],
            sdk_runtime_source_sha256=truth['sdk_runtime_source_sha256'],sdk_surface_snapshot_sha256=truth['sdk_surface_snapshot_sha256']),
        native_schema=dict(Extrude_class_guid=EXTRUDE,common_controls='Existing decode_extrude/layout_observer; no common schema copied or ordinary fields changed',
            thin_block='Same bounded native bool/location/owned thickness parameter schema as prior Thin Extrude captures',
            following_frame='Single typed profile selection, reservedzero4, owned-new-anchor count0/1+refs, reservedzero4, target-body-proxy count1+ref',
            historical_target_scope='Owned body proxy references seed anchor/nativeBODY311; target is not relabelled a new feature-owned body',
            owned_new_anchor_scope='Cut alone owns one additional anchor→BODY1764. Join/Intersect own no new anchor although they have current geometry.',
            body_list_runtime_proof='Independent callback validates typed target/seed/new ownership, reciprocal current BODY collection, mapping membership and exact bounded bytes; late same-asset ASM ID qualification remains separate.'),
        samples=[],malformed_guards=[],legacy_controls=[],ordinary_control={},
        limitations=['Supported family is solid one-sided untapered positive distance, Side1 positive finite owned thickness, one closed four-Line profile. Other Boolean thin combinations remain unsupported.',
            'Wall side denotes extrusion extent side; no universal inward/outward wall direction or thin-wall geometry regeneration claimed.',
            'Native historical targetBODY311 remains separate from genuinely owned newBODY1764. Current collection facts are not generic lifetime, hidden/deleted state or persistent topology.',
            'Cut has two actual current/result BRep bodies but only one new owned anchor; result count is not inferred from new-anchor count.',
            'Join participantBodies SDK getter/setter not invoked because the property applies to Cut/Intersect. Typed target provenance is separate from actual participant getter semantics.',
            'Input DistanceExtentDefinition.distance returns None before add in these captures; configured request and rolled feature ModelParameter value are kept distinct.',
            'Shared common extrusion dictionaries and old Thin summaries remain exactly unchanged. New wrapper does not mutate feature dictionaries or clear warnings itself.',
            'No API entity token or temporary topology identifier becomes a native object ID. Source/member routes precede numerical corroboration; general traversal/topology/regeneration unresolved.'])
    contexts={};wall_checks=extent_checks=common_checks=0
    for actual in truth['samples']:
        filename=DIRECTORY+'/'+actual['file']
        assert actual['operation_status']=='FeatureReturned' and not actual['getter_errors'] and not actual['setter_errors']
        assert actual['close_owned_document_returned'] is True and actual['roll_before_feature_returned'] is True
        assert actual['export']['sha256']==digest(ROOT/filename) and actual['export']['size_bytes']==(ROOT/filename).stat().st_size
        assert actual['timeline_count']==actual['timeline_marker_position']
        data,records,features,member,members=context(filename,zstd)
        before=copy.deepcopy(features)
        old=decode_thin_extrudes(data,records,features)
        decoded=decode_thin_extrude_operations(data,records,features)
        assert features==before and not decoded['unresolved'] and len(decoded['decoded'])==1
        row,=decoded['decoded'];fid=row['feature_object_id'];metadata=row['thin_metadata'];evidence=row['body_list_evidence']
        feature,=[f for f in features if f['object_id']==fid];record,=[r for r in records if r.is_primary and r.object_id==fid]
        assert not old['decoded'] and old['unresolved']==[dict(feature_object_id=fid,reason='Only observed solid NewBody untapered distance Thin Extrude family supported')]
        expected_operation={'join':'Join','cut':'Cut','intersect':'Intersect'}[actual['case']]
        common=[]
        for f in features:
            if f.get('class_guid')!=EXTRUDE:continue
            r,=[r for r in records if r.is_primary and r.object_id==f['object_id']]
            payload=data[r.body:r.end];observed=[]
            default=decode_extrude(payload,f);callback=decode_extrude(payload,f,layout_observer=observed.append)
            assert default==callback and len(observed)==1
            common.append(dict(feature_object_id=f['object_id'],controls=default[0],unresolved=default[1]));common_checks+=1
        current,=[c for c in common if c['feature_object_id']==fid]
        assert current['controls']==row['common_extrusion_controls'] and current['unresolved']==[]
        assert current['controls']['operation']['kind']==expected_operation
        assert current['controls']['extent']['mode']=='OneSided' and current['controls']['start']==dict(stored_code=0,kind='ProfilePlane')
        assert 'result_anchor_object_id' not in row and 'native_body_object_id' not in row
        assert evidence['target_native_body_object_ids']==[311] and evidence['target_seed_owner_object_ids']==[279]
        assert evidence['native_current_body_object_ids']==([311,1764] if actual['case']=='cut' else [311])
        assert len(evidence['new_result_anchor_object_ids'])==(1 if actual['case']=='cut' else 0)
        assert evidence['new_result_native_body_object_ids']==([1764] if actual['case']=='cut' else [])
        assert bytes.fromhex(evidence['stored_body_list_hex'])==data[record.body+evidence['body_list_start_offset']:record.body+evidence['body_list_end_offset']]
        assert bytes.fromhex(metadata['block_hex'])==data[record.body+metadata['block_start_offset']:record.body+metadata['block_end_offset']]
        assert metadata['side_one']['wall_location']=='Side1' and metadata['side_one']['stored_wall_location_code']==0
        assert metadata['side_two']['applicable'] is False and metadata['side_two']['binding_object_id'] is None
        for key in ('actual_input_before_add','feature_before_node'):
            api=actual[key]
            assert api['operation']==current['controls']['operation']['stored_code']-1
            assert api['isThinExtrude'] is api['isSolid'] is True and api['hasTwoExtents'] is False
            assert not api['control_getter_errors'] and api['thinExtrudeWallLocationOne']==metadata['side_one']['stored_wall_location_code']
            numeric=api['thinExtrudeWallThicknessOne'];value=numeric['realValue'] if key=='actual_input_before_add' else numeric['value']
            assert value==metadata['side_one']['thickness_cm']==0.12
            if key=='feature_before_node':
                assert numeric['role']==metadata['side_one']['parameter_role']=='Side1WallThickness'
                assert numeric['name']==metadata['side_one']['parameter_name']
                assert numeric['createdBy']['name']==feature['name'] and numeric['expression']=='1.20 mm'
            assert api['side_two']['getter_called'] is api['side_two']['setter_called'] is False
            wall_checks+=1
        rolled=actual['feature_before_node']
        assert actual['actual_input_before_add']['extentOne']['distance'] is None
        assert rolled['extentOne']['distance']['value']==current['controls']['extent']['side_one']['distance_cm']==2.5
        assert rolled['extentOne']['distance']['role']=='AlongDistance' and rolled['extentOne']['distance']['createdBy']['name']==feature['name']
        assert rolled['taperAngleOne']['value']==current['controls']['extent']['side_one']['taper_angle_radians']==0.
        extent_checks+=1
        if actual['case']=='join':
            assert rolled['participantBodies'] is None and rolled['participant_applicability']['getter_called'] is False
            assert actual['participant_setter_status'].startswith('NotApplicable')
        else:
            assert actual['input_participant_handle_equality'] is actual['rolled_participant_handle_equality'] is True
            participant,=rolled['participantBodies']
            assert participant['name']==actual['source_target_before_thin']['name']
        assert row['profile']['kind']=='SketchProfile' and len(row['profile']['loops'])==1
        assert row['profile']['sketch_name']==rolled['profile']['parentSketch']['name']
        refs=row['profile']['loops'][0]['curve_references']
        assert len(refs)==len(rolled['profile']['loops'][0]['curves'])==4 and all(r['entity_kind']=='Line' for r in refs)
        assert actual['feature_at_timeline_end']['healthState']==0 and actual['feature_at_timeline_end']['errorOrWarningMessage']==''
        assert actual['component_bodies_after_thin']['count']==len(evidence['native_current_body_object_ids'])
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=decoded,
            expected_legacy_thin_summary=old,expected_common_extrusion_controls=common,
            actual_API_operation=rolled['operation'],actual_API_isThinExtrude=True,actual_API_wall_thickness_cm=0.12,
            actual_API_side_one_distance_cm=2.5,actual_API_current_BRep_count=actual['component_bodies_after_thin']['count'],
            actual_API_participant_getter_called=rolled['participant_applicability']['getter_called'],
            historical_target_native_body_ids=evidence['target_native_body_object_ids'],new_owned_native_body_ids=evidence['new_result_native_body_object_ids'],
            exact_thin_block_and_body_list_byte_replays=True,owned_document_closed_true=True))
        contexts[actual['case']]=(data,records,features,member,members,row)
    data,records,features,member,members,row=contexts['cut']
    fid=row['feature_object_id'];by_id={r.object_id:r for r in records if r.is_primary};record=by_id[fid];metadata=row['thin_metadata'];one=metadata['side_one']
    def reject(label,offset,payload,changed_features=None,extra_changes=()):
        damaged=bytearray(data);damaged[offset:offset+len(payload)]=payload
        for o,p in extra_changes:damaged[o:o+len(p)]=p
        answer=decode_thin_extrude_operations(bytes(damaged),records,features if changed_features is None else changed_features)
        assert not answer['decoded'] and len(answer['unresolved'])==1
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offset=offset,rejected=True,reason=answer['unresolved'][0]['reason']))
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    reject('native thin flag not boolean',record.body+metadata['stored_flag_offset'],b'\2')
    reject('Center location outside captured Boolean family',record.body+one['location_code_offset'],struct.pack('<I',1))
    along=next(p for f in features if f['object_id']==fid for p in f['parameters'] if p['role']=='AlongDistance')
    reject('thickness reference points at valid AlongDistance binding',record.body+one['binding_reference_offset'],ref(along['binding_object_id']))
    binding=by_id[one['binding_object_id']]
    reject('wall binding owner footer differs',binding.end-11,ref(279))
    reject('cached wall thickness differs from numeric parameter',binding.body+21,struct.pack('<d',0.13))
    changed=copy.deepcopy(features);feature,=[f for f in changed if f['object_id']==fid]
    parameter=next(p for p in feature['parameters'] if p['binding_object_id']==one['binding_object_id']);parameter['raw_float64']=0.
    reject('zero thickness rejected with all matching copies',binding.body+21,struct.pack('<d',0.),changed,[(parameter['value_offset'],struct.pack('<d',0.))])
    profile_proxy=by_id[row['profile_proxy_object_id']]
    reject('profile proxy owner differs',profile_proxy.end-11,ref(279))
    body_proxy=by_id[row['body_list_evidence']['target_body_selection_object_ids'][0]]
    reject('target body proxy owner differs',body_proxy.end-11,ref(279))
    prior=json.loads((ROOT/'thin-extrude-decoding.json').read_text())
    for saved in prior['samples']:
        d,rs,fs,n,m=context(saved['file'],zstd)
        old=decode_thin_extrudes(d,rs,fs)
        assert old==saved['expected_summary']
        empty=decode_thin_extrude_operations(d,rs,fs)
        assert empty['decoded']==empty['unresolved']==[]
        report['legacy_controls'].append(dict(archive=saved['file'],full_prior_thin_summary_exact=True,new_wrapper_no_candidate=True))
    ordinary=prior['ordinary_control'];d,rs,fs,n,m=context(ordinary['file'],zstd)
    feature,=[f for f in fs if f.get('class_guid')==EXTRUDE];r,=[r for r in rs if r.is_primary and r.object_id==feature['object_id']]
    inspection=inspect_thin_extrude(d,rs,d[r.body:r.end],feature,features=fs)
    assert inspection==ordinary['expected_inspection']
    assert not decode_thin_extrudes(d,rs,fs)['decoded'] and not decode_thin_extrude_operations(d,rs,fs)['decoded']
    report['ordinary_control']=dict(archive=ordinary['file'],full_prior_False_inspection_exact=True,no_new_runtime_sidecar=True)
    report['summary']=dict(actual_archives=3,decoded_thin_Boolean_features=3,actual_owned_wall_getter_checks=wall_checks,
        actual_owned_extent_getter_checks=extent_checks,exact_common_callback_default_controls=common_checks,
        bounded_thin_and_body_list_byte_replays=3,malformed_guards=len(report['malformed_guards']),
        exact_prior_Thin_full_summaries=len(report['legacy_controls']),exact_ordinary_False_control=1,
        ordinary_common_parser_edits=0,main_runs=0,live_calls=0)
    report['runtime_source_sha256']={f:digest(ROOT/f) for f in ('decode_thin_extrudes.py','decode_thin_extrude_operations.py','validate_thin_extrude_operations.py',
        'decode_thin_extrude_body_routes.py','decode_extrude.py','decode_parameters.py')}
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default=str(ROOT/'thin-extrude-operation-decoding.json'))
    args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd)
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':main()
