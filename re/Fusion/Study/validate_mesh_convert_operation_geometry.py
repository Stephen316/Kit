"""Owned result routes/current-prefix recovery and collective BRep evidence."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_base_feature_single_lists import decode_base_feature_single_lists
from decode_mesh_convert import decode_mesh_convert
from decode_mesh_convert_inputs import decode_mesh_convert_inputs
from decode_mesh_convert_result_bodies import decode_mesh_convert_result_bodies
from decode_mesh_current_prefix import decode_mesh_current_prefix
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_normals import decode_mesh_normal_pools
from decode_mesh_face_group_caches import decode_mesh_face_group_caches
from validate_mesh_remesh import load
from validate_mesh_normals import _direction_error

CAPTURE='meshconvertoperations-5af73924aa60'


def rounded(values):return [round(value,12) for value in values]


def graph_bundle(graph):
    if not graph['body_transform_is_identity']:raise ValueError('Convert result cached BODY transform is not identity')
    if not all(s['geometry']['kind']=='Plane' for s in graph['analytic_surfaces']):raise ValueError('Convert result cache outside planar facets')
    return dict(vertex_count=graph['counts']['vertex'],edge_count=graph['counts']['edge'],face_count=graph['counts']['face'],
        unordered_vertices_cm=sorted(rounded(v) for v in graph['raw_vertex_positions']),
        unordered_plane_origin_normal_pairs=sorted((rounded(s['geometry']['raw_origin']),rounded(s['geometry']['normal'])) for s in graph['analytic_surfaces']))


def api_bundle(body):
    if not all(f['geometry']['objectType']=='adsk::core::Plane' for f in body['faces']):raise ValueError('Convert API result outside planar facets')
    return dict(vertex_count=len(body['vertices']),edge_count=len(body['edges']),face_count=len(body['faces']),
        unordered_vertices_cm=sorted(rounded(v['position_cm']) for v in body['vertices']),
        unordered_plane_origin_normal_pairs=sorted((rounded(f['geometry']['origin']),rounded(f['geometry']['normal'])) for f in body['faces']))


def multiset(bundles):return sorted(json.dumps(bundle,sort_keys=True,separators=(',',':')) for bundle in bundles)


def validate(root,zstd):
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text())
    journal=[json.loads(line) for line in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks,samples,controls,guards=[],[],[],[]
    def check(label,condition,**fields):
        if not condition:raise AssertionError(label)
        checks.append(dict(check=label,**fields))
    check('Actual3captures complete with no case errors',(root/CAPTURE/'complete.txt').is_file() and len(truth['samples'])==3 and truth['errors']==[] and journal[-1]['phase']=='batch_complete')
    closes=[r for r in journal if r['phase']=='owned_document_close_returned']
    check('Actual3owned closeFalse returned true',len(closes)==3 and all(r['returned'] is True and r['save'] is False for r in closes))
    check('Exact executed generator snapshot hash',hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file'];args=load(root,archive,zstd);data,records,features,member,members=args
        original_hash=hashlib.sha256(data).hexdigest();meshes=decode_mesh_contents_variants(data,records,member,members)
        multi=decode_mesh_convert_inputs(*args)
        base=decode_base_feature_single_lists(data,records,features)
        is_base=actual['case'].startswith('base_feature')
        check(archive+' export hash exact',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        check(archive+' input handle equality actually recorded',actual['input_body_equals_import_handles'] is True)
        if is_base:
            check(archive+' null return independent of new BRep count',actual['add_returned_nonnull'] is False and actual['actual_returned_identity'] is None and actual['component_brep_before_convert']['count']==0 and actual['component_brep_after_convert']['count']==1)
            check(archive+' native partialBaseFeature300 independently decoded',len(base['partial'])==1 and not base['unresolved'] and not multi['decoded'])
            definition=base['partial'][0];feature_id=definition['feature_object_id'];anchor_ids=definition['result_anchor_object_ids']
            routes=decode_mesh_convert_result_bodies(data,records,member,members,feature_id,anchor_ids)
            check(archive+' explicit result and stored body table identities distinct',definition['stored_body_table_object_ids']==[306] and routes['result_native_body_object_ids']==[312] and definition['source_mesh_object_id'] is None)
            check(archive+' component derived from BODYcollection, suppliedargumentexact',routes['result_body_component_object_id']==3 and routes==decode_mesh_convert_result_bodies(data,records,member,members,feature_id,anchor_ids,3))
            check(archive+' one current nativeMesh still counted independently',len(meshes['decoded'])==1 and not meshes['unresolved'] and actual['component_meshes_after_convert']['count']==1)
            native=meshes['decoded'][0];proof=native['native_current_prefix_membership']
            check(archive+' alternateprefix proves current singleton/BaseMeshowner without flag meanings',proof['stored_current_collection_member_ids']==[native['mesh_object_id']]==[213] and proof['reciprocal_base_mesh_feature_object_id']==218 and proof['component_object_id']==3)
            polygon=actual['component_meshes_after_convert']['meshes'][0]['original_polygon_mesh']
            check(archive+' current mesh API arrays exact after native identity fixed',[v for p in native['geometry']['component_node_coordinates_cm'] for v in p]==polygon['nodeCoordinatesAsDouble'] and native['geometry']['triangle_node_indices']==polygon['triangleNodeIndices'])
        else:
            check(archive+' one two-input native Parametric feature/noBasepartial',len(multi['decoded'])==1 and not multi['unresolved'] and not base['partial'])
            settings=multi['decoded'][0]['settings'];feature_id=multi['decoded'][0]['feature_object_id'];anchor_ids=settings['result_anchor_object_ids']
            routes=decode_mesh_convert_result_bodies(data,records,member,members,feature_id,anchor_ids,settings['qualified_source_meshes'][0]['component_object_id'])
            check(archive+' two independent results and no source/resultpairing',routes['result_native_body_object_ids']==[377,384] and settings['source_to_result_pairing'] is None and len(settings['qualified_source_meshes'])==2)
            check(archive+' no current native mesh; retained warnings exact',not meshes['decoded'] and meshes['unresolved']==[dict(mesh_object_id=i,reason='Unobserved opt-in native mesh prefix') for i in (213,226)] and actual['component_meshes_after_convert']['count']==0)
            for source in settings['qualified_source_meshes']:
                matched=[m for m in actual['component_meshes_before_convert']['meshes'] if m['name']==source['name']]
                check(archive+' source'+str(source['mesh_object_id'])+' explicit retained mesh and API source name',source['retained_membership_status']=='NotInCountedMembers' and source['retained_owner_collection_member_ids']==[] and len(matched)==1)
                p=matched[0]['original_polygon_mesh']
                check(archive+' source'+str(source['mesh_object_id'])+' source arrays corroborate without resultpairing',[v for point in source['geometry']['component_node_coordinates_cm'] for v in point]==p['nodeCoordinatesAsDouble'] and source['geometry']['triangle_node_indices']==p['triangleNodeIndices'])
        check(archive+' collection and native mapping fullbytes replay',routes['result_collection_provenance']['exact_collection_and_mapping_replay'] is True)
        mapping=routes['stored_asm_body_identifiers']['decoded'][0]
        parsed=inspect_asm(members[mapping['history_blob_member']]);topology=decode_topology(parsed)
        check(archive+' explicit sameblob initialBODY mapping fully parsed',parsed['complete_token_stream'] is True and len(mapping['bindings'])==len(routes['result_native_body_object_ids']))
        bundles=[]
        for binding in mapping['bindings']:
            matches=[g for g in topology['body_graphs'] if g['body_index']==binding['asm_body_index']]
            check(archive+' nativeBODY'+str(binding['native_body_object_id'])+' storedhandle/ASMrootunique',len(matches)==1 and binding['asm_stored_entity_id']==binding['stored_handle'])
            bundles.append(graph_bundle(matches[0]))
        api_bodies=actual['component_brep_after_convert']['bodies'];api_bundles=[api_bundle(body) for body in api_bodies]
        check(archive+' complete BRep result-data multiset corroborates API collectively',multiset(bundles)==multiset(api_bundles))
        check(archive+' collective result proof invariant to API ordering',multiset(bundles)==multiset(list(reversed(api_bundles))))
        normals=decode_mesh_normal_pools(meshes);groups=decode_mesh_face_group_caches(meshes)
        check(archive+' current normal/group helpers have no errors',not normals['unresolved'] and not groups['unresolved'])
        if is_base:
            api=actual['component_meshes_after_convert']['meshes'][0];flat=api['display_triangle_mesh']['normalVectorsAsDouble'];vectors=[flat[i:i+3] for i in range(0,len(flat),3)]
            error=_direction_error(normals['decoded'][0]['derived_asset_unit_vectors'],vectors)
            check(archive+' existing current normal directions and ordered labels corroborate API',error<1e-7 and groups['decoded'][0]['decoded_triangle_face_group_temporary_ids']==api['original_polygon_mesh']['triangleFaceGroupTempIds'])
        check(archive+' native bytes untouched',hashlib.sha256(data).hexdigest()==original_hash)
        samples.append(dict(archive=archive,feature_object_id=feature_id,result_anchor_object_ids=anchor_ids,
            expected_result_body_routes=routes,expected_mesh_contents=meshes,expected_normal_pools=normals,
            expected_face_group_caches=groups,expected_prior_mesh_diagnostics=copy.deepcopy(meshes['unresolved']),
            actual_API_result_BRep_data_multiset=api_bundles,
            result_geometry_comparison_scope='Native BODY mapping established by explicit anchors/collection/ASM stored IDs first. Complete geometric result bundles compared collectively as an unordered multiset at12decimal numerical precision; no per-native-ID API identity or per-source/result pairing.',
            native_API_result_assignment=None))
        if actual['case']=='base_feature_closed':guard_context=(args,feature_id,anchor_ids,routes)
    # Old complete Convert summaries/current warnings remain exact.
    old=json.loads((root/'mesh-convert-decoding.json').read_text())
    for sample in old['samples']:
        args=load(root,sample['archive'],zstd)
        check(sample['archive']+' legacy full Convert dictionary exact',decode_mesh_convert(*args)==sample['expected_decoded'])
        mesh=decode_mesh_contents_variants(args[0],args[1],args[3],args[4])
        check(sample['archive']+' legacy current mesh diagnostics/fullsummary exact',mesh==sample['prior_mesh_contents'])
        controls.append(dict(archive=sample['archive'],old_Convert_and_mesh_dictionaries_exact=True))
    args,feature_id,anchor_ids,routes=guard_context;data,records,features,member,members=args
    mapping_id=routes['native_history_mapping']['mapping_record_object_id'];mapping=next(r for r in records if r.is_primary and r.object_id==mapping_id)
    collection=next(r for r in records if r.is_primary and r.object_id==routes['result_body_collection_object_id'])
    def guard(label,mutate=None,anchors=None,component=None):
        bad=bytearray(data)
        if mutate:mutate(bad)
        try:decode_mesh_convert_result_bodies(bytes(bad),records,member,members,feature_id,anchor_ids if anchors is None else anchors,component)
        except (ValueError,IndexError,KeyError,struct.error) as error:reason=str(error)
        else:raise AssertionError(label)
        check(label,True);guards.append(dict(guard=label,reason=reason))
    guard('Reject duplicate result anchor IDs',anchors=anchor_ids*2)
    guard('Reject supplied unrelated component',component=9999)
    guard('Reject native handle absent from ASM BODY table',lambda d:struct.pack_into('<Q',d,mapping.body+6,31))
    guard('Reject repeated collection BODY reference mismatch',lambda d:struct.pack_into('<Q',d,collection.end-21,306))
    # Prefix qualification deliberately leaves retained source failures identical.
    for archive in ('meshconvertoperations-5af73924aa60/two_mesh_parametric.f3d','meshconverts-4b42d39fb1d5/faceted_closed.f3d','meshcombines-541ebb6cc93f/join.f3d'):
        args=load(root,archive,zstd);d,r,_,_,_=args;identity=226 if 'meshcombines-' in archive else 213
        record=next(x for x in r if x.is_primary and x.object_id==identity)
        try:decode_mesh_current_prefix(d,r,identity,d[record.body:record.body+22])
        except ValueError as error:reason=str(error)
        else:raise AssertionError('Retained source unexpectedly current')
        check(archive+' retains exact old prefix diagnostic',reason=='Unobserved opt-in native mesh prefix')
        guards.append(dict(guard=archive+' retainedsourceprefix',reason=reason))
    return dict(sample_count=3,qualified_result_BODY_count=4,recovered_current_mesh_count=2,
        check_count=len(checks),malformed_guard_count=len(guards),samples=samples,legacy_controls=controls,
        checks=checks,malformed_guards=guards,actual_terminal_journal=journal[-1],actual_document_close_journal=closes,
        limitations=['Null BaseFeature operation return alone does not prove conversion; typed partial definition/owned result anchors and independent API BRep collection retained separately',
            'BaseFeature stored-tableBODY306 and anchoredBODY312 remain distinct without PM/DM identity inference',
            'Alternative mesh packed prefix accepted only with reciprocal counted current membership/component/BaseMesh proof; retained warnings unchanged',
            'Result cache comparisons are unordered collective data, no native/API per-result assignment',
            'Mesh source lists and BRep result lists remain independent; no source/result matching by order/geometry',
            'ASM stored IDs are local to explicitly referenced history blobs, not global identities or ordinals',
            'No conversion algorithm, lifecycle, current visibility or regeneration claim'],
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'validate_mesh_convert_operation_geometry.py','decode_mesh_convert_result_bodies.py','decode_mesh_current_prefix.py',
            'decode_mesh_convert_inputs.py','decode_base_feature_single_lists.py','decode_mesh_contents.py',
            'decode_mesh_geometry_variants.py','decode_body_asm_identifiers.py')})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='mesh-convert-operation-geometry-decoding.json');args=parser.parse_args()
    result=validate(Path(__file__).resolve().parent,args.zstd_library);Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('sample_count','qualified_result_BODY_count','recovered_current_mesh_count','check_count','malformed_guard_count')}))

if __name__=='__main__':main()
