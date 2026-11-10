"""Focused inherited/nested attribute owner-chain proof against saved ASM blobs."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, encode_generic_tag_payload
from fusion_archive import read_members

BASELINE = 'efef90b'
FILES = ['moretools-88a2cd6cad0b/MoveRotate.f3d','moretools-88a2cd6cad0b/MoveTranslate.f3d',
 'movemodes-0dd2f72dd9a7/point_to_position_component.f3d','movemodes-0dd2f72dd9a7/point_to_position_nested_design.f3d'] + [
 'movemodes-34cba3ced135/'+name+'.f3d'for name in ('along_axis','along_sketch_line','free','point_to_point',
 'point_to_position','rotate_axis','xyz_component','xyz_design','xyz_nested_design')] + [
 'surfacebounds-ac801bb00fae/'+name+'.f3d'for name in ('untrim_all','untrim_external','untrim_internal','untrim_manual')] + [
 'surfacetools-856ca50cf4c7/reverse_normal.f3d'] + [
 'splitfacemodes-4fc4adf2a868/'+name+'.f3d'for name in ('along_vector','closest_point','line','line_extended','multiple_faces','plane','plane_extended')]


def validate(root, zstd):
    source = subprocess.run(['git','show',BASELINE+':decode_asm_recipe_tags.py'],cwd=root,check=True,text=True,capture_output=True).stdout
    baseline = {'__name__':'attribute_owner_baseline'}
    exec(compile(source,BASELINE+'-decode_asm_recipe_tags.py','exec'),baseline)
    checks, samples, nested_rows, special_rows, guards = 0, [], [], [], []
    total = Counter()
    nested_example = special_example = None

    def check(test, reason):
        nonlocal checks
        if not test:
            raise AssertionError(reason)
        checks += 1

    for filename in FILES:
        for member, blob in read_members(root/filename,zstd).items():
            if not member.endswith(('.smb','.smbh')):
                continue
            parsed = inspect_asm(blob); before_parsed = copy.deepcopy(parsed)
            old = baseline['decode_asm_generic_tags'](blob,parsed=parsed,allow_fpm_tracking=True)
            new = decode_asm_generic_tags(blob,parsed=parsed,allow_fpm_tracking=True)
            by = {r['index']:r for r in parsed['records']if r['record_kind']=='entity'and r['section']=='geometry'}
            geometry = [r for r in parsed['records']if r['record_kind']=='entity'and r['section']in('geometry','trailing_states')]
            ordinal = {r['index']:i for i,r in enumerate(geometry)}
            new_tags = {t['attribute_record_index']:t for t in new['tags']}
            old_tags = {t['attribute_record_index']:t for t in old['tags']}
            target_errors = []
            for failure in old['unresolved']:
                rec = by[failure['attribute_record_index']]; ts=rec['tokens']
                owner = by.get(ts[4]['value'])
                definition = ts[5]['value']
                if ((definition=='generic_tag_attrib_def'and owner and owner['name']in('body','face','edge'))
                        or definition=='Timestamp_attrib_def'):
                    target_errors.append(failure)
            ids={t['attribute_record_index']for t in target_errors}
            check(not ids.intersection(u['attribute_record_index']for u in new['unresolved']),
                  'all targeted former header/chain diagnostics are resolved by shared reader')
            check(all(new_tags[i]==t for i,t in old_tags.items()),'every previously decoded generic name dictionary remains exact')
            total['previous_generic_tags_exact'] += len(old_tags)
            total['target_diagnostics_recovered'] += len(target_errors)
            local_nested,local_special = [],[]

            def pointer(token, null=False):
                check(token['kind']=='pointer'and token['tag']==12 and isinstance(token['value'],int)and not isinstance(token['value'],bool),
                      'common header pointer type preserved')
                value=token['value']
                if null and value==-1:
                    return None
                check(value in by,'stored pointer remains in bounded initial geometry entity table')
                return value

            def origin(rec):
                return {'inspection_record_index':rec['index'],'geometry_entity_ordinal':ordinal[rec['index']],
                        'kind':rec['name'],'section':rec['section'],'byte_offset':rec['offset']}

            for parent in by.values():
                ts=parent['tokens']
                if parent['name']=='ATTRIB_CUSTOM-attrib'and ts[0]['value']!=-1:
                    owner=by[pointer(ts[4])]
                    check(owner['name']in('body','face')and ts[5]['value']=='generic_tag_attrib_def',
                          'captured nested-head parent is a BODY/FACE generic naming attribute')
                    child=by[pointer(ts[0])]; ct=child['tokens']
                    check(child['name']=='ATTRIB_CUSTOM-attrib'and [t['tag']for t in ct[:5]]==[12,4,12,12,12],
                          'nested child retains typed common custom header')
                    check([ct[i]['value']for i in (0,1,2,3)]==[-1,-1,-1,-1]and pointer(ct[4])==parent['index'],
                          'child is singleton, has no own child and returns to exact parent attribute')
                    check([r['index']for r in by.values()if r['name']=='ATTRIB_CUSTOM-attrib'and r['tokens'][0]['value']==child['index']]==[parent['index']],
                          'nested child has exactly one literal parent head reference')
                    check(parent['index']in new_tags,'non-null header parent receives a topology naming tag')
                    parent_tag=new_tags[parent['index']]
                    check(encode_generic_tag_payload(parent_tag)==blob[parent_tag['payload_offset']:parent_tag['payload_end_offset']],
                          'newly admitted parent naming payload byte replay remains exact')
                    check(child['index']not in new_tags,'empty nested child is not promoted to topology naming tag')
                    nested_summary=[a for a in new['ignored_validated_other_definition_attributes']if a['attribute_record_index']==child['index']]
                    check(len(nested_summary)==1,'nested child has exactly one validated metadata entry')
                    child_summary,=nested_summary
                    check(child_summary['owner_record_index']==parent['index']and child_summary['owner_kind']=='ATTRIB_CUSTOM-attrib',
                          'shared metadata retains immediate attribute owner instead of assigning the root FACE/BODY')
                    result={'file':filename,'member':member,'root_owner':origin(owner),'parent_attribute':origin(parent),
                        'child_attribute':origin(child),'raw_parent_header_fields':ts[:5],'raw_child_header_fields':ct[:5],
                        'shared_parent_generic_name':parent_tag,'shared_nested_child_metadata':child_summary,
                        'scope':'Typed singleton metadata ownership only; no child literal/native identity, chronological state or topology selection meaning.'}
                    nested_rows.append(result);local_nested.append(parent['index'])
                    total['nested_parent_'+owner['name']] += 1
                    if nested_example is None:
                        nested_example=blob,parsed,parent,child
                if parent['name']=='no_merge_attribute-st-attrib':
                    check(len(ts)==5 and [t['tag']for t in ts]==[12,4,12,12,12],
                          'no_merge literal record contains exactly the common five typed header fields')
                    check(ts[0]['value']==-1 and ts[1]['value']==-1 and ts[2]['value']==-1,
                          'captured no_merge sibling is terminal and has no own child')
                    previous=by[pointer(ts[3])]; owner=by[pointer(ts[4])]
                    check(owner['name']=='edge'and previous['name']=='ATTRIB_CUSTOM-attrib'
                          and previous['tokens'][5]['value']=='generic_tag_attrib_def',
                          'noncustom marker is a sibling of a generic name on an EDGE')
                    check(previous['tokens'][2]['value']==parent['index']and previous['tokens'][4]['value']==owner['index']
                          and owner['tokens'][0]['value']==previous['index'],
                          'EDGE/head/generic/marker next-previous-owner links all reciprocal')
                    check(previous['index']in new_tags,'generic name survives the validated noncustom sibling')
                    replay=b''.join(bytes([t['tag']])+struct.pack('<q',t['value'])for t in ts)
                    check(replay==blob[ts[0]['offset']:parent['end_offset']-1],'entire noncustom marker payload byte replay exact')
                    special_rows.append({'file':filename,'member':member,'owner':origin(owner),'generic_sibling':origin(previous),
                        'noncustom_sibling':origin(parent),'stored_header_fields':ts,'payload_hex':replay.hex(),
                        'scope':'Literal class and reciprocal five-field header only; merge behavior/solver semantics remain unassigned.'})
                    local_special.append(parent['index']);total['no_merge_siblings'] += 1
                    if special_example is None:
                        special_example=blob,parsed,previous,parent
            check(parsed==before_parsed,'all original parsed records and tokens remain unchanged')
            samples.append({'file':filename,'member':member,'former_target_diagnostics':target_errors,
                'new_unresolved_retained':new['unresolved'],'new_nested_parent_record_indices':local_nested,
                'new_no_merge_record_indices':local_special,'previous_generic_names_exact':len(old_tags)})
    check(total['target_diagnostics_recovered']==111,'exact targeted FACE/BODY/EDGE/Timestamp diagnostic inventory recovered')
    check(total['nested_parent_face']==77 and total['nested_parent_body']==13 and total['no_merge_siblings']==8,
          'exact raw variant counts agree with the original diagnostic inventory')

    def rejects(label, example, token, value, target):
        blob,parsed,*_=example
        changed=bytearray(blob);struct.pack_into('<q',changed,token['offset']+1,value)
        rejected=decode_asm_generic_tags(bytes(changed),allow_fpm_tracking=True)
        check(target not in {t['attribute_record_index']for t in rejected['tags']}
              and target in {u['attribute_record_index']for u in rejected['unresolved']},label)
        guards.append({'guard':label,'rejected_parent_attribute_record_index':target,
            'diagnostics':[u for u in rejected['unresolved']if u['attribute_record_index']==target]})
    blob,parsed,parent,child=nested_example
    rejects('Nested child owner fails its parent backlink',nested_example,child['tokens'][4],parent['tokens'][4]['value'],parent['index'])
    rejects('Nested parent cannot own itself',nested_example,parent['tokens'][0],parent['index'],parent['index'])
    rejects('Captured singleton child cannot gain a next sibling',nested_example,child['tokens'][2],parent['index'],parent['index'])
    rejects('Parent topological owner no longer reciprocal',nested_example,parent['tokens'][4],0,parent['index'])
    blob,parsed,generic,marker=special_example
    rejects('Noncustom sibling previous pointer must return to generic sibling',special_example,marker['tokens'][3],-1,generic['index'])
    rejects('Noncustom sibling owner must agree with EDGE chain',special_example,marker['tokens'][4],0,generic['index'])
    rejects('Noncustom sibling common-header sentinel remains strict',special_example,marker['tokens'][1],0,generic['index'])
    return {'stage':'Nested custom attribute heads and bounded noncustom EDGE siblings',
        'validation':{'checks':checks,'saved_files':len(FILES),'saved_blobs':len(samples),**dict(total),'malformed_guards':guards,'new_API_calls':0},
        'baseline':{'commit':BASELINE,'module':'decode_asm_recipe_tags.py','source_sha256':hashlib.sha256(source.encode()).hexdigest(),
                    'scope':'Read-only baseline generic owner rules with current pure payload helper; no baseline archive or source mutations.'},
        'findings':['All 90 nonnull parent header pointers form one-level singleton metadata ownership. The immediate child owner is the parent attribute; BODY/FACE remains a separate root owner.',
            'Thirteen Timestamp errors were indirect: the reciprocal BODY sibling chain passed through a generic parent with its own nested metadata child.',
            'Eight no_merge_attribute-st-attrib records share exactly five typed common header fields with custom attributes and occur as terminal reciprocal EDGE siblings. Their class name does not assign solver behavior.',
            'Initial geometry ordinal values equal inspection indices in these examples, but both identities and original byte origins are retained separately. No fixed-offset conversion is introduced.'],
        'limits':['The face_recipes validator separately owns the empty child payload framing/literal distribution proof; this report focuses owner/header chains and production classification.',
            'Only captured singleton nested generic metadata and exact terminal no_merge EDGE sibling layouts are qualified; arbitrary nesting, cycles, subclasses and payload variants remain unsupported.',
            'No new feature selection, persistent identity, historical state or lifecycle semantics are assigned.'],
        'samples':samples,'nested_owner_provenance':nested_rows,'noncustom_EDGE_sibling_provenance':special_rows}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--zstd-library',type=Path)
    p.add_argument('--report',type=Path)
    args=p.parse_args()
    z=args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result=validate(args.root,z)
    (args.report or args.root/'attribute-owner-variant-decoding.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['validation'],indent=2))
