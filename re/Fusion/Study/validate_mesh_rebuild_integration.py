"""Forty-nine fixed cached outputs: bounded MeshRepair Rebuild and current caches.

The old46 complete outputs must remain exact. New3 differences require complete
operation/geometry/normal/group goldens, explicit native-owner classification,
and exact restoration before whole-output comparison. No main fallback.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from validate_history_cache_integration import differences

ROOT=Path(__file__).resolve().parent
BASELINE='775102f'
FILES=('meshcontrasts-10c2557c91a3/stl_centimeter.f3d',
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
 'meshreversenormals-2bc2dd3780cc/closed_once.f3d',
 'meshreversenormals-2bc2dd3780cc/closed_twice.f3d',
 'meshreversenormals-2bc2dd3780cc/open_once.f3d',
 'meshsmooths-56f38f13430a/smooth_default_point_zero_two.f3d',
 'meshsmooths-56f38f13430a/smooth_point_one.f3d',
 'meshsmooths-56f38f13430a/smooth_point_two_five.f3d',
 'meshshells-f5a2d6730f62/closed_thickness_point_one.f3d',
 'meshshells-f5a2d6730f62/open_thickness_point_one.f3d',
 'meshshells-f5a2d6730f62/open_thickness_point_two.f3d',
 'meshfacegroups-0b682fa7d749/accurate_boundary_point_zero_zero_one.f3d',
 'meshfacegroups-0b682fa7d749/fast_eighty_degrees.f3d',
 'meshfacegroups-0b682fa7d749/fast_twenty_degrees.f3d',
 'meshseparates-41126250c03f/connected_shell_control.f3d',
 'meshseparates-41126250c03f/two_face_groups.f3d',
 'meshseparates-41126250c03f/two_shells.f3d',
 'meshremoves-8b2188cd274d/one_remove_one.f3d',
 'meshremoves-8b2188cd274d/two_remove_both.f3d',
 'meshremoves-8b2188cd274d/two_remove_first.f3d',
 'meshcombinefacegroups-33142f03b86e/adjacent_pair.f3d',
 'meshcombinefacegroups-33142f03b86e/adjacent_pair_reversed.f3d',
 'meshcombinefacegroups-33142f03b86e/connected_triple.f3d',
 'meshrepairs-2387e4f9c2d2/closed_close_holes_control.f3d',
 'meshrepairs-2387e4f9c2d2/open_close_holes.f3d',
 'meshrepairs-2387e4f9c2d2/open_stitch_remove.f3d',
 'meshrepairrebuilds-66d4316c2e8d/accurate_density_eight_offset_point_zero_five.f3d',
 'meshrepairrebuilds-66d4316c2e8d/accurate_density_eight_offset_zero.f3d',
 'meshrepairrebuilds-66d4316c2e8d/fast_density_eight.f3d')
BASE_MESH='99F6967E-ED35-4222-B906-5CCF0AC70B53'
REPAIR='68691143-5EE3-428E-9CD3-F728E4718559'
MESH_LEVEL='Observed component mesh ownership, native asset links and captured geometry buffers; general mesh formats, lifecycle and regeneration unresolved'
REPAIR_LEVEL='Observed MeshRepair method and owned control/mesh/asset routes; additional methods, lifecycle and regeneration unresolved'
OPERATION_REPORT='mesh-repair-rebuild-decoding.json'
GEOMETRY_REPORT='mesh-rebuild-geometry-decoding.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def restore(actual,prior,keys):
    for key in keys:
        if key in prior:actual[key]=copy.deepcopy(prior[key])
        else:actual.pop(key,None)


def goldens(name):
    rows=json.loads((ROOT/name).read_text())['samples']
    assert len({row['archive'] for row in rows})==len(rows)
    return {row['archive']:row for row in rows}


def manifest(outputs):
    assert len(outputs)==len(FILES)==49
    for filename,output in zip(FILES,outputs):
        assert output['file']==str(ROOT/filename),(filename,'Cache order/path differs')
        assert len({s['member'] for s in output['streams']})==len(output['streams'])
        for stream in output['streams']:
            assert len({f['object_id'] for f in stream['features']})==len(stream['features'])


def compare(before,current,filename,operations,geometry):
    after=copy.deepcopy(current)
    counts=dict(MeshRepair_Rebuild=0,new_BaseMesh_features=0,new_current_mesh_rows=0,
                new_normal_pools=0,new_group_caches=0,operation_tool_additions=0)
    if filename not in operations:
        assert current==before,(filename,'Legacy complete output changed',differences(before,current))
    else:
        assert filename in geometry and len(before['streams'])==len(after['streams'])
        for prior,stream in zip(before['streams'],after['streams']):
            assert stream['member']==prior['member']
            focused=geometry[filename]
            for key,expected_key in (('mesh_contents','expected_mesh_contents'),('mesh_normal_pools','expected_normal_pools'),
                                      ('mesh_face_group_caches','expected_face_group_caches')):
                assert stream.get(key)==focused[expected_key],(filename,key,'Geometry golden differs')
            mesh=stream['mesh_contents'];normals=stream['mesh_normal_pools'];groups=stream['mesh_face_group_caches']
            assert len(mesh['decoded'])==len(normals['decoded'])==len(groups['decoded'])==1
            assert not mesh['unresolved'] and not normals['unresolved'] and not groups['unresolved']
            mesh_row=mesh['decoded'][0];identity=mesh_row['mesh_object_id']
            assert normals['decoded'][0]['mesh_object_id']==groups['decoded'][0]['mesh_object_id']==identity
            old_mesh=prior['mesh_contents']
            assert not old_mesh['decoded'] and old_mesh['unresolved']==[dict(mesh_object_id=identity,reason='Unobserved opt-in mesh buffer dimensions')]
            assert not prior.get('mesh_normal_pools',dict(decoded=[]))['decoded']
            assert not prior.get('mesh_face_group_caches',dict(decoded=[]))['decoded']
            counts['new_current_mesh_rows']+=1;counts['new_normal_pools']+=1;counts['new_group_caches']+=1
            restore(stream,prior,('mesh_contents','mesh_normal_pools','mesh_face_group_caches'))
            features={f['object_id']:f for f in stream['features']};old_features={f['object_id']:f for f in prior['features']}
            assert set(features)==set(old_features)
            owner=mesh_row['feature_object_id'];base=features[owner];old_base=old_features[owner]
            assert mesh_row['native_feature_class_guid']==base['class_guid']==old_base['class_guid']==BASE_MESH
            assert old_base['kind']=='UnsupportedFeature' and base['kind']=='BaseMeshFeature'
            assert base['mesh_contents']==mesh_row and base['decode_level']==MESH_LEVEL
            restore(base,old_base,('kind','mesh_contents','decode_level'));counts['new_BaseMesh_features']+=1
            repaired=operations[filename]['expected_decoded']
            assert stream.get('mesh_repairs')==repaired and len(repaired['decoded'])==1 and not repaired['unresolved']
            row=repaired['decoded'][0];repair_id=row['feature_object_id'];feature=features[repair_id];old=old_features[repair_id]
            assert repair_id!=owner and feature['class_guid']==old['class_guid']==REPAIR
            assert old['kind']=='UnsupportedFeature' and row['kind']==feature['kind']=='MeshRepair'
            assert feature.get('name')==old.get('name')==row.get('name')
            assert feature['tool_settings']==row['settings'] and feature['decode_level']==REPAIR_LEVEL
            restore(feature,old,('kind','tool_settings','decode_level'));restore(stream,prior,('mesh_repairs',))
            counts['MeshRepair_Rebuild']+=1
            tool=dict(object_id=repair_id,kind='MeshRepair')
            assert tool not in prior['tool_decoding']['decoded'] and stream['tool_decoding']['decoded'].count(tool)==1
            stream['tool_decoding']['decoded'].remove(tool);counts['operation_tool_additions']+=1
            assert stream['tool_decoding']['unresolved']==prior['tool_decoding']['unresolved']
            discovery=stream['feature_discovery'];old_discovery=prior['feature_discovery']
            assert discovery['class_decoded_mesh_base_feature_count']==1 and discovery['class_decoded_mesh_repair_count']==1
            restore(discovery,old_discovery,('class_decoded_mesh_base_feature_count','class_decoded_mesh_repair_count'))
            recovered={owner,repair_id}
            unsupported=[r for r in old_discovery['unsupported_features'] if r['object_id'] not in recovered]
            assert discovery['unsupported_features']==unsupported and discovery['unsupported_feature_count']==len(unsupported)
            assert {r['object_id'] for r in old_discovery['unsupported_features']}-{r['object_id'] for r in unsupported}==recovered
            restore(discovery,old_discovery,('unsupported_features','unsupported_feature_count'))
            kinds={owner:'BaseMeshFeature',repair_id:'MeshRepair'}
            def timeline(entry):
                ident=entry['object_id']
                if ident in recovered:
                    assert entry['kind']==kinds[ident];entry['kind']=old_features[ident]['kind']
                for child in entry.get('children',[]):timeline(child)
            for sequence in stream['timeline_decoding']['sequences']:
                for entry in sequence['visible_entries']:timeline(entry)
    assert after==before,(filename,'Unqualified prior-output difference',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),**counts,all_other_fields_exact=True,
        prior_tool_warnings_ASM_placement_and_partial_definitions_exact=True,
        baseline_output_sha256=canonical(before),current_output_sha256=canonical(current),
        qualified_difference_paths=differences(before,current))


def cache_rows(path,side):
    cache=json.loads(Path(path).read_text())
    if isinstance(cache,list):return cache
    assert cache['baseline_commit']==BASELINE and cache['files']==list(FILES)
    return cache[side]


def validate(baseline_path,current_path,manifest_path):
    assert json.loads(Path(manifest_path).read_text())==list(FILES)
    before=cache_rows(baseline_path,'before');current=cache_rows(current_path,'after')
    manifest(before);manifest(current)
    operations=goldens(OPERATION_REPORT);geometry=goldens(GEOMETRY_REPORT)
    assert set(operations)==set(geometry)==set(FILES[-3:])
    rows=[compare(old,new,filename,operations,geometry) for filename,old,new in zip(FILES,before,current)]
    totals={key:sum(row[key] for row in rows) for key,value in rows[0].items() if type(value) is int}
    assert all(value==3 for value in totals.values())
    assert all(old==new for old,new in zip(before[:46],current[:46]))
    evidence=['validate_mesh_rebuild_integration.py','decode_basics.py','decode_mesh_repair.py','decode_mesh_contents.py',
        'decode_mesh_geometry_variants.py','decode_mesh_normals.py','decode_mesh_face_group_caches.py',
        'decode_retained_mesh_sources.py',OPERATION_REPORT,GEOMETRY_REPORT]
    return dict(scope='49 fixed cached outputs against775102f, only three Rebuild Repair positives and report-qualified current cache/owner recoveries restored before exact comparison',
        baseline_commit=BASELINE,files=list(FILES),samples=rows,
        inputs=dict(baseline_cache_sha256=sha(baseline_path),current_cache_sha256=sha(current_path),manifest_sha256=sha(manifest_path),
            baseline_output_set_sha256=canonical(before),current_output_set_sha256=canonical(current)),
        summary=dict(saved_files=49,legacy_complete_output_controls=46,**totals,unqualified_output_changes=0,ASM_changes=0,placement_changes=0,full_main_runs=0,live_API_calls=0),
        evidence_sha256={name:sha(ROOT/name) for name in evidence},
        limitations=['Only explicitly observed Rebuild controls and current stored arrays/caches are qualified; no repair/rebuild algorithm or source-state replay.',
            'All prior46 whole outputs, including three earlier Repair settings, remain exact. Additional asset temporal role stays scoped by focused runtime output.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-outputs',type=Path,default=Path('/private/tmp/fusion-mesh-rebuilds-baseline.json'))
    parser.add_argument('--current-outputs',type=Path,default=Path('/private/tmp/fusion-mesh-rebuilds-current.json'))
    parser.add_argument('--files',type=Path,default=Path('/private/tmp/fusion-mesh-rebuilds-files.json'))
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-rebuild-integration.json')
    args=parser.parse_args();report=validate(args.baseline_outputs,args.current_outputs,args.files)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
