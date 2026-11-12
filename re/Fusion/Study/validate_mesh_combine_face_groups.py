"""Three actual CombineFaceGroups selections, metadata bridge and order contrast."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from decode_mesh_combine_face_groups import decode_mesh_combine_face_groups, _asset_group_names, COMBINE_GROUPS
from decode_mesh_face_group_caches import decode_mesh_face_group_caches
from decode_mesh_face_groups import decode_mesh_face_groups
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from validate_mesh_remesh import load

CAPTURE='meshcombinefacegroups-33142f03b86e'


def validate(root,zstd):
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text())
    journal=[json.loads(line) for line in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks,samples,guards,controls=[],[],[],[]
    def check(label,condition,**fields):
        if not condition:raise AssertionError(label)
        checks.append(dict(check=label,**fields))
    check('Actual complete3 exports without case errors',(root/CAPTURE/'complete.txt').is_file() and truth['terminal_status']=='complete' and len(truth['samples'])==3 and truth['errors']==[])
    closes=[r for r in journal if r['phase']=='owned_document_close_returned']
    check('Owned closeFalse returned true3times',len(closes)==3 and all(r['returned'] is True and r['save'] is False for r in closes))
    check('Exact executed generator source snapshot hash',hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    check('Exact SDK surface snapshot hash',hashlib.sha256((root/CAPTURE/truth['sdk_surface_snapshot']).read_bytes()).hexdigest()==truth['sdk_surface_snapshot_sha256'])
    check('Actual terminal journal agrees with captures',journal[-1]['phase']=='batch_terminal' and journal[-1]['sample_count']==3 and journal[-1]['error_count']==0)
    by_case={}
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file']
        args=load(root,archive,zstd);data,records,features,member,members=args
        meshes=decode_mesh_contents_variants(data,records,member,members);before=copy.deepcopy(meshes)
        result=decode_mesh_combine_face_groups(*args,mesh_contents=meshes)
        check(archive+' exactly one observed feature/no unresolved',len(result['decoded'])==1 and not result['unresolved'])
        check(archive+' actual archive exporthash',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        row=result['decoded'][0];settings=row['settings'];api=actual['feature_before_node']
        check(archive+' actual feature class/name/healthy agree',api['objectType']=='adsk::fusion::MeshCombineFaceGroupsFeature' and row['name']==api['name'] and api['healthState']==0 and api['errorOrWarningMessage']=='')
        check(archive+' direct actual input mesh equality and group ownership',actual['input_targetBaseFeature'] is None and api['mesh_equals_expected_source'] is True and all(g['parentBody_equals_expected_mesh'] is True for g in actual['selection_proof']['selected_groups']))
        selected=actual['selection_proof']['selected_temporary_ids'];count=len(selected)
        check(archive+' native asset namespace labels corroborate actual selected temporary labels',settings['selected_asset_group_labels']==selected)
        check(archive+' before-add submitted handle matrix identity',actual['inputFaceGroups_before_add']['ordered_equals_submitted']==[[i==j for j in range(count)] for i in range(count)])
        rolled=api['inputFaceGroups']
        check(archive+' rolled actual group temporary labels/parent mesh agree', [g['tempId'] for g in rolled['groups']]==selected and all(g['parentBody_equals_expected_mesh'] is True for g in rolled['groups']))
        check(archive+' original and rolled handles compare unequal, no persistence assumption',rolled['ordered_equals_submitted']==[[False]*count for _ in range(count)])
        check(archive+' native feature fullpayload byte replay proved',settings['layout']['exact_full_payload_replay'] is True and bytes.fromhex(settings['layout']['stored_feature_body_hex'])==data[settings['layout']['feature_body_offset']:settings['layout']['feature_body_end_offset']])
        check(archive+' typed current mesh source/asset agrees',len(meshes['decoded'])==1 and not meshes['unresolved'] and meshes['decoded'][0]['mesh_object_id']==settings['native_mesh_object_id']==settings['input_selection']['mesh_object_id'] and meshes['decoded'][0]['asset_object_id']==settings['current_mesh_asset']['asset_object_id'])
        check(archive+' independent native BaseMesh owner retained',settings['current_mesh_native_feature_owner_object_id']==meshes['decoded'][0]['feature_object_id'] and settings['current_mesh_native_feature_owner_object_id']!=row['feature_object_id'])
        for table_key in ('current_asset_group_namespace','additional_asset_group_namespace'):
            table=settings[table_key]
            check(archive+' '+table_key+' exact unique8label/UUID table',{entry['stored_asset_group_label'] for entry in table['entries']}==set(range(1,9)) and len({entry['stored_asset_group_uuid'] for entry in table['entries']})==8)
        check(archive+' selected orderedUUIDs distinct and leading repeatslast',len(set(settings['stored_selected_asset_group_uuids']))==count and settings['stored_leading_asset_group_uuid']==settings['stored_selected_asset_group_uuids'][-1])
        native=meshes['decoded'][0];geometry=native['geometry'];api_mesh=actual['component_meshes_after_combine_groups']['meshes'][0]
        original=api_mesh['original_polygon_mesh']
        check(archive+' exact current triangle index order',geometry['triangle_node_indices']==original['triangleNodeIndices'])
        check(archive+' exact current ordered coordinate array',[v for point in geometry['component_node_coordinates_cm'] for v in point]==original['nodeCoordinatesAsDouble'])
        cache=decode_mesh_face_group_caches(meshes)
        check(archive+' exact current ordered API group IDs',cache['decoded'][0]['decoded_triangle_face_group_temporary_ids']==original['triangleFaceGroupTempIds'] and cache['decoded'][0]==settings['current_triangle_face_groups'])
        check(archive+' actual preparation group array retained separately',actual['component_meshes_before_combine_groups']['meshes'][0]['original_polygon_mesh']['triangleFaceGroupTempIds']==list(range(1,9)))
        preparation=decode_mesh_face_groups(*args,mesh_contents=meshes)
        check(archive+' old preparatory current-asset diagnostic remains scoped',not preparation['decoded'] and len(preparation['unresolved'])==1 and preparation['unresolved'][0]['reason']=='FaceGroups selected mesh current asset route unresolved')
        check(archive+' existing hierarchy and mesh diagnostics not mutated',meshes==before)
        samples.append(dict(archive=archive,expected_decoded=result,expected_mesh_contents=meshes,
            expected_face_group_caches=cache,expected_preparatory_face_groups=preparation,
            actual_API_selected_temporary_ids=selected,actual_API_output_triangle_group_temporary_ids=original['triangleFaceGroupTempIds'],
            actual_before_add_handle_matrix=actual['inputFaceGroups_before_add']['ordered_equals_submitted'],
            actual_rolled_handle_matrix=rolled['ordered_equals_submitted'],
            identity_scope='Typed mesh selection plus exact same-asset label/UUID table precedes API temporary-label comparison. Original and rolled group handles are not claimed persistent.'))
        by_case[actual['case']]=settings
        if actual['case']=='adjacent_pair':saved=(args,meshes,result)
    a,b,c=[by_case[name] for name in ('adjacent_pair','adjacent_pair_reversed','connected_triple')]
    check('Actual reversed selection order changes observed resulting cache labels',a['selected_asset_group_labels']==[1,2] and b['selected_asset_group_labels']==[2,1] and a['current_triangle_face_groups']['decoded_triangle_face_group_temporary_ids']==[2,2,3,4,5,6,7,8] and b['current_triangle_face_groups']['decoded_triangle_face_group_temporary_ids']==[1,1,3,4,5,6,7,8])
    check('Actual connected triple observed output retained without general algorithm',c['selected_asset_group_labels']==[1,2,4] and c['current_triangle_face_groups']['decoded_triangle_face_group_temporary_ids']==[4,4,3,4,5,6,7,8])
    args,meshes,result=saved;data,records,features,member,members=args
    record=next(r for r in records if r.is_primary and r.class_guid==COMBINE_GROUPS)
    selection=result['decoded'][0]['settings']['input_selection'];proxy=next(r for r in records if r.is_primary and r.object_id==selection['proxy_object_id'])
    def guard(label,mutate=None,feature_mutate=None):
        bad=bytearray(data);named=copy.deepcopy(features)
        if mutate:mutate(bad)
        if feature_mutate:feature_mutate(named)
        rejected=decode_mesh_combine_face_groups(bytes(bad),records,named,member,members,meshes)
        check(label,not rejected['decoded'] and len(rejected['unresolved'])==1)
        guards.append(dict(guard=label,reason=rejected['unresolved'][0]['reason']))
    guard('Reject unsupported selected count4',lambda d:struct.pack_into('<I',d,record.body+64,4))
    guard('Reject leading UUID disagreement',lambda d:d.__setitem__(record.body+6,ord('a') if d[record.body+6]!=ord('a') else ord('b')))
    guard('Reject selected UUID duplicate',lambda d:d.__setitem__(slice(record.body+72,record.body+108),d[record.body+112:record.body+148]))
    guard('Reject typed selection owner backlink mismatch',lambda d:struct.pack_into('<Q',d,proxy.end-10,9999))
    guard('Reject duplicated discovery feature identity',feature_mutate=lambda fs:fs.append(copy.deepcopy(next(f for f in fs if f['object_id']==record.object_id))))
    # The pure namespace parser receives an already-qualified explicit asset;
    # mutations test its independent exact table and unique-key grammar.
    asset=result['decoded'][0]['settings']['current_mesh_asset']
    def table_guard(label,mutate):
        bad=copy.deepcopy(asset);metadata=bytes.fromhex(bad['geometry']['stored_metadata_hex'])
        bad['geometry']['stored_metadata_hex']=mutate(metadata).hex()
        try:_asset_group_names(bad)
        except (ValueError,UnicodeError,struct.error) as error:reason=str(error)
        else:raise AssertionError(label)
        check(label,True);guards.append(dict(guard=label,reason=reason))
    entries=result['decoded'][0]['settings']['current_asset_group_namespace']['entries']
    table_guard('Reject duplicate metadata groupUUID',lambda raw:raw.replace(entries[1]['stored_asset_group_uuid'].encode(),entries[0]['stored_asset_group_uuid'].encode()))
    table_guard('Reject duplicate metadata numericlabel',lambda raw:raw.replace(bytes.fromhex('322808')+bytes([entries[1]['stored_asset_group_label']]),bytes.fromhex('322808')+bytes([entries[0]['stored_asset_group_label']]),1))
    table_guard('Reject metadata namespace descriptor variant',lambda raw:raw.replace(bytes.fromhex('080712027232'),bytes.fromhex('080712027233'),1))
    old=json.loads((root/'mesh-face-group-decoding.json').read_text())
    for sample in old['samples']:
        args=load(root,sample['archive'],zstd);mesh=decode_mesh_contents_variants(args[0],args[1],args[3],args[4])
        check(sample['archive']+' prior GenerateFaceGroups dictionaries exact',decode_mesh_face_groups(*args,mesh_contents=mesh)==sample['expected_decoded'])
        empty=decode_mesh_combine_face_groups(*args,mesh_contents=mesh)
        check(sample['archive']+' new helper empty outside native Combine class',not empty['decoded'] and not empty['unresolved'])
        controls.append(dict(archive=sample['archive'],prior_GenerateFaceGroups_dictionary_exact=True))
    return dict(interface='decode_mesh_combine_face_groups(data,records,features,member,members,mesh_contents=None)',
        sample_count=3,decoded_feature_count=3,selected_asset_group_key_count=7,current_triangle_temporary_label_count=24,
        check_count=len(checks),malformed_guard_count=len(guards),samples=samples,old_controls=controls,
        checks=checks,malformed_guards=guards,actual_terminal_journal=journal[-1],actual_document_close_journal=closes,
        capture=CAPTURE,executed_generator_sha256=truth['executed_generator_sha256'],
        limitations=['Ordered selectedUUIDs resolve only inside explicit native selected-mesh asset metadata namespaces',
            'Temporary labels and groupUUIDs are not promoted to persistent native geometry identity',
            'Before-add handle identity holds; rollback handles all compare unequal despite matching temporary labels',
            'Observed reversed-input order effect is recorded, no universal merge-survivor algorithm inferred',
            'Additional asset temporal role unqualified; metadata table entries may have no current triangle occurrence',
            'Old preparatory GenerateFaceGroups current-asset diagnostic intentionally preserved',
            'No regeneration, history replay or lifecycle claim'],
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'decode_mesh_combine_face_groups.py','validate_mesh_combine_face_groups.py','GenerateMeshCombineFaceGroupContrasts.py',
            'decode_mesh_contents.py','decode_mesh_geometry_variants.py','decode_mesh_selections.py','decode_mesh_face_group_caches.py')})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='mesh-combine-face-group-decoding.json');args=parser.parse_args()
    result=validate(Path(__file__).resolve().parent,args.zstd_library);Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('sample_count','decoded_feature_count','check_count','malformed_guard_count')}))

if __name__=='__main__':main()
