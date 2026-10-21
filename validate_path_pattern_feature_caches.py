"""Fixed eighteen Path cache summaries, with focused dual-route Feature proofs."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_path_pattern_feature_caches import decode_path_pattern_cache_evidence
from decode_path_pattern_cache_evidence import decode_path_pattern_cache_evidence as default_reader
from decode_placement import decode_placement
from decode_sketch import decode_sketches
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
BODY_FILES=tuple('pathpatterns-de9857f6a1bc/'+s+'.f3d' for s in (
    'spacing','extent','start_offset','flipped','symmetric','arc_identical','arc_along','multiple_bodies','suppressed_instance'))+tuple(
    'pathpatterncomposites-b6b4cf615504/'+s+'.f3d' for s in ('composite_identical','composite_along','spline_along','composite_multiple'))
FEATURE_FILES=tuple('pathpatterninputs-7edfa558db34/feature_'+s+'.f3d' for s in ('optimized','identical'))
CONTROLS=('rectmodes-a069f8f4b8a2/body_one.f3d','rectmodes-a069f8f4b8a2/feature_optimized.f3d','circularmodes-45f859c1f1b6/body_full.f3d')
FILES=BODY_FILES+FEATURE_FILES+CONTROLS


def validate(root,zstd,baseline_path):
    baseline=json.loads(baseline_path.read_text());assert baseline['baseline_commit']=='56495ea' and baseline['files']==list(FILES)
    before={Path(o['file']).relative_to(root).as_posix():o['streams'][0] for o in baseline['before']}
    report=dict(interface='decode_path_pattern_cache_evidence(data,records,features,member,members,body_blob_bindings)->decoded/unresolved/scope',
        integration=dict(stream='path_pattern_cache_evidence',feature_attachment='path_pattern_cache_evidence',feature_id='feature_object_id',expected_summary='samples[].expected_summary'),
        scope='Two saved singleton Extrude Feature PathPatterns plus thirteen BODY/composite cases and three unrelated controls. Full original native Feature input/association/anchor proof and actual sketch/placement/assembly fragments precede common native key/cache joins. No API identity/traversal/current-state or serialized per-element matrix claimed.',
        baseline=dict(commit='56495ea',sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest()),
        samples=[],guards=[],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'decode_path_pattern_feature_caches.py','validate_path_pattern_feature_caches.py','decode_path_pattern_cache_evidence.py',
            'decode_path_pattern_inputs.py','decode_path_patterns.py','decode_path_pattern_composites.py','decode_sketch.py',
            'decode_placement.py','decode_assembly.py','decode_body_selections.py','decode_body_asm_identifiers.py',
            'decode_circular_feature_caches.py','decode_circular_placement_evidence.py','decode_asm_recipe_tags.py')})
    groups=caches=vertices=feature_groups=feature_vertices=fpm_count=0;max_residual=0.;saved=None
    truth=json.loads((root/'pathpatterninputs-7edfa558db34/ground_truth.json').read_text())
    for archive in FILES:
        data,records,features,member,members=load(root,archive,zstd)
        decode_sketches(data,records,features);decode_placement(data,records,features)
        stream=before[archive];bindings=stream['body_blob_bindings'];original=copy.deepcopy((features,bindings))
        out=decode_path_pattern_cache_evidence(data,records,features,member,members,bindings)
        assert (features,bindings)==original
        sample=dict(archive=archive,archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),expected_summary=out,caller_metadata_unchanged=True)
        default=default_reader(data,records,features,member,members,bindings)
        if archive in CONTROLS:
            assert out==default and not out['decoded'] and not out['unresolved']
            sample['unrelated_complete_empty_control']=True
        else:
            assert len(out['decoded'])==1 and not out['unresolved'],(archive,out)
            row=out['decoded'][0];assert row['complete_controller_source_group_bijection']
            assert all(row[k] is None for k in ('API_element_identity','logical_grid_identity','current_placement'))
            pairs=dict(row['active_instance_ordinal_pairs']);assert len(row['element_cache_groups'])==len(pairs)
            for group in row['element_cache_groups']:
                groups+=1;assert pairs[group['stored_element_ordinal']]==group['stored_naming_key']
                assert {b['source_native_body_object_id'] for b in group['cache_bodies']}==set(row['source_native_body_object_ids'])
                for body in group['cache_bodies']:
                    caches+=1;fit=body['measured_relative_rigid_fit'];vertices+=fit['matched_vertex_count'];max_residual=max(max_residual,fit['maximum_vertex_residual_raw'])
                    assert fit['matched_vertex_count']==8 and fit['maximum_vertex_residual_raw']<1e-8
                    assert body['stored_face_naming_components'][2]==group['stored_naming_key']
            if archive in BODY_FILES:
                assert out==default
                sample['shared_BODY_dictionary_exact']=True
                if archive.endswith('/suppressed_instance.f3d'):
                    assert row['stored_suppressed_element_ordinals']==[1]
                    assert row['suppressed_cache_groups']==[dict(stored_element_ordinal=1,stored_naming_key=305,element_object_id=row['element_record_object_ids'][1],result_cache_assignment=None)]
                    sample['suppression_scope']='Literal nonseed mask removes naming305 pair only; no API ID/visibility assignment'
            else:
                assert not default['decoded'] and not default['unresolved']
                assert row['feature_object_id']==363 and row['pattern_entity_type']=='Features' and row['stored_entity_type_code']==1
                assert row['source_feature_object_ids']==[243] and row['source_native_body_object_ids']==[275]
                assert row['stored_instance_ordinal_pairs']==[[1,305],[2,306]] and row['element_record_ordinals']==[0,1,2]
                assert row['stored_suppressed_element_ordinals']==[]
                source=row['source_feature_input_provenance'];p=source['sources'][0];item=p['input_descriptor']
                assert source['input_proxy_object_id']==371 and source['input_collection_object_id']==367
                assert item['descriptor_object_id']==374 and item['terminal_object_id']==377 and item['source_feature_object_id']==243
                assert [item[k] for k in ('association_record_object_id','association_bridge_object_id','association_terminal_object_id')]==[498,499,500]
                assert item['source_body_anchor_object_id']==281 and p['source_body_anchor']['object_id']==281
                assert p['source_body_anchor']['source_owner_object_id']==243 and p['source_body_anchor']['native_body_object_id']==275
                assert source['fresh_assembly_unresolved']==[]
                old=next(f for f in stream['features'] if f['object_id']==363)['tool_settings']
                assert source['full_path_input_settings']==old
                assert all(source[k] is None for k in ('exact_API_handle_identity','current_source_identity','persistent_source_identity','qualified_historical_state','path_traversal'))
                by={r.object_id:r for r in records if r.is_primary}
                assert len(p['native_records'])==10
                for native in p['native_records']:
                    r=by[native['object_id']];assert native==dict(object_id=r.object_id,class_guid=r.class_guid,record_offset=r.start,body_offset=r.body,end_offset=r.end,payload_hex=data[r.body:r.end].hex())
                seed=row['source_cache_bodies'][0]['source_body_binding'];assert seed['asm_body_index']==1 and seed['asm_stored_entity_id']==24
                proofs=row['source_feature_face_naming_proofs'];assert len(proofs)==3
                for proof in proofs:
                    assert len(proof['proof']['faces'])==6 and proof['proof']['FPM_literal_identity'] is None
                    fpms=[a for f in proof['proof']['faces'] for a in f['opaque_FPM_attributes']];fpm_count+=len(fpms)
                    assert len(fpms)==(6 if proof['native_body_object_id']==275 else 0)
                api=next(s for s in truth['samples'] if s['file']==Path(archive).name)
                sample['actual_API_settings']=api.get('settings',api.get('requested'))
                sample['prior_full_Path_input_settings_exact']=True
                feature_groups+=len(row['element_cache_groups']);feature_vertices+=sum(b['measured_relative_rigid_fit']['matched_vertex_count'] for g in row['element_cache_groups'] for b in g['cache_bodies'])
                if saved is None:saved=(data,records,features,member,members,bindings,row)
        report['samples'].append(sample)
    data,records,features,member,members,bindings,row=saved;primary={r.object_id:r for r in records if r.is_primary}
    def rejected(label,changed_data=None,changed_records=None,changed_members=None):
        out=decode_path_pattern_cache_evidence(changed_data if changed_data is not None else data,
            changed_records if changed_records is not None else records,features,member,
            changed_members if changed_members is not None else members,bindings)
        assert not out['decoded'] and len(out['unresolved'])==1,(label,out)
        report['guards'].append(dict(case=label,reason=out['unresolved'][0]['reason']))
    changed=bytearray(data);struct.pack_into('<Q',changed,primary[377].body+2,363)
    rejected('Feature identity leaf changed to receiver',changed_data=bytes(changed))
    changed=bytearray(data);struct.pack_into('<Q',changed,primary[500].body+2,243)
    rejected('Association second leaf no longer repeats descriptor source anchor',changed_data=bytes(changed))
    changed=bytearray(data);struct.pack_into('<Q',changed,primary[281].body+92,363)
    rejected('Explicit source anchor owner changed',changed_data=bytes(changed))
    rejected('Conflicting-class duplicate source identity',changed_records=records+[replace(primary[243],class_guid=primary[363].class_guid)])
    blob_member=row['history_blob_member'];blob=members[blob_member];parsed=inspect_asm(blob)
    proof=next(p for p in row['source_feature_face_naming_proofs'] if p['native_body_object_id']==275)
    fpm=proof['proof']['faces'][0]['opaque_FPM_attributes'][0];a=parsed['records'][fpm['attribute_record_index']]
    changed=bytearray(blob);struct.pack_into('<q',changed,a['tokens'][4]['offset']+1,1)
    rejected('Opaque FPM reciprocal source FACE owner changed',changed_members={**members,blob_member:bytes(changed)})
    changed=bytearray(blob);struct.pack_into('<q',changed,a['tokens'][7]['offset']+1,a['tokens'][7]['value']+17)
    literal=decode_path_pattern_cache_evidence(data,records,features,member,{**members,blob_member:bytes(changed)},bindings)
    assert len(literal['decoded'])==1 and not literal['unresolved']
    oldrow=copy.deepcopy(row);newrow=copy.deepcopy(literal['decoded'][0]);oldproof=oldrow.pop('source_feature_face_naming_proofs');newproof=newrow.pop('source_feature_face_naming_proofs')
    assert oldrow==newrow and oldproof!=newproof
    report['opaque_FPM_literal_control']=dict(attribute_record_index=a['index'],original_literal=a['tokens'][7]['value'],changed_literal=a['tokens'][7]['value']+17,all_identity_groups_and_fits_exact=True,FPM_identity=None)
    point=parsed['records'][row['element_cache_groups'][0]['cache_bodies'][0]['measured_relative_rigid_fit']['vertex_correspondence'][-1]['target']['point_index']]
    changed=bytearray(blob);struct.pack_into('<d',changed,point['tokens'][3]['offset']+1,point['tokens'][3]['value'][0]+.125)
    rejected('Identity-fixed eighth vertex violates rigid fit',changed_members={**members,blob_member:bytes(changed)})
    report['summary']=dict(focused_archives=18,BODY_patterns=13,Feature_patterns=2,unrelated_controls=3,
        element_groups=groups,result_caches=caches,typed_vertex_pairs=vertices,maximum_residual_raw=max_residual,
        Feature_groups=feature_groups,Feature_vertex_pairs=feature_vertices,opaque_source_FPM_proofs=fpm_count,
        guards=len(report['guards']),opaque_FPM_literal_control=1,old_tool_settings_changes=0,
        API_grid_or_traversal_identity_claims=0,main_runs=0,live_calls=0)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--zstd-library');p.add_argument('--baseline',default='/private/tmp/fusion-path-pattern-cache-baseline.json');p.add_argument('--output',default='path-pattern-feature-cache-decoding.json');args=p.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(ROOT,zstd,Path(args.baseline));Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
