"""Actual placed-profile source frames, component geometry and strict defaults."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_placed_profile_portions import decode_placed_profile_portions, _provider
from decode_placement import transform_point
from decode_profile_circle_portions import decode_profile_circle_portions
from decode_profile_line_portions import decode_profile_line_portions
from decode_profile_mixed_portions import decode_profile_mixed_portions
from decode_sketch import attributes
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_trimmed_profiles import signature

ROOT=Path(__file__).resolve().parent
CAPTURE='placedprofiletrims-037ed41056a4'
FILES=tuple(CAPTURE+'/'+case+'.f3d' for case in ('offset_xy_circle_lens','origin_xz_mixed_segment','angled_rectangle_overlap'))
DECODERS={'CircleCircle':decode_profile_circle_portions,'LineLine':decode_profile_line_portions,'CircleLine':decode_profile_mixed_portions}


def _world_signature(kind,data):
    def point(value):return tuple(round(x,8) for x in value)
    if kind=='Line':return ('Line',tuple(sorted((point(data[0]),point(data[1])))))
    return ('Circle',point(data[0]),point(data[1]),round(data[2],8))


def validate(zstd=None,model_cache=None):
    cache=dict(model_cache or {});checks=0
    report={'scope':'Three actual root-owned placed-profile captures, typed native source/component/BODY frame qualification and component-space API corroboration; existing local derivations reused without fabricating identity placement',
        'interface':'decode_placed_profile_portions(data,records,features,member,members,body_identifier_summary)',
        'integration':'Separate placed_profile_portions summary/feature arrays; preserve original strict identity-only helper outputs/errors. Component points are additional derived fields alongside source-local points and unchanged derived angles/fractions.',
        'API_direction_caveat':{'status':'Observed mislabeled capture metadata retained unchanged',
            'raw_key':'api_component_to_sketch_transform',
            'raw_scope_label':'API transform is component-to-sketch; copied inverse and independent sketchToModelSpace basis probes are retained separately',
            'actual_observation':'In all three saved captures the raw getter matrix and native canonical matrix match independent sketchToModelSpace basis probes; the inverse fails that forward-direction comparison.',
            'production_basis':'Native typed matrix plus reciprocal owners and BODY frame, not the misleading capture/SDK label or inverted getter assumption',
            'plane_origin_limit':'An arbitrary support-plane geometry origin need not equal the Sketch origin; the tilted capture supplies a concrete counterexample.'},
        'samples':[],'old_default_controls':[],'strict_placed_default_controls':[],'guards':[],
        'limitations':['Root-owned parent-component coordinates only; no occurrence/world transform or assembly solve.',
            'Only the explicit143-byte native rigid matrix, typed native Sketch/transform/RootComponent/baseComponent and reciprocal collection/scope families observed here are qualified.',
            'Mapped native BODY must independently belong to the same component and have an explicitly decoded identity ASM transform.',
            'Circle/Line/Mixed local primitive, selector and proper-intersection restrictions remain unchanged; no new selector constants or serialized trim parameters are introduced.',
            'All full-tuple matching COEDGE candidates remain. Geometry corroborates an established native association and does not select its identity.',
            'No persistent topology lifecycle, regeneration, native writer or full-format coverage claim.']}
    def check(condition):
        nonlocal checks
        assert condition
        checks+=1
    def context(relative):
        path=ROOT/relative;members=read_members(path,zstd);model=cache.get(relative)
        if model is None:model=decode_basics(path,zstd);cache[relative]=model
        stream=model['streams'][0];member=stream['member'];data=members[member]
        records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        return data,records,stream,member,members
    contexts={};totals={'files':0,'derived_source_portions':0,'qualified_COEDGEs':0,'component_API_geometry_set_checks':0,
        'measured_basis_checks':0,'source_world_geometry_primitives':0,'inverse_forward_counterexamples':0,'support_plane_origin_counterexamples':0}
    truth=json.loads((ROOT/CAPTURE/'ground_truth.json').read_text())
    strict_errors={'CircleCircle':'Circle portion source placement is outside observed identity context',
        'LineLine':'Derived Line source placement outside observed identity context','CircleLine':'Mixed source Sketch placement outside observed identity context'}
    keys={'CircleCircle':'profile_circle_portions','LineLine':'profile_line_portions','CircleLine':'profile_mixed_portions'}
    for relative in FILES:
        data,records,stream,member,members=context(relative);before=copy.deepcopy(stream['features'])
        result=decode_placed_profile_portions(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
        check(not result['unresolved'] and len(result['decoded'])==1);check(before==stream['features'])
        row=result['decoded'][0];family=row['placed_profile_family'];frame=row['source_frame'];matrix=frame['sketch_to_component_matrix']
        api=next(sample for sample in truth['samples'] if sample['file']==Path(relative).name);placement=api['placement_truth']
        check(not truth['errors'] and api['export']['sha256']==hashlib.sha256((ROOT/relative).read_bytes()).hexdigest())
        check(frame['status']=='QualifiedNativeSketchToComponentFrame')
        native_basis=[transform_point(matrix,point) for point in placement['basis_local_points_cm']]
        observed_basis=placement['basis_component_points_cm']
        raw_basis=[transform_point(placement['api_component_to_sketch_transform'],point) for point in placement['basis_local_points_cm']]
        inverted_basis=[transform_point(placement['api_inverted_sketch_transform'],point) for point in placement['basis_local_points_cm']]
        native_error=max(math.dist(a,b) for a,b in zip(native_basis,observed_basis));raw_error=max(math.dist(a,b) for a,b in zip(raw_basis,observed_basis));inverse_error=max(math.dist(a,b) for a,b in zip(inverted_basis,observed_basis))
        check(native_error<1e-9 and raw_error<1e-9 and inverse_error>1e-6)
        totals['measured_basis_checks']+=4;totals['inverse_forward_counterexamples']+=1
        sketch=next(feature for feature in stream['features'] if feature['kind']=='Sketch' and feature['sketch_object_id']==row['native_sketch_object_id'])
        native_world=[]
        for geometry in sketch['geometry']:
            if geometry['kind']=='Line':native_world.append(_world_signature('Line',[geometry['component_start_cm'],geometry['component_end_cm']]))
            elif geometry['kind']=='Circle':native_world.append(_world_signature('Circle',[geometry['component_center_cm'],geometry['component_normal'],geometry['radius_cm']]))
        api_world=[]
        for source in api['source_curves']:
            geometry=source['full_world_geometry'];check(not geometry['getter_errors'])
            if source['object_type'].endswith('SketchLine'):api_world.append(_world_signature('Line',geometry['data'][1:3]))
            else:api_world.append(_world_signature('Circle',geometry['data'][1:4]))
        check(sorted(native_world)==sorted(api_world));totals['source_world_geometry_primitives']+=len(api_world)
        expected={}
        for curve in [curve for loop in api['selected_profile']['loops'] for curve in loop['curves']]:
            local=[item['result_cm'][1] for item in curve['portion_geometry']['evaluated_points']]
            component=[item['point_cm'] for item in curve['portion_evaluated_component_points_cm']]
            check(len(component)==3 and not curve['getter_errors'])
            key=signature(local);check(key not in expected);expected[key]=(local,component)
        observed=set();max_component_error=0.
        for portion in row['derived_source_portions']:
            local=[portion['derived_sketch_local_points_cm'][key] for key in ('start','midpoint','end')]
            component=[portion['derived_component_points_cm'][key] for key in ('start','midpoint','end')]
            key=signature(local);check(key in expected and key not in observed);observed.add(key)
            check(all(math.dist(transform_point(matrix,a),b)<1e-9 for a,b in zip(local,component)))
            actual=expected[key][1];error=max(math.dist(component[1],actual[1]),max(min(math.dist(point,other) for other in (actual[0],actual[2])) for point in (component[0],component[2])))
            check(error<1e-9);max_component_error=max(max_component_error,error)
            check(len(portion['all_full_tuple_cache_candidates_corroborate'])==2)
            for evidence in portion['all_full_tuple_cache_candidates_corroborate']:
                check(max(evidence['max_endpoint_set_error_cm'],evidence['midpoint_error_cm'])<1e-9);totals['qualified_COEDGEs']+=1
            totals['derived_source_portions']+=1
        check(observed==set(expected))
        body_frame=frame['stored_BODY_frame'];check(body_frame['asm_identity_transform_record_index']==4)
        check(body_frame['stored_scale']==1. and body_frame['stored_flags']==[False,False,False])
        # Exact old strict placement rejection remains available independently.
        defaults={}
        for kind,decoder in DECODERS.items():
            default=decoder(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
            optional=default if default['decoded'] or default['unresolved'] else None
            check(stream.get(keys[kind])==optional)
            defaults[kind]=default
        check(not defaults[family]['decoded'] and defaults[family]['unresolved'][0]['reason']==strict_errors[family])
        report['strict_placed_default_controls'].append({'file':relative,'all_three_default_summaries_equal_preoptin_main':True,'selected_family':family,'unchanged_strict_reason':strict_errors[family]})
        plane_origin=placement['plane_origin_cm'];sketch_origin=native_basis[0];origin_delta=math.dist(plane_origin,sketch_origin)
        if family=='LineLine':check(origin_delta>1e-6);totals['support_plane_origin_counterexamples']+=1
        report['samples'].append({'file':relative,'archive_sha256':hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(),'expected_summary':result,
            'features_unchanged':True,'API_component_geometry_corroboration':{'whole_portion_geometry_set_equal':True,'max_component_endpoint_midpoint_set_error_cm':max_component_error,
                'native_matrix_basis_error_cm':native_error,'raw_mislabeled_API_getter_basis_error_cm':raw_error,'inverse_forward_basis_error_cm':inverse_error,
                'source_world_geometry_set_equal':True,'support_plane_origin_cm':plane_origin,'native_Sketch_origin_component_cm':sketch_origin,'plane_vs_Sketch_origin_distance_cm':origin_delta,
                'identity_join_uses_geometry':False,'scope':'Independent actual sketchToModelSpace and worldGeometry observations; no assembly/world placement conversion'}})
        contexts[relative]=(data,records,stream,member,members,result)
        totals['files']+=1;totals['component_API_geometry_set_checks']+=1
    # Every previous local-family golden is unchanged, including absence of the
    # opt-in fields; these identity contexts receive no new placed diagnostics.
    for report_name,family in (('profile-circle-portion-decoding.json','CircleCircle'),('profile-line-portion-decoding.json','LineLine'),('profile-mixed-portion-decoding.json','CircleLine')):
        for sample in json.loads((ROOT/report_name).read_text())['samples']:
            relative=sample['file'];data,records,stream,member,members=context(relative)
            actual=DECODERS[family](data,records,stream['features'],member,members,stream['body_asm_identifiers'])
            check(actual==sample['expected_summary'])
            placed=decode_placed_profile_portions(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
            check(not placed['decoded'] and not placed['unresolved'])
            report['old_default_controls'].append({'file':relative,'family':family,'exact_frozen_default_dictionary':True,'no_new_placed_rows_or_diagnostics':True})
    # Focused frame corruptions: primitive selectors and native cache naming stay
    # intact, so ownership/matrix/BODY frame proof must independently reject them.
    data,records,stream,member,members,result=contexts[FILES[0]];row=result['decoded'][0];frame=row['source_frame'];by={record.object_id:record for record in records if record.is_primary};transform=by[frame['native_transform_object_id']]
    def reject(label,bad_data=None,bad_members=None,bad_features=None):
        actual=decode_placed_profile_portions(data if bad_data is None else bad_data,records,stream['features'] if bad_features is None else bad_features,member,
            members if bad_members is None else bad_members,stream['body_asm_identifiers'])
        check(not actual['decoded'] and bool(actual['unresolved']));report['guards'].append({'case':label,'rejected':True,'reason':actual['unresolved'][0]['reason']})
    bad=bytearray(data);struct.pack_into('<Q',bad,transform.end-10,row['native_sketch_object_id']);reject('Native transform owner changed from Component to Sketch',bad_data=bytes(bad))
    collection=by[frame['native_sketch_collection_object_id']];payload=data[collection.body:collection.end];_,cursor=attributes(payload,2)
    bad=bytearray(data);struct.pack_into('<Q',bad,collection.body+cursor+4+1,transform.object_id);reject('Reciprocal Sketch collection no longer lists source Sketch',bad_data=bytes(bad))
    bad=bytearray(data);struct.pack_into('<d',bad,transform.body+3,1.25);reject('Native matrix no longer has rigid unit axes',bad_data=bytes(bad))
    bad_features=copy.deepcopy(stream['features']);next(feature for feature in bad_features if feature['kind']=='Sketch')['placement']['sketch_to_component_matrix'][11]+=0.125
    reject('Canonical placement differs from actual native matrix',bad_features=bad_features)
    blob_member=row['history_blob_member'];blob=members[blob_member];parsed=inspect_asm(blob);token=parsed['records'][frame['stored_BODY_frame']['asm_identity_transform_record_index']]['tokens'][6]
    check(token['kind']=='double');bad=bytearray(blob);struct.pack_into('<d',bad,token['offset']+1,1.25);bad_members=dict(members);bad_members[blob_member]=bytes(bad)
    reject('Stored BODY transform becomes nonidentity despite source frame proof',bad_members=bad_members)
    provider=_provider(data,records,stream['features'],members);api=next(sample for sample in truth['samples'] if sample['file']==Path(FILES[0]).name)
    def inverse_callback(sketch,qualified):
        proof=provider(sketch,qualified);proof['sketch_to_component_matrix']=api['placement_truth']['api_inverted_sketch_transform'];return proof
    actual=decode_profile_circle_portions(data,records,stream['features'],member,members,stream['body_asm_identifiers'],source_frame=inverse_callback)
    check(not actual['decoded'] and actual['unresolved'][0]['reason']=='Qualified source frame differs from canonical Sketch placement')
    report['guards'].append({'case':'Inverse suggested by misleading API label cannot replace canonical forward matrix','rejected':True,'reason':actual['unresolved'][0]['reason']})
    check(len(truth['samples'])==3 and not truth['errors'] and (ROOT/CAPTURE/'complete.txt').is_file())
    check(hashlib.sha256((ROOT/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    journal=[json.loads(line) for line in (ROOT/CAPTURE/'journal.jsonl').read_text().splitlines()];closes=[entry for entry in journal if entry['phase']=='owned_document_close_returned']
    check(len(closes)==3 and all(entry['returned'] is True and entry['save'] is False for entry in closes))
    report['provenance']={'baseline_stage':'be90d01','capture':CAPTURE,'capture_truth_sha256':hashlib.sha256((ROOT/CAPTURE/'ground_truth.json').read_bytes()).hexdigest(),
        'executed_generator_sha256':truth['executed_generator_sha256'],'raw_truth_and_executed_source_unchanged':True,
        'current_source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
            'GeneratePlacedProfileTrimContrasts.py','GenerateTrimmedProfileContrasts.py','decode_placed_profile_portions.py','validate_placed_profile_portions.py',
            'decode_profile_circle_portions.py','decode_profile_line_portions.py','decode_profile_mixed_portions.py')},
        'historical_hash_scope':'Old focused-report source hashes remain their historical snapshots; current opt-in helpers are checked against exact old dictionaries and strict placement errors.'}
    report['summary']={**totals,'exact_old_family_dictionaries':len(report['old_default_controls']),'strict_old_placed_error_controls':3,'guards':len(report['guards']),'checks':checks}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--zstd-library');parser.add_argument('--model-cache',type=Path,action='append',default=[])
    parser.add_argument('--output',type=Path,default=ROOT/'placed-profile-portion-decoding.json');args=parser.parse_args();cache={}
    for path in args.model_cache:
        value=json.loads(path.read_text());cache.update(dict(zip(value['files'],value['before'])) if 'files' in value and 'before' in value else value)
    result=validate(args.zstd_library,cache);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
