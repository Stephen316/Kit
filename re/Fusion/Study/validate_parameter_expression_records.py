"""Focused full-index expression-storage contrast; no runtime dependency reader.

This is a source-byte inspector for offline contrasts. The stored expression is
one counted UTF16LE string, not a claimed native token/operand graph. Existing
parameter/table readers establish identity, cached-value and reciprocal owner
semantics. Opaque expression metadata stays literal; no AST is parsed here.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

from decode_parameters import decode_stream, read_string
from decode_parameter_tables import decode_parameter_tables, NUMERIC
from decode_sketch import reference

SCOPE = ('Complete observed unbound user-parameter payload field framing and reciprocal '
         'owned identity; native expression operands/dependency edges unresolved')


def _encode_expression_record(item):
    """Replay one complete observed payload from typed fields; not a file writer."""
    def string(value):
        raw=value.encode('utf-16le')
        return struct.pack('<I',len(raw)//2)+raw
    body=bytes(7)+struct.pack('<I',6)+b'\0'+string(item['comment'])
    body+=struct.pack('<I',item['stored_parameter_index'])+b'\0'+string(item['stored_expression'])
    body+=bytes.fromhex(item['expression_metadata_hex'])
    for field in ('role','stored_text_value','display_units','parameter_name'):
        body+=string(item[field])
    body+=struct.pack('<d',item['stored_numeric_cache'])+b'\0\1'+struct.pack('<Q',item['collection_object_id'])+b'\0\0'
    return body


def _inspect_expression_records(data,records):
    """Inspect only strictly owned unbound user records, not derived syntax edges."""
    records=list(records)
    parameters,rejected=decode_stream(data,records)
    tables=decode_parameter_tables(data,records,parameters)
    primary={}
    for r in records:
        if r.is_primary:primary.setdefault(r.object_id,[]).append(r)
    result=dict(decoded=[],unresolved=[],native_expression_operand_records=None,
                native_expression_dependency_edges=None,scope=SCOPE)
    for parameter in tables['user_parameters']:
        identity=parameter['parameter_object_id']
        try:
            choices=primary.get(identity,[])
            if len(choices)!=1 or choices[0].class_guid!=NUMERIC:
                raise ValueError('Expression source is not one typed primary user parameter')
            record=choices[0];body=data[record.body:record.end]
            if body[:12]!=bytes(7)+struct.pack('<I',6)+b'\0':
                raise ValueError('Unobserved expression record prefix')
            spans=[dict(field='header',kind='literal_bytes',relative_start=0,relative_end=12)]
            def text(cursor,field):
                value,end=read_string(body,cursor,allow_text_controls=True)
                spans.append(dict(field=field,kind='counted_UTF16LE',relative_start=cursor,relative_end=end,
                                  stored_UTF16_code_units=(end-cursor-4)//2))
                return value,end
            comment,cursor=text(12,'comment')
            index=struct.unpack_from('<I',body,cursor)[0]
            spans.append(dict(field='stored_parameter_index',kind='u32',relative_start=cursor,relative_end=cursor+4));cursor+=4
            if body[cursor]!=0:raise ValueError('Only absent feature bindings admitted')
            spans.append(dict(field='absent_feature_binding',kind='literal_null',relative_start=cursor,relative_end=cursor+1));cursor+=1
            expression,cursor=text(cursor,'stored_expression')
            metadata=body[cursor:cursor+10]
            if len(metadata)!=10:raise ValueError('Truncated expression metadata')
            spans.append(dict(field='expression_metadata',kind='literal_ten_bytes',relative_start=cursor,relative_end=cursor+10));cursor+=10
            values={}
            for field in ('role','stored_text_value','display_units','parameter_name'):
                values[field],cursor=text(cursor,field)
            cache=struct.unpack_from('<d',body,cursor)[0]
            spans.append(dict(field='stored_numeric_cache',kind='float64',relative_start=cursor,relative_end=cursor+8));cursor+=8
            if body[cursor]!=0:raise ValueError('Unobserved parameter owner separator')
            spans.append(dict(field='owner_separator',kind='literal_zero',relative_start=cursor,relative_end=cursor+1));cursor+=1
            owner=reference(body,cursor)
            if owner!=parameter['collection_object_id'] or cursor+11!=len(body):
                raise ValueError('Expression source owner/complete extent disagrees')
            spans.append(dict(field='collection_owner',kind='typed_reference',relative_start=cursor,relative_end=cursor+11))
            for first,second in zip(spans,spans[1:]):
                if first['relative_end']!=second['relative_start']:raise ValueError('Expression payload field partition has a gap')
            for span in spans:
                span.update(absolute_start=record.body+span['relative_start'],absolute_end=record.body+span['relative_end'])
            item=dict(parameter_object_id=identity,class_guid=record.class_guid,
                      parameter_name=values['parameter_name'],comment=comment,stored_parameter_index=index,
                      stored_expression=expression,expression_metadata_hex=metadata.hex(),
                      role=values['role'],stored_text_value=values['stored_text_value'],display_units=values['display_units'],
                      stored_numeric_cache=cache,value_type=parameter['value_type'],
                      collection_object_id=owner,name_registry_object_id=parameter['name_registry_object_id'],
                      field_spans=spans,payload_byte_count=len(body),source_payload_sha256=hashlib.sha256(body).hexdigest(),
                      native_operand_records=None,native_dependency_edges=None,
                      source_status='One counted stored expression string; no separately identified native operand/opcode block in this complete payload',
                      scope=SCOPE)
            if _encode_expression_record(item)!=body:
                raise ValueError('Complete typed expression payload replay differs')
            result['decoded'].append(item)
        except (ValueError,UnicodeError,IndexError,KeyError,struct.error) as error:
            result['unresolved'].append(dict(parameter_object_id=identity,reason=str(error)))
    # Table failures are not silently converted into unowned expression rows.
    result['unresolved'].extend(dict(source='parameter_table',**row) for row in tables['unresolved'])
    result['unresolved'].extend(dict(source='parameter_record',**row) for row in rejected)
    return result


def validate_fixtures(root,zstd_library=None):
    """Contrast complete indexed payloads, not repeated literal-ID searches."""
    from fusion_archive import read_members
    from fusion_metadata import design_records
    root=Path(root)
    prior=json.loads((root/'parameter-native-link-audit.json').read_text())
    files=[s['file'] for s in prior['samples']]
    report=dict(status='No separate native expression operand/opcode/dependency record identified; no runtime decoder or integration hook added',
        scope='Complete source-payload partitions and full-index comparison across10 aligned saved expression/function exports, with one3-parameter identity/control archive',
        prior_work=['parameter-native-link-audit.json','parameter-dependency-structure-audit.json'],
        method='Complete metadata-indexed record key/body comparison plus exact typed parameter field partition/replay; no ID pattern scan and no expression AST parsing',
        native_expression_operand_records=None,native_expression_dependency_edges=None,
        integration='Evidence report only. Preserve existing derived-expression labels and unresolved native edges; do not add a runtime helper duplicating the parameter reader.',
        samples=[],full_index_contrast={},malformed_guards=[],limitations=[
            'Independent documents were exported, so arbitrary document/bookkeeping changes cannot be causally separated from expression changes.',
            'Two changing non-string payload spans totaling20bytes remain opaque. They are retained explicitly and not assigned colors/timestamps or ruled out as expression-related storage.',
            'The complete observed parameter payload has no unpartitioned bytes, but its ten-byte expression metadata still has only partial semantics. No native operand structure is inferred from invariant metadata.',
            'A serialized UTF16 expression name occurrence is not a native reference edge. Quoted names and unused owned parameters are explicit negative controls.',
            'This does not prove that Fusion lacks compressed, implicit, alternate-namespace or regeneration-time dependency representation.'],
        next_action={'generator':'GenerateParameterIdentityContrasts.py','status':'Prepared previously; not executed',
            'reason':'The remaining arbitrary UUID/string/20opaque-byte changes require same-document, same-ID, same-expression-length and same-result contrasts before attributing any field to native dependencies.',
            'contrast':'literal10mm -> alpha reference -> bravo reference -> literal return; retain source IDs and actual dependencyParameters getters',
            'present_Fusion_dispatch':False})
    indexed=[]; saved=None; record_count=0; api_edges=0
    for filename in files:
        members=read_members(root/filename,zstd_library)
        member=next(n for n in members if n.endswith('FusionDesignSegmentType1/BulkStream.dat'))
        data=members[member];records,index=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        result=_inspect_expression_records(data,records)
        assert not result['unresolved'],(filename,result['unresolved'])
        truth=json.loads((root/filename).parent.joinpath('ground_truth.json').read_text())
        sample=next(s for s in truth['samples'] if s['file']==Path(filename).name)
        actual={p['name']:p for p in sample.get('parameters',sample.get('user_parameters',[]))}
        row=dict(file=filename,member=member,design_record_count=len(records),inspected_parameter_records=result['decoded'],
                 independently_captured_API_dependencies_only=[])
        for parameter in result['decoded']:
            a=actual[parameter['parameter_name']]
            assert parameter['stored_expression']==a['expression']
            if parameter['value_type']=='Text':assert parameter['stored_text_value']==a['text_value']
            else:assert parameter['stored_numeric_cache']==a['value']
            api_edges+=len(a['dependency_names'])
            row['independently_captured_API_dependencies_only'].append(dict(parameter_object_id=parameter['parameter_object_id'],
                parameter_name=parameter['parameter_name'],API_dependency_names=a['dependency_names'],API_dependent_names=a['dependent_names'],
                source='Actual capture getter; not a decoded native edge'))
            record_count+=1
        report['samples'].append(row)
        if len(records)==221:
            mapping={(r.object_id,r.class_guid,r.is_primary):data[r.body:r.end] for r in records}
            assert len(mapping)==221
            indexed.append((filename,mapping,data,records,result))
        if filename.endswith('/product_sum.f3d'):saved=(data,records,result)
    assert len(indexed)==10
    keys=set(indexed[0][1]);assert all(set(row[1])==keys for row in indexed)
    varying=[key for key in sorted(keys) if len({row[1][key] for row in indexed})>1]
    assert len(varying)==8
    contrast=dict(files=[row[0] for row in indexed],identical_indexed_identity_and_class_sets=True,
        record_payloads_per_file=221,byte_identical_record_payloads=221-len(varying),varying_record_payloads=[],
        new_or_missing_operand_record_identities=0,unclassified_variable_nonstring_byte_spans=[])
    # These offsets describe only the fully aligned221-record study layout.
    # Each counted string is validated before masking; opaque spans remain
    # expressly unclassified. No mask is a claim of causal independence.
    strings={1:[(117,'asset_member_string')],3:None,57:[(43,'occurrence_UUID_string'),(119,'occurrence_UUID_string')],
             200:[(43,'configuration_member_string')],201:[(42,'configuration_rule_member_string')]}
    for key in varying:
        identity,guid,primary=key
        item=dict(object_id=identity,class_guid=guid,is_primary=primary,
                  payload_lengths=sorted({len(row[1][key]) for row in indexed}),varying_fields=[],observed_values=[])
        if identity==205:
            residues=[]
            for filename,mapping,data,records,result in indexed:
                parameter=next(p for p in result['decoded'] if p['parameter_object_id']==205)
                raw=mapping[key]
                selected={s['field']:raw[s['relative_start']:s['relative_end']] for s in parameter['field_spans']}
                # Cached text/numeric values, display unit and value-kind are
                # distinct stored fields, not imaginary expression operands.
                variable=('stored_expression','stored_text_value','display_units','stored_numeric_cache')
                residue=b''.join(selected[field] for field in selected if field not in variable and field!='expression_metadata')+selected['expression_metadata'][4:]
                residues.append(residue)
                item['observed_values'].append(dict(file=filename,stored_expression=parameter['stored_expression'],
                    value_type=parameter['value_type'],display_units=parameter['display_units'],stored_text_value=parameter['stored_text_value'],
                    stored_numeric_cache=parameter['stored_numeric_cache'],expression_metadata_hex=parameter['expression_metadata_hex']))
            assert len(set(residues))==1
            item.update(varying_fields=list(variable)+['expression_metadata.u32_value_kind'],
                        all_other_typed_field_bytes_identical=True,nonvalue_residue_sha256=hashlib.sha256(residues[0]).hexdigest(),
                        separate_native_operand_block=None)
        else:
            if identity==3 and primary:definitions=[(137,'Part_Number_value_string')];opaque=[]
            elif identity==3:definitions=[(414,'component_UUID_string'),(517,'component_UUID_string')];opaque=[(181,193)]
            elif identity==34:definitions=[];opaque=[(23,31)]
            else:definitions=strings[identity];opaque=[]
            normalized=[]
            for filename,mapping,*_ in indexed:
                raw=mapping[key];masked=bytearray(raw);values=[]
                for offset,label in definitions:
                    value,end=read_string(raw,offset)
                    if 'UUID' in label:assert re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',value)
                    masked[offset:end]=bytes(end-offset)
                    values.append(dict(field=label,relative_start=offset,relative_end=end,value=value))
                for start,end in opaque:
                    masked[start:end]=bytes(end-start)
                    values.append(dict(field='unclassified_literal_bytes',relative_start=start,relative_end=end,raw_hex=raw[start:end].hex()))
                normalized.append(bytes(masked));item['observed_values'].append(dict(file=filename,fields=values))
            assert len(set(normalized))==1,(key,'unclassified varying residue')
            item.update(all_bytes_outside_listed_fields_identical=True,normalized_payload_sha256=hashlib.sha256(normalized[0]).hexdigest(),
                        varying_fields=[dict(field=label,relative_start=offset) for offset,label in definitions]+[
                            dict(field='unclassified_literal_bytes',relative_start=start,relative_end=end) for start,end in opaque])
            if opaque:contrast['unclassified_variable_nonstring_byte_spans'].append(dict(object_id=identity,class_guid=guid,
                spans=[dict(relative_start=a,relative_end=b,byte_count=b-a) for a,b in opaque],interpretation=None))
        contrast['varying_record_payloads'].append(item)
    report['full_index_contrast']=contrast
    data,records,result=saved
    parameter=next(p for p in result['decoded'] if p['parameter_object_id']==205)
    def fail(label,position,replacement):
        changed=bytearray(data);changed[position:position+len(replacement)]=replacement
        out=_inspect_expression_records(bytes(changed),records)
        assert not any(p['parameter_object_id']==205 for p in out['decoded']) and out['unresolved']
        report['malformed_guards'].append(dict(label=label,rejected=True,reasons=out['unresolved']))
    spans={s['field']:s for s in parameter['field_spans']}
    fail('Oversized stored expression string extent',spans['stored_expression']['absolute_start'],struct.pack('<I',999999))
    fail('Unobserved value-kind metadata',spans['expression_metadata']['absolute_start'],struct.pack('<I',2))
    fail('Nonreciprocal collection owner',spans['collection_owner']['absolute_start']+1,struct.pack('<Q',17))
    report['validation']=dict(saved_files=len(files),fully_partitioned_parameter_payloads=record_count,typed_payload_replays=record_count,
        indexed_contrast_files=len(indexed),indexed_record_payloads_compared=221*len(indexed),varying_payload_identities=len(varying),
        byte_identical_payload_identities=221-len(varying),unclassified_variable_nonstring_bytes=20,
        actual_API_dependency_edges=api_edges,new_decoded_native_dependency_edges=0,malformed_guards_passed=len(report['malformed_guards']),
        new_runtime_decoder_added=False,new_live_Fusion_calls=0)
    return report
