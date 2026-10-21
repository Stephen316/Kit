"""Two-target sheet controls, unpaired native groups and exact prior Split outputs."""
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
from decode_split_body_multi_sheet_tools import decode_split_body_multi_sheet_tools
from decode_selection import known_construction_entities,native_proxy_references
from validate_replace_face_targets import context

ROOT=Path(__file__).resolve().parent
DIRECTORY='splitbodymultisheets-c78bec32dc3f'
BASELINE='8fc49a4'
OLD_REASON='Split sheet common tool/per-target prefix differs'


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
    frozen=types.ModuleType('frozen_multi_split_default');exec(compile(source,'frozen_decode_split.py','exec'),frozen.__dict__)
    report=dict(scope='Three actual two-target SplitBody sheet tools; common native controls reused, source descriptor/new-anchor groups separately retained, no source/result pairing or general split regeneration.',
        interface='decode_split_body_multi_sheet_tools(data,records,features)->decoded/unresolved/scope; rows feature_object_id/kind/name/settings',
        common_parser_change='None this stage: existing decode_split already supports counted two-target fields and the previously approved bounded tool_resolver hook.',
        integration=dict(merged_family='split_body_sheet_tools',variant_scope_key='multi_target_scope',settings_field='settings',
            decode_level='Observed multi-target SplitBody sheet tool, extension controls and grouped source/new-body routes; persistent topology and regeneration unresolved',
            cleared_singleton_reason=OLD_REASON,late_body_evidence_path='settings.tool.native_evidence',
            late_stream='split_body_multi_sheet_routes',
            scope='Append qualified new rows; remove only exact same-feature singleton-prefix rejection. Existing common partial settings/tool rows unchanged unless replaced by qualified new settings. Old singleton late routes consume original singleton rows only; failed variants retain old diagnostics.'),
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(folder/'ground_truth.json'),
            executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],
            sdk_runtime_sha256=truth['sdk_runtime_sha256'],fusion_version=truth['fusion_version']),
        native_schema=dict(feature_class_guid=SPLIT,per_target_count_offset=49,per_target_anchor_reference_offsets=[53,64],source_proxy_reference_offset=83,
            stored_operation_flag_offset=22,tool_proxy_reference_offset=34,
            operation_flag_scope='Literal309 agrees DcFeatureOperationIdFlag proxy attribute; no new meaning inferred from count or numeric value.',
            group_scope='Two explicit historical source descriptors and two explicitly owned new anchors are independent groups; no zip or per-source assignment.'),
        samples=[],malformed_guards=[],legacy_controls=[],singleton_controls=[],profile_negative_controls=[],
        limitations=['Only captured two-source root SplitBody and independent owned Patch-sheet face/body tools are qualified; more targets, imported contexts and arbitrary source/tool owners remain unsupported.',
            'Source descriptor order, new-anchor order, current collection order and actual API body arrays are separate. No ordinal or geometric source/result pairing is asserted.',
            'Native face/body tool classes and extension boolean are explicit. Actual input and feature getter representations are independently preserved.',
            'Definition/controller58byte record stores a shared feature owner but no proven per-source/new-body association; no such relation is invented.',
            'Typed current5 BODY membership is distinct from API feature.bodies count2 and historical selectors. Persistent selected ASMface identity, lifecycle and regeneration remain unresolved.',
            'Three failed Profile attempts remain negative controls with zero native SplitBody records; their accepted createInput does not establish Profile native coverage.'])
    contexts={}
    for actual in truth['samples']:
        filename=DIRECTORY+'/'+actual['file'];data,records,features,member,members=context(filename,zstd)
        assert actual['close_owned_document_returned'] is True and not actual['getter_errors']
        assert actual['export']['returned_success'] is True and actual['export']['sha256']==digest(ROOT/filename)
        assert actual['export']['size_bytes']==(ROOT/filename).stat().st_size
        assert actual['roll_before_feature_returned'] is True and actual['timeline_count']==actual['timeline_marker_position']
        before=copy.deepcopy(features);decoded=decode_split_body_multi_sheet_tools(data,records,features)
        assert before==features and len(decoded['decoded'])==1 and not decoded['unresolved']
        row,=decoded['decoded'];settings=row['settings'];fid=row['feature_object_id'];tool=settings['tool']
        feature,=[f for f in features if f['object_id']==fid];record,=[r for r in records if r.is_primary and r.object_id==fid]
        native=data[record.body:record.end];known=known_construction_entities(data,records,features)
        default=decode_split(data,records,native,feature,known)
        assert default==frozen.decode_split(data,records,native,feature,known)
        assert default['tool'] is None and default['tool_selection_status']=='Split tool reference unresolved'
        restored=copy.deepcopy(settings);restored['tool']=None;restored['tool_selection_status']='Split tool reference unresolved'
        assert restored==default
        singleton=decode_split_body_sheet_tools(data,records,features)
        assert not singleton['decoded'] and singleton['unresolved']==[dict(feature_object_id=fid,class_guid=SPLIT,reason=OLD_REASON)]
        expected='BRepBody' if actual['case']=='sheet_body_no_extend' else 'BRepFace'
        assert tool['entity']['kind']==expected and isinstance(tool['native_evidence'],dict)
        assert settings['is_tool_extended']==actual['requested']['isSplittingToolExtended']==actual['input_before_add']['isSplittingToolExtended']==actual['feature_before_node']['isSplittingToolExtended']
        assert actual['input_before_add']['splittingTool']['actual_type_branch']==actual['feature_before_node']['splittingTool']['actual_type_branch']==expected
        assert actual['input_before_add']['splitBodies']['actual_type_branch']=='Collection' and actual['input_before_add']['splitBodies']['count']==2
        assert actual['feature_before_node']['splitBodies']['actual_type_branch']=='Collection' and actual['feature_before_node']['splitBodies']['count']==2
        assert actual['input_before_add']['targetBaseFeature'] is None
        assert settings['input_body_count']==len(settings['per_target_record_object_ids'])==len(settings['target_descriptor_object_ids'])==2
        assert len(set(settings['per_target_record_object_ids']))==len(set(settings['target_descriptor_object_ids']))==2
        assert settings['stored_operation_flag']==struct.unpack_from('<Q',native,22)[0]==309
        assert actual['component_bodies_after_split']['count']==5 and actual['feature_before_node']['bodies']['count']==2
        for phase in ('feature_before_node','feature_at_timeline_end'):
            assert actual[phase]['healthState']==0 and actual[phase]['errorOrWarningMessage']==''
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=decoded,
            expected_default_settings=default,expected_singleton_summary=singleton,
            actual_input_tool_type=expected,actual_feature_tool_type=expected,actual_input_body_count=2,actual_feature_split_body_count=2,
            actual_is_tool_extended=settings['is_tool_extended'],actual_current_BRep_count=5,actual_feature_BRep_count=2,
            stored_common_prefix_hex=native[:94].hex(),source_to_new_result_pairing=None,owned_document_closed_true=True))
        contexts[actual['case']]=(data,records,features,row)
    data,records,features,row=contexts['sheet_face_no_extend'];settings=row['settings'];fid=row['feature_object_id']
    by_id={r.object_id:r for r in records if r.is_primary};record=by_id[fid]
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    def reject(label,offset=None,payload=b''):
        damaged=bytearray(data)
        if offset is not None:damaged[offset:offset+len(payload)]=payload
        answer=decode_split_body_multi_sheet_tools(bytes(damaged),records,features)
        assert not answer['decoded'] and len(answer['unresolved'])==1,(label,answer)
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offset=offset,rejected=True,reason=answer['unresolved'][0]['reason']))
    reject('Nonboolean extension control',record.body+6,b'\2')
    reject('Operation flag disagrees with native attribute',record.body+22,struct.pack('<Q',310))
    reject('Uncaptured per-target count3',record.body+49,struct.pack('<I',3))
    reject('Duplicate newly owned anchor list reference',record.body+64,ref(settings['per_target_record_object_ids'][0]))
    proxy=by_id[settings['tool_selection_record_object_id']];descriptor=by_id[settings['tool_descriptor_object_id']]
    reject('Tool proxy owner differs',proxy.end-11,ref(fid+1))
    reject('Tool descriptor owner differs',descriptor.end-11,ref(fid+1))
    target_proxy=by_id[settings['target_selection_record_object_id']]
    reject('Duplicate historical source descriptor references',target_proxy.body+17,ref(settings['target_descriptor_object_ids'][0]))
    with patch('decode_split_body_multi_sheet_routes.resolve_split_body_multi_sheet_tool',lambda *args:None):reject('Unresolved tool cannot become complete settings')
    prior=json.loads((ROOT/'split-body-sheet-tool-decoding.json').read_text())
    for control in prior['legacy_controls']:
        filename=control['archive'];d,rs,fs,_,_=context(filename,zstd);known=known_construction_entities(d,rs,fs);rows=[]
        for f in fs:
            if f.get('class_guid')!=SPLIT:continue
            r=next(r for r in rs if r.start==f['record_offset']);default=decode_split(d,rs,d[r.body:r.end],f,known)
            assert default==frozen.decode_split(d,rs,d[r.body:r.end],f,known)
            rows.append(dict(feature_object_id=f['object_id'],settings=default))
        assert rows==control['expected_default_settings']
        empty=decode_split_body_multi_sheet_tools(d,rs,fs);assert not empty['decoded'] and not empty['unresolved']
        report['legacy_controls'].append(dict(archive=filename,full_prior_default_settings_exact=True,new_wrapper_no_candidate=True))
    for control in prior['samples']:
        filename=control['archive'];d,rs,fs,_,_=context(filename,zstd)
        assert decode_split_body_sheet_tools(d,rs,fs)==control['expected_decoded']
        empty=decode_split_body_multi_sheet_tools(d,rs,fs);assert not empty['decoded'] and not empty['unresolved']
        report['singleton_controls'].append(dict(archive=filename,full_prior_singleton_summary_exact=True,new_wrapper_no_candidate=True))
    negatives=json.loads((ROOT/'split-body-profile-attempts.json').read_text())
    for sample in negatives['samples']:
        filename=sample['archive'];d,rs,fs,_,_=context(filename,zstd)
        assert not any(r.is_primary and r.class_guid==SPLIT for r in rs)
        empty=decode_split_body_multi_sheet_tools(d,rs,fs);assert not empty['decoded'] and not empty['unresolved']
        report['profile_negative_controls'].append(dict(archive=filename,native_SplitBody_records=0,new_wrapper_no_candidate=True))
    report['default_preservation']=dict(pinned_revision=BASELINE,pinned_decode_split_sha256=hashlib.sha256(source.encode()).hexdigest(),
        plane_controls=5,singleton_sheet_controls=3,negative_Profile_controls=3,scope='Direct helpers only; no main-reader execution')
    report['source_sha256']={p:digest(ROOT/p) for p in ('decode_split.py','decode_split_body_sheet_tools.py','decode_split_body_sheet_routes.py','decode_split_body_multi_sheet_tools.py','decode_split_body_multi_sheet_routes.py','validate_split_body_multi_sheet_tools.py')}
    report['validation']=dict(actual_exports=3,decoded_two_target_tools=3,face_tools=2,body_tools=1,extension_boolean_contrasts=2,
        exact_new_default_partial_settings=3,malformed_guards=len(report['malformed_guards']),exact_old_plane_default_files=5,
        exact_singleton_sheet_summary_files=3,negative_Profile_files=3,no_main_calls=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default='split-body-multi-sheet-tool-decoding.json');args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd);Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['validation'],sort_keys=True))
