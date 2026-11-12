"""Split sheet role/new-anchor/current-set proof and collective API geometry."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_split_body_sheet_tools import decode_split_body_sheet_tools
from decode_split_body_sheet_routes import resolve_split_body_sheet_tool,qualify_split_body_sheet_routes,SCOPE
from decode_replace_face_body_routes import resolve_replace_face_target,qualify_replace_face_body_routes
from validate_mesh_remesh import load
from validate_mesh_convert_operation_geometry import graph_bundle,multiset
from validate_replace_face_body_routes import api_bundle

CAPTURE='splitbodysheets-b7548618fb65'


def validate(root,zstd):
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text());journal=[json.loads(x) for x in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks,samples,controls,guards=[],[],[],[]
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    check('Actual three healthy exports/terminal/errors empty',(root/CAPTURE/'complete.txt').is_file() and len(truth['samples'])==3 and not truth['errors'] and journal[-1]['terminal_status']=='Complete')
    closes=[j for j in journal if j['phase']=='owned_document_close_returned']
    check('Three owned closeFalse returnedTrue',len(closes)==3 and all(j['returned'] is True and j['save'] is False for j in closes))
    check('Executed generator snapshot hash',hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file'];data,records,features,member,members=load(root,archive,zstd);before=copy.deepcopy(features)
        early=decode_split_body_sheet_tools(data,records,features)
        check(archive+' independent common controls/tool callback decoded',len(early['decoded'])==1 and not early['unresolved'])
        row=early['decoded'][0];settings=row['settings'];tool=settings['tool'];evidence=tool['native_evidence']
        qualified=qualify_split_body_sheet_routes(data,records,member,members,evidence)
        check(archive+' actual archive SHA',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        expected=actual['requested']['splitting_tool_argument_type']
        check(archive+' actual API/native representations independently agree in corpus',tool['entity']['kind']==expected and actual['exact_createInput_arguments']['splitting_tool_argument_type']=='adsk::fusion::'+expected and actual['feature_before_node']['splittingTool']['actual_type_branch']==expected)
        check(archive+' extension flag common/API agree',settings['is_tool_extended']==actual['requested']['isSplittingToolExtended']==actual['feature_before_node']['isSplittingToolExtended'])
        check(archive+' historical source/tool identities distinct',evidence['source_historical_native_body_object_id']==275 and evidence['tool_historical_native_body_object_id']==379 and evidence['source_body_route']['descriptor']['source_owner_object_id']==243)
        check(archive+' one input source versus three current BODYs distinct',settings['input_body_count']==1 and evidence['source_body_route']['descriptor']['context_record_object_ids']==[] and len(evidence['native_current_body_collection']['body_object_ids'])==3 and actual['component_bodies_after_split']['count']==3)
        check(archive+' operation flag echoed through explicit owned toolproxy',evidence['tool_route']['selection']['attributes']=={'DcFeatureOperationIdFlag':settings['stored_operation_flag']})
        new_id=1010 if expected=='BRepBody' else 997
        check(archive+' per-target new anchor uniquely owned by Splitfeature',evidence['newly_owned_native_body_object_ids']==[new_id] and evidence['per_target_record_object_ids']==settings['per_target_record_object_ids'] and len(evidence['newly_owned_result_anchors'])==1 and evidence['newly_owned_result_anchors'][0]['source_owner_object_id']==row['feature_object_id'])
        check(archive+' current set contains historicalsource/tool/newanchorBODY',set(evidence['native_current_body_collection']['body_object_ids'])=={275,379,new_id})
        check(archive+' no selected ASMface/API or source/result identity assignments',qualified['selected_tool_asm_face_id'] is None and qualified['native_API_body_assignment'] is None and qualified['source_to_result_pairing'] is None)
        mapping=qualified['stored_asm_body_identifiers']['decoded'][0];parsed=inspect_asm(members[mapping['history_blob_member']]);topology=decode_topology(parsed)
        check(archive+' complete sameasset ASM token stream',parsed['complete_token_stream'] is True)
        native=[]
        for binding in mapping['bindings']:
            graphs=[g for g in topology['body_graphs'] if g['body_index']==binding['asm_body_index']]
            check(archive+' BODY'+str(binding['native_body_object_id'])+' literal storedID root',len(graphs)==1 and binding['stored_handle']==binding['asm_stored_entity_id'])
            native.append(graph_bundle(graphs[0]))
        api=[api_bundle(b) for b in actual['component_bodies_after_split']['bodies']]
        check(archive+' complete current planar geometry matches API collectively',multiset(native)==multiset(api))
        check(archive+' collective comparison invariant to API collection order',multiset(native)==multiset(list(reversed(api))))
        check(archive+' auxBODY2 remains outside native current identity mapping',[(b['native_body_object_id'],b['asm_body_index']) for b in mapping['bindings']]==[(275,1),(379,3),(new_id,4)] and any(a['kind']=='body' and a['asm_record_index']==2 and a['stored_entity_id']==-1 for a in mapping['auxiliary_declared_roots']))
        check(archive+' source features untouched',features==before)
        samples.append(dict(archive=archive,feature_object_id=row['feature_object_id'],expected_native_evidence=evidence,
            expected_body_route=qualified,expected_body_routes_summary=dict(decoded=[qualified],unresolved=[],scope=SCOPE),
            actual_API_current_geometry_bundles=api,native_API_body_assignment=None,
            actual_requested_tool_type=actual['exact_createInput_arguments']['splitting_tool_argument_type'],actual_rolled_tool_type=actual['feature_before_node']['splittingTool']['actual_type_branch'],
            geometry_scope='Explicit source/tool historical anchors, separately Split-owned new anchor, reciprocal current BODYset and literal stored ASM IDs fix native identities before all three current complete planar bundles are compared as unordered data multisets at12decimals. No geometry chooses source/result/API identity; the current3 set includes the sheet and does not mean3 feature-owned results.'))
        if expected=='BRepBody':saved=(data,records,features,member,members,row,evidence)
    old=json.loads((root/'replace-face-body-route-decoding.json').read_text())
    for sample in old['samples']:
        data,records,features,member,members=load(root,sample['archive'],zstd);evidence=sample['expected_native_evidence'];feature=next(f for f in features if f['object_id']==sample['feature_object_id'])
        _,target=resolve_replace_face_target(data,records,evidence['target_selection_record_object_id'],feature,{})
        qualified=qualify_replace_face_body_routes(data,records,member,members,evidence)
        check(sample['archive']+' extracted reader preserves old full native+late dictionaries',target['native_evidence']==evidence and qualified==sample['expected_body_route'])
        controls.append(dict(archive=sample['archive'],old_full_native_and_late_dicts_exact=True))
    prior=json.loads((root/'split-decoding.json').read_text())
    for sample in prior['decodings']:
        data,records,features,member,members=load(root,sample['file'],zstd);summary=decode_split_body_sheet_tools(data,records,features)
        check(sample['file']+' prior plane Split family not falsely classified',not summary['decoded'] and not summary['unresolved'])
        controls.append(dict(archive=sample['file'],new_sheet_family_no_false_match=True))
    data,records,features,member,members,row,evidence=saved;fid=row['feature_object_id'];feature=next(f for f in features if f['object_id']==fid);record=next(r for r in records if r.is_primary and r.object_id==fid)
    def guard(label,mutation=None,alter=None):
        bad=bytearray(data)
        if mutation:mutation(bad)
        phase='PureNativeRoles'
        try:
            tool=resolve_split_body_sheet_tool(bytes(bad),records,evidence['tool_selection_record_object_id'],feature,{})
            phase='LateASMQualification';fresh=tool['native_evidence']
            if alter:alter(fresh)
            qualify_split_body_sheet_routes(bytes(bad),records,member,members,fresh)
        except (ValueError,KeyError,IndexError,UnicodeError,struct.error) as error:reason=str(error)
        else:raise AssertionError(label)
        checks.append(label);guards.append(dict(guard=label,phase=phase,reason=reason))
    guard('Reject operationflag disagrees with owned toolproxy',lambda b:struct.pack_into('<Q',b,record.body+22,row['settings']['stored_operation_flag']+1))
    guard('Reject per-target anchor replaced by historicalsource anchor',lambda b:struct.pack_into('<Q',b,record.body+54,281))
    definition=next(r for r in records if r.is_primary and r.object_id==evidence['definition_record_object_id'])
    guard('Reject definition reciprocalowner mismatch',lambda b:struct.pack_into('<Q',b,definition.body+41,fid+1))
    leafid=evidence['tool_route']['typed_context']['body_identity_leaf_object_id'];leaf=next(r for r in records if r.is_primary and r.object_id==leafid)
    guard('Reject tool contextleaf referring to sourceBODY',lambda b:struct.pack_into('<Q',b,leaf.body+2,275))
    mapping=next(r for r in records if r.is_primary and r.object_id==evidence['native_history_mapping_object_id'])
    guard('Pure native roles pass but unknown ASMhandle fails late',lambda b:struct.pack_into('<Q',b,mapping.body+6,99999))
    guard('Reject tampered late owned-result identities',alter=lambda e:e.__setitem__('newly_owned_native_body_object_ids',[]))
    qualified=qualify_split_body_sheet_routes(data,records,member,members,evidence);own=dict(members);own.pop(qualified['native_history_mapping']['history_blob_member'])
    try:qualify_split_body_sheet_routes(data,records,member,own,evidence)
    except ValueError as error:reason=str(error)
    else:raise AssertionError('Missing blob accepted')
    checks.append('Reject missing explicitly referenced sameasset blob');guards.append(dict(guard=checks[-1],phase='LateASMQualification',reason=reason))
    sources=('decode_split_body_sheet_routes.py','decode_owned_surface_selection.py','decode_replace_face_body_routes.py','validate_split_body_sheet_routes.py','decode_split_body_sheet_tools.py','decode_split.py','decode_body_bindings.py','decode_body_asm_identifiers.py')
    return dict(sample_count=3,historical_source_route_count=3,historical_tool_route_count=3,new_owned_BODY_count=3,qualified_stored_BODY_count=9,
        check_count=len(checks),malformed_guard_count=len(guards),samples=samples,legacy_controls=controls,checks=checks,malformed_guards=guards,
        actual_document_close_journal=closes,actual_terminal_journal=journal[-1],
        capture_provenance=dict(capture_directory=CAPTURE,executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],sdk_runtime_sha256=truth['sdk_runtime_sha256']),
        old_ReplaceFace_golden_report_sha256=hashlib.sha256((root/'replace-face-body-route-decoding.json').read_bytes()).hexdigest(),
        source_sha256={s:hashlib.sha256((root/s).read_bytes()).hexdigest() for s in sources},
        limitations=['One selected historical sourceBODY differs from three currentBODYs including the independent sheet',
            'Only one new currentBODY has an explicit Split-owned anchor; originalsource and tool retain distinct historical owners',
            'Native face/body tool distinctions retained independently from requested and rolled API representation',
            'Definition58byte ownerbacklink and raw fields validated without inventing topology-operation semantics',
            'ASM auxiliary BODY2 unassigned; explicit current handles resolve roots1/3/4 without ordinal guessing',
            'Complete planar current geometry bundles agree API collectively; no native/API tempID/token/name/ordinal identity or persistentface assignment',
            'No Split extension solver, historical lifecycle, current visibility or regeneration claim'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='split-body-sheet-route-decoding.json');args=parser.parse_args()
    root=Path(__file__).resolve().parent;z=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(root,z);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('sample_count','qualified_stored_BODY_count','check_count','malformed_guard_count')}))

if __name__=='__main__':main()
