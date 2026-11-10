"""Focused FACE FPM context joins, independent identities and counterordering."""
import copy
import json
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_face_tracking_contexts import decode_face_tracking_contexts,SCOPE
from fusion_archive import read_members
from fusion_metadata import design_records


def validate(zstd_library,root=None):
    root=Path(root) if root is not None else Path(__file__).resolve().parent
    old=json.loads((root/'generic-name-variant-decoding.json').read_text())
    files=sorted({s['file'] for s in old['samples'] if any(v['family']=='FACE_FPM' for v in s['variants'])})
    report=dict(scope=SCOPE,interfaces={
        'decoder':'decode_face_tracking_contexts(data,records,features,member,members,body_identifier_summary,body_selections=None)->decoded/unresolved/scope',
        'integration':'Late after feature-tool/body-selection/body-identifier decoding. Separate context summary/feature attachments only; retain existing selection failures and null selected/persistent/historical-state fields.'},
        proof_order=[
            'Actual feature record explicitly owns its input collection. Collection and owned proxy list the same ordered typed feature descriptors.',
            'Each ordinary descriptor owns a typed90055 leaf containing the explicit source Extrude feature identity; descriptor owner, source settings and native class agree.',
            'Descriptor explicitly references a typed body anchor and reciprocal6CCF support; anchor source-owner and support source-owner both equal the explicit source feature identity.',
            'FullRound uses the strict existing set/proxy/aggregate/three-source-role reader; aggregate anchor and reciprocal support establish only its historical native BODY context.',
            'Native body/handle mapping and its explicit same-asset filename are revalidated. Typed ASM BODY stored handle and reciprocal BODY face graph qualify context membership independently of FPM values.',
            'Only then are typed reciprocal FACE-owned FPM records within that mapped BODY collected and their literal values compared with the independently owned descriptor ID. Equality remains literal corroboration, not an encoded reference.'],
        samples=[],guards=[],counterexamples=[],negative_controls=[],limitations=[
            'Exact selected source FACE, persistent FACE identity and qualified historical state remain null in every decoded context.',
            'FullRound covers two of six mapped BODY faces, while its aggregate has three independently decoded source-face roles; no FPM face-to-role or selected/surviving lifecycle inference follows.',
            'Pattern context uses mapped seed BODY membership, not generated BODY ordinal, coordinate placement or an FPM literal interpreted as a feature ID.',
            'Source feature API getter names corroborate native source roles; no API getter for FPM literals or persistent cache topology was captured.',
            'This stage does not clear old selection/geometry warnings or introduce new geometry evaluation or feature regeneration.'])
    contexts=faces=APIchecks=0;saved={}
    for filename in files:
        stream=decode_basics(root/filename,zstd_library)['streams'][0]
        members=read_members(root/filename,zstd_library);data=members[stream['member']]
        records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')])
        features=stream['features'];before=copy.deepcopy(features)
        result=decode_face_tracking_contexts(data,records,features,stream['member'],members,stream['body_asm_identifiers'],stream['body_selections'])
        assert not result['unresolved'],(filename,result['unresolved'])
        assert features==before
        actual_file=json.loads((root/filename).parent.joinpath('ground_truth.json').read_text())
        actual=next(s for s in actual_file['samples'] if s['file']==Path(filename).name)
        row=dict(file=filename,expected_decoded=result,API_source_feature_checks=[],input_features_unchanged=True)
        names=[]
        for r in result['decoded']:
            c=r['native_context'];contexts+=1;faces+=r['tracked_FACE_count']
            assert r['exact_selected_source_FACE_identity'] is r['persistent_FACE_identity'] is r['qualified_historical_state'] is None
            assert r['literal_is_serialized_native_reference'] is False
            if c['input_role']=='ExplicitExtrudeFeatureInput':names.append(c['source_feature_name'])
            if c['input_role']=='FullRoundAggregateBodyContext':
                assert r['tracked_FACE_count']==2 and len(r['mapped_BODY_FACE_record_indices'])==6
                report['counterexamples'].append(dict(file=filename,kind='FullRoundTwoTrackedFacesVersusThreeSelectedFaceRoles',
                    tracking_FACE_count=2,source_face_role_count=3,mapped_BODY_FACE_count=6,
                    conclusion='Tracking body context does not assign one tracked FACE per selected role or qualify historical/current state'))
        if names:
            expected_names=actual.get('settings',{}).get('input_names')
            if expected_names is None:expected_names=[x['name'] for x in actual['actual_inputs']]
            assert names==expected_names,(filename,names,expected_names)
            row['API_source_feature_checks'].append(dict(ordered_explicit_source_names=names,actual_API_input_names=expected_names,matches=True))
            APIchecks+=len(names)
        if filename.endswith('mirror_two_features.f3d'):
            assert [r['native_context']['descriptor_object_id'] for r in result['decoded']]==[400,404]
            assert [r['initial_ASM_BODY_record_index'] for r in result['decoded']]==[2,1]
            report['counterexamples'].append(dict(file=filename,kind='NativeInputOrderDiffersFromStoredBODYOrder',
                descriptor_input_order=[400,404],mapped_BODY_order=[2,1],source_feature_input_order=names,
                conclusion='Independent descriptor/anchor/body joins determine groups before literal comparison; ordinal matching would reverse them'))
        report['samples'].append(row);saved[filename]=(data,records,features,stream['member'],members,stream['body_asm_identifiers'],stream['body_selections'],result)
    assert len(files)==14 and contexts==15 and faces==78
    for filename in ['circularmodes-45f859c1f1b6/body_full.f3d','specialfillets-d50f7a4f04e0/rule_all_both.f3d']:
        s=decode_basics(root/filename,zstd_library)['streams'][0];m=read_members(root/filename,zstd_library);d=m[s['member']]
        rr,_=design_records(d,m[s['member'].replace('BulkStream.dat','MetaStream.dat')])
        r=decode_face_tracking_contexts(d,rr,s['features'],s['member'],m,s['body_asm_identifiers'],s['body_selections'])
        assert not r['decoded'] and not r['unresolved']
        report['negative_controls'].append(dict(file=filename,no_unrelated_FACE_contexts=True))
    filename='remainingbodyinputs-7b3357274e85/mirror_two_features.f3d'
    data,records,features,member,members,mapping,bodies,result=saved[filename]
    by={r.object_id:r for r in records if r.is_primary}
    def reject(label,changed_data=data,changed_mapping=mapping,changed_members=None):
        mm=dict(members) if changed_members is None else changed_members
        if changed_members is None:mm[member]=changed_data
        out=decode_face_tracking_contexts(changed_data,records,features,member,mm,changed_mapping,bodies)
        assert out['unresolved'],label
        report['guards'].append(dict(label=label,rejected=True,reasons=out['unresolved']))
    changed=bytearray(data);struct.pack_into('<Q',changed,by[400].body+253,999999)
    reject('Descriptor owner differs from feature',bytes(changed))
    changed=bytearray(data);struct.pack_into('<Q',changed,by[403].body+2,243)
    reject('Feature leaf swaps source without matching anchor/support',bytes(changed))
    changed_mapping=copy.deepcopy(mapping);changed_mapping['decoded'][0]['bindings'][0]['asm_body_index']=2
    reject('Supplied BODY ordinal conflicts with stored handle mapping',changed_mapping=changed_mapping)
    # Keep the same original membership and descriptor proof but perturb one
    # correctly framed FPM literal. It must become explicit noncorroboration.
    context=result['decoded'][0];blob_member=context['history_blob_member'];blob=members[blob_member]
    from asm_records import inspect_asm
    parsed=inspect_asm(blob);attribute=context['corroborating_FACE_tracking_attributes'][0]['attribute_record_index']
    literal=parsed['records'][attribute]['tokens'][7]
    changed_blob=bytearray(blob);struct.pack_into('<q',changed_blob,literal['offset']+1,404)
    changed_members=dict(members);changed_members[blob_member]=bytes(changed_blob)
    reject('FPM literal disagrees after independent same-BODY proof',changed_members=changed_members)
    report['validation']=dict(saved_files=len(files),independent_native_contexts=contexts,corroborated_FACE_attributes=faces,
        actual_API_source_feature_name_comparisons=APIchecks,negative_controls=len(report['negative_controls']),guards_passed=len(report['guards']),
        FullRound_unassigned_role_counterexamples=3,two_input_Mirror_counterorder_proofs=1,
        prior_feature_mutations=0,new_live_API_calls=0,new_persistent_FACE_ID_claims=0,selection_failures_cleared=0)
    return report
