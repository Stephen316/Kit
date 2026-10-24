"""Focused actual Feature/Occurrence PathPattern evidence and strict regressions."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_path_pattern_inputs import decode_path_pattern_inputs, FEATURE, OCCURRENCE_PATTERN
from decode_path_patterns import decode_path_pattern
from decode_path_pattern_composites import decode_path_pattern_composites
from decode_sketch import same
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
FOLDER='pathpatterninputs-7edfa558db34'


def load(path,zstd,stream=None):
    members=read_members(path,zstd)
    if stream is None:
        stream=next(s for s in decode_basics(path,zstd)['streams'] if 'assembly_decoding' in s)
    data=members[stream['member']]
    records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')])
    return data,records,stream


def validate(root,zstd):
    folder=root/FOLDER;truth=json.loads((folder/'ground_truth.json').read_text())
    assert (folder/'complete.txt').is_file() and truth['terminal_status']=='complete'
    assert not truth['errors'] and len(truth['samples'])==3
    report=dict(interface='decode_path_pattern_inputs(data,records,features,assembly,*,body_selections=None) -> decoded/unresolved/scope; decoded rows feature_object_id/kind/name/settings',
        common_parser='parse_path_pattern_controls extracted from strict legacy Body wrapper; explicit compute/entity allowlist, empty-pair opt-in and typed element/auxiliary callbacks only',
        captures=FOLDER,api_version=truth['fusion_version'],samples=[],old_body_controls=[],old_composite_controls=[],guards=[],
        validation_command='python3 validate_path_pattern_inputs.py --zstd-library <libzstd path>',
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'GeneratePathPatternInputContrasts.py','decode_path_patterns.py','decode_path_pattern_inputs.py',
            'validate_path_pattern_inputs.py',FOLDER+'/executed-generator-source.txt')})
    saved={}
    for sample in truth['samples']:
        path=folder/sample['file'];data,records,stream=load(path,zstd)
        features,assembly=stream['features'],stream['assembly_decoding']
        decoded=decode_path_pattern_inputs(data,records,features,assembly,body_selections=stream['body_selections'])
        assert len(decoded['decoded'])==1 and not decoded['unresolved'],decoded
        row=decoded['decoded'][0];settings=row['settings'];api=sample['settings']
        selected=settings['path'];sketch=next(f for f in features if f.get('sketch_object_id')==selected['sketch_object_id'])
        curve=next(c for c in sketch['geometry'] if c['object_id']==selected['curve_object_id'])
        actual_path=sample['actual_path']['entities'][0]
        checks=dict(feature_name_matches_actual=row['name']==sample['feature_identity']['name'],
            actual_common_controls_match=all(settings[k]==api[k] for k in ('quantity','distance_cm','start_fraction','is_flipped','is_symmetric','orientation_along_path','suppressed_element_ids')),
            actual_distance_type_matches={0:'Extent',1:'Spacing'}[api['distance_type']]==settings['distance_type'],
            actual_entity_type_matches=settings['pattern_entity_type_api_value']==api['pattern_entity_type'],
            stored_compute_word_matches_actual_getter=settings['stored_compute_option_code']==api['pattern_compute_option'],
            source_sketch_name_matches=sketch.get('name')==actual_path['source_sketch_name'],
            source_line_points_match=all(same(curve[key],actual_path[actual]) for key,actual in (('component_start_cm','source_start_cm'),('component_end_cm','source_end_cm'))),
            source_curve_is_typed_sketch_line=curve['kind']=='Line' and actual_path['source_entity_type']=='adsk::fusion::SketchLine',
            actual_export_healthy_and_closed=sample['health_state']==0 and sample['warning']=='' and sample['close_owned_document_returned'] is True,
            only_actual_nurbs_endpoint_getter_errors_retained=len(sample['getter_errors'])==4 and all("'NurbsCurve3D' object has no attribute" in e['error'] for e in sample['getter_errors']),
            actual_export_hash_matches=hashlib.sha256(path.read_bytes()).hexdigest()==sample['export']['sha256'],
            native_elements_cover_actual_count=len(settings['element_record_object_ids'])==len(sample['pattern_elements'])==3,
            actual_input_singleton_matches=settings['input_entity_count']==len(sample['actual_inputs'])==1,
            path_opposition_stays_unresolved='unresolved' in settings['path_traversal_status'])
        if settings['pattern_entity_type']=='Features':
            source=settings['input_descriptors'][0]
            checks.update(actual_input_feature_name_matches=source['source_feature_name']==sample['actual_inputs'][0]['name'],
                actual_input_class_matches=sample['actual_inputs'][0]['entity_type']=='adsk::fusion::ExtrudeFeature',
                active_compute_option_matches=settings['pattern_compute_option']=={0:'Optimized',1:'Identical'}[api['pattern_compute_option']],
                native_result_anchors_plus_seed_match_api_body_count=settings['generated_result_reference_count']+1==len(sample['feature_bodies']),
                actual_result_features_null_retained=sample['result_features']['status']=='returned_null')
        else:
            actual_elements=sample['pattern_elements']
            native_ids=[settings['source_native_occurrence_object_id'],*settings['created_native_occurrence_object_ids']]
            native={o['object_id']:o for o in assembly['native_occurrences']}
            actual_occurrences=[e['occurrences'][0] for e in actual_elements]
            checks.update(actual_input_component_matches=settings['source_component_name']==sample['actual_inputs'][0]['component_name'],
                source_stored_matrix_matches_actual=same(settings['stored_source_local_matrix'],sample['actual_inputs'][0]['transform']),
                created_stored_matrices_match_actual=all(same(a,b['transform']) for a,b in zip(settings['stored_created_local_matrices'],actual_occurrences[1:])),
                algebraic_relative_matrices_match_api_elements=all(same(a,b['transform']) for a,b in zip(settings['relative_instance_matrix_caches'],actual_elements)),
                actual_instance_counts_match=len(native_ids)==sample['collections_after']['root_occurrence_count'],
                native_instance_numbers_match_api_names=all(a['name']==settings['source_component_name']+':'+str(native[i]['instance_number']) for i,a in zip(native_ids,actual_occurrences)),
                inactive_compute_semantics_unclaimed=settings['pattern_compute_option'] is None,
                actual_result_features_null_retained=sample['result_features']['status']=='returned_null',
                actual_source_before_after_matrix_copy_matches=same(sample['collections_before']['all_occurrences'][0]['transform'],settings['stored_source_local_matrix']))
        assert all(checks.values()),(sample['file'],checks)
        report['samples'].append(dict(archive=str(path.relative_to(root)),checks=checks,expected_decoded=decoded,
            actual_api_settings=api,actual_inputs=sample['actual_inputs'],actual_path=sample['actual_path'],
            actual_pattern_elements=sample['pattern_elements'],actual_result_features=sample['result_features'],
            retained_getter_errors=sample['getter_errors']))
        saved[sample['case']]=(data,records,stream,decoded)
    # Exact stored historical goldens: no current-main corpus sweep is needed.
    old=json.loads((root/'path-pattern-decoding.json').read_text())
    for sample in old['decodings']:
        stream=sample['streams'][0];data,records,stream=load(root/sample['file'],zstd,stream)
        feature=next(f for f in stream['features'] if f['kind']=='PathPattern')
        record=next(r for r in records if r.is_primary and r.object_id==feature['object_id'])
        actual=decode_path_pattern(data,records,data[record.body:record.end],feature,stream['features'])
        assert actual==feature['tool_settings'],sample['file']
        report['old_body_controls'].append(dict(archive=sample['file'],prior_tool_settings_exact=True))
    old_composites=json.loads((root/'path-pattern-composite-decoding.json').read_text())
    for sample in old_composites['samples']:
        data,records,stream=load(root/sample['archive'],zstd)
        feature=next(f for f in stream['features'] if f['kind']=='PathPattern')
        record=next(r for r in records if r.is_primary and r.object_id==feature['object_id'])
        actual=decode_path_pattern_composites(data,records,data[record.body:record.end],feature,stream['features'])
        assert actual==sample['decoded'],sample['archive']
        unrelated=decode_path_pattern_inputs(data,records,stream['features'],stream['assembly_decoding'],body_selections=stream['body_selections'])
        assert not unrelated['decoded'] and not unrelated['unresolved'],unrelated
        report['old_composite_controls'].append(dict(archive=sample['archive'],prior_decoded_exact=True,new_helper_leaves_body_branch_untouched=True))
    def guard(case,label,identity,offset,replacement):
        data,records,stream,_=saved[case];record=next(r for r in records if r.is_primary and r.object_id==identity)
        changed=bytearray(data);changed[record.body+offset:record.body+offset+len(replacement)]=replacement
        result=decode_path_pattern_inputs(bytes(changed),records,stream['features'],stream['assembly_decoding'],body_selections=stream['body_selections'])
        assert not result['decoded'] and len(result['unresolved'])==1,(label,result)
        report['guards'].append(dict(check=label,passed=True,reason=result['unresolved'][0]['reason']))
    feature=saved['feature_optimized'][3]['decoded'][0];fs=feature['settings'];source=fs['input_descriptors'][0]
    guard('feature_optimized','Unobserved feature compute mode',fs['control_record_object_id'],125,struct.pack('<I',9))
    guard('feature_optimized','Feature descriptor reciprocal owner mismatch',source['descriptor_object_id'],253,struct.pack('<Q',source['source_feature_object_id']))
    guard('feature_optimized','Source feature leaf cannot select pattern itself',source['terminal_object_id'],2,struct.pack('<Q',feature['feature_object_id']))
    guard('feature_optimized','Association leaf must repeat source body anchor',source['association_terminal_object_id'],2,struct.pack('<Q',source['source_feature_object_id']))
    guard('feature_optimized','Result anchor must belong to pattern',fs['result_record_object_ids'][0],92,struct.pack('<Q',source['source_feature_object_id']))
    occurrence=saved['root_occurrence'][3]['decoded'][0];os=occurrence['settings']
    guard('root_occurrence','Created datum must point back to pattern',os['created_occurrence_datum_object_ids'][0],29,struct.pack('<Q',os['source_native_occurrence_object_id']))
    guard('root_occurrence','Typed occurrence element must repeat matching datum',os['element_record_object_ids'][1],7,struct.pack('<Q',os['source_occurrence_datum_object_id']))
    guard('root_occurrence','Occurrence UUID table source must agree',occurrence['feature_object_id'],647,b'0\x000\x000\x000\x00')
    guard('root_occurrence','Uncaptured nonzero start is rejected',os['control_record_object_id'],105,struct.pack('<d',.25))
    report['limitations']=[
        'Only one Extrude Feature or one root Occurrence input, quantity3, positive spacing, zero start, identical orientation and no flip/symmetry/suppression is admitted in this new branch. Existing Body reader scope is unchanged.',
        'Feature compute words0/1 are active Optimized/Identical contrasts. Occurrence word2 is an observed inactive getter, retained raw; its native entity code0 is qualified only by explicit occurrence routes and datums, not equated universally with API enum3.',
        'The actual PathEntity.curve was NurbsCurve3D and lacks startPoint/endPoint getters. All twelve AttributeErrors are retained; finite endpoints come from independently captured underlying SketchLine points.',
        'Occurrence source/result datums, UUID table, reciprocal context routes, local matrices and element membership are explicit. Relative matrices are separately labeled algebraic cache relationships corroborated only by actual translated-case API element matrices.',
        'No feature/solid regeneration, persistent result topology, general opposed path traversal, current visibility/lifecycle replay or joint-solved world placement is implemented. resultFeatures returned null in all actual captures; body/occurrence result records are reported distinctly.']
    report['counts']=dict(actual_samples=3,actual_endpoint_getter_errors=sum(len(s['getter_errors']) for s in truth['samples']),
        old_body_goldens=len(report['old_body_controls']),old_composite_goldens=len(report['old_composite_controls']),malformed_guards=len(report['guards']))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--zstd-library',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'path-pattern-input-decoding.json');args=parser.parse_args()
    report=validate(ROOT,args.zstd_library);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']))
