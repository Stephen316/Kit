"""Focused saved Draft parting-line contrasts and exact strict-default controls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from decode_basics import decode_basics
from decode_draft import decode_draft
from decode_parting_line_drafts import decode_parting_line_drafts
from decode_selection import known_construction_entities
from decode_sketch import same
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
FOLDER='partinglinedrafts-c4d07c76fcd5'
BASELINE='cd4cad1'


def load(path,zstd):
    main=decode_basics(path,zstd)
    stream=next(s for s in main['streams'] if 'features' in s)
    members=read_members(path,zstd);data=members[stream['member']]
    records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')])
    return data,records,stream


def validate(root,zstd):
    truth=json.loads((root/FOLDER/'ground_truth.json').read_text())
    assert (root/FOLDER/'complete.txt').is_file() and truth['terminal_status']=='complete'
    assert len(truth['samples'])==3 and not truth['errors']
    report=dict(interface='decode_parting_line_drafts(data,records,features,known=None) -> decoded/unresolved/scope; success rows feature_object_id/kind/name/settings',
        shared_hooks='parse_draft_controls first54 binding/flag fields with explicit header opt-in; make_draft_selection_readers owned descriptor/proxy framing with explicit Edge recipe/context opt-in and counted recipe reader',
        captures=FOLDER,api_version=truth['fusion_version'],samples=[],old_fixed_plane_controls=[],guards=[],
        old_warning='Unsupported observed fixed-plane Draft class/header',
        warning_scope='Only successful corresponding Draft tool failure may be cleared; setup SplitFace and persistent topology/context diagnostics remain independent',
        validation_command='python3 validate_parting_line_drafts.py --zstd-library <libzstd path>',
        source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'GeneratePartingLineDraftContrasts.py','decode_draft.py','decode_parting_line_drafts.py',
            'validate_parting_line_drafts.py',FOLDER+'/executed-generator-source.txt')})
    saved={}
    for sample in truth['samples']:
        path=root/FOLDER/sample['file'];data,records,stream=load(path,zstd);features=stream['features']
        decoded=decode_parting_line_drafts(data,records,features)
        assert len(decoded['decoded'])==1 and not decoded['unresolved'],decoded
        row=decoded['decoded'][0];settings=row['settings'];api=sample['settings'];definition=api['definition']
        body={b['object_id']:b for b in stream['body_properties']['bodies']}[settings['historical_native_body_object_id']]
        owner=next(f for f in features if f['object_id']==settings['historical_source_owner_object_id'])
        plane=settings['pull_geometry']['native_selection']['entity'];actual_plane=api['pull_geometry']
        input_descriptors=settings['input_selections'][0]['descriptors'];parting=settings['parting_line_selection']['descriptors']
        fixed=settings['moving_fixed_edge_selection'];moving=fixed is not None
        actual_sources=[*api['input_faces'],*api['parting_line_curves'],*(api['moving_fixed_edges'] or [])]
        checks=dict(actual_export_hash_matches=hashlib.sha256(path.read_bytes()).hexdigest()==sample['export']['sha256'],
            actual_health_no_errors_close=True if sample['health_state']==0 and sample['warning']=='' and sample['close_owned_document_returned'] is True and not sample['getter_errors'] and not sample['setter_errors'] else False,
            actual_feature_name_matches=row['name']==sample['feature_identity']['name'],
            actual_draft_type_matches=settings['draft_type_api_value']==api['draft_type']==sample['actual_input_types']['draft_type']==1,
            actual_parting_type_matches=settings['parting_line_type_api_value']==api['parting_line_type']==sample['actual_input_types']['parting_line_type'],
            actual_angle_value_matches=same([settings['angle_one_radians']],[definition['angle_one_radians']]),
            actual_extent_mode_matches=settings['angle_mode']==definition['angle_mode']=='SingleAngle',
            actual_symmetry_matches=settings['is_symmetric']==definition['is_symmetric'],
            actual_flip_chain_flags_match=settings['is_direction_flipped']==api['is_direction_flipped'] and settings['is_tangent_chain']==api['is_tangent_chain'],
            native_two_face_count_matches_actual=len(input_descriptors)==len(api['input_faces'])==2,
            native_edge_parting_count_matches_actual=len(parting)==len(api['parting_line_curves'])==1,
            native_moving_fixed_edge_count_matches_actual=(fixed['descriptor_count'] if moving else 0)==len(api['moving_fixed_edges'] or []),
            typed_recipe_roles_are_faces_then_edges=all(d['kind']=='Face' and d['recipe']['payload_kind'] in ('face_recipe_data','bounded_face_recipe_data') for d in input_descriptors) and all(d['kind']=='Edge' and d['recipe']['payload_kind']=='edge_recipe_data' for d in parting+(fixed['descriptors'] if moving else [])),
            actual_target_body_name_matches_all_roles=body['name']==sample['before_body']['name'] and all(s['body_name']==body['name'] for s in actual_sources),
            explicit_historical_source_owner_matches_seed=owner['kind']=='Extrude' and owner['name']=='PartingDraftSeedExtrude',
            explicit_native_xy_origin_normal_match_actual=same(plane['origin_cm'],actual_plane['origin_cm']) and same(plane['normal'],actual_plane['normal']),
            native_chaining_remains_unmapped=settings['is_chained'] is None and api['is_chained'] is None,
            native_moving_direction_remains_unmapped=settings['moving_direction'] is None and (api['moving_direction']==2 if moving else api['moving_direction'] is None),
            actual_input_entity_types_agree=all(s['entity_type']=='adsk::fusion::BRepFace' for s in api['input_faces']) and all(s['entity_type']=='adsk::fusion::BRepEdge' for s in api['parting_line_curves']+(api['moving_fixed_edges'] or [])))
        # Parameter identities are compared by native role and exact value, never by expression text.
        feature=next(f for f in features if f['object_id']==row['feature_object_id'])
        actual_parameters={p['role']:p for p in sample['parameters'] if p['created_by']==row['name']}
        native_parameters={p['role']:p for p in feature['parameters']}
        checks['both_explicit_angle_binding_roles_match_actual_parameters']=all(
            native_parameters[role]['binding_object_id']==settings['angle_binding_object_ids'][role]
            and native_parameters[role]['raw_float64']==actual_parameters[role]['value'] for role in ('Angle1','Angle2'))
        assert all(checks.values()),(sample['file'],checks)
        report['samples'].append(dict(archive=str(path.relative_to(root)),checks=checks,expected_decoded=decoded,
            actual_api_settings=api,actual_requested=sample['requested'],actual_parameters=actual_parameters,
            actual_result_bodies=sample['feature_bodies'],actual_root_bodies=sample['root_bodies'],
            actual_getter_errors=sample['getter_errors'],actual_setter_errors=sample['setter_errors'],
            saved_setup_splitface_failures=[e for e in stream['tool_decoding']['unresolved'] if e['kind']=='SplitFace'],
            identity_scope='API coordinates/evaluator samples are independent capture evidence only; no selected native FACE/EDGE ordinal or persistent topology inferred by geometry/order'))
        saved[sample['case']]=(data,records,stream,decoded)
    # Read the approved historical parser, using current identical dependencies for
    # intentional earlier metadata-label corrections. No checkout or Git mutation.
    baseline_source=subprocess.check_output(['git','show',BASELINE+':decode_draft.py'],cwd=root,text=True)
    namespace={'__name__':'frozen_draft_'+BASELINE};exec(compile(baseline_source,'<git:'+BASELINE+':decode_draft.py>','exec'),namespace)
    baseline=namespace['decode_draft'];report['strict_default_baseline']=dict(revision=BASELINE,source_sha256=hashlib.sha256(baseline_source.encode()).hexdigest())
    old=json.loads((root/'draft-decoding.json').read_text())
    old_saved=None
    for sample in old['samples']:
        data,records,stream=load(root/sample['file'],zstd);feature=next(f for f in stream['features'] if f['object_id']==sample['feature_object_id'])
        record=next(r for r in records if r.is_primary and r.object_id==feature['object_id']);body=data[record.body:record.end]
        known=known_construction_entities(data,records,stream['features'])
        before=baseline(data,records,body,feature,known);after=decode_draft(data,records,body,feature,known)
        assert after==before,sample['file']
        untouched=decode_parting_line_drafts(data,records,stream['features']);assert not untouched['decoded'] and not untouched['unresolved']
        report['old_fixed_plane_controls'].append(dict(archive=sample['file'],baseline_settings_exact=True,new_helper_leaves_fixed_plane_untouched=True))
        if old_saved is None:old_saved=data,records,stream,feature,record,known
    def guard(case,label,identity,offset,replacement):
        data,records,stream,_=saved[case];record=next(r for r in records if r.is_primary and r.object_id==identity)
        changed=bytearray(data);changed[record.body+offset:record.body+offset+len(replacement)]=replacement
        result=decode_parting_line_drafts(bytes(changed),records,stream['features'])
        assert not result['decoded'] and len(result['unresolved'])==1,(label,result)
        report['guards'].append(dict(check=label,passed=True,reason=result['unresolved'][0]['reason']))
    row=saved['fixed_three'][3]['decoded'][0];settings=row['settings'];parting=settings['parting_line_selection']['descriptors'][0]
    data,records,_,_=saved['fixed_three'];p={r.object_id:r for r in records if r.is_primary}
    guard('fixed_three','Unknown Draft type header',row['feature_object_id'],6,struct.pack('<I',4))
    guard('fixed_three','Uncaptured fixed nonsymmetric angle mode',row['feature_object_id'],12,struct.pack('<I',1))
    guard('fixed_three','Parting proxy owner must be feature',settings['parting_line_selection']['selection_record_object_id'],p[settings['parting_line_selection']['selection_record_object_id']].end-p[settings['parting_line_selection']['selection_record_object_id']].body-10,struct.pack('<Q',settings['historical_source_owner_object_id']))
    guard('fixed_three','Parting descriptor context must be Edge family',parting['object_id'],184,struct.pack('<Q',settings['input_selections'][0]['descriptors'][0]['context_record_object_ids'][0]))
    guard('fixed_three','Parting/input role proxies cannot alias',row['feature_object_id'],68,struct.pack('<Q',settings['input_selections'][0]['selection_record_object_id']))
    guard('fixed_three','Explicit historical body anchor must resolve',parting['object_id'],199,struct.pack('<Q',settings['historical_source_owner_object_id']))
    # Exact repeated binding position follows the explicit9-reference table.
    guard('fixed_three','Repeated angle dependency must agree',row['feature_object_id'],254,struct.pack('<Q',settings['angle_binding_object_ids']['Angle2']))
    moving=saved['moving_both_three'][3]['decoded'][0];ms=moving['settings']
    guard('moving_both_three','Uncontrasted moving raw byte54 rejected',moving['feature_object_id'],54,b'\1')
    guard('moving_both_three','Moving fixed edges require two descriptors',ms['moving_fixed_edge_selection']['selection_record_object_id'],2,struct.pack('<I',1))
    report['strict_default_error_controls']=[]
    data,records,stream,feature,record,known=old_saved
    for offset,value in ((10,b'\2'),(12,struct.pack('<I',99))):
        changed=bytearray(data[record.body:record.end]);changed[offset:offset+len(value)]=value
        errors=[]
        for parser in (baseline,decode_draft):
            try:parser(data,records,bytes(changed),feature,known)
            except ValueError as error:errors.append(str(error))
            else:raise AssertionError('Malformed old default accepted')
        assert len(errors)==2 and errors[0]==errors[1]
        report['strict_default_error_controls'].append(dict(offset=offset,exact_error=errors[0],passed=True))
    a,b=[saved[k][3]['decoded'][0]['settings'] for k in ('fixed_three','fixed_seven')]
    report['fixed_angle_contrast']=dict(headers_equal=a['stored_header_fields']==b['stored_header_fields'],
        angle_bindings_same_native_ids=a['angle_binding_object_ids']==b['angle_binding_object_ids'],
        angle_values_differ_and_match_actual=a['angle_one_radians']!=b['angle_one_radians'],
        scope='Same captured source construction and native field roles,3degree versus7degree actual getter/parameter contrasts; bookkeeping UUIDs not treated as semantic controls')
    assert all(v for k,v in report['fixed_angle_contrast'].items() if k!='scope')
    report['limitations']=[
        'New branch admits only exact captured two-face/one-bounded-edge setup with XY pull, positive finite single angle, no direction flip/tangent chaining, fixed symmetric mode or moving nonsymmetric mode with two fixed edges.',
        'Native headers(3,2)/(3,3) distinguish Fixed/Moving parting-line type. Moving BothAngles getter2 has no independently contrasted native discriminator; byte54 remains raw and moving_direction remains None. Chaining also remains None.',
        '5662 descriptor recipes discriminate Face versus Edge roles and explicit historical body anchor/source owner. Recipe names and geometry caches do not establish exact persistent selected FACE/EDGE or qualified historical ASM state.',
        'The actual setup SplitFace reader warning is preserved. No regeneration, draft surface construction, trim reconstruction, lifecycle replay, or universal direction/chaining field interpretation is claimed.',
        'Actual source edge/face geometry and trimmed evaluator samples are retained only as independent API evidence. Native source identity is established by typed owned selection chains, not by matching geometry or ordering.']
    report['counts']=dict(actual_samples=3,old_fixed_plane_settings_exact=len(report['old_fixed_plane_controls']),
        malformed_new_guards=len(report['guards']),strict_default_error_controls=len(report['strict_default_error_controls']),
        actual_getter_errors=sum(len(s['getter_errors']) for s in truth['samples']),actual_case_errors=len(truth['errors']))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--zstd-library',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'parting-line-draft-decoding.json');args=parser.parse_args()
    report=validate(ROOT,args.zstd_library);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']))
