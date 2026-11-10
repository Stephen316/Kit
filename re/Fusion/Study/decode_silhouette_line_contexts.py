"""Role-gated Silhouette linear-edge point/direction caches, not edge evaluators.

The55-byte context shape alone cannot establish natural curve type. This helper
requires an owned direct BRepEdge Silhouette view-direction input, whose API
contract is linear. Edge-defined axes and arbitrary topology contexts stay out.
"""
import math
import struct

from decode_body_selections import ANCHOR, SUPPORT
from decode_silhouette_directions import TOPOLOGY, decode_silhouette_directions
from decode_silhouette_splits import DIRECTION, FEATURE
from decode_sketch import attributes, numbers, reference

LINE_CONTEXT = '50AEE8B4-9456-4DD7-847D-6F6C909BBB9D'
SCOPE = 'Direct linear BRepEdge Silhouette view-direction role only: separately stored line point/vector cache, without natural edge geometry, trim/closure, persistent topology or evaluated source reconstruction'


def inspect_silhouette_line_context(data, records, item):
    """Additional cached point/direction for a prior guarded Silhouette item.

    item is one decoded entry from decode_silhouette_directions. The native
    owner, direct input role and descriptor/context/anchor/support joins are
    rechecked here. No supplied is_closed or geometry-family claim is trusted.
    """
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Silhouette line-context typed identity missing, ambiguous or wrong class')
        return data[record.body:record.end]

    owner = item['feature_object_id']
    feature = typed(owner, FEATURE)
    if feature[0] != 0 or feature[1] not in (0, 1):
        raise ValueError('Unobserved Silhouette line-role feature prefix')
    props, cursor = attributes(feature, 2) if feature[1] else ({}, 2)
    if props or feature[cursor:cursor+8] != bytes(8):
        raise ValueError('Unobserved Silhouette line-role feature framing')
    direction_id = reference(feature, cursor+8)
    source = item['view_direction']['entity']
    if (source['kind'] != 'BRepEdge' or item['stored_direction_method_code'] != 8
            or item['direction_control_object_id'] != direction_id):
        raise ValueError('Cache interpretation requires the direct linear BRepEdge Silhouette direction role')
    control = typed(direction_id, DIRECTION)
    descriptor_id = source['descriptor_object_id']
    if (len(control) != 202 or control[:6] != bytes.fromhex('000008000000')
            or struct.unpack_from('<I', control, 70)[0] != 8
            or struct.unpack_from('<I', control, 99)[0] != 1
            or reference(control, 103) != descriptor_id or reference(control, 191) != owner):
        raise ValueError('Silhouette line role/control descriptor or owner disagrees')
    descriptor = typed(descriptor_id, TOPOLOGY)
    if (len(descriptor) != 276 or descriptor[:4] != bytes(4)
            or struct.unpack_from('<I', descriptor, 15)[0] != 1
            or descriptor[171:183] != struct.pack('<QI', 2, 1)
            or struct.unpack_from('<I', descriptor, 194)[0] != 1
            or reference(descriptor, 265) != owner
            or reference(descriptor, 4) != source['recipe']['object_id']
            or source['recipe']['payload_kind'] != 'edge_recipe_data'):
        raise ValueError('Silhouette line context owned source descriptor/recipe disagrees')
    context_id = reference(descriptor, 183)
    context = typed(context_id, LINE_CONTEXT)
    if (source['context_evidence']['object_id'] != context_id or len(context) != 55
            or context[:2] != bytes(2) or context[50:] != bytes.fromhex('0000000100')):
        raise ValueError('Unobserved Silhouette line context cache framing')
    anchor_id = reference(descriptor, 198)
    anchor = typed(anchor_id, ANCHOR)
    if (len(anchor) != 102 or anchor[:2] != bytes(2) or anchor_id != source['body_anchor_object_id']
            or reference(anchor, 80) != source['native_body_object_id']
            or reference(anchor, 91) != source['source_owner_object_id']):
        raise ValueError('Silhouette line context historical source identity disagrees')
    support_id = reference(descriptor, 253)
    support = typed(support_id, SUPPORT)
    if (len(support) != 58 or support[:12] != bytes.fromhex('000000000000010101000000')
            or reference(support, 12) != source['source_owner_object_id']
            or reference(support, 31) != descriptor_id):
        raise ValueError('Silhouette line context support is not reciprocal')
    values = numbers(context, 2, 6)
    origin, vector = values[:3], values[3:]
    length = math.sqrt(sum(value*value for value in vector))
    if not all(math.isfinite(value) for value in values) or not math.isfinite(length) or length <= 1e-12:
        raise ValueError('Degenerate or nonfinite role-gated line point/vector cache')
    return {'feature_object_id': owner, 'direction_control_object_id': direction_id,
            'source_descriptor_object_id': descriptor_id, 'context_object_id': context_id,
            'context_class_guid': LINE_CONTEXT, 'context_payload_hex': context.hex(),
            'semantic_gate': 'Native direct BRepEdge Silhouette viewDirection method8; documented API input must be linear',
            'cached_line_point_cm': origin, 'stored_line_vector': vector,
            'cached_unit_direction': [value/length for value in vector],
            'vector_scale_status': 'Stored cache vector scale; not interpreted as general natural edge length, parameterization or trim domain',
            'body_anchor_object_id': anchor_id, 'native_body_object_id': source['native_body_object_id'],
            'source_owner_object_id': source['source_owner_object_id'], 'support_object_id': support_id,
            'coordinate_scope': 'Captured root-component cache coordinates in cm; occurrence transforms unsupported',
            'source_geometry_status': 'Stored point/direction cache only; natural edge evaluator and exact persistent BRep/ASM geometry remain unresolved',
            'scope': SCOPE}


