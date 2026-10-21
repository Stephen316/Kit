"""Three actual MeshReduce control successes and one preserved expression failure."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from decode_basics import named_features,attach_parameters
from discover_features import discover_features
from decode_parameters import decode_stream
from decode_mesh_contents import MESH
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_reduce import decode_mesh_reduce,REDUCE
from decode_mesh_selections import decode_mesh_selection
from decode_sketch import same
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
CAPTURES=('meshreduces-780954a23308','meshreduces-8f01528f7f21')


def load(root,archive,zstd):
    members=read_members(root/archive,zstd);member=next(n for n in members if n.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
    data=members[member];records,index=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
    features=named_features(data,records);discover_features(data,records,features,index)
    parameters,_=decode_stream(data,records);attach_parameters(data,records,features,parameters)
    return data,records,features,member,members


def api_triangles(mesh):
    flat=mesh['nodeCoordinatesAsDouble'];points=[flat[i:i+3] for i in range(0,len(flat),3)];indices=mesh['triangleNodeIndices']
    return sorted(tuple(sorted(tuple(points[indices[start+i]]) for i in range(3))) for start in range(0,len(indices),3))


def validate(root,zstd):
    report=dict(interface='decode_mesh_reduce(data,records,features,member,members,mesh_contents=None) -> decoded/unresolved/scope; rows feature_object_id/kindMeshReduce/name/settings',
        shared_selection_interface='decode_mesh_selection(data,records,proxy_id,feature_id); exact94/105-byte owned proxy and263-byte typed mesh descriptor/90055 repeat',
        validation_command='python3 validate_mesh_reduce.py --zstd-library <libzstd path>',
        samples=[],guards=[],selection_controls=[],old_controls=[],prefix_counterexamples=[],
        source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'GenerateMeshReduceContrasts.py','GenerateMeshReduceProportionHoldout.py','decode_mesh_reduce.py',
            'decode_mesh_selections.py','decode_mesh_geometry_variants.py','decode_mesh_contents.py','decode_parameters.py','validate_mesh_reduce.py')})
    saved={};successes=negatives=0
    for folder in CAPTURES:
        truth=json.loads((root/folder/'ground_truth.json').read_text())
        assert (root/folder/'complete.txt').is_file()
        executed=(root/folder/'executed-generator-source.txt').read_bytes()
        assert hashlib.sha256(executed).hexdigest()==truth['executed_generator_sha256']
        for sample in truth['samples']:
            archive=folder+'/'+sample['file'];loaded=load(root,archive,zstd);data,records,features,member,members=loaded
            initial_features=copy.deepcopy(features);mesh_summary=decode_mesh_contents_variants(data,records,member,members)
            decoded=decode_mesh_reduce(data,records,features,member,members,mesh_summary)
            assert features==initial_features and len(mesh_summary['decoded'])==1 and not mesh_summary['unresolved']
            api_before=sample['source_before_reduce']['original_polygon_mesh']
            api_after=sample['component_meshes_after_reduce']['meshes'][0]['original_polygon_mesh']
            current=mesh_summary['decoded'][0];geometry=current['geometry']
            checks=dict(actual_export_hash_matches=hashlib.sha256((root/archive).read_bytes()).hexdigest()==sample['export']['sha256'],
                actual_document_close_returned_true=sample['close_owned_document_returned'] is True,
                source_mesh_is_six_nodes_eight_triangles=api_before['nodeCount']==6 and api_before['triangleCount']==8,
                current_mesh_is_six_nodes_eight_triangles=api_after['nodeCount']==6 and api_after['triangleCount']==8,
                native_current_count_matches_actual=geometry['node_count']==api_after['nodeCount'] and geometry['triangle_count']==api_after['triangleCount'],
                native_current_ordered_coordinates_match_actual=same([x for p in geometry['component_node_coordinates_cm'] for x in p],api_after['nodeCoordinatesAsDouble']),
                native_current_ordered_triangle_indices_match_actual=geometry['triangle_node_indices']==api_after['triangleNodeIndices'],
                API_before_after_triangle_coordinate_multisets_equal=api_triangles(api_before)==api_triangles(api_after))
            observation=dict(API_source_arrays=api_before,API_current_arrays=api_after,
                literal_API_arrays_equal=api_before['nodeCoordinatesAsDouble']==api_after['nodeCoordinatesAsDouble'] and api_before['triangleNodeIndices']==api_after['triangleNodeIndices'],
                API_source_mesh_name=sample['source_before_reduce']['name'],
                API_current_mesh_name=sample['component_meshes_after_reduce']['meshes'][0]['name'])
            if sample['reduce_status']=='FeatureReturned':
                successes+=1;assert len(decoded['decoded'])==1 and not decoded['unresolved'],decoded
                row=decoded['decoded'][0];settings=row['settings'];actual=sample['feature_before_node'];active=actual['active_target_parameter']
                params={p['role']:p for p in sample['model_parameters_after'] if p['createdBy']['name']==row['name']}
                controls=sample['input_before_add'];is_count=settings['target_type']=='FaceCount'
                checks.update(native_method_code_matches_actual=settings['stored_method_code']==actual['meshReduceMethodType']==controls['meshReduceMethodType'],
                    native_target_code_matches_actual=settings['stored_target_code']==actual['meshReduceTargetType']==controls['meshReduceTargetType'],
                    active_role_value_units_match_actual=active['role']==('Face Count' if is_count else 'Proportion') and active['value']==(settings['requested_face_count'] if is_count else settings['requested_proportion_stored_value']) and active['unit']=='',
                    all_three_native_binding_roles_values_and_units_match_API=all(r['stored_value']==params[role]['value'] and r['display_units']==params[role]['unit'] for role,r in settings['scalar_bindings'].items()),
                    actual_input_mesh_name_matches_typed_source=settings['mesh_name']==actual['mesh']['name']==sample['source_before_reduce']['name'],
                    actual_feature_input_handle_equality_observed=sample['feature_input_mesh_equals_import_handle'] is True,
                    current_asset_corroborates_selected_native_mesh=settings['native_mesh_object_id']==current['mesh_object_id'] and settings['current_mesh_asset']['asset_object_id']==current['asset_object_id'],
                    native_BaseMesh_owner_remains_distinct=settings['current_mesh_native_feature_owner_object_id']==current['feature_object_id']!=row['feature_object_id'],
                    reduce_mesh_ownership_not_invented=settings['mesh_reduce_owns_current_mesh'] is None,
                    additional_asset_temporal_role_not_invented=settings['additional_asset_temporal_role'] is None,
                    actual_feature_healthy=sample['feature_at_timeline_end']['healthState']==0 and sample['feature_at_timeline_end']['errorOrWarningMessage']=='',
                    actual_BRep_feature_collections_empty=actual['brep_bodies']==[] and actual['brep_faces']==[],
                    counts_do_not_claim_target_attainment=settings['face_count_target_attained_in_current_cache'] is False if is_count else settings['face_count_target_attained_in_current_cache'] is None,
                    stored_two_asset_coordinate_multisets_equal=settings['stored_two_asset_triangle_coordinate_multisets_equal'] is True,
                    successful_API_arrays_are_reindexed=observation['literal_API_arrays_equal'] is False)
                if not is_count:
                    checks['real50_not_normalized_to_point5']=sample['requested_value_input']['realValue']==controls['active_target_value_input']['realValue']==active['value']==50.0 and active['expression']=='50'
                record=next(r for r in records if r.is_primary and r.object_id==row['feature_object_id'])
                saved[sample['case']]=(loaded,decoded,record)
                observation.update(API_active_parameter=active,API_feature_before_node=actual,
                    geometry_note='Both actual node/face counts remain6/8 and triangle-coordinate multisets agree; ordered arrays differ. This does not assert that the target was reached or reproduce an algorithm.')
            else:
                negatives+=1;assert sample['case']=='adaptive_proportion_fifty' and folder==CAPTURES[0]
                checks.update(no_native_Reduce_feature_created=not any(r.is_primary and r.class_guid==REDUCE for r in records),
                    negative_not_promoted_to_decoded_or_unresolved_feature=not decoded['decoded'] and not decoded['unresolved'],
                    real_error_is_expression_at_add='RuntimeError: 3 : invalid expression' in sample['reduce_error']['error'],
                    string50_percent_request_preserved=sample['requested_value_input']['stringValue']=='50 %' and sample['input_before_add']['active_target_value_input']['stringValue']=='50 %',
                    failed_attempt_source_arrays_remain_literal_equal=observation['literal_API_arrays_equal'] is True,
                    no_failed_attempt_ModelParameters=sample['model_parameters_after']==[])
                observation.update(API_negative_error=sample['reduce_error'],API_requested_value_input=sample['requested_value_input'],
                    negative_scope='Archive has no native MeshReduce feature; expression failure is independently preserved API evidence, not a decoded native error or unsupported feature invention.')
            assert all(checks.values()),(archive,checks)
            report['samples'].append(dict(archive=archive,expected_decoded=decoded,expected_mesh_contents=mesh_summary,checks=checks,
                actual_reduce_status=sample['reduce_status'],observation=observation,
                actual_input_controls=sample.get('input_before_add'),executed_generator_sha256=truth['executed_generator_sha256'],
                top_level_getter_errors=sample['getter_errors'],setter_errors=sample['setter_errors']))
    assert successes==3 and negatives==1
    # PlaneCut independently supplies an existing105-byte source proxy and94-byte
    # result proxy with a null secondary list, proving both shared frame variants.
    loaded=load(root,'meshplanecuts-18f2683c83f5/split_body_minimal_fill.f3d',zstd)
    data,records,features,member,members=loaded
    for proxy_id,expected_mesh,secondary in ((309,213,1),(338,333,0)):
        selected=decode_mesh_selection(data,records,proxy_id,308)
        assert selected['mesh_object_id']==expected_mesh and selected['stored_secondary_count']==secondary
        report['selection_controls'].append(dict(archive='meshplanecuts-18f2683c83f5/split_body_minimal_fill.f3d',expected_selection=selected))
    for archive in ('meshcontrasts-10c2557c91a3/stl_centimeter.f3d','meshplanecuts-18f2683c83f5/split_body_minimal_fill.f3d'):
        data,records,features,member,members=load(root,archive,zstd)
        decoded=decode_mesh_reduce(data,records,features,member,members)
        assert not decoded['decoded'] and not decoded['unresolved']
        report['old_controls'].append(dict(archive=archive,no_false_Reduce_feature=True))
    # The packed prefix is not a reference: its same bytes would point to no
    # oldtetra object, PlaneCut's construction plane, or Reduce's unrelated proxy.
    for archive in ('meshcontrasts-10c2557c91a3/stl_centimeter.f3d','meshplanecuts-18f2683c83f5/split_body_minimal_fill.f3d',CAPTURES[0]+'/adaptive_count_six.f3d'):
        data,records,features,member,members=load(root,archive,zstd)
        mesh_record=next(r for r in records if r.is_primary and r.class_guid==MESH)
        raw=data[mesh_record.body+11:mesh_record.body+22];assert raw==bytes.fromhex('0101010000000000000000')
        collision=struct.unpack_from('<Q',raw,1)[0];targets=[r for r in records if r.is_primary and r.object_id==collision]
        report['prefix_counterexamples'].append(dict(archive=archive,stored_native_mesh_prefix_11_22_hex=raw.hex(),
            numeric_value_if_forced_as_reference=collision,coincidental_primary_class_guid=targets[0].class_guid if targets else None,
            accepted_as_mesh_to_proxy_reference=False))
    assert [r['coincidental_primary_class_guid'] for r in report['prefix_counterexamples']]==[None,'D869265F-F339-4751-A066-91D30F81FF08','22975A91-16AD-4CC9-A5E4-B4F8B4C27881']
    loaded,baseline,feature_record=saved['adaptive_count_six'];data,records,features,member,members=loaded
    settings=baseline['decoded'][0]['settings'];by={r.object_id:r for r in records if r.is_primary}
    def guard(label,identity,offset,replacement,selection_only=False):
        changed=bytearray(data);record=by[identity];changed[record.body+offset:record.body+offset+len(replacement)]=replacement
        if selection_only:
            try:decode_mesh_selection(bytes(changed),records,settings['input_selection']['proxy_object_id'],feature_record.object_id)
            except (ValueError,IndexError,struct.error) as error:reason=str(error)
            else:raise AssertionError(label)
        else:
            current=decode_mesh_reduce(bytes(changed),records,features,member,members)
            assert not current['decoded'] and len(current['unresolved'])==1,(label,current)
            reason=current['unresolved'][0]['reason']
        report['guards'].append(dict(check=label,passed=True,reason=reason))
    guard('Unknown native Reduce method',feature_record.object_id,13,struct.pack('<I',9))
    guard('Uncaptured MaximumDeviation target',feature_record.object_id,29,struct.pack('<I',0))
    guard('Scalar binding must be owned by feature',settings['scalar_bindings']['Face Count']['binding_object_id'],6,struct.pack('<Q',204))
    guard('Binding and parameter numeric copies must agree',settings['scalar_bindings']['Face Count']['binding_object_id'],22,struct.pack('<I',7))
    guard('Two stored assets must not alias',feature_record.object_id,55,data[feature_record.body+44:feature_record.body+55])
    guard('Repeated scalar role references must agree',feature_record.object_id,188,struct.pack('<Q',settings['scalar_bindings']['Tolerance']['binding_object_id']))
    selected=settings['input_selection']
    guard('Mesh proxy footer owner mismatch',selected['proxy_object_id'],95,struct.pack('<Q',204),True)
    guard('Direct mesh and typed leaf must repeat same identity',selected['leaf_object_id'],2,struct.pack('<Q',feature_record.object_id),True)
    guard('Secondary list count must meet exact proxy extent',selected['proxy_object_id'],19,struct.pack('<I',0),True)
    guard('Mesh descriptor owner mismatch',selected['descriptor_object_id'],253,struct.pack('<Q',204),True)
    report['counts']=dict(actual_samples=4,successful_native_Reduce_features=3,preserved_failed_expression_archives=1,
        successful_FaceCount6_with_eight_actual_triangles=2,successful_Proportion_real50=1,
        shared_selection_variant_controls=2,old_no_false_positive_controls=2,prefix_numeric_collision_counterexamples=3,
        malformed_guards=len(report['guards']),full_main_reader_runs=0,live_API_calls=0)
    report['limits']=[
        'Successful native feature controls do not prove FaceCount6 was achieved: both actual count cases and their current stored caches retain6nodes/8triangles. API before/after geometry is reindexed; raw arrays remain independent.',
        'Real50.0 succeeds with Proportion ModelParameter50.0/unitempty/expression50; string50 % fails at add. This proves only these concrete input representations and does not invent a universal percent normalization rule.',
        'Only Adaptive/Uniform FaceCount6 and Adaptive real50 Proportion with inactivezero bindings are admitted. MaximumDeviation, other values/method combinations, procedural reduction and general mesh layouts remain unsupported.',
        'Typed source proxy/descriptor/leaf proves native input mesh identity. First asset is independently corroborated as its current stored asset; additional asset remains temporally unqualified. No MeshReduce result ownership, historical source state or API baseOrFormFeature is inferred.',
        'Packed native mesh bytes11:22 are invariant across incompatible/no-object257 controls and are not a proxy backlink. The shared selection factory uses variable typed fields only.',
        'Despite SDK base-class null wording, actual BRep bodies/faces getters return empty collections; those observations are retained and never treated as mesh results.',
        'Known mesh polygon-array getter errors are preserved in nested API snapshots; no empty arrays or synthetic successful getters substituted.']
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--zstd-library',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-reduce-decoding.json');args=parser.parse_args()
    report=validate(ROOT,args.zstd_library);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']))
