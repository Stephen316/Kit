"""Saved historical GenerateFaceGroups controls, typed asset/history joins and defaults."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import types
from unittest.mock import patch

import decode_mesh_face_groups as common
from decode_historical_mesh_face_groups import decode_historical_mesh_face_groups,OLD_REASON
from decode_mesh_combine_face_groups import decode_mesh_combine_face_groups
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_placement import transform_point
from decode_sketch import reference
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
CAPTURE='meshcombinefacegroups-33142f03b86e'
BASELINE='4587d9e'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(zstd):
    checks=[];samples=[];guards=[];controls=[];saved=[]
    def check(label,value,**evidence):
        if not value:raise AssertionError(label)
        checks.append(dict(check=label,**evidence))
    source=subprocess.check_output(['git','show',BASELINE+':decode_mesh_face_groups.py'],cwd=ROOT).decode()
    frozen=types.ModuleType('historical_face_groups_frozen');exec(compile(source,'frozen_mesh_face_groups.py','exec'),frozen.__dict__)
    folder=ROOT/CAPTURE;truth=json.loads((folder/'ground_truth.json').read_text())
    check('Actual terminal three exports and no case errors',truth['terminal_status']=='complete' and not truth['errors'] and len(truth['samples'])==3 and (folder/'complete.txt').is_file())
    check('Exact executed generator snapshot',digest(folder/'executed-generator-source.txt')==truth['executed_generator_sha256'])
    check('Exact SDK public surface snapshot',digest(folder/truth['sdk_surface_snapshot'])==truth['sdk_surface_snapshot_sha256'])
    check('Exact owned mesh helper snapshot',digest(folder/'executed-mesh-source-helper.txt')==truth['mesh_source_helper_sha256'])
    combine_goldens={v['archive']:v['expected_decoded'] for v in json.loads((ROOT/'mesh-combine-face-group-decoding.json').read_text())['samples']}
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file'];d,rs,fs,member,members=load(ROOT,archive,zstd)
        meshes=decode_mesh_contents_variants(d,rs,member,members);before_fs,before_mesh=copy.deepcopy(fs),copy.deepcopy(meshes)
        strict=common.decode_mesh_face_groups(d,rs,fs,member,members,meshes)
        check(archive+' full strict default outcome unchanged',strict==frozen.decode_mesh_face_groups(d,rs,fs,member,members,meshes) and not strict['decoded'] and len(strict['unresolved'])==1 and strict['unresolved'][0]['reason']==OLD_REASON)
        check(archive+' whole CombineFaceGroups summary remains exact',decode_mesh_combine_face_groups(d,rs,fs,member,members,meshes)==combine_goldens[archive])
        result=decode_historical_mesh_face_groups(d,rs,fs,member,members,meshes)
        check(archive+' one qualified stored feature asset',len(result['decoded'])==1 and not result['unresolved'])
        row,=result['decoded'];s=row['settings'];route=row['route'];api=actual['preparation_feature'];inp=actual['preparation_input_controls']
        check(archive+' export and close evidence',digest(ROOT/archive)==actual['export']['sha256'] and actual['close_owned_document_returned'] is True and not actual['getter_errors'] and not actual['setter_errors'])
        check(archive+' healthy actual preparation feature',api['healthState']==0 and api['errorOrWarningMessage']=='' and not api['feature_getter_errors'] and not api['control_getter_errors'])
        check(archive+' actual method/name/type match',s['method']=='Fast' and s['stored_method_code']==api['meshGenerateFaceGroupsMethodType']==inp['meshGenerateFaceGroupsMethodType']==0 and row['name']==api['name'] and api['objectType']=='adsk::fusion::MeshGenerateFaceGroupsFeature')
        for role,prop in (('Angle Threshold','angleThreshold'),('Minimum Face Group Size','minimumFaceGroupSize')):
            binding=s['scalar_bindings'][role];value=api[prop]
            check(archive+' '+role+' API role/name/value/unit/creator',binding['is_active'] is True and binding['stored_value']==value['value']==inp[prop]['realValue'] and binding['parameter_name']==value['name'] and value['role']==role and value['unit']==binding['display_units'] and value['createdBy']['name']==row['name'])
        check(archive+' inactive boundary not promoted',s['boundary_tolerance_cm'] is None and not s['scalar_bindings']['Boundary Tolerance']['is_active'] and api['boundaryTolerance'] is None and inp['boundaryTolerance'] is None and api['boundaryTolerance_status'].startswith('Inactive'))
        feature_asset=s['stored_feature_asset'];current_asset=s['selected_current_mesh_asset'];additional=s['additional_stored_asset'];mesh,=meshes['decoded']
        check(archive+' stored and current explicit identities separate',s['stored_feature_asset_is_current'] is False and feature_asset['asset_object_id']!=current_asset['asset_object_id']==mesh['asset_object_id'] and current_asset['asset_member']==mesh['asset_member'] and 'current_mesh_asset' not in s)
        check(archive+' unchanged reciprocal current mesh owner',s['native_mesh_object_id']==mesh['mesh_object_id']==route['selected_native_mesh_object_id'] and s['current_mesh_native_feature_owner_object_id']==mesh['feature_object_id'] and s['current_mesh_native_owner_class_guid']==mesh['native_feature_class_guid'] and route['selected_current_mesh_route']['collection_mesh_object_ids']==mesh['collection_mesh_object_ids'])
        check(archive+' explicit feature39 and Combine additional identity agree',route['stored_feature_asset_object_id']==route['following_combine_additional_asset_object_id']==feature_asset['asset_object_id'] and route['stored_feature_asset_member']==feature_asset['asset_member'])
        history=route['history'];ids=history['native_entry_object_ids']
        check(archive+' actual typed history order distinct from counters',ids[history['feature_native_entry_index']]==row['feature_object_id'] and ids[history['combine_native_entry_index']]==route['following_combine_feature_object_id'] and history['feature_native_entry_index']<history['combine_native_entry_index'])
        check(archive+' feature complete raw bytes retained',bytes.fromhex(route['stored_feature_body_hex'])==d[route['feature_body_offset']:route['feature_body_end_offset']] and reference(d[route['feature_body_offset']:route['feature_body_end_offset']],39)==feature_asset['asset_object_id'])
        check(archive+' asset50 additional role remains unknown',s['additional_asset_temporal_role'] is None and route['asset50_temporal_role'] is None and additional['asset_object_id'] not in (feature_asset['asset_object_id'],current_asset['asset_object_id']))
        before=actual['component_meshes_before_combine_groups']['meshes'][0]['original_polygon_mesh'];after=actual['component_meshes_after_combine_groups']['meshes'][0]['original_polygon_mesh']
        cache=s['triangle_face_groups'];labels=cache['decoded_triangle_face_group_temporary_ids'];geometry=feature_asset['geometry']
        check(archive+' exact ordered before-Combine group labels',labels==before['triangleFaceGroupTempIds']==list(range(1,9)) and before['triangleCount']==8)
        check(archive+' exact typed stored-cache indices against API before',geometry['triangle_node_indices']==before['triangleNodeIndices'])
        matrix=route['selected_current_mesh_route']['asset_coordinates_to_component_matrix']
        derived=[x for p in geometry['stored_node_coordinates_float32'] for x in transform_point(matrix,p)]
        maximum=max(abs(a-b) for a,b in zip(derived,before['nodeCoordinatesAsDouble']))
        check(archive+' current mesh frame applied to explicit stored asset corroborates before API',len(derived)==len(before['nodeCoordinatesAsDouble']) and maximum<1e-7,maximum_coordinate_discrepancy_cm=maximum,scope='Report-only derived comparison; no historical transform state inferred or published')
        raw=bytes.fromhex(cache['stored_payload_hex']);check(archive+' full stored Int32 group byte replay',raw==struct.pack('<8i',*cache['stored_int32_forward_differences'])==bytes.fromhex(geometry['buffers'][5]['uncompressed_payload_hex']))
        check(archive+' current after-Combine ordered arrays independently match',mesh['geometry']['triangle_node_indices']==after['triangleNodeIndices'] and [x for p in mesh['geometry']['component_node_coordinates_cm'] for x in p]==after['nodeCoordinatesAsDouble'])
        check(archive+' before/cache grouping not falsely current',labels!=after['triangleFaceGroupTempIds'] and mesh['asset_object_id']==current_asset['asset_object_id'])
        check(archive+' input data structures unchanged',before_fs==fs and before_mesh==meshes)
        samples.append(dict(archive=archive,archive_sha256=digest(ROOT/archive),expected_decoded=result,expected_default=strict,actual_preparation_controls=dict(method=api['meshGenerateFaceGroupsMethodType'],angle_threshold_radians=api['angleThreshold']['value'],minimum_face_group_size=api['minimumFaceGroupSize']['value'],health=api['healthState']),actual_API_before_Combine_triangle_face_group_ids=before['triangleFaceGroupTempIds'],actual_API_after_Combine_triangle_face_group_ids=after['triangleFaceGroupTempIds'],maximum_report_only_coordinate_discrepancy_cm=maximum,native_API_handle_pairing=None))
        saved.append((d,rs,fs,member,members,meshes,result))
    d,rs,fs,member,members,meshes,result=saved[0];row=result['decoded'][0];fid=row['feature_object_id'];byid={r.object_id:r for r in rs if r.is_primary};r=byid[fid]
    def guard(label,mutation=None,mesh_mutation=None,asset_mutation=None):
        changed=bytearray(d);changed_mesh=copy.deepcopy(meshes)
        if mutation:mutation(changed)
        if mesh_mutation:mesh_mutation(changed_mesh)
        def bad_asset(*args,**kwargs):
            a=original_asset(*args,**kwargs)
            if a['asset_object_id']==row['route']['stored_feature_asset_object_id']:asset_mutation(a)
            return a
        if asset_mutation:
            original_asset=common.decode_mesh_asset
            with patch('decode_mesh_face_groups.decode_mesh_asset',bad_asset):answer=decode_historical_mesh_face_groups(bytes(changed),rs,fs,member,members,changed_mesh)
        else:answer=decode_historical_mesh_face_groups(bytes(changed),rs,fs,member,members,changed_mesh)
        strict=common.decode_mesh_face_groups(bytes(changed),rs,fs,member,members,changed_mesh)
        check(label,not answer['decoded']);guards.append(dict(guard=label,variant_unresolved=answer['unresolved'],default_unresolved=strict['unresolved']))
    binding=byid[row['settings']['scalar_bindings']['Angle Threshold']['binding_object_id']]
    guard('Reject scalar owner mismatch',lambda b:struct.pack_into('<Q',b,binding.body+6,fid+1))
    guard('Reject repeated dependency count mismatch',lambda b:struct.pack_into('<I',b,r.body+156,4))
    proxy=byid[row['settings']['input_selection']['proxy_object_id']]
    guard('Reject selected proxy owner mismatch',lambda b:struct.pack_into('<Q',b,proxy.end-10,fid+1))
    history=byid[row['route']['history']['history_record_object_id']];a=row['route']['history']['feature_native_entry_index'];b=row['route']['history']['combine_native_entry_index']
    def reverse_history(buf):
        first=bytes(buf[history.body+17+11*a:history.body+28+11*a]);second=bytes(buf[history.body+17+11*b:history.body+28+11*b]);buf[history.body+17+11*a:history.body+28+11*a]=second;buf[history.body+17+11*b:history.body+28+11*b]=first
    guard('Reject reversed explicit native history',reverse_history)
    guard('Reject absent shared history source',lambda buf:struct.pack_into('<Q',buf,history.body+18+11*a,999999))
    combine=byid[row['route']['following_combine_feature_object_id']]
    guard('Reject Combine additional asset reference alias',lambda buf:struct.pack_into('<Q',buf,combine.body+54,row['settings']['additional_stored_asset']['asset_object_id']))
    guard('Reject selected current asset member mismatch',mesh_mutation=lambda m:m['decoded'][0].update(asset_member='wrong/asset.paramesh'))
    guard('Reject feature-cache count/label pattern mismatch',asset_mutation=lambda a:a['geometry']['buffers'][5].update(uncompressed_payload_hex=struct.pack('<8i',*([1]*7+[9])).hex()))
    old=json.loads((ROOT/'mesh-face-group-decoding.json').read_text())
    for sample in old['samples']:
        archive=sample['archive'];args=load(ROOT,archive,zstd);d,rs,fs,member,members=args;meshes=decode_mesh_contents_variants(d,rs,member,members)
        current=common.decode_mesh_face_groups(d,rs,fs,member,members,meshes)
        check(archive+' pinned whole current-only summary exact',current==frozen.decode_mesh_face_groups(d,rs,fs,member,members,meshes))
        check(archive+' historical report whole summary exact',current==sample['expected_decoded'])
        empty=decode_historical_mesh_face_groups(d,rs,fs,member,members,meshes);check(archive+' no historical false candidate',not empty['decoded'] and not empty['unresolved'])
        controls.append(dict(archive=archive,pinned_and_prior_report_full_summary_exact=True,new_wrapper_no_candidate=True))
    return dict(interface='decode_historical_mesh_face_groups(data,records,features,member,members,mesh_contents=None)->decoded/unresolved/scope; rows feature_object_id/kind/name/settings/route',shared_opt_in='decode_mesh_face_groups(...,allow_stored_feature_asset=False); exact current-only default unchanged',integration=dict(stream='historical_mesh_face_groups',feature_route='historical_mesh_face_group_route',kind='MeshGenerateFaceGroups',clear_only_qualified_prior_reason=OLD_REASON,counter='class_decoded_historical_mesh_face_group_count',old_summary_key_and_counter_preserved=True,decode_level='Observed historical MeshGenerateFaceGroups controls and stored feature cache before CombineFaceGroups; current asset ownership and general lifecycle remain separate'),capture=CAPTURE,ground_truth_sha256=digest(folder/'ground_truth.json'),executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['sdk_surface_snapshot_sha256'],mesh_source_helper_sha256=truth['mesh_source_helper_sha256'],samples=samples,malformed_guards=guards,legacy_controls=controls,checks=checks,validation=dict(actual_exports=3,healthy_preparation_features=3,owned_closes_true=3,stored_triangle_labels=24,check_count=len(checks),malformed_guards=len(guards),legacy_current_summaries_exact=len(controls),legacy_Combine_summaries_exact=3,strict_new_file_rejections_exact=3,no_live_calls=True,no_main_calls=True),default_preservation=dict(pinned_revision=BASELINE,pinned_reader_sha256=hashlib.sha256(source.encode()).hexdigest()),source_sha256={p:digest(ROOT/p) for p in ('decode_mesh_face_groups.py','decode_historical_mesh_face_groups.py','validate_historical_mesh_face_groups.py','decode_mesh_combine_face_groups.py','decode_mesh_geometry_variants.py','decode_mesh_selections.py','decode_timeline.py')},limitations=['The same-asset ID/typed selection/history joins establish stored-feature cache provenance; coordinates, names and order do not choose identity.','The stored Generate asset is not the current native mesh asset. Current mesh associations and geometry remain unchanged.','API controls and ordered before-Combine labels corroborate three saved cases only; temporary labels are not persistent face identities. No native/API handle pairing is asserted.','Current mesh transform applied to stored asset coordinates is report-only corroboration after identity joins, not proof of arbitrary historical placement state.','Explicit asset50 has no assigned temporal role. General source/result lifecycle, grouping algorithm, regeneration and history replay remain unresolved.'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--zstd');p.add_argument('--output',default='historical-mesh-face-group-decoding.json');a=p.parse_args()
    z=a.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['validation'],sort_keys=True))
