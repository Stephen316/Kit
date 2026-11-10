"""Focused plural Thread controls and exact pinned singleton compatibility."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import types
from unittest.mock import patch

from decode_extrude import optional_reference
from decode_parameters import read_string
from decode_thread_multi_faces import THREAD,decode_thread_multi_faces
from decode_threads import decode_thread
from validate_mesh_repair import context

ROOT=Path(__file__).resolve().parent
DIRECTORY='threadmultifaces-e4bc4a120fbf'
BASELINE='46192df'
OLD_FILES=[
 'threadmodes-d51d2ae60564/'+name+'.f3d' for name in
 ('cosmetic_full','modeled_full','partial_high','partial_low','left_handed','internal')
]+['threadmodes-9574579d310b/left_handed.f3d']
OLD_FILES += ['tappedholes-409e96788503/'+name+'.f3d' for name in
              ('cosmetic_full','cosmetic_partial','modeled_full')]


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(zstd):
    folder=ROOT/DIRECTORY;truth=json.loads((folder/'ground_truth.json').read_text())
    assert truth['terminal_status']=='Complete' and not truth['errors'] and len(truth['samples'])==3
    assert (folder/'complete.txt').is_file()
    progress=json.loads((folder/'progress.json').read_text())
    assert progress['phase']=='batch_terminal' and progress['exported_sample_count']==3 and progress['error_count']==0
    assert digest(folder/'executed-generator-source.txt')==truth['executed_generator_sha256']
    assert digest(folder/'executed-sdk-surface.txt')==truth['executed_sdk_surface_sha256']
    source=subprocess.check_output(['git','show',BASELINE+':decode_threads.py'],cwd=ROOT).decode()
    old=types.ModuleType('frozen_thread_default');exec(compile(source,'frozen_decode_threads.py','exec'),old.__dict__)
    report=dict(scope='Three actual two-face cosmetic Threads, full external/partial external/full internal, using unchanged common controls and separately bounded native source routes. No modeled or attached-hole plural support claimed.',
        interface='decode_thread_multi_faces(data,records,features)->decoded/unresolved/scope; decoded rows feature_object_id/kind/name/settings',
        integration=dict(stream='thread_multi_faces',settings_field='settings',
            decode_level='Observed two-face cosmetic Thread controls and typed historical cylindrical sources; persistent face identity and regeneration unresolved',
            cleared_old_reason='Unsupported thread length/offset/selection count',
            scope='Only same-feature old singleton rejection may be removed after successful opt-in decode; existing unresolved_inputs and unrelated diagnostics retained.'),
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(folder/'ground_truth.json'),
            executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],
            sdk_runtime_sha256=truth['sdk_runtime_sha256'],fusion_version=truth['fusion_version']),
        native_schema=dict(Thread_class_guid=THREAD,selection_list='uint32 count2 followed by two typed 11-byte proxy references; each proxy owns exactly one typed cylindrical-face descriptor',
            common_controls='All flags, thread strings, numeric dimensions, bindings and mode fields reused from decode_threads.decode_thread',
            parameter_controls='Both typed native parameter records, attached parameters and three feature-owner binding references agree; finite positive length/nonnegative offset checked independently in opt-in wrapper',
            identity_scope='Historical native source BODY order differs from current collection order. API selected handles are not identified with native recipes or ASM faces.'),
        samples=[],malformed_guards=[],legacy_controls=[],
        limitations=['Only captured right-handed cosmetic straight ISO metric two-source modes are qualified. Other plural, modeled, attached-hole and partial-internal variants remain unsupported.',
            'Actual input handles equal selected handles before add, but rolled feature face handles do not equal them in all three captures. No API/native per-face assignment or ordinal source/result pairing is claimed.',
            'Timeline-end inputCylindricalFaces getter fails because the feature was not rolled back; successful rollback getters are distinct evidence.',
            'Historical source routes and reciprocal stored current BODY membership do not prove persistent selected-face identity or general lifecycle.',
            'Full-length stored length/offset remain inactive; no values are invented from uncalled partial-property getters.',
            'Geometry/ASM BODY corroboration is covered by the independent thread-body-route report; controls do not regenerate threads.'])
    contexts={};numeric_checks=0
    for actual in truth['samples']:
        filename=DIRECTORY+'/'+actual['file'];d,rs,fs,member,members=context(filename,zstd)
        assert actual['close_owned_document_returned'] is True and not actual['getter_errors'] and not actual['setter_errors']
        assert actual['export']['returned_success'] is True and actual['export']['sha256']==digest(ROOT/filename)
        assert actual['export']['size_bytes']==(ROOT/filename).stat().st_size
        assert actual['timeline_count']==actual['timeline_marker_position'] and actual['roll_before_feature_returned'] is True
        before=copy.deepcopy(fs);answer=decode_thread_multi_faces(d,rs,fs)
        assert fs==before and len(answer['decoded'])==1 and not answer['unresolved']
        row,=answer['decoded'];s=row['settings'];fid=row['feature_object_id']
        feature,=[f for f in fs if f['object_id']==fid];record,=[r for r in rs if r.is_primary and r.object_id==fid]
        try:decode_thread(d,rs,d[record.body:record.end],feature)
        except ValueError as error:assert str(error)=='Unsupported thread length/offset/selection count'
        else:raise AssertionError('Default singleton guard unexpectedly admitted plural Thread')
        api=actual['feature_before_node'];info=api['threadInfo']
        assert api['healthState']==0 and api['errorOrWarningMessage']=='' and not api['control_getter_errors']
        assert api['isModeled']==s['is_modeled']==False and api['isFullLength']==s['is_full_length']
        strings={'thread_type':'threadType','thread_size':'threadSize','thread_designation':'threadDesignation','thread_class':'threadClass'}
        for native,key in strings.items():assert s[native]==info[key]
        for native,key in {'thread_angle_degrees':'threadAngle','pitch_cm':'threadPitch','major_diameter_cm':'majorDiameter','minor_diameter_cm':'minorDiameter','pitch_diameter_cm':'pitchDiameter'}.items():
            assert math.isclose(s[native],info[key],rel_tol=1e-14,abs_tol=1e-14);numeric_checks+=1
        assert s['is_internal']==info['isInternal'] and s['is_right_handed']==info['isRightHanded']==True
        assert s['attached_hole_object_id'] is None and s['stored_modeled_table_pairs']==[]
        assert len(s['selection_record_object_ids'])==len(s['descriptor_object_ids'])==2
        assert 'selection_record_object_id' not in s
        assert actual['input_faces_equal_selected_handles'] is True and actual['feature_input_faces_equal_selected_handles'] is False
        assert len(api['inputCylindricalFaces'])==len(actual['input_before_add']['inputCylindricalFaces'])==2
        errors=actual['feature_at_timeline_end']['control_getter_errors']
        assert len(errors)==1 and errors[0]['getter']=='inputCylindricalFaces' and "Didn't roll editing feature back" in errors[0]['error']
        evidence=s['selection_evidence'];cursor=evidence['selection_start_offset'];end=evidence['selection_end_offset']
        assert d[record.body+cursor:record.body+end].hex()==evidence['stored_selection_list_hex']
        assert evidence['historical_native_body_object_ids']==list(reversed(evidence['native_current_body_object_ids']))
        assert actual['component_bodies_after_thread']['count']==2
        assert len(s['control_parameter_evidence'])==2
        for control in s['control_parameter_evidence']:
            binding,=[r for r in rs if r.is_primary and r.object_id==control['binding_object_id']]
            assert d[binding.body:binding.end].hex()==control['stored_binding_payload_hex']
            assert control['is_active']==(not s['is_full_length'])
        if s['is_full_length']:
            assert s['active_length_cm'] is s['active_offset_cm'] is s['active_location'] is None
            assert all(v=='NotCalled_FullLength' for v in api['inactive_partial_controls'].values())
        else:
            assert s['active_length_cm']==api['threadLength']['value'] and s['active_offset_cm']==api['threadOffset']['value']
            assert s['active_location']=='HighEnd' and s['stored_location_code']==1 and api['threadLocation']==0
            assert api['threadLength']['role']=='ThreadLength' and api['threadOffset']['role']=='ThreadOffset'
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=answer,
            actual_initial_input_handle_equality=True,actual_rolled_feature_handle_equality=False,
            actual_timeline_end_face_getter_errors=errors,actual_API_current_BRep_count=2,
            exact_selection_and_binding_byte_replays=True,owned_document_closed_true=True))
        contexts[actual['case']]=(d,rs,fs,row)
    d,rs,fs,row=contexts['external_two_partial'];s=row['settings'];e=s['selection_evidence'];fid=row['feature_object_id']
    by_id={r.object_id:r for r in rs if r.is_primary};record=by_id[fid]
    def ref(i):return b'\1'+struct.pack('<Q',i)+bytes(2)
    def reject(label,offset=None,payload=b'',changed_features=None):
        damaged=bytearray(d)
        if offset is not None:damaged[offset:offset+len(payload)]=payload
        answer=decode_thread_multi_faces(bytes(damaged),rs,fs if changed_features is None else changed_features)
        assert not answer['decoded'] and len(answer['unresolved'])==1,(label,answer)
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offset=offset,rejected=True,reason=answer['unresolved'][0]['reason']))
    cursor=e['selection_start_offset']
    reject('Unsupported selection count3',record.body+cursor,struct.pack('<I',3))
    reject('Duplicate source proxy IDs',record.body+cursor+15,ref(s['selection_record_object_ids'][0]))
    proxy=by_id[s['selection_record_object_ids'][0]];descriptor=by_id[s['descriptor_object_ids'][0]]
    reject('Proxy feature owner differs',proxy.end-11,ref(fid+1))
    reject('Descriptor feature owner differs',descriptor.end-11,ref(fid+1))
    reject('Descriptor reference has wrong typed class',proxy.body+6,ref(fid))
    binding=by_id[s['parameter_bindings']['ThreadLength']]
    reject('Binding cached length differs from typed parameter',binding.body+21,struct.pack('<d',.8))
    changed=copy.deepcopy(fs);f=next(f for f in changed if f['object_id']==fid)
    next(p for p in f['parameters'] if p['role']=='ThreadLength')['raw_float64']=float('nan')
    reject('Nonfinite attached active length',changed_features=changed)
    changed=copy.deepcopy(fs);f=next(f for f in changed if f['object_id']==fid)
    next(p for p in f['parameters'] if p['role']=='ThreadOffset')['raw_float64']=float('inf')
    reject('Nonfinite attached active offset',changed_features=changed)
    native=d[record.body:record.end];string_cursor=15+16*struct.unpack_from('<I',native,11)[0]
    for _ in range(5):_,string_cursor=read_string(native,string_cursor)
    _,binding_cursor=optional_reference(native,string_cursor+38)
    reject('Uncaptured left-handed plural family',record.body+binding_cursor+22,b'\0')
    from decode_thread_body_routes import resolve_thread_multi_faces
    def bad_extent(*args):
        result=resolve_thread_multi_faces(*args);result['selection_end_offset']+=1;return result
    with patch('decode_thread_body_routes.resolve_thread_multi_faces',bad_extent):reject('Resolver extent must equal exact counted selection bytes')
    for filename in OLD_FILES:
        data,records,features,_,_=context(filename,zstd);rows=[]
        for f in features:
            if f.get('class_guid')!=THREAD:continue
            r,=[r for r in records if r.is_primary and r.object_id==f['object_id']]
            settings=decode_thread(data,records,data[r.body:r.end],f)
            assert settings==old.decode_thread(data,records,data[r.body:r.end],f)
            rows.append(dict(feature_object_id=f['object_id'],settings=settings))
        assert rows
        empty=decode_thread_multi_faces(data,records,features)
        assert not empty['decoded'] and not empty['unresolved']
        report['legacy_controls'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_default_settings=rows,
            full_pinned_default_dictionary_exact=True,new_wrapper_no_candidate=True,
            attached_hole_ThreadDepth=filename.startswith('tappedholes-')))
    report['default_preservation']=dict(pinned_revision=BASELINE,pinned_decode_threads_sha256=hashlib.sha256(source.encode()).hexdigest(),
        scope='Direct default decoder comparison only; historical thread-decoding.json lacks later attached-hole keys and is not misrepresented as a current full-dictionary golden.',standalone_files=7,attached_hole_files=3)
    report['source_sha256']={name:digest(ROOT/name) for name in ('decode_threads.py','decode_thread_multi_faces.py','decode_thread_body_routes.py','validate_thread_multi_faces.py')}
    report['validation']=dict(actual_exports=3,decoded_controls=3,owned_face_proxies=6,typed_descriptors=6,owned_numeric_bindings=6,
        actual_API_dimension_comparisons=numeric_checks,malformed_guards=len(report['malformed_guards']),
        exact_pinned_default_files=len(report['legacy_controls']),attached_hole_ThreadDepth_files=3,no_main_pipeline_calls=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default='thread-multi-face-decoding.json');args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    answer=validate(zstd);Path(args.output).write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer['validation'],sort_keys=True))
