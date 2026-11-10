"""Five actual non-seed suppressions plus explicit even seed counterexample."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_circular_patterns import decode_circular_pattern
from decode_circular_symmetric_suppression import decode_circular_symmetric_suppression,inspect_circular_suppression
from decode_selection import known_construction_entities
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
DIRECTORIES=('circularsymsuppression-bef7ede4d911','circularsymsuppression-c837268fa458')


def validate(zstd):
    report={'scope':'Six actual exports: five verified non-seed symmetric circular suppression selections and one native-ordinal1 counterexample; bounded quantity4/5 native-Z/pi-angle single-body family only',
        'interface':'decode_circular_symmetric_suppression(data,records,features)->decoded/partial/unresolved/scope; full rows feature_object_id/tool_settings; partial rows have no tool_settings',
        'integration':'Attach full settings for five positive rows and clear only symmetric-suppression mapping diagnostic; keep old default tool failure/settings/placement warning for partial seed counterexample',
        'mapping':'API ID equals index of suppressed native ordinal in explicit ordered element-reference table; never ordinal-minus-one, geometry, nearest angle or body order',
        'captured_tables':{'quantity4':[4,2,1,3],'quantity5':[4,2,1,3,5]},'capture_provenance':[],
        'samples':[],'malformed_guards':[],'legacy_controls':[],
        'limitations':['Full runtime support is single suppression only: quantity5 non-seed ordinals2/3/4/5, quantity4 ordinal4. Other counts, tables, input modes, axes, angles or multi-ID combinations remain unsupported.',
            'Native ordinal1 maps to API index2 in both captured tables. Four-body case marks this ID suppressed but retains all four bodies and six member faces; no physical removal claimed.',
            'Getter failures on suppressed-member faces are retained, not interpreted as returned zero faces.',
            'API element transforms are literal evidence and remain subject to the existing circular getter/placement warnings. No rotation repair or geometry regeneration.',
            'This is suppression control-ID correspondence, not persistent topology, body lifecycle or assembly solving.']}
    contexts={};positive=partial=errors=elements=0
    for directory in DIRECTORIES:
        path=ROOT/directory;truth=json.loads((path/'ground_truth.json').read_text())
        assert truth['status']=='complete' and not truth['errors'] and len(truth['samples'])==3
        assert hashlib.sha256((path/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256']
        report['capture_provenance'].append({'ground_truth_file':directory+'/ground_truth.json','ground_truth_sha256':hashlib.sha256((path/'ground_truth.json').read_bytes()).hexdigest(),
            'executed_generator_sha256':truth['executed_generator_sha256'],'executed_source_snapshot':directory+'/executed-generator-source.txt'})
        for sample in truth['samples']:
            assert sample['status']=='exported' and sample['close_owned_document_result'] is True
            relative=directory+'/'+sample['file'];members=read_members(ROOT/relative,zstd);stream=decode_basics(ROOT/relative,zstd)['streams'][0];name=stream['member'];data=members[name]
            records,_=design_records(data,members[name.replace('BulkStream.dat','MetaStream.dat')]);features=stream['features'];before=copy.deepcopy(features)
            summary=decode_circular_symmetric_suppression(data,records,features);assert not summary['unresolved'] and before==features
            feature,=[f for f in features if f['kind']=='CircularPattern'];info=inspect_circular_suppression(data,records,feature)
            api=sample['settings'];requested=sample['requested']['suppressed_ids']
            assert api['is_symmetric'] is True and api['quantity']==info['quantity'] and api['health_state']==0 and not api['warning']
            assert api['suppressed_element_ids']==sample['setter_readback_under_rollback']==requested
            actual_before=sample['before_suppression']['elements'];actual_after=sample['after_suppression_elements']
            assert [e['id'] for e in actual_before]==[e['id'] for e in actual_after]==list(range(info['quantity']))
            assert all(e['is_suppressed'] is False for e in actual_before)
            assert [e['id'] for e in actual_after if e['is_suppressed']]==requested
            assert [info['stored_element_ordinals'].index(i) for i in info['stored_suppressed_element_ordinals']]==requested
            elements+=len(actual_after)
            getter_errors=sample['getter_errors'];errors+=len(getter_errors)
            for error in getter_errors:assert error['field']=='after.element.faces' and 'InternalValidationError : return_size > 0' in error['error']
            # Reconstruct the counted tail and complete ordered element records;
            # leading controller controls are retained literally, not rewritten.
            payload=bytes.fromhex(info['controller_payload_hex']);offset=info['suppression_list_offset']
            replay=payload[:offset]+struct.pack('<I',len(info['stored_suppressed_element_ordinals']))+b''.join(struct.pack('<I',i) for i in info['stored_suppressed_element_ordinals'])
            assert replay==payload
            ref=lambda i:b'\1'+struct.pack('<Q',i)+bytes(2)
            for identity,ordinal in zip(info['element_record_object_ids'],info['stored_element_ordinals']):
                r,=[r for r in records if r.is_primary and r.object_id==identity]
                assert data[r.body:r.end]==bytes(2)+struct.pack('<I',ordinal)+ref(info['control_object_id'])
            record,=[r for r in records if r.is_primary and r.object_id==feature['object_id']]
            try:decode_circular_pattern(data,records,data[record.body:record.end],feature,known_construction_entities(data,records,features),features)
            except ValueError as error:default_error=str(error)
            else:raise AssertionError('Old default unexpectedly accepts symmetric suppression')
            if info['stored_suppressed_element_ordinals']==[1]:
                row,=summary['partial'];assert not summary['decoded'] and 'tool_settings' not in row
                assert row['mapped_api_suppressed_element_ids']==[2] and row['generated_result_reference_count']==3
                assert api['root_body_count']==4 and len(sample['root_bodies_after'])==4 and not getter_errors
                suppressed,=[e for e in actual_after if e['is_suppressed']];assert suppressed['generated_face_count']==6
                assert default_error=='Invalid or duplicate circular pattern suppression identifiers';partial+=1
                result_count=3
            else:
                row,=summary['decoded'];assert not summary['partial'];settings=row['tool_settings']
                assert settings['suppressed_element_ids']==requested and settings['stored_element_ordinals']==info['stored_element_ordinals']
                assert settings['stored_suppressed_element_ordinals']==info['stored_suppressed_element_ordinals']
                assert settings['quantity']==api['quantity'] and settings['pattern_entity_type_code']==api['pattern_entity_type']
                assert settings['total_angle_radians']==api['total_angle_radians'] and settings['pattern_compute_option_code']==api['pattern_compute_option']
                assert settings['generated_result_reference_count']==info['quantity']-2
                assert api['root_body_count']==len(sample['root_bodies_after'])==info['quantity']-1
                assert len(getter_errors)==1 and default_error=='Symmetric circular suppression/API identifier mapping has not been observed'
                positive+=1;result_count=settings['generated_result_reference_count']
            report['samples'].append({'file':relative,'expected_summary':summary,'expected_settings':row.get('tool_settings'),
                'actual_suppressed_element_ids':requested,'actual_native_suppressed_ordinals':info['stored_suppressed_element_ordinals'],
                'actual_API_element_flags':[{k:e[k] for k in ('id','is_suppressed','generated_face_count')} for e in actual_after],
                'actual_root_body_count':api['root_body_count'],'native_generated_result_reference_count':result_count,
                'actual_getter_errors':getter_errors,'old_default_error_retained_for_comparison':default_error,
                'controller_suppression_tail_exact_replay':True,'typed_element_records_exact_replay':True,'owned_document_close_result':True})
            contexts[sample['case']]=(data,records,features,feature,info)
    data,records,features,feature,info=contexts['quantity5_suppress_id1'];control,=[r for r in records if r.is_primary and r.object_id==info['control_object_id']];offset=control.body
    def reject(label,bad):
        result=decode_circular_symmetric_suppression(bytes(bad),records,features)
        assert not result['decoded'] and not result['partial'] and len(result['unresolved'])==1
        report['malformed_guards'].append({'case':label,'reason':result['unresolved'][0]['reason']})
    bad=bytearray(data);bad[offset+2]=2;reject('Symmetry flag not boolean',bad)
    bad=bytearray(data);struct.pack_into('<I',bad,offset+50,9);reject('Ordinal table count exceeds exact element framing',bad)
    bad=bytearray(data);struct.pack_into('<I',bad,offset+info['suppression_list_offset'],2);reject('Suppression count exceeds exact tail extent',bad)
    bad=bytearray(data);struct.pack_into('<I',bad,offset+info['suppression_list_offset']+4,0);reject('Suppression ordinal absent from typed element table',bad)
    bad=bytearray(data);struct.pack_into('<I',bad,offset+41,1);reject('Feature-input mode not captured body context',bad)
    element,=[r for r in records if r.is_primary and r.object_id==info['element_record_object_ids'][0]]
    bad=bytearray(data);struct.pack_into('<Q',bad,element.body+7,control.object_id+1);reject('Element controller reference differs',bad)
    for filename in ('body_symmetric.f3d','body_suppressed.f3d','body_full.f3d'):
        relative='circularmodes-45f859c1f1b6/'+filename;members=read_members(ROOT/relative,zstd);stream=decode_basics(ROOT/relative,zstd)['streams'][0];data=members[stream['member']]
        records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')]);before=copy.deepcopy(stream['features'])
        result=decode_circular_symmetric_suppression(data,records,stream['features']);assert not result['decoded'] and not result['partial'] and not result['unresolved'] and stream['features']==before
        report['legacy_controls'].append({'file':relative,'no_new_summary_or_mutation':True})
    assert positive==5 and partial==1 and errors==5
    report['summary']={'actual_exports':6,'verified_nonseed_suppression_settings':positive,'seed_negative_partial_only':partial,
        'actual_element_flag_checks':elements,'typed_element_record_replays':elements,'suppression_tail_replays':6,'retained_actual_getter_errors':errors,
        'malformed_guards':len(report['malformed_guards']),'legacy_controls':3,'all_owned_documents_closed_true':True}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default=str(ROOT/'circular-symmetric-suppression-decoding.json'));args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(zstd);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
