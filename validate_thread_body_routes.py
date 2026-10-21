"""Focused plural Thread native identity routes and collective saved geometry proof."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_parameters import read_string
from decode_extrude import optional_reference
from decode_threads import decode_thread
from decode_thread_body_routes import THREAD,SCOPE,resolve_thread_multi_faces,qualify_thread_body_routes
from validate_mesh_remesh import load

CAPTURE='threadmultifaces-e4bc4a120fbf'


def cursor_for(body):
    cursor=15+16*struct.unpack_from('<I',body,11)[0]
    for _ in range(5):_,cursor=read_string(body,cursor)
    _,cursor=optional_reference(body,cursor+38)
    return cursor+22+41


def rounded(v):return [round(x,12) for x in v]


def native_bundle(graph):
    if not graph['body_transform_is_identity']:raise ValueError('Nonidentity Thread BODY cache unsupported')
    surfaces=graph['analytic_surfaces']
    if len(surfaces)!=graph['counts']['face'] or any(s['geometry']['kind'] not in ('Cylinder','Plane') for s in surfaces):raise ValueError('Outside captured analytic Thread surface family')
    return dict(vertex_count=graph['counts']['vertex'],edge_count=graph['counts']['edge'],face_count=graph['counts']['face'],
        unordered_vertices_cm=sorted(rounded(v) for v in graph['raw_vertex_positions']),
        unordered_surface_kinds=sorted(s['geometry']['kind'] for s in surfaces),
        unordered_cylinders=sorted((rounded(s['geometry']['raw_origin']),rounded(s['geometry']['axis']),round(s['geometry']['raw_radius'],12)) for s in surfaces if s['geometry']['kind']=='Cylinder'))


def api_bundle(body):
    edges={e['tempId'] for f in body['faces'] for e in f['edges']}
    return dict(vertex_count=len(body['vertices']),edge_count=len(edges),face_count=len(body['faces']),
        unordered_vertices_cm=sorted(rounded(v['position_cm']) for v in body['vertices']),
        unordered_surface_kinds=sorted(f['geometry_object_type'].split('::')[-1] for f in body['faces']),
        unordered_cylinders=sorted((rounded(f['cylinder']['origin']),rounded(f['cylinder']['axis']),round(f['cylinder']['radius_cm'],12)) for f in body['faces'] if f['cylinder'] is not None))


def multiset(values):return sorted(json.dumps(v,sort_keys=True) for v in values)


def validate(root,zstd):
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text())
    journal=[json.loads(line) for line in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks,samples,guards,controls=[],[],[],[]
    def check(name,value):
        if not value:raise AssertionError(name)
        checks.append(name)
    check('Actual terminal three exports/errors empty',(root/CAPTURE/'complete.txt').is_file() and len(truth['samples'])==3 and not truth['errors'] and journal[-1]['phase']=='batch_terminal' and journal[-1]['terminal_status']=='Complete')
    closes=[r for r in journal if r['phase']=='owned_document_close_returned']
    check('Three owned closeFalse returnedTrue',len(closes)==3 and all(r['returned'] is True and r['save'] is False for r in closes))
    check('Executed source snapshot hash',hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file'];data,records,features,member,members=load(root,archive,zstd)
        feature=next(f for f in features if f['class_guid']==THREAD);record=next(r for r in records if r.is_primary and r.object_id==feature['object_id'])
        body=data[record.body:record.end];before=copy.deepcopy(features);cursor=cursor_for(body)
        evidence=resolve_thread_multi_faces(data,records,body,feature,cursor)
        qualified=qualify_thread_body_routes(data,records,member,members,evidence)
        check(archive+' archive hash',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        check(archive+' two distinct singleton proxies/descriptors/historical bodies',len(set(evidence['selection_record_object_ids']))==len(set(evidence['descriptor_object_ids']))==len(set(evidence['historical_native_body_object_ids']))==2)
        check(archive+' native source order differs current collection order',evidence['historical_native_body_object_ids']==list(reversed(evidence['native_current_body_object_ids'])))
        check(archive+' typed contexts exactly match owned face recipes',all(r['typed_context']['descriptor_recipe']==r['face_selection']['recipe'] and r['typed_context']['native_body_object_id']==r['face_selection']['native_body_object_id'] for r in evidence['owned_face_source_routes']))
        check(archive+' all face recipes remain bounded opaque payloads',all(r['face_selection']['recipe']['payload_kind']=='bounded_face_recipe_data' and r['face_selection']['recipe']['uninterpreted_payload_int32'] for r in evidence['owned_face_source_routes']))
        check(archive+' full native source/mapping bytes replay',evidence['layout']['exact_selection_and_mapping_replay'] and bytes.fromhex(evidence['stored_selection_list_hex'])==body[cursor:evidence['selection_end_offset']])
        check(archive+' no ASMface or API assignment',qualified['selected_asm_face_object_ids'] is None and qualified['native_API_face_assignment'] is None and qualified['source_to_result_pairing'] is None)
        check(archive+' actual pre-add equal handles and rolled handle mismatch retained',actual['input_faces_equal_selected_handles'] is True and actual['feature_input_faces_equal_selected_handles'] is False)
        check(archive+' original selected handles invalid after roll',all(f['isValid'] is False and f['cylinder'] is None and f['getter_errors'] for f in actual['selected_faces_before_node']))
        check(archive+' rolled feature getter returns two valid cylinders',len(actual['feature_before_node']['inputCylindricalFaces'])==2 and all(f['isValid'] and f['cylinder'] for f in actual['feature_before_node']['inputCylindricalFaces']))
        check(archive+' end-timeline input getter error retained',any(e['getter']=='inputCylindricalFaces' and "roll" in e['error'] for e in actual['feature_at_timeline_end']['control_getter_errors']))
        mapping=qualified['stored_asm_body_identifiers']['decoded'][0]
        parsed=inspect_asm(members[mapping['history_blob_member']]);topology=decode_topology(parsed)
        check(archive+' same-asset ASM complete tokens',parsed['complete_token_stream'] is True)
        native=[];native_reversals=[]
        for binding in mapping['bindings']:
            graphs=[g for g in topology['body_graphs'] if g['body_index']==binding['asm_body_index']]
            check(archive+' BODY'+str(binding['native_body_object_id'])+' exact stored ID route',len(graphs)==1 and binding['stored_handle']==binding['asm_stored_entity_id'])
            native.append(native_bundle(graphs[0]));native_reversals.append(sorted((s['geometry']['kind'],s['face_is_reversed']) for s in graphs[0]['analytic_surfaces']))
        api=[api_bundle(b) for b in actual['component_bodies_after_thread']['bodies']]
        api_reversals=[sorted((f['geometry_object_type'].split('::')[-1],f['isParamReversed']) for f in b['faces']) for b in actual['component_bodies_after_thread']['bodies']]
        check(archive+' stored/API reversal comparison retained independently', (multiset(native_reversals)==multiset(api_reversals)) is (not actual['requested']['internal']))
        check(archive+' current analytic geometry data multiset corroborates API',multiset(native)==multiset(api))
        check(archive+' data comparison invariant to API collection order',multiset(native)==multiset(list(reversed(api))))
        check(archive+' caller features unchanged',before==features)
        summary=dict(decoded=[qualified],unresolved=[],scope=SCOPE)
        samples.append(dict(archive=archive,feature_object_id=feature['object_id'],expected_selection_evidence=evidence,
            expected_body_route=qualified,expected_body_routes_summary=summary,
            actual_API_current_geometry_bundles=api,native_API_body_assignment=None,
            native_stored_surface_face_reversal_multiset=native_reversals,actual_API_surface_param_reversal_multiset=api_reversals,
            reversal_multisets_equal=multiset(native_reversals)==multiset(api_reversals),
            reversal_comparison_scope='Literal stored face flag and API surface-param reversal are separately retained; no general semantic equivalence. Internal cylinder flags differ; not used for geometric agreement or identity.',
            actual_input_faces_equal_selected_handles=actual['input_faces_equal_selected_handles'],
            actual_feature_input_faces_equal_selected_handles=actual['feature_input_faces_equal_selected_handles'],
            actual_invalid_selected_face_handle_count=len(actual['selected_faces_before_node']),
            geometry_scope='Typed BODY anchors, reciprocal stored collection, literal mapping and initial ASM BODY IDs qualify native identities first. Current topology counts, vertices, analytic kinds and cylinders compare collectively as unordered bundles at12decimal precision. Plane origins/normals unavailable in saved API; exact selected ASMface and per-body API identities remain unresolved.'))
        saved=(data,records,features,member,members,feature,record,cursor,evidence)
    old=json.loads((root/'thread-decoding.json').read_text())
    for prior in old['decodings']:
        data,records,features,_,_=load(root,prior['file'],zstd)
        expected=[f for st in prior['streams'] for f in st['features'] if f['kind']=='Thread']
        for oldfeature in expected:
            feature=next(f for f in features if f['object_id']==oldfeature['object_id']);record=next(r for r in records if r.is_primary and r.object_id==feature['object_id'])
            decoded=decode_thread(data,records,data[record.body:record.end],feature)
            expected={**oldfeature['tool_settings'],'attached_hole_object_id':None}
            check(prior['file']+' historical singleton settings plus established null parent-hole field exact',decoded==expected)
            controls.append(dict(archive=prior['file'],feature_object_id=feature['object_id'],historical_settings_plus_established_null_parent_hole_exact=True,expected_settings=expected))
    data,records,features,member,members,feature,record,cursor,evidence=saved
    def guard(label,mutation=None,alter=None,missing_blob=False):
        bad=bytearray(data)
        if mutation:mutation(bad)
        phase='PureNativeSelection'
        try:
            fresh=resolve_thread_multi_faces(bytes(bad),records,bytes(bad[record.body:record.end]),feature,cursor)
            phase='LateASMQualification'
            if alter:alter(fresh)
            own=dict(members)
            if missing_blob:own.pop(member.rsplit('/FusionDesignSegmentType1/',1)[0]+'/Breps.BlobParts/'+fresh['stored_history_filename'])
            qualify_thread_body_routes(bytes(bad),records,member,own,fresh)
        except (ValueError,KeyError,IndexError,struct.error,UnicodeError) as error:reason=str(error)
        else:raise AssertionError(label)
        checks.append(label);guards.append(dict(guard=label,phase=phase,reason=reason))
    guard('Reject unobserved three-proxy count',lambda b:struct.pack_into('<I',b,record.body+cursor,3))
    first=evidence['selection_record_object_ids'][0]
    guard('Reject duplicate source proxy identities',lambda b:struct.pack_into('<Q',b,record.body+cursor+4+11+1,first))
    descriptor=next(r for r in records if r.is_primary and r.object_id==evidence['descriptor_object_ids'][0])
    guard('Reject descriptor owner backlink mismatch',lambda b:struct.pack_into('<Q',b,descriptor.end-10,feature['object_id']+1))
    context=evidence['owned_face_source_routes'][0]['typed_context'];cr=next(r for r in records if r.is_primary and r.object_id==context['context_object_id'])
    guard('Reject descriptor/context entity text disagreement',lambda b:b.__setitem__(cr.body+90,ord('0') if b[cr.body+90]!=ord('0') else ord('1')))
    mapping=next(r for r in records if r.is_primary and r.object_id==evidence['native_history_mapping']['mapping_record_object_id'])
    guard('Valid native framing rejects absent ASMhandle only late',lambda b:struct.pack_into('<Q',b,mapping.body+6,99999))
    guard('Reject tampered late historical BODY evidence',alter=lambda e:e.__setitem__('historical_native_body_object_ids',[]))
    guard('Valid native framing rejects missing sameasset blob late',missing_blob=True)
    sources=('decode_thread_body_routes.py','validate_thread_body_routes.py','decode_threads.py','decode_face_selections.py','decode_selection_context_recipes.py','decode_body_asm_identifiers.py')
    return dict(sample_count=3,selected_source_count=6,qualified_BODY_count=6,check_count=len(checks),malformed_guard_count=len(guards),
        samples=samples,legacy_controls=controls,checks=checks,malformed_guards=guards,
        capture_provenance=dict(capture_directory=CAPTURE,executed_generator_sha256=truth['executed_generator_sha256'],
            executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],sdk_runtime_sha256=truth['sdk_runtime_sha256']),
        actual_document_close_journal=closes,actual_terminal_journal=journal[-1],
        source_sha256={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in sources},
        limitations=['Two distinct singleton proxies, not a single proxy with a plural descriptor list',
            'Native source ordering differs from stored current BODY ordering; no ordinal source/result or API pairing',
            'Historical seed anchors and current counted membership are retained separately; initial ASM root is not a lifecycle claim',
            'Before-add input handles compare equal; after roll stored original selected handles are invalid and equality is false',
            'Current geometry bundles corroborate API collectively; exact selected ASM face remains unresolved',
            'Saved API omits plane origin/normal geometry; no full surface evaluator claim',
            'Internal native face flag and API param reversal differ; literals retained without equivalence or correction',
            'Cosmetic geometry resizing is observed, no thread regeneration or solver algorithm inferred'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='thread-body-route-decoding.json');args=parser.parse_args()
    root=Path(__file__).resolve().parent
    z=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(root,z);Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('sample_count','qualified_BODY_count','check_count','malformed_guard_count')}))

if __name__=='__main__':main()
