"""Actual mixed-source portion proof, scoped candidate gates and analytic reuse."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_profile_mixed_portions import decode_profile_mixed_portions
from decode_trimmed_profiles import decode_trimmed_profiles
from decode_sketch import attributes
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_profile_line_portions import validate as validate_previous
from validate_trimmed_profiles import signature

ROOT=Path(__file__).resolve().parent
CAPTURE='mixedprofiletrims-a125a4c1749e'
FILES=tuple(CAPTURE+'/'+case+'.f3d' for case in ('circle_line_segment','line_circle_reverse_creation','shifted_circle_line_segment'))


def validate(zstd=None,model_cache=None):
    cache=dict(model_cache or {});checks=0
    report={'scope':'Three actual ordered/shifted mixed finite-Line/Circle smaller-segment captures; native six-tuple cache identity precedes bounded derived source geometry',
        'interface':'decode_profile_mixed_portions(data,records,features,member,members,body_identifier_summary)',
        'integration':'Optional stream profile_mixed_portions plus feature arrays; full cached native proof may separately support qualified membership, while derived geometry remains explicitly separate from serialized selectors/parameters.',
        'observed_native_grammar':{'Circle_selector_pair':[2,2],'Line_selector_pair':[2,3],'direction_literals':[0],
            'code':3,'secondary_tag':0,'opaque_u64':0,
            'interpretation_scope':'Two proper interior finite-Line/Circle intersections divide the finite Line into3 portions and the Circle into2. Only captured central-Line/upper-minor-Circle selections are accepted.'},
        'analytic_reuse':{'identity':'decode_trimmed_profiles complete native/Sketch/source-BODY/all-six-field cache proof unchanged',
            'source_points':'Existing Circle and Line analytic point functions',
            'cached_points':'Existing Circle cached evaluator and factored evaluate_stored_line_samples, also used by the original Line helper',
            'new_math':'Proper finite-Line/Circle quadratic roots; derived Line fractions and Circle reference-axis angles'},
        'samples':[],'guards':[],'unrelated_family_controls':[],'contrasts':[],
        'limitations':['Exactly one ordinary Circle and one finite horizontal increasing-X Line in an identity XY Sketch; chord strictly above Circle center, both intersections strictly interior to Line.',
            'Only Circle(2,2)/Line(2,3), secondary0, direction0, opaque0 and one outer two-curve profile are admitted.',
            'Derived angle/fraction fields are not native serialized trim parameters or API Arc/Line evaluator parameters.',
            'Complete native tuple identity is proved before geometric corroboration; all named COEDGE candidates remain.',
            'Major segments, reversed Line directions, other chords/frames/tangencies/endpoint cuts, repeated mixed sources and other selector families remain unsupported.',
            'No geometry-based persistent identity, solver, current-body lifecycle or native writing.']}
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
    contexts={};totals={'files':0,'derived_source_portions':0,'qualified_COEDGEs':0,'API_geometry_set_checks':0,'derived_Line_portions':0,'derived_Circle_portions':0}
    for relative in FILES:
        data,records,stream,member,members=context(relative);before=copy.deepcopy(stream['features'])
        result=decode_profile_mixed_portions(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
        check(not result['unresolved'] and len(result['decoded'])==1);check(before==stream['features'])
        row=result['decoded'][0];truth=json.loads((ROOT/CAPTURE/'ground_truth.json').read_text());api=next(sample for sample in truth['samples'] if sample['file']==Path(relative).name)
        check(not truth['errors'] and api['export']['sha256']==hashlib.sha256((ROOT/relative).read_bytes()).hexdigest())
        check(api['available_profile_count']==2)
        expected={}
        for curve in [curve for loop in api['selected_profile']['loops'] for curve in loop['curves']]:
            check(not curve['getter_errors'] and not curve['portion_geometry']['getter_errors'])
            check(len(curve['source_indices_by_api_equality'])==1)
            source=api['source_curves'][curve['source_indices_by_api_equality'][0]]
            check(source['object_type']==curve['underlying_sketch_entity_type'])
            points=[item['result_cm'][1] for item in curve['portion_geometry']['evaluated_points']]
            key=signature(points);check(key not in expected)
            item={'points':points,'source':source,'portion':curve['portion_geometry']}
            if source['object_type'].endswith('SketchLine'):
                check(curve['portion_geometry']['parameter_extents']==[True,0.,1.])
                a,b=source['full_sketch_geometry']['data'][1:3];direction=[y-x for x,y in zip(a,b)];square=sum(value*value for value in direction)
                item['API_derived_source_fraction_interval']=sorted(sum((x-y)*d for x,y,d in zip(point,a,direction))/square for point in (points[0],points[2]))
            else:
                check(source['full_sketch_geometry']['object_type'].endswith('Circle3D'))
                check(curve['portion_geometry']['object_type'].endswith('Arc3D'))
            expected[key]=item
        observed=set();comparisons=[]
        for portion in row['derived_source_portions']:
            kind=portion['native_source_kind'];points=[portion['derived_sketch_local_points_cm'][key] for key in ('start','midpoint','end')];key=signature(points)
            check(key in expected and key not in observed);observed.add(key);actual=expected[key]
            check(actual['source']['object_type'].endswith('Sketch'+kind))
            error=max(math.dist(points[1],actual['points'][1]),max(min(math.dist(point,other) for other in (actual['points'][0],actual['points'][2])) for point in (points[0],points[2])))
            check(error<1e-9);check(len(portion['all_full_tuple_cache_candidates_corroborate'])==2)
            if kind=='Line':
                a,b=portion['derived_native_start_end_fraction_interval'];check(0<a<b<1)
                check(max(abs(a-actual['API_derived_source_fraction_interval'][0]),abs(b-actual['API_derived_source_fraction_interval'][1]))<1e-9)
                parameter_evidence={'derived_source_fraction_interval':[a,b],'actual_API_trimmed_Line_evaluator_interval':[0.,1.],
                    'independently_API_derived_source_fraction_interval':actual['API_derived_source_fraction_interval']}
            else:
                a,b=portion['derived_reference_axis_angle_interval_radians'];bounds=actual['portion']['parameter_extents']
                check(0<a<b<math.pi and bounds[0] and bounds[1]==0.)
                check(math.isclose(b-a,bounds[2]-bounds[1],abs_tol=1e-9))
                parameter_evidence={'derived_reference_axis_angle_interval_radians':[a,b],'actual_API_Arc_evaluator_interval':bounds[1:],
                    'matching_span_does_not_equate_parameter_origins':True}
            for candidate in portion['all_full_tuple_cache_candidates_corroborate']:
                check(max(candidate['max_endpoint_set_error_cm'],candidate['midpoint_error_cm'])<1e-9);totals['qualified_COEDGEs']+=1
            comparisons.append({'native_source_object_id':portion['native_source_object_id'],'native_source_kind':kind,
                'max_endpoint_midpoint_set_error_cm':error,**parameter_evidence,
                'comparison_scope':'Independent whole geometry-set corroboration after native tuple identity; API source relationships use direct sketchEntity equality'})
            totals['derived_source_portions']+=1;totals['derived_'+kind+'_portions']+=1
        check(observed==set(expected));check(len(row['source_curves'])==2)
        # The old default remains strict; mixed support is an explicitly separate branch.
        original=decode_trimmed_profiles(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
        check(not original['decoded'] and bool(original['unresolved']))
        totals['files']+=1;totals['API_geometry_set_checks']+=1
        report['samples'].append({'file':relative,'archive_sha256':hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(),
            'expected_summary':result,'features_unchanged':True,'API_geometry_comparisons':comparisons,
            'original_trim_helper_rejection_preserved':original['unresolved']})
        contexts[relative]=(data,records,stream,member,members,result)
    # Re-execute prior focused validator once because the shared Line cache
    # evaluator was factored; compare complete old values, not historical hashes.
    old=json.loads((ROOT/'profile-line-portion-decoding.json').read_text());previous=validate_previous(zstd,cache)
    check(previous['summary']==old['summary']);check(previous['guards']==old['guards'])
    for before,after in zip(old['samples'],previous['samples']):check(before['expected_summary']==after['expected_summary'])
    check(previous['Circle_gate_controls']==old['Circle_gate_controls'])
    report['previous_default_controls']={'historical_Line_stage':'751c282','exact_old_Line_helper_dictionaries':3,
        'exact_old_Line_guards':6,'exact_old_Circle_helper_dictionaries':6,'prior_validator_checks':previous['summary']['checks'],
        'historical_report_sha256':hashlib.sha256((ROOT/'profile-line-portion-decoding.json').read_bytes()).hexdigest(),
        'source_hash_scope':'Historical source hashes remain historical. The factored sampler changes current source bytes while complete default outputs and errors remain exact.'}
    controls=[sample['file'] for sample in old['samples']]+[sample['file'] for sample in json.loads((ROOT/'profile-circle-portion-decoding.json').read_text())['samples']]
    for relative in controls:
        data,records,stream,member,members=context(relative);before=copy.deepcopy(stream['features'])
        result=decode_profile_mixed_portions(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
        check(not result['decoded'] and not result['unresolved']);check(before==stream['features'])
        report['unrelated_family_controls'].append({'file':relative,'no_mixed_rows_or_diagnostics':True,'features_unchanged':True})
    # Reversal changes native tags/order while the qualified derived shape stays equal.
    def geometry_set(row):
        return sorted(signature([portion['derived_sketch_local_points_cm'][key] for key in ('start','midpoint','end')]) for portion in row['derived_source_portions'])
    first=contexts[FILES[0]][-1]['decoded'][0];reversed_row=contexts[FILES[1]][-1]['decoded'][0];shifted=contexts[FILES[2]][-1]['decoded'][0]
    check(geometry_set(first)==geometry_set(reversed_row));check(first['derived_source_circle_line_intersections']['derived_line_fractions']!=shifted['derived_source_circle_line_intersections']['derived_line_fractions'])
    report['contrasts'].append({'kind':'Creation order reversed','source_tag_pairs_original':[[source['native_entity_kind'],source['native_entity_tag']] for source in first['source_curves']],
        'source_tag_pairs_reversed':[[source['native_entity_kind'],source['native_entity_tag']] for source in reversed_row['source_curves']],
        'derived_geometry_sets_equal':True,'native_identity_remains_file_scoped':True})
    report['contrasts'].append({'kind':'Shifted center/radius/chord change derived intervals',
        'original_intersections':first['derived_source_circle_line_intersections'],'shifted_intersections':shifted['derived_source_circle_line_intersections'],
        'same_literal_selector_domain':{'Circle':[2,2],'Line':[2,3]}})
    data,records,stream,member,members,result=contexts[FILES[0]];row=result['decoded'][0];by={record.object_id:record for record in records if record.is_primary}
    source=next(source for source in row['source_curves'] if source['native_entity_kind']=='Line');ref=source['stored_profile_reference'];definition=by[row['profile_loop_definition_object_id']];offset=definition.body+ref['stored_tuple_offset_in_definition']
    def reject(label,bad_data=None,bad_members=None,bad_features=None):
        result=decode_profile_mixed_portions(data if bad_data is None else bad_data,records,stream['features'] if bad_features is None else bad_features,member,
            members if bad_members is None else bad_members,stream['body_asm_identifiers'])
        check(not result['decoded'] and bool(result['unresolved']));report['guards'].append({'case':label,'rejected':True,'reason':result['unresolved'][0]['reason']})
    bad=bytearray(data);struct.pack_into('<I',bad,offset+24,1);reject('Uncaptured outer Line portion1/3',bad_data=bytes(bad))
    bad=bytearray(data);struct.pack_into('<Q',bad,offset+12,1);reject('Nonzero mixed secondary tag',bad_data=bytes(bad))
    bad=bytearray(data);struct.pack_into('<I',bad,offset+20,1);reject('Uncaptured mixed stored direction1',bad_data=bytes(bad))
    native=by[source['native_entity_object_id']];_,cursor=attributes(data[native.body:native.end],2)
    bad=bytearray(data);struct.pack_into('<Q',bad,native.body+cursor+107+1,native.object_id)
    reject('Native mixed Line endpoint reference replaced by Line object',bad_data=bytes(bad))
    bad_features=copy.deepcopy(stream['features']);next(feature for feature in bad_features if feature['kind']=='Sketch')['placement']['sketch_to_component_matrix'][3]=1.
    reject('Nonidentity mixed source Sketch placement',bad_features=bad_features)
    blob_member=row['history_blob_member'];blob=members[blob_member];parsed=inspect_asm(blob);edge=parsed['records'][source['cached_coedge_candidates'][0]['edge_record_index']];token=edge['tokens'][4]
    check(token['kind']=='double');bad=bytearray(blob);struct.pack_into('<d',bad,token['offset']+1,token['value']+.125)
    bad_members=dict(members);bad_members[blob_member]=bytes(bad);reject('Full-tuple named Line cache interval disagrees with derived mixed portion',bad_members=bad_members)
    truth=json.loads((ROOT/CAPTURE/'ground_truth.json').read_text());snapshot=(ROOT/CAPTURE/'executed-generator-source.txt').read_bytes()
    check(len(truth['samples'])==3 and not truth['errors'] and (ROOT/CAPTURE/'complete.txt').is_file());check(hashlib.sha256(snapshot).hexdigest()==truth['executed_generator_sha256'])
    journal=[json.loads(line) for line in (ROOT/CAPTURE/'journal.jsonl').read_text().splitlines()];closes=[entry for entry in journal if entry['phase']=='owned_document_close_returned']
    check(len(closes)==3 and all(entry['returned'] is True and entry['save'] is False for entry in closes))
    report['provenance']={'baseline_stage':'751c282','capture':CAPTURE,'actual_close_returns_all_true':True,
        'capture_truth_sha256':hashlib.sha256((ROOT/CAPTURE/'ground_truth.json').read_bytes()).hexdigest(),
        'executed_generator_sha256':truth['executed_generator_sha256'],
        'current_source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
            'GenerateMixedProfileTrimContrasts.py','GenerateTrimmedProfileContrasts.py','decode_profile_mixed_portions.py','validate_profile_mixed_portions.py','decode_profile_line_portions.py')}}
    report['summary']={**totals,'old_Line_dictionary_controls':3,'old_Circle_dictionary_controls':6,
        'old_Line_guards_preserved':6,'unrelated_empty_gate_controls':len(report['unrelated_family_controls']),
        'guards':len(report['guards']),'checks':checks}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--zstd-library',default=None)
    parser.add_argument('--model-cache',type=Path,action='append',default=[]);parser.add_argument('--output',type=Path,default=ROOT/'profile-mixed-portion-decoding.json')
    args=parser.parse_args();cache={}
    for path in args.model_cache:
        value=json.loads(path.read_text());cache.update(dict(zip(value['files'],value['before'])) if 'files' in value and 'before' in value else value)
    result=validate(args.zstd_library,cache);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
