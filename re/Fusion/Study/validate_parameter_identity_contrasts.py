"""Offline same-document full-index contrast and reciprocal scope-clock evidence.

Uses the existing strict parameter inspector; creates no expression AST or
native dependency graph from expression text. No live Fusion calls.
"""
import argparse
from copy import deepcopy
from dataclasses import replace
from datetime import datetime
import hashlib
import json
from pathlib import Path
import struct
from uuid import UUID

from decode_assembly import COMPONENT_GUID, decode_assembly
from decode_dependencies import decode_dependencies
from decode_parameters import read_string
from decode_scope_update_times import decode_scope_update_times, SUPPORT_GUID
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_parameter_expression_records import _inspect_expression_records, _encode_expression_record

ROOT = Path(__file__).resolve().parent
CAPTURE = 'parameteridentity-8fc83529b236'


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def validate(root=ROOT, zstd_library=None):
    root = Path(root)
    capture = root / CAPTURE
    truth = json.loads((capture / 'ground_truth.json').read_text())
    journal = [json.loads(line) for line in (capture / 'journal.jsonl').read_text().splitlines() if line.strip()]
    assert truth['terminal_status'] == 'complete' and not truth['errors'] and truth['exported_sample_count'] == 4
    report = dict(status='Same-document expression field isolated; reciprocal scope u64 receives conditional time rendering only',
        scope='Four completed same-document saved exports; every metadata-indexed native payload compared, existing strict user-parameter field partitions replayed, independent API dependency getters retained',
        integration=dict(helper='decode_scope_update_times(data, records, assembly)',
            output='decoded/unresolved/scope; optional independent summary after assembly decoding',
            expression_dependency_integration='None; no native operand records or dependency edges identified by this stage'),
        native_expression_operand_records=None, native_expression_dependency_edges=None,
        provenance=dict(capture_directory=CAPTURE, ground_truth_sha256=_digest((capture/'ground_truth.json').read_bytes()),
            journal_sha256=_digest((capture/'journal.jsonl').read_bytes()),
            generator_sha256=_digest((root/'GenerateParameterIdentityContrasts.py').read_bytes()),
            source_sha256={name:_digest((root/name).read_bytes()) for name in (
                'validate_parameter_identity_contrasts.py','decode_scope_update_times.py',
                'validate_parameter_expression_records.py','decode_parameters.py','decode_parameter_tables.py',
                'decode_assembly.py','decode_dependencies.py','fusion_metadata.py','fusion_archive.py')}),
        samples=[], full_index_contrast={}, malformed_guards=[], synthetic_value_controls=[], prior_saved_controls=[],
        limitations=[
            'A stored counted expression string is not a typed reference or a native operand graph. API dependency getters are independent observations, not decoded native edges.',
            'Only the complete220 indexed records in each native Design segment of this controlled same-document experiment are compared; other archive members are outside this full-index comparison, and no claim that native dependency representation is universally absent.',
            'Timestamp epoch/unit interpretation is inferred from four tight journal intervals, not a native epoch/unit tag. Assignment, compute, update, save and other lifecycle events remain unqualified.',
            'Bookkeeping UUID changes do not establish parameter identity changes. API entity tokens remain opaque and are used only for equality across these same-document getter captures.',
            'The inherited component12-byte span181:193 remains byte-identical here; an independent component-color experiment belongs to a separate decoder/report.',
            'Zero and out-of-datetime-range u64 controls are synthetic malformed/value-bound tests, not evidence that such values occur in these four captures.'])
    snapshots=[]; baseline_tokens=None
    for sample in truth['samples']:
        path=capture/sample['file'];raw=path.read_bytes()
        assert _digest(raw)==sample['export']['sha256'] and sample['export']['returned_success']
        assert not sample['getter_errors'] and all(sample['observed_controls'].values())
        assert sample['timeline_count']==sample['marker_position']==0 and sample['user_parameter_count']==3
        members=read_members(path,zstd_library)
        member=next(n for n in members if n.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
        data=members[member];records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        payloads={(r.object_id,r.class_guid,r.is_primary):data[r.body:r.end] for r in records}
        assert len(payloads)==len(records)==220
        primary={r.object_id:r for r in records if r.is_primary}
        assembly=decode_assembly(data,records,[])
        dependency_before=decode_dependencies(data,records,[],assembly)
        clocks=decode_scope_update_times(data,records,assembly)
        assert len(clocks['decoded'])==1 and not clocks['unresolved']
        assert decode_dependencies(data,records,[],assembly)==dependency_before
        clock=clocks['decoded'][0]
        assert (clock['object_id'],clock['component_object_id'],clock['support_object_id'])==(33,3,34)
        support=payloads[(34,SUPPORT_GUID,True)]
        replay=bytes(12)+b'\1'+struct.pack('<Q',33)+bytes(2)+struct.pack('<Q',clock['stored_u64'])+bytes(8)
        assert replay==support
        observed={item['phase']:item for item in journal if item.get('case')==sample['case']}
        assigned=datetime.fromisoformat(observed['expression_assigned']['time_utc'])
        computed=datetime.fromisoformat(observed['computed']['time_utc'])
        converted=datetime.fromisoformat(clock['derived_UTC_if_epoch_microseconds'])
        assert assigned < converted < computed
        params=_inspect_expression_records(data,records)
        assert not params['unresolved'] and len(params['decoded'])==3
        byname={item['parameter_name']:item for item in params['decoded']}
        api={item['name']:item for item in sample['parameters']}
        tokens={name:item['entity_token'] for name,item in api.items()}
        if baseline_tokens is None:baseline_tokens=tokens
        assert tokens==baseline_tokens
        assert api['result']['dependency_names']==sample['expected_result_dependency_names']
        for name,item in byname.items():
            assert api[name]['is_valid'] and not api[name]['getter_errors']
            assert item['stored_expression']==api[name]['expression']
            assert item['stored_numeric_cache']==api[name]['value_cm']==1.0
            assert item['display_units']==api[name]['unit']=='mm'
            assert _encode_expression_record(item)==payloads[(item['parameter_object_id'],item['class_guid'],True)]
        assert [(byname[n]['parameter_object_id'],n) for n in ('alpha','bravo','result')]==[(202,'alpha'),(203,'bravo'),(204,'result')]
        for name in ('alpha','bravo'):
            assert api[name]['dependent_names']==(['result'] if name in sample['expected_result_dependency_names'] else [])
        assert all(g['edge_count']==0 for g in dependency_before['graphs'])
        relative=str(path.relative_to(root))
        report['samples'].append(dict(file=relative,archive_sha256=_digest(raw),source_Design_member=member,
            indexed_record_count=len(records),source_Design_sha256=_digest(data),
            actual_API_parameters=[dict(name=api[n]['name'],expression=api[n]['expression'],value_cm=api[n]['value_cm'],
                dependency_names=api[n]['dependency_names'],dependent_names=api[n]['dependent_names'],
                entity_token_sha256=_digest(api[n]['entity_token'].encode())) for n in ('alpha','bravo','result')],
            actual_controls=sample['observed_controls'],
            native_parameters=params['decoded'],native_dependency_tables=dependency_before['graphs'],
            expected_scope_update_times=clocks,
            clock_journal_comparison=dict(expression_assigned=assigned.isoformat(timespec='microseconds'),
                conditional_UTC=converted.isoformat(timespec='microseconds'),computed=computed.isoformat(timespec='microseconds'),
                strictly_inside_interval=True,after_assignment_microseconds=int((converted-assigned).total_seconds()*1000000),
                before_computed_microseconds=int((computed-converted).total_seconds()*1000000)),
            complete_support_payload_replay=True,unchanged_dependency_reader_output=True))
        snapshots.append(dict(file=relative,data=data,records=records,payloads=payloads,params=byname,assembly=assembly,clocks=clocks))
    keys=set(snapshots[0]['payloads'])
    assert all(set(s['payloads'])==keys for s in snapshots)
    varying=sorted(k for k in keys if len({s['payloads'][k] for s in snapshots})>1)
    assert [(k[0],k[2]) for k in varying]==[(1,True),(3,False),(34,True),(200,True),(201,True),(204,True)]
    fields={1:('asset_member_string',117),3:('component_UUID_string',517),
            200:('configuration_member_string',43),201:('rule_member_string',42)}
    varied=[]
    for key in varying:
        rows=[];normalized=[]
        for s in snapshots:
            body=s['payloads'][key]
            if key[0] in fields:
                field,start=fields[key[0]];value,end=read_string(body,start)
                if key[0]==3:UUID(value)
                else:UUID(value.split('.')[1])
                value_fields=[dict(field=field,relative_start=start,relative_end=end,stored_value=value)]
            elif key[0]==34:
                start,end=23,31
                value_fields=[dict(field='stored_scope_support_u64',relative_start=start,relative_end=end,
                                   stored_value=struct.unpack_from('<Q',body,start)[0])]
            else:
                item=s['params']['result'];span=next(x for x in item['field_spans'] if x['field']=='stored_expression')
                start,end=span['relative_start'],span['relative_end']
                value_fields=[dict(field='stored_expression',relative_start=start,relative_end=end,stored_value=item['stored_expression'])]
            normalized.append(body[:start]+bytes(end-start)+body[end:])
            rows.append(dict(file=s['file'],payload_byte_count=len(body),payload_sha256=_digest(body),fields=value_fields))
        assert len(set(normalized))==1
        varied.append(dict(object_id=key[0],class_guid=key[1],is_primary=key[2],observed_fields=rows,
                           all_bytes_outside_listed_fields_identical=True,normalized_payload_sha256=_digest(normalized[0])))
    resultkey=next(k for k in keys if k[0]==204 and k[2])
    assert snapshots[0]['payloads'][resultkey]==snapshots[3]['payloads'][resultkey]
    componentkey=(3,COMPONENT_GUID,False)
    colorbytes=[s['payloads'][componentkey][181:193] for s in snapshots]
    assert len(set(colorbytes))==1
    resultpartitions=[s['params']['result'] for s in snapshots]
    assert len({x['expression_metadata_hex'] for x in resultpartitions})==1
    report['full_index_contrast']=dict(identical_indexed_identity_and_class_sets=True,
        record_payloads_per_file=220,byte_identical_record_payloads=214,varying_record_payloads=varied,
        unchanged_component_span=dict(relative_start=181,relative_end=193,raw_hex=colorbytes[0].hex()),
        literal_return_result_payload_byte_exact=True,same_parameter_API_tokens_all_four=True,
        native_result_metadata_hex=resultpartitions[0]['expression_metadata_hex'],
        result_payload_changes_confined_to_one_counted_expression=True,
        actual_API_dependency_transitions=[[],['alpha'],['bravo'],[]],
        native_expression_operand_records=None,native_expression_dependency_edges=None,
        interpretation='Actual API dependencies change while only the counted expression changes in the complete result payload; four other string-bearing records and one independently owned scope support u64 change elsewhere. No universal graph-absence claim.')
    first=snapshots[0];data=first['data'];records=first['records'];assembly=first['assembly']
    scope=next(r for r in records if r.is_primary and r.object_id==33)
    support=next(r for r in records if r.is_primary and r.object_id==34)
    def guard(name, changed_data=data, changed_records=records, changed_assembly=assembly):
        result=decode_scope_update_times(changed_data,changed_records,changed_assembly)
        assert not result['decoded'] and len(result['unresolved'])==1
        report['malformed_guards'].append(dict(control=name,rejected=True,reason=result['unresolved'][0]['reason']))
    def patch(position,raw):return data[:position]+raw+data[position+len(raw):]
    guard('nonzero_support_prefix',patch(support.body,b'\1'))
    guard('wrong_reciprocal_scope_owner',patch(support.body+13,struct.pack('<Q',202)))
    guard('untyped_scope_anchor',patch(scope.body+18,struct.pack('<Q',202)))
    guard('untyped_component_definition',patch(scope.body+4,struct.pack('<Q',202)))
    guard('truncated_support',changed_records=[replace(r,end=r.end-1) if r is support else r for r in records])
    guard('duplicate_support_primary',changed_records=records+[support])
    altered=deepcopy(assembly);altered['components'][0]['name']='synthetic wrong name'
    guard('assembly_summary_name_disagrees',changed_assembly=altered)
    for value in (0,2**64-1):
        result=decode_scope_update_times(patch(support.body+23,struct.pack('<Q',value)),records,assembly)
        assert not result['unresolved'] and result['decoded'][0]['stored_u64']==value
        assert result['decoded'][0]['derived_UTC_if_epoch_microseconds'] is None
        report['synthetic_value_controls'].append(dict(stored_u64=value,conditional_UTC=None,
            retained_status=result['decoded'][0]['time_interpretation_status'],captured_occurrence_claim=False))
    # An older quoted-name fixture exercises the same owned support grammar;
    # it supplies no independent journal and receives no time/event validation.
    filename='parameterexpressions-3ddbef2b20bd/text_name_literal.f3d'
    members=read_members(root/filename,zstd_library)
    member=next(n for n in members if n.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
    olddata=members[member];oldrecords,_=design_records(olddata,members[member.replace('BulkStream.dat','MetaStream.dat')])
    oldassembly=decode_assembly(olddata,oldrecords,[])
    olddeps=decode_dependencies(olddata,oldrecords,[],oldassembly)
    oldresult=decode_scope_update_times(olddata,oldrecords,oldassembly)
    assert len(oldresult['decoded'])==1 and not oldresult['unresolved']
    assert decode_dependencies(olddata,oldrecords,[],oldassembly)==olddeps
    report['prior_saved_controls'].append(dict(file=filename,archive_sha256=_digest((root/filename).read_bytes()),
        expected_scope_update_times=oldresult,dependency_reader_unchanged=True,
        independent_journal_time_comparison=None,scope='Older owned support framing control only; no captured time or native expression-edge claim'))
    report['validation']=dict(saved_exports=4,prior_saved_controls=1,complete_indexed_payloads_compared=880,
        typed_user_parameter_replays=12,scope_support_replays=4,independent_journal_intervals=4,
        malformed_guards=len(report['malformed_guards']),synthetic_value_controls=2,
        live_API_calls=0,expression_AST_parses=0,all_checks_passed=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--zstd-library')
    parser.add_argument('--output',type=Path,default=ROOT/'parameter-identity-contrast-decoding.json')
    args=parser.parse_args()
    result=validate(args.root,args.zstd_library)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['validation'],sort_keys=True))
