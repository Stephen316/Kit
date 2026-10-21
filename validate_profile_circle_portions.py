"""Focused selector holdouts, repeated-source identity and derived Circle portions."""
import argparse
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_profile_circle_portions import decode_profile_circle_portions
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_trimmed_profiles import signature, validate as validate_previous

ROOT=Path(__file__).resolve().parent
CAPTURE='trimselectorholdouts-ac245ecd1e2f'
FILES=tuple(CAPTURE+'/'+case+'.f3d' for case in (
    'shifted_unequal_lens','reverse_creation_lens','repeated_circle','repeated_circle_reverse_creation'))+(
    'trimmedprofiles-a804f8da1496/circle_lens.f3d','trimmedprofiles-a804f8da1496/circle_right_complement.f3d')


def validate(zstd=None,model_cache=None):
    cache=dict(model_cache or {})
    report={'scope':'Four independent selector holdouts plus two actual original Circle-profile controls; bounded derived source angles/geometry remain distinct from serialized selectors and API Arc parameterization',
            'interface':'decode_profile_circle_portions(data,records,features,member,members,body_identifier_summary)',
            'integration':'Optional stream profile_circle_portions plus same-named feature arrays. Preserve prior default trimmed_profiles/cache summaries. Qualified repeated-source loop membership may clear only its exact old strict-membership warning after full native/cache proof.',
            'tested_interpretation':{'status':'Observed bounded derived rule corroborated in six saved controlled cases; not a universal file-format rule',
                'selector_b':'Number of proper intersection-defined portions of that source Circle in the observed context',
                'selector_a':'One-based portion index; index1 crosses the positive reference-axis seam, later indices follow increasing reference-axis angle',
                'hypothesis_timing':'Exploratory hypothesis sent to root after actual holdout exports existed but before inspecting their native tuples. It is not presented as preregistered.',
                'not_inferred':['Native serialized endpoint/angle fields','API Arc evaluator parameter conversion','Stored direction flag/API traversal semantics','Creation order or profile array order as an identity join']},
            'samples':[],'guards':[],'contrasts':[],
            'limitations':['Only 2–3 ordinary Circles in identity-placed XY sketches; all source Circles must have independently qualified profile/cache membership.',
                'Proper non-tangent intersections, no reference-axis seam intersections or coincident cuts; captured selector pairs(1,2)/(2,2)/(2,4)/(4,4) only.',
                'Repeated-source context is bounded to the captured distinct(2,4)/(4,4) pair; identical full tuples and missing selected-portion coverage remain rejected.',
                'Every matching COEDGE survives; complete native six-literal identity precedes all geometric corroboration.',
                'Analytic portions are derived from native source geometry and marked DerivedAnalyticSourceCirclePortion. Native selectors remain serialized literals and do not acquire fabricated angle fields.',
                'General Line/Line derivation and other curve/frame/selector families remain unsupported. Original rectangle cache correspondence stays supported separately.',
                'No solver, current-body lifecycle, persistent topology identity or native writer.']}
    checks=0
    def check(condition):
        nonlocal checks
        assert condition
        checks+=1
    totals=Counter();contexts={}
    for relative in FILES:
        path=ROOT/relative;members=read_members(path,zstd)
        model=cache.get(relative)
        if model is None:model=decode_basics(path,zstd);cache[relative]=model
        stream=model['streams'][0];member=stream['member'];data=members[member]
        records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        before=copy.deepcopy(stream['features'])
        result=decode_profile_circle_portions(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
        check(not result['unresolved'] and len(result['decoded'])==1)
        check(before==stream['features'])
        truth=json.loads((path.parent/'ground_truth.json').read_text())
        api=next(sample for sample in truth['samples'] if sample['file']==path.name)
        check(not truth['errors'] and api['export']['sha256']==hashlib.sha256(path.read_bytes()).hexdigest())
        row=result['decoded'][0];api_curves=[curve for loop in api['selected_profile']['loops'] for curve in loop['curves']]
        expected={}
        for curve in api_curves:
            check(not curve['getter_errors'] and not curve['portion_geometry']['getter_errors'])
            check(len(curve['source_indices_by_api_equality'])==1)
            points=[item['result_cm'][1] for item in curve['portion_geometry']['evaluated_points']]
            key=signature(points);check(key not in expected);expected[key]=points
        observed={};max_error=0.
        for portion in row['derived_source_portions']:
            check(portion['geometry_status']=='DerivedAnalyticSourceCirclePortion')
            points=[portion['derived_sketch_local_points_cm'][key] for key in ('start','midpoint','end')]
            key=signature(points);check(key in expected and key not in observed);observed[key]=points
            comparison=expected[key]
            error=max(math.dist(points[1],comparison[1]),
                      max(min(math.dist(point,other) for other in (comparison[0],comparison[2])) for point in (points[0],points[2])))
            check(error<1e-9);max_error=max(max_error,error)
            check(len(portion['all_full_tuple_cache_candidates_corroborate'])==2)
            for evidence in portion['all_full_tuple_cache_candidates_corroborate']:
                check(evidence['max_endpoint_set_error_cm']<1e-9 and evidence['midpoint_error_cm']<1e-9)
                totals['qualified_COEDGEs']+=1
            totals['derived_source_portions']+=1
        check(set(expected)==set(observed))
        actual_multiplicity=sorted(Counter(curve['source_indices_by_api_equality'][0] for curve in api_curves).values())
        native_multiplicity=sorted(Counter(portion['native_source_circle_object_id'] for portion in row['derived_source_portions']).values())
        check(actual_multiplicity==native_multiplicity)
        repeated=[source for source in row['source_curves'] if 'stored_profile_references' in source]
        if repeated:
            check(len(repeated)==1 and len(repeated[0]['stored_profile_references'])==2)
            source=repeated[0]
            check(sorted(ref['stored_reference_selector_pair'] for ref in source['stored_profile_references'])==[[2,4],[4,4]])
            check(all('stored_profile_reference' in candidate for candidate in source['cached_coedge_candidates']))
            check(len({tuple(candidate['stored_decimal_text_fields']) for candidate in source['cached_coedge_candidates']})==2)
            totals['repeated_source_groups']+=1
        totals['files']+=1;totals['source_circle_groups']+=len(row['source_curves']);totals['API_portion_geometry_set_checks']+=1
        report['samples'].append({'file':relative,'archive_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'expected_summary':result,'features_unchanged':True,
            'API_corroboration':{'identity_join_uses_geometry':False,'whole_portion_geometry_set_equal':True,
                'max_endpoint_midpoint_set_error_cm':max_error,'API_direct_source_equality_multiplicity':actual_multiplicity,
                'qualified_native_source_multiplicity':native_multiplicity,
                'API_parameters_not_equated_with_derived_reference_axis_angles':True}})
        contexts[relative]=(data,records,stream,member,members,result)
    # Preserve the entire historical unique-source outputs and guard reasons.
    frozen=json.loads((ROOT/'trimmed-profile-decoding.json').read_text())
    previous=validate_previous(zstd,cache)
    check(previous['guards']==frozen['guards'])
    check(previous['summary']==frozen['summary'])
    for before,after in zip(frozen['samples'],previous['samples']):
        check(before['file']==after['file'] and before['expected_summary']==after['expected_summary'])
    check(previous['legacy_default_controls']==frozen['legacy_default_controls'])
    report['historical_controls']={'frozen_stage_commit':'8c9e3a9','old_three_default_helper_dictionaries_exact':True,
        'old_seven_guards_exact':True,'old_four_default_cache_dictionaries_exact':True,
        'old_report_sha256':hashlib.sha256((ROOT/'trimmed-profile-decoding.json').read_bytes()).hexdigest(),
        'historical_source_hash_scope':'Old report hashes describe the source snapshot at stage8c9e3a9; current opt-in helper/generator source hashes intentionally differ. Golden outputs/guards, rather than relabeled historical hashes, establish compatibility.'}
    # Contrast source identity follows scoped native tuples, not creation/array order.
    a=contexts[CAPTURE+'/repeated_circle.f3d'][-1]['decoded'][0]
    b=contexts[CAPTURE+'/repeated_circle_reverse_creation.f3d'][-1]['decoded'][0]
    repeated_a=next(source for source in a['source_curves'] if 'stored_profile_references' in source)
    repeated_b=next(source for source in b['source_curves'] if 'stored_profile_references' in source)
    check(repeated_a['native_entity_tag']==102 and repeated_b['native_entity_tag']==106)
    def derived_geometry_set(row):
        return sorted(signature([portion['derived_sketch_local_points_cm'][key] for key in ('start','midpoint','end')]) for portion in row['derived_source_portions'])
    check(derived_geometry_set(a)==derived_geometry_set(b))
    report['contrasts'].append({'kind':'Repeated Circle survives reversed creation order',
        'original_repeated_native_tag':102,'reversed_repeated_native_tag':106,
        'selectors_in_both':[[2,4],[4,4]],'derived_full_geometry_sets_equal':True,
        'identity_scope':'Native IDs/tags remain scoped to each file; cross-file shape comparison is corroboration, not a persistent identity join'})
    # Native full-tuple corruption and consistency-preserving wrong-count probe.
    def reject(label,context,bad_data=None,bad_members=None,bad_features=None):
        data,records,stream,member,members,_=context
        result=decode_profile_circle_portions(data if bad_data is None else bad_data,records,
            stream['features'] if bad_features is None else bad_features,member,
            members if bad_members is None else bad_members,stream['body_asm_identifiers'])
        check(not result['decoded'] and bool(result['unresolved']))
        report['guards'].append({'case':label,'rejected':True,'reason':result['unresolved'][0]['reason']})
    context=contexts[CAPTURE+'/repeated_circle.f3d'];data,records,stream,member,members,result=context
    row=result['decoded'][0];by={record.object_id:record for record in records if record.is_primary};definition=by[row['profile_loop_definition_object_id']]
    source=next(source for source in row['source_curves'] if 'stored_profile_references' in source)
    first,second=source['stored_profile_references']
    offset=definition.body+first['stored_tuple_offset_in_definition'];other_offset=definition.body+second['stored_tuple_offset_in_definition']
    bad=bytearray(data);bad[other_offset:other_offset+40]=bad[offset:offset+40]
    reject('Duplicate repeated-source full tuple remains ambiguous',context,bad_data=bytes(bad))
    bad=bytearray(data);struct.pack_into('<I',bad,offset+24,3)
    reject('Uncaptured valid-range selector3/4 not generalized',context,bad_data=bytes(bad))
    blob_member=row['history_blob_member'];blob=members[blob_member];parsed=inspect_asm(blob)
    bad=bytearray(blob)
    for candidate in source['cached_coedge_candidates']:
        if candidate['stored_decimal_text_fields']!=first['stored_coedge_text_fields']:continue
        token=parsed['records'][candidate['attribute_record_index']]['tokens'][9]
        replacement=' '.join(second['stored_coedge_text_fields']).encode('ascii');check(len(replacement)==len(token['value']))
        bad[token['offset']+2:token['offset']+2+len(replacement)]=replacement
    bad_members=dict(members);bad_members[blob_member]=bytes(bad)
    reject('One selected portion loses all candidates although source tag still covered',context,bad_members=bad_members)
    context=contexts[CAPTURE+'/shifted_unequal_lens.f3d'];data,records,stream,member,members,result=context
    row=result['decoded'][0];by={record.object_id:record for record in records if record.is_primary};definition=by[row['profile_loop_definition_object_id']]
    source=next(source for source in row['source_curves'] if source['stored_profile_reference']['stored_reference_selector_pair']==[1,2])
    ref=source['stored_profile_reference'];offset=definition.body+ref['stored_tuple_offset_in_definition']
    bad_data=bytearray(data);struct.pack_into('<II',bad_data,offset+24,2,4)
    blob_member=row['history_blob_member'];blob=members[blob_member];parsed=inspect_asm(blob);bad=bytearray(blob)
    for candidate in source['cached_coedge_candidates']:
        token=parsed['records'][candidate['attribute_record_index']]['tokens'][9];fields=list(candidate['stored_decimal_text_fields']);fields[-2:]=['2','4']
        replacement=' '.join(fields).encode('ascii');check(len(replacement)==len(token['value']))
        bad[token['offset']+2:token['offset']+2+len(replacement)]=replacement
    bad_members=dict(members);bad_members[blob_member]=bytes(bad)
    reject('Native and all cached selector counts changed consistently but geometry has only2 intersections',context,bad_data=bytes(bad_data),bad_members=bad_members)
    bad_features=copy.deepcopy(stream['features']);sketch=next(feature for feature in bad_features if feature['kind']=='Sketch')
    sketch['placement']['sketch_to_component_matrix'][3]=1.
    reject('Nonidentity source Sketch placement outside captured derivation',context,bad_features=bad_features)
    bad_features=copy.deepcopy(stream['features']);sketch=next(feature for feature in bad_features if feature['kind']=='Sketch')
    circles=[geometry for geometry in sketch['geometry'] if geometry['kind']=='Circle'];circles[1]['center_cm'][0]=2.6
    reject('Tangent source geometry outside proper-intersection rule',context,bad_features=bad_features)
    # Exact executed source, current reproduction source and historical source differ explicitly.
    truth=json.loads((ROOT/CAPTURE/'ground_truth.json').read_text());executed=(ROOT/CAPTURE/'executed-generator-source.txt').read_bytes()
    check(hashlib.sha256(executed).hexdigest()==truth['executed_generator_sha256'])
    journal=[json.loads(line) for line in (ROOT/CAPTURE/'journal.jsonl').read_text().splitlines()]
    closes=[entry for entry in journal if entry['phase']=='owned_document_close_returned']
    check(len(closes)==4 and all(entry['returned'] is True and entry['save'] is False for entry in closes))
    report['provenance']={'capture':CAPTURE,'capture_truth_sha256':hashlib.sha256((ROOT/CAPTURE/'ground_truth.json').read_bytes()).hexdigest(),
        'executed_base_generator_sha256':truth['executed_generator_sha256'],
        'executed_source_snapshot':'executed-generator-source.txt','actual_close_returns_all_true':True,
        'raw_truth_metadata_caveat':'Inherited scope string says Three owned local documents, but four actual samples/exports/close returns are recorded. Raw truth remains unchanged; current reproduction generator fixes configured count.',
        'current_source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
            'GenerateTrimSelectorHoldouts.py','GenerateTrimmedProfileContrasts.py','decode_profile_circle_portions.py','decode_trimmed_profiles.py','validate_profile_circle_portions.py')}}
    report['summary']={**dict(totals),'old_unique_source_dictionaries_preserved':3,'old_default_cache_dictionaries_preserved':4,
                       'old_guards_preserved':7,'new_guards':len(report['guards']),'checks':checks}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library',default=None)
    parser.add_argument('--model-cache',type=Path,action='append',default=[],help='Optional dictionary by path, or files/before baseline cache; omitted files decode once')
    parser.add_argument('--output',type=Path,default=ROOT/'profile-circle-portion-decoding.json')
    args=parser.parse_args();cache={}
    for path in args.model_cache:
        value=json.loads(path.read_text());cache.update(dict(zip(value['files'],value['before'])) if 'files' in value and 'before' in value else value)
    report=validate(args.zstd_library,cache);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))
