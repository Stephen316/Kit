"""Two partial-capture Trim sources, opaque recipe replay and exact old surface controls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import types
from unittest.mock import patch

from decode_profiles import decode_profiles
from decode_surface_tools import decode_surface_tool
from decode_surface_trim_tools import TRIM,decode_surface_trim_tools
from decode_selection import known_construction_entities
from validate_replace_face_targets import context as source_context

ROOT=Path(__file__).resolve().parent
BASELINE='a8e8e93'
CAPTURES=('surfacetrimtools-c507461585b5','surfacetrimtools-ce3c7e1c703e')
OLD_FILES=('surfacebounds-ac801bb00fae/extend_natural.f3d', 'surfacebounds-ac801bb00fae/extend_tangent.f3d', 'surfacebounds-ac801bb00fae/extend_perpendicular.f3d', 'surfacebounds-ac801bb00fae/extend_perpendicular_negative.f3d', 'surfacebounds-ac801bb00fae/extend_aligned.f3d', 'surfacebounds-ac801bb00fae/extend_two_edges.f3d', 'surfacebounds-ac801bb00fae/untrim_internal.f3d', 'surfacebounds-ac801bb00fae/untrim_external.f3d', 'surfacebounds-ac801bb00fae/untrim_all.f3d', 'surfacebounds-ac801bb00fae/untrim_manual.f3d', 'surfacebounds-ac801bb00fae/ruled_tangent.f3d', 'surfacebounds-ac801bb00fae/ruled_normal.f3d', 'surfacebounds-ac801bb00fae/ruled_direction.f3d', 'surfacebounds-ac801bb00fae/ruled_mitered.f3d', 'surfacebounds-ac801bb00fae/trim_positive.f3d', 'surfacebounds-ac801bb00fae/trim_negative.f3d', 'surfacebounds-8804bbf80755/extend_no_chain.f3d', 'surfacetools-856ca50cf4c7/patch_rectangle.f3d', 'surfacetools-856ca50cf4c7/patch_circle.f3d', 'surfacetools-856ca50cf4c7/offset_positive.f3d', 'surfacetools-856ca50cf4c7/offset_negative.f3d', 'surfacetools-856ca50cf4c7/offset_rounded.f3d', 'surfacetools-856ca50cf4c7/stitch_tight.f3d', 'surfacetools-856ca50cf4c7/stitch_loose.f3d', 'surfacetools-856ca50cf4c7/unstitch_face.f3d', 'surfacetools-856ca50cf4c7/unstitch_chain.f3d', 'surfacetools-856ca50cf4c7/reverse_normal.f3d', 'surfacetools-856ca50cf4c7/delete_opening.f3d')
SURFACE_KINDS=('SurfacePatch','SurfaceOffset','SurfaceStitch','Unstitch','ReverseNormal','SurfaceDeleteFace','SurfaceExtend','SurfaceUntrim','SurfaceRuled','SurfaceTrim')


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def context(filename,zstd):
    data,records,features,member,members=source_context(filename,zstd)
    decode_profiles(data,records,features)
    return data,records,features,member,members


def outcome(reader,*args):
    try:return dict(settings=reader(*args))
    except (ValueError,KeyError,IndexError,struct.error) as error:return dict(error_type=type(error).__name__,reason=str(error))


def validate(zstd):
    source=subprocess.check_output(['git','show',BASELINE+':decode_surface_tools.py'],cwd=ROOT).decode()
    frozen=types.ModuleType('frozen_surface_trim_default');exec(compile(source,'frozen_decode_surface_tools.py','exec'),frozen.__dict__)
    report=dict(scope='Two actual healthy SurfaceTrim face/body source tools exported from interrupted batches. No batch completion is asserted. Common recipe/target parsing retained; selected-cell semantics and uncaptured sketch-Line support unresolved.',
        interface='decode_surface_trim_tools(data,records,features)->decoded/unresolved/scope; rows feature_object_id/kind/name/settings',
        shared_hook='decode_surface_tool(...,trim_tool_resolver=None). Default ConstructionPlane path unchanged; opt-in five-argument callback closes over features, requires matching owner/selection IDs and BRepFace/BRepBody kind, and cannot overwrite common recipe/target/status fields.',
        integration=dict(stream='surface_trim_tools',settings_field='settings',cleared_old_reason='Only observed planar trim tools supported',
            decode_level='Observed SurfaceTrim face/body tool and typed source; selected-cell recipe, persistent topology and regeneration unresolved',
            source_stream='surface_trim_sources',source_feature_field='surface_trim_source',
            native_source_evidence_path='settings.tool.native_source_evidence',
            scope='Only qualified same-feature old plane-only rejection replaced. Existing target/recipe bytes and unresolved cell status retained; old surface controls and unrelated diagnostics exact.'),
        execution_scope=dict(live_work_stopped_after_user_crash_report=True,live_calls_made_by_validator=False,
            filesystem_evidence='Both truth files lack terminal_status and both folders lack complete.txt; last journal/progress phase records owned document close returnedTrue after one valid export.',
            separately_reported_session_evidence='User reported repeated Fusion crashes; parent observed each owning process absent after the captured case. These observations do not establish a crash cause or universal API failure.',
            uncaptured_case='sketch_line',uncaptured_case_status='No export/native proof; remains unsupported; planned generator is not execution evidence.'),
        captures=[],samples=[],malformed_guards=[],legacy_controls=[],
        limitations=['Only captured singleton BRepFace/BRepBody tool sources from owned Patch sheets are qualified. No SketchLine implementation or source-kind allowance is added.',
            'These are valid case exports/healthy features/owned closes within PartialNoTerminalMarker folders, not completed capture batches; empty case-error arrays do not prove process or batch success.',
            'Native selected-cell recipe wrapper/definition identities and full bytes are preserved. Actual API selected cell indices remain enumeration indices, with no native recipe/kept-region mapping inferred.',
            'Historical source BODY/component routes do not prove persistent selected ASMface/API handle identity, target/result pairing, lifecycle or regeneration.',
            'Target proxy/descriptor ownership remains the existing common parser evidence; no additional target topology semantics are invented.',
            'No crash cause, universal Trim support restriction or safe retry recommendation is inferred. Live API/UI/capture work stopped by the parent after the crash report; validation is offline only.'])
    samples=[]
    for directory in CAPTURES:
        folder=ROOT/directory;truth=json.loads((folder/'ground_truth.json').read_text());progress=json.loads((folder/'progress.json').read_text())
        assert 'terminal_status' not in truth and not (folder/'complete.txt').exists()
        assert len(truth['samples'])==1 and not truth['errors']
        assert progress['phase']=='owned_document_close_returned' and progress['returned'] is True and progress['save'] is False
        assert progress['sample_count']==1 and progress['error_count']==0
        assert digest(folder/'executed-generator-source.txt')==truth['executed_generator_sha256']
        assert digest(folder/'executed-sdk-surface.txt')==truth['executed_sdk_surface_sha256']
        entrypoint=truth.get('entrypoint_provenance')
        if entrypoint:assert digest(folder/entrypoint['executed_snapshot'])==entrypoint['sha256']
        report['captures'].append(dict(directory=directory,state='PartialNoTerminalMarker',ground_truth_sha256=digest(folder/'ground_truth.json'),
            planned_cases=truth['planned_cases'],exported_cases=[s['case'] for s in truth['samples']],terminal_status=None,complete_marker_present=False,
            last_progress=progress,executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],
            sdk_runtime_sha256=truth['sdk_runtime_sha256'],fusion_version=truth['fusion_version'],entrypoint_provenance=entrypoint,
            case_errors=truth['errors'],scope='Observed capture files only; batch success and failure cause not inferred'))
        samples.extend((directory,a) for a in truth['samples'])
    contexts={};recipe_bytes=0
    for directory,actual in samples:
        filename=directory+'/'+actual['file'];data,records,features,member,members=context(filename,zstd)
        assert actual['close_owned_document_returned'] is True and not actual['getter_errors']
        assert actual['export']['returned_success'] is True and actual['export']['sha256']==digest(ROOT/filename)
        assert actual['export']['size_bytes']==(ROOT/filename).stat().st_size
        assert actual['timeline_count']==actual['timeline_marker_position'] and actual['roll_before_feature_returned'] is True
        assert actual['createInput_returned_nonnull'] is True and actual['add_returned_feature'] is True and actual['trim_status']=='FeatureReturned'
        assert actual['input_identity']['isValid'] is True and not actual['input_identity']['getter_errors']
        assert actual['input_targetBaseFeature'] is None
        before=copy.deepcopy(features);decoded=decode_surface_trim_tools(data,records,features)
        assert before==features and len(decoded['decoded'])==1 and not decoded['unresolved']
        row,=decoded['decoded'];settings=row['settings'];fid=row['feature_object_id'];tool=settings['tool']
        feature,=[f for f in features if f['object_id']==fid];record,=[r for r in records if r.is_primary and r.object_id==fid]
        body=data[record.body:record.end];known=known_construction_entities(data,records,features)
        default=outcome(decode_surface_tool,data,records,body,feature,known)
        assert default==outcome(frozen.decode_surface_tool,data,records,body,feature,known)==dict(error_type='ValueError',reason='Only observed planar trim tools supported')
        expected='BRepFace' if actual['case']=='sheet_face' else 'BRepBody'
        assert tool['entity']['kind']==actual['input_actual_trimTool']['actual_type_branch']==actual['feature_before_node']['trimTool']['actual_type_branch']==expected
        assert tool['selection_record_object_id']==settings['tool_selection']['selection_record_object_id']
        evidence=tool['native_source_evidence'];assert evidence['feature_object_id']==fid and evidence['tool_selection_record_object_id']==tool['selection_record_object_id']
        assert evidence['tool_descriptor_object_ids']==settings['tool_selection']['descriptor_object_ids']
        assert settings['tool_selection']['stored_descriptor_count']==settings['target_selection']['stored_descriptor_count']==1
        definition,=[r for r in records if r.is_primary and r.object_id==settings['recipe_definition_object_id']]
        wrapper,=[r for r in records if r.is_primary and r.object_id==settings['recipe_record_object_id']]
        assert data[definition.body:definition.end].hex()==settings['stored_recipe_payload_hex']
        assert data[wrapper.body:wrapper.end]==bytes.fromhex('000001000000')+b'\1'+struct.pack('<Q',definition.object_id)+bytes(2)
        assert settings['trim_cell_status']=='Selected-cell semantics and bounded-face recipe undecoded; original recipe retained'
        recipe_bytes+=definition.end-definition.body
        for phase in ('feature_before_node','feature_at_timeline_end'):
            assert actual[phase]['healthState']==0 and actual[phase]['errorOrWarningMessage']=='' and not actual[phase]['getter_errors']
        assert len(actual['component_bodies_after_trim'])==2 and len(actual['feature_at_timeline_end']['bodies'])==1
        selected=[cell['api_enumeration_index'] for cell in actual['input_cells_after_selection'] if cell['isSelected']]
        assert selected==actual['selected_input_cell_indices'] and selected
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),capture_state='PartialNoTerminalMarker',expected_decoded=decoded,
            expected_default_failure=default,actual_input_tool_type=actual['input_actual_trimTool']['actual_type_branch'],actual_feature_tool_type=actual['feature_before_node']['trimTool']['actual_type_branch'],
            actual_selected_input_cell_enumeration_indices=selected,native_cell_recipe_assignment=None,
            exact_recipe_wrapper_payload_hex=data[wrapper.body:wrapper.end].hex(),exact_selected_cell_recipe_bytes_replayed=definition.end-definition.body,
            actual_current_BRep_count=2,actual_timeline_end_feature_BRep_count=1,owned_case_exported_and_closed_true=True,batch_terminal_success_claimed=False))
        contexts[actual['case']]=(data,records,features,row)
    assert set(contexts)=={'sheet_face','sheet_body'}
    data,records,features,row=contexts['sheet_face'];settings=row['settings'];fid=row['feature_object_id'];by_id={r.object_id:r for r in records if r.is_primary};record=by_id[fid]
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    def reject(label,offset=None,payload=b''):
        damaged=bytearray(data)
        if offset is not None:damaged[offset:offset+len(payload)]=payload
        answer=decode_surface_trim_tools(bytes(damaged),records,features)
        assert not answer['decoded'] and len(answer['unresolved'])==1,(label,answer)
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offset=offset,rejected=True,reason=answer['unresolved'][0]['reason']))
    reject('Reserved Trim prefix differs',record.body,b'\1')
    wrapper=by_id[settings['recipe_record_object_id']]
    reject('Selected-cell recipe wrapper framing differs',wrapper.body+2,b'\2')
    reject('Unobserved target count2',record.body+40,struct.pack('<I',2))
    proxy=by_id[settings['tool_selection']['selection_record_object_id']];target_descriptor=by_id[settings['target_selection']['descriptor_object_ids'][0]]
    reject('Tool proxy owner differs',proxy.end-11,ref(fid+1))
    reject('Target descriptor owner differs',target_descriptor.end-11,ref(fid+1))
    from decode_surface_trim_sources import resolve_surface_trim_source
    def callback_guard(label,change):
        def bad(*args):
            answer=resolve_surface_trim_source(*args);change(answer);return answer
        with patch('decode_surface_trim_sources.resolve_surface_trim_source',bad):
            answer=decode_surface_trim_tools(data,records,features)
            assert not answer['decoded'] and len(answer['unresolved'])==1
            report['malformed_guards'].append(dict(guard=label,rejected=True,reason=answer['unresolved'][0]['reason']))
    callback_guard('Callback source selection differs',lambda a:a.update(selection_record_object_id=fid))
    callback_guard('Callback native owner differs',lambda a:a['native_source_evidence'].update(feature_object_id=fid+1))
    callback_guard('Callback native evidence missing',lambda a:a.pop('native_source_evidence'))
    callback_guard('Uncaptured SketchLine callback kind rejected',lambda a:a['entity'].update(kind='SketchLine'))
    historical={}
    for filename in ('surface-tool-decoding.json','surface-boundary-decoding.json'):
        for sample in json.loads((ROOT/filename).read_text())['decodings']:
            historical[sample['file']]={f['object_id']:f for stream in sample['streams'] for f in stream['features']}
    published=old_trim=0
    for filename in OLD_FILES:
        d,rs,fs,_,_=context(filename,zstd);known=known_construction_entities(d,rs,fs);rows=[]
        for f in fs:
            if f['kind'] not in SURFACE_KINDS:continue
            r=next(r for r in rs if r.start==f['record_offset']);args=(d,rs,d[r.body:r.end],f,known)
            current=outcome(decode_surface_tool,*args);assert current==outcome(frozen.decode_surface_tool,*args)
            old_feature=historical.get(filename,{}).get(f['object_id'],{})
            historical_exact=None
            if 'tool_settings'in old_feature and 'settings'in current:
                assert current['settings']==old_feature['tool_settings'];historical_exact=True
            published+=int('settings'in current);old_trim+=int(f['kind']=='SurfaceTrim')
            rows.append(dict(feature_object_id=f['object_id'],kind=f['kind'],full_pinned_default_outcome_exact=True,
                full_historical_settings_exact=historical_exact,current_decoded='settings'in current,
                outcome_sha256=hashlib.sha256(json.dumps(current,sort_keys=True).encode()).hexdigest()))
        assert rows
        empty=decode_surface_trim_tools(d,rs,fs);assert not empty['decoded'] and not empty['unresolved']
        report['legacy_controls'].append(dict(archive=filename,comparisons=rows,new_wrapper_no_candidate=True))
    report['default_preservation']=dict(pinned_revision=BASELINE,pinned_surface_tools_sha256=hashlib.sha256(source.encode()).hexdigest(),
        legacy_files=len(OLD_FILES),legacy_decoded_surface_features=published,old_ConstructionPlane_Trim_features=old_trim,
        scope='Direct common decoder only; full pinned dictionaries/errors compared, historical settings compared when published. No main-reader execution.')
    report['source_sha256']={p:digest(ROOT/p) for p in ('decode_surface_tools.py','decode_surface_trim_tools.py','decode_surface_trim_sources.py','validate_surface_trim_tools.py')}
    report['validation']=dict(actual_exports=2,healthy_features=2,owned_case_closes_true=2,partial_capture_folders=2,terminal_complete_batches=0,
        decoded_face_sources=1,decoded_body_sources=1,SketchLine_support_added=False,opaque_recipe_bytes_replayed=recipe_bytes,
        malformed_guards=len(report['malformed_guards']),exact_legacy_surface_files=len(OLD_FILES),no_live_calls=True,no_main_calls=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default='surface-trim-tool-decoding.json');args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd);Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['validation'],sort_keys=True))
