"""Actual ReplaceFace target kinds, bounded guards and exact old face-edit controls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import types
from unittest.mock import patch

from decode_face_tools import decode_face_tool
from decode_replace_face_targets import REPLACE,decode_replace_face_targets
from decode_selection import known_construction_entities
from decode_placement import decode_placement
from validate_thin_extrude_operations import context as source_context

ROOT=Path(__file__).resolve().parent
DIRECTORY='replacefacetargets-670e35eedbc8'
BASELINE='7b2daac'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def context(filename,zstd):
    data,records,features,member,members=source_context(filename,zstd)
    decode_placement(data,records,features)
    return data,records,features,member,members


def validate(zstd):
    folder=ROOT/DIRECTORY;truth=json.loads((folder/'ground_truth.json').read_text())
    assert truth['terminal_status']=='Complete' and not truth['errors'] and len(truth['samples'])==3
    assert (folder/'complete.txt').is_file()
    progress=json.loads((folder/'progress.json').read_text())
    assert progress['phase']=='batch_terminal' and progress['exported_sample_count']==3 and progress['error_count']==0
    assert digest(folder/'executed-generator-source.txt')==truth['executed_generator_sha256']
    assert digest(folder/'executed-sdk-surface.txt')==truth['executed_sdk_surface_sha256']
    source=subprocess.check_output(['git','show',BASELINE+':decode_face_tools.py'],cwd=ROOT).decode()
    frozen=types.ModuleType('frozen_face_tools');exec(compile(source,'frozen_decode_face_tools.py','exec'),frozen.__dict__)
    report=dict(scope='Three actual owned ReplaceFace features with singleton independent Patch-sheet face/body targets and source Extrude face; explicit native target representation and tangent-chain control only. Existing shared selection/header codec reused.',
        interface='decode_replace_face_targets(data,records,features)->decoded/unresolved/scope; rows feature_object_id/kind/name/settings',
        shared_hook='decode_face_tool(...,replace_target_resolver=None); optional five-argument callback returns(target_descriptor_guid,replacement_target). None preserves default plane-only path and errors; opt-in admits only singleton5662 face/9716 body descriptors through existing owner/class checks.',
        integration=dict(stream='replace_face_targets',settings_field='settings',
            decode_level='Observed ReplaceFace sheet target type, tangent control and owned source/target routes; persistent face identity and regeneration unresolved',
            cleared_old_reason='Unsupported face-edit selection descriptor class',
            late_body_evidence_path='settings.replacement_target.native_evidence',
            scope='Only same-feature old target-class rejection replaced on success. Kind/discovery/timeline/unresolved_inputs and unrelated warnings remain unchanged.'),
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(folder/'ground_truth.json'),
            executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],
            sdk_runtime_sha256=truth['sdk_runtime_sha256'],fusion_version=truth['fusion_version']),
        native_schema=dict(feature_class_guid=REPLACE,prefix='0000',tangent_bool_offset=2,target_count_offset=3,target_reference_offset=7,
            source_count_offset=18,source_reference_offset=22,source_descriptor_guid='5662F619-2281-4AD9-93DC-1FCFDA1062E7',
            target_face_descriptor_guid='5662F619-2281-4AD9-93DC-1FCFDA1062E7',target_body_descriptor_guid='9716F783-676D-42E0-93F9-EBF273E7C035',
            target_face_descriptor_extent=276,target_body_descriptor_extent=290,proxy_extent=105),
        samples=[],malformed_guards=[],legacy_controls=[],
        limitations=['Only captured one-source-face replacement using independent owned Patch sheet face/body target routes is qualified; plural, arbitrary imported surfaces, other source owners and general regeneration remain unsupported.',
            'Native target classes distinguish BRepFace and BRepBody. API face argument becomes a Collection in the feature getter, while body argument/getter remain BRepBody; these representations are recorded separately.',
            'No public feature.sourceFaces getter exists; original input source faces were captured before add. No feature-source getter value is invented.',
            'Explicit recipe/context/seed BODY routes do not imply persistent selected ASM face identity, exact face-to-API matching, source/result pairing or universal lifecycle.',
            'Same-asset ASM BODY joins and numerical geometry corroboration are separate late evidence, not required to identify the native target descriptor kind.',
            'Current component contains two BRep bodies and feature.bodies contains one in these captures; no geometry is selected by ordinal, names, coordinates or bounds.'])
    contexts={}
    for actual in truth['samples']:
        filename=DIRECTORY+'/'+actual['file'];data,records,features,member,members=context(filename,zstd)
        assert actual['close_owned_document_returned'] is True and not actual['getter_errors']
        assert actual['export']['returned_success'] is True and actual['export']['sha256']==digest(ROOT/filename)
        assert actual['export']['size_bytes']==(ROOT/filename).stat().st_size
        assert actual['roll_before_feature_returned'] is True and actual['timeline_count']==actual['timeline_marker_position']
        before=copy.deepcopy(features);decoded=decode_replace_face_targets(data,records,features)
        assert features==before and len(decoded['decoded'])==1 and not decoded['unresolved']
        row,=decoded['decoded'];settings=row['settings'];fid=row['feature_object_id'];target=settings['replacement_target'];e=target['native_evidence']
        feature,=[f for f in features if f['object_id']==fid];record,=[r for r in records if r.is_primary and r.object_id==fid]
        native=data[record.body:record.end]
        for reader in (decode_face_tool,frozen.decode_face_tool):
            try:reader(data,records,native,feature,known_construction_entities(data,records,features))
            except ValueError as error:assert str(error)==report['integration']['cleared_old_reason']
            else:raise AssertionError('Default plane-only target reader unexpectedly admitted BRep target')
        expected='BRepBody' if actual['case']=='sheet_body' else 'BRepFace'
        assert target['kind']==expected and settings['is_tangent_chain']==actual['requested']['isTangentChain']
        assert settings['is_tangent_chain']==actual['input_before_add']['isTangentChain']==actual['feature_before_node']['isTangentChain']
        assert actual['input_before_add']['targetFaces']['actual_type_branch']==expected
        feature_target=actual['feature_before_node']['targetFaces']
        if expected=='BRepFace':
            assert feature_target['actual_type_branch']=='Collection' and feature_target['count']==1
            assert feature_target['items'][0]['actual_type_branch']=='BRepFace'
        else:assert feature_target['actual_type_branch']=='BRepBody'
        assert actual['exact_createInput_arguments']['target_argument_type']=='adsk::fusion::'+expected
        assert actual['exact_createInput_arguments']['source_count']==1
        source_input=actual['input_before_add']['sourceFaces']
        assert source_input['actual_type_branch']=='Collection' and source_input['count']==1 and source_input['items'][0]['actual_type_branch']=='BRepFace'
        assert actual['feature_before_node']['sourceFaces_scope'].startswith('No public feature.sourceFaces getter')
        assert actual['input_before_add']['targetBaseFeature'] is None
        assert len(settings['source_descriptor_object_ids'])==len(settings['target_descriptor_object_ids'])==settings['selected_descriptor_count']==1
        assert e['source_selection_record_object_id']==settings['source_selection_record_object_id']
        assert e['target_selection_record_object_id']==settings['target_selection_record_object_id']
        assert e['raw_role_prefix_hex']==native[:33].hex()
        assert e['source_historical_native_body_object_id']==275 and e['replacement_historical_native_body_object_id']==target['native_body_object_id']==379
        assert set(e['native_current_body_collection']['body_object_ids'])=={275,379}
        assert actual['component_bodies_after_replace']['count']==2 and actual['feature_before_node']['bodies']['count']==1
        for phase in ('feature_before_node','feature_at_timeline_end'):
            assert actual[phase]['healthState']==0 and actual[phase]['errorOrWarningMessage']==''
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=decoded,
            actual_input_target_type=actual['input_before_add']['targetFaces']['actual_type_branch'],
            actual_rolled_feature_target_type=feature_target['actual_type_branch'],native_target_kind=target['kind'],
            actual_tangent_chain=settings['is_tangent_chain'],actual_current_BRep_count=2,actual_feature_BRep_count=1,
            actual_source_getter_scope=actual['feature_before_node']['sourceFaces_scope'],exact_role_prefix_replay=True,owned_document_closed_true=True))
        contexts[actual['case']]=(data,records,features,row)
    data,records,features,row=contexts['sheet_face'];settings=row['settings'];fid=row['feature_object_id']
    by_id={r.object_id:r for r in records if r.is_primary};record=by_id[fid]
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    def reject(label,offset=None,payload=b''):
        damaged=bytearray(data)
        if offset is not None:damaged[offset:offset+len(payload)]=payload
        answer=decode_replace_face_targets(bytes(damaged),records,features)
        assert not answer['decoded'] and len(answer['unresolved'])==1,(label,answer)
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offset=offset,rejected=True,reason=answer['unresolved'][0]['reason']))
    reject('Nonboolean tangent control',record.body+2,b'\2')
    reject('Unsupported target selection group count',record.body+3,struct.pack('<I',2))
    reject('Unsupported source selection group count',record.body+18,struct.pack('<I',2))
    target_proxy=by_id[settings['target_selection_record_object_id']];target_desc=by_id[settings['target_descriptor_object_ids'][0]]
    source_desc=by_id[settings['source_descriptor_object_ids'][0]]
    reject('Target proxy owner differs',target_proxy.end-11,ref(fid+1))
    reject('Target descriptor owner differs',target_desc.end-11,ref(fid+1))
    reject('Source descriptor owner differs',source_desc.end-11,ref(fid+1))
    reject('Source and replacement proxy aliases',record.body+22,ref(settings['target_selection_record_object_id']))
    from decode_replace_face_body_routes import resolve_replace_face_target
    def bad_guid(*args):
        _,target=resolve_replace_face_target(*args);return '5A1BF548-241F-46FD-9FB5-E4B05126EB9D',target
    with patch('decode_replace_face_body_routes.resolve_replace_face_target',bad_guid):reject('Callback cannot admit an unsupported descriptor kind')
    prior=json.loads((ROOT/'face-edit-decoding.json').read_text())
    for control in prior['decodings']:
        filename=control['file'];d,rs,fs,_,_=context(filename,zstd);known=known_construction_entities(d,rs,fs);rows=[]
        prior_features={f['object_id']:f for stream in control['streams'] for f in stream['features']}
        for f in fs:
            if f['kind'] not in ('OffsetFaces','ReplaceFace','DeleteFace'):continue
            r=next(r for r in rs if r.start==f['record_offset'])
            settings=decode_face_tool(d,rs,d[r.body:r.end],f,known)
            assert settings==frozen.decode_face_tool(d,rs,d[r.body:r.end],f,known)
            assert settings==prior_features[f['object_id']]['tool_settings']
            rows.append(dict(feature_object_id=f['object_id'],kind=f['kind'],settings=settings))
        assert len(rows)==1
        empty=decode_replace_face_targets(d,rs,fs);assert not empty['decoded'] and not empty['unresolved']
        report['legacy_controls'].append(dict(archive=filename,expected_default_settings=rows,
            full_pinned_default_dictionary_exact=True,full_historical_settings_exact=True,new_wrapper_no_candidate=True))
    report['default_preservation']=dict(pinned_revision=BASELINE,pinned_face_tools_sha256=hashlib.sha256(source.encode()).hexdigest(),
        files=7,offset_controls=4,construction_plane_replace_controls=2,delete_face_controls=1,scope='Direct common decoder, no main-reader execution')
    report['source_sha256']={p:digest(ROOT/p) for p in ('decode_face_tools.py','decode_replace_face_targets.py','decode_replace_face_body_routes.py','validate_replace_face_targets.py')}
    report['validation']=dict(actual_exports=3,decoded_targets=3,native_face_targets=2,native_body_targets=1,tangent_boolean_contrasts=2,
        typed_source_routes=3,typed_target_routes=3,malformed_guards=len(report['malformed_guards']),exact_pinned_default_files=7,exact_historical_settings_files=7,no_main_calls=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default='replace-face-target-decoding.json');args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd);Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['validation'],sort_keys=True))
