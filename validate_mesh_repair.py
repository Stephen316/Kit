"""Three owned MeshRepair definitions; inactive bindings and explicit asset checks."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_basics import attach_parameters
from discover_features import discover_features
from fusion_archive import read_members
from fusion_metadata import design_records
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_repair import REPAIR, decode_mesh_repair
from decode_parameters import decode_stream
from decode_placement import transform_point

ROOT=Path(__file__).resolve().parent
DIRECTORY='meshrepairs-2387e4f9c2d2'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def context(filename,zstd):
    members=read_members(ROOT/filename,zstd)
    member,=[n for n in members if n.endswith('/FusionDesignSegmentType1/BulkStream.dat')]
    data=members[member]
    records,registry=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
    features=[]
    discover_features(data,records,features,registry)
    parameters,_=decode_stream(data,records)
    attach_parameters(data,records,features,parameters)
    return data,records,features,member,members


def check_arrays(geometry,actual,matrix=None):
    points=geometry.get('component_node_coordinates_cm')
    if points is None:points=[transform_point(matrix,p) for p in geometry['stored_node_coordinates_float32']]
    assert [v for p in points for v in p]==actual['original_polygon_mesh']['nodeCoordinatesAsDouble']
    assert geometry['triangle_node_indices']==actual['original_polygon_mesh']['triangleNodeIndices']
    assert len(points)==actual['original_polygon_mesh']['nodeCount']==4
    assert len(geometry['triangle_node_indices'])//3==actual['original_polygon_mesh']['triangleCount']


def validate(zstd):
    truth_path=ROOT/DIRECTORY/'ground_truth.json'
    truth=json.loads(truth_path.read_text())
    assert truth['terminal_status']=='complete' and not truth['errors'] and len(truth['samples'])==3
    assert digest(ROOT/DIRECTORY/'executed-generator-source.txt')==truth['executed_generator_sha256']
    assert digest(ROOT/DIRECTORY/truth['helper_snapshot'])==truth['mesh_source_helper_sha256']
    assert digest(ROOT/DIRECTORY/truth['sdk_surface_snapshot'])==truth['sdk_surface_snapshot_sha256']
    report=dict(scope='Three actual CloseHoles/StitchAndRemove root tetra captures; native method, owned inactive Density/Offset parameters, explicit current/additional asset routes and strict common caches only. No repair/rebuild algorithm reconstructed.',
        interface='decode_mesh_repair(data,records,features,member,members,mesh_contents=None)->decoded/unresolved/scope; rows feature_object_id/kindMeshRepair/name/settings',
        integration=dict(stream='mesh_repairs',counter='class_decoded_mesh_repair_count',
            decode_level='Observed MeshRepair method and owned control/mesh/asset routes; additional methods, lifecycle and regeneration unresolved',
            compatibility='No common parser/geometry changes or old diagnostic removal needed. BaseMesh owner remains distinct from Repair input/current role.'),
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(truth_path),
            executed_generator_sha256=truth['executed_generator_sha256'],mesh_source_helper_sha256=truth['mesh_source_helper_sha256'],
            sdk_runtime_source_sha256=truth['sdk_runtime_source_sha256'],sdk_surface_snapshot_sha256=truth['sdk_surface_snapshot_sha256']),
        native_schema=dict(primary_class_guid=REPAIR,Density_binding_reference_offset=2,Offset_binding_reference_offset=13,
            uninterpreted_uint32_offset=24,method_uint32_offset=28,contrasted_methods={'0':'CloseHoles','1':'StitchAndRemove'},
            current_asset_reference_offset=32,additional_asset_reference_offset=43,owned_mesh_proxy_reference_offset=58,
            nil_uuid_offset=70,repeated_dependency_count_offset=149,repeated_dependency_reference_offset=153,
            repeated_order=['source proxy','source descriptor','Density binding','Offset binding'],label_offset=201,
            binding_proof='Typed integer/float binding, three agreeing feature-owner references, typed parameter record, native role/value/binding references and already attached feature parameter all agree.',
            inactive_control_distinction='Stored Density128/Offset0 ModelParameters exist and actual ModelParameter getters corroborate them. SDK Rebuild-only property getters/setters were never called; inactive controls are not active repair settings.'),
        samples=[],malformed_guards=[],legacy_controls=[],
        limitations=['Only CloseHoles0/StitchAndRemove1 methods captured. Wrap/Rebuild/OneTouch and active Rebuild controls remain unsupported.',
            'Native uint32@24 is invariant zero. It is not named a Rebuild enum or boolean from invariance; mesh_repair_rebuild_type remains None.',
            'Current asset is bound independently through selected native Mesh/BaseMesh/collection and asset UUID/same-asset filename. Additional asset is explicit, but matching rolled arrays does not assign universal source/history/lifecycle meaning.',
            'Open inputs yield closed current four-triangle caches in these captures. No algorithm, general repair success, face correspondence, persistent topology or arbitrary history replay inferred.',
            'Actual API baseOrFormFeature None is separate from reciprocal native BaseMesh membership; Repair is not promoted to native mesh owner.',
            'MeshBody.area differs from area derived after native matrix scaling; exact coordinate/index arrays and closed volumes corroborate caches but do not establish area scalar encoding.',
            'Geometry/normal holdout validation is independently reported by the other agent; this report retains exact common current summaries rather than broadening any common parser.'])
    contexts={};binding_checks=method_checks=array_checks=0
    for actual in truth['samples']:
        filename=DIRECTORY+'/'+actual['file']
        assert actual['repair_status']=='FeatureReturned' and not actual['getter_errors'] and not actual['setter_errors']
        assert actual['actual_imported_mesh_count']==1 and actual['close_owned_document_returned'] is True
        assert actual['roll_before_feature_returned'] is True and actual['input_mesh_equals_import_handle'] is True and actual['rolled_mesh_equals_import_handle'] is True
        assert actual['export']['sha256']==digest(ROOT/filename) and actual['export']['size_bytes']==(ROOT/filename).stat().st_size
        data,records,features,member,members=context(filename,zstd)
        before=copy.deepcopy(features)
        meshes=decode_mesh_contents_variants(data,records,member,members)
        decoded=decode_mesh_repair(data,records,features,member,members,meshes)
        assert features==before and not decoded['unresolved']
        row,=decoded['decoded'];settings=row['settings']
        assert row['kind']=='MeshRepair' and settings['native_mesh_object_id']==213
        code=1 if actual['case']=='open_stitch_remove' else 0
        assert settings['stored_method_code']==code and settings['method']==('StitchAndRemove' if code else 'CloseHoles')
        assert settings['mesh_repair_rebuild_type'] is settings['mesh_repair_owns_current_mesh'] is None
        for key in ('input_defaults','input_before_add','feature_before_node','feature_at_timeline_end'):
            api=actual[key]
            assert api['meshRepairType']==(1 if key=='input_defaults' else code)
            assert not api['control_getter_errors']
            assert set(api['inactive_rebuild_controls'])=={'meshRepairRebuildType','density','offset'}
            assert all(p['status']=='NotApplicable' and p['getter_called'] is False and p['setter_called'] is False for p in api['inactive_rebuild_controls'].values())
            method_checks+=1
        assert actual['feature_at_timeline_end']['healthState']==0 and actual['feature_at_timeline_end']['errorOrWarningMessage']==''
        parameters={p['role']:p for p in actual['model_parameters_after']}
        assert set(parameters)==set(settings['scalar_bindings'])=={'Density','Offset'}
        for role,scalar in settings['scalar_bindings'].items():
            api=parameters[role]
            assert scalar['stored_value']==api['value'] and scalar['display_units']==api['unit'] and scalar['parameter_name']==api['name']
            assert scalar['is_active'] is False and scalar['applicability']=='NotApplicable'
            assert api['createdBy']['name']==row['name'] and not api['parameter_getter_errors']
            binding_checks+=1
        mesh,=meshes['decoded']
        assert not meshes['unresolved'] and mesh['mesh_object_id']==settings['input_selection']['mesh_object_id']
        assert mesh['feature_object_id']==settings['current_mesh_native_feature_owner_object_id']==218
        assert settings['current_mesh_native_owner_class_guid']=='99F6967E-ED35-4222-B906-5CCF0AC70B53'
        assert mesh['asset_object_id']==settings['current_mesh_asset']['asset_object_id']==373
        assert settings['additional_stored_asset']['asset_object_id']==211 and settings['additional_asset_temporal_role'] is None
        current,=actual['component_meshes_after_repair']['meshes']
        assert current['baseOrFormFeature'] is None and current['isClosed'] is True
        assert mesh['name']==current['name']==actual['feature_before_node']['mesh_body']['name']
        check_arrays(mesh['geometry'],current)
        assert math.isclose(mesh['geometry']['derived_absolute_volume_cm3'],current['volume'],rel_tol=1e-12,abs_tol=1e-12)
        additional=settings['additional_stored_asset']['geometry']
        rolled=actual['feature_before_node']['mesh_body']
        check_arrays(additional,rolled,mesh['asset_coordinates_to_component_matrix'])
        array_checks+=2
        assert rolled['isClosed'] is (actual['case']=='closed_close_holes_control')
        assert additional['triangle_count']==(4 if actual['case']=='closed_close_holes_control' else 3)
        assert settings['current_cache_node_count']==settings['current_cache_triangle_count']==4
        layout=settings['layout']
        assert layout['exact_full_payload_replay'] is True and bytes.fromhex(layout['feature_body_hex'])==data[layout['feature_body_offset']:layout['feature_body_end_offset']]
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=decoded,
            expected_mesh_contents=meshes,actual_API_default_method_code=1,actual_API_configured_method_code=code,
            actual_API_current_closed=current['isClosed'],actual_API_current_triangle_count=current['original_polygon_mesh']['triangleCount'],
            actual_API_rolled_closed=rolled['isClosed'],actual_API_rolled_triangle_count=rolled['original_polygon_mesh']['triangleCount'],
            exact_current_and_additional_arrays_correspond_to_captured_getters=True,
            additional_array_scope='Explicit typed additional asset was resolved first. Matrix-transformed array equality corroborates rolled input, without choosing native identity by coordinates or assigning universal temporal role.',
            actual_API_ModelParameters=[dict(role=p['role'],name=p['name'],value=p['value'],unit=p['unit'],created_by_name=p['createdBy']['name']) for p in parameters.values()],
            inactive_Rebuild_properties_getter_and_setter_called=False,exact_full_feature_payload_replay=True,owned_document_closed_true=True,
            area_scalar_counterexample=dict(actual_API_MeshBody_area=current['area'],derived_scaled_cache_area=mesh['geometry']['derived_area_cm2'])))
        contexts[actual['case']]=(data,records,features,member,members,decoded)
    data,records,features,member,members,decoded=contexts['open_close_holes']
    row,=decoded['decoded'];settings=row['settings'];fid=row['feature_object_id']
    by_id={r.object_id:r for r in records if r.is_primary};feature_record=by_id[fid]
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    def reject(label,offset,payload):
        damaged=bytearray(data);damaged[offset:offset+len(payload)]=payload
        answer=decode_mesh_repair(bytes(damaged),records,features,member,members)
        assert not answer['decoded'] and len(answer['unresolved'])==1 and answer['unresolved'][0]['class_guid']==REPAIR
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offset=offset,rejected=True,reason=answer['unresolved'][0]['reason']))
    reject('unsupported Wrap method2',feature_record.body+28,struct.pack('<I',2))
    reject('uncontrasted opaque control word',feature_record.body+24,struct.pack('<I',1))
    binding=by_id[settings['scalar_bindings']['Density']['binding_object_id']]
    reject('Density binding feature owner differs',binding.body+5,ref(218))
    reject('Density binding differs from parameter and attached numeric copy',binding.body+22,struct.pack('<I',129))
    reject('current asset aliases additional instead of native current pointer',feature_record.body+32,ref(211))
    proxy=by_id[settings['input_selection']['proxy_object_id']]
    reject('source proxy belongs to different feature',proxy.end-11,ref(218))
    reject('dependency table count5',feature_record.body+149,struct.pack('<I',5))
    attached=copy.deepcopy(features)
    target,=[f for f in attached if f['object_id']==fid]
    density,=[p for p in target['parameters'] if p['role']=='Density']
    density['raw_float64']=129.
    answer=decode_mesh_repair(data,records,attached,member,members)
    assert not answer['decoded'] and len(answer['unresolved'])==1
    report['malformed_guards'].append(dict(guard='attached feature Density value differs despite unchanged native bytes',rejected=True,reason=answer['unresolved'][0]['reason']))
    prior=json.loads((ROOT/'mesh-remove-decoding.json').read_text())
    for saved in prior['samples']:
        if not saved['archive'].endswith(('/one_remove_one.f3d','/two_remove_first.f3d')):continue
        d,rs,fs,n,m=context(saved['archive'],zstd)
        old=decode_mesh_contents_variants(d,rs,n,m)
        assert old==saved['expected_mesh_contents']
        empty=decode_mesh_repair(d,rs,fs,n,m,old)
        assert not empty['decoded'] and not empty['unresolved']
        report['legacy_controls'].append(dict(archive=saved['archive'],existing_mesh_contents_exact=True,new_helper_no_candidates=True))
    report['summary']=dict(saved_archives=3,decoded_features=3,actual_method_readbacks=method_checks,
        owned_inactive_parameter_API_checks=binding_checks,exact_current_and_additional_array_checks=array_checks,
        full_feature_payload_replays=3,malformed_guards=len(report['malformed_guards']),
        exact_legacy_controls=len(report['legacy_controls']),common_parser_changes=0,main_runs=0,live_calls=0)
    report['runtime_source_sha256']={f:digest(ROOT/f) for f in ('decode_mesh_repair.py','validate_mesh_repair.py',
        'decode_mesh_contents.py','decode_mesh_geometry_variants.py','decode_parameters.py','decode_mesh_selections.py')}
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default=str(ROOT/'mesh-repair-decoding.json'))
    args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd)
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':main()
