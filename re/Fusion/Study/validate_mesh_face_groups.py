"""Three real GenerateFaceGroups controls and ordered buffer5 cache evidence."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_mesh_face_groups import decode_mesh_face_groups, FACE_GROUPS
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from validate_mesh_remesh import load

CAPTURE = 'meshfacegroups-0b682fa7d749'


def validate(root, zstd):
    truth = json.loads((root/CAPTURE/'ground_truth.json').read_text())
    journal = [json.loads(line) for line in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks, guards, samples, controls = [], [], [], []
    def check(label, condition, **evidence):
        if not condition: raise AssertionError(label)
        checks.append(dict(check=label, **evidence))
    check('Actual terminal3 exports without case errors', (root/CAPTURE/'complete.txt').is_file() and truth['terminal_status']=='complete' and not truth['errors'] and len(truth['samples'])==3)
    closes = [r for r in journal if r['phase']=='owned_document_close_returned']
    check('Actual3 owned close(False) returned true', len(closes)==3 and all(r['returned'] is True and r['save'] is False for r in closes))
    check('Terminal journal agrees with3 successful exports', journal[-1]['phase']=='batch_terminal' and journal[-1]['sample_count']==3 and journal[-1]['error_count']==0)
    check('Exact executed generator snapshot hash', hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file']
        data,records,features,member,members=load(root,archive,zstd)
        meshes=decode_mesh_contents_variants(data,records,member,members)
        feature_before,mesh_before=copy.deepcopy(features),copy.deepcopy(meshes)
        result=decode_mesh_face_groups(data,records,features,member,members,meshes)
        check(archive+' one feature/no unresolved', len(result['decoded'])==1 and not result['unresolved'])
        check(archive+' exact archive exporthash', hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        check(archive+' healthy actual parametric feature and successful owned close', actual['face_groups_status']=='FeatureReturned' and actual['close_owned_document_returned'] is True and actual['feature_at_timeline_end']['healthState']==0 and actual['feature_at_timeline_end']['errorOrWarningMessage']=='')
        row=result['decoded'][0];settings=row['settings'];api=actual['feature_before_node']
        check(archive+' actual feature name/type/enum agree', row['name']==api['name'] and api['objectType']=='adsk::fusion::MeshGenerateFaceGroupsFeature' and settings['stored_method_code']==api['meshGenerateFaceGroupsMethodType'])
        check(archive+' actual input and rolled source handle equal owned import', actual['input_mesh_equals_import_handle'] is True and actual['feature_input_mesh_equals_import_handle'] is True and actual['roll_before_feature_returned'] is True)
        check(archive+' upstream current mesh uniquely selected typed owner retained', len(meshes['decoded'])==1 and not meshes['unresolved'] and settings['input_selection']['mesh_object_id']==meshes['decoded'][0]['mesh_object_id']==settings['native_mesh_object_id']==213 and settings['current_mesh_native_feature_owner_object_id']==meshes['decoded'][0]['feature_object_id'])
        check(archive+' first asset explicitly agrees with selected current mesh', settings['current_mesh_asset']['asset_object_id']==meshes['decoded'][0]['asset_object_id'] and settings['current_mesh_asset']['asset_member']==meshes['decoded'][0]['asset_member'])
        check(archive+' additional asset distinct and temporal role unresolved', settings['additional_stored_asset']['asset_object_id']!=settings['current_mesh_asset']['asset_object_id'] and settings['additional_asset_temporal_role'] is None)
        api_fields={'Angle Threshold':'angleThreshold','Boundary Tolerance':'boundaryTolerance','Minimum Face Group Size':'minimumFaceGroupSize'}
        for role,binding in settings['scalar_bindings'].items():
            prop=api_fields[role]
            if binding['is_active']:
                observed=api[prop]
                check(archive+' '+role+' active API parameter reciprocal name/role/unit/value', observed['name']==binding['parameter_name'] and observed['role']==role and observed['unit']==binding['display_units'] and observed['value']==binding['stored_value'] and observed['createdBy']['name']==row['name'])
                check(archive+' '+role+' requested input real equals actual parameter', actual['input_before_add'][prop]['realValue']==binding['stored_value'])
            else:
                check(archive+' '+role+' inactive API not invoked, native value retained separately', api[prop] is None and api[prop+'_status'].startswith('Inactive') and binding['stored_value'] is not None)
        native=meshes['decoded'][0];geometry=native['geometry']
        observed_mesh=actual['component_meshes_after_face_groups']['meshes'][0]
        original=observed_mesh['original_polygon_mesh']
        check(archive+' actual current source name agrees before cache comparison', observed_mesh['name']==native['name'])
        check(archive+' exact ordered API triangle indices match native asset', original['triangleNodeIndices']==geometry['triangle_node_indices'])
        points=[x for p in geometry['component_node_coordinates_cm'] for x in p]
        discrepancy=max(abs(a-b) for a,b in zip(points,original['nodeCoordinatesAsDouble']))
        check(archive+' ordered component coordinates corroborate actual API', len(points)==len(original['nodeCoordinatesAsDouble']) and discrepancy<1e-7, maximum_coordinate_discrepancy_cm=discrepancy)
        cache=settings['triangle_face_groups'];groups=cache['decoded_triangle_face_group_temporary_ids']
        check(archive+' exact ordered group tempIDs match actual API', groups==original['triangleFaceGroupTempIds'] and len(groups)==original['triangleCount']==8)
        differences=cache['stored_int32_forward_differences']
        check(archive+' complete buffer5 byte replay exact', struct.pack('<8i',*differences).hex()==cache['stored_payload_hex']==geometry['buffers'][5]['uncompressed_payload_hex'])
        check(archive+' generic geometry keeps auxiliary buffer5 unresolved', 5 in geometry['unresolved_buffers'])
        check(archive+' API prior mesh group IDs zero', actual['component_meshes_before_face_groups']['meshes'][0]['original_polygon_mesh']['triangleFaceGroupTempIds']==[0]*8)
        check(archive+' native decoding mutates neither existing features nor mesh summary', features==feature_before and meshes==mesh_before)
        samples.append(dict(archive=archive,expected_decoded=result,expected_mesh_contents=meshes,
            actual_API_ordered_triangle_face_group_temporary_ids=groups,
            actual_API_active_control_fields=api['active_control_fields'],
            exact_ordered_triangle_indices_equal=True, maximum_coordinate_discrepancy_cm=discrepancy))
        if actual['case']=='fast_twenty_degrees': saved=(data,records,features,member,members,meshes)
    counts={Path(s['archive']).stem:s['expected_decoded']['decoded'][0]['settings']['triangle_face_groups']['distinct_temporary_id_count'] for s in samples}
    check('Independent Fast20/Fast80 angle contrast changes temporary group cache8to1', counts['fast_twenty_degrees']==8 and counts['fast_eighty_degrees']==1)
    check('Accurate method independently corroborates8 temporary groups', counts['accurate_boundary_point_zero_zero_one']==8)
    data,records,features,member,members,meshes=saved
    record=next(r for r in records if r.is_primary and r.class_guid==FACE_GROUPS)
    binding=next(r for r in records if r.is_primary and r.object_id==265)
    def guard(label, mutate=None, mesh_mutate=None):
        bad_data=bytearray(data);bad_mesh=copy.deepcopy(meshes)
        if mutate:mutate(bad_data)
        if mesh_mutate:mesh_mutate(bad_mesh)
        result=decode_mesh_face_groups(bytes(bad_data),records,features,member,members,bad_mesh)
        check(label, not result['decoded'] and len(result['unresolved'])==1)
        guards.append(dict(guard=label,reason=result['unresolved'][0]['reason']))
    guard('Reject uncaptured method2',lambda d:struct.pack_into('<I',d,record.body+35,2))
    guard('Reject repeated dependency count mismatch',lambda d:struct.pack_into('<I',d,record.body+156,4))
    guard('Reject scalar binding owner mismatch',lambda d:d.__setitem__(binding.body+7,2))
    guard('Reject missing selected current mesh',mesh_mutate=lambda m:m.__setitem__('decoded',[]))
    guard('Reject buffer5 descriptor without difference flag',mesh_mutate=lambda m:m['decoded'][0]['geometry']['buffers'][5].__setitem__('descriptor_hex','81a15401'))
    guard('Reject buffer5 decompression prefix-only status',mesh_mutate=lambda m:m['decoded'][0]['geometry']['buffers'][5].__setitem__('decompression_scope','Declared-size prefix only'))
    guard('Reject unobserved group-ID pattern',mesh_mutate=lambda m:m['decoded'][0]['geometry']['buffers'][5].__setitem__('uncompressed_payload_hex',struct.pack('<8i',*([1]*7+[9])).hex()))
    old=json.loads((root/'mesh-decoding.json').read_text())
    for item in old['samples']:
        args=load(root,item['archive'],zstd);d,r,f,n,m=args
        mesh=decode_mesh_contents_variants(d,r,n,m)
        check(item['archive']+' original strict mesh full dictionary unchanged',mesh==item['expected_decoded'])
        empty=decode_mesh_face_groups(d,r,f,n,m,mesh)
        check(item['archive']+' no unrelated FaceGroups diagnostics',not empty['decoded'] and not empty['unresolved'])
        controls.append(dict(archive=item['archive'],expected_mesh_contents=mesh))
    return dict(interface='decode_mesh_face_groups(data,records,features,member,members,mesh_contents=None) -> decoded/unresolved/scope; rows feature_object_id/kind/name/settings',
        sample_count=3,decoded_feature_count=3,ordered_triangle_temporary_id_count=24,check_count=len(checks),malformed_guard_count=len(guards),
        capture=CAPTURE,executed_generator_sha256=truth['executed_generator_sha256'],
        actual_terminal_journal=journal[-1],actual_document_close_journals=closes,
        samples=samples,old_controls=controls,checks=checks,malformed_guards=guards,
        limitations=['Only observed Fast20/80 and Accurate0.001cm controls admitted; inactive values retained as inactive',
            'Buffer5 interpretation bounded to observed6-node/8-triangle same-asset caches and two output patterns',
            'Triangle array order directly corroborated only for these actual saved API captures',
            'Temporary IDs are not persistent native geometry IDs; no regeneration algorithm',
            'Additional stored asset lifecycle and remaining buffers unqualified',
            'Generic geometry auxiliary diagnostics unchanged'],
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'decode_mesh_face_groups.py','validate_mesh_face_groups.py','GenerateMeshFaceGroupContrasts.py',
            'decode_mesh_contents.py','decode_mesh_geometry_variants.py','decode_mesh_selections.py','decode_parameters.py')})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='mesh-face-group-decoding.json');args=parser.parse_args()
    result=validate(Path(__file__).resolve().parent,args.zstd_library);Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('sample_count','decoded_feature_count','check_count','malformed_guard_count')}))

if __name__=='__main__':main()
