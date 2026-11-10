"""Three actual SketchLine trims, bounded common-hook guards and exact old controls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import types
from unittest.mock import patch

from decode_selection import known_construction_entities
from decode_surface_tools import decode_surface_tool
from decode_surface_trim_lines import decode_surface_trim_lines
from decode_surface_trim_tools import decode_surface_trim_tools
from decode_surface_trim_line_sources import resolve_surface_trim_line_source
from validate_surface_trim_tools import context, outcome, OLD_FILES, SURFACE_KINDS

ROOT=Path(__file__).resolve().parent
BASELINE='e8af2ba'
FILES=('surfacetrimtools-ca26d21e7ad9/sketch_line.f3d',
       'surfacetrimtools-650ca09579b1/sketch_line_offset_positive.f3d',
       'surfacetrimtools-650ca09579b1/sketch_line_reversed_negative.f3d')
FACE_BODY=('surfacetrimtools-c507461585b5/sheet_face.f3d',
           'surfacetrimtools-ce3c7e1c703e/sheet_body.f3d',
           'surfacetrimtools-560510587441/sheet_face.f3d',
           'surfacetrimtools-ca26d21e7ad9/sheet_body.f3d')


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(zstd):
    checks=[];samples=[];captures={};guards=[];legacy=[];facebody=[];contexts=[]
    def check(label,condition):
        if not condition:raise AssertionError(label)
        checks.append(label)
    source=subprocess.check_output(['git','show',BASELINE+':decode_surface_tools.py'],cwd=ROOT).decode()
    frozen=types.ModuleType('frozen_surface_line_default');exec(compile(source,'frozen_surface_default.py','exec'),frozen.__dict__)
    recipe_bytes=0
    for archive in FILES:
        directory,filename=archive.split('/');folder=ROOT/directory;truth=json.loads((folder/'ground_truth.json').read_text())
        actual=next(s for s in truth['samples'] if s['file']==filename)
        check(archive+' terminal complete',truth['terminal_status']=='Complete' and not truth['errors'] and (folder/'complete.txt').is_file())
        check(archive+' executed generator/SDK snapshots exact',digest(folder/'executed-generator-source.txt')==truth['executed_generator_sha256'] and digest(folder/'executed-sdk-surface.txt')==truth['executed_sdk_surface_sha256'])
        entry=truth.get('entrypoint_provenance')
        if entry:check(archive+' executed entrypoint snapshot exact',digest(folder/entry['executed_snapshot'])==entry['sha256'])
        check(archive+' export and owned close exact',actual['close_owned_document_returned'] is True and actual['export']['returned_success'] is True and actual['export']['sha256']==digest(ROOT/archive) and actual['export']['size_bytes']==(ROOT/archive).stat().st_size)
        check(archive+' successful lifecycle finalization',actual['trim_wrappers_released_before_move_to_end'] is True and actual['post_wrapper_release_compute_all_returned'] is True and actual['finalization']['ok'] is True)
        check(archive+' no getter errors',not actual['getter_errors'])
        for phase in ('feature_before_node','feature_at_timeline_end'):
            check(archive+' healthy '+phase,actual[phase]['healthState']==0 and actual[phase]['errorOrWarningMessage']=='' and not actual[phase]['getter_errors'])
        data,records,features,member,members=context(archive,zstd);before=copy.deepcopy(features)
        decoded=decode_surface_trim_lines(data,records,features)
        check(archive+' exactly one bounded Line Trim',len(decoded['decoded'])==1 and not decoded['unresolved'] and features==before)
        row,=decoded['decoded'];settings=row['settings'];fid=row['feature_object_id'];tool=settings['tool'];evidence=tool['native_source_evidence']
        f=next(f for f in features if f['object_id']==fid);r=next(r for r in records if r.is_primary and r.object_id==fid);body=data[r.body:r.end]
        known=known_construction_entities(data,records,features)
        default=outcome(decode_surface_tool,data,records,body,f,known)
        check(archive+' exact old plane-only failure preserved',default==outcome(frozen.decode_surface_tool,data,records,body,f,known)==dict(error_type='ValueError',reason='Only observed planar trim tools supported'))
        check(archive+' actual input and rolled tool remain SketchLine',actual['input_actual_trimTool']['actual_type_branch']==actual['feature_before_node']['trimTool']['actual_type_branch']==tool['entity']['kind']=='SketchLine')
        check(archive+' owned selection and source IDs agree',tool['selection_record_object_id']==settings['tool_selection']['selection_record_object_id']==evidence['tool_selection_record_object_id'] and fid==evidence['feature_object_id'] and settings['tool_selection']['stored_descriptor_count']==settings['target_selection']['stored_descriptor_count']==1)
        byid={r.object_id:r for r in records if r.is_primary};definition=byid[settings['recipe_definition_object_id']];wrapper=byid[settings['recipe_record_object_id']]
        check(archive+' exact opaque recipe payload replay',data[definition.body:definition.end].hex()==settings['stored_recipe_payload_hex'])
        check(archive+' exact typed wrapper replay',data[wrapper.body:wrapper.end]==bytes.fromhex('000001000000')+b'\1'+struct.pack('<Q',definition.object_id)+bytes(2))
        check(archive+' cell assignment remains unknown',settings['trim_cell_status']=='Selected-cell semantics and bounded-face recipe undecoded; original recipe retained' and evidence['native_trim_cell_assignment'] is None)
        selected=[c['api_enumeration_index'] for c in actual['input_cells_after_selection'] if c['isSelected']]
        check(archive+' literal selected API indices preserved',selected==actual['selected_input_cell_indices'] and bool(selected))
        recipe_bytes+=definition.end-definition.body
        captures[directory]=dict(directory=directory,capture_status=truth['terminal_status'],complete_marker_present=True,ground_truth_sha256=digest(folder/'ground_truth.json'),executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],sdk_runtime_sha256=truth['sdk_runtime_sha256'],fusion_version=truth['fusion_version'],entrypoint_provenance=entry,errors=truth['errors'])
        samples.append(dict(archive=archive,archive_sha256=digest(ROOT/archive),expected_decoded=decoded,expected_default_failure=default,actual_requested=actual['requested'],actual_input_tool_type='SketchLine',actual_rolled_tool_type='SketchLine',actual_selected_input_cell_enumeration_indices=selected,native_cell_recipe_assignment=None,exact_recipe_wrapper_payload_hex=data[wrapper.body:wrapper.end].hex(),opaque_recipe_bytes_replayed=definition.end-definition.body,owned_export_and_close_true=True,capture_status=truth['terminal_status']))
        contexts.append((data,records,features,row))
    data,records,features,row=contexts[0];fid=row['feature_object_id'];settings=row['settings'];byid={r.object_id:r for r in records if r.is_primary};r=byid[fid]
    def reject(label,offset,payload):
        changed=bytearray(data);changed[offset:offset+len(payload)]=payload
        answer=decode_surface_trim_lines(bytes(changed),records,features)
        check(label,not answer['decoded'] and len(answer['unresolved'])==1)
        guards.append(dict(guard=label,absolute_mutation_offset=offset,reason=answer['unresolved'][0]['reason']))
    def ref(i):return b'\1'+struct.pack('<Q',i)+bytes(2)
    reject('Reject reserved Trim prefix',r.body,b'\1')
    reject('Reject recipe wrapper framing',byid[settings['recipe_record_object_id']].body+2,b'\2')
    reject('Reject target count2',r.body+40,struct.pack('<I',2))
    reject('Reject owned tool proxy mismatch',byid[settings['tool_selection']['selection_record_object_id']].end-11,ref(fid+1))
    reject('Reject owned target descriptor mismatch',byid[settings['target_selection']['descriptor_object_ids'][0]].end-11,ref(fid+1))
    for label,change in [('Callback source selection mismatch',lambda a:a.update(selection_record_object_id=fid)),('Callback native owner mismatch',lambda a:a['native_source_evidence'].update(feature_object_id=fid+1)),('Callback proof missing',lambda a:a.pop('native_source_evidence')),('Callback unrequested BRepFace kind',lambda a:a['entity'].update(kind='BRepFace'))]:
        def bad(*args):
            a=resolve_surface_trim_line_source(*args);change(a);return a
        with patch('decode_surface_trim_line_sources.resolve_surface_trim_line_source',bad):answer=decode_surface_trim_lines(data,records,features)
        check(label,not answer['decoded'] and len(answer['unresolved'])==1);guards.append(dict(guard=label,reason=answer['unresolved'][0]['reason']))
    feature=next(f for f in features if f['object_id']==fid);body=data[r.body:r.end]
    def resolver(d,rs,i,f,k):return resolve_surface_trim_line_source(d,rs,i,f['object_id'],features)
    for value in ((),('SketchLine','SketchLine'),('Unknown',),['SketchLine']):
        try:decode_surface_tool(data,records,body,feature,{},trim_tool_resolver=resolver,allowed_trim_tool_kinds=value)
        except ValueError as error:reason=str(error)
        else:raise AssertionError('invalid explicit kinds accepted')
        check('Reject explicit tool kinds '+repr(value),reason=='Unsupported explicit Trim tool kinds');guards.append(dict(guard='Reject explicit tool kinds '+repr(value),reason=reason))
    try:decode_surface_tool(data,records,body,feature,{},trim_tool_resolver=resolver)
    except ValueError as error:reason=str(error)
    else:raise AssertionError('default callback admitted Line')
    check('Default callback still excludes SketchLine',reason=='Trim tool resolver source identity/owner/type disagrees');guards.append(dict(guard='Default callback still excludes SketchLine',reason=reason))
    for archive in OLD_FILES:
        d,rs,fs,_,_=context(archive,zstd);known=known_construction_entities(d,rs,fs);rows=[]
        for f in fs:
            if f['kind'] not in SURFACE_KINDS:continue
            rec=next(r for r in rs if r.start==f['record_offset']);args=(d,rs,d[rec.body:rec.end],f,known)
            now=outcome(decode_surface_tool,*args);check(archive+' default '+str(f['object_id']),now==outcome(frozen.decode_surface_tool,*args))
            rows.append(dict(feature_object_id=f['object_id'],kind=f['kind'],full_pinned_default_outcome_exact=True,outcome_sha256=hashlib.sha256(json.dumps(now,sort_keys=True).encode()).hexdigest()))
        empty=decode_surface_trim_lines(d,rs,fs);check(archive+' no Line false candidate',not empty['decoded'] and not empty['unresolved'])
        legacy.append(dict(archive=archive,comparisons=rows,new_wrapper_no_candidate=True))
    historical={s['archive']:s['expected_decoded'] for s in json.loads((ROOT/'surface-trim-tool-decoding.json').read_text())['samples']}
    for archive in FACE_BODY:
        d,rs,fs,_,_=context(archive,zstd);current=decode_surface_trim_tools(d,rs,fs)
        with patch('decode_surface_trim_tools.decode_surface_tool',frozen.decode_surface_tool):old=decode_surface_trim_tools(d,rs,fs)
        check(archive+' whole FaceBody summary exact',current==old and len(current['decoded'])==1 and not current['unresolved'])
        if archive in historical:check(archive+' historical golden exact',current==historical[archive])
        empty=decode_surface_trim_lines(d,rs,fs);check(archive+' no Line candidate',not empty['decoded'] and not empty['unresolved'])
        facebody.append(dict(archive=archive,full_pinned_face_body_summary_exact=True,full_prior_report_exact=archive in historical,line_wrapper_no_candidate=True))
    return dict(scope='Three healthy completed actual SketchLine Trim cases. Common recipe/target parser retained; line source and direction do not assign selected cells or persistent topology.',interface='decode_surface_trim_lines(data,records,features)->decoded/unresolved/scope; rows feature_object_id/kind/name/settings',integration=dict(stream='surface_trim_lines',source_stream='surface_trim_line_sources',feature_source_field='surface_trim_line_source',settings_field='settings',cleared_old_reason='Only observed planar trim tools supported',decode_level='Observed SurfaceTrim sketch-Line tool and typed sketch source; selected-cell recipe, persistent topology and regeneration unresolved'),captures=list(captures.values()),samples=samples,malformed_guards=guards,legacy_controls=legacy,face_body_controls=facebody,default_preservation=dict(pinned_revision=BASELINE,pinned_surface_tools_sha256=hashlib.sha256(source.encode()).hexdigest(),full_legacy_surface_file_outcomes_exact=len(legacy),full_face_body_summaries_exact=len(facebody),scope='Direct common decoder and bounded wrappers only; no main-reader execution'),checks=checks,source_sha256={p:digest(ROOT/p) for p in ('decode_surface_tools.py','decode_surface_trim_lines.py','decode_surface_trim_line_sources.py','validate_surface_trim_lines.py')},validation=dict(actual_exports=3,healthy_features=3,owned_closes_true=3,terminal_complete_batches=len(captures),opaque_recipe_bytes_replayed=recipe_bytes,check_count=len(checks),malformed_guards=len(guards),exact_legacy_surface_files=len(legacy),exact_face_body_controls=len(facebody),no_live_calls=True,no_main_calls=True),limitations=['Only singleton canonical SketchLine source tools are qualified. Natural line endpoint orientation/offset remain separate from Trim cell/side semantics.','Selected API cell enumeration indices and the exact raw native recipe are retained without pairing. Target persistent topology and lifecycle remain unresolved.','API endpoints corroborate identity established by typed sketch/tag references; coordinates do not choose identity. Derived interior samples are not independently measured API evaluator samples.','Successful lifecycle-repaired captures do not establish universal process stability or a universal crash cause. Original interrupted Face/Body captures remain historical PartialNoTerminalMarker evidence.'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--zstd');p.add_argument('--output',default='surface-trim-line-decoding.json');a=p.parse_args()
    z=a.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['validation'],sort_keys=True))
