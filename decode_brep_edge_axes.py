"""Captured BRep-edge construction axes with separately stored native geometry.

This promotes the already observed edge-source schema to construction features.
Axis line caches do not identify the selected ASM edge or regenerate its curve.
"""

import math
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_parameters import read_string
from decode_selection import known_construction_entities
from decode_silhouette_directions import AXIS_FEATURE, AXIS_GEOMETRY, resolve_silhouette_direction
from decode_sketch import attributes, numbers, reference


SCOPE = 'Observed variant4/method8 BRep-edge ConstructionAxis definition with explicit owned edge recipe and independently stored finite native line geometry; persistent edge mapping and construction regeneration unresolved'


def decode_brep_edge_axes(data, records, features, body_selections=None):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('BRep-axis typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    definitions, unresolved = [], []
    bodies, known = body_selections, None
    for feature in features:
        if feature['kind'] != 'ConstructionAxis' or feature['class_guid'] != AXIS_FEATURE:
            continue
        owner = feature['object_id']
        try:
            record, payload = typed(owner, AXIS_FEATURE)
            if payload[:6] != bytes.fromhex('000004000000'):
                continue
            backend_id = reference(payload, 17)
            _, backend = typed(backend_id, 'F2A7590D-6654-4674-B393-A2AEF4FEC48A')
            if len(backend) < 74 or struct.unpack_from('<I', backend, 70)[0] != 8:
                continue  # Existing sketch-line Edge method10 remains unchanged.
            if (record.start != feature['record_offset'] or feature['parameters'] or len(payload) != 236
                    or payload[28] != 1 or payload[105:112] != bytes.fromhex('00000002000000')
                    or reference(payload, 112) != backend_id):
                raise ValueError('Unobserved BRep-edge axis feature framing/parameters')
            namespace, cursor = read_string(payload, 29)
            label, label_end = read_string(payload, 138)
            if (namespace != str(uuid.UUID(int=0)) or cursor != 105 or label != 'WorkAxis'
                    or struct.unpack_from('<Q', payload, label_end)[0] != feature['stored_index']):
                raise ValueError('BRep-axis feature metadata/index changed')
            axis_id, descriptor_id = reference(payload, 6), reference(payload, 123)
            native_record, native = typed(axis_id, AXIS_GEOMETRY)
            props, cursor = attributes(native, 2)
            if native[:2] != b'\0\1' or props != {'EntityGenesis': 0} or cursor != 58:
                raise ValueError('Unobserved BRep-axis native geometry attributes')
            origin, raw = numbers(native, cursor, 3), numbers(native, cursor+24, 3)
            length = math.sqrt(sum(v*v for v in raw))
            if not math.isfinite(length) or length <= 1e-12:
                raise ValueError('Degenerate or nonfinite native axis vector')
            _, end = read_string(native, cursor+64)
            collection_id = reference(native, end)
            if (struct.unpack_from('<Q', native, end+11)[0] != feature['stored_index']
                    or native[end+19] != 0 or reference(native, end+20) != owner
                    or native[end+31:end+33] != b'\0\1' or reference(native, len(native)-11) != collection_id):
                raise ValueError('BRep-axis native geometry/feature/collection ownership disagrees')
            name, name_end = read_string(native, end+33)
            if feature.get('name') is not None and (name or None) != feature['name']:
                raise ValueError('BRep-axis native and feature names disagree')
            _, collection = typed(collection_id, 'A8635B5F-1E2C-45FD-8BA9-0173B0FEB75E')
            if (len(collection) != 73 or collection[:6] != bytes.fromhex('000001000000')
                    or reference(collection, 6) != axis_id or struct.unpack_from('<I', collection, 47)[0] != 1
                    or reference(collection, 51) != axis_id):
                raise ValueError('BRep-axis collection repeated native membership disagrees')
            component_id = reference(collection, 62)
            typed(component_id, 'E03784ED-5E19-4E14-B9F2-3B07017018CD')
            if bodies is None:
                bodies = decode_body_selections(data, records)
            if known is None:
                known = known_construction_entities(data, records, features)
            source = resolve_silhouette_direction(data, records, features, backend_id, descriptor_id, owner, bodies, known)
            if source['stored_direction_method_code'] != 8 or source['entity']['kind'] != 'BRepEdge':
                raise ValueError('Construction axis source is not the captured owned BRep edge')
            geometry = {'name': name or None, 'axis_object_id': axis_id, 'geometry_record_offset': native_record.start,
                        'axis_collection_object_id': collection_id, 'component_object_id': component_id,
                        'origin_cm': origin, 'direction': [v/length for v in raw], 'stored_raw_direction': raw,
                        'coordinate_units': 'cm', 'coordinate_scope': 'Native component; occurrence transforms are not inferred',
                        'direction_encoding': 'Normalized finite native line vector; raw scale is not interpreted as a trimmed edge length'}
            definitions.append({'feature_object_id': owner, 'kind': 'ConstructionAxis', 'name': name or None,
                                'definition_kind': 'Edge', 'api_definition_class': 'ConstructionAxisEdgeDefinition',
                                'stored_feature_variant_code': 4, 'stored_backend_method_code': 8,
                                'backend_object_id': backend_id,
                                'support_inputs': [{'role': 'edgeEntity', **source}], 'cached_geometry': geometry,
                                'support_consistency': {'matches': None, 'scope': 'Owned edge recipe/body provenance; axis cache is not substituted for selected edge evaluator geometry'},
                                'collection_opaque_middle_hex': collection[17:47].hex(),
                                'native_geometry_suffix_hex': native[name_end:].hex(), 'scope': SCOPE})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'feature_object_id': owner, 'kind': 'ConstructionAxis', 'reason': str(error)})
    return {'definitions': definitions, 'unresolved': unresolved, 'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    import copy
    import json
    from decode_basics import decode_basics
    from decode_sketch import same
    from fusion_archive import read_members
    from fusion_metadata import design_records

    archive = root/'silhouettedirections-805c2eaa2411/faces_custom_axis_x.f3d'
    truth = json.loads((archive.parent/'ground_truth.json').read_text())
    sample = next(s for s in truth['samples'] if s['file'] == archive.name)
    main = decode_basics(archive, zstd_library);stream = main['streams'][0]
    members = read_members(archive, zstd_library);data = members[stream['member']]
    records, _ = design_records(data, members.get(stream['member'].replace('BulkStream.dat', 'MetaStream.dat')))
    primary = {r.object_id: r for r in records if r.is_primary}
    result = decode_brep_edge_axes(data, records, stream['features'])
    assert len(result['definitions']) == 1 and not result['unresolved']
    definition = result['definitions'][0];geometry = definition['cached_geometry']
    actual = sample['actual_direction'];source = definition['support_inputs'][0]
    prop = next(b for b in stream['body_properties']['bodies'] if b['object_id'] == source['entity']['native_body_object_id'])
    checks = {'name_matches_actual_axis': geometry['name'] == actual['name'],
              'native_origin_matches_actual_axis': same(geometry['origin_cm'], actual['origin_cm']),
              'normalized_native_vector_matches_actual_axis': same(geometry['direction'], actual['direction']),
              'definition_class_matches_actual_axis': actual['definition_type'].endswith('::'+definition['api_definition_class']),
              'actual_definition_edge_is_linear_BRep': actual['definition_edge']['entity_type'].endswith('::BRepEdge') and actual['definition_edge']['geometry_type'].endswith('::Line3D'),
              'owned_source_body_name_matches_actual_definition_edge': prop['name'] == actual['definition_edge']['body']['name'],
              'raw_vector_remains_separate_from_unit_direction': not same(geometry['stored_raw_direction'], geometry['direction']),
              'selected_edge_geometry_stays_unresolved': source['entity']['source_geometry'] is None}
    assert all(checks.values()), checks
    axis_id = geometry['axis_object_id'];native_record = primary[axis_id]
    native = data[native_record.body:native_record.end]
    _, cursor = attributes(native, 2);_, end = read_string(native, cursor+64)
    backend_id = definition['backend_object_id']
    mutations = [('Native axis owner mismatch', axis_id, end+21, struct.pack('<Q', 999999)),
                 ('Repeated backend reference mismatch', definition['feature_object_id'], 113, struct.pack('<Q', 999999)),
                 ('Degenerate cached axis vector', axis_id, cursor+24, bytes(24)),
                 ('Unobserved defining edge count', backend_id, 99, struct.pack('<I', 2)),
                 ('Repeated axis collection member mismatch', geometry['axis_collection_object_id'], 52, struct.pack('<Q', 999999))]
    guards = []
    for label, identity, offset, replacement in mutations:
        r = primary[identity];changed = bytearray(data)
        changed[r.body+offset:r.body+offset+len(replacement)] = replacement
        rejected = decode_brep_edge_axes(bytes(changed), records, copy.deepcopy(stream['features']))
        assert not rejected['definitions'] and rejected['unresolved'], label
        guards.append({'check': label, 'rejected': True, 'reason': rejected['unresolved'][0]['reason']})
    changed = bytearray(data);backend = primary[backend_id]
    changed[backend.body+6:backend.body+30] = struct.pack('<ddd', 123., 456., 789.)
    cache_control = decode_brep_edge_axes(bytes(changed), records, copy.deepcopy(stream['features']))
    assert cache_control['definitions'][0]['cached_geometry'] == geometry
    assert cache_control['definitions'][0]['support_inputs'][0]['stored_control_cache']['origin_cm'] == [123., 456., 789.]
    previous = []
    for name in ('axis_edge', 'axis_two_points'):
        candidate = root/'constructionmodes-e355ad6031c0'/(name+'.f3d')
        assert candidate.is_file(), candidate
        control = decode_basics(candidate, zstd_library)['streams'][0]
        contents = read_members(candidate, zstd_library);raw = contents[control['member']]
        rs, _ = design_records(raw, contents.get(control['member'].replace('BulkStream.dat', 'MetaStream.dat')))
        no_op = decode_brep_edge_axes(raw, rs, control['features'])
        assert not no_op['definitions'] and not no_op['unresolved']
        previous.append(str(candidate.relative_to(root)))
    return {'archive': str(archive.relative_to(root)), 'checks': checks, 'expected_summary': result,
            'negative_checks': guards, 'cache_separation_control': True, 'prior_no_op_controls': previous,
            'api_evidence_scope': 'One captured actual axis origin/direction/name/definition class and defining BRep edge/body; generic construction is not regenerated.',
            'limitations': ['Only variant4/method8 is added; earlier sketch-line Edge method10 stays with its existing reader.',
                            'Finite native line vectors are normalized while raw values remain; raw vector scale is not a general edge length.',
                            'Axis cache is independent of control previews and never establishes persistent source-edge geometry or identity.']}


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate', action='store_true', required=True)
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('brep-edge-axis-decoding.json'))
    args = parser.parse_args()
    report = validate_fixtures(Path(__file__).resolve().parent, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'API_checks': len(report['checks']), 'negative_checks': len(report['negative_checks'])}))
