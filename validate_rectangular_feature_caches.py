"""Fixed twelve native rectangular Feature-cache fixtures and prior controls."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_rectangular_feature_caches import decode_rectangular_pattern_cache_evidence
from decode_rectangular_cache_evidence import decode_rectangular_cache_evidence
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
POSITIVES = tuple('rectmodes-a069f8f4b8a2/feature_'+s+'.f3d' for s in ('optimized','identical','adjust'))+(
    'rectsymholdouts-cf85ce4a0382/feature_input.f3d',)
CONTROLS = tuple('rectmodes-a069f8f4b8a2/'+s+'.f3d' for s in ('body_one','body_multiple_customaxis','body_sketchlines'))+(
    'rectsymmetry-f09c57dcfd51/symmetric_one.f3d','circularmodes-45f859c1f1b6/body_full.f3d',
    'circularmodes-45f859c1f1b6/feature_optimized.f3d','surfacetools-856ca50cf4c7/offset_positive.f3d',
    'surfacebounds-ac801bb00fae/untrim_all.f3d')
FILES = POSITIVES+CONTROLS


def validate(root,zstd,baseline_path):
    baseline=json.loads(baseline_path.read_text())
    assert baseline['baseline_commit']=='ccd06a7' and baseline['files']==list(FILES)
    before={Path(o['file']).relative_to(root).as_posix():o['streams'][0] for o in baseline['before']}
    report=dict(interface='decode_rectangular_pattern_cache_evidence(data,records,features,member,members,body_blob_bindings)->decoded/unresolved/scope',
        integration=dict(stream='rectangular_cache_evidence',feature_attachment='rectangular_cache_evidence',feature_id='feature_object_id',expected_summary='samples[].expected_summary'),
        scope='Four actual singleton Extrude Feature-input rectangular patterns, including symmetric holdout. Native feature leaf/owned anchor/BODY/same-asset stored-ID route and complete generic/FPM FACE chains precede controller-key/name bijection and all vertex fits. No logical-grid/API/current/persistent identity or serialized per-element transform claimed.',
        baseline=dict(commit='ccd06a7',sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest()),
        samples=[],guards=[],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'decode_rectangular_feature_caches.py','validate_rectangular_feature_caches.py','decode_rectangular_cache_evidence.py',
            'decode_rectangular_pattern_modes.py','decode_circular_feature_caches.py','decode_circular_placement_evidence.py',
            'decode_body_selections.py','decode_body_asm_identifiers.py','decode_asm_recipe_tags.py','decode_brep.py')})
    groups=caches=vertices=fpm_count=0;maximum=0.;saved=None
    for archive in FILES:
        data,records,features,member,members=load(root,archive,zstd);stream=before[archive];bindings=stream['body_blob_bindings']
        original=copy.deepcopy((features,bindings));out=decode_rectangular_pattern_cache_evidence(data,records,features,member,members,bindings)
        assert (features,bindings)==original
        sample=dict(archive=archive,archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),expected_summary=out)
        default=decode_rectangular_cache_evidence(data,records,features,member,members,bindings)
        old=stream.get('rectangular_cache_evidence',default)
        assert old==default
        if archive in POSITIVES:
            assert default['decoded']==[] and default['unresolved']==[]
            assert len(out['decoded'])==1 and not out['unresolved'],out
            row=out['decoded'][0];assert row['feature_object_id']==282
            assert row['pattern_entity_type']=='Features' and row['stored_entity_type_code']==1
            assert row['source_feature_object_ids']==[243] and row['source_native_body_object_ids']==[275]
            assert all(row[k] is None for k in ('API_element_identity','logical_grid_identity','current_placement'))
            source=row['source_feature_input_provenance'];p=source['sources'][0]
            assert source['pattern_entity_type']=='Features' and source['input_proxy_object_id']==290 and source['input_collection_object_id']==286
            assert p['input_descriptor']['descriptor_object_id']==293 and p['input_descriptor']['terminal_object_id']==296
            assert p['source_body_anchor']['object_id']==281 and p['source_body_anchor']['source_owner_object_id']==243
            assert p['source_body_anchor']['native_body_object_id']==275
            by={r.object_id:r for r in records if r.is_primary}
            for native in p['native_records']:
                r=by[native['object_id']]
                assert native==dict(object_id=r.object_id,class_guid=r.class_guid,record_offset=r.start,
                    body_offset=r.body,end_offset=r.end,payload_hex=data[r.body:r.end].hex())
            assert len(p['native_records'])==8
            seed=row['source_cache_bodies'][0]['source_body_binding']
            assert seed['native_body_object_id']==275 and seed['asm_body_index']==1 and seed['asm_stored_entity_id']==6
            api=next(s for s in json.loads((root/Path(archive).parent/'ground_truth.json').read_text())['samples'] if s['file']==Path(archive).name)
            settings=next(f for f in stream['features'] if f['object_id']==282)['tool_settings']
            assert api['settings']['pattern_entity_type']==1 and api['settings']['input_count']==1
            assert row['stored_compute_option_code']==api['settings']['pattern_compute_option']==settings['pattern_compute_option_code']
            assert row['stored_symmetry_flags']==[api['settings']['symmetric_one'],api['settings']['symmetric_two']]
            assert row['stored_instance_key_pairs']==settings['stored_instance_key_pairs']
            assert row['element_record_keys']==settings['stored_element_keys']
            assert len(row['element_cache_groups'])==api['settings']['result_body_count']-1
            assert row['complete_controller_source_group_bijection']
            sample['actual_API_settings']=api['settings'];sample['actual_API_pattern_elements']=api['pattern_elements']
            sample['prior_tool_settings']=settings
            pairs=dict(row['stored_instance_key_pairs']);matched=set()
            for group in row['element_cache_groups']:
                groups+=1;assert pairs[group['stored_element_key']]==group['stored_naming_key'] and len(group['cache_bodies'])==1
                for body in group['cache_bodies']:
                    caches+=1;fit=body['measured_relative_rigid_fit'];vertices+=fit['matched_vertex_count'];maximum=max(maximum,fit['maximum_vertex_residual_raw'])
                    assert fit['matched_vertex_count']==8 and fit['maximum_vertex_residual_raw']<1e-8
                    assert body['stored_face_naming_components'][0]==301 and body['stored_face_naming_components'][2]==group['stored_naming_key']
                    assert body['result_native_body_object_id'] not in matched;matched.add(body['result_native_body_object_id'])
                    assert len(body['complete_result_face_naming_proof'])==6
            proofs=row['source_feature_face_naming_proofs'];assert len(proofs)==len(matched)+1
            for proof in proofs:
                faces=proof['proof']['faces'];assert len(faces)==6 and proof['proof']['FPM_literal_identity'] is None
                fpms=[a for f in faces for a in f['opaque_FPM_attributes']];fpm_count+=len(fpms)
                assert len(fpms)==(6 if proof['native_body_object_id']==275 else 0)
                assert all(a['stored_tracking_literal']==293 and a['definition_name']=='FPM_tracked_attrib_def' for a in fpms)
            if archive==POSITIVES[0]:
                assert row['stored_instance_key_pairs']==[[2,306],[3,304],[5,307],[6,305],[9,308]]
                assert row['element_record_keys']==[1,3,6,2,5,9]
                sample['nonenumeration_key_join_control']='First result cache naming304 belongs to typed element key3, not first sorted pair key2/naming306; no API or logical-grid identity inferred'
                saved=(data,records,features,member,members,bindings,row)
        else:
            assert out==old,(archive,'prior full summary changed')
            sample['prior_complete_summary_exact']=True
        report['samples'].append(sample)
    data,records,features,member,members,bindings,row=saved;primary={r.object_id:r for r in records if r.is_primary}
    def rejected(label,changed_data=None,changed_records=None,changed_members=None):
        out=decode_rectangular_pattern_cache_evidence(changed_data if changed_data is not None else data,
            changed_records if changed_records is not None else records,features,member,
            changed_members if changed_members is not None else members,bindings)
        assert not out['decoded'] and len(out['unresolved'])==1,(label,out)
        report['guards'].append(dict(case=label,reason=out['unresolved'][0]['reason']))
    changed=bytearray(data);struct.pack_into('<Q',changed,primary[296].body+2,282)
    rejected('Feature selector leaf changed to receiver',changed_data=bytes(changed))
    changed=bytearray(data);struct.pack_into('<Q',changed,primary[281].body+92,282)
    rejected('Extrude source anchor owner changed',changed_data=bytes(changed))
    rejected('Conflicting-class duplicate source primary',changed_records=records+[replace(primary[243],class_guid=primary[282].class_guid)])
    blob_member=row['history_blob_member'];blob=members[blob_member];parsed=inspect_asm(blob)
    proof=next(p for p in row['source_feature_face_naming_proofs'] if p['native_body_object_id']==275)
    fpm=proof['proof']['faces'][0]['opaque_FPM_attributes'][0];a=parsed['records'][fpm['attribute_record_index']]
    changed=bytearray(blob);struct.pack_into('<q',changed,a['tokens'][4]['offset']+1,1)
    rejected('FPM reciprocal FACE owner changed',changed_members={**members,blob_member:bytes(changed)})
    changed=bytearray(blob);struct.pack_into('<q',changed,a['tokens'][7]['offset']+1,310)
    literal=decode_rectangular_pattern_cache_evidence(data,records,features,member,{**members,blob_member:bytes(changed)},bindings)
    assert len(literal['decoded'])==1 and not literal['unresolved']
    oldrow=copy.deepcopy(row);newrow=copy.deepcopy(literal['decoded'][0]);oldproof=oldrow.pop('source_feature_face_naming_proofs');newproof=newrow.pop('source_feature_face_naming_proofs')
    assert oldrow==newrow and oldproof!=newproof
    report['opaque_FPM_literal_control']=dict(attribute_record_index=a['index'],original_literal=293,changed_literal=310,
        all_native_identity_groups_and_fits_exact=True,literal_feature_identity=None)
    point=parsed['records'][row['element_cache_groups'][0]['cache_bodies'][0]['measured_relative_rigid_fit']['vertex_correspondence'][-1]['target']['point_index']]
    changed=bytearray(blob);struct.pack_into('<d',changed,point['tokens'][3]['offset']+1,point['tokens'][3]['value'][0]+.125)
    rejected('Identity-fixed eighth point violates rigid fit',changed_members={**members,blob_member:bytes(changed)})
    report['summary']=dict(focused_archives=12,feature_patterns=4,symmetric_feature_holdouts=1,element_groups=groups,
        result_caches=caches,typed_vertex_pairs=vertices,maximum_residual_raw=maximum,opaque_source_FPM_proofs=fpm_count,
        body_controls_complete_exact=4,unrelated_controls_complete_exact=4,guards=len(report['guards']),
        opaque_FPM_literal_control=1,logical_grid_or_API_identity_claims=0,old_warning_clearances=0,main_runs=0,live_calls=0)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--zstd-library');p.add_argument('--baseline',default='/private/tmp/fusion-rectangular-feature-cache-baseline.json');p.add_argument('--output',default='rectangular-feature-cache-decoding.json');args=p.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(ROOT,zstd,Path(args.baseline));Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
