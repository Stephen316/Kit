"""Focused checks of shared-linear dimension measurement geometry caches."""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_dimension_annotations import decode_dimension_annotations,encode_dimension_measurement_cache,SCOPE
from decode_dimension_controls import decode_dimension_controls
from fusion_archive import read_members
from fusion_metadata import design_records


def validate_fixtures(root,zstd_library=None):
    root=Path(root)
    files=['dimensions-f83a2edd2f72/dimensions.f3d','advanced-627f7fe095f4/advanced.f3d']
    report=dict(scope=SCOPE,interfaces={
        'decoder':'decode_dimension_annotations(data,records,features,dimension_controls=None)->decoded/unresolved/scope',
        'integration':'Call after existing dimension_controls; attach separate measurement-cache summary and optional matching dimension annotation. Existing class/kind/binding/reference/style/text fields are preserved.',
        'replay':'encode_dimension_measurement_cache(item)->129byte cache block'},
        observed_framing='At validated dimension attribute/dependency prefix end: measurement-line XYZ pair, source-anchor XYZ pair, literal0, float64 distance, repeated second source-anchor XYZ; then already-decoded reference/style fields.',
        recovered_fields=[
            'Point/Point input roles are copied in reverse order into source-anchor slots; measurement points are the explicit Aligned/Horizontal/Vertical projection onto the stored annotation line.',
            'Parallel Line/Line Offset copies the explicitly referenced endpoint of each input line, in reverse input order, and shifts both onto the annotation line along the first source line.',
            'Ellipse radius anchors are the explicit center and positive stored major/minor axis radius point; no arbitrary endpoint search or universal side flag inferred.',
            'Concentric inner-first circles contribute radial points on their explicitly referenced circles along the stored annotation direction.',
            'LinearDiameter stores the explicit second point and its reflection across the explicitly referenced first line.',
            'Cached distance equals the bound parameter and projected measurement span; repeated anchor equals source-anchor slot1. Horizontal/Vertical source-anchor Euclidean distance is a concrete counterexample to treating every stored pair as the measurement span.'],
        samples=[],negative_controls=[],malformed_guards=[],limitations=[
            'This is stored annotation/measurement geometry, not a constraint or sketch solver, general dimension recomputation algorithm or final rendered label.',
            'The original nine-case study captures actual parameter/driving getters and API creation text-position arguments, but no final post-creation textPosition getter; existing position evidence remains labeled accordingly.',
            'Only observed ordinary shared-linear-class XY source configurations are admitted. Other shared-class inputs and rotated/3D/cache variants stay explicit failures.',
            'No new reference/style/tangent-side flags or getter properties are invented. Projected and source anchors remain distinct stored fields.',
            'Synthetic radius/reflection/contact construction points do not acquire invented native sketch-point IDs. Native IDs are used only for explicit ordered source and endpoint/center references.'])
    count=replays=comparisons=0;saved=None
    for filename in files:
        stream=decode_basics(root/filename,zstd_library)['streams'][0]
        members=read_members(root/filename,zstd_library);data=members[stream['member']]
        records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')])
        features=stream['features'];controls=decode_dimension_controls(data,records,features)
        before_features=copy.deepcopy(features);before_controls=copy.deepcopy(controls)
        result=decode_dimension_annotations(data,records,features,controls)
        assert not result['unresolved'],result['unresolved']
        assert features==before_features and controls==before_controls
        assert decode_dimension_controls(data,records,features)==before_controls
        truth=json.loads((root/filename).parent.joinpath('ground_truth.json').read_text())
        if 'samples' in truth:
            by_name={x['name']:x['dimension'] for x in truth['samples'] if 'dimension' in x}
        else:
            by_name={x['name']:x['dimensions'][0] for x in truth['sketches'] if len(x['dimensions'])==1}
        sketch_by={f['sketch_object_id']:f for f in features if f['kind']=='Sketch'}
        row=dict(file=filename,expected_decoded=result,checks=[],existing_controls_and_features_unchanged=True)
        for item in result['decoded']:
            raw=encode_dimension_measurement_cache(item)
            assert raw==data[item['geometry_cache_offset']:item['geometry_cache_offset']+129]
            replays+=1;count+=1
            sketch=sketch_by[item['sketch_object_id']];actual=by_name[sketch['name']]
            expected=actual.get('parameter_value',actual.get('value'))
            assert expected is not None and math.isclose(expected,item['cached_measurement_cm'],abs_tol=1e-9)
            comparisons+=1
            row['checks'].append(dict(object_id=item['object_id'],kind=item['kind'],sketch_name=sketch['name'],
                matches_captured_API_measurement=True,actual_API_measurement_cm=expected,
                cache_block_replay_matches=True,cache_block_sha256=hashlib.sha256(raw).hexdigest(),
                source_anchor_distance_cm=math.dist(*item['stored_source_anchor_points_cm']),
                projected_measurement_distance_cm=math.dist(*item['stored_measurement_line_points_cm']),
                source_role_geometry_and_annotation_projection_validated=True))
        report['samples'].append(row)
        if filename==files[0]:saved=data,records,features,controls,result
    assert count==10
    # Tangent/Radial/Angle families retain their established readers. This
    # helper does not turn a same-looking floating point block into a success.
    for filename in ['dimcontrols-2a0d0bdbc8a6/tangent_reference.f3d','dimcontrols-2a0d0bdbc8a6/radius_driving.f3d']:
        s=decode_basics(root/filename,zstd_library)['streams'][0];m=read_members(root/filename,zstd_library);d=m[s['member']]
        rr,_=design_records(d,m[s['member'].replace('BulkStream.dat','MetaStream.dat')])
        a=decode_dimension_annotations(d,rr,s['features'],s['dimension_controls'])
        assert not a['decoded'] and not a['unresolved']
        report['negative_controls'].append(dict(file=filename,no_unrelated_class_recovered=True))
    data,records,features,controls,result=saved
    first=result['decoded'][0]
    def rejected(label,changed,changed_features=features):
        out=decode_dimension_annotations(changed,records,changed_features,controls)
        assert any(r['object_id']==first['object_id'] for r in out['unresolved'])
        report['malformed_guards'].append(dict(label=label,rejected=True,
            reason=next(r['reason'] for r in out['unresolved'] if r['object_id']==first['object_id'])))
    changed=bytearray(data);struct.pack_into('<d',changed,first['geometry_cache_offset'],9.)
    rejected('Wrong stored annotation projection coordinate',bytes(changed))
    changed=bytearray(data);struct.pack_into('<d',changed,first['geometry_cache_offset']+97,9.)
    rejected('Measurement cache disagrees with bound parameter',bytes(changed))
    changed=bytearray(data);struct.pack_into('<d',changed,first['geometry_cache_offset']+105,9.)
    rejected('Repeated anchor differs from explicit first input copy',bytes(changed))
    wrong=copy.deepcopy(features)
    sketch=next(f for f in wrong if f['kind']=='Sketch' and f['sketch_object_id']==first['sketch_object_id'])
    next(g for g in sketch['geometry'] if g['object_id']==first['entity_ids'][0])['sketch_object_id']+=1
    rejected('Source geometry claims a different sketch owner',data,wrong)
    report['validation']=dict(decoded_measurement_caches=count,complete129byte_replays=replays,
        actual_API_value_comparisons=comparisons,independent_holdout_caches=1,
        negative_class_controls=len(report['negative_controls']),malformed_guards_passed=len(report['malformed_guards']),
        existing_annotation_outputs_unchanged=True,new_live_API_calls=0,new_solver_claims=0)
    return report
