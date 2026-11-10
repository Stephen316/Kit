"""Singleton Thread-family routes, cached analytic geometry and plural preservation."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_thread_families import decode_thread_families
from decode_thread_body_routes import resolve_thread_multi_faces,qualify_thread_body_routes
from decode_thread_family_body_routes import resolve_thread_family_faces,qualify_thread_family_body_routes,SCOPE
from validate_mesh_remesh import load
from validate_thread_body_routes import native_bundle,api_bundle,multiset

CAPTURE='threadfamilies-459264fae49b'


def validate(root,zstd):
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text())
    journal=[json.loads(line) for line in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks,samples,controls,guards=[],[],[],[]
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    check('Actual three exports complete/no case errors',(root/CAPTURE/'complete.txt').is_file() and len(truth['samples'])==3 and not truth['errors'] and journal[-1]['terminal_status']=='Complete')
    closes=[r for r in journal if r['phase']=='owned_document_close_returned']
    check('Three owned closeFalse returnedTrue',len(closes)==3 and all(r['returned'] is True and r['save'] is False for r in closes))
    check('Executed generator snapshot hash',hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file'];data,records,features,member,members=load(root,archive,zstd);before=copy.deepcopy(features)
        early=decode_thread_families(data,records,features)
        check(archive+' independent controls and native singleton callback decoded',len(early['decoded'])==1 and not early['unresolved'])
        row=early['decoded'][0];evidence=row['settings']['selection_evidence'];fid=row['feature_object_id']
        qualified=qualify_thread_family_body_routes(data,records,member,members,evidence)
        check(archive+' archive SHA',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        check(archive+' exact singleton proxy/descriptor/BODY list',len(evidence['selection_record_object_ids'])==len(evidence['descriptor_object_ids'])==len(evidence['historical_native_body_object_ids'])==1 and evidence['historical_native_body_object_ids']==evidence['native_current_body_object_ids'])
        source=evidence['owned_face_source_routes'][0];face=source['face_selection'];context=source['typed_context']
        check(archive+' context/recipe/anchor explicit identity agreement',context['descriptor_recipe']==face['recipe'] and context['native_body_object_id']==face['native_body_object_id'] and context['body_anchor_object_id']==face['body_anchor_object_id'] and context['optional_context_recipe_route'] is None)
        check(archive+' historical seedowner remains distinct from Thread',face['source_owner_object_id']!=fid and face['recipe']['payload_kind']=='bounded_face_recipe_data')
        check(archive+' source and mapping literal replay retained',evidence['layout']['exact_selection_and_mapping_replay'] is True)
        check(archive+' identity unknowns remain explicit',qualified['selected_asm_face_object_ids'] is None and qualified['native_API_face_assignment'] is None and qualified['source_to_result_pairing'] is None)
        check(archive+' API preadd equality and rolled inequality retained',actual['input_faces_equal_selected_handles'] is True and actual['feature_input_faces_equal_selected_handles'] is False)
        check(archive+' invalid original selected handle retained',all(f['isValid'] is False and f['cylinder'] is None for f in actual['selected_faces_before_node']))
        check(archive+' rolled getter independently returns valid source cylinder',len(actual['feature_before_node']['inputCylindricalFaces'])==1 and actual['feature_before_node']['inputCylindricalFaces'][0]['isValid'] is True)
        mapping=qualified['stored_asm_body_identifiers']['decoded'][0];parsed=inspect_asm(members[mapping['history_blob_member']]);topology=decode_topology(parsed)
        check(archive+' sameasset initial ASM complete',parsed['complete_token_stream'] is True and len(mapping['bindings'])==1)
        binding=mapping['bindings'][0];graphs=[g for g in topology['body_graphs'] if g['body_index']==binding['asm_body_index']]
        check(archive+' explicit native handle to typed initial ASM BODY',len(graphs)==1 and binding['stored_handle']==binding['asm_stored_entity_id'] and binding['native_body_object_id']==face['native_body_object_id'])
        graph=graphs[0];native=[native_bundle(graph)];api=[api_bundle(b) for b in actual['component_bodies_after_thread']['bodies']]
        check(archive+' complete observed geometry bundle corroborates current API',multiset(native)==multiset(api))
        native_flags=[sorted((s['geometry']['kind'],s['face_is_reversed']) for s in graph['analytic_surfaces'])]
        api_flags=[sorted((f['geometry_object_type'].split('::')[-1],f['isParamReversed']) for f in b['faces']) for b in actual['component_bodies_after_thread']['bodies']]
        internal=actual['requested']['internal']
        check(archive+' raw reversal observations retained without semantic equivalence',(multiset(native_flags)==multiset(api_flags)) is (not internal))
        check(archive+' caller feature dictionaries untouched',features==before)
        samples.append(dict(archive=archive,feature_object_id=fid,expected_selection_evidence=evidence,
            expected_body_route=qualified,expected_body_routes_summary=dict(decoded=[qualified],unresolved=[],scope=SCOPE),
            actual_API_current_geometry_bundles=api,native_API_body_assignment=None,
            actual_input_faces_equal_selected_handles=actual['input_faces_equal_selected_handles'],
            actual_feature_input_faces_equal_selected_handles=actual['feature_input_faces_equal_selected_handles'],
            native_stored_surface_face_reversal_multiset=native_flags,actual_API_surface_param_reversal_multiset=api_flags,
            reversal_multisets_equal=multiset(native_flags)==multiset(api_flags),
            geometry_scope='Explicit historical source anchor, reciprocal counted BODY collection and stored native/ASM IDs qualify native identity first; current vertices, topology counts, analytic kinds and cylinder parameters corroborate the complete API collection as an unordered data multiset. No selected ASMface/API identity assignment. Plane origin/normal absent in API; stored face/API param reversal literal flags kept separate.'))
        saved=(data,records,features,member,members,fid,evidence)
    # Reuse exact frozen prior plural dictionaries, not new self-generated expectations.
    old=json.loads((root/'thread-body-route-decoding.json').read_text())
    for sample in old['samples']:
        data,records,features,member,members=load(root,sample['archive'],zstd);expected=sample['expected_selection_evidence'];fid=expected['feature_object_id']
        record=next(r for r in records if r.is_primary and r.object_id==fid);feature=next(f for f in features if f['object_id']==fid)
        evidence=resolve_thread_multi_faces(data,records,data[record.body:record.end],feature,expected['selection_start_offset'])
        qualified=qualify_thread_body_routes(data,records,member,members,evidence)
        check(sample['archive']+' old plural native evidence/full qualified dictionaries exact',evidence==expected and qualified==sample['expected_body_route'])
        controls.append(dict(archive=sample['archive'],old_complete_evidence_and_qualified_body_route_exact=True))
    data,records,features,member,members,fid,evidence=saved
    record=next(r for r in records if r.is_primary and r.object_id==fid);feature=next(f for f in features if f['object_id']==fid);cursor=evidence['selection_start_offset']
    def guard(label,mutate=None,alter=None,missing_blob=False,plural=False):
        bad=bytearray(data)
        if mutate:mutate(bad)
        phase='PureNativeSelection'
        try:
            resolver=resolve_thread_multi_faces if plural else resolve_thread_family_faces
            fresh=resolver(bytes(bad),records,bytes(bad[record.body:record.end]),feature,cursor)
            phase='LateASMQualification'
            if alter:alter(fresh)
            own=dict(members)
            if missing_blob:own.pop(member.rsplit('/FusionDesignSegmentType1/',1)[0]+'/Breps.BlobParts/'+fresh['stored_history_filename'])
            qualify_thread_family_body_routes(bytes(bad),records,member,own,fresh)
        except (ValueError,KeyError,IndexError,struct.error,UnicodeError) as error:reason=str(error)
        else:raise AssertionError(label)
        checks.append(label);guards.append(dict(guard=label,phase=phase,reason=reason))
    guard('Reject two-proxy list in bounded singleton callback',lambda b:struct.pack_into('<I',b,record.body+cursor,2))
    guard('Old plural callback still rejects singleton with exact old diagnostic',plural=True)
    check('Exact old plural count rejection preserved',guards[-1]['reason']=='Only captured two-proxy Thread source layout supported')
    descriptor=next(r for r in records if r.is_primary and r.object_id==evidence['descriptor_object_ids'][0])
    guard('Reject descriptor/feature owner mismatch',lambda b:struct.pack_into('<Q',b,descriptor.end-10,fid+1))
    mapping=next(r for r in records if r.is_primary and r.object_id==evidence['native_history_mapping']['mapping_record_object_id'])
    guard('Pure frame succeeds but unknown ASMhandle fails late',lambda b:struct.pack_into('<Q',b,mapping.body+6,99999))
    guard('Reject altered late native evidence',alter=lambda e:e.__setitem__('historical_native_body_object_ids',[]))
    guard('Pure frame succeeds but missing sameasset blob fails late',missing_blob=True)
    sourcefiles=('decode_thread_body_routes.py','decode_thread_family_body_routes.py','validate_thread_family_body_routes.py','decode_thread_families.py','decode_threads.py','validate_thread_body_routes.py')
    return dict(sample_count=3,selected_source_count=3,qualified_BODY_count=3,check_count=len(checks),malformed_guard_count=len(guards),samples=samples,legacy_controls=controls,checks=checks,malformed_guards=guards,
        actual_document_close_journal=closes,actual_terminal_journal=journal[-1],
        old_plural_golden_report_sha256=hashlib.sha256((root/'thread-body-route-decoding.json').read_bytes()).hexdigest(),
        capture_provenance=dict(capture_directory=CAPTURE,executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],sdk_runtime_sha256=truth['sdk_runtime_sha256']),
        source_sha256={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in sourcefiles},
        limitations=['Controls/family labels/units independently decoded by A; source routes do not infer physical units from labels',
            'Singleton historical source anchors and current counted membership are distinct stored facts',
            'Stored initial ASM BODY ID correspondence does not prove lifecycle or exact selected face identity',
            'Rolled original handles invalid and equalityFalse; returned input cylinders independently observed',
            'Current analytic geometry data agrees collectively; no API handle/token/ordinal identity pairing',
            'Internal literal native face flag/API param reversal differ without assumed equivalent semantics',
            'Plane geometry absent in API; no full surface cache evaluator, regeneration or general thread-family claim'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='thread-family-body-route-decoding.json');args=parser.parse_args()
    root=Path(__file__).resolve().parent
    z=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(root,z);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('sample_count','qualified_BODY_count','check_count','malformed_guard_count')}))

if __name__=='__main__':main()
