"""Thin operation target/new-body/ASM routes and collective API geometry."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_basics import decode_sketches
from decode_brep import decode_topology
from decode_thin_extrude_body_routes import resolve_thin_extrude_body_routes,qualify_thin_extrude_body_routes,SCOPE
from decode_thin_extrude_operations import decode_thin_extrude_operations
from decode_thin_extrudes import decode_thin_extrudes,inspect_thin_extrude
from validate_mesh_convert_operation_geometry import graph_bundle,api_bundle,multiset
from validate_mesh_remesh import load

CAPTURE='thinextrudeoperations-edb76642a509'


def load_features(root,archive,zstd):
    args=load(root,archive,zstd);decode_sketches(args[0],args[1],args[2]);return args


def actual_bundle(body):
    # This capture calls the independently observed Plane origin key origin_cm.
    adapted={**body,'faces':[{**face,'geometry':{**face['geometry'],'origin':face['geometry']['origin_cm']}} for face in body['faces']]}
    return api_bundle(adapted)


def validate(root,zstd):
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text())
    journal=[json.loads(line) for line in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks,samples,guards,controls=[],[],[],[]
    def check(label,condition,**fields):
        if not condition:raise AssertionError(label)
        checks.append(dict(check=label,**fields))
    check('Actual terminal3exports/no case errors',(root/CAPTURE/'complete.txt').is_file() and truth['terminal_status']=='complete' and not truth['errors'] and len(truth['samples'])==3)
    closes=[r for r in journal if r['phase']=='owned_document_close_returned']
    check('Actual3owned closeFalse true',len(closes)==3 and all(r['returned'] is True and r['save'] is False for r in closes))
    check('Exact executed generator snapshot hash',hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file'];args=load_features(root,archive,zstd);data,records,features,member,members=args
        check(archive+' actual archive hash',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        operations=decode_thin_extrude_operations(data,records,features)
        check(archive+' independent early thin controls/profile fully decoded',len(operations['decoded'])==1 and not operations['unresolved'])
        early=operations['decoded'][0];evidence=early['body_list_evidence'];features_before=copy.deepcopy(features)
        qualified=qualify_thin_extrude_body_routes(data,records,member,members,evidence)
        summary=dict(decoded=[qualified],unresolved=[],scope=SCOPE)
        check(archive+' target selection remains historical seedowner279/nativeBODY311',evidence['target_native_body_object_ids']==[311] and evidence['target_seed_anchor_object_ids']==[317] and evidence['target_seed_owner_object_ids']==[279] and early['feature_object_id']!=279)
        check(archive+' owned proxy/descriptor references match target',evidence['target_body_selection_proxy']['owner_object_id']==early['feature_object_id'] and evidence['target_body_descriptor']['owner_object_id']==early['feature_object_id'] and evidence['target_body_descriptor']['native_body_object_id']==311)
        expected_new=[1764] if actual['case']=='cut' else []
        check(archive+' separately owned new bodies exact',evidence['new_result_native_body_object_ids']==expected_new and evidence['native_current_body_object_ids']==[311]+expected_new and all(a['source_owner_object_id']==early['feature_object_id'] for a in evidence['new_result_body_anchors']))
        check(archive+' body-list offsets/fullbytes replay retained',bytes.fromhex(evidence['stored_body_list_hex'])==data[next(r for r in records if r.is_primary and r.object_id==early['feature_object_id']).body+evidence['body_list_start_offset']:next(r for r in records if r.is_primary and r.object_id==early['feature_object_id']).body+evidence['body_list_end_offset']] and evidence['layout']['exact_body_list_and_mapping_replay'] is True)
        check(archive+' no source/result identity pairing',qualified['source_to_result_pairing'] is None)
        if actual['case']=='join':
            check(archive+' Join native target evidence separate from inactive APIparticipants',actual['actual_input_before_add']['participantBodies'] is None and actual['actual_input_before_add']['participant_applicability']['status']=='NotApplicable' and actual['actual_input_before_add']['participant_applicability']['getter_called'] is False and actual['actual_input_before_add']['participant_applicability']['setter_called'] is False)
        else:
            check(archive+' actual explicit and rolled APIparticipant handle equality',actual['input_participant_handle_equality'] is True and actual['rolled_participant_handle_equality'] is True)
        mapping=qualified['stored_asm_body_identifiers']['decoded'][0]
        check(archive+' native mapping retains all current bodies by storedhandle',set(b['native_body_object_id'] for b in mapping['bindings'])==set(evidence['native_current_body_object_ids']) and len(mapping['bindings'])==actual['component_bodies_after_thin']['count'])
        parsed=inspect_asm(members[mapping['history_blob_member']]);topology=decode_topology(parsed)
        check(archive+' sameasset ASM complete tokens',parsed['complete_token_stream'] is True)
        graphs=[]
        for binding in mapping['bindings']:
            found=[g for g in topology['body_graphs'] if g['body_index']==binding['asm_body_index']]
            check(archive+' nativeBODY'+str(binding['native_body_object_id'])+' exact typed stored-ID root',len(found)==1 and binding['stored_handle']==binding['asm_stored_entity_id'])
            graphs.append(found[0])
        actual_bodies=actual['component_bodies_after_thin']['bodies']
        native_bundles=[graph_bundle(g) for g in graphs];api_bundles=[actual_bundle(b) for b in actual_bodies]
        check(archive+' complete BRep geometry bundles corroborate API collectively',multiset(native_bundles)==multiset(api_bundles))
        check(archive+' collective geometry proof invariant to API order',multiset(native_bundles)==multiset(list(reversed(api_bundles))))
        check(archive+' auxiliary unnumbered ASM BODY retained unassigned',len(mapping.get('auxiliary_declared_roots',[]))==1 and mapping['auxiliary_declared_roots'][0]['kind']=='body' and mapping['auxiliary_declared_roots'][0]['stored_entity_id']==-1)
        if actual['case']=='cut':
            check(archive+' Cut result103 uses ASMrecord3 not ordinal2',[(b['native_body_object_id'],b['stored_handle'],b['asm_body_index']) for b in mapping['bindings']]==[(311,102,1),(1764,103,3)])
        check(archive+' existing feature dictionaries not mutated',features==features_before)
        samples.append(dict(archive=archive,feature_object_id=early['feature_object_id'],
            expected_body_list_evidence=evidence,expected_body_route=qualified,expected_body_routes_summary=summary,
            expected_default_strict_thin_summary=decode_thin_extrudes(data,records,features),
            actual_API_result_geometry_bundles=api_bundles,
            geometry_comparison_scope='Explicit native target/new-owned/current-collection mapping fixes native BODY identities before complete result data bundles are compared collectively as an unordered multiset at12decimal numerical precision; no per-native-ID/API or source/result pairing',
            native_API_result_assignment=None))
        if actual['case']=='cut':saved=(args,early,evidence)
    # Full previous NewBody sidecars remain exact; no main decode is needed.
    previous=json.loads((root/'thin-extrude-decoding.json').read_text())
    for old in previous['samples']:
        args=load_features(root,old['file'],zstd);data,records,features,member,members=args
        summary=decode_thin_extrudes(data,records,features)
        check(old['file']+' prior full Thin NewBody dictionary exact',summary==old['expected_summary'])
        check(old['file']+' new Boolean helper no false matching',not decode_thin_extrude_operations(data,records,features)['decoded'])
        controls.append(dict(archive=old['file'],complete_NewBody_summary_exact=True))
    ordinary=previous['ordinary_control'];args=load_features(root,ordinary['file'],zstd);data,records,features,member,members=args
    feature=next(f for f in features if f['kind']=='Extrude');record=next(r for r in records if r.is_primary and r.object_id==feature['object_id'])
    check(ordinary['file']+' ordinary False inspection exact',inspect_thin_extrude(data,records,data[record.body:record.end],feature,features=features)==ordinary['expected_inspection'])
    args,early,evidence=saved;data,records,features,member,members=args
    record=next(r for r in records if r.is_primary and r.object_id==early['feature_object_id']);start=evidence['body_list_start_offset']
    def guard(label,mutate=None,alter_evidence=None,remove_blob=False):
        bad=bytearray(data)
        if mutate:mutate(bad)
        phase='NativeFraming'
        try:
            fresh=resolve_thin_extrude_body_routes(bytes(bad),records,bytes(bad[record.body:record.end]),dict(object_id=record.object_id,record_offset=record.start),start)
            phase='LateASMQualification'
            if alter_evidence:alter_evidence(fresh)
            own_members=dict(members)
            if remove_blob:own_members.pop(member.split('/FusionDesignSegmentType1/')[0]+'/Breps.BlobParts/'+fresh['stored_history_filename'])
            qualify_thin_extrude_body_routes(bytes(bad),records,member,own_members,fresh)
        except (ValueError,KeyError,IndexError,struct.error) as error:reason=str(error)
        else:raise AssertionError(label)
        check(label,True);guards.append(dict(guard=label,phase=phase,reason=reason))
    guard('Reject unsupported new-anchor count2',lambda d:struct.pack_into('<I',d,record.body+start+4,2))
    proxy=next(r for r in records if r.is_primary and r.object_id==evidence['target_body_selection_object_ids'][0])
    guard('Reject owned target proxy backlink mismatch',lambda d:struct.pack_into('<Q',d,proxy.end-10,279))
    mapping=next(r for r in records if r.is_primary and r.object_id==evidence['native_history_mapping']['mapping_record_object_id'])
    guard('Native framing passes but unknown ASM handle fails late',lambda d:struct.pack_into('<Q',d,mapping.body+6,104))
    guard('Reject tampered late current-body evidence',alter_evidence=lambda e:e.__setitem__('native_current_body_object_ids',[]))
    guard('Native framing passes but missing sameasset blob fails late',remove_blob=True)
    return dict(interface='resolve_thin_extrude_body_routes(data,records,body,feature,cursor) pure callback; qualify_thin_extrude_body_routes(data,records,member,members,evidence) late ASM proof',
        sample_count=3,target_descriptor_count=3,new_owned_BODY_count=1,qualified_mapped_BODY_count=4,
        check_count=len(checks),malformed_guard_count=len(guards),samples=samples,legacy_controls=controls,
        checks=checks,malformed_guards=guards,actual_document_close_journal=closes,actual_terminal_journal=journal[-1],
        limitations=['Historical seed targetBODY311 not relabeled as feature-owned result; separate newCutBODY1764 anchor retained',
            'Join native target selection does not imply applicable API participantBodies getter/setter',
            'Native current collection proves stored membership only; source/result geometry pairing and lifecycle remain unresolved',
            'Cut BODYhandle103 resolves ASMrecord3; ordinal2 is an unassigned auxiliary BODY',
            'Geometry comparisons are unordered complete-data multisets, no native/API per-body assignment',
            'Early controls/native framing can succeed while late ASM qualification remains unresolved',
            'No Thin wall Boolean algorithm, current visibility or regeneration'],
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'decode_thin_extrude_body_routes.py','validate_thin_extrude_body_routes.py','decode_thin_extrude_operations.py',
            'decode_thin_extrudes.py','decode_body_properties.py','decode_body_asm_identifiers.py')})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='thin-extrude-body-route-decoding.json');args=parser.parse_args()
    result=validate(Path(__file__).resolve().parent,args.zstd_library);Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('sample_count','qualified_mapped_BODY_count','check_count','malformed_guard_count')}))

if __name__=='__main__':main()
