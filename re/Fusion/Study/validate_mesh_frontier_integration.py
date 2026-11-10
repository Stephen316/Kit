"""Fixed 22-file cached integration of bounded mesh frontier additions.

No main decoder fallback: the root-produced current cache is required. Each
allowed difference is checked against focused goldens or an indexed helper
before whole-output equality is required.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from decode_base_feature_empty_lists import decode_base_feature_empty_lists
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_normals import decode_mesh_normal_pools
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_history_cache_integration import differences

ROOT = Path(__file__).resolve().parent
BASELINE = '1b12e40'
FILES = (
    'meshcontrasts-10c2557c91a3/stl_centimeter.f3d',
    'meshcontrasts-10c2557c91a3/stl_millimeter.f3d',
    'meshcontrasts-10c2557c91a3/triangle_data_centimeter.f3d',
    'meshplanecuts-18f2683c83f5/split_body_minimal_fill.f3d',
    'meshplanecuts-18f2683c83f5/trim_minimal_fill.f3d',
    'meshplanecuts-18f2683c83f5/trim_no_fill.f3d',
    'meshreduces-780954a23308/adaptive_count_six.f3d',
    'meshreduces-780954a23308/adaptive_proportion_fifty.f3d',
    'meshreduces-780954a23308/uniform_count_six.f3d',
    'meshreduces-8f01528f7f21/adaptive_proportion_fifty.f3d',
    'meshconverts-4b42d39fb1d5/faceted_closed.f3d',
    'meshconverts-4b42d39fb1d5/faceted_open.f3d',
    'meshconverts-4b42d39fb1d5/prismatic_closed.f3d',
    'meshremeshes-f07f97514069/adaptive_edge_one_point_five.f3d',
    'meshremeshes-f07f97514069/adaptive_edge_two.f3d',
    'meshremeshes-f07f97514069/uniform_edge_two.f3d',
    'meshcombines-541ebb6cc93f/cut.f3d',
    'meshcombines-541ebb6cc93f/intersect.f3d',
    'meshcombines-541ebb6cc93f/join.f3d',
    'splinepatches-ac5e846e59c0/splinepatches.f3d',
    'splinepatches-900d152c2380/splinepatches.f3d',
    'assembly-acc48a9dc05d/assembly.f3d',
)
BASE_MESH = '99F6967E-ED35-4222-B906-5CCF0AC70B53'
BASE_FEATURE = 'D7015B81-AB4D-4C89-BED7-AA4411E1964A'
MESH_LEVEL = ('Observed component mesh ownership, native asset links and captured geometry buffers; '
              'general mesh formats, lifecycle and regeneration unresolved')
SPECS = (
    ('mesh_remeshes','mesh-remesh-decoding.json','MeshRemesh','class_decoded_mesh_remesh_count',
     '828DDA62-2750-447D-8728-06C9B7C2B117',
     'Observed MeshRemesh method/target and owned parameter/mesh/asset routes; preservation flags, historical lifecycle and regeneration unresolved'),
    ('mesh_conversions','mesh-convert-decoding.json','MeshConvert','class_decoded_mesh_convert_count',
     '62B85DC3-27B5-47BA-9F13-B2527B72EE49',
     'Observed Faceted MeshConvert source and owned BRep result/history routes; alternative methods, lifecycle and regeneration unresolved'),
    ('mesh_combinations','mesh-combine-decoding.json','MeshCombine','class_decoded_mesh_combine_count',
     'EE0E56E8-5894-4D65-BAF4-9DAAF811307F',
     'Observed MeshCombine operation and selected target/tool asset routes; flags, historical lifecycle and regeneration unresolved'),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def read(name):
    return json.loads((ROOT/name).read_text())


def goldens(name):
    rows = read(name)['samples']
    assert len({row['archive'] for row in rows}) == len(rows),(name,'Duplicate archive')
    return {row['archive']:row for row in rows}


def restore(actual, prior, keys):
    for key in keys:
        if key in prior:
            actual[key] = copy.deepcopy(prior[key])
        else:
            actual.pop(key,None)


def optional_summary(actual, key, expected, populated):
    assert actual.get(key) == (expected if populated else None),(key,'Native/helper summary differs')
    actual.pop(key,None)


def manifest(outputs):
    assert len(outputs) == len(FILES) == 22
    for filename,output in zip(FILES,outputs):
        assert output['file'] == str(ROOT/filename),(filename,'Wrong cache path/order')
        assert len({s['member'] for s in output['streams']}) == len(output['streams'])
        for stream in output['streams']:
            assert len({f['object_id'] for f in stream['features']}) == len(stream['features'])


def compare(before,current,filename,zstd,reports):
    after = copy.deepcopy(current)
    assert len(before['streams']) == len(after['streams'])
    members = read_members(ROOT/filename,zstd)
    counts = dict(partial_BaseFeature_definitions=0,normal_pools=0,normal_pool_failures=0,
                  MeshRemesh=0,MeshConvert=0,MeshCombine=0,new_BaseMesh_features=0,
                  new_current_mesh_rows=0,operation_tool_additions=0)
    for prior,stream in zip(before['streams'],after['streams']):
        assert stream['member'] == prior['member']
        member = stream['member'];data = members[member]
        records,_ = design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        features = {f['object_id']:f for f in stream['features']}
        old_features = {f['object_id']:f for f in prior['features']}
        assert set(features) == set(old_features),(filename,'Native feature identities changed')
        # Partial definition is independently framed, but changes no feature kind or errors.
        assert 'base_feature_empty_lists' not in prior
        partial = decode_base_feature_empty_lists(data,records,stream['features'])
        optional_summary(stream,'base_feature_empty_lists',partial,bool(partial['partial'] or partial['unresolved']))
        if filename in reports['base-feature-empty-list-decoding.json']:
            assert partial == reports['base-feature-empty-list-decoding.json'][filename]['expected_decoded']
        expected_partial = {row['feature_object_id']:row for row in partial['partial']}
        for identity,feature in features.items():
            if identity in expected_partial:
                assert feature.pop('base_feature_empty_list_definition') == expected_partial[identity]
                assert feature['class_guid'] == BASE_FEATURE and feature['kind'] == old_features[identity]['kind']
                counts['partial_BaseFeature_definitions'] += 1
            else:
                assert 'base_feature_empty_list_definition' not in feature
        # Source geometry remains separate from selected retained meshes in operation settings.
        mesh = decode_mesh_contents_variants(data,records,member,members)
        assert stream.get('mesh_contents') == (mesh if mesh['decoded'] or mesh['unresolved'] else None)
        normals = decode_mesh_normal_pools(mesh)
        optional_summary(stream,'mesh_normal_pools',normals,bool(normals['decoded'] or normals['unresolved']))
        assert 'mesh_normal_pools' not in prior
        if filename in reports['mesh-normal-decoding.json']:
            assert normals == reports['mesh-normal-decoding.json'][filename]['expected_decoded']
        counts['normal_pools'] += len(normals['decoded']);counts['normal_pool_failures'] += len(normals['unresolved'])
        old_mesh = prior.get('mesh_contents',{'decoded':[],'unresolved':[]})
        by_mesh = {row['mesh_object_id']:row for row in mesh['decoded']}
        assert len(by_mesh) == len(mesh['decoded'])
        for row in old_mesh['decoded']:
            assert by_mesh[row['mesh_object_id']] == row,(filename,'Prior successful current mesh dictionary changed')
        new_mesh_ids = set(by_mesh)-{row['mesh_object_id'] for row in old_mesh['decoded']}
        changed_mesh = stream.get('mesh_contents') != prior.get('mesh_contents')
        if changed_mesh:
            qualified = filename.startswith(('meshremeshes-f07f97514069/','meshcombines-541ebb6cc93f/'))
            assert qualified and new_mesh_ids,(filename,'Unqualified current mesh summary change')
            report_name = 'mesh-remesh-decoding.json' if filename.startswith('meshremeshes-') else 'mesh-combine-decoding.json'
            assert mesh == reports[report_name][filename]['expected_mesh_contents'],(filename,'Full current mesh golden differs')
        counts['new_current_mesh_rows'] += len(new_mesh_ids)
        restore(stream,prior,('mesh_contents',))
        discovery = stream['feature_discovery'];old_discovery = prior['feature_discovery']
        recovered = set();kinds = {};base_ids = set()
        for mesh_row in mesh['decoded']:
            identity = mesh_row['feature_object_id']
            if identity is None or identity not in features or features[identity]['class_guid'] != BASE_MESH:
                continue
            base_ids.add(identity)
            feature = features[identity]
            assert feature['kind'] == 'BaseMeshFeature' and feature['decode_level'] == MESH_LEVEL
            assert feature['mesh_contents'] == mesh_row and mesh_row['native_feature_class_guid'] == BASE_MESH
            if old_features[identity]['kind'] != 'BaseMeshFeature':
                assert old_features[identity]['kind'] == 'UnsupportedFeature'
                assert mesh_row['mesh_object_id'] in new_mesh_ids
                recovered.add(identity);kinds[identity]='BaseMeshFeature';counts['new_BaseMesh_features'] += 1
            restore(feature,old_features[identity],('kind','decode_level','mesh_contents'))
        if base_ids:
            assert discovery['class_decoded_mesh_base_feature_count'] == len(base_ids)
            restore(discovery,old_discovery,('class_decoded_mesh_base_feature_count',))
        for key,report_name,kind,counter,guid,level in SPECS:
            assert key not in prior
            expected_row = reports[report_name].get(filename)
            actual = stream.pop(key,None)
            if expected_row is None:
                assert actual is None,(filename,key,'New summary not covered by focused report')
                continue
            expected = expected_row['expected_decoded']
            assert actual == (expected if expected['decoded'] or expected['unresolved'] else None),(filename,key,'Operation golden differs')
            for row in expected['decoded']:
                identity = row['feature_object_id'];feature = features[identity]
                assert row['kind'] == feature['kind'] == kind and feature['class_guid'] == guid
                assert old_features[identity]['kind'] == 'UnsupportedFeature'
                assert feature['name'] == row['name'] == old_features[identity]['name']
                assert feature['tool_settings'] == row['settings'] and feature['decode_level'] == level
                restore(feature,old_features[identity],('kind','tool_settings','decode_level'))
                entry = dict(object_id=identity,kind=kind)
                assert entry not in prior['tool_decoding']['decoded']
                assert stream['tool_decoding']['decoded'].count(entry) == 1
                stream['tool_decoding']['decoded'].remove(entry)
                recovered.add(identity);kinds[identity]=kind;counts[kind] += 1;counts['operation_tool_additions'] += 1
            if expected['decoded'] or expected['unresolved']:
                assert discovery[counter] == len(expected['decoded'])
                restore(discovery,old_discovery,(counter,))
            else:
                assert discovery.get(counter) == old_discovery.get(counter)
        expected_unsupported = [row for row in old_discovery['unsupported_features'] if row['object_id'] not in recovered]
        assert discovery['unsupported_features'] == expected_unsupported
        assert discovery['unsupported_feature_count'] == len(expected_unsupported)
        assert {row['object_id'] for row in old_discovery['unsupported_features']}-{row['object_id'] for row in expected_unsupported} == recovered
        restore(discovery,old_discovery,('unsupported_features','unsupported_feature_count'))
        assert stream['tool_decoding']['unresolved'] == prior['tool_decoding']['unresolved'],(filename,'Prior tool warnings changed')
        def timeline(entry):
            identity = entry['object_id']
            if identity in recovered:
                assert entry['kind'] == kinds[identity]
                entry['kind'] = old_features[identity]['kind']
            for child in entry.get('children',[]):
                timeline(child)
        for sequence in stream['timeline_decoding']['sequences']:
            for entry in sequence['visible_entries']:
                timeline(entry)
    assert after == before,(filename,'Unqualified output difference',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),**counts,
        all_other_fields_exact=True,ASM_and_placement_exact=True,prior_tool_warnings_exact=True,
        baseline_output_sha256=canonical(before),current_output_sha256=canonical(current),
        qualified_difference_paths=differences(before,current))


def cache_rows(path, side):
    cache = json.loads(Path(path).read_text())
    if isinstance(cache,list):
        return cache
    assert cache['baseline_commit'] == BASELINE and cache['files'] == list(FILES)
    return cache[side]


def validate(zstd, baseline_path, current_path, manifest_path):
    assert json.loads(Path(manifest_path).read_text()) == list(FILES)
    before = cache_rows(baseline_path,'before');current = cache_rows(current_path,'after')
    manifest(before);manifest(current)
    report_names = [spec[1] for spec in SPECS]+['mesh-normal-decoding.json','base-feature-empty-list-decoding.json']
    reports = {name:goldens(name) for name in report_names}
    rows = [compare(old,new,name,zstd,reports) for name,old,new in zip(FILES,before,current)]
    totals = {key:sum(row[key] for row in rows) for key,value in rows[0].items() if type(value) is int}
    assert totals['MeshRemesh'] == 3 and totals['MeshConvert'] == 2 and totals['MeshCombine'] == 3
    assert totals['operation_tool_additions'] == 8
    evidence = ['validate_mesh_frontier_integration.py','decode_basics.py','decode_mesh_contents.py',
        'decode_mesh_geometry_variants.py','decode_mesh_normals.py','decode_base_feature_empty_lists.py',
        'decode_mesh_remesh.py','decode_mesh_convert.py','decode_mesh_combine.py',
        'decode_retained_mesh_sources.py','decode_mesh_selections.py']+report_names
    return dict(scope='22 pinned cached main outputs, only bounded report/helper-qualified mesh additions restored before exact whole-output comparison',
        baseline_commit=BASELINE,files=list(FILES),samples=rows,
        inputs=dict(baseline_cache_sha256=sha(baseline_path),current_cache_sha256=sha(current_path),
            manifest_sha256=sha(manifest_path),baseline_output_set_sha256=canonical(before),current_output_set_sha256=canonical(current)),
        summary=dict(saved_files=22,**totals,unqualified_output_changes=0,ASM_changes=0,placement_changes=0,full_main_runs=0,live_API_calls=0),
        evidence_sha256={name:sha(ROOT/name) for name in evidence},
        limitations=['Normal pools do not establish per-corner/vertex associations or reproduce PolygonMesh normals.',
            'Partial BaseFeature lists do not classify BaseFeature, assign meshes or clear existing warnings.',
            'Current mesh, retained selected input and additional stored assets remain separate; no general lifecycle or geometry regeneration inference.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-outputs',type=Path,default=Path('/private/tmp/fusion-mesh-frontier-baseline.json'))
    parser.add_argument('--current-outputs',type=Path,required=True)
    parser.add_argument('--files',type=Path,default=Path('/private/tmp/fusion-mesh-frontier-files.json'))
    parser.add_argument('--zstd-library',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-frontier-integration.json')
    args=parser.parse_args();report=validate(args.zstd_library,args.baseline_outputs,args.current_outputs,args.files)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
