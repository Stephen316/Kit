"""ReplaceFace role provenance and collective saved planar geometry evidence."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_replace_face_targets import decode_replace_face_targets
from decode_replace_face_body_routes import resolve_replace_face_target,qualify_replace_face_body_routes,SCOPE
from validate_mesh_remesh import load
from validate_mesh_convert_operation_geometry import graph_bundle,multiset,rounded

CAPTURE='replacefacetargets-670e35eedbc8'


def api_bundle(body):
    faces=body['faces'];edges={e['tempId'] for f in faces for e in f['edges']}
    if not all(f['geometry']['objectType']=='adsk::core::Plane' for f in faces):raise ValueError('Outside captured planar ReplaceFace family')
    return dict(vertex_count=len(body['vertices']),edge_count=len(edges),face_count=len(faces),
        unordered_vertices_cm=sorted(rounded(v['position_cm']) for v in body['vertices']),
        unordered_plane_origin_normal_pairs=sorted((rounded(f['geometry']['origin']),rounded(f['geometry']['normal'])) for f in faces))


def validate(root,zstd):
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text());journal=[json.loads(x) for x in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks,samples,controls,guards=[],[],[],[]
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    check('Actual terminal3exports/errors empty',(root/CAPTURE/'complete.txt').is_file() and len(truth['samples'])==3 and not truth['errors'] and journal[-1]['terminal_status']=='Complete')
    closes=[j for j in journal if j['phase']=='owned_document_close_returned']
    check('All3owned closeFalse returnedTrue',len(closes)==3 and all(j['returned'] is True and j['save'] is False for j in closes))
    check('Exact executed generator source hash',hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file'];data,records,features,member,members=load(root,archive,zstd);before=copy.deepcopy(features)
        early=decode_replace_face_targets(data,records,features)
        check(archive+' early common controls and target callback success',len(early['decoded'])==1 and not early['unresolved'])
        row=early['decoded'][0];settings=row['settings'];target=settings['replacement_target'];evidence=target['native_evidence']
        qualified=qualify_replace_face_body_routes(data,records,member,members,evidence)
        check(archive+' exact archive hash',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        check(archive+' distinct historical source/target/feature ownership',evidence['source_historical_native_body_object_id']==275 and evidence['replacement_historical_native_body_object_id']==379 and evidence['source_face_route']['face']['source_owner_object_id']==243 and evidence['replacement_target_route'].get('face',evidence['replacement_target_route'].get('descriptor'))['source_owner_object_id']==344)
        check(archive+' source role remains one owned face recipe',evidence['source_face_route']['face']['recipe']['payload_kind']=='bounded_face_recipe_data' and settings['source_descriptor_object_ids']==[evidence['source_face_route']['face']['descriptor_object_id']])
        expected=actual['requested']['target_argument_type']
        check(archive+' requested native target representation recorded independently',target['kind']==expected and actual['exact_createInput_arguments']['target_argument_type']=='adsk::fusion::'+expected)
        rolled=actual['feature_before_node']['targetFaces']
        check(archive+' actual rolled target getter shape retained',rolled['actual_type_branch']==('BRepBody' if expected=='BRepBody' else 'Collection'))
        check(archive+' source APIgetter scope is input only','No public feature.sourceFaces getter' in actual['feature_before_node']['sourceFaces_scope'] and 'sourceFaces' in actual['input_before_add'])
        if expected=='BRepBody':
            context=evidence['replacement_target_route']['typed_context']
            check(archive+' body naming context typedleaf repeats anchoredBODY',context['leaf_native_body_object_id']==379 and evidence['replacement_target_route']['descriptor']['native_body_object_id']==379 and evidence['replacement_target_route']['recipe']['payload_kind']=='body_recipe_data')
        else:
            check(archive+' face target context recipe independently qualified',evidence['replacement_target_route']['face']['recipe']['payload_kind']=='face_recipe_data' and evidence['replacement_target_route']['typed_context']['native_body_object_id']==379)
        check(archive+' tangent flag agrees actual input/getter',settings['is_tangent_chain']==actual['requested']['isTangentChain']==actual['feature_before_node']['isTangentChain'])
        check(archive+' current collection records both historical roles',evidence['native_current_body_collection']['body_object_ids']==[275,379] and actual['component_bodies_after_replace']['count']==2)
        check(archive+' exact ASMface/API/result assignments stay unknown',qualified['selected_source_asm_face_id'] is None and qualified['selected_replacement_asm_face_id'] is None and qualified['native_API_body_assignment'] is None and qualified['source_to_result_pairing'] is None)
        mapping=qualified['stored_asm_body_identifiers']['decoded'][0];parsed=inspect_asm(members[mapping['history_blob_member']]);topology=decode_topology(parsed)
        check(archive+' complete sameasset ASM tokens',parsed['complete_token_stream'] is True)
        native=[]
        for binding in mapping['bindings']:
            graphs=[g for g in topology['body_graphs'] if g['body_index']==binding['asm_body_index']]
            check(archive+' BODY'+str(binding['native_body_object_id'])+' explicit stored handle root',len(graphs)==1 and binding['stored_handle']==binding['asm_stored_entity_id'])
            native.append(graph_bundle(graphs[0]))
        api=[api_bundle(b) for b in actual['component_bodies_after_replace']['bodies']]
        check(archive+' complete planar geometry bundles corroborate API collectively',multiset(native)==multiset(api))
        check(archive+' geometry corroboration independent of API ordering',multiset(native)==multiset(list(reversed(api))))
        check(archive+' auxiliary BODY remains distinct from replacement stored ID',[(b['native_body_object_id'],b['asm_body_index']) for b in mapping['bindings']]==[(275,1),(379,3)] and any(a['kind']=='body' and a['asm_record_index']==2 and a['stored_entity_id']==-1 for a in mapping['auxiliary_declared_roots']))
        check(archive+' feature dictionaries not mutated',features==before)
        samples.append(dict(archive=archive,feature_object_id=row['feature_object_id'],expected_native_evidence=evidence,
            expected_body_route=qualified,expected_body_routes_summary=dict(decoded=[qualified],unresolved=[],scope=SCOPE),
            actual_API_current_geometry_bundles=api,native_API_body_assignment=None,
            actual_requested_target_type=actual['exact_createInput_arguments']['target_argument_type'],actual_rolled_target_getter_branch=rolled['actual_type_branch'],
            actual_source_faces_getter_scope=actual['feature_before_node']['sourceFaces_scope'],
            geometry_scope='Explicit source and replacement descriptors/anchors, reciprocal collection and native stored ASM IDs fix native identities first. Complete planar vertex/edge/face counts, vertices and plane-origin/normal bundles compared collectively as unordered data multisets at12decimals. No API tempID/token/name/ordinal body pairing or persistent selected face identity; current membership is not feature-result ownership.'))
        if expected=='BRepBody':saved=(data,records,features,member,members,row,evidence)
    old=json.loads((root/'face-edit-decoding.json').read_text())
    for prior in old['decodings']:
        data,records,features,_,_=load(root,prior['file'],zstd);summary=decode_replace_face_targets(data,records,features)
        check(prior['file']+' old face-edit families not falsely matched',not summary['decoded'] and not summary['unresolved'])
        controls.append(dict(archive=prior['file'],no_false_new_target_classification=True))
    data,records,features,member,members,row,evidence=saved;fid=row['feature_object_id'];feature=next(f for f in features if f['object_id']==fid)
    record=next(r for r in records if r.is_primary and r.object_id==fid)
    def guard(label,mutate=None,alter=None,target_id=None):
        bad=bytearray(data)
        if mutate:mutate(bad)
        phase='PureNativeRoles'
        try:
            _,target=resolve_replace_face_target(bytes(bad),records,evidence['target_selection_record_object_id'] if target_id is None else target_id,feature,{})
            phase='LateASMQualification';fresh=target['native_evidence']
            if alter:alter(fresh)
            own=dict(members)
            qualify_replace_face_body_routes(bytes(bad),records,member,own,fresh)
        except (ValueError,KeyError,IndexError,UnicodeError,struct.error) as error:reason=str(error)
        else:raise AssertionError(label)
        checks.append(label);guards.append(dict(guard=label,phase=phase,reason=reason))
    guard('Reject swapped source/target operand',target_id=evidence['source_selection_record_object_id'])
    descriptor=next(r for r in records if r.is_primary and r.object_id==row['settings']['target_descriptor_object_ids'][0])
    guard('Reject target descriptor owner mismatch',lambda b:struct.pack_into('<Q',b,descriptor.end-10,fid+1))
    context=evidence['replacement_target_route']['typed_context'];leaf=next(r for r in records if r.is_primary and r.object_id==context['body_identity_leaf_object_id'])
    guard('Reject contextleaf selecting other historical sourceBODY',lambda b:struct.pack_into('<Q',b,leaf.body+2,275))
    mapping=next(r for r in records if r.is_primary and r.object_id==evidence['native_history_mapping_object_id'])
    guard('Pure roleframe passes but absent ASMhandle rejected late',lambda b:struct.pack_into('<Q',b,mapping.body+6,99999))
    guard('Reject tampered late source role',alter=lambda e:e.__setitem__('source_historical_native_body_object_id',379))
    # Remove actual explicit blob after proving ordinary native roles again.
    q=qualify_replace_face_body_routes(data,records,member,members,evidence);actual_blob=q['native_history_mapping']['history_blob_member']
    absent=dict(members);absent.pop(actual_blob)
    try:qualify_replace_face_body_routes(data,records,member,absent,evidence)
    except ValueError as error:reason=str(error)
    else:raise AssertionError('Missing blob accepted')
    checks.append('Reject missing explicitly named sameasset blob');guards.append(dict(guard=checks[-1],phase='LateASMQualification',reason=reason))
    sources=('decode_replace_face_body_routes.py','validate_replace_face_body_routes.py','decode_replace_face_targets.py','decode_face_tools.py','decode_face_selections.py','decode_body_selections.py','decode_body_bindings.py','decode_body_asm_identifiers.py')
    return dict(sample_count=3,historical_source_BODY_route_count=3,historical_replacement_BODY_route_count=3,
        qualified_stored_BODY_count=6,check_count=len(checks),malformed_guard_count=len(guards),samples=samples,legacy_controls=controls,checks=checks,malformed_guards=guards,
        actual_document_close_journal=closes,actual_terminal_journal=journal[-1],
        capture_provenance=dict(capture_directory=CAPTURE,executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],sdk_runtime_sha256=truth['sdk_runtime_sha256']),
        source_sha256={s:hashlib.sha256((root/s).read_bytes()).hexdigest() for s in sources},
        limitations=['Current role BODY membership does not establish ReplaceFace-owned result anchors or lifecycle',
            'Historical source and independent Patch replacement kept distinct; no source/result ordinal matching',
            'Face API target and body API target have distinct native representations in this corpus',
            'Feature sourceFaces has no public getter; actual input-only source observation retained',
            'BODY379 uses stored ASMrecord3; auxiliary unnumbered BODYrecord2 stays unassigned',
            'Complete current planar geometry collectively corroborates API without per-body native/API identity or selected-face mapping',
            'No general ReplaceFace surface solver, tangent regeneration or persistent topology identity'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='replace-face-body-route-decoding.json');args=parser.parse_args()
    root=Path(__file__).resolve().parent;z=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(root,z);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('sample_count','qualified_stored_BODY_count','check_count','malformed_guard_count')}))

if __name__=='__main__':main()
