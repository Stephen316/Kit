"""Fixed-NURBS Sweep controls, bounded callback guards and prior-default compatibility."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import types
from unittest.mock import patch

from decode_sweep import decode_sweep
from decode_sweep_modes import SWEEP,decode_sweep_modes
from decode_sweep_fixed_spline_paths import decode_sweep_fixed_spline_paths
from decode_sketch import attributes,reference
from validate_replace_face_targets import context

ROOT=Path(__file__).resolve().parent
DIRECTORY='sweepnurbspaths-7ded30a4b9ae'
BASELINE='e8206de'
OLD_ERROR=('Unsupported observed Sweep variant; decode_sweep: Sketch/curve tag missing, unsupported or ambiguous; '
           'decode_sweep_operations: Sweep path sketch/curve tag unresolved or ambiguous; '
           'decode_sweep_profiles: Unsupported observed Sweep mode control header; '
           'decode_solid_sweep: Unsupported observed Cut solid Sweep control layout')
OLD_FILES=('sweeps-5f87eff25e24/line_perpendicular.f3d', 'sweeps-5f87eff25e24/arc_perpendicular.f3d', 'sweeps-5f87eff25e24/arc_parallel.f3d', 'sweeps-5f87eff25e24/arc_partial.f3d', 'sweeps-5f87eff25e24/line_taper.f3d', 'sweeps-5f87eff25e24/line_twist.f3d', 'sweeps-5f87eff25e24/line_surface.f3d', 'sweeps-5f87eff25e24/line_cut.f3d', 'moretools-88a2cd6cad0b/Sweep.f3d', 'moretools-380212ab6368/SweepPartial.f3d', 'sweepguides-db118be14bfe/composite_line_arc.f3d', 'sweepguides-db118be14bfe/closed_circle.f3d', 'sweepguides-9887de71bf9e/rail_scale.f3d', 'sweepguides-9887de71bf9e/rail_stretch.f3d', 'sweepguides-9887de71bf9e/rail_no_scaling.f3d', 'sweepguides-9887de71bf9e/rail_full_extents.f3d', 'sweepguides-9887de71bf9e/guide_surface.f3d', 'sweepguides-9887de71bf9e/guide_surface_chain.f3d', 'sweepoperations-62378e7c0294/join.f3d', 'sweepoperations-62378e7c0294/intersect.f3d', 'sweepoperations-62378e7c0294/two_sided.f3d', 'sweepoperations-62378e7c0294/rail_flip_false.f3d', 'sweepoperations-62378e7c0294/rail_flip_true.f3d', 'sweepoperations-62378e7c0294/guided_cut.f3d', 'sweepprofiles-b2b7a2774752/planar_face.f3d', 'sweepprofiles-b2b7a2774752/open_sketch_surface.f3d', 'sweepprofiles-b2b7a2774752/open_brep_edge_surface.f3d', 'sweepprofiles-b2b7a2774752/two_profile_collection.f3d', 'sweepprofiles-8d489fe02d2d/open_sketch_surface.f3d', 'sweepprofiles-8d489fe02d2d/open_brep_edge_surface.f3d', 'sweepprofiles-f20861d6c5c2/open_brep_edge_partial.f3d', 'sweepprofiles-f20861d6c5c2/open_brep_edge_reversed.f3d', 'solidsweeps-7d2677669e3d/solid_perpendicular.f3d', 'solidsweeps-7d2677669e3d/solid_rigid.f3d', 'solidsweeps-7d2677669e3d/solid_aligned.f3d', 'solidsweeps-7d2677669e3d/solid_twist.f3d', 'solidsweeps-5b5ecd5e01b9/solid_twist_zero.f3d', 'solidsweeps-5b5ecd5e01b9/solid_twist_sixty.f3d')


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def outcome(reader,*args):
    try:return dict(settings=reader(*args))
    except (ValueError,KeyError,IndexError,struct.error) as error:return dict(error_type=type(error).__name__,reason=str(error))


def validate(zstd):
    folder=ROOT/DIRECTORY;truth=json.loads((folder/'ground_truth.json').read_text())
    assert truth['terminal_status']=='Complete' and not truth['errors'] and len(truth['samples'])==3
    assert (folder/'complete.txt').is_file()
    progress=json.loads((folder/'progress.json').read_text())
    assert progress['phase']=='batch_complete' and progress['sample_count']==3 and progress['error_count']==0
    assert digest(folder/'executed-generator-source.txt')==truth['executed_generator_sha256']
    for sdk in truth['sdk_sources'].values():assert digest(folder/sdk['executed_surface_file'])==sdk['executed_surface_sha256']
    source=subprocess.check_output(['git','show',BASELINE+':decode_sweep_modes.py'],cwd=ROOT).decode()
    frozen=types.ModuleType('frozen_sweep_modes');exec(compile(source,'frozen_decode_sweep_modes.py','exec'),frozen.__dict__)
    report=dict(scope='Three actual fixed cubic NURBS Sweep paths, polynomial/rational/multispan, with one Circle profile and solid full perpendicular NewBody controls. Common profile/numeric parser reused; explicit curve caches are separate from traversal and swept geometry.',
        interface='decode_sweep_fixed_spline_paths(data,records,features)->decoded/unresolved/scope; rows feature_object_id/kind/name/settings',
        shared_hook='decode_sweep_modes(...,path_resolver=None); opt-in primary-path-only five-argument callback, bounded selection/descriptor/count/unique-curve/closure schema. Default primitive and rail parsers unchanged.',
        integration=dict(stream='sweep_fixed_spline_paths',settings_field='settings',cleared_old_reason=OLD_ERROR,
            decode_level='Observed Sweep fixed-NURBS path controls and typed sketch source; traversal, persistent topology and regeneration unresolved',
            source_stream='sweep_fixed_spline_sources',source_feature_field='sweep_fixed_spline_source',
            native_source_evidence_path='settings.path.native_source_evidence',
            scope='Replace only same-feature old aggregate Sweep failure after qualified success. Existing input warnings, cached geometry, placements, topology and unrelated errors retained.'),
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(folder/'ground_truth.json'),
            executed_generator_sha256=truth['executed_generator_sha256'],sdk_sources=truth['sdk_sources'],fusion_version=truth['fusion_version']),
        native_schema=dict(Sweep_class_guid=SWEEP,path='Existing owned proxy5A descriptor/E2 leaf selecting sketchID/entitytag; canonical FixedSpline geometry continuation and typed parent-component frame qualified by B source helper',
            controls='Existing decode_sweep_modes defaultNewBody/full/perpendicular controls/profile/control-owner/result-anchor checks; no duplicated codec',
            source_family='Open nonperiodic cubic, natural domain0..1;4controls polynomial/rational single span or6controls polynomial multispan in captured identity native sketch frame'),
        samples=[],malformed_guards=[],legacy_controls=[],
        limitations=['Only captured open fixed-cubic paths, one outer Circle profile, full-distance solid perpendicular NewBody, no guides and zero taper/twist are qualified. Other modes, profiles, frames and periodic forms remain unsupported.',
            'NURBS natural parameter-domain evaluations are derived from stored source controls; no swept surface, frame transport, general trim or regeneration algorithm is reconstructed.',
            'All actual PathEntity.isOpposedToEntity getters are false, but no native contrast proves that semantic. Native traversal/opposition remainsNone and is not inferred from natural knot order.',
            'Configured input.guideRail getter fails InternalValidationError in all3. Native absent guide selections and rolled guideRailNone/successful getters are independent evidence.',
            'Input distanceTwo is ValueInput1 although rolled feature.distanceTwo isNone and native AgainstDistance0 is inactive. No equality is claimed between those distinct states.',
            'Actual API NURBS controlPoints getters serialize metadata rather than coordinates in this capture. Constructor numeric arrays and other actual getters are corroborated separately by the source validator, not represented as direct API control-point equality here.',
            'Rolled-before-node feature.bodies is empty in all3, while timeline-end feature.bodies and current component bodies each contain1; no result identity is inferred from an empty rollback collection.',
            'Native source frame is the parent component identity frame, not a solved occurrence/world placement. Persistent face identities, topology/lifecycle and native writing remain unresolved.'])
    contexts={};control_checks=0
    for actual in truth['samples']:
        filename=DIRECTORY+'/'+actual['file'];data,records,features,member,members=context(filename,zstd)
        assert actual['close_owned_document_returned'] is True and not actual['getter_errors']
        assert actual['export']['returned_success'] is True and actual['export']['sha256']==digest(ROOT/filename)
        assert actual['export']['size_bytes']==(ROOT/filename).stat().st_size
        assert actual['roll_before_feature_returned'] is True and actual['timeline_count']==actual['timeline_marker_position']
        before=copy.deepcopy(features);decoded=decode_sweep_fixed_spline_paths(data,records,features)
        assert before==features and len(decoded['decoded'])==1 and not decoded['unresolved']
        row,=decoded['decoded'];s=row['settings'];fid=row['feature_object_id'];path=s['path']
        feature,=[f for f in features if f['object_id']==fid];record,=[r for r in records if r.is_primary and r.object_id==fid]
        body=data[record.body:record.end];old=outcome(decode_sweep,data,records,body,feature,features)
        assert old==dict(error_type='ValueError',reason=OLD_ERROR)
        input_api=actual['configured_input'];api=actual['feature_before_node']
        assert not api['getter_errors'] and api['healthState']==0 and api['errorOrWarningMessage']==''
        errors=input_api['getter_errors'];assert len(errors)==1 and errors[0]['getter']=='guideRail' and 'InternalValidationError' in errors[0]['error']
        assert s['operation']=='NewBody' and s['stored_operation_code']==4 and input_api['operation']==api['operation']==3
        assert s['orientation']=='Perpendicular' and s['stored_mode_code']==2 and input_api['orientation']==api['orientation']==1
        assert s['is_solid']==input_api['isSolid']==api['isSolid']==True
        assert input_api['distanceOne']['valueType']==1 and input_api['distanceOne']['realValue']==s['path_fraction']==api['distanceOne']['value']==1.
        assert api['distanceOne']['role']=='AlongDistance' and api['distanceOne']['createdBy']['name']==feature['name']
        assert input_api['distanceTwo']['realValue']==1. and api['distanceTwo'] is None
        assert s['distance_two_fraction'] is None and s['stored_against_path_fraction']==0.
        assert api['guideRail'] is None and api['guideSurfaces']==[] and s['stored_guide_rail'] is None and s['guide_surfaces']==[]
        for field,role in [('taperAngle','TaperAngle'),('twistAngle','TwistAngle')]:
            assert input_api[field]['realValue']==api[field]['value']==s['stored_parameter_values'][role]==0.
            assert api[field]['role']==role and api[field]['createdBy']['name']==feature['name']
        assert s['taper_angle_radians']==s['twist_angle_radians']==0.
        assert path['count']==api['path']['count']==input_api['path']['count']==1
        assert path['is_closed']==api['path']['isClosed']==input_api['path']['isClosed']==False
        assert path['segments'][0]['kind']=='FixedSpline' and path['segments'][0]['path_is_opposed_to_entity'] is None
        assert api['path']['entities'][0]['isOpposedToEntity'] is False
        assert path['native_source_evidence']['path_is_opposed_to_entity'] is None
        assert s['profile']['loops'][0]['curve_references'][0]['entity_kind']=='Circle'
        assert len(actual['component_bodies_after_sweep'])==len(actual['feature_at_timeline_end']['bodies'])==len(s['result_body_anchors'])==1
        assert api['bodies']==[]
        for role,binding_id in s['parameter_bindings'].items():
            p,=[p for p in feature['parameters'] if p['binding_object_id']==binding_id and p['role']==role]
            assert p['raw_float64']==s['stored_parameter_values'][role];control_checks+=1
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=decoded,expected_old_failure=old,
            actual_API_operation=api['operation'],actual_API_orientation=api['orientation'],actual_input_guideRail_getter_errors=errors,
            actual_rolled_guideRail=None,actual_rolled_getter_errors=[],actual_input_distanceTwo=1.,actual_rolled_distanceTwo=None,
            actual_API_path_is_opposed_to_entity=False,native_path_opposition=None,actual_current_BRep_count=1,actual_timeline_end_feature_BRep_count=1,actual_rolled_before_node_feature_BRep_count=0,owned_document_closed_true=True))
        contexts[actual['case']]=(data,records,features,row)
    data,records,features,row=contexts['polynomial_cubic'];s=row['settings'];fid=row['feature_object_id']
    by_id={r.object_id:r for r in records if r.is_primary};record=by_id[fid];body=data[record.body:record.end]
    _,base=attributes(body,2) if body[1] else ({},2)
    from decode_sweep_fixed_spline_sources import resolve_sweep_fixed_spline_path
    def reject(label,offset=None,payload=b'',changed_features=None):
        damaged=bytearray(data)
        if offset is not None:damaged[offset:offset+len(payload)]=payload
        fs=features if changed_features is None else changed_features
        answer=decode_sweep_fixed_spline_paths(bytes(damaged),records,fs);assert not answer['decoded'],(label,answer)
        feature=next(f for f in fs if f['object_id']==fid)
        try:decode_sweep_modes(bytes(damaged),records,bytes(damaged)[record.body:record.end],feature,fs,path_resolver=resolve_sweep_fixed_spline_path)
        except (ValueError,KeyError,IndexError,struct.error) as error:reason=str(error)
        else:
            assert answer['unresolved'];reason=answer['unresolved'][0]['reason']
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offset=offset,rejected=True,reason=reason))
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    proxy=by_id[s['path']['selection_record_object_id']];descriptor=by_id[s['path']['segments'][0]['descriptor_object_id']]
    reject('Path proxy feature owner differs',proxy.end-11,ref(fid+1))
    reject('Path descriptor feature owner differs',descriptor.end-11,ref(fid+1))
    reject('Uncaptured surface Sweep',record.body+base+11,b'\0')
    reject('Uncaptured parallel orientation',record.body+base+128,struct.pack('<I',1))
    changed=copy.deepcopy(features);feature=next(f for f in changed if f['object_id']==fid)
    next(p for p in feature['parameters'] if p['role']=='AlongDistance')['raw_float64']=.5
    reject('Uncaptured partial fixed-NURBS distance',changed_features=changed)
    def callback_guard(label,mutate):
        def bad(*args):
            answer=resolve_sweep_fixed_spline_path(*args);mutate(answer);return answer
        with patch('decode_sweep_fixed_spline_sources.resolve_sweep_fixed_spline_path',bad):
            answer=decode_sweep_fixed_spline_paths(data,records,features)
            assert not answer['decoded'] and len(answer['unresolved'])==1
            report['malformed_guards'].append(dict(guard=label,rejected=True,reason=answer['unresolved'][0]['reason']))
    callback_guard('Callback selection identity differs',lambda a:a.update(selection_record_object_id=a['selection_record_object_id']+1))
    callback_guard('Callback count differs from literal proxy',lambda a:a.update(count=2))
    callback_guard('Callback closure flag must be bool',lambda a:a.update(is_closed=0))
    callback_guard('Callback descriptor differs from native list',lambda a:a['segments'][0].update(descriptor_object_id=fid))
    published=mode_results=0
    for filename in OLD_FILES:
        d,rs,fs,_,_=context(filename,zstd);rows=[]
        for f in fs:
            if f.get('class_guid')!=SWEEP:continue
            r=next(r for r in rs if r.start==f['record_offset']);args=(d,rs,d[r.body:r.end],f,fs)
            current=outcome(decode_sweep,*args)
            with patch('decode_sweep_operations.decode_sweep_modes',frozen.decode_sweep_modes),patch('decode_sweep_profiles.decode_sweep_modes',frozen.decode_sweep_modes):
                prior=outcome(decode_sweep,*args)
            assert current==prior,(filename,current,prior)
            direct=outcome(decode_sweep_modes,*args);assert direct==outcome(frozen.decode_sweep_modes,*args)
            published+=int('settings'in current);mode_results+=int('settings'in direct)
            rows.append(dict(feature_object_id=f['object_id'],full_public_outcome_exact=True,strict_default_mode_outcome_exact=True,
                public_outcome_sha256=hashlib.sha256(json.dumps(current,sort_keys=True).encode()).hexdigest(),public_decoded='settings'in current))
        assert rows
        empty=decode_sweep_fixed_spline_paths(d,rs,fs);assert not empty['decoded'] and not empty['unresolved']
        report['legacy_controls'].append(dict(archive=filename,comparisons=rows,new_wrapper_no_candidate=True))
    report['default_preservation']=dict(pinned_revision=BASELINE,pinned_decode_sweep_modes_sha256=hashlib.sha256(source.encode()).hexdigest(),
        legacy_files=len(OLD_FILES),public_decoded_features=published,strict_default_mode_decoded_features=mode_results,
        scope='Full public dictionary/error comparison with pinned common modes substituted into unchanged operations/profile readers; strict default modes compared separately. No main-reader execution.')
    report['source_sha256']={p:digest(ROOT/p) for p in ('decode_sweep_modes.py','decode_sweep_fixed_spline_paths.py','decode_sweep_fixed_spline_sources.py','validate_sweep_fixed_spline_paths.py')}
    report['validation']=dict(actual_exports=3,decoded_fixed_NURBS_paths=3,actual_common_control_comparisons=control_checks,
        actual_input_guideRail_failures_retained=3,native_opposition_unresolved=3,malformed_guards=len(report['malformed_guards']),
        exact_legacy_public_files=len(OLD_FILES),exact_strict_default_mode_files=len(OLD_FILES),no_main_calls=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default='sweep-fixed-spline-path-decoding.json');args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd);Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['validation'],sort_keys=True))
