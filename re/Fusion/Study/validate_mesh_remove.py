"""Owned MeshRemove captures: explicit singleton routes, actual array-return contrast."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from discover_features import discover_features
from fusion_archive import read_members
from fusion_metadata import design_records
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_remove import REMOVE, decode_mesh_remove
from decode_sketch import reference

ROOT=Path(__file__).resolve().parent
DIRECTORY='meshremoves-8b2188cd274d'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def context(filename,zstd):
    members=read_members(ROOT/filename,zstd)
    member,=[n for n in members if n.endswith('/FusionDesignSegmentType1/BulkStream.dat')]
    data=members[member]
    records,registry=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
    features=[]
    discover_features(data,records,features,registry)
    return data,records,features,member,members


def exact_arrays(geometry,actual):
    assert [v for p in geometry['component_node_coordinates_cm'] for v in p]==actual['original_polygon_mesh']['nodeCoordinatesAsDouble']
    assert geometry['triangle_node_indices']==actual['original_polygon_mesh']['triangleNodeIndices']
    assert geometry['node_count']==actual['original_polygon_mesh']['nodeCount']==4
    assert geometry['triangle_count']==actual['original_polygon_mesh']['triangleCount']==4
    assert math.isclose(geometry['derived_absolute_volume_cm3'],actual['volume'],rel_tol=1e-12,abs_tol=1e-12)


def validate(zstd):
    truth_path=ROOT/DIRECTORY/'ground_truth.json'
    truth=json.loads(truth_path.read_text())
    assert truth['terminal_status']=='complete' and truth['errors']==[] and len(truth['samples'])==3
    assert digest(ROOT/DIRECTORY/'executed-generator-source.txt')==truth['executed_generator_sha256']
    assert digest(ROOT/DIRECTORY/truth['helper_snapshot'])==truth['mesh_source_helper_sha256']
    assert digest(ROOT/DIRECTORY/truth['sdk_surface_snapshot'])==truth['sdk_surface_snapshot_sha256']
    report=dict(scope='Three actual owned root MeshRemove add calls: one-of-one, first-of-two, both-of-two. Four native singleton-feature definitions decoded independently from typed selections; reversed API-return order and current membership separately preserved.',
        interface='decode_mesh_remove(data,records,features,member,members,mesh_contents=None)->decoded/unresolved/scope; rows feature_object_id/kindMeshRemove/name/settings',
        integration=dict(stream='mesh_removals',counter='class_decoded_mesh_remove_count',
            decode_level='Observed MeshRemove singleton inputs and retained source/current membership routes; call grouping, lifecycle and regeneration unresolved',
            preserve='Retained source strict mesh_contents prefix diagnostics and all prior warnings remain; no deletion/visibility flag or current-membership exception introduced.'),
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(truth_path),
            executed_generator_sha256=truth['executed_generator_sha256'],mesh_source_helper_sha256=truth['mesh_source_helper_sha256'],
            sdk_runtime_source_sha256=truth['sdk_runtime_source_sha256'],sdk_surface_snapshot_sha256=truth['sdk_surface_snapshot_sha256']),
        native_schema=dict(primary_class_guid=REMOVE,owned_singleton_mesh_proxy_reference_offset=2,
            nil_uuid_string_offset=13,dependency_count_uint32_offset=92,dependency_reference_offsets=[96,107],
            dependency_reference_order=['owned source proxy','source descriptor'],feature_label_offset=122,
            reference_extent_note='Reference@2 consumes bytes2:13; byte12 belongs to the reference padding, not an independent flag.',
            retained_source_proof='Shared strict selected-mesh factory validates typed proxy/descriptor/leaf, reciprocal BaseMesh membership, equal native matrices, asset UUID/file/header, and source absent from bounded current counted collection.'),
        samples=[],malformed_guards=[],legacy_controls=[],
        limitations=['API inputBodies list length two creates two native singleton features in the captured case, but the first returned feature selects the second requested body. No native API-call group or return-array index is assigned.',
            'Source absence from current counted members is an explicit stored fact. Retained records, reciprocal BaseMesh membership and assets do not decode general deletion, hidden, visibility, suppression or lifetime semantics.',
            'Source API baseOrFormFeature getters are None while native BaseMesh membership is explicit. These notions remain separate.',
            'Actual source and remaining meshes are compared only after explicit typed selection/owner/asset routes. No geometry, array position or name similarity chooses native IDs.',
            'Only small root tetra layouts and empty/singleton current collections are admitted; arbitrary assemblies, general multiple inputs per native feature, mesh regeneration and later timeline replay remain unsupported.',
            'MeshBody.area differs from transformed-cache derived area while coordinates, indices and volumes agree. Residuals are preserved and no area scalar convention inferred.'])
    contexts={};source_checks=current_checks=replays=0
    for actual in truth['samples']:
        filename=DIRECTORY+'/'+actual['file']
        assert actual['remove_status']=='FeatureArrayReturned' and not actual['getter_errors']
        assert actual['close_owned_document_returned'] is True and actual['add_returned_null'] is False
        assert actual['add_returned_python_type']=='MeshRemoveFeatureVector'
        assert all(i['actual_count']==1 for i in actual['imports']) and actual['model_parameters_after']==[]
        assert actual['export']['sha256']==digest(ROOT/filename) and actual['export']['size_bytes']==(ROOT/filename).stat().st_size
        data,records,features,member,members=context(filename,zstd)
        before=copy.deepcopy(features)
        meshes=decode_mesh_contents_variants(data,records,member,members)
        decoded=decode_mesh_remove(data,records,features,member,members,meshes)
        assert features==before and not decoded['unresolved']
        assert len(decoded['decoded'])==actual['add_returned_feature_count']==len(actual['features_at_timeline_end'])
        assert len(decoded['decoded'])==(2 if actual['case']=='two_remove_both' else 1)
        actual_features={f['name']:f for f in actual['features_at_timeline_end']}
        rolled={actual['features_at_timeline_end'][r['returned_array_index']]['name']:r for r in actual['rolled_features']}
        assert len(actual_features)==len(rolled)==len(decoded['decoded'])
        evidence=[]
        for row in decoded['decoded']:
            settings=row['settings'];source=settings['retained_source'];api=actual_features[row['name']];rollback=rolled[row['name']]
            assert row['kind']=='MeshRemove' and settings['operation']=='Remove'
            assert api['healthState']==0 and api['errorOrWarningMessage']=='' and not api['feature_getter_errors']
            assert rollback['roll_before_feature_returned'] is True and not rollback['getter_errors']
            rolled_feature=rollback['feature_before_node']
            assert rolled_feature['input_body_count']==api['input_body_count']==settings['native_feature_record_input_count']==1
            source_api,=rolled_feature['inputBodies']
            assert source['name']==source_api['name']==api['inputBodies'][0]['name']
            assert source_api['baseOrFormFeature'] is None
            assert source['retained_membership_status']=='NotInCountedMembers'
            assert settings['selected_mesh_object_id']==settings['input_selection']['mesh_object_id']==source['mesh_object_id']
            assert source['mesh_object_id'] not in settings['current_counted_mesh_object_ids']
            assert source['retained_owner_collection_member_ids']==settings['current_counted_mesh_object_ids']
            assert settings['selected_mesh_is_in_current_counted_members'] is False
            assert settings['API_add_call_group'] is settings['API_returned_array_index'] is settings['is_deleted'] is settings['is_hidden'] is None
            assert not settings['remaining_geometry_unresolved']
            exact_arrays(source['geometry'],source_api)
            source_checks+=1
            layout=settings['layout']
            assert bytes.fromhex(layout['feature_body_hex'])==data[layout['feature_body_offset']:layout['feature_body_end_offset']]
            assert layout['exact_full_payload_replay'] is True
            replays+=1
            assert settings['current_counted_mesh_count']==actual['component_meshes_after_remove']['count']
            remaining=settings['current_counted_meshes']
            actual_remaining=actual['component_meshes_after_remove']['meshes']
            assert len(remaining)==len(actual_remaining)==settings['current_counted_mesh_count']
            for m,a in zip(remaining,actual_remaining):
                # At most one current member in these captures; no multi-result order bridge is assumed.
                assert len(remaining)==1 and m['name']==a['name']
                exact_arrays(m['geometry'],a)
                current_checks+=1
            evidence.append(dict(feature_object_id=row['feature_object_id'],native_source_mesh_object_id=source['mesh_object_id'],
                source_native_BaseMesh_feature_object_id=source['base_mesh_feature_object_id'],
                captured_returned_array_index=rollback['returned_array_index'],
                actual_rolled_source_vs_all_imported_handle_equality=rollback['input_bodies_vs_all_imported_handle_equality'],
                actual_source_custom_name=source_api['name'],exact_source_arrays_and_volume_match=True,
                source_API_area=source_api['area'],source_transformed_cache_derived_area=source['geometry']['derived_area_cm2'],
                scope='API index is capture evidence only and is not promoted to native settings or inferred from source position.'))
        if actual['case']=='two_remove_both':
            assert actual['input_bodies_vs_all_imported_handle_equality']==[[True,False],[False,True]]
            assert [r['input_bodies_vs_all_imported_handle_equality'] for r in actual['rolled_features']]==[[[False,True]],[[True,False]]]
        if actual['case']=='two_remove_first':
            assert actual['remaining_current_vs_all_imported_handle_equality']==[[False,True]]
        else:assert actual['remaining_current_vs_all_imported_handle_equality']==[]
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=decoded,
            expected_mesh_contents=meshes,actual_add_return_type=actual['add_returned_python_type'],
            actual_returned_feature_count=actual['add_returned_feature_count'],
            actual_input_list_count=len(actual['input_before_add']['inputBodies']),
            actual_current_mesh_count=actual['component_meshes_after_remove']['count'],
            actual_input_vs_all_imported_handle_equality=actual['input_bodies_vs_all_imported_handle_equality'],
            actual_remaining_vs_all_imported_handle_equality=actual['remaining_current_vs_all_imported_handle_equality'],
            explicit_per_feature_selection_evidence=evidence,owned_document_closed_true=True))
        contexts[actual['case']]=(data,records,features,member,members,decoded)
    data,records,features,member,members,decoded=contexts['two_remove_first']
    row,=decoded['decoded'];settings=row['settings'];fid=row['feature_object_id']
    by_id={r.object_id:r for r in records if r.is_primary}
    feature_record=by_id[fid]
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    def reject(label,offset,payload):
        damaged=bytearray(data);damaged[offset:offset+len(payload)]=payload
        answer=decode_mesh_remove(bytes(damaged),records,features,member,members)
        assert not answer['decoded'] and len(answer['unresolved'])==1 and answer['unresolved'][0]['class_guid']==REMOVE
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offset=offset,rejected=True,reason=answer['unresolved'][0]['reason']))
    reject('unsupported native feature prefix',feature_record.body,b'\1')
    reject('dependency count3',feature_record.body+92,struct.pack('<I',3))
    reject('dependency descriptor differs from owned source',feature_record.body+107,ref(218))
    proxy=by_id[settings['input_selection']['proxy_object_id']]
    reject('source proxy feature owner differs',proxy.end-11,ref(218))
    leaf=by_id[settings['input_selection']['leaf_object_id']]
    reject('direct mesh pointer and typed leaf disagree',leaf.body+2,struct.pack('<Q',246))
    base=by_id[settings['retained_source']['base_mesh_feature_object_id']]
    reject('source BaseMesh backlink points at remaining mesh',base.body+6,ref(246))
    collection,=[r for r in records if not r.is_primary and r.object_id==settings['current_mesh_collection_object_id'] and r.class_guid=='A7AEA631-985B-4DD1-8CE2-DE2C-14B54081']
    reject('source inserted into current counted members',collection.body+5,ref(settings['selected_mesh_object_id']))
    asset=by_id[settings['retained_source']['asset_object_id']]
    original=data[asset.body+17]
    reject('native asset UUID differs from same-asset embedded header',asset.body+17,bytes([ord('1') if original!=ord('1') else ord('2')]))
    separate=json.loads((ROOT/'mesh-separate-decoding.json').read_text())
    for old in separate['samples']:
        if not old['archive'].endswith(('/two_shells.f3d','/connected_shell_control.f3d')):continue
        d,rs,fs,n,m=context(old['archive'],zstd)
        old_mesh=decode_mesh_contents_variants(d,rs,n,m)
        assert old_mesh==old['expected_mesh_contents']
        empty=decode_mesh_remove(d,rs,fs,n,m,old_mesh)
        assert not empty['decoded'] and not empty['unresolved']
        report['legacy_controls'].append(dict(archive=old['archive'],existing_mesh_contents_exact=True,new_helper_no_candidates=True))
    report['summary']=dict(saved_archives=3,decoded_native_features=4,actual_API_add_calls=3,
        exact_source_array_checks=source_checks,exact_remaining_array_checks=current_checks,
        full_feature_payload_replays=replays,malformed_guards=len(report['malformed_guards']),
        exact_legacy_controls=len(report['legacy_controls']),API_return_order_counterexamples=1,
        common_source_changes=0,main_runs=0,live_calls=0)
    report['runtime_source_sha256']={f:digest(ROOT/f) for f in ('decode_mesh_remove.py','validate_mesh_remove.py',
        'decode_retained_mesh_sources.py','decode_mesh_contents.py','decode_mesh_geometry_variants.py','decode_mesh_selections.py')}
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default=str(ROOT/'mesh-remove-decoding.json'))
    args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd)
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':main()
