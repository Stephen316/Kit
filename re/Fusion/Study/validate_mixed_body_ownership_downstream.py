"""Two independent native ownership→identifier→placement helper chains."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from asm_records import inspect_asm_members
from decode_assembly import decode_assembly
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_bindings import decode_body_bindings
from decode_body_placement import decode_body_placement
from decode_body_properties import decode_body_properties
from decode_body_selections import decode_body_selections
from decode_component_body_proxies import decode_component_body_proxies
from decode_historical_body_components import decode_historical_body_components
from decode_mixed_body_collections import decode_mixed_body_collections
from decode_sketch import reference
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
CAPTURE = 'meshconvertoperations-5af73924aa60'
FILES = (CAPTURE+'/base_feature_closed.f3d', CAPTURE+'/base_feature_open.f3d')


def validate(root, zstd):
    truth_path = root/CAPTURE/'ground_truth.json'
    truth = json.loads(truth_path.read_text())
    report = dict(scope='Independent native mixed BODY ownership, explicit same-blob BODY identifier and stored root-component placement chains; no API identity or current lifecycle inference',
        derivation='Fresh raw assembly, body properties and ASM inspections; direct helper composition only. Current main output is neither read nor used as a golden.',
        ground_truth_sha256=hashlib.sha256(truth_path.read_bytes()).hexdigest(),
        samples=[], reused_guard_evidence=[dict(report=name,
            sha256=hashlib.sha256((root/name).read_bytes()).hexdigest(),
            scope='Existing recorded malformed-reference controls; not rerun by this two-file positive derivation')
            for name in ('body-asm-identifier-decoding.json', 'mixed-empty-body-mapping-decoding.json')],
        source_sha256={name: hashlib.sha256((root/name).read_bytes()).hexdigest()
            for name in ('decode_assembly.py', 'decode_body_properties.py', 'decode_mixed_body_collections.py',
                'decode_body_selections.py', 'decode_component_body_proxies.py', 'decode_body_bindings.py',
                'decode_body_asm_identifiers.py', 'decode_historical_body_components.py',
                'decode_body_placement.py', 'asm_records.py', 'decode_brep.py',
                'validate_mixed_body_ownership_downstream.py')})
    for archive in FILES:
        data, records, features, member, members = load(root, archive, zstd)
        assembly = decode_assembly(data, records, copy.deepcopy(features))
        assert not assembly['unresolved']
        properties = decode_body_properties(data, records, assembly)
        old_properties = copy.deepcopy(properties)
        mixed = decode_mixed_body_collections(data, records, assembly, properties)
        assert not mixed['unresolved'] and len(mixed['decoded']) == 2
        patches = [p for row in mixed['decoded'] for p in row['body_ownership_updates']]
        assert {p['object_id'] for p in patches} == {306, 312}
        properties['collections'].extend(row['collection'] for row in mixed['decoded'])
        for body in properties['bodies']:
            patch = next(p for p in patches if p['object_id'] == body['object_id'])
            body.update(patch)
            body.pop('ownership_status', None)
        properties['unresolved'] = [e for e in properties['unresolved']
            if e['kind'] != 'BodyCollection' or e['object_id'] not in {7, 22}]
        assert not properties['unresolved']
        primary = {r.object_id: r for r in records if r.is_primary}
        for identity, owner in ((306, 22), (312, 7)):
            native = primary[identity]
            assert reference(data, native.end-11) == owner
            qualified = next(row for row in mixed['decoded'] if row['object_id'] == owner)
            assert qualified['body_member_object_ids'] == [identity]
            assert qualified['component_object_id'] == 3

        selections = decode_body_selections(data, records, properties)
        proxies = decode_component_body_proxies(data, records, selections, assembly)
        assert not proxies['decoded'] and not proxies['unresolved']
        selections['component_context_scope'] = proxies['scope']
        assert len(selections['body_anchors']) == 1 and not selections['unresolved']
        anchor = selections['body_anchors'][0]
        assert anchor['native_body_object_id'] == 312 and anchor['source_owner_object_id'] == 300
        assert anchor['body_properties']['collection_object_id'] == 7
        assert anchor['body_properties']['component_object_id'] == 3

        asm = inspect_asm_members(members)
        bindings = decode_body_bindings(data, records, member, asm, properties)
        assert not bindings['unresolved'] and len(bindings['decoded']) == 1
        identifiers = decode_body_asm_identifiers(data, records, member, members, bindings)
        assert not identifiers['unresolved'] and len(identifiers['decoded']) == 1
        mapping = bindings['decoded'][0]
        identified = identifiers['decoded'][0]
        assert mapping['mapping_record_object_id'] == 8 and mapping['owner_object_id'] == 7
        assert mapping['body_count'] == 1 and len(mapping['bindings']) == 1
        binding = mapping['bindings'][0]
        patch = identified['bindings'][0]
        assert binding['native_body_object_id'] == patch['native_body_object_id'] == 312
        assert binding['stored_handle'] == patch['asm_stored_entity_id']
        assert binding['component_object_id'] == 3 and patch['asm_body_index'] == 1
        binding.pop('candidate_asm_body_index', None)
        binding.update(patch)
        binding['handle_scope'] = binding['identifier_scope']
        mapping['scope'] = 'Explicit native body/blob mapping; only validated same-blob typed BODY identifier joins supply ASM roots'
        bindings['scope'] = 'Native body/blob mapping and observed typed per-blob BODY identifiers; final-body lifecycle unresolved'
        historical = decode_historical_body_components(data, records, bindings, assembly)
        assert historical['decoded'] == [] and historical['unresolved'] == []
        assert historical['already_owned_body_bindings_unchanged'] == 1
        placement = decode_body_placement(bindings, assembly, asm)
        assert not placement['unresolved'] and len(placement['bodies']) == 1
        placed = placement['bodies'][0]
        assert placed['native_body_object_id'] == 312 and placed['component_object_id'] == 3
        assert len(placed['placements']) == 1 and placed['placements'][0]['path'] == ''
        frame = placed['placements'][0]['component_to_world_matrix']
        assert frame == [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]
        graph = next(g for s in asm['streams'] if s['member'] == mapping['history_blob_member']
                     for g in s['topology']['body_graphs'] if g['body_index'] == 1)
        assert graph['body_transform_is_identity'] and graph['counts']['vertex'] == 4
        assert placed['component_vertex_positions_cm'] == graph['raw_vertex_positions']
        assert placed['placements'][0]['world_vertex_positions_cm'] == graph['raw_vertex_positions']
        actual = next(s for s in truth['samples'] if s['file'] == Path(archive).name)
        bodies = actual['component_brep_after_convert']['bodies']
        assert len(bodies) == 1
        api = bodies[0]
        points = placed['component_vertex_positions_cm']
        API_points = [v['position_cm'] for v in api['vertices']]
        assert sorted(points) == sorted(API_points)
        bounds = dict(min=[min(p[i] for p in points) for i in range(3)],
                      max=[max(p[i] for p in points) for i in range(3)])
        assert bounds == api['bounding_box_cm']
        derived_volume = None
        if graph['counts']['face'] == 4:
            p, q, r, s = points
            a, b, c = ([q[i]-p[i] for i in range(3)], [r[i]-p[i] for i in range(3)], [s[i]-p[i] for i in range(3)])
            derived_volume = abs(sum(a[i]*(b[(i+1)%3]*c[(i+2)%3]-b[(i+2)%3]*c[(i+1)%3]) for i in range(3)))/6
            assert api['isSolid'] and math.isclose(derived_volume, api['volume'], abs_tol=1e-12)
        else:
            assert graph['counts']['face'] == 3 and not api['isSolid'] and api['volume'] is None
        report['samples'].append(dict(archive=archive,
            archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),
            expected_body_selections=selections, expected_body_blob_bindings=bindings,
            expected_historical_body_components=historical, expected_body_placement=placement,
            exact_A_ownership_patches=patches,
            unchanged_name_fields=[dict(object_id=b['object_id'], name=b['name'], name_status=b['name_status'])
                                   for b in old_properties['bodies']],
            native_route=dict(anchor_object_id=anchor['object_id'], owner_feature_object_id=300,
                selected_result_BODY=312, ordinary_collection=7, separate_table_BODY=306,
                separate_table_collection=22, component_object_id=3, mapping_object_id=8,
                stored_handle=binding['stored_handle'],
                ASM_BODY_stored_entity_ID=patch['asm_stored_entity_id'], ASM_record_index=1,
                body_transform_identity=True, stored_root_component_frame=frame),
            API_geometry_corroboration=dict(native_API_identity_assignment=None,
                complete_vertex_set_exact=True, bounding_box_cm=bounds,
                API_isSolid=api['isSolid'], derived_closed_tetra_volume_cm3=derived_volume,
                actual_API_volume_cm3=api['volume'], scope='Unique result collection geometry corroboration; no API entity identity assigned')))
    report['summary'] = dict(focused_files=2, typed_BODY_ownership_patches=4,
        qualified_anchor_binding_placement_chains=2, API_geometry_corroborations=2,
        main_runs=0, live_calls=0, current_main_used_as_golden=False)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--zstd-library', required=True)
    parser.add_argument('--output', type=Path, default=ROOT/'mixed-body-ownership-downstream-decoding.json')
    args = parser.parse_args()
    report = validate(args.root.resolve(), args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps(report['summary']))
