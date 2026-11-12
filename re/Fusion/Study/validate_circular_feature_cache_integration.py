"""Fixed ten-file circular feature-input cache refinement against 99d96e7.

Only three existing cache-evidence rejection rows may become independently
qualified feature-input cache proofs; old body/geometry/getter warnings stay.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from validate_history_cache_integration import differences
ROOT=Path(__file__).resolve().parent
BASELINE='99d96e7'
FILES=tuple('circularmodes-45f859c1f1b6/'+name+'.f3d' for name in (
 'feature_optimized','feature_identical','feature_adjust','body_full','body_negative','body_suppressed','body_symmetric','multiple_customaxis'))+(
 'surfacetools-856ca50cf4c7/offset_positive.f3d',
 'surfacebounds-ac801bb00fae/untrim_all.f3d')
TARGETS=set(FILES[:3])
SUMMARY='circular_placement_evidence'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

EVIDENCE='circular-feature-cache-decoding.json'
HOOK_EVIDENCE='circular-cache-hook-decoding.json'
OLD_REJECTION='Circular naming/cache evidence currently supports explicit body inputs only'
GETTER_WARNING='Circular API getter matrix sets disagree with ordinary equally spaced rotation sets in captured full/partial/symmetric fixtures; transform semantics unresolved'


def evidence():
    rows={}
    for row in json.loads((ROOT/EVIDENCE).read_text())['samples']:
        if row['archive'] not in FILES:continue
        assert row['archive'] not in rows
        rows[row['archive']]=row['expected_summary']
    assert set(rows)==set(FILES)
    hook=json.loads((ROOT/HOOK_EVIDENCE).read_text())
    defaults={r['archive']:r for r in hook['default_controls']}
    frozen={r['archive']:r for r in hook['frozen_pre_hook_defaults']['samples']}
    assert set(defaults)==set(frozen)==set(FILES[:8])
    assert hook['frozen_pre_hook_defaults']['baseline'].startswith(BASELINE)
    for name,row in defaults.items():
        assert row['inactive_callbacks_exact'] is True
        assert row['expected_default']==frozen[name]['expected_default']
        assert row['member']==frozen[name]['member']
    return dict(summaries=rows,defaults=defaults)


def qualify_feature(row,old,feature):
    settings=feature['tool_settings'];identity=feature['object_id']
    assert row['feature_object_id']==identity and row['pattern_entity_type']=='Features' and row['pattern_entity_type_code']==1
    assert row['source_feature_object_ids']==settings['source_feature_object_ids'] and len(row['source_feature_object_ids'])==1
    provenance=row['source_feature_input_provenance']
    assert provenance['pattern_entity_type']=='Features'
    assert provenance['input_proxy_object_id']==settings['input_selection_record_object_id']
    assert provenance['input_collection_object_id']==settings['input_entity_collection_object_id']
    assert len(provenance['sources'])==1
    source=provenance['sources'][0]
    assert source['input_descriptor']==settings['input_descriptors'][0]
    source_id=row['source_feature_object_ids'][0]
    assert next(f for f in old['features'] if f['object_id']==source_id)['kind']=='Extrude'
    source_anchor=source['source_body_anchor']
    assert source_anchor['source_owner_object_id']==source_id
    source_body=source_anchor['native_body_object_id']
    assert row['source_native_body_object_ids']==[source_body]
    anchors={a['object_id']:a for a in old['body_selections']['body_anchors']}
    assert anchors[source_anchor['object_id']]['native_body_object_id']==source_body
    assert anchors[source_anchor['object_id']]['source_owner_object_id']==source_id
    bindings={b['native_body_object_id']:(m,b) for m in old['body_blob_bindings']['decoded'] for b in m['bindings']}
    pairs=dict(settings['stored_instance_ordinal_pairs']);element_ids=dict(zip(settings['stored_element_ordinals'],settings['element_record_object_ids']))
    groups=row['element_cache_groups'];assert len(groups)==3 and not row['suppressed_elements_without_generated_cache_group']
    assert {g['stored_ordinal'] for g in groups}==set(pairs)
    results=set();vertex_pairs=0
    for group in groups:
        assert group['stored_naming_key']==pairs[group['stored_ordinal']]
        assert group['element_object_id']==element_ids[group['stored_ordinal']]
        assert len(group['cache_bodies'])==1
        body=group['cache_bodies'][0];anchor_id=body['result_anchor_object_id'];result_body=body['result_native_body_object_id']
        assert anchor_id not in results;results.add(anchor_id)
        assert anchor_id in settings['result_record_object_ids']
        assert anchors[anchor_id]['source_owner_object_id']==identity and anchors[anchor_id]['native_body_object_id']==result_body
        assert body['source_native_body_object_id']==source_body
        mapping,binding=bindings[result_body]
        assert row['history_blob_member']==mapping['history_blob_member']==bindings[source_body][0]['history_blob_member']
        assert row['mapping_record_object_id']==mapping['mapping_record_object_id']
        assert body['asm_body_index']==binding['asm_body_index'] and body['asm_body_stored_id']==binding['asm_stored_entity_id']
        components=body['stored_face_naming_components'];assert len(components)==3 and components[2]==group['stored_naming_key']
        assert components[1]==row['uninterpreted_common_feature_naming_component']
        vertex_pairs+=body['measured_relative_rigid_fit']['matched_vertex_count']
    assert results==set(settings['result_record_object_ids']) and vertex_pairs==24
    naming=row['source_feature_face_naming_proofs'];assert len(naming)==4
    assert {n['native_body_object_id'] for n in naming}=={source_body}|{anchors[a]['native_body_object_id'] for a in results}
    fpm=0
    for named in naming:
        _,binding=bindings[named['native_body_object_id']]
        assert named['asm_body_index']==binding['asm_body_index']
        assert named['binding']['native_body_object_id']==binding['native_body_object_id']
        assert named['binding']['asm_body_index']==binding['asm_body_index']
        assert named['binding']['asm_stored_entity_id']==binding['asm_stored_entity_id']
        proof=named['proof'];assert proof['FPM_literal_identity'] is None and len(proof['faces'])==6
        fpm+=sum(len(face['opaque_FPM_attributes']) for face in proof['faces'])
    assert fpm==6
    return len(groups),vertex_pairs,fpm


def compare(before,current,filename,proof):
    after=copy.deepcopy(current);expected=proof['summaries'][filename]
    assert len(before['streams'])==len(after['streams'])==1
    old=before['streams'][0];stream=after['streams'][0];assert old['member']==stream['member']
    default_check=0
    if filename in proof['defaults']:
        default=proof['defaults'][filename]
        assert old['member']==default['member'] and old[SUMMARY]==default['expected_default'],(filename,'Independent old default dictionary differs from pinned main baseline')
        default_check=1
    if expected['decoded'] or expected['unresolved']:assert stream[SUMMARY]==expected,(filename,'Independent complete facade summary differs')
    else:assert SUMMARY not in stream
    assert stream['pattern_placements']==old['pattern_placements'],(filename,'Existing placement/getter warning changed')
    getter_warnings=sum(r['reason']==GETTER_WARNING for r in old['pattern_placements']['unresolved'])
    refined=attached=groups=vertices=fpm=0
    if filename in TARGETS:
        old_summary=old[SUMMARY];summary=stream[SUMMARY]
        assert not old_summary['decoded'] and len(old_summary['unresolved'])==1
        failure=old_summary['unresolved'][0];assert failure['reason']==OLD_REJECTION
        assert len(summary['decoded'])==1 and not summary['unresolved']
        row=summary['decoded'][0];identity=row['feature_object_id'];assert identity==failure['feature_object_id']
        old_features={f['object_id']:f for f in old['features']};features={f['object_id']:f for f in stream['features']}
        assert old_features[identity]['kind']==features[identity]['kind']=='CircularPattern'
        assert SUMMARY not in old_features[identity] and features[identity].pop(SUMMARY)==row
        groups,vertices,fpm=qualify_feature(row,old,old_features[identity])
        assert set(summary)==set(old_summary)=={'decoded','unresolved','scope'}
        stream[SUMMARY]=copy.deepcopy(old_summary);refined=attached=1
    assert after==before,(filename,'Unqualified previous-output change',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),qualified_feature_cache_refinements=refined,
        receiving_feature_annotations=attached,independent_pre_hook_default_dictionary_checks=default_check,qualified_element_cache_groups=groups,typed_vertex_pairs=vertices,
        retained_opaque_FPM_proofs=fpm,retained_getter_disagreement_warnings=getter_warnings,
        whole_output_unchanged=before==current,whole_output_exact_after_restoring_only_independent_feature_cache_summary_and_attachment=True,
        all_tool_settings_placements_API_getter_warnings_global_geometry_and_ASM_exact=True,
        baseline_output_sha256=digest(before),current_output_sha256=digest(current),qualified_difference_paths=differences(before,current))


def read_cache(path,side):
    value=json.loads(Path(path).read_text())
    if isinstance(value,list):return value
    assert value['files']==list(FILES)
    if 'baseline_commit' in value:assert value['baseline_commit'].startswith(BASELINE)
    return value[side]


def validate(zstd,baseline_cache=None,current_cache=None):
    if baseline_cache:before=read_cache(baseline_cache,'before')
    else:
        from validate_history_cache_integration import baseline_outputs
        before=baseline_outputs(FILES,zstd,revision=BASELINE)
    if current_cache:current=read_cache(current_cache,'after')
    else:
        from decode_basics import decode_basics
        current=json.loads(json.dumps([decode_basics(ROOT/name,zstd) for name in FILES]))
    assert len(before)==len(current)==len(FILES)==10
    assert [r['file'] for r in before]==[str(ROOT/name) for name in FILES]==[r['file'] for r in current]
    proof=evidence();rows=[compare(b,a,name,proof) for b,a,name in zip(before,current,FILES)]
    keys=('qualified_feature_cache_refinements','receiving_feature_annotations','independent_pre_hook_default_dictionary_checks','qualified_element_cache_groups','typed_vertex_pairs','retained_opaque_FPM_proofs','retained_getter_disagreement_warnings')
    summary={k:sum(r[k] for r in rows) for k in keys}
    summary.update(saved_files=10,whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),unexpected_changes=0,baseline_main_calls=0 if baseline_cache else 10,current_main_calls=0 if current_cache else 10,live_API_calls=0)
    caches={}
    if baseline_cache:caches['baseline']=dict(path=str(Path(baseline_cache).resolve()),sha256=sha(baseline_cache))
    if current_cache:caches['current']=dict(path=str(Path(current_cache).resolve()),sha256=sha(current_cache))
    sources=('validate_circular_feature_cache_integration.py','decode_circular_feature_caches.py','decode_circular_placement_evidence.py','decode_basics.py')
    return dict(scope='Fixed ten saved archives against 99d96e7; only three feature-input circular cache-evidence refinements and separate receiving-feature annotations',baseline_commit=BASELINE,files=list(FILES),summary=summary,samples=rows,cache_provenance=caches,evidence_sha256={name:sha(ROOT/name) for name in (EVIDENCE,HOOK_EVIDENCE)},source_sha256={p:sha(ROOT/p) for p in sources},limitations=['Relative rigid fits follow exact typed native selector/anchor/BODY/naming/vertex joins, not coordinates or result-list order','Computed cache-relative matrices are not serialized element transforms, regenerated geometry or API getter corrections','FPM literals remain opaque metadata and supply no source identity','All prior tool settings, placement/getter diagnostics, current geometry, lifecycle labels and global ASM dictionaries remain exact','Independent focused full dictionaries qualify every refinement; current main does not generate its own expected golden','No live calls or corpus-wide main; cache flags avoid repeated fixed-manifest decoding'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache');p.add_argument('--current-cache');p.add_argument('--zstd-library');p.add_argument('--output',default='circular-feature-cache-integration.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z,a.baseline_cache,a.current_cache);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
