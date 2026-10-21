"""Main-reader geometry integration with explicit prior-output boundaries."""

import copy
import json
from pathlib import Path

from decode_basics import decode_basics
from validate_history_cache_integration import baseline_outputs

ROOT = Path(__file__).resolve().parent
FILES = (
    'solidsweeps-5b5ecd5e01b9/solid_twist_sixty.f3d',
    'solidsweeps-7d2677669e3d/solid_twist.f3d',
    'embosstext-cd769aa41cdf/two_texts.f3d',
    'specialfillets-d50f7a4f04e0/rule_asymmetric.f3d',
    'tappedholes-409e96788503/modeled_full.f3d',
    'lofts-03b4a6f1ce2f/centerline.f3d',
    'sweeps-5f87eff25e24/line_twist.f3d',
    'pipeedgecontrasts-5bd287323ae7/line_full.f3d',
    'edgemodes-52695761f185/fillet_curvature.f3d',
    'bodymodes-df9b7113539f/scale_uniform.f3d',
    'sweepguides-9887de71bf9e/rail_scale.f3d',
    'solidsweeps-7d2677669e3d/solid_aligned.f3d',
    'pipepaths-3d11bd427946/spline_circular.f3d',
)


def topology_structure(graph):
    value = copy.deepcopy(graph)
    for key in ('spline_curves', 'spline_surfaces', 'analytic_surfaces'):
        value.pop(key)
    for loop in value['face_trim_loops']:
        loop.pop('uv_endpoints_close_in_this_chart')
        for trim in loop['trims']:
            trim.pop('uv_curve')
    return value


def validate(zstd):
    baseline = baseline_outputs(FILES, zstd, revision='0f97d1d')
    rows, old_failures, remaining, new_uv = [], 0, 0, 0
    for filename, before in zip(FILES, baseline):
        after = json.loads(json.dumps(decode_basics(ROOT/filename, zstd)))
        # Parameters, constraints, feature controls, body joins/placement and
        # context/source diagnostics must remain identical outside ASM geometry.
        a, b = copy.deepcopy(before), copy.deepcopy(after)
        a.pop('asm_decoding'); b.pop('asm_decoding')
        assert a == b, (filename, 'Non-ASM output changed')
        old_streams = {s['member']: s for s in before['asm_decoding']['streams']}
        streams = {s['member']: s for s in after['asm_decoding']['streams']}
        assert old_streams.keys() == streams.keys()
        stream_rows = []
        for member, current in streams.items():
            previous = old_streams[member]
            a, b = copy.deepcopy(previous), copy.deepcopy(current)
            old_topology, topology = a.pop('topology'), b.pop('topology')
            namespace = b.pop('inline_subtypes', None)
            assert a == b, (filename, member, 'Framing or metadata changed')
            if namespace:
                assert not namespace['unresolved'], (filename, member, 'Namespace unresolved')
            old_keys = {(e.get('kind'), e.get('index')) for e in old_topology['unresolved']}
            current_keys = {(e.get('kind'), e.get('index')) for e in topology['unresolved']}
            assert current_keys <= old_keys, (filename, member, 'New geometry rejection')
            old_graphs = {g['body_index']: g for g in old_topology['body_graphs']}
            graphs = {g['body_index']: g for g in topology['body_graphs']}
            assert old_graphs.keys() == graphs.keys(), (filename, member, 'Stored BODY graph roots changed')
            decoded_uv = 0
            for body_id, graph in graphs.items():
                prior = old_graphs[body_id]
                assert topology_structure(graph) == topology_structure(prior)
                for field, key in (('spline_curves', 'curve_index'), ('spline_surfaces', 'surface_index')):
                    current_caches = {row[key]: row for row in graph[field]}
                    for old_cache in prior[field]:
                        assert current_caches[old_cache[key]] == old_cache
                for old_loop, loop in zip(prior['face_trim_loops'], graph['face_trim_loops']):
                    for old_trim, trim in zip(old_loop['trims'], loop['trims']):
                        if old_trim['uv_curve'] is not None:
                            assert trim['uv_curve'] == old_trim['uv_curve']
                        elif trim['uv_curve'] is not None:
                            decoded_uv += 1
                new_surfaces = {row['surface_index'] for row in graph['spline_surfaces']}
                assert len(prior['analytic_surfaces']) == len(graph['analytic_surfaces'])
                for old_surface, surface in zip(prior['analytic_surfaces'], graph['analytic_surfaces']):
                    old_status = old_surface.get('geometry_status')
                    new_status = surface.get('geometry_status')
                    left, right = dict(old_surface), dict(surface)
                    left.pop('geometry_status', None); right.pop('geometry_status', None)
                    assert left == right
                    if old_status != new_status:
                        assert surface['surface_index'] in new_surfaces
            old_failures += len(old_topology['unresolved'])
            remaining += len(topology['unresolved'])
            new_uv += decoded_uv
            stream_rows.append({'member': member, 'original_geometry_rejections': len(old_topology['unresolved']),
                'remaining_geometry_rejections': topology['unresolved'], 'new_uv_trim_caches': decoded_uv,
                'qualified_inline_references': namespace['qualified_reference_count'] if namespace else 0,
                'initial_topology_structure_unchanged': True, 'prior_geometry_outputs_unchanged': True})
        rows.append({'file': filename, 'non_ASM_output_unchanged': True, 'streams': stream_rows})
    assert remaining < old_failures and new_uv > 0
    return {'scope': 'Thirteen saved main-reader cases at baseline0f97d1d; newly recovered cached geometry and subtype/UV links only, with unsupported geometry diagnostics retained',
            'baseline_commit': '0f97d1d', 'samples': rows,
            'summary': {'saved_files': len(FILES), 'prior_geometry_rejections': old_failures,
                        'remaining_geometry_rejections': remaining, 'new_uv_trim_caches': new_uv,
                        'non_ASM_output_changes': 0, 'new_API_calls': 0},
            'limitations': ['Counts concern these thirteen archives, not full-format completion.',
                           'No native writer, exact procedural geometry, general parameter remapping or history regeneration is established.']}


if __name__ == '__main__':
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result = validate(str(zstd))
    (ROOT/'parameter-namespace-integration.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
