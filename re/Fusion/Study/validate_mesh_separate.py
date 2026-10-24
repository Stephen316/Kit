"""Three actual MeshSeparate definitions, typed sources/results and cache controls."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
from unittest.mock import patch

from decode_basics import named_features
from discover_features import discover_features
from fusion_archive import read_members
from fusion_metadata import design_records
from decode_mesh_contents import MESH
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_separate import SEPARATE, decode_mesh_separate, decode_mesh_separate_definition

ROOT = Path(__file__).resolve().parent
DIRECTORY = 'meshseparates-41126250c03f'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def context(filename, zstd):
    members = read_members(ROOT/filename, zstd)
    member, = [n for n in members if n.endswith('/FusionDesignSegmentType1/BulkStream.dat')]
    data = members[member]
    records, registry = design_records(data, members[member.replace('BulkStream.dat','MetaStream.dat')])
    features = named_features(data,records)
    discover_features(data,records,features,registry)
    return data,records,features,member,members


def exact_arrays(geometry, actual):
    points = geometry['component_node_coordinates_cm']
    assert [v for p in points for v in p] == actual['original_polygon_mesh']['nodeCoordinatesAsDouble']
    assert geometry['triangle_node_indices'] == actual['original_polygon_mesh']['triangleNodeIndices']
    assert geometry['node_count'] == actual['original_polygon_mesh']['nodeCount']
    assert geometry['triangle_count'] == actual['original_polygon_mesh']['triangleCount']
    assert math.isclose(geometry['derived_absolute_volume_cm3'],actual['volume'],rel_tol=1e-12,abs_tol=1e-12)


def validate(zstd):
    truth_path = ROOT/DIRECTORY/'ground_truth.json'
    truth = json.loads(truth_path.read_text())
    assert truth['terminal_status']=='complete' and not truth['errors'] and len(truth['samples'])==3
    assert digest(ROOT/DIRECTORY/'executed-generator-source.txt')==truth['executed_generator_sha256']
    assert digest(ROOT/DIRECTORY/truth['sdk_surface_snapshot'])==truth['sdk_surface_snapshot_sha256']
    report = dict(scope='Three owned MeshBody Separate captures: Shell splitting two disconnected tetrahedra, FaceGroup mode on one actual group containing both shells, and a connected Shell control. Literal controls, typed sources/results and actual cache arrays only.',
        interface='decode_mesh_separate(data,records,features,member,members,mesh_contents=None)->decoded/unresolved/scope; rows feature_object_id/kind/name/settings',
        pure_definition_interface='decode_mesh_separate_definition(data,records,feature_id)->feature_object_id/output_mesh_object_ids/source_selection/method and strict typed ownership/framing; never calls geometry/current mesh decoders',
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(truth_path),
            executed_generator_sha256=truth['executed_generator_sha256'],sdk_runtime_source_sha256=truth['sdk_runtime_source_sha256'],
            sdk_surface_snapshot_sha256=truth['sdk_surface_snapshot_sha256']),
        native_schema=dict(primary_class_guid=SEPARATE,result_count_uint32_offset=2,result_list_ref_offset=6,
            result_ref_stride=11,list_end='6+11*count',method_uint32_offset='list_end+2',
            method_codes={'0':'Shell','1':'FaceGroup'},source_proxy_reference_offset='list_end+12',
            nil_uuid_offset='list_end+24',repeated_dependency_order=['source proxy','source descriptor'],
            invariant_control_scope='isKeepBody=False only; raw zero2 and zero6 are not assigned flag semantics. isMultipleBodies not queried or encoded by inference.',
            result_proof='Feature direct result refs, typed native MESH backlinks@489, shared collection backlink, exact ordered counted members and typed component',
            source_proof='Owned typed mesh proxy/descriptor/leaf, source excluded from current members, retained owner collection equals results, reciprocal BaseMeshFeature membership'),
        samples=[],malformed_guards=[],legacy_controls=[],
        limitations=['No Separate algorithm, arbitrary face-group collection input, keepBody=True, inactive isMultipleBodies or native partition IDs decoded.',
            'Connected control returns a distinct result native mesh despite unchanged tetra arrays. This does not establish general no-op handling or persistent source/result identity.',
            'One actual FaceGroup contains both disconnected tetra shells; FaceGroup method therefore yields one output. Group IDs and internal partition meaning remain separate from Shell mode.',
            'Full source cache arrays are compared after typed native identity/owner/asset joins. Native result names are empty despite API MeshBody2/MeshBody3 defaults. Entire output array multisets corroborate the already identified native result group; no individual API handle/name-to-native-result mapping is claimed or chosen by geometry/order.',
            'Native source retained owner and BaseMesh backlink do not mean source is a current counted member, API BaseFeature owner, hidden/deleted state or general lifecycle.',
            'API area scalars differ from area derived after the explicit native scale matrix; exact geometry arrays and volume agree, but area scalar encoding/convention is not claimed.',
            'Known one-zero index suffix is retained as separate bounded framing evidence; its semantic meaning and auxiliary-stream semantics remain unresolved.'])
    contexts={}
    output_checks=source_checks=control_checks=0
    for actual in truth['samples']:
        filename=DIRECTORY+'/'+actual['file']
        assert actual['separate_status']=='FeatureReturned' and actual['actual_imported_mesh_count']==1
        assert not actual['getter_errors'] and not actual['setter_errors'] and actual['close_owned_document_returned'] is True
        assert actual['roll_before_feature_returned'] is True and actual['input_mesh_equals_import_handle'] is True
        assert actual['rolled_mesh_equals_import_handle'] is True and actual['model_parameters_after']==[]
        assert actual['export']['size_bytes']==(ROOT/filename).stat().st_size and actual['export']['sha256']==digest(ROOT/filename)
        data,records,features,member,members=context(filename,zstd)
        before=copy.deepcopy(features)
        strict=decode_mesh_contents_variants(data,records,member,members)
        summary=decode_mesh_separate(data,records,features,member,members,strict)
        assert features==before and not summary['unresolved']
        row,=summary['decoded'];settings=row['settings']
        fid=row['feature_object_id']
        with patch('decode_mesh_separate.decode_mesh_contents',side_effect=AssertionError('Pure definition must not decode current meshes')),patch('decode_mesh_separate.decode_mesh_asset',side_effect=AssertionError('Pure definition must not decode geometry')):
            definition=decode_mesh_separate_definition(data,records,fid)
        contexts[actual['case']] = (data,records,features,member,members,definition)
        code=1 if actual['case']=='two_face_groups' else 0
        assert settings['stored_method_code']==code and settings['method']==('FaceGroup' if code else 'Shell')
        for key in ('input_defaults','input_before_add','feature_before_node','feature_at_timeline_end'):
            a=actual[key]
            assert a['meshSeparateType']==(0 if key=='input_defaults' else code) and a['isKeepBody'] is False
            assert a['isMultipleBodies']['getter_called'] is False
            control_checks+=1
        assert settings['is_keep_body'] is settings['is_multiple_bodies'] is None
        assert actual['feature_at_timeline_end']['healthState']==0 and actual['feature_at_timeline_end']['errorOrWarningMessage']==''
        assert not settings['geometry_unresolved']
        source=settings['retained_source']
        assert source['mesh_object_id']==definition['source_selection']['mesh_object_id']==213
        assert source['retained_membership_status']=='NotInCountedMembers'
        assert source['retained_owner_collection_member_ids']==settings['result_mesh_object_ids']==definition['output_mesh_object_ids']
        assert source['name']==actual['feature_before_node']['mesh_body']['name']==actual['source_before_separate']['name']
        assert source['base_mesh_feature_object_id']==218
        assert actual['source_before_separate']['baseOrFormFeature'] is None
        sourcegeometry=source.get('geometry') or source.get('asset_geometry',{}).get('geometry')
        exact_arrays(sourcegeometry,actual['feature_before_node']['mesh_body'])
        source_checks+=1
        actual_outputs=actual['component_meshes_after_separate']['meshes']
        assert len(actual_outputs)==settings['current_result_count']==len(settings['result_mesh_object_ids'])
        assert len(actual_outputs)==(2 if actual['case']=='two_shells' else 1)
        for output in settings['current_result_meshes']:
            metadata=output['metadata'];geometry=output['qualified_geometry']
            assert metadata['mesh_object_id'] in settings['result_mesh_object_ids'] and metadata['feature_object_id']==fid
            assert metadata['native_feature_class_guid']==SEPARATE and metadata['name']==''
            assert metadata['collection_mesh_object_ids']==settings['result_mesh_object_ids']
            assert geometry is not None
            output_checks+=1
        def native_arrays(o):
            g=o['qualified_geometry']
            return json.dumps([[v for p in g['component_node_coordinates_cm'] for v in p],g['triangle_node_indices']])
        def api_arrays(a):
            g=a['original_polygon_mesh']
            return json.dumps([g['nodeCoordinatesAsDouble'],g['triangleNodeIndices']])
        assert sorted(map(native_arrays,settings['current_result_meshes']))==sorted(map(api_arrays,actual_outputs))
        assert all(a['baseOrFormFeature'] is None for a in actual_outputs)
        assert all(math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-12) for x,y in zip(
            sorted(o['qualified_geometry']['derived_absolute_volume_cm3'] for o in settings['current_result_meshes']),
            sorted(a['volume'] for a in actual_outputs)))
        layout=settings['layout']
        assert bytes.fromhex(layout['feature_body_hex'])==data[layout['feature_body_offset']:layout['feature_body_end_offset']]
        assert layout['exact_full_payload_replay'] is True
        input_api=actual['feature_before_node']['mesh_body']
        input_arrays=input_api['original_polygon_mesh']
        same_arrays=(len(actual_outputs)==1 and actual_outputs[0]['original_polygon_mesh']['nodeCoordinatesAsDouble']==input_arrays['nodeCoordinatesAsDouble'] and actual_outputs[0]['original_polygon_mesh']['triangleNodeIndices']==input_arrays['triangleNodeIndices'])
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),expected_decoded=summary,
            expected_mesh_contents=strict,expected_definition=definition,
            actual_API_method_code=code,actual_API_keep_body=False,actual_API_inactive_multiple_bodies_getter_called=False,
            actual_API_input_node_count=input_arrays['nodeCount'],actual_API_input_triangle_count=input_arrays['triangleCount'],
            actual_API_input_face_group_count=len(input_api['face_groups']),actual_API_current_result_count=len(actual_outputs),
            actual_API_current_output_counts=[dict(nodes=a['original_polygon_mesh']['nodeCount'],triangles=a['original_polygon_mesh']['triangleCount']) for a in actual_outputs],
            single_result_arrays_equal_input=same_arrays,
            native_stored_result_names=[o['metadata']['name'] for o in settings['current_result_meshes']],
            actual_API_result_names=[a['name'] for a in actual_outputs],
            actual_API_result_handle_scope='Only full output coordinate/index ARRAY MULTISET equality corroborates the typed native result group. Individual API handle/name-to-native-ID mapping remains unproved; empty native names are not replaced by dynamic API names.',
            exact_source_and_all_output_arrays_match=True,exact_feature_payload_replay=True,owned_document_closed_true=True,
            area_scalar_counterexample=dict(source_API_area=actual['feature_before_node']['mesh_body']['area'],
                source_transformed_cache_area=sourcegeometry['derived_area_cm2'],
                API_output_areas=[a['area'] for a in actual_outputs],
                native_transformed_output_areas=[o['qualified_geometry']['derived_area_cm2'] for o in settings['current_result_meshes']],
                scope='Residual preserved; no area scalar transformation or convention inferred')))
    # Bounded structural guards, independent of geometry availability.
    data,records,features,member,members,definition=contexts['two_shells']
    feature_record,=[r for r in records if r.is_primary and r.object_id==definition['feature_object_id']]
    by_id={r.object_id:r for r in records if r.is_primary}
    def malformed(label,offset,payload,*,runtime=False):
        damaged=bytearray(data);damaged[offset:offset+len(payload)]=payload
        if runtime:
            answer=decode_mesh_separate(bytes(damaged),records,features,member,members)
            assert not answer['decoded'] and len(answer['unresolved'])==1
            reason=answer['unresolved'][0]['reason']
        else:
            try: decode_mesh_separate_definition(bytes(damaged),records,definition['feature_object_id'])
            except (ValueError,IndexError,struct.error) as error: reason=str(error)
            else: raise AssertionError('Malformed structural guard accepted: '+label)
        report['malformed_guards'].append(dict(guard=label,absolute_mutation_offset=offset,rejected=True,reason=reason))
    def ref(identity): return b'\1'+struct.pack('<Q',identity)+bytes(2)
    base=feature_record.body
    malformed('unobserved result count3',base+2,struct.pack('<I',3))
    malformed('unobserved method2',base+definition['method_field_body_relative_offset'],struct.pack('<I',2))
    malformed('source aliases result list',base+6,ref(213))
    malformed('dependency descriptor does not repeat source',base+definition['layout']['repeated_dependency_body_relative_offset']+11,ref(218))
    output=by_id[definition['output_mesh_object_ids'][0]]
    malformed('output feature owner is different BaseMesh',output.body+489,ref(218))
    collection,=[r for r in records if not r.is_primary and r.object_id==definition['mesh_collection_object_id'] and r.class_guid=='A7AEA631-985B-4DD1-8CE2-DE2C-14B54081']
    malformed('counted collection member differs from direct result',collection.body+5,ref(213))
    proxy=by_id[definition['source_selection']['proxy_object_id']]
    malformed('source proxy owned by wrong feature',proxy.end-11,ref(218))
    source=by_id[213]
    malformed('source matrix copy mismatch',source.body+152,struct.pack('<d',2.),runtime=True)
    # Non-candidate controls preserve existing shared runtime dictionary exactly.
    old=json.loads((ROOT/'mesh-combine-decoding.json').read_text())
    for saved in old['samples']:
        if not saved['archive'].endswith(('/join.f3d','/intersect.f3d')): continue
        d,rs,fs,n,m=context(saved['archive'],zstd)
        current=decode_mesh_contents_variants(d,rs,n,m)
        assert current==saved['expected_mesh_contents']
        summary=decode_mesh_separate(d,rs,fs,n,m,current)
        assert not summary['decoded'] and not summary['unresolved']
        report['legacy_controls'].append(dict(archive=saved['archive'],existing_mesh_contents_exact=True,new_helper_no_candidates=True))
    report['summary']=dict(saved_archives=3,decoded_separate_features=3,actual_control_readbacks=control_checks,
        exact_source_array_checks=source_checks,exact_current_result_array_checks=output_checks,
        exact_feature_payload_replays=3,malformed_guards=len(report['malformed_guards']),
        exact_legacy_mesh_controls=len(report['legacy_controls']),pure_definition_no_geometry_dependency=True,
        main_runs=0,live_calls=0)
    report['runtime_source_sha256']={f:digest(ROOT/f) for f in ('decode_mesh_separate.py','validate_mesh_separate.py',
        'decode_mesh_contents.py','decode_mesh_geometry_variants.py','decode_retained_mesh_sources.py','decode_mesh_selections.py')}
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default=str(ROOT/'mesh-separate-decoding.json'))
    args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd)
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':main()
