"""Two interrupted-batch Trim source exports; no uncaptured Line/cell semantics."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_asm_subtypes import decode_asm_subtypes
from decode_basics import decode_sketches
from decode_placement import decode_placement
from decode_brep import decode_topology
from decode_body_bindings import decode_body_bindings
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_surface_trim_tools import decode_surface_trim_tools
from decode_surface_trim_sources import resolve_surface_trim_source,SCOPE,TRIM
from decode_sketch import reference
from validate_mesh_remesh import load
from validate_mesh_convert_operation_geometry import graph_bundle,multiset
from validate_replace_face_body_routes import api_bundle

CAPTURES=(('surfacetrimtools-c507461585b5','sheet_face.f3d'),('surfacetrimtools-ce3c7e1c703e','sheet_body.f3d'))


def validate(root,zstd):
    checks,samples,guards,batches,controls=[],[],[],[],[]
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    contexts={}
    for capture,filename in CAPTURES:
        folder=root/capture;truth=json.loads((folder/'ground_truth.json').read_text());journal=[json.loads(x) for x in (folder/'journal.jsonl').read_text().splitlines()]
        progress=json.loads((folder/'progress.json').read_text())
        check(capture+' preserved PartialNoTerminalMarker',not(folder/'complete.txt').exists() and truth.get('terminal_status') is None and progress['phase']=='owned_document_close_returned')
        check(capture+' exactly one actual successful export/no recorded errors',len(truth['samples'])==1 and not truth['errors'] and truth['samples'][0]['file']==filename)
        closes=[j for j in journal if j['phase']=='owned_document_close_returned']
        check(capture+' valid owned closeFalse actualTrue',len(closes)==1 and closes[0]['save'] is False and closes[0]['returned'] is True)
        check(capture+' executed generator snapshot hash',hashlib.sha256((folder/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
        entrypoint=truth.get('entrypoint_provenance')
        if entrypoint:check(capture+' retry entrypoint source snapshot separately preserved',hashlib.sha256((folder/entrypoint['executed_snapshot']).read_bytes()).hexdigest()==entrypoint['sha256'])
        batches.append(dict(capture_directory=capture,status='PartialNoTerminalMarker',recorded_sample_count=1,recorded_error_count=0,
            actual_last_journal=journal[-1],actual_progress=progress,actual_owned_close_journal=closes,
            executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],
            entrypoint_provenance=entrypoint,execution_status_scope='Successful export and owned close observed; no terminalComplete marker or completed-batch claim. Process exit/crash cause not inferred from these saved artifacts.'))
        actual=truth['samples'][0];archive=capture+'/'+filename;data,records,features,member,members=load(root,archive,zstd)
        decode_sketches(data,records,features);decode_placement(data,records,features);before=copy.deepcopy(features)
        early=decode_surface_trim_tools(data,records,features)
        check(archive+' common codec and proven source callback succeed',len(early['decoded'])==1 and not early['unresolved'])
        row=early['decoded'][0];settings=row['settings'];tool=settings['tool'];source=tool['native_source_evidence'];fid=row['feature_object_id']
        source_row=dict(feature_object_id=fid,native_source_evidence=source,scope=SCOPE)
        check(archive+' export actualTrue and actualbyteshash',actual['export']['returned_success'] is True and hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        check(archive+' callback owner/proxy IDs match common frame',source['feature_object_id']==fid and source['tool_selection_record_object_id']==tool['selection_record_object_id']==settings['tool_selection']['selection_record_object_id'])
        expected=actual['requested']['trim_tool_argument_type']
        check(archive+' actual requested/input/rolled representations retained separately',tool['entity']['kind']==expected and actual['exact_createInput_tool_argument']['actual_type_branch']==expected and actual['input_actual_trimTool']['actual_type_branch']==expected and actual['feature_before_node']['trimTool']['actual_type_branch']==expected)
        route=source['source_route'];identity=route['face'] if route['kind']=='Face' else route['descriptor']
        check(archive+' canonical historical Patch/body/component source proof',identity['source_owner_object_id']==331 and identity['native_body_object_id']==source['historical_native_body_object_id']==366 and source['native_component_object_id']==3)
        if expected=='BRepFace':check(archive+' owned face recipe/context is explicit but persistentfaceunknown',route['face']['recipe']['payload_kind']=='face_recipe_data' and route['typed_context']['native_body_object_id']==366)
        else:check(archive+' owned body context identityleaf repeats anchored BODY',route['recipe']['payload_kind']=='body_recipe_data' and route['typed_context']['leaf_native_body_object_id']==366)
        check(archive+' selectedcell and ASMface/API assignment stay unresolved',source['selected_asm_face_id'] is None and source['native_API_source_assignment'] is None and 'unresolved' in source['cell_selection_status'] and 'undecoded' in settings['trim_cell_status'])
        # Canonical BODY mappings are independent report-only corroboration.
        mappings=decode_body_bindings(data,records,member,dict(streams=[dict(member=n) for n in members if n.endswith('.smbh')]))
        candidates=[m for m in mappings['decoded'] if 366 in [b['native_body_object_id'] for b in m['bindings']]]
        check(archive+' one canonical sameasset currentBODY mapping contains source',len(candidates)==1)
        identifiers=decode_body_asm_identifiers(data,records,member,members,dict(decoded=candidates))
        check(archive+' literal stored ASM BODY ID correspondence independently qualifies',len(identifiers['decoded'])==1 and not identifiers['unresolved'])
        mapping=identifiers['decoded'][0];raw=members[mapping['history_blob_member']];parsed=inspect_asm(raw);catalog=decode_asm_subtypes(raw,parsed=parsed);topology=decode_topology(parsed,subtype_catalog=catalog)
        check(archive+' catalogue-aware topology and tokens complete',parsed['complete_token_stream'] is True and not topology['unresolved'])
        native=[];source_bundle=None
        for binding in mapping['bindings']:
            matches=[g for g in topology['body_graphs'] if g['body_index']==binding['asm_body_index']]
            check(archive+' nativeBODY'+str(binding['native_body_object_id'])+' unique typed storedID route',len(matches)==1 and binding['stored_handle']==binding['asm_stored_entity_id'])
            bundle=graph_bundle(matches[0]);native.append(bundle)
            if binding['native_body_object_id']==366:source_bundle=bundle
        api=[api_bundle(body) for body in actual['component_bodies_after_trim']]
        check(archive+' all current planar bodies numerically corroborate APIcollectively',multiset(native)==multiset(api))
        check(archive+' complete sourcebody data corroborates recorded APItoolbody',source_bundle==api_bundle(actual['tool_body_before_trim']))
        check(archive+' native/ASM mappings avoid leading-root ordinals',[(b['native_body_object_id'],b['asm_body_index']) for b in mapping['bindings']]==[(278,3),(366,5)])
        check(archive+' no source or features mutated',features==before)
        samples.append(dict(archive=archive,feature_object_id=fid,capture_status='PartialNoTerminalMarker',expected_tool=tool,
            expected_source_row=source_row,expected_source_summary=dict(decoded=[source_row],unresolved=[],scope=SCOPE),
            actual_requested_tool_kind=actual['exact_createInput_tool_argument']['actual_type_branch'],actual_input_tool_kind=actual['input_actual_trimTool']['actual_type_branch'],actual_rolled_tool_kind=actual['feature_before_node']['trimTool']['actual_type_branch'],
            actual_API_selected_input_cell_indices=actual['selected_input_cell_indices'],native_cell_index_assignment=None,
            independent_current_BODY_ASM_evidence=dict(native_history_mapping=candidates[0],stored_asm_body_identifiers=identifiers,
                ASM_topology_unresolved=topology['unresolved'],native_source_body_planar_bundle=source_bundle,
                actual_API_source_body_planar_bundle=api_bundle(actual['tool_body_before_trim']),actual_API_current_planar_bundles=api,
                native_API_source_assignment=None,scope='Report-only canonical BODY/ASM stored-ID evidence after source identity is fixed by owned native selectors. Numerical source body and current body-set corroboration do not establish API handle/persistentface identity, native Trim selected-cell semantics, lifecycle or regeneration; production ASM outputs unchanged.')))
        contexts[expected]=(data,records,features,member,members,row,source)
    # Existing plane Trim family is retained by its original common parser.
    for archive in ('surfacebounds-ac801bb00fae/trim_positive.f3d','surfacebounds-ac801bb00fae/trim_negative.f3d'):
        data,records,features,_,_=load(root,archive,zstd);summary=decode_surface_trim_tools(data,records,features)
        check(archive+' old plane Trim not falsely matched by new wrapper',not summary['decoded'] and not summary['unresolved'])
        controls.append(dict(archive=archive,old_plane_family_no_false_match=True))
    def guard(label,context_kind,mutation=None,tool_override=None):
        data,records,features,member,members,row,source=contexts[context_kind];bad=bytearray(data)
        if mutation:mutation(bad,records,row,source)
        try:resolve_surface_trim_source(bytes(bad),records,source['tool_selection_record_object_id'] if tool_override is None else tool_override,row['feature_object_id'],features)
        except (ValueError,KeyError,IndexError,UnicodeError,struct.error) as error:reason=str(error)
        else:raise AssertionError(label)
        checks.append(label);guards.append(dict(guard=label,reason=reason))
    data,records,features,member,members,row,source=contexts['BRepFace'];feature_record=next(r for r in records if r.is_primary and r.object_id==row['feature_object_id']);target_id=reference(data[feature_record.body:feature_record.end],44)
    guard('Reject target proxy substituted for source operand','BRepFace',tool_override=target_id)
    def owner_mismatch(b,records,row,source):
        r=next(r for r in records if r.is_primary and r.object_id==source['tool_selection_record_object_id']);struct.pack_into('<Q',b,r.end-10,row['feature_object_id']+1)
    guard('Reject source proxy/feature owner mismatch','BRepFace',owner_mismatch)
    def descriptor_owner(b,records,row,source):
        r=next(r for r in records if r.is_primary and r.object_id==source['tool_descriptor_object_ids'][0]);struct.pack_into('<Q',b,r.end-10,row['feature_object_id']+1)
    guard('Reject source face descriptor/feature backlink mismatch','BRepFace',descriptor_owner)
    def leaf_alias(b,records,row,source):
        i=source['source_route']['typed_context']['body_identity_leaf_object_id'];r=next(r for r in records if r.is_primary and r.object_id==i);struct.pack_into('<Q',b,r.body+2,278)
    guard('Reject body context identityleaf selecting targetBODY','BRepBody',leaf_alias)
    def unknown_descriptor(b,records,row,source):
        unknown=next(r for r in records if r.is_primary and r.class_guid=='5A1BF548-241F-46FD-9FB5-E4B05126EB9D');proxy=next(r for r in records if r.is_primary and r.object_id==source['tool_selection_record_object_id']);struct.pack_into('<Q',b,proxy.body+7,unknown.object_id)
    guard('Reject unobserved nonface/nonbody source descriptor','BRepBody',unknown_descriptor)
    sourcefiles=('decode_surface_trim_sources.py','validate_surface_trim_sources.py','decode_surface_trim_tools.py','decode_surface_tools.py','decode_owned_surface_selection.py','decode_body_bindings.py','decode_body_asm_identifiers.py')
    return dict(sample_count=2,completed_batch_count=0,partial_without_terminal_batch_count=2,native_source_count=2,report_only_current_BODY_count=4,
        check_count=len(checks),malformed_guard_count=len(guards),samples=samples,capture_batches=batches,legacy_controls=controls,checks=checks,malformed_guards=guards,
        prepared_uncaptured_variants=[dict(kind='SketchLine',capture_status='NotCaptured',runtime_support=False)],
        source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sourcefiles},
        limitations=['Exactly two successful exports/owned closes from two PartialNoTerminalMarker batches; no completed batch claim or inferred crash cause',
            'SketchLine tool capture did not occur; explicitly unsupported in this source helper',
            'Source-only production output retains face/body tool representation and historical Patch BODY provenance',
            'Common target proxy/recipe remain independent; actual API cell indices are not decoded native cell IDs',
            'Selected-cell/keep-remove side semantics, exact selected ASMface, API handle identity and lifecycle unresolved',
            'Current planar body-set/source numerical corroboration is report-only; no production BODY/ASM outputs changed',
            'No additional live API calls, UI work, trim solver or regeneration'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='surface-trim-source-decoding.json');args=parser.parse_args()
    root=Path(__file__).resolve().parent;z=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(root,z);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('sample_count','partial_without_terminal_batch_count','check_count','malformed_guard_count')}))

if __name__=='__main__':main()