def decode_silhouette_line_contexts(data, records, features, body_selections=None, *, source_summary=None):
    """Additional decoded/unresolved/scope; no mutation or topology-failure clearing."""
    source_summary = source_summary if source_summary is not None else decode_silhouette_directions(data, records, features, body_selections)
    decoded, unresolved = [], []
    for item in source_summary['decoded']:
        if item['view_direction']['entity']['kind'] != 'BRepEdge' or item['stored_direction_method_code'] != 8:
            continue
        try:
            decoded.append(inspect_silhouette_line_context(data, records, item))
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'feature_object_id': item['feature_object_id'], 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved, 'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    """One role-gated addition, existing cross-role evidence and exclusion controls."""
    import copy
    import json
    from pathlib import Path
    from decode_basics import decode_basics
    from decode_pipe_edge_controls import inspect_pipe_edge_controls
    from decode_sketch import same
    from fusion_archive import read_members
    from fusion_metadata import design_records

    root = Path(root)
    folder = 'silhouettedirections-805c2eaa2411'
    filename = folder+'/faces_brep_edge_x.f3d'
    report = {'scope': SCOPE, 'integration': {
        'individual': 'inspect_silhouette_line_context(data,records,item), where item is an existing decoded Silhouette direction item',
        'summary': 'decode_silhouette_line_contexts(data,records,features,body_selections=None,*,source_summary=None)',
        'merge': 'Attach cached_source_line_context only to the corresponding direct BRepEdge Silhouette direction source or retain as separate decoded summary. Preserve source_geometryNone and unrelated topology-context failures; this is cached direction evidence, not regenerated/evaluated edge geometry.',
        'expected_output': 'sample.expected_summary is the full additional summary for exact equality.',
        'validator': 'decode_silhouette_line_contexts.validate_fixtures(root,zstd_library=None)'},
        'schema_basis': {'reuse': 'decode_revolve_axes._edge_axis already parses the same50AEE55 point/vector cache; this stage adds a role-gated Silhouette attachment, not a universal curve-family decoder.',
            'shape': 'Exactly55 bytes: prefixzero16, sixfloat64 fields, trailer0000000100. For the admitted linear view-direction role, firstthree fields are a cached point and lastthree a finite nonzero vector; normalized direction is separately derived.',
            'gate': 'The existing guarded Silhouette reader plus native feature/control/direct BRepEdge method8 correspondence must establish the input role. Neither context class/size nor cache coordinates select a topology identity.',
            'SDK_contract': 'Installed adsk.fusion.SilhouetteSplitFeatures.createInput and SilhouetteSplitFeatureInput.viewDirection accept a linear BRepEdge. RevolveFeatureInput.axis also documents a linear edge. ConstructionAxisInput.setByEdge accepts linear/circular edges, so its role alone is deliberately insufficient.'},
        'sample': {}, 'comparisons': [], 'exclusion_controls': [], 'malformed_guards': [],
        'limitations': ['Only direct BRepEdge Silhouette method8 is newly attached. Edge-defined construction-axis sources are not promoted from their role alone because that API also accepts circular edges.',
                        'Vector scale is not treated as natural curve parameterization, trim length or closure. Persistent recipe-to-ASM geometry and occurrence transforms remain unresolved.',
                        'The stored F2 preview/control origin/vector remain separate from this typed source-context cache.',
                        'No cache-only context failures are cleared by this additional direction evidence. Full Pipe failures and unknown closure remain untouched.']}

    def load(name):
        stream = decode_basics(root/name, zstd_library)['streams'][0]
        members = read_members(root/name, zstd_library)
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        return data, records, stream

    def check(label, actual, expected):
        assert actual == expected, (label, actual, expected)
        report['comparisons'].append({'label': label, 'actual': actual, 'expected': expected, 'passed': True})

    data, records, stream = load(filename)
    features = stream['features']
    baseline = decode_silhouette_directions(data, records, features, stream['body_selections'])
    parsed = decode_silhouette_line_contexts(data, records, features, stream['body_selections'], source_summary=baseline)
    check('Exactly one admitted direct linear-edge direction', len(parsed['decoded']), 1)
    check('No additional unresolved', parsed['unresolved'], [])
    actual = next(s for s in json.loads((root/folder/'ground_truth.json').read_text())['samples'] if s['file'] == Path(filename).name)
    api = actual['actual_direction']
    cached = parsed['decoded'][0]
    check('Cached source point matches independent actual edge line origin', cached['cached_line_point_cm'], api['line_origin_cm'])
    check('Normalized cached direction matches independent actual edge line direction', cached['cached_unit_direction'], api['line_direction'])
    check('Actual source API linear edge', [api['entity_type'], api['geometry_type']], ['adsk::fusion::BRepEdge', 'adsk::core::Line3D'])
    preview = baseline['decoded'][0]['view_direction']['stored_control_cache']
    check('Natural edge geometry remains unresolved', baseline['decoded'][0]['view_direction']['entity']['source_geometry'], None)
    check('Additional pass preserves existing source summary', decode_silhouette_directions(data, records, features, stream['body_selections']), baseline)
    report['sample'] = {'file': filename, 'API_actual_direction': api, 'expected_summary': parsed,
                        'separate_stored_control_preview': preview,
                        'preview_comparison_observation': {'same_point': same(preview['origin_cm'], cached['cached_line_point_cm']),
                                                           'same_raw_vector': same(preview['vector'], cached['stored_line_vector'])}}

    revolve_name = 'revolveaxes-a83b542c4a07/brep_edge.f3d'
    raw, rs, prior = load(revolve_name)
    selected = prior['revolve_axes']['decoded'][0]['axis']
    context_record = next(r for r in rs if r.is_primary and r.object_id == selected['context_record_object_id'])
    payload = raw[context_record.body:context_record.end]
    truth = next(s for s in json.loads((root/Path(revolve_name).parent/'ground_truth.json').read_text())['samples'] if s['file'] == 'brep_edge.f3d')['actual_axis']
    values = numbers(payload, 2, 6)
    check('Existing Revolve same context class and size', [context_record.class_guid, len(payload)], [LINE_CONTEXT, 55])
    check('Existing Revolve parser agrees with source cache point/vector', [selected['entity']['start_cm'], selected['entity']['stored_direction_vector']], [values[:3], values[3:]])
    check('Existing Revolve independent API start corroborates cached point', values[:3], truth['start_cm'])
    check('Existing Revolve independent API endpoint contrast corroborates stored vector', values[3:], [b-a for a,b in zip(truth['start_cm'], truth['end_cm'])])
    no_revolve = decode_silhouette_line_contexts(raw, rs, prior['features'], prior['body_selections'])
    check('No duplicate Revolve source attachment', no_revolve['decoded'], [])
    report['exclusion_controls'].append({'file': revolve_name, 'status': 'Existing negative-Y length3 cached source grammar corroborated; no new Silhouette attachment',
                                          'API_actual_axis': truth})

    axis_name = folder+'/faces_custom_axis_x.f3d'
    raw, rs, prior = load(axis_name)
    axis_source = decode_silhouette_directions(raw, rs, prior['features'], prior['body_selections'])
    axis_result = decode_silhouette_line_contexts(raw, rs, prior['features'], prior['body_selections'], source_summary=axis_source)
    check('Circular-capable construction-axis role is not promoted', axis_result['decoded'], [])
    try:
        inspect_silhouette_line_context(raw, rs, axis_source['decoded'][0])
    except ValueError as error:
        axis_rejection = str(error)
    else:
        raise AssertionError('Construction-axis direction admitted as direct linear BRepEdge')
    check('Construction-axis existing source summary unchanged', decode_silhouette_directions(raw, rs, prior['features'], prior['body_selections']), axis_source)
    report['exclusion_controls'].append({'file': axis_name, 'status': 'Actual captured source edge is linear, but circular-capable axis role provides no general linear-only semantic gate', 'rejection': axis_rejection})

    pipe_name = 'pipeedgecontrasts-5bd287323ae7/circle_full.f3d'
    raw, rs, prior = load(pipe_name)
    pipe = next(f for f in prior['features'] if f['kind'] == 'Pipe')
    record = next(r for r in rs if r.is_primary and r.object_id == pipe['object_id'])
    pipe_body = raw[record.body:record.end]
    pipe_source = inspect_pipe_edge_controls(raw, rs, pipe_body, pipe, prior['features'])
    check('Closed circle Pipe gets no line-context interpretation', decode_silhouette_line_contexts(raw, rs, prior['features'], prior['body_selections'])['decoded'], [])
    wrong_owner = copy.deepcopy(baseline['decoded'][0]);wrong_owner['feature_object_id'] = pipe['object_id']
    try:
        inspect_silhouette_line_context(raw, rs, wrong_owner)
    except ValueError as error:
        pipe_rejection = str(error)
    else:
        raise AssertionError('Pipe owner admitted to Silhouette line-only role')
    check('Pipe closure remains unclaimed', pipe_source['path']['is_closed'], None)
    report['exclusion_controls'].append({'file': pipe_name, 'actual_API_source': 'Circle3D, closed Path from saved Pipe getter truth',
                                          'status': 'No Silhouette role, no cache interpretation, no closure inference', 'rejection': pipe_rejection})

    by_id = {r.object_id: r for r in records if r.is_primary}
    owner = baseline['decoded'][0]
    preview_changed = bytearray(data)
    control_record = by_id[cached['direction_control_object_id']]
    preview_changed[control_record.body+6:control_record.body+30] = struct.pack('<3d', 123., 456., 789.)
    check('Changing stored F2 preview point leaves typed source-context cache unchanged',
          inspect_silhouette_line_context(bytes(preview_changed), records, owner), cached)
    report['preview_separation_control'] = 'A changed F2 control/preview point is not substituted for the source-context point; the entire additional source-context result remains identical.'
    guards = [('Wrong native direction method', cached['direction_control_object_id'], 70, struct.pack('<I', 5)),
              ('Owned descriptor mismatch', cached['direction_control_object_id'], 104, struct.pack('<Q', 999999)),
              ('Degenerate line context vector', cached['context_object_id'], 26, bytes(24)),
              ('Nonreciprocal source support', cached['support_object_id'], 32, struct.pack('<Q', cached['feature_object_id']))]
    for label, identity, offset, replacement in guards:
        changed = bytearray(data);record = by_id[identity]
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        try:
            inspect_silhouette_line_context(bytes(changed), records, owner)
        except (ValueError, KeyError, IndexError, struct.error) as error:
            report['malformed_guards'].append({'label': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError(label)
    report['validation'] = {'new_cached_direction_entries': 1, 'actual_capture_files': 4,
                            'prior_independent_linear_grammar_control': 1, 'excluded_circular_capable_axis_cases': 1,
                            'excluded_closed_circle_Pipe_cases': 1, 'comparisons_passed': len(report['comparisons']),
                            'malformed_guards_passed': len(report['malformed_guards']),
                            'topology_context_failures_cleared': 0, 'full_Pipe_failures_cleared': 0, 'new_API_calls': 0}
    return report
