"""Qualified asymmetric direction, derived Line trim and rigid-group additions."""
import argparse
import copy
import json
from pathlib import Path

from decode_basics import decode_basics
from decode_asymmetric_fillet_flips import decode_asymmetric_fillet_flips
from decode_profile_line_portions import decode_profile_line_portions
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_history_cache_integration import baseline_outputs,differences

ROOT=Path(__file__).resolve().parent
BASELINE='2e31d25'
FILES=('asymmetricfilletflips-b09b81df3c08/swapped_offsets_false.f3d',
 'asymmetricfilletflips-b09b81df3c08/unequal_default_false.f3d',
 'asymmetricfilletflips-b09b81df3c08/unequal_flipped_true.f3d',
 'linetrimholdouts-456e1d19906d/reverse_rectangle_creation.f3d',
 'linetrimholdouts-456e1d19906d/translated_unequal_rectangles.f3d',
 'rigidgroups-0784a68632cd/nested_include_children.f3d',
 'rigidgroups-0784a68632cd/root_active.f3d',
 'rigidgroups-0784a68632cd/root_suppressed.f3d',
 'edgemodes-87edbf67527b/fillet_asymmetric.f3d',
 'edgemodes-87edbf67527b/fillet_variable.f3d',
 'trimmedprofiles-a804f8da1496/rectangle_overlap.f3d',
 'trimmedprofiles-a804f8da1496/circle_lens.f3d',
 'asbuiltjoints-790406c4498b/rigid.f3d',
 'assembly-acc48a9dc05d/assembly.f3d')
CONTROLS=FILES[9:10]+FILES[11:]


def read(name):return json.loads((ROOT/name).read_text())


