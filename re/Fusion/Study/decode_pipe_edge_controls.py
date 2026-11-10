"""Bounded Pipe BRep source/extent evidence, separate from full tool settings.

Five actual edge contrasts prove AgainstDistance -> API distanceOne. They do not
provide independently decoded edge closure/geometry; optional point-selector
presence and a topology descriptor bit are preserved without closure semantics.
"""

import argparse
import json
import math
from pathlib import Path
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import RECIPE_GUID, decode_recipe
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import numbers, reference, same

PIPE = '73615646-8752-4EE6-AD02-0B90804B7CD7'
TOPOLOGY = '5662F619-2281-4AD9-93DC-1FCFDA1062E7'


def inspect_pipe_edge_controls(data, records, body, feature, features):
    """Return separate provenance/controls only; never claim full Pipe settings."""
    if (feature['class_guid'] != PIPE or len(body) < 94 or body[:7] != bytes.fromhex('00010000000000')
            or struct.unpack_from('<I', body, 7)[0] != 4 or body[11:13] != b'\0\1'
            or body[68] not in (0, 1)):
        raise ValueError('Unsupported edge Pipe header')
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {i: items[0] for i, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Pipe edge typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    def topology(identity, expected_kind):
        _, payload = typed(identity, TOPOLOGY)
        if (len(payload) != 276 or payload[:3] != bytes(3) or payload[3] not in (0, 1)
                or struct.unpack_from('<I', payload, 15)[0] != 1
                or reference(payload, 265) != feature['object_id']):
            raise ValueError('Pipe topology descriptor prefix/count/owner mismatch')
        record, _ = typed(reference(payload, 4), RECIPE_GUID)
        recipe = decode_recipe(data, record, primary)
        if recipe['payload_kind'] != expected_kind:
            raise ValueError('Pipe source recipe kind mismatch')
        return payload, recipe

    has_point = bool(body[68])
    path_offset = 79 if has_point else 69
    if struct.unpack_from('<I', body, path_offset+11)[0] != 0:
        raise ValueError('Only captured circular-section solid BRep Pipes supported')
    path_id = reference(body, path_offset)
    proxy_record, proxy = typed(path_id, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    identities, properties = native_proxy_references(data, proxy_record)
    if properties or len(identities) != 1 or reference(proxy, len(proxy)-11) != feature['object_id']:
        raise ValueError('Pipe edge proxy must contain one owned descriptor')
    descriptor_id = identities[0]
    descriptor, recipe = topology(descriptor_id, 'edge_recipe_data')
    namespace, cursor = read_string(descriptor, 19)
    entity, cursor = read_string(descriptor, cursor)
    uuid.UUID(namespace)
    uuid.UUID(entity)
    if cursor != 171 or descriptor[cursor:cursor+12] != struct.pack('<QI', 2, 1):
        raise ValueError('Unobserved Pipe edge context list')
    context_id = reference(descriptor, cursor+12)
    _, context = typed(context_id, 'C46D3EEB-40E1-43FA-83DC-9CB204335417')
    if len(context) != 181 or context[:10] != bytes(2)+struct.pack('<Q', 4):
        raise ValueError('Unobserved Pipe source context framing')
    context_namespace, end = read_string(context, 10)
    context_entity, end = read_string(context, end)
    if (context_namespace != namespace or context_entity != entity or end != 162
            or context[end:end+8] != struct.pack('<Q', 2)):
        raise ValueError('Pipe context UUID/source correspondence mismatch')
    wrapper_id = reference(context, 170)
    _, wrapper = typed(wrapper_id, '4B31DA1B-FCD6-4527-BC3E-BE1FBAF867FE')
    if len(wrapper) != 14 or wrapper[:2] != bytes(2) or wrapper[-1:] != b'\0':
        raise ValueError('Unobserved Pipe context recipe wrapper')
    context_recipe_record, _ = typed(reference(wrapper, 2), RECIPE_GUID)
    context_recipe = decode_recipe(data, context_recipe_record, primary)
    if context_recipe['payload_kind'] != 'edge_recipe_data':
        raise ValueError('Pipe context requires edge recipe')
    if struct.unpack_from('<I', descriptor, 194)[0] != 1:
        raise ValueError('Unobserved Pipe historical body anchor count')
    anchor_id = reference(descriptor, 198)
    anchors = [a for a in decode_body_selections(data, records)['body_anchors'] if a['object_id'] == anchor_id]
    if len(anchors) != 1:
        raise ValueError('Pipe historical body anchor unresolved')
    anchor = anchors[0]
    auxiliary = None
    if has_point:
        auxiliary_id = reference(body, 68)
        _, point_payload = typed(auxiliary_id, '69EE2FA7-BCC7-449E-9CA9-976CEFDFED44')
        if (len(point_payload) != 178 or point_payload[:23] != bytes(23)
                or struct.unpack_from('<I', point_payload, 47)[0] != 1
                or struct.unpack_from('<I', point_payload, 75)[0] != 1
                or reference(point_payload, 167) != feature['object_id']):
            raise ValueError('Pipe auxiliary point selection layout/count/owner mismatch')
        point_descriptor_id = reference(point_payload, 79)
        _, vertex_recipe = topology(point_descriptor_id, 'vertex_recipe_data')
        auxiliary = {'selection_object_id': auxiliary_id, 'descriptor_object_id': point_descriptor_id,
                     'stored_xyz_cm': numbers(point_payload, 23, 3), 'stored_method_code': 1,
                     'vertex_recipe': vertex_recipe,
                     'coordinate_scope': 'Stored point cache agrees with actual root-component source start vertex in captured open-line cases; exact Pipe role/persistent vertex identity unresolved'}
    bindings = {p['binding_object_id']: p for p in feature['parameters']}
    controls = {}
    for offset, role in ((13, 'AgainstDistance'), (24, 'AlongDistance'), (46, 'SectionSize'), (57, 'SectionThickness')):
        identity = reference(body, offset)
        parameter = bindings.get(identity)
        if parameter is None or parameter['role'] != role or not math.isfinite(parameter['raw_float64']):
            raise ValueError('Pipe native parameter role/value mismatch')
        controls[role] = {'binding_object_id': identity, 'stored_value': parameter['raw_float64']}
    against, along, size, thickness = (controls[k]['stored_value'] for k in ('AgainstDistance', 'AlongDistance', 'SectionSize', 'SectionThickness'))
    if not (0 < against <= 1 and 0 <= along <= 1 and size > 0 and thickness == 0):
        raise ValueError('Unsupported captured solid Pipe control range')
    if has_point and not math.isclose(against, along, rel_tol=0, abs_tol=1e-12):
        raise ValueError('Observed populated-selector Pipe extent copies disagree')
    if not has_point and against+along > 1+1e-12:
        raise ValueError('Observed absent-selector Pipe extent sum exceeds one')
    return {'feature_object_id': feature['object_id'], 'feature_class_guid': PIPE,
            'status': 'PartialBRepSourceAndExtentEvidence',
            'tool_settings_status': 'Unresolved; separate provenance/control evidence only',
            'decoded_controls': {'operation': 'NewBody', 'stored_operation_code': 4,
                                 'section_type': 'Circular', 'stored_section_type_code': 0,
                                 'is_hollow': False, 'section_size_cm': size,
                                 'stored_section_thickness_cm': thickness,
                                 'active_section_thickness_cm': None},
            'native_has_auxiliary_point_selector': has_point,
            'native_parameter_controls': controls, 'distance_one_fraction': against,
            'distance_one_scope': 'AgainstDistance matches actual API distanceOne across full/partial open lines and full/two-sided closed circles; native role retained',
            'distance_two_fraction': None, 'distance_two_status': 'Closure-dependent API availability unresolved natively; AlongDistance preserved without universal API mapping',
            'path': {'kind': 'BRepEdgeRecipe', 'selection_object_id': path_id, 'descriptor_object_id': descriptor_id,
                     'descriptor_class_guid': TOPOLOGY, 'stored_descriptor_flag_byte3': descriptor[3],
                     'stored_descriptor_flag_scope': 'Opaque: value1 occurs for both open negative-direction line and closed circle',
                     'recipe': recipe, 'context_object_id': context_id, 'context_recipe_wrapper_object_id': wrapper_id,
                     'context_recipe': context_recipe, 'namespace_text': namespace, 'entity_guid_text': entity,
                     'body_anchor_object_id': anchor_id, 'native_body_object_id': anchor['native_body_object_id'],
                     'source_owner_object_id': anchor['source_owner_object_id'],
                     'is_closed': None, 'path_is_opposed_to_entity': None, 'curve_geometry': None,
                     'scope': 'Explicit owned recipes/context and historical body; persistent ASM edge mapping, closure and curve geometry unresolved'},
            'auxiliary_point_selection': auxiliary,
            'branch_evidence_scope': 'Selector populated in actual open-line captures and absent in actual closed-circle captures. This correlation is retained without asserting a general closure flag or reconstructing edge geometry.'}


def validate_fixtures(root, zstd_library):
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    folder = root/'pipeedgecontrasts-5bd287323ae7'
    truth = json.loads((folder/'ground_truth.json').read_text())
    assert (folder/'complete.txt').is_file() and not truth['errors'] and len(truth['samples']) == 5
    report = {'api_version': truth['fusion_version'], 'samples': [], 'negative_checks': [],
              'interface': 'inspect_pipe_edge_controls(data,records,body,feature,features): separate partial source/extent summary only; never full tool_settings',
              'validation_command': 'python3 decode_pipe_edge_controls.py --validate --zstd-library <local libzstd path>'}
    for sample in truth['samples']:
        assert not sample['getter_errors']
        archive = folder/sample['file']
        main = decode_basics(archive, zstd_library)
        stream = next(s for s in main['streams'] if any(f['kind'] == 'Pipe' for f in s['features']))
        features = stream['features']
        feature = next(f for f in features if f['kind'] == 'Pipe')
        members = read_members(archive, zstd_library)
        data = members[stream['member']]
        records, _ = design_records(data, members.get(stream['member'].replace('BulkStream.dat','MetaStream.dat')))
        by = {r.object_id: r for r in records if r.is_primary}
        record = by[feature['object_id']]
        result = inspect_pipe_edge_controls(data, records, data[record.body:record.end], feature, features)
        api = sample['settings']
        path, selected = result['path'], api['path']['members'][0]['source']
        properties = {b['object_id']: b for b in stream['body_properties']['bodies']}
        closed = api['path']['is_closed']
        controls = result['native_parameter_controls']
        checks = {'distance_one_matches_actual': same([result['distance_one_fraction']], [api['distance_one']]),
                  'operation_section_hollow_match_actual': api['operation'] == 3 and api['section_type'] == 0 and api['is_hollow'] is False,
                  'section_size_matches_actual': same([controls['SectionSize']['stored_value']], [api['section_size_cm']]),
                  'stored_thickness_matches_actual': same([controls['SectionThickness']['stored_value']], [api['section_thickness_cm']]),
                  'body_name_matches_independent_actual': properties[path['native_body_object_id']]['name'] == selected['body_name'],
                  'native_closure_geometry_and_distance_two_remain_unknown': path['is_closed'] is None and path['curve_geometry'] is None and result['distance_two_fraction'] is None,
                  'actual_api_closedness_contrasts_selector_presence': result['native_has_auxiliary_point_selector'] is (not closed),
                  'context_contains_second_edge_recipe_not_curve_geometry': path['context_recipe']['payload_kind'] == 'edge_recipe_data'}
        if closed:
            checks['stored_along_matches_actual_active_distance_two'] = same([controls['AlongDistance']['stored_value']], [api['distance_two']])
            checks['actual_circle_geometry'] = selected['natural_geometry']['geometry_type'] == 'adsk::core::Circle3D'
        else:
            checks['open_along_is_copy_and_actual_distance_two_null'] = same([controls['AlongDistance']['stored_value']], [api['distance_one']]) and api['distance_two'] is None
            checks['stored_point_cache_matches_actual_source_start_vertex'] = same(result['auxiliary_point_selection']['stored_xyz_cm'], selected['start_vertex']['point_cm'])
        assert all(checks.values()), (sample['file'], checks)
        report['samples'].append({'archive': str(archive.relative_to(root)), 'status': 'PartialProvenanceAndControls',
                                  'checks': checks, 'partial': result, 'actual_api_settings': api})
        if sample['case'] == 'line_offset_negative_partial':
            negative_case = data, records, features, feature, record, by, result
    data, records, features, feature, record, by, result = negative_case
    descriptor = by[result['path']['descriptor_object_id']]
    context = by[result['path']['context_object_id']]
    auxiliary = by[result['auxiliary_point_selection']['selection_object_id']]
    recipe = by[result['path']['recipe']['object_id']]
    marker = data.index(b'edge_recipe_data', recipe.body, recipe.end)
    mutations = [('Descriptor wrong owner', descriptor.body+266, struct.pack('<Q', 999999)),
                 ('Context UUID/source mismatch', context.body+14, b'Z\0'),
                 ('Auxiliary wrong owner', auxiliary.body+168, struct.pack('<Q', 999999)),
                 ('Wrong edge recipe kind', marker, b'xxxx_recipe_data')]
    for label, offset, replacement in mutations:
        changed = bytearray(data)
        changed[offset:offset+len(replacement)] = replacement
        try:
            inspect_pipe_edge_controls(bytes(changed), records, data[record.body:record.end], feature, features)
        except (ValueError, KeyError, struct.error) as error:
            report['negative_checks'].append({'check': label, 'passed': True, 'reason': str(error)})
        else:
            raise AssertionError(label)
    flags = {s['archive'].split('/')[-1]: {'native_descriptor_byte3': s['partial']['path']['stored_descriptor_flag_byte3'],
                                         'actual_api_closed': s['actual_api_settings']['path']['is_closed']} for s in report['samples']}
    assert flags['line_offset_negative_partial.f3d']['native_descriptor_byte3'] == flags['circle_full.f3d']['native_descriptor_byte3'] == 1
    assert not flags['line_offset_negative_partial.f3d']['actual_api_closed'] and flags['circle_full.f3d']['actual_api_closed']
    report['closure_flag_counterexample'] = flags
    report['limitations'] = ['No full Pipe settings accepted from topology recipes: native closure/curve geometry and persistent ASM identity remain unresolved.',
                             'Auxiliary selector presence correlates with actual closure in these cases, but no general closure bit is established.',
                             'AgainstDistance is now independently contrasted across open/closed full/partial cases; AlongDistance remains raw in production because API availability depends on unresolved closure.',
                             'Root-component solid circular NewBody only; hollow/other sections, occurrence contexts, opposed flags and regeneration are outside these contrasts.']
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate', required=True, action='store_true')
    parser.add_argument('--zstd-library', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('pipe-edge-control-decoding.json'))
    args = parser.parse_args()
    report = validate_fixtures(Path(__file__).resolve().parent, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'partial_samples': len(report['samples']), 'negative_checks': len(report['negative_checks']), 'output': str(args.output)}))
