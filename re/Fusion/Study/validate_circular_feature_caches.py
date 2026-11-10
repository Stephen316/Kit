"""Fixed ten saved controls for Feature-input circular cache correspondence."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_circular_feature_caches import decode_circular_cache_evidence
from decode_circular_placement_evidence import decode_circular_placement_evidence
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
FOLDER = 'circularmodes-45f859c1f1b6'
FILES = tuple(FOLDER+'/'+s+'.f3d' for s in ('feature_optimized','feature_identical','feature_adjust',
    'body_full','body_negative','body_suppressed','body_symmetric','multiple_customaxis'))+(
    'surfacetools-856ca50cf4c7/offset_positive.f3d','surfacebounds-ac801bb00fae/untrim_all.f3d')


def validate(root,zstd,baseline_path):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit'] == '99d96e7' and baseline['files'] == list(FILES)
    before = {Path(o['file']).relative_to(root).as_posix():o['streams'][0] for o in baseline['before']}
    truth = json.loads((root/FOLDER/'ground_truth.json').read_text())
    report = dict(scope='Three actual singleton Extrude Feature-input circular patterns; typed selector and complete canonical generic/FPM FACE chains precede named-vertex rigid cache fits. No serialized per-element transform, API getter correction or persistent/current/history identity claim.',
        interface='decode_circular_cache_evidence(data,records,features,member,members,body_blob_bindings)->decoded/unresolved/scope',
        integration=dict(stream='circular_placement_evidence',feature_attachment='circular_placement_evidence',feature_id='feature_object_id',
            expected_summary='samples[].expected_summary',body_control_dictionaries_unchanged=True),
        baseline=dict(commit='99d96e7',sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest()),
        samples=[],guards=[],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'decode_circular_feature_caches.py','validate_circular_feature_caches.py','decode_circular_placement_evidence.py',
            'decode_circular_patterns.py','decode_body_selections.py','decode_body_asm_identifiers.py','decode_asm_recipe_tags.py','decode_brep.py')})
    groups=caches=vertices=FPM=0;maximum=0.;saved=None
    for archive in FILES:
        data,records,features,member,members=load(root,archive,zstd)
        stream=before[archive];bindings=stream['body_blob_bindings']
        original=copy.deepcopy((features,bindings))
        output=decode_circular_cache_evidence(data,records,features,member,members,bindings)
        assert (features,bindings)==original
        sample=dict(archive=archive,archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),expected_summary=output)
        old=stream.get('circular_placement_evidence')
        if old is None:
            old=decode_circular_placement_evidence(data,records,features,member,members,bindings)
            assert not old['decoded'] and not old['unresolved']
        if '/feature_' in archive:
            assert len(output['decoded'])==1 and not output['unresolved'],output
            row=output['decoded'][0]
            assert row['pattern_entity_type']=='Features' and row['pattern_entity_type_code']==1
            assert row['feature_object_id']==282 and row['source_feature_object_ids']==[243]
            assert row['source_native_body_object_ids']==[275]
            source=row['source_feature_input_provenance'];assert source['pattern_entity_type']=='Features'
            p=source['sources'][0];assert p['input_descriptor']['descriptor_object_id']==293
            assert p['input_descriptor']['terminal_object_id']==296 and p['source_body_anchor']['object_id']==281
            assert p['source_body_anchor']['source_owner_object_id']==243 and p['source_body_anchor']['native_body_object_id']==275
            assert not old['decoded'] and old['unresolved']==[dict(feature_object_id=282,reason='Circular naming/cache evidence currently supports explicit body inputs only')]
            api=next(s for s in truth['samples'] if s['file']==Path(archive).name)
            assert api['settings']['pattern_entity_type']==1 and api['settings']['input_count']==1 and api['settings']['result_body_count']==4
            sample['actual_API_settings']=api['settings'];sample['actual_API_pattern_elements']=api['pattern_elements']
            assert len(row['element_cache_groups'])==3
            for group in row['element_cache_groups']:
                groups+=1;assert len(group['cache_bodies'])==1
                for body in group['cache_bodies']:
                    caches+=1;fit=body['measured_relative_rigid_fit'];vertices+=fit['matched_vertex_count']
                    assert fit['matched_vertex_count']==8 and fit['maximum_vertex_residual_raw']<1e-8
                    maximum=max(maximum,fit['maximum_vertex_residual_raw'])
                    assert all(len(pair['incident_face_name_keys'])==3 for pair in fit['vertex_correspondence'])
            proofs=row['source_feature_face_naming_proofs'];assert len(proofs)==4
            source_binding=next(p for p in proofs if p['native_body_object_id']==275)['binding']
            assert source_binding['native_body_object_id']==275 and source_binding['asm_body_index']==1 and source_binding['asm_stored_entity_id']==6
            for proof in proofs:
                faces=proof['proof']['faces'];assert len(faces)==6 and proof['proof']['FPM_literal_identity'] is None
                for face in faces:
                    assert face['generic_tags']
                    FPM+=len(face['opaque_FPM_attributes'])
                    assert all(a['definition_name']=='FPM_tracked_attrib_def' and a['stored_tracking_literal']>0 for a in face['opaque_FPM_attributes'])
            assert 'pattern_placements' in stream and any(r['feature_object_id']==282 for r in stream['pattern_placements']['unresolved'])
            sample['prior_API_getter_placement_warning_preserved']=True
            if saved is None:saved=(data,records,features,member,members,bindings,row)
        else:
            assert output==old,(archive,'prior complete cache summary differs')
            sample['prior_complete_summary_exact']=True
        report['samples'].append(sample)
    data,records,features,member,members,bindings,row=saved
    primary={r.object_id:r for r in records if r.is_primary}
    def rejected(label,changed_data=None,changed_records=None,changed_members=None,changed_bindings=None):
        out=decode_circular_cache_evidence(changed_data if changed_data is not None else data,
            changed_records if changed_records is not None else records,features,member,
            changed_members if changed_members is not None else members,changed_bindings if changed_bindings is not None else bindings)
        assert not out['decoded'] and len(out['unresolved'])==1,(label,out)
        report['guards'].append(dict(case=label,reason=out['unresolved'][0]['reason']))
    changed=bytearray(data);struct.pack_into('<Q',changed,primary[296].body+2,282)
    rejected('Feature leaf source changed to receiving Circular feature',changed_data=bytes(changed))
    changed=bytearray(data);struct.pack_into('<Q',changed,primary[281].body+92,282)
    rejected('Source anchor owner changed',changed_data=bytes(changed))
    rejected('Conflicting-class duplicate source primary',changed_records=records+[replace(primary[243],class_guid=primary[282].class_guid)])
    blob_member=row['history_blob_member'];blob=members[blob_member];parsed=inspect_asm(blob)
    proofs=row['source_feature_face_naming_proofs']
    target=next(p for p in proofs if p['native_body_object_id']!=275)
    face=target['proof']['faces'][0];attr=parsed['records'][face['generic_tags'][0]['attribute_record_index']]
    changed=bytearray(blob);struct.pack_into('<q',changed,attr['tokens'][4]['offset']+1,1)
    rejected('Generic FACE reciprocal owner changed',changed_members={**members,blob_member:bytes(changed)})
    fpm=next(a for p in proofs for f in p['proof']['faces'] for a in f['opaque_FPM_attributes'])
    a=parsed['records'][fpm['attribute_record_index']];changed=bytearray(blob)
    struct.pack_into('<q',changed,a['tokens'][6]['offset']+1,2)
    rejected('FPM schema changed',changed_members={**members,blob_member:bytes(changed)})
    changed=bytearray(blob);struct.pack_into('<q',changed,a['tokens'][4]['offset']+1,1)
    rejected('FPM reciprocal FACE owner changed',changed_members={**members,blob_member:bytes(changed)})
    # A positive literal-only contrast proves FPM numbers are retained metadata,
    # rather than feature IDs or the basis of the correspondence join.
    changed=bytearray(blob);struct.pack_into('<q',changed,a['tokens'][7]['offset']+1,a['tokens'][7]['value']+17)
    opaque=decode_circular_cache_evidence(data,records,features,member,{**members,blob_member:bytes(changed)},bindings)
    assert len(opaque['decoded'])==1 and not opaque['unresolved']
    neutral_before=copy.deepcopy(row);neutral_after=copy.deepcopy(opaque['decoded'][0])
    before_proofs=neutral_before.pop('source_feature_face_naming_proofs');after_proofs=neutral_after.pop('source_feature_face_naming_proofs')
    assert neutral_before==neutral_after and before_proofs!=after_proofs
    report['opaque_FPM_literal_control']=dict(changed_attribute_record_index=a['index'],
        original_literal=a['tokens'][7]['value'],changed_literal=a['tokens'][7]['value']+17,
        all_identity_groups_and_fits_exact=True,literal_identity_semantics=None)
    targetbody=row['element_cache_groups'][0]['cache_bodies'][0]
    point=parsed['records'][targetbody['measured_relative_rigid_fit']['vertex_correspondence'][-1]['target']['point_index']]
    changed=bytearray(blob);struct.pack_into('<d',changed,point['tokens'][3]['offset']+1,point['tokens'][3]['value'][0]+.125)
    rejected('Identity-fixed eighth vertex contradicts rigid fit',changed_members={**members,blob_member:bytes(changed)})
    report['summary']=dict(focused_archives=len(FILES),feature_patterns=3,element_groups=groups,result_caches=caches,
        typed_vertex_pairs=vertices,maximum_residual_raw=maximum,opaque_FPM_attribute_proofs=FPM,
        body_controls_complete_exact=5,unrelated_controls_complete_exact=2,guards=len(report['guards']),opaque_FPM_literal_control=1,
        serialized_element_matrices_claimed=0,API_getter_warnings_cleared=0,main_runs=0,live_calls=0)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--zstd-library');p.add_argument('--baseline',default='/private/tmp/fusion-circular-feature-cache-baseline.json');p.add_argument('--output',default='circular-feature-cache-decoding.json');args=p.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(ROOT,zstd,Path(args.baseline));Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
