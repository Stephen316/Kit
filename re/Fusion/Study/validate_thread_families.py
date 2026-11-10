"""Actual straight Thread family controls, exact XML rows and preserved defaults."""
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
import xml.etree.ElementTree as ET

from decode_thread_families import FAMILIES,THREAD,decode_thread_families
from decode_thread_multi_faces import decode_thread_multi_faces
from decode_threads import decode_thread
from decode_parameters import read_string
from validate_mesh_repair import context

ROOT=Path(__file__).resolve().parent
DIRECTORY='threadfamilies-459264fae49b'
BASELINE='72ed331'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def xml_match(folder,source,settings):
    """Exact literal size/designation/class/gender lookup, never numerical proximity."""
    path=folder/source['snapshot_file'];assert digest(path)==source['sha256']
    tree=ET.fromstring(path.read_bytes());assert tree.findtext('Name')==settings['thread_type']
    gender='internal' if settings['is_internal'] else 'external';matches=[]
    for size_index,size in enumerate(tree.findall('ThreadSize')):
        if size.findtext('Size')!=settings['thread_size']:continue
        for designation_index,designation in enumerate(size.findall('Designation')):
            if settings['thread_designation'] not in (designation.findtext('ThreadDesignation'),designation.findtext('CTD')):continue
            for thread_index,thread in enumerate(designation.findall('Thread')):
                if thread.findtext('Gender')==gender and thread.findtext('Class')==settings['thread_class']:
                    matches.append((size_index,designation_index,thread_index,size,designation,thread))
    assert len(matches)==1
    si,di,ti,size,designation,thread=matches[0]
    unit=tree.findtext('Unit');scale={'in':2.54,'mm':.1}[unit]
    values={k:float(thread.findtext(field))*scale for k,field in (
        ('major_diameter_cm','MajorDia'),('minor_diameter_cm','MinorDia'),('pitch_diameter_cm','PitchDia'))}
    pitch=designation.findtext('Pitch');tpi=designation.findtext('TPI')
    assert (pitch is None)!=(tpi is None)
    values['pitch_cm']=float(pitch)*scale if pitch is not None else 2.54/float(tpi)
    values['thread_angle_degrees']=float(tree.findtext('Angle'))
    for key,value in values.items():assert math.isclose(value,settings[key],rel_tol=1e-14,abs_tol=1e-14)
    return dict(snapshot_file=source['snapshot_file'],snapshot_sha256=source['sha256'],
        element_path=f'ThreadType/ThreadSize[{si}]/Designation[{di}]/Thread[{ti}]',
        size_literal=size.findtext('Size'),diameter_unit_literal=unit,angle_literal=tree.findtext('Angle'),
        designation_fields={child.tag:child.text for child in designation if child.tag!='Thread'},
        selected_thread_fields={child.tag:child.text for child in thread},
        derived_values=values,pitch_conversion='Declared Pitch scaled by XML length unit' if pitch is not None else '2.54 cm per inch / literal threads-per-inch; independent of XML diameter unit',
        selection_basis='Exact native/API family, size, designation or CTD, class and gender; no geometry/nearest-value matching')


