"""Fixed mixed native collection / empty BRep mapping integration.

Comparison implementation awaits frozen independent schemas; no live access.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from validate_base_mesh_definition_integration import FILES as BASE_MESH_FILES
from validate_history_cache_integration import differences

ROOT=Path(__file__).resolve().parent
BASELINE='0db5338'
FILES=BASE_MESH_FILES+(
    'meshconverts-4b42d39fb1d5/prismatic_closed.f3d',
    'meshconvertoperations-5af73924aa60/base_feature_closed.f3d',
    'meshconvertoperations-5af73924aa60/base_feature_open.f3d',
    'namedbodies-3c7c11fc2924/namedbodies.f3d',
    'advanced-627f7fe095f4/advanced.f3d',
    'assembly-acc48a9dc05d/assembly.f3d')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

REPORTS=('mixed-body-collection-decoding.json','mixed-empty-body-mapping-decoding.json','mixed-body-ownership-downstream-decoding.json')
COLLECTION_ERRORS=('Body collection repeated count disagrees','Body collection repeated membership disagrees')


def evidence():
    result={}
    for filename in REPORTS:
        document=json.loads((ROOT/filename).read_text())
        rows={r['archive']:r for r in document['samples']}
        assert len(rows)==len(document['samples']),('Duplicate evidence archive',filename)
        expected=set(FILES) if filename!=REPORTS[2] else {name for name in FILES if '/base_feature_' in name}
        assert set(rows)==expected,('Evidence manifest differs',filename,set(rows)^expected)
        result[filename]=rows
    return result


def remove_errors(rows,identities,reasons,key='object_id',kind=None):
    matched=[r for r in rows if r.get(key) in identities and r.get('reason') in reasons and (kind is None or r.get('kind')==kind)]
    assert {r[key] for r in matched}==set(identities),('Missing qualified prior errors',identities,matched)
    assert len(matched)==len(identities),'Repeated prior diagnostic'
    return [r for r in rows if r not in matched]


def qualify_hydration(old,stream,patches,golden,counts):
    """Bound independent full helper goldens to the precise native ownership patches."""
    assert patches and golden is not None
    for key in ('body_selections','body_blob_bindings','historical_body_components','body_placement'):
        assert stream[key]==golden['expected_'+key],('Independent downstream helper differs',key)
    selected=copy.deepcopy(old['body_selections']);anchor_count=0
    for anchor in selected['body_anchors']:
        identity=anchor['native_body_object_id']
        if identity in patches:
            properties=anchor['body_properties'];patch=patches[identity]
            for key in ('component_object_id','component_name','collection_object_id','ownership_evidence'):
                assert key not in properties
                properties[key]=patch[key]
            anchor_count+=1
    assert selected==stream['body_selections']
    bindings=copy.deepcopy(old['body_blob_bindings']);bound_ids=[]
    bodies={r['object_id']:r for r in stream['body_properties']['bodies']}
    for mapping in bindings['decoded']:
        for row in mapping['bindings']:
            identity=row['native_body_object_id']
            if identity in patches:
                bound_ids.append(identity)
                for key in ('name','name_status','component_object_id','component_name'):
                    assert key not in row
                    row[key]=bodies[identity][key]
    assert len(bound_ids)==len(set(bound_ids))==1
    assert bindings==stream['body_blob_bindings']
    historical=copy.deepcopy(old['historical_body_components'])
    historical['unresolved']=remove_errors(historical['unresolved'],bound_ids,('Result body collection repeated membership disagrees',),key='native_body_object_id')
    historical['already_owned_body_bindings_unchanged']+=len(bound_ids)
    assert historical==stream['historical_body_components']
    placement=stream['body_placement'];oldplace=old['body_placement']
    assert not oldplace['bodies'] and len(placement['bodies'])==1 and placement['scope']==oldplace['scope']
    assert placement['unresolved']==remove_errors(oldplace['unresolved'],bound_ids,('Typed ASM BODY identifier association or explicit component owner unresolved',),key='native_body_object_id')
    for row in placement['bodies']:
        identity=row['native_body_object_id'];assert identity in bound_ids
        binding=next(b for m in old['body_blob_bindings']['decoded'] for b in m['bindings'] if b['native_body_object_id']==identity)
        mapping=next(m for m in old['body_blob_bindings']['decoded'] if binding in m['bindings'])
        assert row['component_object_id']==patches[identity]['component_object_id']
        assert row['history_blob_member']==mapping['history_blob_member']
        assert row['asm_body_index']==binding['asm_body_index'] and row['asm_stored_entity_id']==binding['asm_stored_entity_id']
        assert row['association_status']==binding['association_status'] and row['lifecycle_status']==binding['lifecycle_status']
        counts['new_qualified_body_placements']+=1
    for key in ('body_selections','body_blob_bindings','historical_body_components','body_placement'):
        stream[key]=copy.deepcopy(old[key])
    counts['hydrated_body_anchors']+=anchor_count;counts['hydrated_body_bindings']+=len(bound_ids)


def compare(before,current,filename,proof):
    after=copy.deepcopy(current)
    a=proof[REPORTS[0]][filename]['expected_decoded'];c=proof[REPORTS[1]][filename]
    empty=c['expected_decoded'];downstream=proof[REPORTS[2]].get(filename)
    counts=dict(collection_summaries=0,mixed_collections=0,removed_collection_errors=0,BRep_ownership_updates=0,
        empty_mapping_summaries=0,empty_mapping_rows=0,removed_binding_errors=0,removed_mapping_variant_errors=0,
        hydrated_body_anchors=0,hydrated_body_bindings=0,new_qualified_body_placements=0)
    assert len(after['streams'])==len(before['streams'])==1
    old=before['streams'][0];stream=after['streams'][0]
    assert old['member']==stream['member']
    for key,summary,count_key in (('mixed_body_collections',a,'collection_summaries'),('mixed_empty_body_mappings',empty,'empty_mapping_summaries')):
        assert key not in old
        if summary['decoded'] or summary['unresolved']:
            assert stream.pop(key)==summary,(filename,'Independent summary differs',key)
            counts[count_key]+=1
        else:assert key not in stream
    assert old['body_blob_bindings']==c['expected_prior_body_bindings']
    assert old['body_mapping_variants']==c['expected_prior_mapping_variants']
    props=copy.deepcopy(old['body_properties']);ids=set();patches={}
    for row in a['decoded']:
        identity=row['object_id'];assert identity not in ids and identity not in {v['object_id'] for v in props['collections']}
        ids.add(identity);props['collections'].append(row['collection'])
        for patch in row['body_ownership_updates']:
            identity=patch['object_id'];assert identity not in patches
            assert identity in row['body_member_object_ids'] and identity not in row['mesh_member_object_ids']
            assert patch['collection_object_id']==row['object_id']
            assert patch['component_object_id']==row['component_object_id']
            assert set(patch)=={'object_id','collection_object_id','component_object_id','component_name','ownership_evidence'}
            patches[identity]=patch
            body=next(b for b in props['bodies'] if b['object_id']==identity)
            assert 'ownership_status' in body
            body.update(patch);body.pop('ownership_status')
    props['unresolved']=remove_errors(props['unresolved'],ids,COLLECTION_ERRORS,kind='BodyCollection')
    assert stream['body_properties']==props,(filename,'Collection/ownership merge differs')
    counts['mixed_collections']=counts['removed_collection_errors']=len(ids);counts['BRep_ownership_updates']=len(patches)
    if patches:qualify_hydration(old,stream,patches,downstream,counts)
    else:assert downstream is None
    # Restore only independently qualified compatible zero-map entries and exact old same-ID diagnostics.
    mapping_ids={r['mapping_record_object_id'] for r in empty['decoded']}
    assert len(mapping_ids)==len(empty['decoded'])
    for key,reason,count_key in (('body_mapping_variants','Body collection repeated native membership disagrees','removed_mapping_variant_errors'),('body_blob_bindings','Unsupported native body mapping count','removed_binding_errors')):
        expected=copy.deepcopy(old[key])
        expected['decoded'].extend(empty['decoded'])
        expected['unresolved']=remove_errors(expected['unresolved'],mapping_ids,(reason,))
        assert stream[key]==expected,(filename,'Qualified empty mapping merge differs',key)
        stream[key]=copy.deepcopy(old[key]);counts[count_key]=len(mapping_ids)
    counts['empty_mapping_rows']=len(mapping_ids)
    stream['body_properties']=copy.deepcopy(old['body_properties'])
    assert after==before,(filename,'Unqualified output change',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),**counts,
        whole_output_unchanged=before==current,whole_output_exact_after_qualified_restoration=True,
        prior_mesh_classification_timeline_warnings_placement_and_ASM_preserved_except_explicit_hydration=True,
        baseline_output_sha256=canonical(before),current_output_sha256=canonical(current),qualified_difference_paths=differences(before,current))


def read_cache(path,side):
    value=json.loads(Path(path).read_text())
    if isinstance(value,list):return value
    assert value['files']==list(FILES)
    if 'baseline_commit' in value:assert value['baseline_commit'].startswith(BASELINE)
    return value[side]


def validate(zstd,baseline_cache=None,current_cache=None,prior_current_cache=None,cache_driver_normalization_retry=False):
    if baseline_cache:before=read_cache(baseline_cache,'before')
    else:
        from validate_history_cache_integration import baseline_outputs
        before=baseline_outputs(FILES,zstd,revision=BASELINE)
    if current_cache:current=read_cache(current_cache,'after')
    else:
        from decode_basics import decode_basics
        current=json.loads(json.dumps([decode_basics(ROOT/name,zstd) for name in FILES]))
    assert len(before)==len(current)==len(FILES)==22
    assert [v['file'] for v in before]==[str(ROOT/name) for name in FILES]==[v['file'] for v in current]
    refresh=None
    if prior_current_cache:
        prior=read_cache(prior_current_cache,'after')
        assert prior==current,'Identity guard unexpectedly changed valid captured outputs'
        refresh=dict(reason='Second current pass justified by added unique primary collection identity guard after first cache',prior_current_cache_path=str(Path(prior_current_cache).resolve()),prior_current_cache_sha256=sha(prior_current_cache),saved_files=22,valid_full_outputs_exact=True,baseline_regenerated=False)
        if cache_driver_normalization_retry:
            refresh['failed_driver_attempt']=dict(current_main_calls=22,baseline_main_calls=0,reason='Raw Python output compared to JSON-normalized prior cache before serialization; artifact not written',decoder_difference_established=False)
            refresh['total_current_main_calls_during_stage']=66
            refresh['total_baseline_main_calls_during_stage']=22
    elif cache_driver_normalization_retry:
        raise AssertionError('Driver retry note requires pre-guard current cache evidence')
    proof=evidence();rows=[compare(b,a,name,proof) for b,a,name in zip(before,current,FILES)]
    keys=('collection_summaries','mixed_collections','removed_collection_errors','BRep_ownership_updates','empty_mapping_summaries','empty_mapping_rows','removed_binding_errors','removed_mapping_variant_errors','hydrated_body_anchors','hydrated_body_bindings','new_qualified_body_placements')
    totals={k:sum(row[k] for row in rows) for k in keys}
    totals.update(saved_files=22,whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),unexpected_changes=0,baseline_main_calls=0 if baseline_cache else 22,current_main_calls=0 if current_cache else 22,live_API_calls=0)
    caches={}
    if baseline_cache:caches['baseline']=dict(path=str(Path(baseline_cache).resolve()),sha256=sha(baseline_cache))
    if current_cache:caches['current']=dict(path=str(Path(current_cache).resolve()),sha256=sha(current_cache))
    sources=('validate_mixed_body_collection_integration.py','decode_mixed_body_collections.py','decode_mixed_empty_body_mappings.py','decode_basics.py')
    return dict(scope='Fixed 22 saved archives against 0db5338; typed mixed collection and empty BRep mapping refinements, with independently qualified BRep-only downstream ownership hydration',baseline_commit=BASELINE,files=list(FILES),summary=totals,samples=rows,cache_provenance=caches,source_change_revalidation=refresh,evidence_sha256={p:sha(ROOT/p) for p in REPORTS},source_sha256={p:sha(ROOT/p) for p in sources},limitations=['Mesh forward collection membership is not Mesh ownership, visibility, API handle identity or lifecycle','Only typed native BODY subset ownership is hydrated; two recovered placements retain same-blob identifier and unresolved lifecycle qualifications','Full independent focused summaries qualify changes; cached main outputs never generate their own expected goldens','All old native Mesh, ASM geometry, classifications, timeline, and unrelated diagnostics remain exact','No live Fusion/UI/API, regeneration, writer support or corpus-wide main run','Cache flags avoid repeated main decoding; without them only pinned fixed 22 files are regenerated'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache');p.add_argument('--current-cache');p.add_argument('--prior-current-cache');p.add_argument('--cache-driver-normalization-retry',action='store_true');p.add_argument('--zstd-library');p.add_argument('--output',default='mixed-body-collection-integration.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z,a.baseline_cache,a.current_cache,a.prior_current_cache,a.cache_driver_normalization_retry);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
