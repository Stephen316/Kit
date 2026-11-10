"""Saved SplitBody sheet controls, exact old partial state and bounded tool proof."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import types
from unittest.mock import patch

from decode_split import decode_split
from decode_split_body_sheet_tools import decode_split_body_sheet_tools,SPLIT
from decode_selection import known_construction_entities
from validate_replace_face_targets import context

ROOT=Path(__file__).resolve().parent
DIRECTORY='splitbodysheets-b7548618fb65'
BASELINE='388f658'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(zstd):
    folder=ROOT/DIRECTORY;truth=json.loads((folder/'ground_truth.json').read_text())
    assert truth['terminal_status']=='Complete' and not truth['errors'] and len(truth['samples'])==3
    assert (folder/'complete.txt').is_file()
    progress=json.loads((folder/'progress.json').read_text())
    assert progress['phase']=='batch_terminal' and progress['exported_sample_count']==3 and progress['error_count']==0
    assert digest(folder/'executed-generator-source.txt')==truth['executed_generator_sha256']
    assert digest(folder/'executed-sdk-surface.txt')==truth['executed_sdk_surface_sha256']
    source=subprocess.check_output(['git','show',BASELINE+':decode_split.py'],cwd=ROOT).decode()
    frozen=types.ModuleType('frozen_split_sheet_default');exec(compile(source,'frozen_decode_split.py','exec'),frozen.__dict__)
    report=dict(scope='Three actual singleton SplitBody controls with independent Patch-sheet face/body tools; explicit native tool/source/result references, extension toggle and common operation-flag agreement. No geometry/ordinal identity selection or regeneration.',
        interface='decode_split_body_sheet_tools(data,records,features)->decoded/unresolved/scope; rows feature_object_id/kind/name/settings',
        shared_hook='decode_split(...,tool_resolver=None); default plane resolution and unresolved None behavior exact. Five-argument callback returns qualified tool.entity.kind BRepFace/BRepBody plus native_evidence; unchanged header/proxy/operationflag/count parsing.',
        integration=dict(stream='split_body_sheet_tools',settings_field='settings',
            decode_level='Observed SplitBody sheet face/body tool, extension control and typed source/result routes; persistent topology and regeneration unresolved',
            old_partial_tool_status='Split tool reference unresolved',late_body_evidence_path='settings.tool.native_evidence',
            scope='Default already publishes partial settings and decoded tool row. Replace only exact qualified partial settings/decode_level, add optional sidecars; no tool summary/error/kind/discovery/timeline changes.'),
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(folder/'ground_truth.json'),
            executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],
            sdk_runtime_sha256=truth['sdk_runtime_sha256'],fusion_version=truth['fusion_version']),
        native_schema=dict(feature_class_guid=SPLIT,prefix='000100000000',extension_boolean_offset=6,definition_reference_offset=11,
            stored_operation_flag_offset=22,tool_count_offset=30,tool_proxy_reference_offset=34,per_target_count_offset=49,per_target_reference_start=53,
            target_proxy_rule='After53+11*count, require0000000001000000 then11byte proxy reference',
            tool_face_descriptor_guid='5662F619-2281-4AD9-93DC-1FCFDA1062E7',tool_body_descriptor_guid='9716F783-676D-42E0-93F9-EBF273E7C035',
            operation_flag_scope='Literal native uint64 agrees DcFeatureOperationIdFlag proxy attribute; no new enum or topology meaning inferred'),
        samples=[],malformed_guards=[],legacy_controls=[],
        limitations=['Qualified family has one historical target and independent owned Patch-sheet tool; arbitrary imported targets, plural sheet/body selections and general extension remain unsupported.',
            'The tool face/body distinction comes from native descriptor classes. Requested and actual API representations remain independently recorded.',
            'Stored extension boolean agrees actual input/feature getters. A small sheet successfully extends in the captured case; no algorithm for general surface extension is reconstructed.',
            'Historical source, unchanged tool sheet and genuinely owned new result references are distinct. Current body counts and API collections do not create an ordinal source/result pairing.',
            'Native recipes and stored BODY/ASM ID joins do not establish persistent selected ASM face identity, API handle identity, lifecycle or regeneration.',
            'The prior common decoder returns successful partial settings with toolNone; this is preserved exactly unless the new pure tool proof succeeds.'])
    contexts={}
    for actual in truth['samples']:
        filename=DIRECTORY+'/'+actual['file'];data,records,features,member,members=context(filename,zstd)
        assert actual['close_owned_document_returned'] is True and not actual['getter_errors']
        assert actual['export']['returned_success'] is True and actual['export']['sha256']==digest(ROOT/filename)
        assert actual['export']['size_bytes']==(ROOT/filename).stat().st_size
        assert actual['roll_before_feature_returned'] is True and actual['timeline_count']==actual['timeline_marker_position']
        before=copy.deepcopy(features);decoded=decode_split_body_sheet_tools(data,records,features)
        assert before==features and len(decoded['decoded'])==1 and not decoded['unresolved']
        row,=decoded['decoded'];settings=row['settings'];fid=row['feature_object_id'];tool=settings['tool']
        feature,=[f for f in features if f['object_id']==fid];record,=[r for r in records if r.is_primary and r.object_id==fid]
        body=data[record.body:record.end];known=known_construction_entities(data,records,features)
        default=decode_split(data,records,body,feature,known)
        assert default==frozen.decode_split(data,records,body,feature,known)
        assert default['tool'] is None and default['tool_selection_status']=='Split tool reference unresolved'
        restored=copy.deepcopy(settings);restored['tool']=None;restored['tool_selection_status']='Split tool reference unresolved'
        assert restored==default
        expected='BRepBody' if actual['case']=='sheet_body_no_extend' else 'BRepFace'
        assert tool is not None and tool['entity']['kind']==expected and isinstance(tool['native_evidence'],dict)
        assert 'tool_selection_status' not in settings
        assert settings['is_tool_extended']==actual['requested']['isSplittingToolExtended']==actual['input_before_add']['isSplittingToolExtended']==actual['feature_before_node']['isSplittingToolExtended']
        assert actual['input_before_add']['splittingTool']['actual_type_branch']==actual['feature_before_node']['splittingTool']['actual_type_branch']==expected
        assert actual['exact_createInput_arguments']['splitting_tool_argument_type']=='adsk::fusion::'+expected
        assert actual['input_before_add']['splitBodies']['actual_type_branch']=='BRepBody'
        assert actual['feature_before_node']['splitBodies']['actual_type_branch']=='Collection' and actual['feature_before_node']['splitBodies']['count']==1
        assert actual['input_before_add']['targetBaseFeature'] is None
        assert settings['input_body_count']==len(settings['per_target_record_object_ids'])==len(settings['target_descriptor_object_ids'])==1
        assert settings['stored_operation_flag']==306 and struct.unpack_from('<Q',body,22)[0]==settings['stored_operation_flag']
        assert body[6]==int(settings['is_tool_extended'])
        assert actual['component_bodies_after_split']['count']==3 and actual['feature_before_node']['bodies']['count']==1
        for phase in ('feature_before_node','feature_at_timeline_end'):
            assert actual[phase]['healthState']==0 and actual[phase]['errorOrWarningMessage']==''
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=decoded,expected_default_settings=default,
            actual_input_tool_type=actual['input_before_add']['splittingTool']['actual_type_branch'],actual_feature_tool_type=actual['feature_before_node']['splittingTool']['actual_type_branch'],
            actual_input_split_body_type='BRepBody',actual_feature_split_bodies_type='Collection',actual_is_tool_extended=settings['is_tool_extended'],
            actual_current_BRep_count=3,actual_feature_BRep_count=1,stored_common_prefix_hex=body[:83].hex(),owned_document_closed_true=True))
        contexts[actual['case']]=(data,records,features,row)
    data,records,features,row=contexts['sheet_face_no_extend'];settings=row['settings'];fid=row['feature_object_id']
    by_id={r.object_id:r for r in records if r.is_primary};record=by_id[fid]
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    def reject(label,offset=None,payload=b''):
        damaged=bytearray(data)
        if offset is not None:damaged[offset:offset+len(payload)]=payload
        answer=decode_split_body_sheet_tools(bytes(damaged),records,features)
        assert not answer['decoded'] and len(answer['unresolved'])==1,(label,answer)
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offset=offset,rejected=True,reason=answer['unresolved'][0]['reason']))
    reject('Nonboolean extension control',record.body+6,b'\2')
    reject('Operation flag disagrees with proxy attribute',record.body+22,struct.pack('<Q',307))
    reject('Uncaptured tool count',record.body+30,struct.pack('<I',2))
    reject('Uncaptured per-target count',record.body+49,struct.pack('<I',2))
    proxy=by_id[settings['tool_selection_record_object_id']];descriptor=by_id[settings['tool_descriptor_object_id']]
    target_descriptor=by_id[settings['target_descriptor_object_ids'][0]]
    reject('Tool proxy feature owner differs',proxy.end-11,ref(fid+1))
    reject('Tool descriptor feature owner differs',descriptor.end-11,ref(fid+1))
    reject('Target descriptor feature owner differs',target_descriptor.end-11,ref(fid+1))
    with patch('decode_split_body_sheet_routes.resolve_split_body_sheet_tool',lambda *args:None):reject('Unresolved callback must not publish complete settings')
    from decode_split_body_sheet_routes import resolve_split_body_sheet_tool
    def wrong_kind(*args):
        tool=resolve_split_body_sheet_tool(*args);tool['entity']['kind']='ConstructionPlane';return tool
    with patch('decode_split_body_sheet_routes.resolve_split_body_sheet_tool',wrong_kind):reject('Opt-in callback cannot substitute another entity kind')
    prior=json.loads((ROOT/'split-decoding.json').read_text())
    for control in prior['decodings']:
        filename=control['file'];d,rs,fs,_,_=context(filename,zstd);known=known_construction_entities(d,rs,fs);rows=[]
        prior_features={f['object_id']:f for stream in control['streams'] for f in stream['features']}
        for f in fs:
            if f.get('class_guid')!=SPLIT:continue
            r=next(r for r in rs if r.start==f['record_offset'])
            default=decode_split(d,rs,d[r.body:r.end],f,known)
            assert default==frozen.decode_split(d,rs,d[r.body:r.end],f,known)
            assert default==prior_features[f['object_id']]['tool_settings']
            rows.append(dict(feature_object_id=f['object_id'],settings=default))
        assert len(rows)==1
        empty=decode_split_body_sheet_tools(d,rs,fs);assert not empty['decoded'] and not empty['unresolved']
        report['legacy_controls'].append(dict(archive=filename,expected_default_settings=rows,full_pinned_default_dictionary_exact=True,
            full_historical_settings_exact=True,new_wrapper_no_candidate=True))
    report['default_preservation']=dict(pinned_revision=BASELINE,pinned_decode_split_sha256=hashlib.sha256(source.encode()).hexdigest(),
        old_files=5,new_partial_files=3,scope='Direct helper comparison only, no main-reader execution or changed diagnostics on default path')
    report['source_sha256']={p:digest(ROOT/p) for p in ('decode_split.py','decode_split_body_sheet_tools.py','decode_split_body_sheet_routes.py','validate_split_body_sheet_tools.py')}
    report['validation']=dict(actual_exports=3,decoded_sheet_tools=3,face_tools=2,body_tools=1,extension_boolean_contrasts=2,
        exact_new_default_partial_settings=3,malformed_guards=len(report['malformed_guards']),exact_pinned_old_files=5,exact_historical_settings_files=5,no_main_calls=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default='split-body-sheet-tool-decoding.json');args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd);Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['validation'],sort_keys=True))
