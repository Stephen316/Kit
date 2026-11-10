"""Fixed 37-file cached integration of bounded mesh partition additions.

No main decoder fallback: the root-produced current cache is required. Each
allowed difference is checked against focused goldens or an indexed helper
before whole-output equality is required.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_normals import decode_mesh_normal_pools
from decode_mesh_face_group_caches import decode_mesh_face_group_caches
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_history_cache_integration import differences

ROOT = Path(__file__).resolve().parent
BASELINE = 'b8a5580'
FILES = ('meshcontrasts-10c2557c91a3/stl_centimeter.f3d', 'meshcontrasts-10c2557c91a3/stl_millimeter.f3d', 'meshcontrasts-10c2557c91a3/triangle_data_centimeter.f3d', 'meshplanecuts-18f2683c83f5/split_body_minimal_fill.f3d', 'meshplanecuts-18f2683c83f5/trim_minimal_fill.f3d', 'meshplanecuts-18f2683c83f5/trim_no_fill.f3d', 'meshreduces-780954a23308/adaptive_count_six.f3d', 'meshreduces-780954a23308/adaptive_proportion_fifty.f3d', 'meshreduces-780954a23308/uniform_count_six.f3d', 'meshreduces-8f01528f7f21/adaptive_proportion_fifty.f3d', 'meshconverts-4b42d39fb1d5/faceted_closed.f3d', 'meshconverts-4b42d39fb1d5/faceted_open.f3d', 'meshconverts-4b42d39fb1d5/prismatic_closed.f3d', 'meshremeshes-f07f97514069/adaptive_edge_one_point_five.f3d', 'meshremeshes-f07f97514069/adaptive_edge_two.f3d', 'meshremeshes-f07f97514069/uniform_edge_two.f3d', 'meshcombines-541ebb6cc93f/cut.f3d', 'meshcombines-541ebb6cc93f/intersect.f3d', 'meshcombines-541ebb6cc93f/join.f3d', 'splinepatches-ac5e846e59c0/splinepatches.f3d', 'splinepatches-900d152c2380/splinepatches.f3d', 'assembly-acc48a9dc05d/assembly.f3d', 'meshreversenormals-2bc2dd3780cc/closed_once.f3d', 'meshreversenormals-2bc2dd3780cc/closed_twice.f3d', 'meshreversenormals-2bc2dd3780cc/open_once.f3d', 'meshsmooths-56f38f13430a/smooth_default_point_zero_two.f3d', 'meshsmooths-56f38f13430a/smooth_point_one.f3d', 'meshsmooths-56f38f13430a/smooth_point_two_five.f3d', 'meshshells-f5a2d6730f62/closed_thickness_point_one.f3d', 'meshshells-f5a2d6730f62/open_thickness_point_one.f3d', 'meshshells-f5a2d6730f62/open_thickness_point_two.f3d', 'meshfacegroups-0b682fa7d749/accurate_boundary_point_zero_zero_one.f3d', 'meshfacegroups-0b682fa7d749/fast_eighty_degrees.f3d', 'meshfacegroups-0b682fa7d749/fast_twenty_degrees.f3d', 'meshseparates-41126250c03f/connected_shell_control.f3d', 'meshseparates-41126250c03f/two_face_groups.f3d', 'meshseparates-41126250c03f/two_shells.f3d')
BASE_MESH = '99F6967E-ED35-4222-B906-5CCF0AC70B53'
BASE_FEATURE = 'D7015B81-AB4D-4C89-BED7-AA4411E1964A'
MESH_LEVEL = ('Observed component mesh ownership, native asset links and captured geometry buffers; '
              'general mesh formats, lifecycle and regeneration unresolved')
SPECS = (
    ('mesh_shells','mesh-shell-decoding.json','MeshShell','class_decoded_mesh_shell_count',
     '1514CDB8-BB81-4895-A953-7B12F4504F99',
     'Observed MeshShell thickness and owned parameter/mesh/asset routes; algorithm, lifecycle and regeneration unresolved'),
    ('mesh_face_groups','mesh-face-group-decoding.json','MeshGenerateFaceGroups','class_decoded_mesh_face_group_count',
     'CA2AE956-FD81-4EBD-A601-F93A0F335722',
     'Observed MeshGenerateFaceGroups method, owned parameters and triangle group cache; general partitions and regeneration unresolved'),
    ('mesh_separations','mesh-separate-decoding.json','MeshSeparate','class_decoded_mesh_separate_count',
     '6B6FDE2E-D9B9-4866-9D07-3123C919B0D2',
     'Observed MeshSeparate method and typed source/output membership; flag encodings, lifecycle and regeneration unresolved'),
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
    assert len(outputs) == len(FILES) == 37
    for filename,output in zip(FILES,outputs):
        assert output['file'] == str(ROOT/filename),(filename,'Wrong cache path/order')
        assert len({s['member'] for s in output['streams']}) == len(output['streams'])
        for stream in output['streams']:
            assert len({f['object_id'] for f in stream['features']}) == len(stream['features'])


def compare(before,current,filename,zstd,reports):
    after = copy.deepcopy(current)
    assert len(before['streams']) == len(after['streams'])
    members = read_members(ROOT/filename,zstd)
    counts = dict(MeshShell=0,MeshGenerateFaceGroups=0,MeshSeparate=0,new_BaseMesh_features=0,
                  new_current_mesh_rows=0,new_normal_pools=0,prior_normal_pool_dictionaries_preserved=0,
                  new_face_group_cache_rows=0,operation_tool_additions=0,Separate_retained_source_warnings_preserved=0)
    for prior,stream in zip(before['streams'],after['streams']):
        assert stream['member'] == prior['member']
        member = stream['member'];data = members[member]
        records,_ = design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        features = {f['object_id']:f for f in stream['features']}
        old_features = {f['object_id']:f for f in prior['features']}
        assert set(features) == set(old_features),(filename,'Native feature identities changed')
        # BaseFeature partial definitions already exist at b8a5580 and are not stripped.
        mesh = decode_mesh_contents_variants(data,records,member,members)
        assert stream.get('mesh_contents') == (mesh if mesh['decoded'] or mesh['unresolved'] else None)
        normals = decode_mesh_normal_pools(mesh)
        assert stream.get('mesh_normal_pools') == (normals if normals['decoded'] or normals['unresolved'] else None)
        prior_normals = prior.get('mesh_normal_pools',dict(decoded=[],unresolved=[]))
        normal_by_id = {row['mesh_object_id']:row for row in normals['decoded']}
        for row in prior_normals['decoded']:
            assert normal_by_id[row['mesh_object_id']] == row,(filename,'Prior full normal-pool dictionary changed')
            counts['prior_normal_pool_dictionaries_preserved'] += 1
        added_normals = set(normal_by_id)-{row['mesh_object_id'] for row in prior_normals['decoded']}
        if stream.get('mesh_normal_pools') != prior.get('mesh_normal_pools'):
            if filename in reports['mesh-shell-normal-decoding.json']:
                expected_normals = reports['mesh-shell-normal-decoding.json'][filename]['expected_decoded']
            else:
                assert filename in reports['mesh-separate-normal-decoding.json'],(filename,'Unqualified normal summary change')
                expected_normals = reports['mesh-separate-normal-decoding.json'][filename]['expected_decoded']
            assert normals == expected_normals and added_normals
        counts['new_normal_pools'] += len(added_normals)
        restore(stream,prior,('mesh_normal_pools',))
        # New cache stream consumes typed current meshes only; retained inputs stay separate.
        assert 'mesh_face_group_caches' not in prior
        groups = decode_mesh_face_group_caches(mesh)
        optional_summary(stream,'mesh_face_group_caches',groups,bool(groups['decoded'] or groups['unresolved']))
        group_goldens = reports['mesh-face-group-cache-decoding.json']
        separate_groups = reports['mesh-face-group-separate-decoding.json']
        if filename in group_goldens:
            assert groups == group_goldens[filename]['expected_decoded']
        elif filename in separate_groups:
            assert groups == separate_groups[filename]['expected_decoded']
        else:
            assert not groups['decoded'] and not groups['unresolved'],(filename,'Ungoldened group cache')
        counts['new_face_group_cache_rows'] += len(groups['decoded'])
        old_mesh = prior.get('mesh_contents',{'decoded':[],'unresolved':[]})
        by_mesh = {row['mesh_object_id']:row for row in mesh['decoded']}
        assert len(by_mesh) == len(mesh['decoded'])
        for row in old_mesh['decoded']:
            assert by_mesh[row['mesh_object_id']] == row,(filename,'Prior successful current mesh dictionary changed')
        new_mesh_ids = set(by_mesh)-{row['mesh_object_id'] for row in old_mesh['decoded']}
        changed_mesh = stream.get('mesh_contents') != prior.get('mesh_contents')
        if changed_mesh:
            qualified = filename.startswith(('meshshells-f5a2d6730f62/','meshseparates-41126250c03f/'))
            assert qualified and new_mesh_ids,(filename,'Unqualified current mesh summary change')
            report_name = 'mesh-shell-decoding.json' if filename.startswith('meshshells-') else 'mesh-separate-decoding.json'
            assert mesh == reports[report_name][filename]['expected_mesh_contents'],(filename,'Full current mesh golden differs')
        if filename.startswith('meshseparates-41126250c03f/'):
            source_error = dict(mesh_object_id=213,reason='Unobserved opt-in native mesh prefix')
            assert source_error in mesh['unresolved'] and source_error in old_mesh['unresolved']
            assert all(row['mesh_object_id'] != 213 for row in mesh['decoded'])
            assert all(row['mesh_object_id'] != 213 for row in groups['decoded'])
            counts['Separate_retained_source_warnings_preserved'] += 1
        assert mesh['unresolved'] == [row for row in old_mesh['unresolved'] if row['mesh_object_id'] not in new_mesh_ids],(filename,'Unqualified current mesh warning change')
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
    report_names = [spec[1] for spec in SPECS]+['mesh-shell-normal-decoding.json','mesh-separate-normal-decoding.json',
        'mesh-face-group-cache-decoding.json','mesh-face-group-separate-decoding.json']
    reports = {name:goldens(name) for name in report_names}
    rows = [compare(old,new,name,zstd,reports) for name,old,new in zip(FILES,before,current)]
    totals = {key:sum(row[key] for row in rows) for key,value in rows[0].items() if type(value) is int}
    assert totals['MeshShell'] == totals['MeshGenerateFaceGroups'] == totals['MeshSeparate'] == 3
    assert totals['operation_tool_additions'] == 9
    assert totals['new_BaseMesh_features'] == 3 and totals['new_current_mesh_rows'] == 7
    assert totals['new_normal_pools'] == 7 and totals['Separate_retained_source_warnings_preserved'] == 3
    evidence = ['validate_mesh_partition_integration.py','decode_basics.py','decode_mesh_contents.py',
        'decode_mesh_geometry_variants.py','decode_mesh_normals.py','decode_mesh_face_group_caches.py',
        'decode_mesh_shell.py','decode_mesh_face_groups.py','decode_mesh_separate.py',
        'decode_retained_mesh_sources.py','decode_mesh_selections.py']+report_names
    return dict(scope='37 pinned cached main outputs, only bounded report/helper-qualified mesh partition additions restored before exact whole-output comparison',
        baseline_commit=BASELINE,files=list(FILES),samples=rows,
        inputs=dict(baseline_cache_sha256=sha(baseline_path),current_cache_sha256=sha(current_path),
            manifest_sha256=sha(manifest_path),baseline_output_set_sha256=canonical(before),current_output_set_sha256=canonical(current)),
        summary=dict(saved_files=37,**totals,unqualified_output_changes=0,ASM_changes=0,placement_changes=0,full_main_runs=0,live_API_calls=0),
        evidence_sha256={name:sha(ROOT/name) for name in evidence},
        limitations=['Normal pools do not establish per-corner/vertex associations or reproduce PolygonMesh normals.',
            'Prior BaseFeature partial definitions and all previous operation/settings streams remain exact; only new positive rows are classified.',
            'Current mesh, retained selected input and additional stored assets remain separate; no general lifecycle or geometry regeneration inference.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-outputs',type=Path,default=Path('/private/tmp/fusion-mesh-partitions-baseline.json'))
    parser.add_argument('--current-outputs',type=Path,required=True)
    parser.add_argument('--files',type=Path,default=Path('/private/tmp/fusion-mesh-partitions-files.json'))
    parser.add_argument('--zstd-library',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-partition-integration.json')
    args=parser.parse_args();report=validate(args.zstd_library,args.baseline_outputs,args.current_outputs,args.files)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
