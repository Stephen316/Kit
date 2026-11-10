"""Captured four-line automatic face-supported sketch boundary relationships.

Each output naming recipe matches exactly one explicit source-context recipe by
full stored recipe bytes. Coordinates and entry ordinals never choose sources.
"""
import struct

from decode_brep_recipes import RECIPE_GUID
from decode_selection import native_proxy_references
from decode_selection_context_recipes import CONTEXT_RECIPE_LINK, TOPOLOGY
from decode_selection_context_variants import decode_selection_context_variants
from decode_sketch import reference
from decode_sketch_projections import CONTROLLER_GUID, ENTRY_GUID, decode_sketch_projections

SCOPE = 'Captured family1 face-boundary projections: explicit four-output naming/cache pairs, unique stored recipe correspondence, historical body provenance and cached sketch endpoint cycle; persistent face/edge topology unresolved'


def decode_face_boundary_projection_family(data, records, features, controller, chunk, primary, naming_leaf, cached_output):
    """Optional controller_family_decoder callback for decode_sketch_projections."""
    if (controller.class_guid != CONTROLLER_GUID or len(chunk) != 105
            or chunk[:6] != bytes.fromhex('000001000001')
            or struct.unpack_from('<I', chunk, 26)[0] != 1):
        raise ValueError('Only captured family1 four-line face boundary projections supported')
    owner = reference(chunk, 94)
    targets = [f for f in features if f['kind'] == 'Sketch' and f['object_id'] == owner]
    if len(targets) != 1 or reference(chunk, 30) != owner:
        raise ValueError('Face boundary projection target sketch owner unresolved')
    target = targets[0]
    entry_id, proxy_id = reference(chunk, 6), reference(chunk, 41)
    _, entry = primary(entry_id, ENTRY_GUID)
    if (len(entry) != 90 or entry[:6] != bytes(2)+struct.pack('<I', 4)
            or struct.unpack_from('<Q', entry, 82)[0] != 1):
        raise ValueError('Unobserved face boundary counted output framing')
    proxy, proxy_payload = primary(proxy_id, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    descriptors, props = native_proxy_references(data, proxy)
    if props or len(descriptors) != 1 or reference(proxy_payload, len(proxy_payload)-11) != owner:
        raise ValueError('Face boundary source proxy descriptor count/owner disagrees')
    descriptor_id = descriptors[0]
    _, descriptor = primary(descriptor_id, TOPOLOGY)
    if len(descriptor) != 309 or reference(descriptor, 298) != owner:
        raise ValueError('Face boundary source descriptor owner/extent disagrees')
    source_summary = decode_selection_context_variants(data, records,
        prior_summary={'unresolved': [{'descriptor_object_id': descriptor_id}]})
    if len(source_summary['contexts']) != 1 or source_summary['unresolved']:
        raise ValueError('Face boundary source context routes unresolved')
    face = source_summary['contexts'][0]
    if (face['owner_object_id'] != owner or face['stored_context_count'] != 4
            or face['descriptor_recipe']['payload_kind'] != 'bounded_face_recipe_data'):
        raise ValueError('Face boundary source is not captured owned four-context bounded face')
    source_routes = {}
    for route in face['context_recipe_routes']:
        recipe = route['cache_naming_route']['recipe']
        record, payload = primary(recipe['object_id'], RECIPE_GUID)
        if recipe['payload_kind'] != 'edge_recipe_data':
            raise ValueError('Face boundary context does not name an edge recipe')
        source_routes.setdefault(payload, []).append(route)
    if len(source_routes) != 4 or any(len(values) != 1 for values in source_routes.values()):
        raise ValueError('Face boundary source edge recipe correspondence ambiguous')

    relationships, used_contexts, output_ids, naming_ids = [], set(), [], []
    for index in range(4):
        naming_id = reference(entry, 6+19*index)
        output_id = struct.unpack_from('<Q', entry, 17+19*index)[0]
        _, naming_payload = primary(naming_id, CONTEXT_RECIPE_LINK)
        if naming_payload[:6] != bytes.fromhex('000100000000') or len(naming_payload) != 18:
            raise ValueError('Unobserved face boundary output naming framing')
        named_id, leaf, leaf_payload, progenitors = naming_leaf(naming_id)
        if leaf.class_guid != RECIPE_GUID or progenitors or named_id != naming_id:
            raise ValueError('Face boundary output naming recipe type/attributes disagree')
        matches = source_routes.get(leaf_payload, [])
        if len(matches) != 1 or matches[0]['context_object_id'] in used_contexts:
            raise ValueError('Face boundary output recipe has no unique unused source context')
        matched = matches[0]
        used_contexts.add(matched['context_object_id'])
        output_record, output_payload = primary(output_id)
        output = cached_output(output_record, output_payload, target['sketch_object_id'])
        if output['kind'] != 'Line' or output['start_point_id'] == output['end_point_id']:
            raise ValueError('Only captured nondegenerate line boundary outputs supported')
        relationships.append({'controller_object_id': controller.object_id, 'controller_family': 1,
            'entry_object_id': entry_id, 'boundary_output_ordinal': index,
            'target_feature_object_id': owner, 'target_sketch_object_id': target['sketch_object_id'],
            'target_sketch_name': target['name'], 'method': 'AutomaticFaceBoundary',
            'method_status': 'Observed native family1 in saved sketches created on planar BRepFaces; actual API line/linked getters were not captured',
            'stored_projection_mode': chunk[5], 'is_linked': None,
            'source_proxy_object_id': proxy_id, 'source_descriptor_object_id': descriptor_id,
            'output_naming_record_object_id': naming_id, 'endpoint_progenitor_record_object_ids': {},
            'source': {'kind': 'BRepFaceBoundaryEdgeRecipe',
                       'face_recipe_object_id': face['descriptor_recipe']['object_id'],
                       'face_recipe_kind': 'bounded_face_recipe_data',
                       'context_object_id': matched['context_object_id'],
                       'source_naming_link_object_id': matched['cache_naming_route']['link_object_id'],
                       'edge_recipe': matched['cache_naming_route']['recipe'],
                       'output_naming_recipe_object_id': leaf.object_id,
                       'recipe_correspondence': 'Unique exact stored recipe-byte equality; independent of context ordinal and coordinates',
                       'body_anchor_object_id': face['body_anchor_object_id'],
                       'native_body_object_id': face['native_body_object_id'],
                       'source_owner_object_id': face['source_owner_object_id'],
                       'topology_status': 'Explicit bounded-face and edge recipes with historical body; persistent BRep/ASM face/edge identities unresolved'},
            'output_cache': output,
            'link_status': 'Explicit family1 controller/output-entry/source-proxy and unique source-context/output-naming recipe correspondence'})
        output_ids.append(output_id)
        naming_ids.append(naming_id)
    if len(set(output_ids)) != 4 or len(set(naming_ids)) != 4 or len(used_contexts) != 4:
        raise ValueError('Face boundary repeated output/naming/source context identity')
    starts = [r['output_cache']['start_point_id'] for r in relationships]
    ends = [r['output_cache']['end_point_id'] for r in relationships]
    if len(set(starts)) != 4 or ends != starts[1:]+starts[:1]:
        raise ValueError('Captured face boundary output endpoint IDs do not form one ordered cycle')
    cycle = {'output_object_ids_in_native_entry_order': output_ids,
             'start_point_object_ids': starts, 'end_point_object_ids': ends,
             'forms_closed_endpoint_cycle': True,
             'scope': 'Explicit cached sketch point identities only; does not establish source face boundary order, persistent BRep topology or regenerated boundary geometry'}
    for item in relationships:
        item['cached_boundary_cycle'] = cycle
    return relationships


def decode_face_boundary_projections(data, records, features):
    """Additional relationships/unresolved/scope/groups; no feature mutation."""
    candidates = set()
    for record in records:
        if record.is_primary and record.class_guid == CONTROLLER_GUID:
            payload = data[record.body:record.end]
            if len(payload) >= 30 and struct.unpack_from('<I', payload, 26)[0] == 1:
                candidates.add(record.object_id)
    parsed = decode_sketch_projections(data, records, features,
        controller_family_decoder=decode_face_boundary_projection_family)
    relationships = [item for item in parsed['relationships'] if item.get('controller_family') == 1]
    groups = {}
    for item in relationships:
        groups.setdefault(item['controller_object_id'], {
            'controller_object_id': item['controller_object_id'], 'entry_object_id': item['entry_object_id'],
            'source_descriptor_object_id': item['source_descriptor_object_id'],
            'target_sketch_object_id': item['target_sketch_object_id'],
            'cached_boundary_cycle': item['cached_boundary_cycle'],
            'is_linked': None, 'scope': SCOPE})
    return {'relationships': relationships, 'unresolved': [item for item in parsed['unresolved'] if item['object_id'] in candidates],
            'groups': list(groups.values()), 'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    """Three saved four-line boundaries, three older controls, six malformed guards."""
    import hashlib
    import json
    from pathlib import Path
    from decode_basics import attach_parameters, named_features, sketch_references
    from decode_parameters import decode_stream
    from decode_sketch import decode_sketches
    from decode_sketch_projection_families import decode_sketch_projection_families
    from fusion_archive import read_members
    from fusion_metadata import design_records

    root = Path(root)
    filenames = [
        'constructionmodes-521ce7cdfdbe/axis_perpendicular_at_point.f3d',
        'holeplacements-04adf73afe93/sketch_point.f3d',
        'holeplacements-04adf73afe93/sketch_points.f3d']
    report = {'scope': SCOPE, 'integration': {
        'summary': 'decode_face_boundary_projections(data,records,features) returns additional relationships/unresolved/groups/scope.',
        'callback': 'decode_face_boundary_projection_family(data,records,features,controller,chunk,primary,naming_leaf,cached_output)',
        'merge': 'Merge relationships by (controller_object_id,output_cache.object_id) into sketch_projections and retain groups separately. Clear only successful corresponding sketch projection controller failures. Do not clear unrelated topology-context geometry or persistent-topology failures.',
        'expected_outputs': 'samples[].expected_summary contains complete per-file additional output for exact comparison.',
        'validator': 'decode_face_boundary_projections.validate_fixtures(root,zstd_library=None)'},
        'framing': {
            'controller': 'Existing105-byte F145 owned framing; native family1 at26, entry reference6, repeated target owner30/94 and source proxy41. Stored byte5=1 retained; not decoded as API isReference/isLinked.',
            'entry': 'CA72 prefixzero16, u32count4, four19-byte pairs (11-byte typed naming ref, rawu64 cache object ID), trailingu64=1; exactly90bytes.',
            'source': 'Owned proxy -> descriptor309 -> typed bounded-face recipe and four linked contexts, decoded by selection-context variants helper. Each output naming edge recipe matches exactly one source context edge recipe by full stored bytes.',
            'cycle': 'Output line start/end sketch point IDs repeat in one ordered four-edge cycle. This is a cached sketch graph property; source BRep boundary topology/ordering is unresolved.'},
        'generation_evidence': {
            'construction': 'GenerateConstructionModes.py creates the AxisPoint sketch with root.sketches.add(face) in axis_perpendicular_at_point; no explicit project call adds these four lines.',
            'holes': 'GenerateHolePlacements.py creates HoleLocations with root.sketches.add(top) before adding one/three hole placement points; no explicit project call adds these four lines.',
            'SDK': 'Installed adsk.fusion.Sketches.addWithoutEdges documentation says that with a BRepFace its edges are not projected and the new sketch is empty. Together with the actual stored controller/source graph and saved generator calls this supports the face-boundary classification.',
            'API_line_getter_status': 'Not captured in these original fixtures. Coordinates, tags and closed cycle below are independently framed native caches, not newly claimed API line getter comparisons.'},
        'limitations': ['API isLinked/isReference and projected line getter settings are unresolved; is_linked remainsNone.',
                        'Unique exact recipe equality establishes native correspondence, not persistent ASM/BRep entity identity or regenerated geometry.',
                        'Only captured four-Line, single planar face-supported root sketches are admitted; holes, curved/multiple boundary loops, non-Line outputs and occurrence contexts need separate controls.'],
        'samples': [], 'comparisons': [], 'older_controls': [], 'malformed_guards': []}
    loaded = {}

    def load(filename):
        members = read_members(root/filename, zstd_library)
        member = next(name for name in members if name.endswith('FusionDesignSegmentType1/BulkStream.dat'))
        data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        features = named_features(data, records)
        parameters, _ = decode_stream(data, records)
        attach_parameters(data, records, features, parameters)
        sketch_references(data, records, features)
        decode_sketches(data, records, features)
        return data, records, features

    def check(label, actual, expected):
        assert actual == expected, (label, actual, expected)
        report['comparisons'].append({'label': label, 'actual': actual, 'expected': expected, 'passed': True})

    for filename in filenames:
        data, records, features = load(filename)
        parsed = decode_face_boundary_projections(data, records, features)
        check(filename+' four relationships', len(parsed['relationships']), 4)
        check(filename+' one group', len(parsed['groups']), 1)
        check(filename+' no additional unresolved', parsed['unresolved'], [])
        targets = {f['object_id']: f for f in features if f['kind'] == 'Sketch'}
        for item in parsed['relationships']:
            target = targets[item['target_feature_object_id']]
            decoded = next(g for g in target['geometry'] if g['object_id'] == item['output_cache']['object_id'])
            cache = item['output_cache']
            check(filename+f" output{cache['object_id']} native geometry/tag join",
                  [decoded['kind'], decoded['entity_tag'], decoded['start_point_id'], decoded['end_point_id'], decoded['start_cm'], decoded['end_cm']],
                  [cache['kind'], cache['entity_tag'], cache['start_point_id'], cache['end_point_id'], cache['start_cm'], cache['end_cm']])
            check(filename+f" output{cache['object_id']} API linked flag remains unknown", item['is_linked'], None)
        sample = next(s for s in json.loads((root/Path(filename).parent/'ground_truth.json').read_text())['samples'] if s['file'] == Path(filename).name)
        report['samples'].append({'file': filename, 'sha256': hashlib.sha256((root/filename).read_bytes()).hexdigest(),
                                  'captured_API_context': sample, 'expected_summary': parsed})
        loaded[filename] = data, records, features, parsed

    controls = ['sketchprojections-67c0c4531b8f/linked_line.f3d',
                'sketchprojections-67c0c4531b8f/included_line.f3d',
                'projectionfamilies-d987c50c2d73/intersect_circle.f3d']
    for filename in controls:
        data, records, features = load(filename)
        before = decode_sketch_projections(data, records, features)
        families_before = decode_sketch_projection_families(data, records, features)
        added = decode_face_boundary_projections(data, records, features)
        check(filename+' no unrelated face boundary recoveries', added['relationships'], [])
        check(filename+' no unrelated face boundary failures', added['unresolved'], [])
        check(filename+' default projection reader unchanged', decode_sketch_projections(data, records, features), before)
        check(filename+' prior projection-family reader unchanged', decode_sketch_projection_families(data, records, features), families_before)
        if not filename.startswith('projectionfamilies-'):
            callback_result = decode_sketch_projections(data, records, features, controller_family_decoder=decode_face_boundary_projection_family)
            check(filename+' opt-in callback leaves Project/Include unchanged', callback_result, before)
        report['older_controls'].append({'file': filename, 'default_relationship_count': len(before['relationships']),
                                         'prior_family_relationship_count': len(families_before['relationships']),
                                         'face_boundary_relationship_count': len(added['relationships'])})

    filename = filenames[1]
    data, records, features, expected = loaded[filename]
    by_id = {r.object_id: r for r in records if r.is_primary}
    descriptor = by_id[302]
    reordered = bytearray(data)
    first, second = data[descriptor.body+183:descriptor.body+194], data[descriptor.body+194:descriptor.body+205]
    reordered[descriptor.body+183:descriptor.body+205] = second+first
    check('Source context reorder does not change recipe-based output association',
          decode_face_boundary_projections(bytes(reordered), records, features), expected)

    entry = by_id[306]
    entry_payload = data[entry.body:entry.end]
    first_pair, second_pair = entry_payload[6:25], entry_payload[25:44]
    source_first, source_second = by_id[412], by_id[416]
    assert source_first.end-source_first.body == source_second.end-source_second.body
    guards = [
        ('Wrong output count/extent', 306, 2, struct.pack('<I', 3)),
        ('Raw output cache ID wrong class', 306, 17, struct.pack('<Q', 314)),
        ('Output naming recipe no longer matches any source recipe', 314, 22, b'9'),
        ('Source recipe byte correspondence ambiguous', 416, 0, data[source_first.body:source_first.end]),
        ('Source descriptor owner disagrees', 302, 299, struct.pack('<Q', 207)),
        ('Non-cyclic native entry pair order', 306, 6, second_pair+first_pair)]
    for label, identity, offset, replacement in guards:
        record = by_id[identity]
        changed = bytearray(data)
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        result = decode_face_boundary_projections(bytes(changed), records, features)
        assert not result['relationships'] and len(result['unresolved']) == 1, label
        report['malformed_guards'].append({'label': label, 'rejected': True, 'reason': result['unresolved'][0]['reason']})
    report['validation'] = {'actual_files': 3, 'new_relationships': 12, 'closed_cached_endpoint_groups': 3,
                            'older_controls': len(controls), 'comparisons_passed': len(report['comparisons']),
                            'malformed_guards_passed': len(report['malformed_guards']), 'actual_API_projected_line_getter_comparisons': 0,
                            'new_API_calls': 0}
    return report
