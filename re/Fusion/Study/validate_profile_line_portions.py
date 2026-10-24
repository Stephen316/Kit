"""Actual Line-profile fraction holdouts, typed source routes and scoped guards."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_profile_circle_portions import decode_profile_circle_portions
from decode_profile_line_portions import decode_profile_line_portions
from decode_sketch import attributes
from decode_trimmed_profiles import decode_trimmed_profiles
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_trimmed_profiles import signature

ROOT=Path(__file__).resolve().parent
CAPTURE='linetrimholdouts-456e1d19906d'
FILES=(CAPTURE+'/reverse_rectangle_creation.f3d',CAPTURE+'/translated_unequal_rectangles.f3d',
       'trimmedprofiles-a804f8da1496/rectangle_overlap.f3d')


def validate(zstd=None,model_cache=None):
    cache=dict(model_cache or {});checks=0
    report={'scope':'Two actual independent Line/Line holdouts plus original rectangle-overlap control; complete native/cache identity before bounded derived source fractions and API geometry corroboration',
        'interface':'decode_profile_line_portions(data,records,features,member,members,body_identifier_summary)',
        'integration':'Optional stream profile_line_portions and same-named feature arrays only; preserve existing selected memberships, warnings and original trimmed/Circle helpers.',
        'tested_interpretation':{'status':'Bounded derived rule confirmed in three saved controlled rectangle-profile cases',
            'selector_b':'Number of proper-intersection-defined finite source Line portions; two in selected captured cases',
            'selector_a':'One-based portion index along explicit native source Line start-to-end direction',
            'derived_domain':'Affine fraction0 at native start endpoint and1 at native end endpoint; source fractions are calculated from intersections, not serialized trim fields',
            'parameter_limit':'Neither the stored ASM edge parameter nor the actual API trimmed-Line evaluator parameter is equated with the derived source fraction'},
        'samples':[],'guards':[],'Circle_gate_controls':[],'contrasts':[],
        'limitations':['Identity-placed XY source Sketch with exactly eight ordinary axis-aligned native Lines forming two explicit disjoint four-Line endpoint cycles.',
            'Selected profile has one outer loop/four unique Line sources with captured selector pairs(1,2)/(2,2).',
            'All eight source Lines, including unselected ones, require typed owner/tag/endpoint-reference and native vector/endpoint-coordinate agreement before computing intersections.',
            'Shared native endpoint IDs qualify ordinary corners; tangential/interior endpoint touches, collinear Lines, duplicate cuts, rotated/3D sources and repeated portions remain unsupported.',
            'Every full-six-tuple matching COEDGE candidate survives. Geometry corroborates an established association and never selects native identity.',
            'Derived geometry does not imply native solver, serialized/API parameter decoding, current-body lifecycle or persistent topology identity.']}
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
    contexts={};totals={'files':0,'derived_source_portions':0,'qualified_COEDGEs':0,'typed_all_source_Lines':0,'API_geometry_set_checks':0,'API_trimmed_evaluators_zero_one':0}
    for relative in FILES:
        data,records,stream,member,members=context(relative);before=copy.deepcopy(stream['features'])
        result=decode_profile_line_portions(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
        check(not result['unresolved'] and len(result['decoded'])==1);check(before==stream['features'])
        row=result['decoded'][0];truth=json.loads((ROOT/Path(relative).parent/'ground_truth.json').read_text());api=next(sample for sample in truth['samples'] if sample['file']==Path(relative).name)
        check(not truth['errors'] and api['export']['sha256']==hashlib.sha256((ROOT/relative).read_bytes()).hexdigest())
        expected={}
        for curve in [curve for loop in api['selected_profile']['loops'] for curve in loop['curves']]:
            check(not curve['getter_errors'] and not curve['portion_geometry']['getter_errors'])
            check(len(curve['source_indices_by_api_equality'])==1)
            source=api['source_curves'][curve['source_indices_by_api_equality'][0]]
            check(source['object_type'].endswith('SketchLine') and curve['portion_geometry']['object_type'].endswith('Line3D'))
            points=[item['result_cm'][1] for item in curve['portion_geometry']['evaluated_points']]
            check(signature(points) not in expected)
            a,b=source['full_sketch_geometry']['data'][1:3];direction=[y-x for x,y in zip(a,b)];square=sum(value*value for value in direction)
            fractions=[sum((x-y)*d for x,y,d in zip(point,a,direction))/square for point in (points[0],points[2])]
            expected[signature(points)]={'points':points,'source_fraction_interval':sorted(fractions)}
            check(curve['portion_geometry']['parameter_extents']==[True,0.,1.])
            totals['API_trimmed_evaluators_zero_one']+=1
        observed={};api_comparisons=[]
        for portion in row['derived_source_portions']:
            check(portion['geometry_status']=='DerivedAnalyticSourceLinePortion')
            points=[portion['derived_sketch_local_points_cm'][key] for key in ('start','midpoint','end')];key=signature(points)
            check(key in expected and key not in observed);observed[key]=points
            actual=expected[key];a,b=portion['derived_native_start_end_fraction_interval']
            check(0<=a<b<=1 and (a,b)!=(0,1))
            check(max(abs(a-actual['source_fraction_interval'][0]),abs(b-actual['source_fraction_interval'][1]))<1e-9)
            error=max(math.dist(points[1],actual['points'][1]),max(min(math.dist(point,other) for other in (actual['points'][0],actual['points'][2])) for point in (points[0],points[2])))
            check(error<1e-9);check(len(portion['all_full_tuple_cache_candidates_corroborate'])==2)
            for candidate in portion['all_full_tuple_cache_candidates_corroborate']:
                check(max(candidate['max_endpoint_set_error_cm'],candidate['midpoint_error_cm'])<1e-9);totals['qualified_COEDGEs']+=1
            api_comparisons.append({'native_source_line_object_id':portion['native_source_line_object_id'],
                'native_source_line_tag':portion['native_source_line_tag'],'derived_source_fraction_interval':[a,b],
                'independently_API_derived_source_fraction_interval':actual['source_fraction_interval'],
                'actual_API_trimmed_Line_evaluator_interval':[0.,1.],'max_endpoint_midpoint_set_error_cm':error,
                'comparison_scope':'Whole geometry-set corroboration after native full-tuple identity; API source selection uses direct API sketchEntity equality, not token/coordinate identity'})
            totals['derived_source_portions']+=1
        check(set(expected)==set(observed));check(len(row['derived_source_line_partitions'])==8)
        totals['files']+=1;totals['typed_all_source_Lines']+=8;totals['API_geometry_set_checks']+=1
        report['samples'].append({'file':relative,'archive_sha256':hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(),
            'expected_summary':result,'features_unchanged':True,'API_geometry_comparisons':api_comparisons})
        contexts[relative]=(data,records,stream,member,members,result)
    # Existing default three positive dictionaries are kept exact, not rewritten.
    prior=json.loads((ROOT/'trimmed-profile-decoding.json').read_text())
    for sample in prior['samples']:
        data,records,stream,member,members=context(sample['file'])
        result=decode_trimmed_profiles(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
        check(result==sample['expected_summary'])
    report['historical_default_controls']={'old_three_trim_cache_dictionaries_exact':True,
        'historical_report_sha256':hashlib.sha256((ROOT/'trimmed-profile-decoding.json').read_bytes()).hexdigest(),
        'source_hash_scope':'Historical report describes its original source snapshot. The new Line helper does not overwrite that report or modify shared readers.'}
    # Circle-only contexts must not receive irrelevant Line-family diagnostics.
    circle_report=json.loads((ROOT/'profile-circle-portion-decoding.json').read_text())
    for sample in circle_report['samples']:
        relative=sample['file'];data,records,stream,member,members=context(relative);before=copy.deepcopy(stream['features'])
        result=decode_profile_line_portions(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
        check(not result['decoded'] and not result['unresolved']);check(before==stream['features'])
        actual_circle=decode_profile_circle_portions(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
        check(actual_circle==sample['expected_summary'])
        report['Circle_gate_controls'].append({'file':relative,'no_Line_rows_or_diagnostics':True,'exact_previous_Circle_helper_dictionary':True})
    # Reversed creation order changes native tags but preserves derived geometry.
    def geometry_set(row):
        return sorted(signature([portion['derived_sketch_local_points_cm'][key] for key in ('start','midpoint','end')]) for portion in row['derived_source_portions'])
    original=contexts[FILES[2]][-1]['decoded'][0];reversed_row=contexts[FILES[0]][-1]['decoded'][0]
    check(geometry_set(original)==geometry_set(reversed_row))
    report['contrasts'].append({'kind':'Reversed rectangle creation order','source_tags_original':[source['native_entity_tag'] for source in original['source_curves']],
        'source_tags_reversed':[source['native_entity_tag'] for source in reversed_row['source_curves']],
        'derived_geometry_sets_equal':True,'identity_scope':'Native references remain file-scoped; cross-file geometry comparison is corroboration only'})
    translated=contexts[FILES[1]][-1]['decoded'][0]
    check(sorted(portion['derived_native_start_end_fraction_interval'] for portion in original['derived_source_portions'])!=sorted(portion['derived_native_start_end_fraction_interval'] for portion in translated['derived_source_portions']))
    report['contrasts'].append({'kind':'Translated unequal rectangles change trim fractions',
        'original_fractions':[portion['derived_native_start_end_fraction_interval'] for portion in original['derived_source_portions']],
        'changed_fractions':[portion['derived_native_start_end_fraction_interval'] for portion in translated['derived_source_portions']],
        'same_captured_selector_pair_domain':[[1,2],[2,2]],'selectors_are_not_fixed_endpoint_values':True})
    # Targeted corruptions leave other native tuples/geometry unchanged.
    data,records,stream,member,members,result=contexts[FILES[1]];row=result['decoded'][0];by={record.object_id:record for record in records if record.is_primary}
    source=row['source_curves'][0];ref=source['stored_profile_reference'];definition=by[row['profile_loop_definition_object_id']]
    offset=definition.body+ref['stored_tuple_offset_in_definition']
    def reject(label,bad_data=None,bad_members=None,bad_features=None):
        result=decode_profile_line_portions(data if bad_data is None else bad_data,records,stream['features'] if bad_features is None else bad_features,member,
            members if bad_members is None else bad_members,stream['body_asm_identifiers'])
        check(not result['decoded'] and bool(result['unresolved']))
        report['guards'].append({'case':label,'rejected':True,'reason':result['unresolved'][0]['reason']})
    bad=bytearray(data);struct.pack_into('<I',bad,offset+24,3);reject('Uncaptured Line selector3',bad_data=bytes(bad))
    # Change native and all named cache selectors together; only the derived
    # source interval/cache geometry disagreement can reject this wrong ordinal.
    new_ordinal=2 if ref['stored_reference_selector_pair'][0]==1 else 1
    bad_data=bytearray(data);struct.pack_into('<I',bad_data,offset+24,new_ordinal)
    blob_member=row['history_blob_member'];blob=members[blob_member];parsed=inspect_asm(blob);bad=bytearray(blob)
    for candidate in source['cached_coedge_candidates']:
        token=parsed['records'][candidate['attribute_record_index']]['tokens'][9];fields=list(candidate['stored_decimal_text_fields']);fields[-2]=str(new_ordinal)
        replacement=' '.join(fields).encode('ascii');check(len(replacement)==len(token['value']))
        bad[token['offset']+2:token['offset']+2+len(replacement)]=replacement
    bad_members=dict(members);bad_members[blob_member]=bytes(bad)
    reject('Native and all cache ordinals consistently changed but stored edge is other portion',bad_data=bytes(bad_data),bad_members=bad_members)
    sketch=next(feature for feature in stream['features'] if feature['kind']=='Sketch')
    selected_ids={source['native_entity_object_id'] for source in row['source_curves']}
    unselected=next(geometry for geometry in sketch['geometry'] if geometry['kind']=='Line' and geometry['object_id'] not in selected_ids)
    native=by[unselected['object_id']];bad=bytearray(data);struct.pack_into('<Q',bad,native.end-10,3)
    reject('Unselected source Line owner differs from explicit Sketch',bad_data=bytes(bad))
    _,cursor=attributes(data[native.body:native.end],2);bad=bytearray(data)
    struct.pack_into('<Q',bad,native.body+cursor+107+1,source['stored_profile_reference']['entity_id'])
    reject('Unselected native Line endpoint reference changed to typed Line object',bad_data=bytes(bad))
    bad_features=copy.deepcopy(stream['features']);next(feature for feature in bad_features if feature['kind']=='Sketch')['placement']['sketch_to_component_matrix'][3]=1.
    reject('Nonidentity source Sketch placement remains unsupported',bad_features=bad_features)
    candidate=source['cached_coedge_candidates'][0];edge=parsed['records'][candidate['edge_record_index']];token=edge['tokens'][4]
    check(token['kind']=='double');bad=bytearray(blob);struct.pack_into('<d',bad,token['offset']+1,token['value']+.125)
    bad_members=dict(members);bad_members[blob_member]=bytes(bad)
    reject('Named cache edge interval changed without source/cached geometry agreement',bad_members=bad_members)
    truth=json.loads((ROOT/CAPTURE/'ground_truth.json').read_text());snapshot=(ROOT/CAPTURE/'executed-generator-source.txt').read_bytes()
    check(len(truth['samples'])==2 and not truth['errors'] and (ROOT/CAPTURE/'complete.txt').is_file())
    check(hashlib.sha256(snapshot).hexdigest()==truth['executed_generator_sha256'])
    journal=[json.loads(line) for line in (ROOT/CAPTURE/'journal.jsonl').read_text().splitlines()];closes=[entry for entry in journal if entry['phase']=='owned_document_close_returned']
    check(len(closes)==2 and all(entry['returned'] is True and entry['save'] is False for entry in closes))
    report['provenance']={'baseline_stage':'2e31d25','capture':CAPTURE,'actual_close_returns_all_true':True,
        'capture_truth_sha256':hashlib.sha256((ROOT/CAPTURE/'ground_truth.json').read_bytes()).hexdigest(),
        'executed_generator_sha256':truth['executed_generator_sha256'],
        'current_source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
            'GenerateLineTrimHoldouts.py','GenerateTrimmedProfileContrasts.py','decode_profile_line_portions.py','validate_profile_line_portions.py','decode_trimmed_profiles.py')}}
    report['summary']={**totals,'old_trim_cache_dictionary_controls':3,'Circle_empty_gate_and_exact_dictionary_controls':6,'guards':len(report['guards']),'checks':checks}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--zstd-library',default=None)
    parser.add_argument('--model-cache',type=Path,action='append',default=[]);parser.add_argument('--output',type=Path,default=ROOT/'profile-line-portion-decoding.json')
    args=parser.parse_args();cache={}
    for path in args.model_cache:
        value=json.loads(path.read_text());cache.update(dict(zip(value['files'],value['before'])) if 'files' in value and 'before' in value else value)
    result=validate(args.zstd_library,cache);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