def validate(zstd):
    folder=ROOT/DIRECTORY;truth=json.loads((folder/'ground_truth.json').read_text())
    assert truth['terminal_status']=='Complete' and not truth['errors'] and len(truth['samples'])==3
    assert (folder/'complete.txt').is_file()
    progress=json.loads((folder/'progress.json').read_text())
    assert progress['phase']=='batch_terminal' and progress['exported_sample_count']==3 and progress['error_count']==0
    assert digest(folder/'executed-generator-source.txt')==truth['executed_generator_sha256']
    assert digest(folder/'executed-sdk-surface.txt')==truth['executed_sdk_surface_sha256']
    source=subprocess.check_output(['git','show',BASELINE+':decode_threads.py'],cwd=ROOT).decode()
    frozen=types.ModuleType('frozen_thread_family_default');exec(compile(source,'frozen_decode_threads.py','exec'),frozen.__dict__)
    report=dict(scope='Three actual full-length right-handed cosmetic singleton Thread families; numeric controls, owned sources and exact installed XML table rows only. No standards implementation, thread regeneration or persistent selected-face identity.',
        interface='decode_thread_families(data,records,features)->decoded/unresolved/scope; rows feature_object_id/kind/name/settings',
        integration=dict(stream='thread_families',settings_field='settings',
            cleared_old_reason='Only observed matching straight metric thread definitions supported',
            scope='Replace only same-feature prior family rejection after success. Default ISO-only reader and existing standalone/attached/plural outputs remain exact; late ASM BODY proof is separate.'),
        shared_opt_in=dict(allowed_families_default=['ISO Metric profile'],family_wrapper_opt_in=list(FAMILIES),
            selection_callback='Existing bounded selection_resolver now accepts count1 or2 only when explicitly provided; supplied family resolver itself requires singleton count1, old plural resolver itself still requires count2.'),
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(folder/'ground_truth.json'),
            executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],
            sdk_runtime_sha256=truth['sdk_runtime_sha256'],fusion_version=truth['fusion_version']),
        samples=[],malformed_guards=[],legacy_controls=[],plural_controls=[],
        limitations=['Qualified new family modes are ANSI Unified external, ISO Metric Trapezoidal external and BSP Pipe internal, full-length right-handed cosmetic singleton only; other genders/modes/families remain unsupported.',
            'Installed XML snapshots supply exact row corroboration, not a runtime dependency or a promise that all standards/table variants are supported.',
            'Native dimensions remain cm and angle degrees. XML in/mm is applied only to dimensional table fields; TPI always divides 2.54 cm/inch, including BSP XML with mm diameters.',
            'Actual rolled feature face handles do not equal the original selected handles in these captures. Native source routes do not claim API handle/selected ASM face identity.',
            'Actual straight isTaperedFalse properties are corroboration of captured definitions; no inferred universal taper flag or helical geometry is introduced.',
            'Full-length native length/offset bindings remain stored and inactive. No values are inferred from uncalled partial-control getters.',
            'Historical source/current stored membership, cached geometry and lifecycle remain separate. General thread modeling, regeneration and native writing remain unresolved.'])
    contexts={};comparisons=0
    for actual in truth['samples']:
        filename=DIRECTORY+'/'+actual['file'];data,records,features,member,members=context(filename,zstd)
        assert actual['close_owned_document_returned'] is True and not actual['getter_errors'] and not actual['setter_errors']
        assert actual['export']['returned_success'] is True and actual['export']['sha256']==digest(ROOT/filename)
        assert actual['export']['size_bytes']==(ROOT/filename).stat().st_size
        assert actual['roll_before_feature_returned'] is True and actual['timeline_count']==actual['timeline_marker_position']
        before=copy.deepcopy(features);decoded=decode_thread_families(data,records,features)
        assert before==features and len(decoded['decoded'])==1 and not decoded['unresolved']
        row,=decoded['decoded'];settings=row['settings'];fid=row['feature_object_id']
        feature,=[f for f in features if f['object_id']==fid];record,=[r for r in records if r.is_primary and r.object_id==fid]
        body=data[record.body:record.end]
        for reader in (decode_thread,frozen.decode_thread):
            try:reader(data,records,body,feature)
            except ValueError as error:assert str(error)==report['integration']['cleared_old_reason']
            else:raise AssertionError('Default ISO-only decoder admitted nonmetric family')
        for phase in ('input_before_add','feature_before_node'):
            api=actual[phase];info=api['threadInfo']
            assert not api['control_getter_errors'] and api['isModeled']==settings['is_modeled']==False
            assert api['isFullLength']==settings['is_full_length']==True and info['isTapered'] is False
            for native,key in {'thread_type':'threadType','thread_size':'threadSize','thread_designation':'threadDesignation','thread_class':'threadClass','is_internal':'isInternal','is_right_handed':'isRightHanded'}.items():assert settings[native]==info[key]
            for native,key in {'thread_angle_degrees':'threadAngle','pitch_cm':'threadPitch','major_diameter_cm':'majorDiameter','minor_diameter_cm':'minorDiameter','pitch_diameter_cm':'pitchDiameter'}.items():
                assert math.isclose(settings[native],info[key],rel_tol=1e-14,abs_tol=1e-14);comparisons+=1
        assert actual['feature_before_node']['healthState']==0 and actual['feature_before_node']['errorOrWarningMessage']==''
        assert actual['input_faces_equal_selected_handles'] is True and actual['feature_input_faces_equal_selected_handles'] is False
        assert len(actual['feature_before_node']['inputCylindricalFaces'])==1
        assert settings['active_length_cm'] is settings['active_offset_cm'] is settings['active_location'] is None
        assert all(value=='NotCalled_FullLength' for value in actual['feature_before_node']['inactive_partial_controls'].values())
        assert settings['attached_hole_object_id'] is None and not settings['stored_modeled_table_pairs']
        evidence=settings['selection_evidence'];assert len(settings['selection_record_object_ids'])==len(settings['descriptor_object_ids'])==1
        assert 'selection_record_object_id' not in settings
        a,b=evidence['selection_start_offset'],evidence['selection_end_offset']
        assert body[a:b].hex()==evidence['stored_selection_list_hex']
        xml=xml_match(folder,truth['installed_XML_sources'][settings['thread_type']],settings)
        actual_xml,=actual['recommended_XML_record']['matching_records']
        assert actual['recommended_XML_record']['match_count']==1
        assert actual_xml['element_path']==xml['element_path'] and actual_xml['selected_thread_fields']==xml['selected_thread_fields']
        assert actual_xml['designation_fields']==xml['designation_fields']
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=decoded,
            exact_XML_row=xml,actual_input_handle_equality=True,actual_rolled_feature_handle_equality=False,
            stored_selection_list_exact_byte_replay=True,actual_API_is_tapered=False,owned_document_closed_true=True))
        contexts[actual['case']]=(data,records,features,row)
    data,records,features,row=contexts['ansi_unified_external'];settings=row['settings'];evidence=settings['selection_evidence']
    fid=row['feature_object_id'];by_id={r.object_id:r for r in records if r.is_primary};record=by_id[fid];body=data[record.body:record.end]
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    def reject(label,offset=None,payload=b'',changed_features=None):
        damaged=bytearray(data)
        if offset is not None:damaged[offset:offset+len(payload)]=payload
        answer=decode_thread_families(bytes(damaged),records,features if changed_features is None else changed_features)
        assert not answer['decoded'] and len(answer['unresolved'])==1,(label,answer)
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offset=offset,rejected=True,reason=answer['unresolved'][0]['reason']))
    cursor=15;string_spans=[]
    for _ in range(5):start=cursor;_,cursor=read_string(body,cursor);string_spans.append((start,cursor))
    reject('Repeated designation disagrees',record.body+string_spans[2][0]+4,'Z'.encode('utf-16le'))
    reject('Invalid nonfinite angle',record.body+2,struct.pack('<d',float('nan')))
    reject('Uncaptured family gender',record.body+10,b'\0')
    reject('Uncaptured modeled flag/table combination',record.body+cursor+21,b'\1')
    reject('Uncaptured two-proxy selection count',record.body+evidence['selection_start_offset'],struct.pack('<I',2))
    proxy=by_id[settings['selection_record_object_ids'][0]];descriptor=by_id[settings['descriptor_object_ids'][0]]
    reject('Face proxy owner differs',proxy.end-11,ref(fid+1))
    reject('Face descriptor owner differs',descriptor.end-11,ref(fid+1))
    binding=by_id[settings['parameter_bindings']['ThreadLength']]
    reject('Stored binding/parameter value copies disagree',binding.body+21,struct.pack('<d',1.1))
    changed=copy.deepcopy(features);feature=next(f for f in changed if f['object_id']==fid)
    next(p for p in feature['parameters'] if p['role']=='ThreadOffset')['raw_float64']=float('inf')
    reject('Nonfinite stored inactive offset',changed_features=changed)
    from decode_thread_family_body_routes import resolve_thread_family_faces
    def bad_extent(*args):
        answer=resolve_thread_family_faces(*args);answer['selection_end_offset']+=1;return answer
    with patch('decode_thread_families.resolve_thread_family_faces',bad_extent):reject('Callback counted extent mismatch')
    previous=json.loads((ROOT/'thread-multi-face-decoding.json').read_text())
    for control in previous['legacy_controls']:
        filename=control['archive'];d,rs,fs,_,_=context(filename,zstd);rows=[]
        for f in fs:
            if f.get('class_guid')!=THREAD:continue
            r,=[r for r in rs if r.is_primary and r.object_id==f['object_id']]
            value=decode_thread(d,rs,d[r.body:r.end],f)
            assert value==frozen.decode_thread(d,rs,d[r.body:r.end],f)
            rows.append(dict(feature_object_id=f['object_id'],settings=value))
        assert rows==control['expected_default_settings']
        assert decode_thread_families(d,rs,fs)['decoded']==decode_thread_families(d,rs,fs)['unresolved']==[]
        report['legacy_controls'].append(dict(archive=filename,full_pinned_default_settings_exact=True,prior_report_settings_exact=True,
            attached_hole_ThreadDepth=control['attached_hole_ThreadDepth']))
    for sample in previous['samples']:
        filename=sample['archive'];d,rs,fs,_,_=context(filename,zstd)
        assert decode_thread_multi_faces(d,rs,fs)==sample['expected_decoded']
        empty=decode_thread_families(d,rs,fs);assert not empty['decoded'] and not empty['unresolved']
        report['plural_controls'].append(dict(archive=filename,full_prior_plural_summary_exact=True))
    report['default_preservation']=dict(pinned_revision=BASELINE,pinned_decode_threads_sha256=hashlib.sha256(source.encode()).hexdigest(),
        standalone_files=7,attached_hole_ThreadDepth_files=3,plural_files=3,scope='Direct helpers only; historical pre-ThreadDepth dictionaries are not misrepresented as current whole-output goldens')
    report['source_sha256']={name:digest(ROOT/name) for name in ('decode_threads.py','decode_thread_families.py','decode_thread_multi_faces.py','decode_thread_body_routes.py','decode_thread_family_body_routes.py','validate_thread_families.py')}
    report['validation']=dict(actual_exports=3,decoded_families=3,exact_XML_rows=3,XML_dimension_checks=15,actual_API_dimension_checks=comparisons,
        typed_singleton_source_routes=3,malformed_guards=len(report['malformed_guards']),exact_legacy_default_files=10,exact_plural_summary_files=3,no_main_calls=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default='thread-family-decoding.json');args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd);Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['validation'],sort_keys=True))
