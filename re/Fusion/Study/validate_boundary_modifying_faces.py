"""Focused native naming registry replay and modifying BoundaryFill face proof."""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_boundary_modifying_faces import decode_boundary_modifying_faces
from decode_native_naming_registry import decode_native_naming_registry, encode_native_naming_registry
from fusion_archive import read_members
from fusion_metadata import design_records


def validate(root,zstd):
    checks,registry_samples,feature_samples,guards=0,[],[],[]
    totals=Counter();saved={}
    files=sorted(root.joinpath('boundaryfills-a0953038318b').glob('*.f3d'))+[
        root/'edgemodes-87edbf67527b/fillet_multiple.f3d',root/'circularmodes-45f859c1f1b6/body_negative.f3d']
    expected={'join_middle.f3d':(5,1),'cut_middle.f3d':(5,1),'intersect_middle.f3d':(6,0)}

    def check(test,reason):
        nonlocal checks
        if not test:
            raise AssertionError(reason)
        checks+=1

    for filename in files:
        members=read_members(filename,zstd);stream=decode_basics(filename,zstd)['streams'][0]
        member=stream['member'];data=members[member]
        records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        mapping=stream['body_asm_identifiers'];before=copy.deepcopy(mapping)
        registry=decode_native_naming_registry(data,records)
        check(not registry['unresolved']and registry['decoded'],'registry control has exact supported reciprocal framing')
        reg,=[r for r in registry['decoded']if not r['registry_is_empty']]
        for entry in registry['decoded']:
            check(encode_native_naming_registry(entry)==data[entry['payload_offset']:entry['payload_offset']+entry['payload_byte_count']],
                  'each populated or explicitly empty registry payload replays exactly')
            if entry['registry_is_empty']:
                check(entry['owner_to_keys']==[]and entry['key_to_owner']==[]and entry['payload_byte_count']==25,
                      'captured empty component registry has both zero counts and exact typed footer')
                totals['empty_registry_controls']+=1
        check(encode_native_naming_registry(reg)==data[reg['payload_offset']:reg['payload_offset']+reg['payload_byte_count']],
              'full stored registry payload replays exactly in both original table orders')
        forward={(key,row['native_owner_object_id'])for row in reg['owner_to_keys']for key in row['naming_keys']}
        reverse={(row['naming_key'],row['native_owner_object_id'])for row in reg['key_to_owner']}
        check(forward==reverse and len(reverse)==len(reg['key_to_owner']),'independent flattened owner/key and reverse tables are bijective')
        check(all(row['stored_owner_field_offset']!=row['stored_key_field_offset']for row in reg['key_to_owner']),
              'owner IDs and naming keys retain separate actual source fields')
        totals['native_registries']+=len(registry['decoded']);totals['registry_owner_rows']+=len(reg['owner_to_keys']);totals['registry_key_rows']+=len(reg['key_to_owner'])
        registry_samples.append({'file':str(filename.relative_to(root)),'member':member,'expected_summary':registry})
        if filename.name=='plane_first.f3d':
            coincident=next(row for row in reg['key_to_owner']if row['naming_key']==304)
            check(coincident['native_owner_object_id']==304 and coincident['native_owner_class_guid']=='49004167-470D-4892-B50E-5C589B1486D2',
                  'captured key/native-ID numeric collision retains independently typed owner fields')
        output=decode_boundary_modifying_faces(data,records,member,members,mapping)
        check(mapping==before,'existing native BODY mapping remains unchanged')
        if filename.name not in expected:
            check(output['decoded']==[]and output['unresolved']==[],'NewBody/unrelated controls do not acquire modifying-face associations')
            continue
        check(not output['unresolved']and len(output['decoded'])==1,'actual modifying case has explicit native/result/name qualification')
        decoded,=output['decoded'];links=decoded['result_FACE_correspondences']
        count,missing=expected[filename.name]
        check(len(links)==count and len(decoded['unmatched_selected_face_recipes'])==missing,'captured whole-group match and counterexample counts')
        owner=next(row for row in reg['owner_to_keys']if row['native_owner_object_id']==decoded['feature_object_id'])
        check(owner['naming_keys']==[decoded['feature_naming_key']],'feature extension key comes from reciprocal native registry rather than BODY name guess')
        for link in links:
            check(link['exact_selected_source_identity']is None and link['persistent_FACE_identity']is None,
                  'stored naming correspondence does not claim persistent face or historical selection identity')
            target=link['result_FACE_naming_tag']
            original=next(row for row in decoded['explicit_modifying_results']if row['explicit_modifying_result_selection']==link['result_selection'])
            check(target in original['body_context']['FACE_naming_tags'],'result FACE belongs to the explicitly selected mapped BODY namespace')
            totals['face_correspondences']+=1;totals['form_'+link['naming_group_form']]+=1
        for result in decoded['explicit_modifying_results']:
            selection=result['explicit_modifying_result_selection']
            ctx=result['body_context']
            check(selection['native_body_object_id']==ctx['native_body_object_id']and selection['descriptor_object_id']==result['result_body_descriptor']['object_id'],
                  'result proxy/descriptor/anchor identity survives independently into exact BODY handle context')
            totals['explicit_modifying_result_body_selections']+=1
            totals['unmatched_result_FACE_groups']+=len(result['unmatched_result_FACE_groups'])
        totals['unmatched_selected_face_recipes']+=missing
        actual=next(s for s in json.loads(filename.parent.joinpath('ground_truth.json').read_text())['samples']if s['file']==filename.name)
        check(actual['operation']+1=={'Join':1,'Cut':2,'Intersect':3}[decoded['operation']],
              'actual saved API operation independently corroborates native feature operation')
        feature_samples.append({'file':str(filename.relative_to(root)),'expected_summary':output,
            'actual_API_controls':{'operation':actual['operation'],'is_remove_tools':actual['is_remove_tools'],
                'output_bodies':actual['output_bodies'],
                'scope':'Saved API operation/result body geometry only; no API persistent face or naming-registry getter supplied these associations.'}})
        saved[filename.name]=data,records,member,members,mapping,registry,output
    data,records,member,members,mapping,registry,output=saved['cut_middle.f3d'];reg,=registry['decoded']

    def decode_changes(data2=None,members2=None):
        d=data if data2 is None else data2
        ms=members if members2 is None else members2
        return decode_native_naming_registry(d,records),decode_boundary_modifying_faces(d,records,member,ms,mapping)

    def rejected_registry(label,offset,value):
        changed=bytearray(data);struct.pack_into('<Q',changed,offset,value)
        rs,fs=decode_changes(bytes(changed),dict(members,**{member:bytes(changed)}))
        check(not rs['decoded']and rs['unresolved']and not fs['decoded']and fs['unresolved'],label)
        guards.append({'guard':label,'registry_diagnostics':rs['unresolved'],'feature_diagnostics':fs['unresolved']})

    reverse=next(row for row in reg['key_to_owner']if row['naming_key']==306)
    rejected_registry('Reverse owner must agree with forward owner of the same key',reverse['stored_owner_field_offset'],243)
    forward=next(row for row in reg['owner_to_keys']if row['native_owner_object_id']==359)
    rejected_registry('Opaque naming key cannot be owned twice',forward['stored_key_field_offsets'][0],301)
    rejected_registry('Typed registry container backlink is required',reg['container_backlink_offset']+1,32)
    # A consistent renumber keeps registry framing valid but cannot qualify old
    # feature-extended names in the untouched ASM cache. Direct exact names stay.
    changed=bytearray(data)
    for offset in(forward['stored_key_field_offsets'][0],reverse['stored_key_field_offset']):
        struct.pack_into('<Q',changed,offset,999)
    rs,fs=decode_changes(bytes(changed),dict(members,**{member:bytes(changed)}))
    check(not rs['unresolved']and not fs['unresolved']and len(fs['decoded'][0]['result_FACE_correspondences'])==4,
          'valid renamed native feature key cannot reuse the old appended cache literal')
    guards.append({'guard':'Consistently renamed feature key preserves registry but rejects old feature-extended FACE correspondence',
        'remaining_exact_entire_recipe_groups':4,'unmatched_recipe_ids':[r['face_recipe']['object_id']for r in fs['decoded'][0]['unmatched_selected_face_recipes']]})
    # Break one half of a paired whole group. A surviving matching term may not
    # be selected as a fallback to qualify the FACE.
    d,rs,m,ms,mp,rg,out=saved['intersect_middle.f3d'];decoded=out['decoded'][0]
    paired=next(a for a in decoded['result_FACE_correspondences']if a['naming_group_form']=='EntireRecipePlusFeatureExtendedRecipeGroup')
    bm=next(r['body_context']['history_blob_member']for r in decoded['explicit_modifying_results'])
    blob=ms[bm];p=inspect_asm(blob);attr=p['records'][paired['result_FACE_naming_tag']['attribute_record_index']]
    term_name=attr['tokens'][12];check(len(term_name['value'])==1,'paired-group guard uses a captured single-byte face label')
    altered=bytearray(blob);altered[term_name['offset']+2]=ord('9')
    result=decode_boundary_modifying_faces(d,rs,m,dict(ms,**{bm:bytes(altered)}),mp)
    check(not result['unresolved']and len(result['decoded'][0]['result_FACE_correspondences'])==5,
          'one matching term does not rescue a broken whole paired group')
    guards.append({'guard':'One half of a paired naming group changed; single-term fallback rejected','remaining_complete_groups':5})
    # Retarget the result descriptor's anchor while retaining its original recipe.
    primary={r.object_id:r for r in records if r.is_primary};desc=primary[363]
    changed=bytearray(data)
    check(data[desc.body+201]==1,'typed result anchor mutation uses the actual captured reference slot')
    struct.pack_into('<Q',changed,desc.body+202,281)
    _,fs=decode_changes(bytes(changed),dict(members,**{member:bytes(changed)}))
    check(not fs['decoded']and fs['unresolved'],'result descriptor anchor must remain reciprocal with owned source context')
    guards.append({'guard':'Modifying result descriptor anchor retargeted','feature_diagnostics':fs['unresolved']})
    return {'stage':'Reciprocal native naming registry and modifying BoundaryFill face groups',
        'interfaces':{'registry':'decode_native_naming_registry(data,records) -> decoded/unresolved/scope',
            'registry_replay':'encode_native_naming_registry(registry) -> exact payload bytes',
            'modifying_faces':'decode_boundary_modifying_faces(data,records,member,members,body_identifier_summary) -> decoded/unresolved/scope'},
        'validation':{'checks':checks,'registry_saved_files':len(files),'modifying_cases':3,**dict(totals),'malformed_guards':guards,'new_API_calls':0},
        'findings':['Forward native owner/key and reverse key/owner tables are independently counted, reciprocal and exactly replayable; a typed footer plus registry-container backlink proves native scope.',
            'The appended306 naming component is explicitly owned by the BoundaryFill feature in the registry. It is not guessed as a result BODY name or native Design ID.',
            'Join selected result BODY naming can retain the source BODY name plus the registry-owned feature key; the complete group is retained. Cut/Intersect use explicit historical result BODY descriptors and the original BODY name.',
            'The three saved operations expose exact whole recipe groups, feature-extended groups, or paired original-plus-feature-extended groups. Every stored term participates; there is no single-term, coordinate or sign-normalization fallback.',
            'Join negative recipe -3 and Cut positive recipe5 have no whole-group result correspondence. Both remain explicit counterexamples instead of receiving inferred geometry/lifecycle assignments.'],
        'limits':['The native registry resolves stored owner fields to independently typed native records. Opaque naming keys never become native object IDs, ASM ordinals or universal persistent topology IDs.',
            'Registry footer/backlink and count domains are bounded to observed framing. The owning history-container record is not otherwise declared fully decoded.',
            'The face helper is bounded to captured one-cell, two-body-tool Join/Cut/Intersect cases, strict single-term recipes and three observed complete naming-group forms.',
            'Result descriptors select historical identities; associations do not classify current-visible/final body lifetime, reconstruct exact selected faces or regenerate Boolean geometry.'],
        'registry_samples':registry_samples,'modifying_face_samples':feature_samples}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--zstd-library',type=Path)
    p.add_argument('--report',type=Path)
    args=p.parse_args();z=args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report=validate(args.root,z)
    (args.report or args.root/'boundary-modifying-face-decoding.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['validation'],indent=2))
