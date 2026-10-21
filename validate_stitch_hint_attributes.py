"""Four actual Patch EDGE stitch-hint siblings and strict ownership guards."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags,encode_generic_tag_payload
from decode_stitch_hint_attributes import decode_stitch_hint_attribute
from fusion_archive import read_members

ROOT=Path(__file__).resolve().parent
DIRECTORY='patchcontinuity-b9b0be85a281'
BASELINE='593bc5e'


def validate(zstd):
    old_source=subprocess.check_output(['git','show',BASELINE+':decode_asm_recipe_tags.py'],cwd=ROOT).decode()
    namespace={};exec(compile(old_source,'<frozen '+BASELINE+' generic reader>','exec'),namespace);old_decode=namespace['decode_asm_generic_tags']
    inventory=json.loads((ROOT/'asm-attribute-frontier-current.json').read_text())
    target_entries=[e for g in inventory['unresolved_groups'] for e in g['entries'] if e['file'].startswith(DIRECTORY+'/')]
    assert len(target_entries)==4
    targets={(e['file'],e['member'],e['attribute_record_index']) for e in target_entries}
    report={'scope':'Only the four new Patch EDGE generic-owner chain failures in two Tangent/Curvature archives, plus Free and accepted no-merge controls; no main/corpus rerun',
        'interface':'decode_stitch_hint_attribute(record,records)->literal header/payload, next/previous IDs and exact initial-geometry ownership/byte spans; independent of generic reader',
        'proposed_shared_change':'Inside attribute_header recognize exact terminal stitch_hint-sys-attrib through the independent helper, return its next=None/previous index, retain existing owner_chain reciprocity and counted generic payload replay.',
        'historical_baseline':BASELINE,'frontier_inventory_file':'asm-attribute-frontier-current.json',
        'frontier_inventory_sha256':hashlib.sha256((ROOT/'asm-attribute-frontier-current.json').read_bytes()).hexdigest(),
        'distinction':'Accepted no_merge sibling has exactly five common tokens; new stitch_hint sibling has the same typed pointer/integer/pointer/pointer/pointer header plus exactly three finite double tokens. Both qualify only via reciprocal EDGE head/generic/sibling links.',
        'samples':[],'malformed_guards':[],'old_controls':[],
        'limits':['Three raw doubles have no decoded tolerance, distance, direction, solver or physical stitch meaning.',
            'Naming tuple/owner-chain recovery does not assign a design object, selected boundary edge, persistent topology or current body lifecycle identity.',
            'Only observed two-node initial EDGE generic-head→terminal stitch-hint chains are accepted; arbitrary class/subclass, payload count, nested or longer chains remain unsupported.',
            'Exact offsets and payload bytes use the original same-blob source; no coordinate normalization, tolerance widening or history-pointer conversion.']}
    captured={};new_count=old_count=production_count=0
    for filename in ('brep_tangent.f3d','brep_curvature.f3d','brep_free.f3d'):
        relative=DIRECTORY+'/'+filename
        for member,blob in read_members(ROOT/relative,zstd).items():
            if not member.endswith(('.smb','.smbh')):continue
            parsed=inspect_asm(blob);assert parsed['complete_token_stream'];before=copy.deepcopy(parsed)
            old=old_decode(blob,parsed,allow_fpm_tracking=True);current=decode_asm_generic_tags(blob,parsed,allow_fpm_tracking=True)
            records=parsed['records'];limit=next((r['index'] for r in records if r['record_kind']=='marker'),len(records))
            hints=[r for r in records[:limit] if r['name']=='stitch_hint-sys-attrib']
            if filename=='brep_free.f3d':
                assert not hints and current==old and not current['unresolved']
                report['old_controls'].append({'archive':relative,'member':member,'kind':'Free has no stitch hint','all_prior_generic_output_exact':True});continue
            assert len(hints)==1;hint=hints[0];evidence=decode_stitch_hint_attribute(hint,records)
            generic=evidence['previous_attribute_record_index'];owner=evidence['owner_record_index']
            assert (relative,member,generic) in targets
            assert old['unresolved']==[{'attribute_record_index':generic,'reason':'Unobserved generic-tag attribute chain class/header'}]
            assert not current['unresolved']
            old_tags={r['attribute_record_index']:r for r in old['tags']};new_tags={r['attribute_record_index']:r for r in current['tags']}
            assert set(new_tags)-set(old_tags)=={generic}
            for index,value in old_tags.items():assert new_tags[index]==value
            assert current['ignored_validated_other_definition_attributes']==old['ignored_validated_other_definition_attributes']
            tag=new_tags[generic];assert tag['owner_kind']=='edge' and tag['owner_record_index']==owner
            assert tag['owner_attribute_chain']==[generic,hint['index']]==evidence['owner_attribute_chain']
            assert encode_generic_tag_payload(tag)==blob[tag['payload_offset']:tag['payload_end_offset']]
            assert bytes.fromhex(evidence['record_hex'])==blob[evidence['record_offset']:evidence['record_end_offset']]
            assert bytes.fromhex(evidence['record_fields_hex'])==blob[evidence['record_fields_offset']:evidence['record_fields_end_offset']]
            assert bytes.fromhex(evidence['numeric_payload_hex'])==blob[evidence['numeric_payload_offset']:evidence['numeric_payload_end_offset']]
            assert [t['kind'] for t in hint['tokens']]==['pointer','integer','pointer','pointer','pointer','double','double','double']
            assert parsed==before
            report['samples'].append({'archive':relative,'member':member,'blob_sha256':hashlib.sha256(blob).hexdigest(),
                'owner_chain_evidence':evidence,'raw_owner_head_token':records[owner]['tokens'][0],
                'raw_generic_header_tokens':records[generic]['tokens'][:5],'raw_hint_tokens':hint['tokens'],
                'new_generic_tag':tag,'expected_generic_reader':current,'old_generic_dictionaries_exact':len(old_tags),
                'exact_record_fields_numeric_and_generic_payload_replay':True,'initial_token_records_unchanged':True})
            captured[(relative,member)]=(blob,parsed,hint['index'],generic,owner)
            old_count+=len(old_tags);new_count+=1;production_count+=1
    assert new_count==production_count==4
    # One existing accepted no-merge EDGE chain, without sweeping its corpus.
    control=json.loads((ROOT/'attribute-owner-variant-decoding.json').read_text())
    row=next(r for r in control['samples'] if r['new_no_merge_record_indices'])
    blob=read_members(ROOT/row['file'],zstd)[row['member']];parsed=inspect_asm(blob)
    old=old_decode(blob,parsed,allow_fpm_tracking=True);current=decode_asm_generic_tags(blob,parsed,allow_fpm_tracking=True)
    assert current==old and not current['unresolved']
    marker=parsed['records'][row['new_no_merge_record_indices'][0]]
    assert marker['name']=='no_merge_attribute-st-attrib' and len(marker['tokens'])==5
    report['old_controls'].append({'archive':row['file'],'member':row['member'],'kind':'Accepted five-token terminal no-merge EDGE sibling',
        'all_prior_generic_output_exact':True,'marker_record_index':marker['index'],'marker_tokens':marker['tokens']})
    blob,parsed,hint_id,generic_id,owner_id=next(iter(captured.values()))
    def reject(label,mutate):
        altered=copy.deepcopy(parsed);mutate(altered['records']);records=altered['records']
        try:decode_stitch_hint_attribute(records[hint_id],records)
        except ValueError as error:reason=str(error)
        else:raise AssertionError((label,'Malformed helper input accepted'))
        current=decode_asm_generic_tags(blob,altered,allow_fpm_tracking=True)
        assert any(e['attribute_record_index']==generic_id for e in current['unresolved'])
        assert not any(t['attribute_record_index']==generic_id for t in current['tags'])
        report['malformed_guards'].append({'case':label,'helper_reason':reason,'production_generic_owner_chain_rejected':True})
    reject('Unknown sibling class',lambda rs:rs[hint_id].update(name='other_hint-sys-attrib'))
    reject('Wrong payload token count',lambda rs:rs[hint_id]['tokens'].pop())
    reject('Nonfinite double payload',lambda rs:rs[hint_id]['tokens'][5].update(value=float('inf')))
    reject('Wrong owner pointer',lambda rs:rs[hint_id]['tokens'][4].update(value=generic_id))
    reject('Wrong previous sibling',lambda rs:rs[hint_id]['tokens'][3].update(value=owner_id))
    reject('Owner head points directly at hint',lambda rs:rs[owner_id]['tokens'][0].update(value=hint_id))
    reject('Nonterminal hint next pointer',lambda rs:rs[hint_id]['tokens'][2].update(value=generic_id))
    reject('Generic head has nonnull previous',lambda rs:rs[generic_id]['tokens'][3].update(value=hint_id))
    report['summary']={'target_initial_chain_diagnostics_recovered':4,'actual_stitch_hint_records':4,
        'production_reader_owner_chain_passes':production_count,'new_generic_tags':new_count,
        'old_generic_tag_dictionaries_exact':old_count,'exact_hint_record_replays':4,'exact_generic_payload_replays':4,
        'Free_and_no_merge_control_blobs':len(report['old_controls']),'malformed_helper_and_production_guards':len(report['malformed_guards']),
        'main_reader_runs':0,'live_API_calls':0,'geometry_identity_claims':0}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default=str(ROOT/'stitch-hint-attribute-decoding.json'));args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(zstd);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
