"""Exact mirrored two-sibling no-merge EDGE naming chains in saved Draft blobs."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags,encode_generic_tag_payload
from decode_counted_asm_names import decode_counted_asm_name
from fusion_archive import read_members

ROOT=Path(__file__).resolve().parent
BASELINE='593bc5e'
DRAFTS=tuple('partinglinedrafts-c4d07c76fcd5/'+case+'.f3d' for case in ('fixed_three','fixed_seven','moving_both_three'))
TAIL_CONTROLS=tuple('splitfacemodes-4fc4adf2a868/'+case+'.f3d' for case in
    ('along_vector','closest_point','line','line_extended','multiple_faces','plane','plane_extended'))


def validate(root,zstd):
    old_source=subprocess.check_output(['git','show',BASELINE+':decode_asm_recipe_tags.py'],cwd=root,text=True)
    old_namespace={'__name__':'old_no_merge_'+BASELINE};exec(compile(old_source,'<git:'+BASELINE+':decode_asm_recipe_tags.py>','exec'),old_namespace)
    old_reader=old_namespace['decode_asm_generic_tags']
    report=dict(scope='Exact five-field no-merge head plus terminal counted generic sibling on typed initial EDGE owners; literal naming correspondence only, no merge behavior or selected/persistent topology identity',
        baseline_commit=BASELINE,baseline_reader_sha256=hashlib.sha256(old_source.encode()).hexdigest(),
        validation_command='python3 validate_draft_no_merge_attributes.py --zstd-library <libzstd path>',
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in
            ('decode_asm_recipe_tags.py','decode_counted_asm_names.py','validate_draft_no_merge_attributes.py')},
        archives=[],blobs=[],new_head_chains=[],old_tail_chains=[],guards=[])
    counts=Counter();guard_example=None
    for filename in (*DRAFTS,*TAIL_CONTROLS):
        path=root/filename;report['archives'].append(dict(archive=filename,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        for member,blob in read_members(path,zstd).items():
            if not member.endswith(('.smb','.smbh')):continue
            parsed=inspect_asm(blob);before_parsed=copy.deepcopy(parsed)
            before=old_reader(blob,parsed=parsed,allow_fpm_tracking=True)
            after=decode_asm_generic_tags(blob,parsed=parsed,allow_fpm_tracking=True)
            records=parsed['records'];limit=next((r['index'] for r in records if r['record_kind']=='marker'),len(records))
            initial=records[:limit];by={r['index']:r for r in initial}
            old_tags={t['attribute_record_index']:t for t in before['tags']};tags={t['attribute_record_index']:t for t in after['tags']}
            recovered=set();local_new=[];local_old=[]
            for marker in initial:
                if marker['name']!='no_merge_attribute-st-attrib':continue
                mt=marker['tokens'];assert len(mt)==5 and [t['tag'] for t in mt]==[12,4,12,12,12]
                assert [mt[i]['kind'] for i in (0,2,3,4)]==['pointer']*4 and mt[1]['kind']=='integer'
                assert [mt[i]['value'] for i in (0,1)]==[-1,-1]
                owner=by[mt[4]['value']];assert owner['name']=='edge'
                if mt[3]['value']==-1:
                    generic=by[mt[2]['value']];gt=generic['tokens']
                    assert filename in DRAFTS and owner['tokens'][0]['value']==marker['index']
                    assert generic['name']=='ATTRIB_CUSTOM-attrib'
                    assert [t['tag'] for t in gt[:5]]==[12,4,12,12,12]
                    assert [gt[i]['value'] for i in (0,1,2,3,4)]==[-1,-1,-1,marker['index'],owner['index']]
                    chain=[marker['index'],generic['index']];orientation='NoMergeHead_GenericTail'
                    assert generic['index'] in tags and tags[generic['index']]['owner_attribute_chain']==chain
                    assert generic['index'] not in old_tags
                    failure=next(e for e in before['unresolved'] if e['attribute_record_index']==generic['index'])
                    assert failure['reason']=='Unsupported no-merge EDGE attribute header'
                    recovered.add(generic['index']);local_new.append(generic['index']);counts['new_head_chains']+=1
                    if guard_example is None:guard_example=blob,parsed,owner,marker,generic
                else:
                    assert mt[2]['value']==-1
                    counts['prior_tail_fixture_controls' if filename in TAIL_CONTROLS else 'draft_existing_tail_controls']+=1
                    generic=by[mt[3]['value']];gt=generic['tokens']
                    assert generic['name']=='ATTRIB_CUSTOM-attrib' and gt[5]['value']=='generic_tag_attrib_def'
                    assert owner['tokens'][0]['value']==generic['index']
                    assert [gt[i]['value'] for i in (0,1,2,3,4)]==[-1,-1,marker['index'],-1,owner['index']]
                    chain=[generic['index'],marker['index']];orientation='GenericHead_NoMergeTail'
                    assert generic['index'] in old_tags and tags[generic['index']]==old_tags[generic['index']]
                    assert tags[generic['index']]['owner_attribute_chain']==chain
                    local_old.append(generic['index']);counts['old_tail_chains']+=1
                payload=decode_counted_asm_name(generic)
                assert encode_generic_tag_payload(payload)==blob[payload['payload_offset']:payload['payload_end_offset']]
                marker_replay=b''.join(bytes([t['tag']])+struct.pack('<q',t['value']) for t in mt)
                assert marker_replay==blob[mt[0]['offset']:marker['end_offset']-1]
                assert all(t in tags[generic['index']].items() for t in payload.items())
                evidence=dict(archive=filename,member=member,blob_sha256=hashlib.sha256(blob).hexdigest(),
                    owner_edge_record_index=owner['index'],owner_byte_offset=owner['offset'],
                    owner_attribute_head_record_index=owner['tokens'][0]['value'],
                    no_merge_record_index=marker['index'],generic_record_index=generic['index'],orientation=orientation,
                    owner_attribute_chain=chain,no_merge_header_tokens=mt,generic_header_tokens=gt[:5],
                    no_merge_header_payload_hex=marker_replay.hex(),counted_generic_payload=payload,
                    shared_generic_tag=tags[generic['index']],
                    scope='Typed owner/head/next/previous reciprocity and exact byte replay; component tuple and class name carry no native identity/solver interpretation')
                report['new_head_chains' if orientation.startswith('NoMerge') else 'old_tail_chains'].append(evidence)
            assert all(tags[identity]==tag for identity,tag in old_tags.items())
            assert {t['attribute_record_index'] for t in after['tags']}==set(old_tags)|recovered
            assert after['unresolved']==[e for e in before['unresolved'] if e['attribute_record_index'] not in recovered]
            assert after['ignored_validated_other_definition_attributes']==before['ignored_validated_other_definition_attributes']
            assert parsed==before_parsed
            counts['blobs']+=1;counts['previous_generic_tags_exact']+=len(old_tags)
            counts['recovered_diagnostics']+=len(recovered)
            report['blobs'].append(dict(archive=filename,member=member,blob_sha256=hashlib.sha256(blob).hexdigest(),
                new_generic_record_indices=local_new,old_tail_generic_record_indices=local_old,
                prior_generic_dictionaries_exact=True,prior_ignored_metadata_exact=True,original_records_unchanged=True,
                expected_decoded=after))
    assert counts['new_head_chains']==counts['recovered_diagnostics']==6
    assert counts['old_tail_chains']==10 and counts['prior_tail_fixture_controls']==8
    assert counts['draft_existing_tail_controls']==2 and counts['blobs']==20
    for filename in DRAFTS:
        rows=[r for r in report['new_head_chains'] if r['archive']==filename]
        assert len(rows)==2 and rows[0]['counted_generic_payload']['payload_hex']==rows[1]['counted_generic_payload']['payload_hex']
        for row in rows:
            payload=row['counted_generic_payload'];assert payload['stored_term_count']==1
            term,=payload['terms'];assert term['name']=='3' and term['stored_index']==0 and term['stored_reference_components_int32']==[304]
    blob,parsed,owner,marker,generic=guard_example
    def rejects(label,record,token_index,value):
        token=record['tokens'][token_index];changed=bytearray(blob);struct.pack_into('<q',changed,token['offset']+1,value)
        summary=decode_asm_generic_tags(bytes(changed),allow_fpm_tracking=True)
        assert generic['index'] not in {t['attribute_record_index'] for t in summary['tags']},label
        failures=[e for e in summary['unresolved'] if e['attribute_record_index']==generic['index']]
        assert len(failures)==1,label
        report['guards'].append(dict(check=label,passed=True,diagnostic=failures[0]))
    rejects('No-merge owner must be same EDGE',marker,4,37)
    rejects('No-merge next cannot point to itself',marker,2,marker['index'])
    rejects('Generic previous must return to no-merge head',generic,3,57)
    rejects('Exact new generic sibling has no own child',generic,0,owner['index'])
    rejects('Exact new generic sibling is terminal',generic,2,marker['index'])
    rejects('EDGE head must point to no-merge head',owner,0,generic['index'])
    rejects('Counted name term count must replay exact payload',generic,10,2)
    rejects('Counted name byte length must agree',generic,11,2)
    counts['guards']=len(report['guards']);counts['archives']=len(report['archives'])
    report['counts']=dict(counts)
    report['limits']=[
        'Only the exact mirrored two-sibling no-merge-head/generic-tail form is added. Existing generic-head/no-merge-tail branch remains unchanged; arbitrary marker subclasses, payloads and longer marker chains are unsupported.',
        'All six recovered generic payloads contain name3/index0/component[304], and each blob has two distinct EDGE owners with that same full payload. This explicitly remains an ambiguous naming correspondence, not a selected source edge.',
        'Component304 is retained as a stored opaque counted integer, never promoted to feature/descriptor/native object identity. no_merge class spelling does not establish merge behavior or solver semantics.',
        'Only initial serialized geometry owner chains are examined. No geometric matching, qualified historical state, persistent topology identity, lifecycle chronology or full-format coverage claim is made.']
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--zstd-library',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'draft-no-merge-attribute-decoding.json');args=parser.parse_args()
    report=validate(ROOT,args.zstd_library);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']))
