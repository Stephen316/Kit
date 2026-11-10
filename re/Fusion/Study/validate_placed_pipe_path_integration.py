"""Qualified placed-profile, Pipe Boolean and PathPattern input integration."""
import argparse
import copy
import json
from pathlib import Path

from decode_basics import decode_basics
from decode_pipe_operations import decode_pipe_operations
from decode_path_pattern_inputs import decode_path_pattern_inputs
from decode_placed_profile_portions import decode_placed_profile_portions
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_history_cache_integration import baseline_outputs,differences

ROOT=Path(__file__).resolve().parent
BASELINE='be90d01'
FILES=('pathpatterninputs-7edfa558db34/feature_identical.f3d',
 'pathpatterninputs-7edfa558db34/feature_optimized.f3d',
 'pathpatterninputs-7edfa558db34/root_occurrence.f3d',
 'pipeoperations-6afc81788dbf/cut.f3d','pipeoperations-6afc81788dbf/intersect.f3d','pipeoperations-6afc81788dbf/join.f3d',
 'placedprofiletrims-037ed41056a4/angled_rectangle_overlap.f3d',
 'placedprofiletrims-037ed41056a4/offset_xy_circle_lens.f3d',
 'placedprofiletrims-037ed41056a4/origin_xz_mixed_segment.f3d',
 'trimmedprofiles-a804f8da1496/circle_lens.f3d','trimmedprofiles-a804f8da1496/rectangle_overlap.f3d',
 'mixedprofiletrims-a125a4c1749e/circle_line_segment.f3d','pipemodes-87cfa7d8d82b/circular.f3d',
 'pipeedgecontrasts-5bd287323ae7/line_partial.f3d','pathpatterns-de9857f6a1bc/spacing.f3d',
 'pathpatterncomposites-b6b4cf615504/composite_along.f3d','assembly-acc48a9dc05d/assembly.f3d')
CONTROLS=FILES[9:]
PIPE_ERROR='Unsupported Pipe variant; single path: Unsupported observed Pipe prefix/operation; extended sketch path: Unsupported observed Pipe prefix/operation'
PIPE_LEVEL='Observed Pipe Boolean controls and owned historical target; topology, lifecycle and regeneration unresolved'
PIPE_KEYS=('stored_operation_code','target_body','API_participant_applicability','participant_scope','layout')


def read(name):return json.loads((ROOT/name).read_text())


def restore_fields(actual,prior,keys):
    for key in keys:
        if key in prior:actual[key]=copy.deepcopy(prior[key])
        else:actual.pop(key,None)


