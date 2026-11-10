"""Explicit auxiliary Pipe vertex-context/body joins, without closure inference."""
import math
import struct

from decode_body_selections import ANCHOR, HELPER, SUPPORT
from decode_pipe_edge_controls import PIPE, TOPOLOGY, inspect_pipe_edge_controls
from decode_sketch import numbers, reference, same

VERTEX_CONTEXT = '994C518A-A831-400A-B7C7-16DAC55F4F1C'
SCOPE = 'Typed auxiliary vertex descriptor/context cache with reciprocal support and shared historical path body; Pipe role, edge geometry, closure and persistent vertex identity unresolved'


def inspect_pipe_auxiliary_vertex_context(data, records, body, feature, features, *, source_evidence=None):
    """Return additional provenance only; never supplies full Pipe tool_settings.

    source_evidence may be the existing inspect_pipe_edge_controls result from
    this same input. It avoids repeating that independently guarded pass.
    """
    source = source_evidence if source_evidence is not None else inspect_pipe_edge_controls(data, records, body, feature, features)
    if (feature['class_guid'] != PIPE or source['feature_object_id'] != feature['object_id']
            or source['feature_class_guid'] != PIPE or not source['native_has_auxiliary_point_selector']
            or source['auxiliary_point_selection'] is None):
        raise ValueError('No captured populated Pipe auxiliary vertex selector')
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Pipe vertex-context typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    owner = feature['object_id']
    auxiliary = source['auxiliary_point_selection']
    selection_id = auxiliary['selection_object_id']
    _, selection = typed(selection_id, '69EE2FA7-BCC7-449E-9CA9-976CEFDFED44')
    if (len(body) < 94 or body[68] != 1 or reference(body, 68) != selection_id
            or len(selection) != 178 or selection[:23] != bytes(23)
            or struct.unpack_from('<I', selection, 47)[0] != 1
            or struct.unpack_from('<I', selection, 75)[0] != 1 or reference(selection, 167) != owner):
        raise ValueError('Pipe vertex-context feature/selector count or owner disagrees')
    descriptor_id = reference(selection, 79)
    _, descriptor = typed(descriptor_id, TOPOLOGY)
    if (len(descriptor) != 276 or descriptor[:4] != bytes(4)
            or struct.unpack_from('<I', descriptor, 15)[0] != 1
            or descriptor[171:183] != struct.pack('<QI', 2, 1)
            or struct.unpack_from('<I', descriptor, 194)[0] != 1
            or reference(descriptor, 265) != owner or descriptor_id != auxiliary['descriptor_object_id']
            or reference(descriptor, 4) != auxiliary['vertex_recipe']['object_id']
            or auxiliary['vertex_recipe']['payload_kind'] != 'vertex_recipe_data'):
        raise ValueError('Pipe auxiliary vertex descriptor framing/recipe/owner disagrees')
    path = source['path']
    _, path_descriptor = typed(path['descriptor_object_id'], TOPOLOGY)
    if (len(path_descriptor) != 276 or reference(path_descriptor, 265) != owner
            or descriptor[19:171] != path_descriptor[19:171]):
        raise ValueError('Pipe path/auxiliary vertex namespace pair disagrees')
    anchor_id = reference(descriptor, 198)
    _, anchor = typed(anchor_id, ANCHOR)
    if (anchor_id != path['body_anchor_object_id'] or reference(path_descriptor, 198) != anchor_id
            or len(anchor) != 102 or anchor[:2] != bytes(2)
            or reference(anchor, 80) != path['native_body_object_id']
            or reference(anchor, 91) != path['source_owner_object_id']):
        raise ValueError('Pipe path/auxiliary vertex historical body correspondence disagrees')
    context_id = reference(descriptor, 183)
    _, context = typed(context_id, VERTEX_CONTEXT)
    if len(context) != 28 or context[:2] != bytes(2) or context[-2:] != b'\1\0':
        raise ValueError('Unobserved Pipe vertex context cache framing')
    position = numbers(context, 2, 3)
    if (not all(math.isfinite(value) for value in position)
            or not same(position, numbers(selection, 23, 3)) or not same(position, auxiliary['stored_xyz_cm'])):
        raise ValueError('Pipe vertex-context and auxiliary selector coordinate copies disagree')
    helper_id, support_id = reference(descriptor, 239), reference(descriptor, 253)
    _, helper = typed(helper_id, HELPER)
    _, support = typed(support_id, SUPPORT)
    if helper != bytes.fromhex('0001000000000000000000000000'):
        raise ValueError('Unobserved Pipe vertex-context helper framing')
    if (len(support) != 58 or support[:12] != bytes.fromhex('000000000000010101000000')
            or reference(support, 12) != path['source_owner_object_id']
            or reference(support, 31) != descriptor_id or support[-8:] != bytes(8)):
        raise ValueError('Pipe vertex-context reciprocal source/descriptor support disagrees')
    return {'feature_object_id': owner, 'selection_object_id': selection_id,
            'descriptor_object_id': descriptor_id, 'vertex_recipe_object_id': auxiliary['vertex_recipe']['object_id'],
            'context_object_id': context_id, 'context_class_guid': VERTEX_CONTEXT,
            'cached_position_cm': position, 'context_payload_hex': context.hex(),
            'namespace_text': path['namespace_text'], 'entity_guid_text': path['entity_guid_text'],
            'body_anchor_object_id': anchor_id, 'native_body_object_id': path['native_body_object_id'],
            'source_owner_object_id': path['source_owner_object_id'],
            'helper_object_id': helper_id, 'support_object_id': support_id,
            'support_payload_hex': support.hex(),
            'association': 'Owned Pipe selector -> owned vertex descriptor -> typed point-cache context; path and vertex share UUID pair and historical anchor; support reciprocates descriptor and historical source owner',
            'coordinate_scope': 'Stored cache copies in captured root-component coordinates; source recipe not evaluated',
            'tool_settings_status': 'Unresolved; this vertex-context join establishes neither edge closedness nor distanceTwo availability',
            'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    """Six actual BRep Pipe captures, four new joins and four malformed guards."""
    import hashlib
    import json
    from pathlib import Path
    from fusion_archive import read_members
    from fusion_metadata import design_records
    from decode_basics import attach_parameters, named_features
    from decode_parameters import decode_stream

    root = Path(root)
    folder = 'pipeedgecontrasts-5bd287323ae7'
    truth = json.loads((root/folder/'ground_truth.json').read_text())
    cases = [(folder+'/'+s['file'], s) for s in truth['samples']]
    other = 'pipepaths-3d11bd427946'
    cases += [(other+'/'+s['file'], s) for s in json.loads((root/other/'ground_truth.json').read_text())['samples'] if s['file'] == 'brep_edge_circular.f3d']
    report = {'scope': SCOPE, 'interface': 'inspect_pipe_auxiliary_vertex_context(data,records,body,feature,features,*,source_evidence=None)',
        'integration': 'Attach only successful additional result to existing partial Pipe auxiliary_point_selection; never clear full Pipe tool failures or set closure/distanceTwo from this result. Optional source_evidence reuses inspect_pipe_edge_controls output from identical inputs.',
        'framing': {'vertex_context': 'Typed994C record: zero16, three float64 cache coordinates, markers0100; exactly28 bytes.',
                    'joins': 'The69EE selector, vertex descriptor and path descriptor all own the same Pipe feature. Vertex/path descriptors repeat the same namespace/entity UUID pair and historical body anchor. Typed6CCF support references that vertex descriptor and the historical anchor source owner.',
                    'recipe_scope': 'Existing guarded vertex_recipe_data source identity reused; its integers are not promoted to native design/ASM identities.'},
        'samples': [], 'comparisons': [], 'malformed_guards': [],
        'closure_status': 'No new explicit source edge closure or natural curve geometry established; all six full Pipe settings failures remain unresolved.',
        'next_discriminating_controls': [
            {'case': 'Open semicircular BRep edge from an extruded sector', 'purpose': 'Contrast curved/open geometry against closed circular edges; separates line-vs-circle payload structure from actual topological closure. Capture natural and trimmed evaluator, Path.isClosed, start/end vertex identity, both Pipe distance getters and every owned context.'},
            {'case': 'Closed ellipse BRep edge from an extruded ellipse', 'purpose': 'Contrast closed non-circular geometry with current closed circle and open arc; seek a closure field independent of primitive geometry family.'},
            {'case': 'Two adjacent BRep line edges forming an open path, and an ordered four-edge closed rectangle', 'purpose': 'Contrast path-level closure with per-edge closure and optional selector presence. Capture ordered members/actual direction and returned vertex identities; do not infer closure from selector absence.'},
            {'case': 'Same open curved edge with reversed Path member direction, varied positive distanceOne', 'purpose': 'Distinguish source start vertex from Pipe start selection and path orientation; source-point cache matching current natural start vertex is insufficient to establish its general role.'}],
        'limitations': ['No source edge was identified inside ASM. Existing body/blob mapping remains distinct from recipe-to-edge identity.',
                        'Descriptor flag1 occurs on both the negative open line and closed circle. Optional selector presence correlates with closure only in this small corpus and is not decoded as closure.',
                        'Source context C46D181 stores namespaces and an edge-recipe route, not independently decoded natural edge geometry. Distinct edge recipe payload shapes are preserved without assigning closure semantics.',
                        'The original fixture filename brep_edge_circular.f3d uses a circular Pipe section on an actual open Line3D source, as confirmed by API truth. Filename is not a geometry discriminator.']}
    loaded = {}

    def check(label, actual, expected):
        assert actual == expected, (label, actual, expected)
        report['comparisons'].append({'label': label, 'actual': actual, 'expected': expected, 'passed': True})

    for filename, actual in cases:
        members = read_members(root/filename, zstd_library)
        member = next(name for name in members if name.endswith('FusionDesignSegmentType1/BulkStream.dat'))
        data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        features = named_features(data, records)
        parameters, _ = decode_stream(data, records)
        attach_parameters(data, records, features, parameters)
        feature = next(f for f in features if f['kind'] == 'Pipe')
        record = next(r for r in records if r.is_primary and r.object_id == feature['object_id'])
        body = data[record.body:record.end]
        source = inspect_pipe_edge_controls(data, records, body, feature, features)
        api = actual['settings']
        selected = api['path']['members'][0]['source']
        natural = selected.get('natural_geometry', selected.get('natural_world_geometry', {}))
        entry = {'file': filename, 'sha256': hashlib.sha256((root/filename).read_bytes()).hexdigest(),
                 'API_observation': {'is_closed': api['path']['is_closed'], 'natural_source_geometry_type': natural['geometry_type'],
                                     'distance_one': api['distance_one'], 'distance_two': api['distance_two']},
                 'native_observation': {'descriptor_flag_byte3': source['path']['stored_descriptor_flag_byte3'],
                                        'has_auxiliary_point_selector': source['native_has_auxiliary_point_selector'],
                                        'stored_against_fraction': source['native_parameter_controls']['AgainstDistance']['stored_value'],
                                        'stored_along_fraction': source['native_parameter_controls']['AlongDistance']['stored_value']}}
        check(filename+' source closure remains unknown', source['path']['is_closed'], None)
        check(filename+' distanceTwo remains unknown', source['distance_two_fraction'], None)
        if source['native_has_auxiliary_point_selector']:
            parsed = inspect_pipe_auxiliary_vertex_context(data, records, body, feature, features, source_evidence=source)
            source_point = (selected['start_vertex']['point_cm'] if 'start_vertex' in selected
                            else selected['start_vertex_point_cm'])
            check(filename+' point cache matches independently captured source start vertex', same(parsed['cached_position_cm'], source_point), True)
            check(filename+' API actual source is open', api['path']['is_closed'], False)
            entry['expected_auxiliary_vertex_context'] = parsed
            loaded[filename] = data, records, body, feature, features, source, parsed
        else:
            try:
                inspect_pipe_auxiliary_vertex_context(data, records, body, feature, features, source_evidence=source)
            except ValueError as error:
                entry['expected_no_populated_auxiliary_reason'] = str(error)
            else:
                raise AssertionError('Unpopulated selector accepted')
        report['samples'].append(entry)

    flags = {Path(s['file']).name: s for s in report['samples']}
    line, circle = flags['line_offset_negative_partial.f3d'], flags['circle_full.f3d']
    check('Descriptor flag counterexample equal flags', line['native_observation']['descriptor_flag_byte3'], circle['native_observation']['descriptor_flag_byte3'])
    check('Descriptor flag counterexample distinct API closedness', line['API_observation']['is_closed'] != circle['API_observation']['is_closed'], True)
    report['closure_flag_counterexample'] = {'open': line['file'], 'closed': circle['file'], 'same_native_descriptor_flag': 1}
    data, records, body, feature, features, source, parsed = loaded[folder+'/line_offset_negative_partial.f3d']
    by_id = {r.object_id: r for r in records if r.is_primary}
    guards = [('Context coordinate copy mismatch', parsed['context_object_id'], 2, struct.pack('<d', 17.0)),
              ('Wrong typed context leaf', parsed['descriptor_object_id'], 184, struct.pack('<Q', parsed['vertex_recipe_object_id'])),
              ('Historical anchor disagreement', parsed['descriptor_object_id'], 199, struct.pack('<Q', 999999)),
              ('Nonreciprocal support descriptor', parsed['support_object_id'], 32, struct.pack('<Q', feature['object_id']))]
    for label, identity, offset, replacement in guards:
        changed = bytearray(data)
        record = by_id[identity]
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        try:
            inspect_pipe_auxiliary_vertex_context(bytes(changed), records, body, feature, features, source_evidence=source)
        except (ValueError, KeyError, IndexError, struct.error) as error:
            report['malformed_guards'].append({'label': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError(label)
    report['validation'] = {'actual_files': len(cases), 'new_auxiliary_vertex_context_joins': len(loaded),
                            'full_Pipe_failures_cleared': 0, 'comparisons_passed': len(report['comparisons']),
                            'malformed_guards_passed': len(report['malformed_guards']), 'new_API_calls': 0}
    return report