def strip_line_additions(current,filename,zstd):
    """Qualify only derived Line metadata; memberships/errors are left intact."""
    after=copy.deepcopy(current)
    counts=dict(derived_line_groups=0,derived_line_portions=0,line_COEDGE_corroborations=0,explicit_line_diagnostics=0)
    expected={r['file']:r['expected_summary'] for r in read('profile-line-portion-decoding.json')['samples']}
    if filename not in expected and not any('profile_line_portions' in s for s in after['streams']):return after,counts
    members=read_members(ROOT/filename,zstd)
    for stream in after['streams']:
        member=stream['member'];data=members[member];records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        summary=decode_profile_line_portions(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
        assert stream.pop('profile_line_portions',None)==(summary if summary['decoded'] or summary['unresolved'] else None)
        if filename in expected:assert summary==expected[filename],(filename,'Line focused evidence differs')
        elif summary['decoded']:raise AssertionError((filename,'Positive Line addition absent from focused evidence'))
        features={f['object_id']:f for f in stream['features']};groups={}
        for row in summary['decoded']:
            groups.setdefault(row['source_feature_object_id'],[]).append(row);counts['derived_line_groups']+=1
            for portion in row['derived_source_portions']:
                assert portion['geometry_status']=='DerivedAnalyticSourceLinePortion'
                assert portion['parameter_status']=='Derived affine fractions between explicit native source endpoints; not serialized trim fields, API evaluator parameters or decoded traversal direction'
                assert portion['all_full_tuple_cache_candidates_corroborate']
                counts['derived_line_portions']+=1;counts['line_COEDGE_corroborations']+=len(portion['all_full_tuple_cache_candidates_corroborate'])
        for identity,rows in groups.items():assert features[identity].pop('profile_line_portions')==rows
        counts['explicit_line_diagnostics']+=len(summary['unresolved'])
    return after,counts


def restore_fields(actual,prior,keys):
    for key in keys:
        if key in prior:actual[key]=copy.deepcopy(prior[key])
        else:actual.pop(key,None)


def compare(before,current,filename,zstd):
    after,counts=strip_line_additions(current,filename,zstd)
    counts.update(asymmetric_fillet_controls=0,recovered_flipped_tool_definitions=0,rigid_groups=0,explicit_rigid_occurrences=0,resolved_rigid_joint_diagnostics=0)
    members=read_members(ROOT/filename,zstd)
    expected={r['file']:r['expected_summary'] for r in read('asymmetric-fillet-flip-decoding.json')['samples']}
    assert len(before['streams'])==len(after['streams'])
    for original,stream in zip(before['streams'],after['streams']):
        member=stream['member'];data=members[member];records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        summary=decode_asymmetric_fillet_flips(data,records,stream['features'])
        assert stream.pop('asymmetric_fillet_flips',None)==(summary if summary['decoded'] or summary['unresolved'] else None)
        if filename in expected:assert summary==expected[filename],(filename,'Asymmetric focused evidence differs')
        features={f['object_id']:f for f in stream['features']};old_features={f['object_id']:f for f in original['features']}
        recovered=set();old_decoded=original['tool_decoding']['decoded']
        for row in summary['decoded']:
            identity=row['feature_object_id'];feature=features[identity]
            assert feature['tool_settings']==row['tool_settings']
            assert feature['decode_level']=='Observed asymmetric-fillet offsets and native flip boolean; exact selected edge orientation and regeneration unresolved'
            restore_fields(feature,old_features[identity],('tool_settings','decode_level'))
            entry=dict(object_id=identity,kind='Fillet')
            if entry not in old_decoded:
                assert any(s.get('isFlipped') is True for s in row['tool_settings']['edge_sets'])
                assert stream['tool_decoding']['decoded'].count(entry)==1
                stream['tool_decoding']['decoded'].remove(entry);recovered.add(identity)
            counts['asymmetric_fillet_controls']+=1
        assert stream['tool_decoding']['decoded']==old_decoded
        old_errors=original['tool_decoding']['unresolved']
        removed=[e for e in old_errors if e['object_id'] in recovered and e['reason']=='Unsupported fillet edge-set mode or layout']
        assert len(removed)==len(recovered)
        assert stream['tool_decoding']['unresolved']==[e for e in old_errors if e not in removed]
        stream['tool_decoding']['unresolved']=copy.deepcopy(old_errors)
        counts['recovered_flipped_tool_definitions']+=len(recovered)
        from decode_rigid_groups import decode_rigid_groups
        rigid=decode_rigid_groups(data,records,stream['assembly_decoding'],stream['features'])
        assert stream.pop('rigid_groups',None)==(rigid if rigid['decoded'] or rigid['unresolved'] else None)
        rigid_expected={r['file']:r['expected_decoded'] for r in read('rigid-group-decoding.json')['samples']}
        if filename in rigid_expected:assert rigid==rigid_expected[filename],(filename,'Rigid-group focused evidence differs')
        elif rigid['decoded']:raise AssertionError((filename,'Positive rigid group absent from focused evidence'))
        group_ids=set();native_ids=set()
        for row in rigid['decoded']:
            identity=row['feature_object_id'];feature=features[identity];prior=old_features[identity]
            assert feature.pop('rigid_group_settings')==row
            assert feature['kind']=='RigidGroup' and feature['name']==(prior.get('name') or row['name'])
            assert feature['decode_level']=='Observed rigid-group occurrence membership and stored relative matrices; suppression and assembly solving unresolved'
            assert row['stored_constraint_type_code']==11 and row['is_suppressed'] is row['include_children'] is None
            restore_fields(feature,prior,('kind','name','decode_level'))
            group_ids.add(identity);native_ids.add(row['object_id']);counts['rigid_groups']+=1
            counts['explicit_rigid_occurrences']+=row['occurrence_count']
        if rigid['decoded'] or rigid['unresolved']:
            discovery=stream['feature_discovery'];prior=original['feature_discovery']
            assert discovery.pop('class_decoded_rigid_group_definition_count')==len(group_ids)
            assert discovery['unsupported_features']==[e for e in prior['unsupported_features'] if e['object_id'] not in group_ids]
            assert discovery['unsupported_feature_count']==len(discovery['unsupported_features'])
            restore_fields(discovery,prior,('unsupported_features','unsupported_feature_count'))
        if native_ids:assert stream['joint_decoding'].pop('rigid_group_native_joint_object_ids')==sorted(native_ids)
        old_joint_errors=original['joint_decoding']['unresolved']
        removed=[e for e in old_joint_errors if e['object_id'] in native_ids and e['kind']=='NativeJoint'
                 and e['reason']=='Native joint not resolved through a supported Assemble definition']
        assert len(removed)==len(native_ids)
        assert stream['joint_decoding']['unresolved']==[e for e in old_joint_errors if e not in removed]
        stream['joint_decoding']['unresolved']=copy.deepcopy(old_joint_errors)
        counts['resolved_rigid_joint_diagnostics']+=len(removed)
        assert stream.get('as_built_joints')==original.get('as_built_joints'),(filename,'Strict AsBuilt diagnostics changed')
        assert len(stream['timeline_decoding']['sequences'])==len(original['timeline_decoding']['sequences'])
        for sequence,prior_sequence in zip(stream['timeline_decoding']['sequences'],original['timeline_decoding']['sequences']):
            assert len(sequence['visible_entries'])==len(prior_sequence['visible_entries'])
            for entry,prior_entry in zip(sequence['visible_entries'],prior_sequence['visible_entries']):
                if entry['object_id'] in group_ids:
                    row=next(r for r in rigid['decoded'] if r['feature_object_id']==entry['object_id'])
                    assert entry['kind']=='RigidGroup' and entry['name']==row['name']
                    restore_fields(entry,prior_entry,('kind','name'))
    assert after==before,(filename,'Unexpected prior-output change',differences(before,after))
    return dict(file=filename,**counts,all_other_prior_fields_exact=True,
        all_ASM_geometry_and_stored_placement_labels_exact=True,old_profile_memberships_and_errors_exact=True,
        qualified_difference_paths=differences(before,current))


def validate(zstd,saved_outputs=None):
    if saved_outputs is None:
        cache=Path('/private/tmp/fusion-direction-trim-group-baseline.json')
        cached=json.loads(cache.read_text()) if cache.exists() else None
        if cached is not None:
            assert cached['baseline_commit']==BASELINE and cached['files']==list(FILES);before=cached['before']
        else:before=baseline_outputs(list(FILES),zstd,revision=BASELINE)
        current=[json.loads(json.dumps(decode_basics(ROOT/name,zstd))) for name in FILES]
    else:
        assert saved_outputs['baseline_commit']==BASELINE and saved_outputs['files']==list(FILES)
        before,current=saved_outputs['before'],saved_outputs['after']
    assert len(before)==len(current)==len(FILES)==14
    rows=[compare(old,actual,name,zstd) for name,old,actual in zip(FILES,before,current)]
    totals={key:sum(row[key] for row in rows) for key,value in rows[0].items() if type(value) is int}
    assert totals['asymmetric_fillet_controls']==4 and totals['recovered_flipped_tool_definitions']==1
    assert totals['derived_line_groups']==3 and totals['derived_line_portions']==12 and totals['line_COEDGE_corroborations']==24
    assert totals['rigid_groups']==totals['resolved_rigid_joint_diagnostics']==3 and totals['explicit_rigid_occurrences']==7
    assert all(old==actual for name,old,actual in zip(FILES,before,current) if name in CONTROLS)
    rule_filename='specialfillets-d50f7a4f04e0/rule_asymmetric.f3d'
    rule=decode_basics(ROOT/rule_filename,zstd)
    members=read_members(ROOT/rule_filename,zstd)
    rule_checked=0
    for stream in rule['streams']:
        data=members[stream['member']];records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')])
        summary=decode_asymmetric_fillet_flips(data,records,stream['features'])
        assert not summary['decoded'] and not summary['unresolved'] and 'asymmetric_fillet_flips' not in stream
        fillets=[f for f in stream['features'] if f['kind']=='Fillet'];feature,=fillets
        assert feature['tool_settings']['mode']=='Rule' and feature['tool_settings']['fillet_feature_type']==1
        assert feature['tool_settings']['is_constant_radius'] is False
        assert feature['tool_settings']['offset_one']['role']=='EdgeOffset1' and feature['tool_settings']['offset_two']['role']=='EdgeOffset2'
        rule_checked+=1
    assert rule_checked==1
    return dict(scope='Fourteen focused absolute-path main-reader outputs against frozen2e31d25; qualify every direction/Line/group addition before exact restoration comparison',
        baseline_commit=BASELINE,samples=rows,rule_asymmetric_gate_control=dict(file=rule_filename,simple_helper_decoded=0,simple_helper_unresolved=0,existing_rule_settings_retained=True,scope='One additional offline current main output; gate control only, separate from frozen14-file equality'),summary=dict(saved_files=14,legacy_full_output_controls=len(CONTROLS),**totals,
            unexpected_prior_output_changes=0,ASM_geometry_changes=0,solved_placement_claims=0,live_API_calls=0),
        limitations=['Derived Line source fractions are separate from serialized trim parameters and API evaluator parameters.',
            'Asymmetric flip is API offset reversal; exact selected topology/world-side correspondence remains unresolved.',
            'Rigid-group constraints and stored occurrence placements do not constitute a solved assembly.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--saved-outputs',type=Path);parser.add_argument('--zstd-library');args=parser.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(zstd,json.loads(args.saved_outputs.read_text()) if args.saved_outputs else None)
    (ROOT/'direction-trim-group-integration.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],sort_keys=True))
