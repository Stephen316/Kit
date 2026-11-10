"""Three actual BRep Patch continuity contrasts, raw fields and strict guards."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_brep import decode_topology
from decode_patch_continuity import decode_patch_continuity
from decode_surface_tools import decode_surface_tool
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
DIRECTORY='patchcontinuity-b9b0be85a281'
FAILED='patchcontinuity-f67ca5b5f724'
BASELINE='cd4cad1'


def validate(zstd):
    directory=ROOT/DIRECTORY;truth=json.loads((directory/'ground_truth.json').read_text());failed=json.loads((ROOT/FAILED/'ground_truth.json').read_text())
    assert truth['status']=='complete' and not truth['errors'] and len(truth['samples'])==3
    assert failed['status']=='complete' and len(failed['errors'])==3 and not list((ROOT/FAILED).glob('*.f3d'))
    for d,t in ((directory,truth),(ROOT/FAILED,failed)):
        assert hashlib.sha256((d/'executed-generator-source.txt').read_bytes()).hexdigest()==t['executed_generator_sha256']
        assert all(s['close_owned_document_result'] is True for s in t['samples'])
    frozen_source=subprocess.check_output(['git','show',BASELINE+':decode_surface_tools.py'],cwd=ROOT).decode()
    namespace={};exec(compile(frozen_source,'<frozen '+BASELINE+' surface parser>','exec'),namespace)
    old_decode=namespace['decode_surface_tool']
    report={'scope':'Three actual singleton circular BRep boundary Patch exports, per-edge Free/Connected,Tangent,Curvature; exact common parser defaults and typed ownership before body geometry controls',
        'interface':'decode_patch_continuity(data,records,features)->decoded/unresolved/scope; decoded rows feature_object_id/settings',
        'integration':'After decode_tools, publish optional patch_continuity stream and qualified SurfacePatch settings; clear only same-feature Unsupported basic sketch-profile patch layout. Existing sketch-profile defaults and selection/lifecycle warnings remain separate.',
        'capture_provenance':{'ground_truth_file':DIRECTORY+'/ground_truth.json','sha256':hashlib.sha256((directory/'ground_truth.json').read_bytes()).hexdigest(),
            'executed_generator_sha256':truth['executed_generator_sha256'],'executed_source_snapshot':DIRECTORY+'/executed-generator-source.txt',
            'initial_failed_capture':{'directory':FAILED,'ground_truth_sha256':hashlib.sha256((ROOT/FAILED/'ground_truth.json').read_bytes()).hexdigest(),
                'executed_generator_sha256':failed['executed_generator_sha256'],'errors':failed['errors'],'all_owned_closed_true':True,
                'fix':'boundary getter returns Path/PathEntity rather than direct edges; corrected typed entity dispatch before successful rerun'}},
        'schema':{'definition_class_guid':'7A1DDA31-F6C4-42F6-8282-8654B2085F40','definition_body_bytes':56,
            'continuity':'uint32@3 varies0/1/2 exactly with actual Connected/Tangent/Curvature getter; only this contrasted meaning promoted',
            'raw_fields':'prefix3bytes, u32@7 literal2, float64@11=.5, bytes30..32 literal010000, byte44zero remain bounded raw fields; scalar agrees actual weight in these captures only',
            'references':'sourceproxy@19, typed bookkeeping@33 with backlink to definition, ownerfeature@45; shared feature prefix/opNewBody/count then callback; source proxy→owned topology descriptor→edge_recipe_data→historical native BODY; owned result anchor separately decoded'},
        'samples':[],'malformed_guards':[],'old_default_controls':[],
        'limitations':['Weight.5 and false flip were not contrasted; no arbitrary weight or flip semantics accepted. Free weight and one-face flip are inactive in SDK docs.',
            'Raw BRep group/header field0 matches returned per-edge mode but no True BRep contrast establishes a general bool mapping.',
            'Referenced B0B3FA59 typed103-byte cache remains literal and opaque; no radius/closure/parameterization or occurrence transform inferred from it.',
            'API edge tokens/names and source geometry are capture evidence only. Exact selected ASM edge, recipe evaluation/persistent topology and lifecycle remain unresolved.',
            'Stored keyed BODY topology/area corroboration follows explicit body identities, never chooses source edge by geometry.',
            'No patch surface continuity solver, geometry regeneration or native writer implemented.']}
    contexts={};controls=[];geometry_checks=0
    for sample in truth['samples']:
        filename=DIRECTORY+'/'+sample['file'];file=ROOT/filename
        assert sample['status']=='exported' and not sample['getter_errors'] and sample['close_owned_document_result'] is True
        assert sample['export_size_bytes']==file.stat().st_size and sample['export_sha256']==hashlib.sha256(file.read_bytes()).hexdigest()
        members=read_members(file,zstd);stream=decode_basics(file,zstd)['streams'][0];member=stream['member'];data=members[member];records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        before=copy.deepcopy(stream['features']);summary=decode_patch_continuity(data,records,stream['features']);assert not summary['unresolved'] and before==stream['features']
        row,=summary['decoded'];settings=row['settings'];feature,=[f for f in stream['features'] if f['object_id']==row['feature_object_id']]
        control,=settings['boundary_controls'];api=sample['settings']['continuity'];code,=api['continuity']
        assert control['stored_continuity_code']==code==sample['requested']['continuity_API_value']
        assert api['is_group_edges'] is False and api['weights']==[.5] and api['is_continuity_direction_flipped']==[False]
        assert control['stored_scalar_at_11']==api['weights'][0] and settings['operation']=='NewBody' and sample['settings']['operation']==3
        assert sample['settings']['interior_entity_count']==0 and sample['health_state']==0 and not sample['warning']
        source,=settings['boundary_sources'];assert source['recipe']['payload_kind']=='edge_recipe_data'
        native_source_id=source['native_body_object_id'];result,=settings['result_body_anchors'];assert result['source_owner_object_id']==feature['object_id']
        actual_source=sample['source_before_patch']['body'];actual_result,=sample['result_bodies'];assert len(sample['root_bodies_after'])==2
        assert math.isclose(actual_source['area_cm2'],math.pi*(4-.49),abs_tol=1e-9)
        if code==0:assert math.isclose(actual_result['area_cm2'],math.pi*.49,abs_tol=1e-9)
        else:assert not math.isclose(actual_result['area_cm2'],math.pi*.49,abs_tol=1e-9)
        keyed=[]
        for native,actual in ((native_source_id,actual_source),(result['native_body_object_id'],actual_result)):
            pairs=[(m,b) for m in stream['body_asm_identifiers']['decoded'] for b in m['bindings'] if b['native_body_object_id']==native]
            mapping,binding=pairs[0];assert len(pairs)==1
            graph,=[g for g in decode_topology(inspect_asm(members[mapping['history_blob_member']]))['body_graphs'] if g['body_index']==binding['asm_body_index']]
            for kind in ('face','edge','vertex'):assert graph['counts'][kind]==actual[kind+'_count']
            keyed.append({'native_body_object_id':native,'asm_body_index':binding['asm_body_index'],'stored_handle':binding['stored_handle'],
                'history_blob_member':mapping['history_blob_member'],'counts_match_actual_getters':True})
            geometry_checks+=1
        getter_edge,=api['edges'];original_edge=sample['source_before_patch']['edge']
        for key in ('body_name','geometry_type','face_count','center_cm','normal','radius_cm','evaluator_samples'):
            assert getter_edge[key]==original_edge[key]
        ref=lambda identity:b'\1'+struct.pack('<Q',identity)+bytes(2)
        replay=bytes.fromhex(control['stored_prefix_hex'])+struct.pack('<II',code,control['stored_field_at_7'])+struct.pack('<d',control['stored_scalar_at_11'])
        replay+=ref(control['boundary_selection_record_object_id'])+bytes.fromhex(control['stored_flags_30_to_32_hex'])+ref(control['control_bookkeeping_object_id'])+bytes([control['stored_flag_at_44']])+ref(feature['object_id'])
        assert replay.hex()==control['control_payload_hex'];controls.append(replay)
        report['samples'].append({'archive':filename,'archive_sha256':sample['export_sha256'],'expected_decoded':summary,
            'expected_settings':settings,'actual_API_continuity':code,'actual_API_weights':api['weights'],'actual_API_flip_flags':api['is_continuity_direction_flipped'],
            'source_before_rolled_getters_agree':True,'exact_definition_payload_replay':True,'typed_BODY_cache_controls':keyed,
            'actual_source_area_cm2':actual_source['area_cm2'],'actual_result_area_cm2':actual_result['area_cm2'],
            'analytic_circle_area_reference_cm2':math.pi*.49,'actual_minus_circle_area_cm2':actual_result['area_cm2']-math.pi*.49,
            'actual_result_bounds_cm':[actual_result['bounds_min_cm'],actual_result['bounds_max_cm']],
            'area_scope':'Free agrees analytic disk; Tangent/Curvature actual area differs and is retained as counterevidence to exact circle-patch area, not an identity selector',
            'all_body_identity_joins_precede_geometry_checks':True})
        contexts[sample['case']]=(data,records,stream['features'],feature,control,row)
    assert [b[3:7] for b in controls]==[struct.pack('<I',i) for i in (0,1,2)]
    assert len({b[:3]+bytes(4)+b[7:] for b in controls})==1
    report['continuity_contrast']={'sole_changed_definition_byte_offset':3,'actual_codes':[0,1,2],
        'raw_weight_and_flags_identical':True,'cross_document_object_ids_are_not_global_identity':True}
    data,records,features,feature,control,row=contexts['brep_tangent'];definition,=[r for r in records if r.is_primary and r.object_id==control['definition_record_object_id']];offset=definition.body
    def reject(label,bad):
        result=decode_patch_continuity(bytes(bad),records,features);assert not result['decoded'] and len(result['unresolved'])==1
        report['malformed_guards'].append({'case':label,'reason':result['unresolved'][0]['reason']})
    bad=bytearray(data);struct.pack_into('<I',bad,offset+3,99);reject('Unknown continuity enum',bad)
    bad=bytearray(data);struct.pack_into('<d',bad,offset+11,.8);reject('Uncontrasted scalar value remains unsupported',bad)
    bad=bytearray(data);struct.pack_into('<Q',bad,offset+46,feature['object_id']+1);reject('Continuity control owner differs',bad)
    proxy,=[r for r in records if r.is_primary and r.object_id==control['boundary_selection_record_object_id']]
    bad=bytearray(data);struct.pack_into('<Q',bad,proxy.end-10,feature['object_id']+1);reject('Boundary proxy owner differs',bad)
    recipe,=[r for r in records if r.is_primary and r.object_id==row['settings']['boundary_sources'][0]['recipe']['object_id']]
    bad=bytearray(data);where=data.index(b'edge_recipe_data',recipe.body,recipe.end);bad[where:where+4]=b'face';reject('Owned recipe has wrong topology kind',bad)
    anchor_id=row['settings']['result_body_anchors'][0]['body_anchor_object_id'];anchor,=[r for r in records if r.is_primary and r.object_id==anchor_id]
    bad=bytearray(data);struct.pack_into('<Q',bad,anchor.body+92,feature['object_id']+1);reject('Result anchor owner differs',bad)
    for filename in ('surfacetools-856ca50cf4c7/patch_rectangle.f3d','surfacetools-856ca50cf4c7/patch_circle.f3d'):
        members=read_members(ROOT/filename,zstd);stream=decode_basics(ROOT/filename,zstd)['streams'][0];data=members[stream['member']]
        records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')]);feature,=[f for f in stream['features'] if f['kind']=='SurfacePatch'];record,=[r for r in records if r.is_primary and r.object_id==feature['object_id']];body=data[record.body:record.end]
        expected=old_decode(data,records,body,feature);actual=decode_surface_tool(data,records,body,feature)
        assert actual==expected and not decode_patch_continuity(data,records,stream['features'])['decoded']
        def unexpected(*args):raise AssertionError('Sketch profile reached BRep callback')
        assert decode_surface_tool(data,records,body,feature,patch_boundary_resolver=unexpected)==expected
        report['old_default_controls'].append({'archive':filename,'frozen_source_revision':BASELINE,'default_dictionary_exact':True,'optin_callback_not_called':True})
    report['summary']={'successful_actual_exports':3,'initial_failed_owned_cases_preserved':3,'continuity_enum_contrasts':3,
        'exact_control_payload_replays':3,'typed_source_and_result_BODY_count_controls':geometry_checks,'source_before_rollback_getter_controls':3,
        'API_source_annulus_area_controls':3,'analytic_Free_result_area_matches':1,'Tangent_Curvature_area_counterexamples':2,'malformed_guards':len(report['malformed_guards']),'old_patch_default_dictionaries_exact':2,'all_owned_documents_closed_true':True}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default=str(ROOT/'patch-continuity-decoding.json'));args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(zstd);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
