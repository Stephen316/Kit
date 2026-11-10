"""Bounded active Rebuild controls; exact old outputs and honest geometry partials."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
from unittest.mock import patch

from validate_mesh_repair import context
from decode_placement import transform_point
from decode_mesh_geometry_variants import decode_mesh_contents_variants,decode_mesh_asset
from decode_mesh_repair import REPAIR,decode_mesh_repair

ROOT=Path(__file__).resolve().parent
DIRECTORY='meshrepairrebuilds-66d4316c2e8d'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_arrays(geometry,actual,matrix=None):
    points=geometry.get('component_node_coordinates_cm')
    if points is None:points=[transform_point(matrix,p) for p in geometry['stored_node_coordinates_float32']]
    assert [v for p in points for v in p]==actual['original_polygon_mesh']['nodeCoordinatesAsDouble']
    assert geometry['triangle_node_indices']==actual['original_polygon_mesh']['triangleNodeIndices']
    assert len(points)==actual['original_polygon_mesh']['nodeCount']
    assert len(geometry['triangle_node_indices'])//3==actual['original_polygon_mesh']['triangleCount']


def validate(zstd):
    truth_path=ROOT/DIRECTORY/'ground_truth.json'
    truth=json.loads(truth_path.read_text())
    assert truth['terminal_status']=='complete' and not truth['errors'] and len(truth['samples'])==3
    assert digest(ROOT/DIRECTORY/'executed-generator-source.txt')==truth['executed_generator_sha256']
    assert digest(ROOT/DIRECTORY/truth['helper_snapshot'])==truth['mesh_source_helper_sha256']
    assert digest(ROOT/DIRECTORY/truth['sdk_surface_snapshot'])==truth['sdk_surface_snapshot_sha256']
    report=dict(scope='Three actual owned Rebuild tetra captures: Fast density8, Accurate density8 Offset0, Accurate density8 Offset0.05cm. Native enum/binding proof plus typed current/additional caches, not a repair algorithm.',
        interface='decode_mesh_repair(data,records,features,member,members,mesh_contents=None); old summary unchanged; Rebuild summary adds partial[] and conditional scope, with controls kept partial if current geometry fails.',
        integration=dict(stream='mesh_repairs',counter='class_decoded_mesh_repair_count',
            decode_level='Observed MeshRepair method and owned control/mesh/asset routes; additional methods, lifecycle and regeneration unresolved',
            compatibility='Three prior CloseHoles/StitchAndRemove full summary dictionaries and common mesh summaries remain exactly equal to historical report. Partial rows carry settings evidence but must not become decoded tool settings.'),
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(truth_path),
            executed_generator_sha256=truth['executed_generator_sha256'],mesh_source_helper_sha256=truth['mesh_source_helper_sha256'],
            sdk_runtime_source_sha256=truth['sdk_runtime_source_sha256'],sdk_surface_snapshot_sha256=truth['sdk_surface_snapshot_sha256']),
        native_schema=dict(class_guid=REPAIR,method_uint32_offset=28,observed_method_code=3,
            active_subtype_uint32_offset=24,observed_rebuild_subtypes={'0':'Fast','2':'Accurate'},
            Density_binding_ref_offset=2,Offset_binding_ref_offset=13,active_Density=8,
            observed_active_Accurate_Offset_internal_cm=[0.,0.05],Fast_Offset='Stored0 inactive; getter/setter not invoked',
            active_scalar_proof='Native binding, typed owner/parameter references, parsed role/numeric copies, attached feature parameter and actual input/feature/ModelParameter getters agree.',
            shared_feature_schema='Existing explicit source proxy58/current asset32/additional asset43/nil UUID70/ordered4dependencies153/footer66 unchanged'),
        samples=[],malformed_guards=[],legacy_controls=[],partial_geometry_guard=None,
        limitations=['Only Rebuild method3/Fast0/Accurate2 with Density8 and Accurate Offset0/0.05cm captured. Other enum/density/offset settings remain unsupported.',
            'Old method0/1 subtype word0 remains uninterpreted/inactive; recognizing Fast0 in active Rebuild does not rename invariant old bytes.',
            'Offset float64/native/API internal value0.05cm displays expression0.50mm with unit mm. No multiplication of stored internal values by display units.',
            'Fast Offset has a serialized ModelParameter0 but its mode-specific getter/setter was not invoked and active_offset_cm remains None.',
            'Current cache is independently qualified via selected native mesh/BaseMesh/collection and same-asset UUID route. Additional asset matches rolled source arrays only after typed reference resolution; temporal/source lifecycle role stays None.',
            'Healthy actual feature and closed result cache do not prove exact repair/rebuild algorithms, target fidelity, universal topology or persistent body/face identity.',
            'Geometry failure produces explicit partial control/metadata evidence with original strict reason and geometry None; it does not become a full decoded tool row.',
            'Independent geometry/normals/group evidence is reported separately in mesh-rebuild-geometry-decoding.json; no coordinate/name/order association chooses native identities.'])
    contexts={};api_checks=scalar_checks=array_checks=0
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
        assert features==before and not decoded['unresolved'] and decoded.get('partial')==[]
        row,=decoded['decoded'];settings=row['settings']
        subtype=0 if actual['case']=='fast_density_eight' else 2
        offset=0.05 if actual['case'].endswith('point_zero_five') else 0.
        assert settings['method']=='Rebuild' and settings['stored_method_code']==3
        assert settings['mesh_repair_rebuild_type']==('Fast' if subtype==0 else 'Accurate') and settings['stored_rebuild_type_code']==subtype
        assert 'stored_uninterpreted_uint32_at_24' not in settings
        assert settings['active_density']==8 and settings['active_offset_cm']==(offset if subtype==2 else None)
        assert settings['mesh_repair_owns_current_mesh'] is None and not settings['geometry_unresolved']
        assert settings['additional_asset_temporal_role'] is None
        assert actual['input_defaults']['meshRepairType']==1 and actual['input_defaults']['meshRepairRebuildType'] is None
        for key in ('input_before_add','feature_before_node','feature_at_timeline_end'):
            api=actual[key]
            assert api['meshRepairType']==3 and api['meshRepairRebuildType']==subtype and not api['control_getter_errors']
            value=api['density']['realValue'] if key=='input_before_add' else api['density']['value']
            assert value==8.
            if subtype==2:
                value=api['offset']['realValue'] if key=='input_before_add' else api['offset']['value']
                assert value==offset
            else:
                assert api['offset'] is None
                assert api['control_activity']['offset']['status']=='NotApplicableOrUnresolved' and api['control_activity']['offset']['getter_called'] is False
            api_checks+=1
        assert actual['feature_at_timeline_end']['healthState']==0 and actual['feature_at_timeline_end']['errorOrWarningMessage']==''
        parameters={p['role']:p for p in actual['model_parameters_after']}
        for role,scalar in settings['scalar_bindings'].items():
            api=parameters[role]
            assert scalar['stored_value']==api['value'] and scalar['display_units']==api['unit'] and scalar['parameter_name']==api['name']
            assert scalar['is_active'] is (role=='Density' or subtype==2)
            assert scalar['applicability']==('Applicable' if scalar['is_active'] else 'NotApplicable')
            assert not api['parameter_getter_errors'] and api['createdBy']['name']==row['name']
            scalar_checks+=1
        if offset:
            assert parameters['Offset']['unit']=='mm' and parameters['Offset']['value']==0.05 and parameters['Offset']['expression']=='0.50 mm'
        mesh,=meshes['decoded']
        assert not meshes['unresolved'] and mesh['mesh_object_id']==settings['native_mesh_object_id']==213
        assert mesh['feature_object_id']==settings['current_mesh_native_feature_owner_object_id']==218
        assert mesh['asset_object_id']==settings['current_mesh_asset']['asset_object_id']==377
        assert settings['additional_stored_asset']['asset_object_id']==211
        current,=actual['component_meshes_after_repair']['meshes']
        assert current['isClosed'] is True and current['baseOrFormFeature'] is None
        check_arrays(mesh['geometry'],current)
        assert math.isclose(mesh['geometry']['derived_absolute_volume_cm3'],current['volume'],rel_tol=1e-12,abs_tol=1e-12)
        rolled=actual['feature_before_node']['mesh_body']
        additional=settings['additional_stored_asset']['geometry']
        check_arrays(additional,rolled,mesh['asset_coordinates_to_component_matrix'])
        assert rolled['original_polygon_mesh']['nodeCount']==rolled['original_polygon_mesh']['triangleCount']==4
        array_checks+=2
        actual_counts=(current['original_polygon_mesh']['nodeCount'],current['original_polygon_mesh']['triangleCount'])
        assert actual_counts==((11,18) if subtype==0 else (12,20) if offset else (9,14))
        assert actual_counts==(settings['current_cache_node_count'],settings['current_cache_triangle_count'])
        layout=settings['layout']
        assert layout['exact_full_payload_replay'] is True and bytes.fromhex(layout['feature_body_hex'])==data[layout['feature_body_offset']:layout['feature_body_end_offset']]
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=decoded,
            expected_mesh_contents=meshes,actual_API_method_code=3,actual_API_rebuild_subtype_code=subtype,
            actual_API_density=8.,actual_API_active_Offset_internal_cm=offset if subtype==2 else None,
            actual_API_Fast_Offset_property_getter_called=False if subtype==0 else None,
            actual_current_cache_counts=dict(nodes=actual_counts[0],triangles=actual_counts[1]),
            actual_API_volume_cm3=current['volume'],exact_current_and_additional_array_checks=True,
            exact_full_feature_payload_replay=True,owned_document_closed_true=True,
            actual_API_ModelParameters=[dict(role=p['role'],name=p['name'],value=p['value'],unit=p['unit'],expression=p['expression']) for p in parameters.values()]))
        contexts[actual['case']]=(data,records,features,member,members,decoded)
    data,records,features,member,members,decoded=contexts['accurate_density_eight_offset_point_zero_five']
    row,=decoded['decoded'];settings=row['settings'];fid=row['feature_object_id']
    by_id={r.object_id:r for r in records if r.is_primary};feature_record=by_id[fid]
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    def reject(label,offset,payload):
        damaged=bytearray(data);damaged[offset:offset+len(payload)]=payload
        answer=decode_mesh_repair(bytes(damaged),records,features,member,members)
        assert not answer['decoded'] and not answer.get('partial') and len(answer['unresolved'])==1
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offset=offset,rejected=True,reason=answer['unresolved'][0]['reason']))
    reject('unobserved Rebuild subtype1',feature_record.body+24,struct.pack('<I',1))
    reject('unsupported Wrap method2',feature_record.body+28,struct.pack('<I',2))
    density=by_id[settings['scalar_bindings']['Density']['binding_object_id']]
    reject('Density binding numeric copy disagrees with typed parameter',density.body+22,struct.pack('<I',9))
    offset=by_id[settings['scalar_bindings']['Offset']['binding_object_id']]
    reject('nonfinite Offset binding',offset.body+21,struct.pack('<d',float('nan')))
    reject('current asset aliases additional',feature_record.body+32,ref(211))
    proxy=by_id[settings['input_selection']['proxy_object_id']]
    reject('input proxy owned by BaseMesh instead of Repair',proxy.end-11,ref(218))
    reject('repeated table count3',feature_record.body+149,struct.pack('<I',3))
    altered=copy.deepcopy(features)
    target,=[f for f in altered if f['object_id']==fid]
    scalar,=[p for p in target['parameters'] if p['role']=='Density'];scalar['parameter_object_id']=218
    answer=decode_mesh_repair(data,records,altered,member,members)
    assert not answer['decoded'] and not answer.get('partial') and len(answer['unresolved'])==1
    report['malformed_guards'].append(dict(guard='attached Density parameter object differs',rejected=True,reason=answer['unresolved'][0]['reason']))
    # Explicit partial test denies current geometry while preserving genuine native metadata/header routes.
    def deny_current_geometry(d,rs,asset_id,n,m,**kwargs):
        if asset_id==377 and not kwargs.get('metadata_only',False):raise ValueError('Focused simulated unsupported current geometry')
        return decode_mesh_asset(d,rs,asset_id,n,m,**kwargs)
    fake_summary=dict(decoded=[],unresolved=[dict(mesh_object_id=213,reason='Focused simulated unsupported current geometry')],scope='Focused guard')
    with patch('decode_mesh_repair.decode_mesh_asset',side_effect=deny_current_geometry):
        partial=decode_mesh_repair(data,records,features,member,members,fake_summary)
    assert not partial['decoded'] and len(partial['unresolved'])==len(partial['partial'])==1
    assert partial['unresolved'][0]['feature_object_id']==fid and partial['unresolved'][0]['reason']==partial['partial'][0]['partial_reason']
    p=partial['partial'][0]['settings']
    assert p['method']=='Rebuild' and p['active_density']==8 and p['active_offset_cm']==0.05
    assert p['current_mesh_asset']['geometry'] is None and p['current_mesh_asset']['asset_header']['fusion_uuid']==settings['current_mesh_asset']['asset_fusion_uuid']
    assert p['current_cache_node_count'] is p['current_cache_triangle_count'] is None
    assert p['geometry_unresolved'][0]['reason']=='Focused simulated unsupported current geometry'
    report['partial_geometry_guard']=dict(scope='Deliberately injected geometry rejection; actual three captures have independently supported complete stored caches',
        controls_and_typed_metadata_preserved=True,no_decoded_tool_row=True,geometry_None=True,strict_reason_retained=True,
        expected_partial_summary=partial)
    old=json.loads((ROOT/'mesh-repair-decoding.json').read_text())
    for saved in old['samples']:
        d,rs,fs,n,m=context(saved['archive'],zstd)
        mesh=decode_mesh_contents_variants(d,rs,n,m)
        answer=decode_mesh_repair(d,rs,fs,n,m,mesh)
        assert answer==saved['expected_decoded'] and mesh==saved['expected_mesh_contents']
        report['legacy_controls'].append(dict(archive=saved['archive'],full_prior_Repair_summary_exact=True,full_prior_current_mesh_summary_exact=True))
    report['summary']=dict(saved_archives=3,decoded_Rebuild_features=3,active_API_control_readbacks=api_checks,
        owned_parameter_API_checks=scalar_checks,exact_current_and_additional_array_checks=array_checks,
        full_feature_payload_replays=3,malformed_guards=len(report['malformed_guards']),explicit_partial_geometry_guard=1,
        exact_prior_Repair_summaries=len(report['legacy_controls']),main_runs=0,live_calls=0)
    report['runtime_source_sha256']={f:digest(ROOT/f) for f in ('decode_mesh_repair.py','validate_mesh_repair_rebuild.py',
        'decode_mesh_contents.py','decode_mesh_geometry_variants.py','decode_parameters.py','decode_mesh_selections.py')}
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default=str(ROOT/'mesh-repair-rebuild-decoding.json'))
    args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd)
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':main()
