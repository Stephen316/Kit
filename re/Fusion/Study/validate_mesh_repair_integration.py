"""Forty-six cached outputs: only qualified MeshRepair additions.

No main decoder or native helper reruns are performed. Exact focused report
rows qualify every allowed feature, tool, counter and timeline change.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from validate_history_cache_integration import differences

ROOT=Path(__file__).resolve().parent
BASELINE='87487cc'
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
 'meshrepairs-2387e4f9c2d2/open_stitch_remove.f3d')
SPECS=(
    ('mesh_repairs','mesh-repair-decoding.json','MeshRepair','class_decoded_mesh_repair_count',
     '68691143-5EE3-428E-9CD3-F728E4718559',
     'Observed MeshRepair method and owned control/mesh/asset routes; additional methods, lifecycle and regeneration unresolved'),
)



def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def restore(actual,prior,keys):
    for key in keys:
        if key in prior:actual[key]=copy.deepcopy(prior[key])
        else:actual.pop(key,None)


def goldens(name):
    rows=json.loads((ROOT/name).read_text())['samples']
    assert len({row['archive'] for row in rows})==len(rows),(name,'Duplicate focused report archive')
    return {row['archive']:row for row in rows}


def check_manifest(outputs):
    assert len(outputs)==len(FILES)==46
    for filename,output in zip(FILES,outputs):
        assert output['file']==str(ROOT/filename),(filename,'Cache filename/order differs')
        assert len({stream['member'] for stream in output['streams']})==len(output['streams'])
        for stream in output['streams']:
            assert len({feature['object_id'] for feature in stream['features']})==len(stream['features'])


def compare(before,current,filename,reports):
    after=copy.deepcopy(current)
    assert len(before['streams'])==len(after['streams'])
    counts=dict(MeshRepair=0,operation_tool_additions=0,
                current_mesh_summary_changes=0,normal_pool_changes=0,group_cache_changes=0)
    for prior,stream in zip(before['streams'],after['streams']):
        assert stream['member']==prior['member']
        features={feature['object_id']:feature for feature in stream['features']}
        old_features={feature['object_id']:feature for feature in prior['features']}
        assert set(features)==set(old_features),(filename,'Native feature discovery identities changed')
        # Stronger than the preceding geometry stage: every existing cache and
        # warning must remain exact. Retained source assets stay separately scoped.
        for key in ('mesh_contents','mesh_normal_pools','mesh_face_group_caches'):
            assert stream.get(key)==prior.get(key),(filename,key,'Existing current cache changed')
        assert stream['tool_decoding']['unresolved']==prior['tool_decoding']['unresolved'],(filename,'Existing tool warning changed')
        geometry_golden=reports['mesh-repair-geometry-decoding.json'].get(filename)
        if geometry_golden is not None:
            for key,expected_key in (('mesh_contents','expected_mesh_contents'),
                                     ('mesh_normal_pools','expected_normal_pools'),
                                     ('mesh_face_group_caches','expected_face_group_caches')):
                assert stream.get(key)==geometry_golden[expected_key],(filename,key,'Focused Repair geometry golden differs')
        discovery=stream['feature_discovery'];old_discovery=prior['feature_discovery']
        recovered=set();kinds={}
        for key,report_name,kind,counter,guid,level in SPECS:
            assert key not in prior
            actual=stream.pop(key,None)
            golden=reports[report_name].get(filename)
            if golden is None:
                assert actual is None,(filename,key,'Unqualified new family summary')
                assert discovery.get(counter)==old_discovery.get(counter)
                continue
            expected=golden['expected_decoded']
            assert actual==(expected if expected['decoded'] or expected['unresolved'] else None),(filename,key,'Focused operation golden differs')
            assert len({row['feature_object_id'] for row in expected['decoded']})==len(expected['decoded'])
            ids=set()
            for row in expected['decoded']:
                identity=row['feature_object_id'];feature=features[identity];old=old_features[identity]
                assert identity not in recovered and feature['class_guid']==old['class_guid']==guid
                assert old['kind']=='UnsupportedFeature' and row['kind']==feature['kind']==kind
                assert feature.get('name')==old.get('name')==row.get('name')
                assert feature['tool_settings']==row['settings'] and feature['decode_level']==level
                restore(feature,old,('kind','tool_settings','decode_level'))
                entry=dict(object_id=identity,kind=kind)
                assert entry not in prior['tool_decoding']['decoded']
                assert stream['tool_decoding']['decoded'].count(entry)==1
                stream['tool_decoding']['decoded'].remove(entry)
                ids.add(identity);recovered.add(identity);kinds[identity]=kind
                counts[kind]+=1;counts['operation_tool_additions']+=1
            if expected['decoded'] or expected['unresolved']:
                assert discovery[counter]==len(ids)
                restore(discovery,old_discovery,(counter,))
            else:assert discovery.get(counter)==old_discovery.get(counter)
        unsupported=[row for row in old_discovery['unsupported_features'] if row['object_id'] not in recovered]
        assert discovery['unsupported_features']==unsupported
        assert discovery['unsupported_feature_count']==len(unsupported)
        assert {row['object_id'] for row in old_discovery['unsupported_features']}-{row['object_id'] for row in unsupported}==recovered
        restore(discovery,old_discovery,('unsupported_features','unsupported_feature_count'))
        def timeline(entry):
            identity=entry['object_id']
            if identity in recovered:
                assert entry['kind']==kinds[identity]
                entry['kind']=old_features[identity]['kind']
            for child in entry.get('children',[]):timeline(child)
        for sequence in stream['timeline_decoding']['sequences']:
            for entry in sequence['visible_entries']:timeline(entry)
    assert after==before,(filename,'Unqualified prior-output change',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),**counts,
        all_other_fields_exact=True,current_mesh_normal_group_cache_and_warnings_exact=True,
        prior_operations_BaseMesh_partial_definitions_ASM_and_placement_exact=True,
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
    check_manifest(before);check_manifest(current)
    reports={name:goldens(name) for name in [spec[1] for spec in SPECS]+['mesh-repair-geometry-decoding.json']}
    rows=[compare(old,new,name,reports) for name,old,new in zip(FILES,before,current)]
    totals={key:sum(row[key] for row in rows) for key,value in rows[0].items() if type(value) is int}
    assert totals['MeshRepair']==3 and totals['operation_tool_additions']==3
    assert all(old==new for old,new in zip(before[:43],current[:43])), 'Previous43 complete outputs changed'
    evidence=['validate_mesh_repair_integration.py','decode_basics.py','decode_mesh_repair.py',
        'validate_mesh_repair_geometry.py','decode_mesh_contents.py','decode_mesh_geometry_variants.py',
        'decode_mesh_normals.py','decode_mesh_face_group_caches.py','decode_retained_mesh_sources.py']+list(reports)
    return dict(scope='46 fixed cached main outputs against87487cc; only three report-qualified positive MeshRepair classifications restored before exact comparison',
        baseline_commit=BASELINE,files=list(FILES),samples=rows,
        inputs=dict(baseline_cache_sha256=sha(baseline_path),current_cache_sha256=sha(current_path),manifest_sha256=sha(manifest_path),
            baseline_output_set_sha256=canonical(before),current_output_set_sha256=canonical(current)),
        summary=dict(saved_files=46,legacy_complete_output_controls=43,**totals,
            unqualified_output_changes=0,ASM_changes=0,placement_changes=0,full_main_runs=0,live_API_calls=0),
        evidence_sha256={name:sha(ROOT/name) for name in evidence},
        limitations=['New operation settings retain their own source/current/retained selection scopes; no visibility or lifecycle replay inferred.',
            'All prior current-reader warnings and preparatory operation diagnostics remain exact; successful Repair does not qualify historical/source lifecycle semantics.',
            'Temporary face-group labels do not establish persistent topology identity or regenerate grouping algorithms.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-outputs',type=Path,default=Path('/private/tmp/fusion-mesh-repairs-baseline.json'))
    parser.add_argument('--current-outputs',type=Path,default=Path('/private/tmp/fusion-mesh-repairs-current.json'))
    parser.add_argument('--files',type=Path,default=Path('/private/tmp/fusion-mesh-repairs-files.json'))
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-repair-integration.json')
    args=parser.parse_args();report=validate(args.baseline_outputs,args.current_outputs,args.files)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