def compare(before,current,filename,zstd):
    after=copy.deepcopy(current);members=read_members(ROOT/filename,zstd)
    counts=dict(pipe_Boolean_controls=0,historical_pipe_target_routes=0,recovered_pipe_tool_errors=0,
        removed_irrelevant_pipe_provenance_errors=0,placed_profile_groups=0,placed_profile_portions=0,
        placed_COEDGE_corroborations=0,recovered_placed_memberships=0,explicit_placed_diagnostics=0,
        path_feature_inputs=0,path_occurrence_inputs=0,recovered_path_tool_errors=0)
    assert len(before['streams'])==len(after['streams'])
    pipe_goldens={r['file']:r['expected_summary'] for r in read('pipe-operation-decoding.json')['samples']}
    placed_goldens={r['file']:r['expected_summary'] for r in read('placed-profile-portion-decoding.json')['samples']}
    path_goldens={r['archive']:r['expected_decoded'] for r in read('path-pattern-input-decoding.json')['samples']}
    for original,stream in zip(before['streams'],after['streams']):
        member=stream['member'];data=members[member];records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        features={f['object_id']:f for f in stream['features']};prior_features={f['object_id']:f for f in original['features']}
        pipe=decode_pipe_operations(data,records,stream['features'])
        assert stream.pop('pipe_operations',None)==(pipe if pipe['decoded'] or pipe['unresolved'] else None)
        if filename in pipe_goldens:assert pipe==pipe_goldens[filename],(filename,'Pipe focused evidence differs')
        elif pipe['decoded']:raise AssertionError((filename,'Positive Pipe not in focused report'))
        for row in pipe['decoded']:
            feature=features[row['feature_object_id']];prior=prior_features[row['feature_object_id']]
            assert feature['tool_settings']==row['tool_settings'] and feature['decode_level']==PIPE_LEVEL
            assert feature.pop('pipe_operation_inputs')=={key:row[key] for key in PIPE_KEYS}
            restore_fields(feature,prior,('tool_settings','decode_level'))
            counts['pipe_Boolean_controls']+=1;counts['historical_pipe_target_routes']+=1
        # Path recovery is also restored before jointly checking tool diagnostics.
        path=decode_path_pattern_inputs(data,records,stream['features'],stream['assembly_decoding'],body_selections=stream['body_selections'])
        assert stream.pop('path_pattern_inputs',None)==(path if path['decoded'] or path['unresolved'] else None)
        if filename in path_goldens:assert path==path_goldens[filename],(filename,'Path input focused evidence differs')
        elif path['decoded']:raise AssertionError((filename,'Positive Path input not in focused report'))
        for row in path['decoded']:
            feature=features[row['feature_object_id']];prior=prior_features[row['feature_object_id']]
            assert feature['kind']==row['kind']=='PathPattern' and feature.get('name')==row['name']
            assert feature['tool_settings']==row['settings']
            assert feature['decode_level']=='Observed Feature/Occurrence PathPattern controls and typed input/result provenance; replay, general placement and regeneration unresolved'
            entity=row['settings']['pattern_entity_type']
            assert entity in ('Features','Occurrences')
            counts['path_feature_inputs']+=int(entity=='Features');counts['path_occurrence_inputs']+=int(entity=='Occurrences')
            restore_fields(feature,prior,('tool_settings','decode_level'))
        all_rows=pipe['decoded']+path['decoded'];recovered=set()
        for row in all_rows:
            identity=row['feature_object_id'];kind='Pipe' if row in pipe['decoded'] else 'PathPattern';entry=dict(object_id=identity,kind=kind)
            if entry not in original['tool_decoding']['decoded']:
                assert stream['tool_decoding']['decoded'].count(entry)==1
                stream['tool_decoding']['decoded'].remove(entry);recovered.add((identity,kind))
        old_errors=original['tool_decoding']['unresolved']
        path_errors=('Unsupported PathPattern variant; single path: Unsupported path-pattern control layout; composite path: Unsupported path-pattern control layout',
            'Unsupported PathPattern variant; single path: Unsupported body path-pattern prefix/class; composite path: Unsupported body path-pattern prefix/class')
        removed=[e for e in old_errors if (e['object_id'],e['kind']) in recovered and e['reason'] in (PIPE_ERROR,*path_errors)]
        assert len(removed)==len(recovered)
        assert stream['tool_decoding']['unresolved']==[e for e in old_errors if e not in removed]
        stream['tool_decoding']['unresolved']=copy.deepcopy(old_errors)
        counts['recovered_pipe_tool_errors']+=sum(kind=='Pipe' for _,kind in recovered)
        counts['recovered_path_tool_errors']+=sum(kind=='PathPattern' for _,kind in recovered)
        pipe_ids={r['feature_object_id'] for r in pipe['decoded']}
        old_provenance=original['pipe_path_provenance']['unresolved']
        removed=[e for e in old_provenance if e['feature_object_id'] in pipe_ids and e['reason']=='Unobserved partial BRep Pipe feature layout']
        assert len(removed)==len(pipe_ids)
        assert stream['pipe_path_provenance']['unresolved']==[e for e in old_provenance if e not in removed]
        stream['pipe_path_provenance']['unresolved']=copy.deepcopy(old_provenance)
        counts['removed_irrelevant_pipe_provenance_errors']+=len(removed)
        placed=decode_placed_profile_portions(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
        assert stream.pop('placed_profile_portions',None)==(placed if placed['decoded'] or placed['unresolved'] else None)
        if filename in placed_goldens:assert placed==placed_goldens[filename],(filename,'Placed profile focused evidence differs')
        elif placed['decoded']:raise AssertionError((filename,'Positive placed profile absent from focused report'))
        grouped={};recovered_memberships=set()
        for row in placed['decoded']:
            identity=row['source_feature_object_id'];feature=features[identity];prior=prior_features[identity]
            grouped.setdefault(identity,[]).append(row);counts['placed_profile_groups']+=1
            counts['placed_profile_portions']+=len(row['derived_source_portions'])
            for portion in row['derived_source_portions']:
                assert portion['all_full_tuple_cache_candidates_corroborate']
                counts['placed_COEDGE_corroborations']+=len(portion['all_full_tuple_cache_candidates_corroborate'])
            descriptor=row['profile_descriptor_object_id']
            if any(s['descriptor_object_id']==descriptor for s in prior.get('profile_selection',[])):continue
            selection=dict(sketch_object_id=row['native_sketch_object_id'],sketch_name=row['native_sketch_name'],
                descriptor_object_id=descriptor,loop_definition_object_id=row['profile_loop_definition_object_id'],loops=row['profile_loops'],
                selection_level='Observed placed profile portion references with qualified native component-frame geometry',
                limitations='Derived local parameters and component points remain separate from serialized parameters; general traversal and cache lifecycle remain unresolved')
            assert feature['profile_selection'].count(selection)==1;feature['profile_selection'].remove(selection)
            if not feature['profile_selection']:feature.pop('profile_selection')
            stream['profile_decoding']['decoded'].remove(dict(feature_object_id=identity,descriptor_object_id=descriptor,
                loop_count=len(row['profile_loops']),reference_layout='ObservedPlacedProfilePortionSelectors'))
            recovered_memberships.add(identity)
        for identity,rows in grouped.items():assert features[identity].pop('placed_profile_portions')==rows
        old_errors=original['profile_decoding']['unresolved']
        removed=[e for e in old_errors if e['feature_object_id'] in recovered_memberships and e['reason']=='Unsupported profile curve or trim-reference layout']
        assert len(removed)==len(recovered_memberships)
        assert stream['profile_decoding']['unresolved']==[e for e in old_errors if e not in removed]
        stream['profile_decoding']['unresolved']=copy.deepcopy(old_errors)
        counts['recovered_placed_memberships']+=len(recovered_memberships);counts['explicit_placed_diagnostics']+=len(placed['unresolved'])
    assert after==before,(filename,'Unexpected prior-output change',differences(before,after))
    return dict(file=filename,**counts,all_other_prior_fields_exact=True,
        all_ASM_geometry_and_stored_placement_labels_exact=True,unrelated_profile_tool_and_placement_diagnostics_exact=True,
        qualified_difference_paths=differences(before,current))


def validate(zstd,saved_outputs=None,*,baseline_cache=None,current_cache=None):
    if saved_outputs is not None:
        assert saved_outputs['baseline_commit']==BASELINE and saved_outputs['files']==list(FILES)
        before,current=saved_outputs['before'],saved_outputs['after']
    else:
        if baseline_cache is None:
            default=Path('/private/tmp/fusion-placed-pipe-path-baseline.json')
            baseline_cache=json.loads(default.read_text()) if default.exists() else None
        if baseline_cache is not None:
            assert baseline_cache['baseline_commit']==BASELINE and baseline_cache['files']==list(FILES);before=baseline_cache['before']
        else:before=baseline_outputs(list(FILES),zstd,revision=BASELINE)
        if current_cache is not None:
            assert current_cache['baseline_commit']==BASELINE and current_cache['files']==list(FILES);current=current_cache['after']
        else:current=[json.loads(json.dumps(decode_basics(ROOT/name,zstd))) for name in FILES]
    assert len(before)==len(current)==len(FILES)==17
    rows=[compare(old,actual,name,zstd) for name,old,actual in zip(FILES,before,current)]
    totals={key:sum(row[key] for row in rows) for key,value in rows[0].items() if type(value) is int}
    assert totals['pipe_Boolean_controls']==totals['historical_pipe_target_routes']==totals['recovered_pipe_tool_errors']==3
    assert totals['removed_irrelevant_pipe_provenance_errors']==3
    assert totals['path_feature_inputs']==2 and totals['path_occurrence_inputs']==1 and totals['recovered_path_tool_errors']==3
    assert totals['placed_profile_groups']==3 and totals['recovered_placed_memberships']==1
    assert totals['placed_profile_portions']==8 and totals['placed_COEDGE_corroborations']==16
    assert all(old==actual for name,old,actual in zip(FILES,before,current) if name in CONTROLS)
    return dict(scope='Seventeen saved absolute-path outputs against frozenbe90d01; helper/report qualified additions with exact old-output restoration',
        baseline_commit=BASELINE,samples=rows,summary=dict(saved_files=17,legacy_full_output_controls=len(CONTROLS),**totals,
            unexpected_prior_output_changes=0,ASM_geometry_changes=0,solved_placement_claims=0,live_API_calls=0),
        limitations=['Placed profile derived local parameters and native component points remain distinct from serialized trim values and assembly world geometry.',
            'Pipe historical targets and PathPattern input/result identities do not establish current lifecycle, general topology or regeneration.',
            'Stored occurrence/element matrices remain unsolved caches; old unrelated warnings and placement labels are preserved.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--saved-outputs',type=Path);parser.add_argument('--baseline-outputs',type=Path);parser.add_argument('--current-outputs',type=Path);parser.add_argument('--zstd-library');args=parser.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(zstd,json.loads(args.saved_outputs.read_text()) if args.saved_outputs else None,
        baseline_cache=json.loads(args.baseline_outputs.read_text()) if args.baseline_outputs else None,
        current_cache=json.loads(args.current_outputs.read_text()) if args.current_outputs else None)
    (ROOT/'placed-pipe-path-integration.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],sort_keys=True))
