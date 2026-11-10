"""Actual Separate outputs: bounded8/8 group-cache extension and30 old goldens."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from decode_mesh_face_group_caches import decode_mesh_face_group_caches
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_separate import decode_mesh_separate_definition, SEPARATE
from validate_mesh_remesh import load

CAPTURE='meshseparates-41126250c03f'


def validate(root,zstd):
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text())
    journal=[json.loads(line) for line in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks,samples,controls=[],[],[]
    def check(label,condition,**evidence):
        if not condition:raise AssertionError(label)
        checks.append(dict(check=label,**evidence))
    check('Actual terminal3 saved exports',(root/CAPTURE/'complete.txt').is_file() and truth['terminal_status']=='complete' and not truth['errors'] and len(truth['samples'])==3)
    closes=[r for r in journal if r['phase']=='owned_document_close_returned']
    check('Actual owned closeFalse3true',len(closes)==3 and all(r['returned'] is True and r['save'] is False for r in closes))
    total=labels=0
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file']
        data,records,features,member,members=load(root,archive,zstd)
        targets=[r for r in records if r.is_primary and r.class_guid==SEPARATE]
        check(archive+' unique Separate feature',len(targets)==1)
        definition=decode_mesh_separate_definition(data,records,targets[0].object_id)
        meshes=decode_mesh_contents_variants(data,records,member,members)
        before=copy.deepcopy(meshes);result=decode_mesh_face_group_caches(meshes)
        api=actual['component_meshes_after_separate']
        check(archive+' exported archive hash exact',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        check(archive+' current result list/collection/API cardinalities agree before numerical comparison',len(result['decoded'])==api['count']==len(definition['output_mesh_object_ids']) and not result['unresolved'] and definition['layout']['exact_full_payload_replay'] is True)
        by_id={m['mesh_object_id']:m for m in meshes['decoded']}
        check(archive+' native current meshes equal explicit Separate outputs',set(by_id)==set(definition['output_mesh_object_ids']))
        check(archive+' retained selected source remains noncurrent with old diagnostic',meshes['unresolved']==[dict(mesh_object_id=definition['source_selection']['mesh_object_id'],reason='Unobserved opt-in native mesh prefix')] and definition['source_selection']['mesh_object_id'] not in by_id)
        native_bundles=[]
        for mesh_id in definition['output_mesh_object_ids']:
            native=by_id[mesh_id];row=next(r for r in result['decoded'] if r['mesh_object_id']==mesh_id)
            g=native['geometry']
            check(archive+' '+str(mesh_id)+' explicit native feature/collection/component ownership',native['feature_object_id']==definition['feature_object_id'] and native['native_feature_class_guid']==SEPARATE and native['collection_mesh_object_ids']==definition['output_mesh_object_ids'] and native['component_object_id']==definition['component_object_id'])
            ids=row['decoded_triangle_face_group_temporary_ids']
            check(archive+' '+str(mesh_id)+' complete buffer5 descriptor/extent retained',row['stored_descriptor_hex']=='82a15401a16401' and len(bytes.fromhex(row['stored_payload_hex']))==len(ids)*4 and 'decompression_scope' not in g['buffers'][5])
            if actual['case']=='two_face_groups':
                check(archive+' only new8/8 native layout and explicit result369',mesh_id==369 and len(g['stored_node_coordinates_float32'])==8 and g['triangle_count']==8)
                guard_source=copy.deepcopy(native)
            native_bundles.append(dict(ordered_triangle_node_indices=g['triangle_node_indices'],
                ordered_triangle_group_temporary_ids=ids,
                ordered_component_node_coordinates_cm=[x for point in g['component_node_coordinates_cm'] for x in point]))
            total+=1;labels+=len(ids)
        api_bundles=[dict(ordered_triangle_node_indices=item['original_polygon_mesh']['triangleNodeIndices'],
            ordered_triangle_group_temporary_ids=item['original_polygon_mesh']['triangleFaceGroupTempIds'],
            ordered_component_node_coordinates_cm=item['original_polygon_mesh']['nodeCoordinatesAsDouble'])
            for item in api['meshes']]
        # These are complete unlabeled result-array bundles. Sorting canonical
        # representations compares a multiset (including multiplicities), not a
        # native-ID -> API-handle assignment. No matched pair table is created.
        def multiset(bundles):
            return sorted(json.dumps(bundle,sort_keys=True,separators=(',',':')) for bundle in bundles)
        native_multiset,api_multiset=multiset(native_bundles),multiset(api_bundles)
        check(archive+' complete result-array multiset exactly corroborates API collectively',native_multiset==api_multiset)
        check(archive+' API collection permutation leaves collective proof unchanged',native_multiset==multiset(list(reversed(api_bundles))))
        check(archive+' no native hierarchy or diagnostic mutations',meshes==before)
        samples.append(dict(archive=archive,expected_decoded=result,expected_mesh_contents=meshes,
            typed_Separate_definition=definition,actual_API_evidence=dict(
                comparison='Unordered multiset of complete result bundles, each retaining ordered triangle indices, ordered temporary-label array and ordered component coordinates',
                native_complete_result_multiset_sha256=hashlib.sha256(json.dumps(native_multiset,separators=(',',':')).encode()).hexdigest(),
                API_complete_result_multiset_sha256=hashlib.sha256(json.dumps(api_multiset,separators=(',',':')).encode()).hexdigest(),
                result_count=len(native_bundles),collective_exact_equality=True,
                identity_scope='Typed Separate output list/current collection proves native outputs. No API per-output handle bridge is present; complete array multisets corroborate collection data only, with no assignment between native IDs and API results.',
                native_API_output_assignment=None)))
    prior=json.loads((root/'mesh-face-group-cache-decoding.json').read_text())
    old_rows=0
    for old in prior['samples']:
        data,records,features,member,members=load(root,old['archive'],zstd)
        mesh=decode_mesh_contents_variants(data,records,member,members)
        got=decode_mesh_face_group_caches(mesh)
        actual_bytes=json.dumps(got,sort_keys=True,separators=(',',':')).encode()
        expected_bytes=json.dumps(old['expected_decoded'],sort_keys=True,separators=(',',':')).encode()
        check(old['archive']+' every previous full cache dictionary canonical-byte exact',actual_bytes==expected_bytes)
        old_rows+=len(got['decoded'])
        controls.append(dict(archive=old['archive'],pool_count=len(got['decoded']),complete_summary_sha256=hashlib.sha256(actual_bytes).hexdigest()))
    bad=copy.deepcopy(guard_source);bad['geometry']['triangle_node_indices']+=[0,1,2]
    rejected=decode_mesh_face_group_caches({'decoded':[bad]})
    check('Reject adjacent unobserved8/9 layout',not rejected['decoded'] and len(rejected['unresolved'])==1)
    return dict(interface='decode_mesh_face_group_caches(mesh_contents)',sample_count=3,current_result_row_count=total,
        collectively_compared_temporary_label_count=labels,prior_full_dictionary_row_count=old_rows,
        check_count=len(checks),samples=samples,old_full_dictionary_controls=controls,checks=checks,
        malformed_guards=[dict(guard='Reject adjacent unobserved8/9 layout',reason=rejected['unresolved'][0]['reason'])],
        runtime_change='Only observed dimension(8,8) added; complete-buffer descriptor, count, native membership, nonnegativeInt32 and exact byte replay unchanged',
        historical_generic_cache_report_sha256=hashlib.sha256((root/'mesh-face-group-cache-decoding.json').read_bytes()).hexdigest(),
        historical_report_scope='Original31-archive/30-row report frozen; this report records current helper source and new Separate holdouts',
        limitations=['All four new actual output group arrays are literal zero; no source-group persistence or grouping meaning assigned',
            'Native output IDs established by typed Separate graph; API corroboration compares unordered complete-array multisets collectively, without per-native-ID/API result assignment',
            'Retained source current-mesh diagnostics remain unchanged','No lifecycle, regeneration or persistent group identity'],
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'decode_mesh_face_group_caches.py','validate_mesh_face_group_separate.py','decode_mesh_separate.py','decode_mesh_geometry_variants.py')})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='mesh-face-group-separate-decoding.json');args=parser.parse_args()
    result=validate(Path(__file__).resolve().parent,args.zstd_library);Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('sample_count','current_result_row_count','collectively_compared_temporary_label_count','prior_full_dictionary_row_count','check_count')}))

if __name__=='__main__':main()
