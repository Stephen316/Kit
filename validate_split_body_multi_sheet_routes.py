"""Two-source Split sheet route groups and collective saved geometry proof."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_split_body_multi_sheet_tools import decode_split_body_multi_sheet_tools
from decode_split_body_multi_sheet_routes import resolve_split_body_multi_sheet_tool,qualify_split_body_multi_sheet_routes,SCOPE
from decode_split_body_sheet_routes import resolve_split_body_sheet_tool,qualify_split_body_sheet_routes
from decode_replace_face_body_routes import resolve_replace_face_target,qualify_replace_face_body_routes
from validate_mesh_remesh import load
from validate_mesh_convert_operation_geometry import graph_bundle,multiset
from validate_replace_face_body_routes import api_bundle

CAPTURE='splitbodymultisheets-c78bec32dc3f'


def validate(root,zstd):
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text());journal=[json.loads(x) for x in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks,samples,controls,guards=[],[],[],[]
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    check('Actual three exports/terminal/errors empty',(root/CAPTURE/'complete.txt').is_file() and len(truth['samples'])==3 and not truth['errors'] and journal[-1]['terminal_status']=='Complete')
    closes=[r for r in journal if r['phase']=='owned_document_close_returned']
    check('Three owned closeFalse returnedTrue',len(closes)==3 and all(r['returned'] is True and r['save'] is False for r in closes))
    check('Exact executed generator snapshot',hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file'];data,records,features,member,members=load(root,archive,zstd);before=copy.deepcopy(features)
        early=decode_split_body_multi_sheet_tools(data,records,features)
        check(archive+' common controls and bounded plural callback decoded',len(early['decoded'])==1 and not early['unresolved'])
        row=early['decoded'][0];settings=row['settings'];tool=settings['tool'];evidence=tool['native_evidence']
        qualified=qualify_split_body_multi_sheet_routes(data,records,member,members,evidence)
        check(archive+' actual archive hash',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        requested=actual['requested']['splitting_tool_argument_type']
        check(archive+' requested native and rolled tool representations independently observed',tool['entity']['kind']==requested and actual['feature_before_node']['splittingTool']['actual_type_branch']==requested)
        check(archive+' extension mode independent APIcontrol agreement',settings['is_tool_extended']==actual['requested']['isSplittingToolExtended']==actual['feature_before_node']['isSplittingToolExtended'])
        check(archive+' two historical source BODYs and owners retained',evidence['source_historical_native_body_object_ids']==[275,354] and [s['descriptor']['source_owner_object_id'] for s in evidence['source_body_routes']]==[243,322])
        check(archive+' sourcegroup oneproxy two distinct owned descriptors',len(set(evidence['source_selection_proxy']['descriptor_object_ids']))==2 and evidence['source_selection_proxy']['owner_object_id']==row['feature_object_id'] and all(s['descriptor']['context_record_object_ids']==[] and s['recipe']['payload_kind']=='body_recipe_data' for s in evidence['source_body_routes']))
        check(archive+' source supportlists do not imply singleton pairing',all(421 in s['descriptor']['support_reference_object_ids'] for s in evidence['source_body_routes']))
        new_ids=[1549,1554] if requested=='BRepBody' else [1536,1541]
        check(archive+' distinct tool and uniquely owned newBODYgroup',evidence['tool_historical_native_body_object_id']==456 and evidence['newly_owned_native_body_object_ids']==new_ids and len(evidence['newly_owned_result_anchors'])==2 and all(a['source_owner_object_id']==row['feature_object_id'] for a in evidence['newly_owned_result_anchors']))
        check(archive+' per-target orderedanchorlist is separate from sources',evidence['per_target_record_object_ids']==settings['per_target_record_object_ids'] and evidence['source_to_new_result_pairing'] is None)
        check(archive+' twoinput sources differ from currentfiveBODYset',settings['input_body_count']==2 and actual['component_bodies_after_split']['count']==5 and set(evidence['native_current_body_collection']['body_object_ids'])=={275,354,456,*new_ids})
        check(archive+' no selected face API or source-result assignment',qualified['selected_tool_asm_face_id'] is None and qualified['native_API_body_assignment'] is None and qualified['source_to_result_pairing'] is None)
        mapping=qualified['stored_asm_body_identifiers']['decoded'][0];parsed=inspect_asm(members[mapping['history_blob_member']]);topology=decode_topology(parsed)
        check(archive+' sameasset initialASM complete tokens',parsed['complete_token_stream'] is True)
        native=[]
        for binding in mapping['bindings']:
            graphs=[g for g in topology['body_graphs'] if g['body_index']==binding['asm_body_index']]
            check(archive+' BODY'+str(binding['native_body_object_id'])+' literal storedID join',len(graphs)==1 and binding['stored_handle']==binding['asm_stored_entity_id'])
            native.append(graph_bundle(graphs[0]))
        api=[api_bundle(b) for b in actual['component_bodies_after_split']['bodies']]
        check(archive+' complete currentfive geometry bundles corroborate APIcollectively',multiset(native)==multiset(api))
        check(archive+' collective comparison independent APIorder',multiset(native)==multiset(list(reversed(api))))
        check(archive+' auxiliaryASM3 not confused with sourceBODY2 or toolBODY4',[(b['native_body_object_id'],b['asm_body_index']) for b in mapping['bindings']]==[(275,1),(354,2),(456,4),(new_ids[0],5),(new_ids[1],6)] and any(a['kind']=='body' and a['asm_record_index']==3 and a['stored_entity_id']==-1 for a in mapping['auxiliary_declared_roots']))
        check(archive+' caller feature dictionaries not mutated',features==before)
        samples.append(dict(archive=archive,feature_object_id=row['feature_object_id'],expected_native_evidence=evidence,
            expected_body_route=qualified,expected_body_routes_summary=dict(decoded=[qualified],unresolved=[],scope=SCOPE),
            actual_API_current_geometry_bundles=api,native_API_body_assignment=None,
            actual_requested_tool_type=actual['exact_createInput_arguments']['splitting_tool_argument_type'],actual_rolled_tool_type=actual['feature_before_node']['splittingTool']['actual_type_branch'],
            geometry_scope='Typed source group2, tool1, independently owned new-anchor group2, reciprocal currentBODYset5 and literal sameblob ASM IDs qualify native identities before all five complete planar data bundles compare as unordered multisets at12decimals. No native/API body or per-source/new-result pairing; current5 includes the independent sheet.'))
        if requested=='BRepBody':saved=(data,records,features,member,members,row,evidence)
    old_sheet=json.loads((root/'split-body-sheet-route-decoding.json').read_text())
    for sample in old_sheet['samples']:
        data,records,features,member,members=load(root,sample['archive'],zstd);evidence=sample['expected_native_evidence'];f=next(f for f in features if f['object_id']==sample['feature_object_id'])
        tool=resolve_split_body_sheet_tool(data,records,evidence['tool_selection_record_object_id'],f,{})
        check(sample['archive']+' singleton full native+late dictionaries exact',tool['native_evidence']==evidence and qualify_split_body_sheet_routes(data,records,member,members,evidence)==sample['expected_body_route'])
        controls.append(dict(archive=sample['archive'],old_singleton_complete_native_and_late_dicts_exact=True))
    old_replace=json.loads((root/'replace-face-body-route-decoding.json').read_text())
    for sample in old_replace['samples']:
        data,records,features,member,members=load(root,sample['archive'],zstd);evidence=sample['expected_native_evidence'];f=next(f for f in features if f['object_id']==sample['feature_object_id'])
        _,target=resolve_replace_face_target(data,records,evidence['target_selection_record_object_id'],f,{})
        check(sample['archive']+' priorReplace complete native+late dictionaries exact',target['native_evidence']==evidence and qualify_replace_face_body_routes(data,records,member,members,evidence)==sample['expected_body_route'])
        controls.append(dict(archive=sample['archive'],old_Replace_complete_native_and_late_dicts_exact=True))
    negative='splitbodyprofiles-be9787c7a7d8';negtruth=json.loads((root/negative/'ground_truth.json').read_text())
    check('Profile capture explicitly CompleteWithErrors',negtruth['terminal_status']=='CompleteWithErrors' and len(negtruth['errors'])==3)
    for actual in negtruth['samples']:
        archive=negative+'/'+actual['file'];data,records,features,_,_=load(root,archive,zstd);summary=decode_split_body_multi_sheet_tools(data,records,features)
        check(archive+' rejectedProfile adds no nativeSplit coverage',actual['split_status']=='AttemptError' and actual['close_owned_document_returned'] is True and not any(f['kind']=='SplitBody' for f in features) and not summary['decoded'] and not summary['unresolved'])
        controls.append(dict(archive=archive,native_SplitBody_feature_count=0,actual_split_status=actual['split_status'],fake_Profile_coverage=False))
    data,records,features,member,members,row,evidence=saved;fid=row['feature_object_id'];f=next(f for f in features if f['object_id']==fid);record=next(r for r in records if r.is_primary and r.object_id==fid)
    def guard(label,mutation=None,alter=None,singleton=False):
        bad=bytearray(data)
        if mutation:mutation(bad)
        phase='PureNativeRoleGroups'
        try:
            resolver=resolve_split_body_sheet_tool if singleton else resolve_split_body_multi_sheet_tool
            tool=resolver(bytes(bad),records,evidence['tool_selection_record_object_id'],f,{})
            phase='LateASMQualification';fresh=tool['native_evidence']
            if alter:alter(fresh)
            qualify_split_body_multi_sheet_routes(bytes(bad),records,member,members,fresh)
        except (ValueError,KeyError,IndexError,struct.error,UnicodeError) as error:reason=str(error)
        else:raise AssertionError(label)
        checks.append(label);guards.append(dict(guard=label,phase=phase,reason=reason))
    guard('Oldsingleton resolver keeps exact plural rejection',singleton=True)
    check('Oldsingleton prefix diagnostic unchanged',guards[-1]['reason']=='Split sheet common tool/per-target prefix differs')
    guard('Reject unobserved threetarget count',lambda b:struct.pack_into('<I',b,record.body+49,3))
    guard('Reject duplicate newlyownedanchor references',lambda b:struct.pack_into('<Q',b,record.body+65,evidence['per_target_record_object_ids'][0]))
    proxy=next(r for r in records if r.is_primary and r.object_id==evidence['source_selection_record_object_id'])
    guard('Reject duplicate historicalsource descriptors',lambda b:struct.pack_into('<Q',b,proxy.body+18,evidence['source_selection_proxy']['descriptor_object_ids'][0]))
    mapping=next(r for r in records if r.is_primary and r.object_id==evidence['native_history_mapping_object_id'])
    guard('Nativegroups pass but absent ASMhandle fails late',lambda b:struct.pack_into('<Q',b,mapping.body+6,99999))
    guard('Reject altered late currentBODYgroup',alter=lambda e:e.__setitem__('source_historical_native_body_object_ids',[]))
    q=qualify_split_body_multi_sheet_routes(data,records,member,members,evidence);own=dict(members);own.pop(q['native_history_mapping']['history_blob_member'])
    try:qualify_split_body_multi_sheet_routes(data,records,member,own,evidence)
    except ValueError as error:reason=str(error)
    else:raise AssertionError('Missing blob accepted')
    checks.append('Reject missing explicitsameassetblob');guards.append(dict(guard=checks[-1],phase='LateASMQualification',reason=reason))
    sourcefiles=('decode_split_body_multi_sheet_routes.py','decode_split_body_sheet_routes.py','decode_owned_surface_selection.py','validate_split_body_multi_sheet_routes.py','decode_split_body_multi_sheet_tools.py','decode_split.py')
    return dict(sample_count=3,historical_source_BODY_count=6,historical_tool_BODY_count=3,new_owned_BODY_count=6,qualified_stored_BODY_count=15,
        check_count=len(checks),malformed_guard_count=len(guards),samples=samples,legacy_controls=controls,checks=checks,malformed_guards=guards,
        actual_document_close_journal=closes,actual_terminal_journal=journal[-1],
        capture_provenance=dict(capture_directory=CAPTURE,executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],sdk_runtime_sha256=truth['sdk_runtime_sha256']),
        frozen_report_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ('split-body-sheet-route-decoding.json','replace-face-body-route-decoding.json')},
        source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sourcefiles},
        limitations=['Two ordered source descriptors and two ordered newanchors establish groups, not a per-source/result bijection',
            'Source support-reference lists also contain Patch owner; no singleton correspondence inferred',
            'Current5 set includes independent historical sheet; not five Split-owned results',
            'ASM auxiliary root is3 here, not2; literal stored IDs determine all joins',
            'Complete currentgeometry corroborates saved API collectively without API temporaryIDs/tokens/names/order choosing identity',
            'Three rejectedProfile attempts retain zero nativeSplit feature coverage',
            'No general splitting solver, persistent face mapping, lifecycle or regeneration'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='split-body-multi-sheet-route-decoding.json');args=parser.parse_args()
    root=Path(__file__).resolve().parent;z=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(root,z);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('sample_count','qualified_stored_BODY_count','check_count','malformed_guard_count')}))

if __name__=='__main__':main()
