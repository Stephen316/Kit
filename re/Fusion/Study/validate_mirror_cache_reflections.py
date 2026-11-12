"""Fixed twelve Mirror cache/plane fixtures; identities precede reflection checks."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_mirror_cache_reflections import decode_mirror_cache_reflections, SCOPE
from decode_sketch import decode_sketches
from decode_placement import decode_placement
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
POSITIVES=tuple('mirrorfeatures-1ffa1b15c612/'+s+'.f3d' for s in (
    'body_brep_face_plane','feature_optimized','feature_identical','feature_adjust'))+(
    'tools-fda3948848f4/Mirror.f3d','bodyselections-62e42366c722/mirror_two_bodies_plane.f3d',
    'remainingbodyinputs-7b3357274e85/mirror_two_features.f3d')
CONTROLS=('remainingbodyinputs-7b3357274e85/mirror_boss_faces.f3d',
    'datummirrorsupport-3a854f334428/offset_selected_support.f3d',
    'surfacetools-856ca50cf4c7/offset_positive.f3d','surfacebounds-ac801bb00fae/untrim_all.f3d',
    'pathpatterns-de9857f6a1bc/spacing.f3d')
FILES=POSITIVES+CONTROLS


def validate(root,zstd,baseline_path):
    baseline=json.loads(baseline_path.read_text());assert baseline['baseline_commit']=='88d8356' and baseline['files']==list(FILES)
    before={Path(o['file']).relative_to(root).as_posix():o['streams'][0] for o in baseline['before']}
    report=dict(interface='decode_mirror_cache_reflections(data,records,features,member,members,body_blob_bindings)->decoded/unresolved/scope',
        integration=dict(stream='mirror_cache_reflections',feature_attachment='mirror_cache_reflection',feature_id='feature_object_id',expected_summary='samples[].expected_summary'),
        scope='Seven actual noncombine native BODY/Extrude Feature Mirrors. Complete owned source/result BODY and FACE-prefix incidence identities precede a Householder computed only from the selected native plane. No matrix fitting, coordinate identity selection, API element/current/history placement or serialized transform claim.',
        baseline=dict(commit='88d8356',sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest()),
        samples=[],guards=[],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'decode_mirror_cache_reflections.py','validate_mirror_cache_reflections.py','decode_mirror_cache_sources.py',
            'decode_mirror_face_planes.py','decode_mirror_modes.py','decode_body_selections.py','decode_body_asm_identifiers.py',
            'decode_circular_feature_caches.py','decode_circular_placement_evidence.py','decode_brep.py')})
    copies=vertices=sourcefpm=resultfpm=0;maximum=0.;loaded={};saved=None;feature_saved=None
    for archive in FILES:
        data,records,features,member,members=load(root,archive,zstd)
        decode_sketches(data,records,features);decode_placement(data,records,features)
        bindings=before[archive]['body_blob_bindings'];original=copy.deepcopy((features,bindings))
        out=decode_mirror_cache_reflections(data,records,features,member,members,bindings)
        assert (features,bindings)==original
        sample=dict(archive=archive,archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),expected_summary=out,caller_metadata_unchanged=True)
        if archive in CONTROLS:
            assert out==dict(decoded=[],unresolved=[],scope=SCOPE),(archive,out)
            sample['recognized_nontarget_or_unrelated_control']=True
        else:
            assert len(out['decoded'])==1 and not out['unresolved'],(archive,out)
            row=out['decoded'][0];fid=row['feature_object_id'];native=row['native_source_provenance'];plane=native['selected_plane']
            assert native['feature_object_id']==fid and native['source_native_body_object_ids']==row['source_native_body_object_ids']
            assert row['complete_source_result_prefix_bijection'] and row['computed_determinant']==-1.
            assert all(row[k] is None for k in ('API_element_identity','persistent_topology_identity','current_placement','qualified_historical_state'))
            matrix=row['computed_householder_matrix'];assert all(math.isfinite(v) for v in matrix)
            assert len(row['cache_body_copies'])==len(row['source_native_body_object_ids'])==len(native['result_anchors'])
            assert {c['result_body_anchor']['object_id'] for c in row['cache_body_copies']}==set(row['owned_result_anchor_object_ids'])
            prefixes=set();targets=set();proofs={p['native_body_object_id']:p for p in row['complete_body_naming_proofs']}
            for c in row['cache_body_copies']:
                copies+=1;vertices+=c['matched_vertex_count'];maximum=max(maximum,c['maximum_vertex_residual_raw'])
                assert c['matched_vertex_count']==8 and c['maximum_vertex_residual_raw']<1e-8
                source=c['source_native_body_object_id'];target=c['result_native_body_object_id'];assert target not in targets;targets.add(target)
                prefix=c['stored_source_naming_prefix'];terms=c['stored_result_face_naming_components']
                assert len(prefix)==1 and len(terms)==3 and terms[0]==prefix[0] and terms[2]==row['stored_instance_key_pair'][1]
                assert terms[1]==row['uninterpreted_common_feature_naming_component'];prefixes.add(prefix[0])
                assert c['result_body_anchor']['source_owner_object_id']==fid
                assert c['source_body_binding']==proofs[source]['binding'] and c['result_body_binding']==proofs[target]['binding']
                assert len(c['vertex_correspondence'])==8
                for v in c['vertex_correspondence']:
                    assert len(v['incident_face_name_keys'])==3
                    sourcepoint=v['source']['raw_position'];expected=[sum(matrix[4*i+j]*sourcepoint[j] for j in range(3))+matrix[4*i+3] for i in range(3)]
                    assert expected==v['computed_reflected_source_position']
                    assert all(abs(a-b)<1e-8 for a,b in zip(expected,v['target']['raw_position']))
            assert len(prefixes)==len(row['source_native_body_object_ids'])
            for nid,p in proofs.items():
                faces=p['proof']['faces'];assert len(faces)==6 and p['proof']['FPM_literal_identity'] is None
                fpms=[a for f in faces for a in f['opaque_FPM_attributes']]
                if nid in row['source_native_body_object_ids']:sourcefpm+=len(fpms)
                else:resultfpm+=len(fpms)
            oldfeature=next(f for f in before[archive]['features'] if f['object_id']==fid)
            sample['prior_tool_settings']=oldfeature['tool_settings']
            if archive==POSITIVES[0]:
                assert plane['kind']=='NamedBRepFaceCache'
                assert matrix==[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,-1.,6.,0.,0.,0.,1.]
                assert row['source_native_body_object_ids']==[275] and [c['result_native_body_object_id'] for c in row['cache_body_copies']]==[415]
                saved=(data,records,features,member,members,bindings,row)
            if archive.endswith('/mirror_two_features.f3d'):
                assert row['source_native_body_object_ids']==[354,275]
                assert [c['source_native_body_object_id'] for c in row['cache_body_copies']]==[354,275]
                assert [c['result_native_body_object_id'] for c in row['cache_body_copies']]!=[a['native_body_object_id'] for a in native['result_anchors']]
                sample['reversed_source_result_order_control']='Source selectors354/275 and literal result order are not paired by position; unique complete prefixes select targets'
            if native['input_kind']=='Feature' and feature_saved is None:feature_saved=(data,records,features,member,members,bindings,row)
        loaded[archive]=(data,records,features,member,members,bindings)
        report['samples'].append(sample)
    data,records,features,member,members,bindings,row=saved;primary={r.object_id:r for r in records if r.is_primary}
    def rejected(label,context,changed_data=None,changed_records=None,changed_members=None):
        d,rs,fs,m,ms,bs=context
        out=decode_mirror_cache_reflections(changed_data if changed_data is not None else d,
            changed_records if changed_records is not None else rs,fs,m,
            changed_members if changed_members is not None else ms,bs)
        assert not out['decoded'] and len(out['unresolved'])==1,(label,out)
        report['guards'].append(dict(case=label,reason=out['unresolved'][0]['reason']))
    context=loaded[POSITIVES[0]]
    anchor=row['cache_body_copies'][0]['result_body_anchor']['object_id'];changed=bytearray(data)
    struct.pack_into('<Q',changed,primary[anchor].body+92,243)
    rejected('Owned result anchor receiver backlink changed',context,changed_data=bytes(changed))
    source=next(r for r in records if r.is_primary and r.object_id==243)
    rejected('Conflicting-class duplicate source owner',context,changed_records=records+[replace(source,class_guid=primary[row['feature_object_id']].class_guid)])
    blob_member=row['history_blob_member'];blob=members[blob_member];parsed=inspect_asm(blob)
    target=row['cache_body_copies'][0]['result_native_body_object_id'];proof=next(p for p in row['complete_body_naming_proofs'] if p['native_body_object_id']==target)
    tag=proof['proof']['faces'][0]['generic_tags'][0];attribute=parsed['records'][tag['attribute_record_index']]
    changed=bytearray(blob);token=attribute['tokens'][12];changed[token['offset']+2]=ord('9')
    rejected('Inherited result FACE name changed without coordinate fallback',context,changed_members={**members,blob_member:bytes(changed)})
    point=parsed['records'][row['cache_body_copies'][0]['vertex_correspondence'][-1]['target']['point_index']]
    changed=bytearray(blob);struct.pack_into('<d',changed,point['tokens'][3]['offset']+1,point['tokens'][3]['value'][0]+.125)
    rejected('Eighth fixed target point disagrees with prescribed reflection',context,changed_members={**members,blob_member:bytes(changed)})
    changed=bytearray(blob);struct.pack_into('<d',changed,point['tokens'][3]['offset']+1,float('nan'))
    rejected('Nonfinite fixed target point cannot pass residual comparison',context,changed_members={**members,blob_member:bytes(changed)})
    d,rs,fs,m,ms,bs,feature_row=feature_saved;bm=feature_row['history_blob_member'];raw=ms[bm];parsed=inspect_asm(raw)
    proof=next(p for p in feature_row['complete_body_naming_proofs'] if p['native_body_object_id'] in feature_row['source_native_body_object_ids'])
    fpm=next(a for f in proof['proof']['faces'] for a in f['opaque_FPM_attributes']);a=parsed['records'][fpm['attribute_record_index']]
    changed=bytearray(raw);struct.pack_into('<q',changed,a['tokens'][7]['offset']+1,a['tokens'][7]['value']+17)
    literal=decode_mirror_cache_reflections(d,rs,fs,m,{**ms,bm:bytes(changed)},bs)
    assert len(literal['decoded'])==1 and not literal['unresolved']
    oldrow=copy.deepcopy(feature_row);newrow=copy.deepcopy(literal['decoded'][0]);oldproof=oldrow.pop('complete_body_naming_proofs');newproof=newrow.pop('complete_body_naming_proofs')
    assert oldrow==newrow and oldproof!=newproof
    report['opaque_FPM_literal_control']=dict(attribute_record_index=a['index'],original_literal=a['tokens'][7]['value'],changed_literal=a['tokens'][7]['value']+17,
        all_native_identity_pairs_and_computed_reflections_exact=True,FPM_identity=None)
    report['summary']=dict(focused_archives=12,Mirror_owners=7,BODY_copies=copies,typed_vertex_pairs=vertices,
        maximum_reflection_residual_raw=maximum,opaque_source_FPM_proofs=sourcefpm,opaque_result_FPM_proofs=resultfpm,
        complete_empty_controls=5,guards=len(report['guards']),opaque_FPM_literal_control=1,
        coordinate_identity_choices=0,fitted_matrices=0,serialized_reflection_matrices_claimed=0,
        old_tool_or_placement_changes=0,main_runs=0,live_calls=0)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--zstd-library');p.add_argument('--baseline',default='/private/tmp/fusion-mirror-cache-reflections-baseline.json');p.add_argument('--output',default='mirror-cache-reflection-decoding.json');args=p.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(ROOT,zstd,Path(args.baseline));Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
