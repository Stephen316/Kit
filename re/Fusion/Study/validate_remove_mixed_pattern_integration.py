"""Strict focused751c282 integration: public Remove, mixed trims and suppression.

Uses supplied root caches, or regenerates only the pinned20 files when omitted.
Every new summary is recomputed by its source helper, known samples
match their focused report, and only exact qualified additions are restored.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from decode_profile_mixed_portions import decode_profile_mixed_portions
from decode_remove_features import decode_remove_features
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_history_cache_integration import baseline_outputs, differences

ROOT=Path(__file__).resolve().parent
BASELINE='751c282'
FILES=(
    'circularsymsuppression-bef7ede4d911/quantity4_suppress_id2.f3d',
    'circularsymsuppression-bef7ede4d911/quantity5_suppress_id1.f3d',
    'circularsymsuppression-bef7ede4d911/quantity5_suppress_id3.f3d',
    'circularsymsuppression-c837268fa458/quantity4_suppress_id0.f3d',
    'circularsymsuppression-c837268fa458/quantity5_suppress_id0.f3d',
    'circularsymsuppression-c837268fa458/quantity5_suppress_id4.f3d',
    'mixedprofiletrims-a125a4c1749e/circle_line_segment.f3d',
    'mixedprofiletrims-a125a4c1749e/line_circle_reverse_creation.f3d',
    'mixedprofiletrims-a125a4c1749e/shifted_circle_line_segment.f3d',
    'removecontrasts-9c5f83456a0e/nested_occurrence.f3d',
    'removecontrasts-9c5f83456a0e/root_body.f3d',
    'removecontrasts-9c5f83456a0e/root_occurrence.f3d',
    'trimmedprofiles-a804f8da1496/circle_lens.f3d',
    'trimmedprofiles-a804f8da1496/rectangle_overlap.f3d',
    'linetrimholdouts-456e1d19906d/translated_unequal_rectangles.f3d',
    'circularmodes-45f859c1f1b6/body_symmetric.f3d',
    'circularmodes-45f859c1f1b6/body_suppressed.f3d',
    'boundaryfills-a0953038318b/new_middle_remove.f3d',
    'splinepatches-ac5e846e59c0/splinepatches.f3d',
    'rigidgroups-0784a68632cd/nested_include_children.f3d',
)
CIRCULAR_DECODE_LEVEL='Observed symmetric circular suppression IDs through the ordered native element table; seed suppression, placement and regeneration unresolved'
CIRCULAR_OLD_FAILURE='Symmetric circular suppression/API identifier mapping has not been observed'
REMOVE_DECODE_LEVEL='Observed native removal target and component scope; current visibility, lifecycle replay and regeneration unresolved'
PROFILE_OLD_FAILURE='Unsupported profile curve or trim-reference layout'


def read(name):
    return json.loads((ROOT/name).read_text())


def _restore(actual,original,keys):
    for key in keys:
        if key in original:actual[key]=copy.deepcopy(original[key])
        else:actual.pop(key,None)


def _summary(stream,key,value,*,partial=False):
    expected=value if value['decoded'] or value['unresolved'] or partial and value['partial'] else None
    assert stream.pop(key,None)==expected,(key,'Main summary differs from source helper')


def _remove_exact(values,value,label):
    assert values.count(value)==1,(label,'Qualified entry missing/duplicated')
    values.remove(value)


def _timeline_restore(original,current,features,recovered):
    count=0
    assert len(original['sequences'])==len(current['sequences'])
    def entries(old_rows,rows):
        nonlocal count
        assert len(old_rows)==len(rows)
        for prior,entry in zip(old_rows,rows):
            assert prior['object_id']==entry['object_id']
            if entry['object_id'] in recovered:
                feature=features[entry['object_id']]
                assert entry['kind']==feature['kind'] and entry['name']==feature['name']
                _restore(entry,prior,('kind','name'));count+=1
            entries(prior.get('children',[]),entry.get('children',[]))
    for prior,sequence in zip(original['sequences'],current['sequences']):
        entries(prior['visible_entries'],sequence['visible_entries'])
    return count


def _restore_pattern_roles(groups,prior_groups,settings):
    assert len(groups)==len(prior_groups)==1
    descriptor_ids=[item['descriptor_object_id'] for item in settings['input_descriptors']]
    assert len(set(descriptor_ids))==len(descriptor_ids)==settings['input_body_count']==settings['input_count']
    for group,prior in zip(groups,prior_groups):
        assert group['selection_record_object_id']==settings['input_selection_record_object_id']
        assert group['descriptor_object_ids']==descriptor_ids
        assert len(group['bodies'])==settings['input_body_count']
        assert [body['native_body_object_id'] for body in group['bodies']]==settings['native_input_body_object_ids']
        for body,descriptor in zip(group['bodies'],settings['input_descriptors']):
            assert all(body[key]==descriptor[key] for key in ('descriptor_object_id','native_body_object_id','body_anchor_object_id'))
        assert group['role']=='PatternInputBody' and prior['role']=='OwnedBodySelection'
        assert group['role_evidence']=='Decoded explicit pattern input-descriptor collection agrees with the body proxy list'
        assert prior['role_evidence']=='Owned referenced body selection; operation-specific input role remains unresolved'
        _restore(group,prior,('role','role_evidence'))
        assert group==prior
    return len(groups)


def compare(before,current,filename,zstd):
    from decode_circular_symmetric_suppression import decode_circular_symmetric_suppression
    after=copy.deepcopy(current);members=read_members(ROOT/filename,zstd)
    assert len(before['streams'])==len(after['streams'])
    counts=dict(mixed_profile_groups=0,mixed_derived_portions=0,mixed_COEDGE_candidates=0,
        mixed_memberships_recovered=0,mixed_strict_profile_diagnostics_resolved=0,
        public_removal_features=0,public_body_targets=0,public_occurrence_targets=0,
        removed_unsupported_feature_entries=0,removal_timeline_entries_updated=0,
        circular_full_tool_recoveries=0,circular_partial_controls=0,
        circular_tool_diagnostics_resolved=0,circular_summary_diagnostics=0,
        circular_feature_body_roles_qualified=0,circular_summary_body_roles_qualified=0,
        removal_tool_input_kinds_updated=0)
    goldens={
        'profile_mixed_portions':{row['file']:row['expected_summary'] for row in read('profile-mixed-portion-decoding.json')['samples']},
        'remove_features':{row['file']:row['expected_decoded'] for row in read('remove-feature-decoding.json')['samples']},
        'circular_symmetric_suppression':{row['file']:row['expected_summary'] for row in read('circular-symmetric-suppression-decoding.json')['samples']},
    }
    for index,(original,stream) in enumerate(zip(before['streams'],after['streams'])):
        assert original['member']==stream['member']
        member=stream['member'];data=members[member]
        records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        assert [feature['object_id'] for feature in original['features']]==[feature['object_id'] for feature in stream['features']]
        features={feature['object_id']:feature for feature in stream['features']}
        old_features={feature['object_id']:feature for feature in original['features']}
        summaries={
            'profile_mixed_portions':decode_profile_mixed_portions(data,records,stream['features'],member,members,stream['body_asm_identifiers']),
            'remove_features':decode_remove_features(data,records,stream['features'],stream['assembly_decoding'],
                body_selections=stream['body_selections'],component_creations=stream['component_creations']),
            'circular_symmetric_suppression':decode_circular_symmetric_suppression(data,records,stream['features']),
        }
        for key,summary in summaries.items():
            assert key not in original,(filename,key,'New-stage summary already present in frozen baseline')
            _summary(stream,key,summary,partial=key=='circular_symmetric_suppression')
            if filename in goldens[key] and index==0:
                assert summary==goldens[key][filename],(filename,key,'Focused evidence differs')
        # Mixed membership: remove only each exact new selection and corresponding
        # decoded row; restore only the exact previous strict-layout diagnostic.
        grouped={};membership_ids=set()
        for row in summaries['profile_mixed_portions']['decoded']:
            identity=row['source_feature_object_id'];feature=features[identity];prior=old_features[identity]
            assert row['feature_object_id']==identity
            grouped.setdefault(identity,[]).append(row)
            descriptor=row['profile_descriptor_object_id']
            if not any(selection['descriptor_object_id']==descriptor for selection in prior.get('profile_selection',[])):
                selection=dict(sketch_object_id=row['native_sketch_object_id'],sketch_name=row['native_sketch_name'],
                    descriptor_object_id=descriptor,loop_definition_object_id=row['profile_loop_definition_object_id'],
                    loops=row['profile_loops'],selection_level='Observed mixed Circle/Line portion references with corroborated derived source geometry',
                    limitations='Derived angles and source fractions are separate from serialized parameters; general trim reconstruction/traversal remain unresolved')
                _remove_exact(feature['profile_selection'],selection,'Mixed selected-profile membership')
                if not feature['profile_selection']:feature.pop('profile_selection')
                decoded=dict(feature_object_id=identity,descriptor_object_id=descriptor,
                    loop_count=len(row['profile_loops']),reference_layout='ObservedMixedCircleLinePortionSelectors')
                _remove_exact(stream['profile_decoding']['decoded'],decoded,'Mixed profile decoded entry')
                membership_ids.add(identity);counts['mixed_memberships_recovered']+=1
            counts['mixed_profile_groups']+=1
            for portion in row['derived_source_portions']:
                assert portion['geometry_status']=='DerivedAnalyticMixedSource'+portion['native_source_kind']+'Portion'
                assert portion['parameter_status']=='Derived from proper finite-Line/Circle intersections; no serialized trim parameters, API evaluator conversion or stored traversal semantics'
                counts['mixed_derived_portions']+=1
                counts['mixed_COEDGE_candidates']+=len(portion['all_full_tuple_cache_candidates_corroborate'])
        for identity,rows in grouped.items():assert features[identity].pop('profile_mixed_portions')==rows
        prior_errors=original['profile_decoding']['unresolved']
        removed=[error for error in prior_errors if error['feature_object_id'] in membership_ids and error['reason']==PROFILE_OLD_FAILURE]
        assert len(removed)==len(membership_ids),(filename,'Mixed strict diagnostic missing/duplicated')
        assert stream['profile_decoding']['unresolved']==[error for error in prior_errors if error not in removed]
        stream['profile_decoding']['unresolved']=copy.deepcopy(prior_errors)
        counts['mixed_strict_profile_diagnostics_resolved']+=len(removed)
        # Remove changes classification/target metadata only; strict direct-body
        # and assembly diagnostics remain independent, including absent members.
        removals=summaries['remove_features'];remove_ids=set()
        for row in removals['decoded']:
            identity=row['feature_object_id'];feature=features[identity];prior=old_features[identity]
            assert identity not in remove_ids;remove_ids.add(identity)
            assert feature['class_guid']==row['feature_class_guid']
            assert feature['kind']==row['kind'] and feature['name']==(prior.get('name') or row['name'])
            assert feature.pop('remove_feature_settings')==row
            assert feature['decode_level']==REMOVE_DECODE_LEVEL
            input_rows=[entry for entry in stream['tool_body_inputs']['decoded'] if entry['feature_object_id']==identity]
            prior_input_rows=[entry for entry in original['tool_body_inputs']['decoded'] if entry['feature_object_id']==identity]
            assert len(input_rows)==len(prior_input_rows)
            for entry,prior_entry in zip(input_rows,prior_input_rows):
                assert entry['kind']==row['kind']=='RemoveBody' and prior_entry['kind']==prior['kind']=='UnsupportedFeature'
                _restore(entry,prior_entry,('kind',));assert entry==prior_entry
                counts['removal_tool_input_kinds_updated']+=1
            counts['public_removal_features']+=1
            counts['public_body_targets']+=int(row['target']['kind']=='Body')
            counts['public_occurrence_targets']+=int(row['target']['kind']=='Occurrence')
        # Timeline names/kinds are checked against the actual classified features
        # before their exact previous feature fields are restored.
        counts['removal_timeline_entries_updated']+=_timeline_restore(original['timeline_decoding'],stream['timeline_decoding'],features,remove_ids)
        for identity in remove_ids:_restore(features[identity],old_features[identity],('kind','name','decode_level'))
        discovery=stream['feature_discovery'];prior_discovery=original['feature_discovery']
        if removals['decoded'] or removals['unresolved']:
            assert discovery['class_decoded_remove_feature_count']==len(remove_ids)
            assert 'class_decoded_remove_feature_count' not in prior_discovery
            discovery.pop('class_decoded_remove_feature_count')
        else:assert 'class_decoded_remove_feature_count' not in discovery
        discarded=[entry for entry in prior_discovery['unsupported_features'] if entry['object_id'] in remove_ids]
        assert len(discarded)==len(remove_ids),(filename,'Public removal was not uniquely unsupported before')
        for entry in discarded:assert entry['class_guid']==old_features[entry['object_id']]['class_guid']
        assert discovery['unsupported_features']==[entry for entry in prior_discovery['unsupported_features'] if entry not in discarded]
        assert discovery['unsupported_feature_count']==len(discovery['unsupported_features'])
        _restore(discovery,prior_discovery,('unsupported_features','unsupported_feature_count'))
        counts['removed_unsupported_feature_entries']+=len(discarded)
        assert stream['direct_body_features']==original['direct_body_features'],(filename,'Strict direct-body output changed')
        assert stream['assembly_decoding']==original['assembly_decoding'],(filename,'Current assembly output changed')
        # Circular full successes qualify settings and one old mapping warning.
        # Partial seed controls acquire only their explicit new summary.
        circular=summaries['circular_symmetric_suppression'];circular_ids=set()
        for row in circular['decoded']:
            identity=row['feature_object_id'];feature=features[identity];prior=old_features[identity]
            assert identity not in circular_ids;circular_ids.add(identity)
            assert feature['tool_settings']==row['tool_settings'] and feature['decode_level']==CIRCULAR_DECODE_LEVEL
            assert feature.get('unresolved_inputs')==prior.get('unresolved_inputs')
            input_rows=[entry for entry in stream['tool_body_inputs']['decoded'] if entry['feature_object_id']==identity]
            prior_input_rows=[entry for entry in original['tool_body_inputs']['decoded'] if entry['feature_object_id']==identity]
            assert len(input_rows)==len(prior_input_rows)==1
            assert input_rows[0]['body_selection_groups']==feature['body_input_associations']
            counts['circular_feature_body_roles_qualified']+=_restore_pattern_roles(
                feature['body_input_associations'],prior['body_input_associations'],row['tool_settings'])
            counts['circular_summary_body_roles_qualified']+=_restore_pattern_roles(
                input_rows[0]['body_selection_groups'],prior_input_rows[0]['body_selection_groups'],row['tool_settings'])
            _restore(feature,prior,('tool_settings','decode_level'))
            _remove_exact(stream['tool_decoding']['decoded'],dict(object_id=identity,kind='CircularPattern'),'Circular decoded tool')
            counts['circular_full_tool_recoveries']+=1
        for row in circular['partial']:
            identity=row['feature_object_id'];assert identity not in circular_ids
            assert features[identity]==old_features[identity],(filename,'Partial suppression changed feature fields')
            counts['circular_partial_controls']+=1
        prior_errors=original['tool_decoding']['unresolved']
        removed=[error for error in prior_errors if error['object_id'] in circular_ids and error['reason']==CIRCULAR_OLD_FAILURE]
        assert len(removed)==len(circular_ids),(filename,'Old circular mapping failure absent/duplicated')
        assert stream['tool_decoding']['unresolved']==[error for error in prior_errors if error not in removed]
        stream['tool_decoding']['unresolved']=copy.deepcopy(prior_errors)
        counts['circular_tool_diagnostics_resolved']+=len(removed)
        counts['circular_summary_diagnostics']+=len(circular['unresolved'])
    assert current['asm_decoding']==before['asm_decoding'],(filename,'ASM geometry or naming/provenance changed')
    assert after==before,(filename,'Unexpected prior-output change',differences(before,after))
    return dict(file=filename,**counts,all_other_prior_fields_exact=True,
        all_ASM_geometry_and_stored_placement_labels_exact=True,
        strict_direct_body_and_current_assembly_diagnostics_exact=True,
        unrelated_warnings_and_partial_seed_feature_unchanged=True,
        qualified_difference_paths=differences(before,current))


def validate(zstd,baseline_cache=None,current_cache=None):
    if baseline_cache is not None:
        frozen=json.loads(Path(baseline_cache).read_text())
    else:
        frozen=dict(baseline_commit=BASELINE,files=list(FILES),before=baseline_outputs(list(FILES),zstd,revision=BASELINE))
    assert frozen['baseline_commit']==BASELINE and frozen['files']==list(FILES)
    assert len(frozen['files'])==len(frozen['before'])==20
    if current_cache is not None:
        current=json.loads(Path(current_cache).read_text())
        assert current['files']==frozen['files']
        if 'before' in current:assert current['before']==frozen['before']
        actual=current.get('current',current.get('after'))
    else:
        from decode_basics import decode_basics
        actual=[json.loads(json.dumps(decode_basics(ROOT/filename,zstd))) for filename in FILES]
    assert actual is not None and len(actual)==len(frozen['files'])
    assert all(output['file']==str(ROOT/filename) for filename,output in zip(FILES,frozen['before']))
    assert all(output['file']==str(ROOT/filename) for filename,output in zip(FILES,actual))
    rows=[compare(before,after,filename,zstd) for filename,before,after in zip(frozen['files'],frozen['before'],actual)]
    totals={key:sum(row[key] for row in rows) for key,value in rows[0].items() if type(value) is int}
    assert totals['mixed_profile_groups']==3 and totals['mixed_derived_portions']==6 and totals['mixed_COEDGE_candidates']==12
    assert totals['mixed_memberships_recovered']==totals['mixed_strict_profile_diagnostics_resolved']==3
    assert totals['public_removal_features']==3 and totals['public_body_targets']==1 and totals['public_occurrence_targets']==2
    assert totals['removed_unsupported_feature_entries']==3
    assert totals['circular_full_tool_recoveries']==totals['circular_tool_diagnostics_resolved']==5
    assert totals['circular_partial_controls']==1 and totals['circular_summary_diagnostics']==0
    assert totals['circular_feature_body_roles_qualified']==totals['circular_summary_body_roles_qualified']==5
    assert totals['removal_tool_input_kinds_updated']==1
    controls=[filename for filename in frozen['files'] if not filename.startswith(('mixedprofiletrims-','removecontrasts-','circularsymsuppression-'))]
    assert len(controls)==8
    for filename in controls:
        index=frozen['files'].index(filename);assert actual[index]==frozen['before'][index]
    return dict(scope='Root-generated20-file current output versus frozen751c282; only qualified mixed source trims, public Remove provenance and symmetric circular suppression additions are allowed',
        baseline_commit=BASELINE,provenance=dict(
            baseline_input=({'cache_path':str(baseline_cache),'cache_sha256':hashlib.sha256(Path(baseline_cache).read_bytes()).hexdigest()} if baseline_cache is not None
                            else {'local_git_revision':BASELINE,'reader':'baseline_outputs with exactly pinned FILES'}),
            current_input=({'cache_path':str(current_cache),'cache_sha256':hashlib.sha256(Path(current_cache).read_bytes()).hexdigest()} if current_cache is not None
                           else {'reader':'current decode_basics with exactly pinned FILES and absolute paths'}),
            archive_manifest=[dict(file=filename,sha256=hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()) for filename in FILES],
            source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
                'validate_remove_mixed_pattern_integration.py','decode_basics.py','decode_remove_features.py',
                'decode_profile_mixed_portions.py','decode_circular_symmetric_suppression.py')}),samples=rows,
        summary=dict(saved_files=20,legacy_full_output_controls=8,**totals,unexpected_prior_output_changes=0,
            ASM_geometry_changes=0,stored_placement_label_changes=0,unrelated_warnings_cleared=0,live_API_calls=0,main_reader_runs_by_validator=(0 if baseline_cache is not None else 20)+(0 if current_cache is not None else 20)),
        limitations=['Derived mixed source geometry remains separate from serialized/API parameters and persistent topology identity.',
            'Public removal provenance does not restore current occurrence membership or override strict historical direct-body diagnostics.',
            'Circular full settings recovery is limited to the observed non-seed table-index rule; the seed negative remains partial and physically unresolved.',
            'This focused integration comparison is not whole-format coverage, solver/replay validation or native writing.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--baseline-cache',type=Path,help='Optional frozen751c282 cache; omitted regenerates only pinned20 baseline files')
    parser.add_argument('--current-cache',type=Path,help='Optional root current-output cache; omitted decodes only pinned20 current files');parser.add_argument('--zstd-library')
    parser.add_argument('--output',type=Path,default=ROOT/'remove-mixed-pattern-integration.json')
    args=parser.parse_args();zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(zstd,args.baseline_cache,args.current_cache);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
