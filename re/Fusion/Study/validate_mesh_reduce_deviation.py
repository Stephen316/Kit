"""Three MaximumDeviation captures; literal methods, active Tolerance, old exactness."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
from unittest.mock import patch

from validate_mesh_repair import context
from decode_mesh_geometry_variants import decode_mesh_contents_variants,decode_mesh_asset
from decode_mesh_reduce import REDUCE,decode_mesh_reduce
from decode_parameters import decode_stream
from decode_placement import transform_point

ROOT=Path(__file__).resolve().parent
DIRECTORY='meshreducedeviations-05a5d48e46d0'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_arrays(geometry,actual,matrix=None):
    points=geometry.get('component_node_coordinates_cm')
    if points is None:points=[transform_point(matrix,p) for p in geometry['stored_node_coordinates_float32']]
    assert [v for p in points for v in p]==actual['original_polygon_mesh']['nodeCoordinatesAsDouble']
    assert geometry['triangle_node_indices']==actual['original_polygon_mesh']['triangleNodeIndices']
    assert len(points)==actual['original_polygon_mesh']['nodeCount']==6
    assert len(geometry['triangle_node_indices'])//3==actual['original_polygon_mesh']['triangleCount']==8


def validate(zstd):
    truth_path=ROOT/DIRECTORY/'ground_truth.json'
    truth=json.loads(truth_path.read_text())
    assert truth['terminal_status']=='complete' and not truth['errors'] and len(truth['samples'])==3
    assert digest(ROOT/DIRECTORY/'executed-generator-source.txt')==truth['executed_generator_sha256']
    assert digest(ROOT/DIRECTORY/'executed-mesh-source-helper.txt')==truth['mesh_source_helper_sha256']
    assert digest(ROOT/DIRECTORY/truth['sdk_surface_snapshot'])==truth['sdk_surface_snapshot_sha256']
    report=dict(scope='Three actual owned MaximumDeviation MeshReduce captures: Adaptive0.05cm/0.1cm and requested Uniform0.1cm. Literal native/API method and target, owned active Tolerance, current/additional assets and exact stored cache controls only.',
        interface='decode_mesh_reduce(data,records,features,member,members,mesh_contents=None); prior summaries unchanged, new MaximumDeviation summary includes conditional scope/partial[]. Partial rows also carry same-feature unresolved and never become full decoded tool settings.',
        integration=dict(stream='mesh_reductions',counter='class_decoded_mesh_reduce_count',
            decode_level_scope='Existing MeshReduce main decode_level unchanged; no new warning removal or common parser extension',
            compatibility='All four historical Reduce full summary dictionaries, including failed-expression negative capture with no Reduce feature, remain exactly equal.'),
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(truth_path),
            executed_generator_sha256=truth['executed_generator_sha256'],mesh_source_helper_sha256=truth['mesh_source_helper_sha256'],
            sdk_runtime_source_sha256=truth['sdk_runtime_source_sha256'],sdk_surface_snapshot_sha256=truth['sdk_surface_snapshot_sha256']),
        native_schema=dict(class_guid=REDUCE,target_uint32_offset=29,MaximumDeviation_target_code=0,
            method_uint32_offset=13,observed_method_codes={'0':'Adaptive','1':'Uniform'},
            maximum_deviation_owned_binding_reference_offset=2,native_parameter_role='Tolerance',
            observed_internal_cm_values=[0.05,0.1],accepted_numeric_scope='Positive finite float64 under the same strictly validated typed role/binding/attached parameter framing; zero/negative/nonfinite rejected',
            inactive_bindings={'Proportion':0.,'Face Count':0},current_asset_reference_offset=44,additional_asset_reference_offset=55,
            selection_reference_offset=70,ordered_dependencies=['selection proxy','descriptor','Proportion binding','Tolerance binding','Face Count binding'],
            method_scope='Requested Uniform, configured input getter, feature getter and native method all remain1. SDK says MaximumDeviation internally uses Adaptive, but actual executed algorithm is not recovered and native/getter method is not normalized.'),
        samples=[],malformed_guards=[],legacy_controls=[],partial_geometry_guard=None,
        limitations=['Positive finite Tolerance is a decoded requested control, not a measured maximum deviation or guarantee that a reduction algorithm achieved it.',
            'Native/API method is preserved literally. effective_algorithm and maximum_deviation_attained remain None; SDK override prose does not turn Uniform1 into a decoded Adaptive algorithm.',
            'Initial unassigned maximumDeviation getter raises InternalValidationError in all three input default snapshots. Null getter result is an error, not an actual value0 or absent parameter; configured/feature getters succeed after assignment.',
            'Proportion and Face Count serialized parameters remain0/inactive. Their target-specific control getters/setters are not invoked by these captures.',
            'Native current mesh ownership remains independently reciprocal BaseMesh membership. Reduce is an owned selection/control route, not promoted to native owner or API baseOrFormFeature.',
            'Additional typed asset matches rolled input arrays after explicit reference/UUID/file binding, but temporal role stays None; no coordinate/order/name search chooses identity.',
            'Current source/result counts6/8 and cache equality do not establish simplification, geometric error bounds, face correspondence or regeneration.',
            'Current geometry failure retains active controls and metadata as partial plus same-feature unresolved with original strict reason; no truncated or manufactured full geometry.',
            'All geometry uses existing observed layouts. Independent normals/groups holdouts are reported separately.'])
    contexts={};method_checks=parameter_checks=array_checks=default_errors=0
    for actual in truth['samples']:
        filename=DIRECTORY+'/'+actual['file']
        assert actual['reduce_status']=='FeatureReturned' and not actual['getter_errors'] and not actual['setter_errors']
        assert actual['close_owned_document_returned'] is True and actual['roll_before_feature_returned'] is True
        assert actual['input_mesh_equals_import_handle'] is True and actual['feature_input_mesh_equals_import_handle'] is True
        assert actual['export']['sha256']==digest(ROOT/filename) and actual['export']['size_bytes']==(ROOT/filename).stat().st_size
        data,records,features,member,members=context(filename,zstd)
        before=copy.deepcopy(features)
        mesh_summary=decode_mesh_contents_variants(data,records,member,members)
        decoded=decode_mesh_reduce(data,records,features,member,members,mesh_summary)
        assert features==before and not decoded['unresolved'] and decoded.get('partial')==[]
        row,=decoded['decoded'];settings=row['settings']
        method=1 if actual['case'].startswith('requested_uniform') else 0
        deviation=0.05 if actual['case'].endswith('zero_five') else 0.1
        assert settings['target_type']=='MaximumDeviation' and settings['stored_target_code']==0
        assert settings['stored_method_code']==method and settings['method']==('Uniform' if method else 'Adaptive')
        assert settings['maximum_deviation_cm']==deviation
        assert settings['maximum_deviation_attained'] is settings['effective_algorithm'] is settings['mesh_reduce_owns_current_mesh'] is None
        assert not settings['geometry_unresolved']
        defaults=actual['input_defaults']
        assert defaults['meshReduceMethodType']==defaults['meshReduceTargetType']==0 and defaults['maximumDeviation'] is None
        error,=defaults['control_getter_errors']
        assert error['getter']=='maximumDeviation' and 'InternalValidationError' in error['error']
        default_errors+=1
        for key in ('input_before_add','feature_before_node','feature_at_timeline_end'):
            api=actual[key]
            assert api['meshReduceMethodType']==method and api['meshReduceTargetType']==0 and not api['control_getter_errors']
            value=api['maximumDeviation']['realValue'] if key=='input_before_add' else api['maximumDeviation']['value']
            assert value==deviation and api['maximumDeviation_activity']['getter_called'] is True
            assert all(v['getter_called'] is v['setter_called'] is False for v in api['inactive_controls'].values())
            method_checks+=1
        assert actual['feature_at_timeline_end']['healthState']==0 and actual['feature_at_timeline_end']['errorOrWarningMessage']==''
        parameters={p['role']:p for p in actual['model_parameters_after']}
        assert set(parameters)==set(settings['scalar_bindings'])=={'Tolerance','Proportion','Face Count'}
        for role,scalar in settings['scalar_bindings'].items():
            api=parameters[role]
            assert scalar['stored_value']==api['value'] and scalar['display_units']==api['unit'] and scalar['parameter_name']==api['name']
            assert scalar['is_active'] is (role=='Tolerance')
            assert not api['parameter_getter_errors'] and api['createdBy']['name']==row['name']
            parameter_checks+=1
        assert parameters['Tolerance']['unit']=='mm' and parameters['Tolerance']['expression']==('0.50 mm' if deviation==0.05 else '1.00 mm')
        mesh,=mesh_summary['decoded']
        assert not mesh_summary['unresolved'] and mesh['mesh_object_id']==settings['native_mesh_object_id']==213
        assert mesh['feature_object_id']==settings['current_mesh_native_feature_owner_object_id']==218
        assert mesh['asset_object_id']==settings['current_mesh_asset']['asset_object_id']==280
        assert settings['additional_stored_asset']['asset_object_id']==211 and settings['additional_asset_temporal_role'] is None
        current,=actual['component_meshes_after_reduce']['meshes']
        assert current['isClosed'] is True and current['baseOrFormFeature'] is None
        check_arrays(mesh['geometry'],current)
        assert math.isclose(mesh['geometry']['derived_absolute_volume_cm3'],current['volume'],rel_tol=1e-12,abs_tol=1e-12)
        additional=settings['additional_stored_asset']['geometry']
        rolled=actual['feature_before_node']['mesh']
        check_arrays(additional,rolled,mesh['asset_coordinates_to_component_matrix'])
        array_checks+=2
        layout=settings['layout']
        assert layout['exact_full_payload_replay'] is True and bytes.fromhex(layout['feature_body_hex'])==data[layout['feature_body_offset']:layout['feature_body_end_offset']]
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=decoded,
            expected_mesh_contents=mesh_summary,requested_method_enum=actual['requested']['method_enum'],actual_native_and_API_method_enum=method,
            requested_and_API_internal_maximum_deviation_cm=deviation,effective_algorithm=None,maximum_deviation_attainment=None,
            default_maximumDeviation_getter_failure=error,
            setter_history=[dict(property=e['property'],requested=e['requested'],assignment_completed=e['assignment_completed'],
                actual_method=e['actual_controls_after_assignment']['meshReduceMethodType'],actual_target=e['actual_controls_after_assignment']['meshReduceTargetType'],
                actual_control_getter_errors=e['actual_controls_after_assignment']['control_getter_errors']) for e in actual['setter_history']],
            actual_API_ModelParameters=[dict(role=p['role'],name=p['name'],value=p['value'],unit=p['unit'],expression=p['expression']) for p in parameters.values()],
            exact_current_and_additional_array_checks=True,exact_full_feature_payload_replay=True,owned_document_closed_true=True))
        contexts[actual['case']]=(data,records,features,member,members,decoded)
    data,records,features,member,members,decoded=contexts['adaptive_deviation_point_one']
    row,=decoded['decoded'];settings=row['settings'];fid=row['feature_object_id']
    by_id={r.object_id:r for r in records if r.is_primary};feature_record=by_id[fid]
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    def reject(label,changes,changed_features=None):
        damaged=bytearray(data)
        for offset,payload in changes:damaged[offset:offset+len(payload)]=payload
        answer=decode_mesh_reduce(bytes(damaged),records,features if changed_features is None else changed_features,member,members)
        assert not answer['decoded'] and not answer.get('partial') and len(answer['unresolved'])==1
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offsets=[o for o,_ in changes],rejected=True,reason=answer['unresolved'][0]['reason']))
    reject('unsupported target3',[(feature_record.body+29,struct.pack('<I',3))])
    tolerance=by_id[settings['scalar_bindings']['Tolerance']['binding_object_id']]
    reject('Tolerance binding owner differs',[(tolerance.body+5,ref(218))])
    reject('Tolerance binding disagrees with parameter and attached value',[(tolerance.body+21,struct.pack('<d',0.2))])
    # Set every numeric copy to0: rejects the active numeric domain, not just copy mismatch.
    parameters,_=decode_stream(data,records)
    parameter,=[p for p in parameters if p['role']=='Tolerance']
    changed=copy.deepcopy(features);feature,=[f for f in changed if f['object_id']==fid]
    active,=[p for p in feature['parameters'] if p['role']=='Tolerance'];active['raw_float64']=0.
    reject('zero active Tolerance rejected even with matching parameter/attached copies',[(tolerance.body+21,struct.pack('<d',0.)),(parameter['value_offset'],struct.pack('<d',0.))],changed)
    proxy=by_id[settings['input_selection']['proxy_object_id']]
    reject('mesh proxy owner differs',[(proxy.end-11,ref(218))])
    reject('current asset aliases additional',[(feature_record.body+44,ref(211))])
    reject('repeated dependency count4',[(feature_record.body+161,struct.pack('<I',4))])
    changed=copy.deepcopy(features);feature,=[f for f in changed if f['object_id']==fid]
    active,=[p for p in feature['parameters'] if p['role']=='Tolerance'];active['parameter_object_id']=218
    reject('attached Tolerance parameter identity differs',[],changed)
    def deny_current_geometry(d,rs,asset_id,n,m,**kwargs):
        if asset_id==280 and not kwargs.get('metadata_only',False):raise ValueError('Focused simulated unsupported current geometry')
        return decode_mesh_asset(d,rs,asset_id,n,m,**kwargs)
    fake=dict(decoded=[],unresolved=[dict(mesh_object_id=213,reason='Focused simulated unsupported current geometry')],scope='Focused guard')
    with patch('decode_mesh_reduce.decode_mesh_asset',side_effect=deny_current_geometry):partial=decode_mesh_reduce(data,records,features,member,members,fake)
    assert not partial['decoded'] and len(partial['partial'])==len(partial['unresolved'])==1
    p=partial['partial'][0]
    assert partial['unresolved'][0]['feature_object_id']==fid and partial['unresolved'][0]['reason']==p['partial_reason']
    assert p['settings']['maximum_deviation_cm']==0.1 and p['settings']['current_mesh_asset']['geometry'] is None
    assert p['settings']['current_mesh_asset']['asset_header']['fusion_uuid']==settings['current_mesh_asset']['asset_fusion_uuid']
    assert p['settings']['current_cache_node_count'] is p['settings']['current_cache_triangle_count'] is None
    assert p['settings']['geometry_unresolved'][0]['reason']=='Focused simulated unsupported current geometry'
    report['partial_geometry_guard']=dict(scope='Deliberately injected geometry failure, not an actual unsupported capture',
        controls_and_typed_header_preserved=True,no_decoded_tool_row=True,strict_reason_retained=True,expected_partial_summary=partial)
    old=json.loads((ROOT/'mesh-reduce-decoding.json').read_text())
    for saved in old['samples']:
        d,rs,fs,n,m=context(saved['archive'],zstd)
        mesh=decode_mesh_contents_variants(d,rs,n,m);summary=decode_mesh_reduce(d,rs,fs,n,m,mesh)
        assert summary==saved['expected_decoded'] and mesh==saved['expected_mesh_contents']
        report['legacy_controls'].append(dict(archive=saved['archive'],full_prior_Reduce_summary_exact=True,full_prior_mesh_contents_exact=True))
    report['summary']=dict(saved_archives=3,decoded_MaximumDeviation_features=3,active_API_method_and_target_readbacks=method_checks,
        owned_parameter_API_checks=parameter_checks,exact_current_and_additional_array_checks=array_checks,
        full_feature_payload_replays=3,retained_actual_default_getter_errors=default_errors,
        malformed_guards=len(report['malformed_guards']),explicit_partial_geometry_guard=1,
        exact_prior_Reduce_summaries=len(report['legacy_controls']),common_parser_changes=0,main_runs=0,live_calls=0)
    report['runtime_source_sha256']={f:digest(ROOT/f) for f in ('decode_mesh_reduce.py','validate_mesh_reduce_deviation.py',
        'decode_mesh_contents.py','decode_mesh_geometry_variants.py','decode_parameters.py','decode_mesh_selections.py')}
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default=str(ROOT/'mesh-reduce-deviation-decoding.json'))
    args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd)
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':main()
