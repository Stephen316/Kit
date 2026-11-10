"""Counted topology context lists and explicitly named secondary recipe routes.

Only new empty-context and linked-context layouts are accepted. Geometry-only
context caches stay unresolved; neither their coordinates nor recipe integers
are interpreted as persistent CAD topology identities.
"""
import struct
import uuid

from decode_body_selections import ANCHOR, CONTEXT, HELPER, SUPPORT, decode_body_selections
from decode_brep_recipes import RECIPE_GUID
from decode_parameters import read_string
from decode_recipe_components import decode_counted_recipe
from decode_selection_context_recipes import TOPOLOGY, CONTEXT_RECIPE_LINK, decode_selection_context_recipes
from decode_sketch import ascii_string, reference

EDGE_CONTEXT = '50AEE8B4-9456-4DD7-847D-6F6C909BBB9D'
SCOPE = 'Explicit counted topology context lists, namespace joins, typed naming/progenitor recipe routes and reciprocal historical body provenance; geometry and persistent topology unresolved'


def decode_selection_context_variants(data, records, body_selections=None, prior_summary=None):
    """Additional contexts/unresolved/scope; merge successes by descriptor_object_id.

    Existing successful context dictionaries are deliberately left to the default
    reader. A supplied prior_summary avoids rescanning that reader.
    """
    body_summary = body_selections if body_selections is not None else decode_body_selections(data, records)
    prior = prior_summary if prior_summary is not None else decode_selection_context_recipes(data, records, body_summary)
    candidates = {item['descriptor_object_id'] for item in prior['unresolved']}
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}
    anchors = {}
    for item in body_summary['body_anchors']:
        anchors.setdefault(item['object_id'], []).append(item)

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Context variant typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    def text_uuid(payload, cursor):
        text, end = read_string(payload, cursor)
        if len(text) != 36:
            raise ValueError('Unobserved context variant UUID length')
        uuid.UUID(text)
        return text, end

    def recipe(identity, kind):
        record, _ = typed(identity, RECIPE_GUID)
        parsed = decode_counted_recipe(data, record)
        if parsed['payload_kind'] != kind:
            raise ValueError('Context variant recipe kind disagrees with captured route')
        return parsed

    def naming(identity, kind, decorated=False):
        _, payload = typed(identity, CONTEXT_RECIPE_LINK)
        if payload[:2] not in (b'\0\0', b'\0\1'):
            raise ValueError('Unobserved context naming link prefix')
        cursor, progenitors = 2, []
        if payload[1]:
            count = struct.unpack_from('<I', payload, cursor)[0]
            cursor += 4
            if count not in ((0, 2) if decorated else (0,)):
                raise ValueError('Unobserved context naming attribute count')
            seen = set()
            for _ in range(count):
                name, cursor = ascii_string(payload, cursor)
                field_type, cursor = ascii_string(payload, cursor)
                if (name not in ('EdgeStartVertexProgenitor', 'EdgeEndVertexProgenitor')
                        or name in seen or field_type != 'StrongRefMetaType'):
                    raise ValueError('Unobserved context naming progenitor role/type')
                seen.add(name)
                target = reference(payload, cursor)
                cursor += 11
                _, leaf = typed(target, CONTEXT_RECIPE_LINK)
                if len(leaf) != 14 or leaf[:2] != bytes(2) or leaf[-1] != 0:
                    raise ValueError('Unobserved vertex progenitor naming leaf')
                progenitors.append({'stored_role': name, 'stored_type': field_type,
                                    'link_object_id': target,
                                    'recipe': recipe(reference(leaf, 2), 'vertex_recipe_data')})
        if len(payload) != cursor+12 or payload[-1] != 0:
            raise ValueError('Unobserved context naming link suffix')
        return {'link_object_id': identity, 'link_class_guid': CONTEXT_RECIPE_LINK,
                'stored_attribute_flag': payload[1], 'recipe': recipe(reference(payload, cursor), kind),
                'progenitor_recipe_routes': progenitors}

    def linked_context(identity, namespace, entity, decorated):
        _, payload = typed(identity, EDGE_CONTEXT)
        if (len(payload) != 75 or payload[:2] != bytes(2) or payload[50] != 0
                or payload[62:64] != b'\0\1'):
            raise ValueError('Only explicitly linked75-byte edge contexts supported; geometry-only context unresolved')
        namespace_id, link_id = reference(payload, 51), reference(payload, 64)
        _, context = typed(namespace_id, CONTEXT)
        if len(context) != 181 or context[:2] != bytes(2) or context[6:10] != bytes(4):
            raise ValueError('Unobserved linked namespace context framing')
        context_namespace, pos = text_uuid(context, 10)
        context_entity, pos = text_uuid(context, pos)
        if (pos != 162 or context_namespace != namespace or context_entity != entity
                or context[162:170] != struct.pack('<Q', 2)):
            raise ValueError('Descriptor/linked namespace context identity disagrees')
        namespace_link_id = reference(context, 170)
        if not decorated and namespace_link_id != link_id:
            raise ValueError('Bounded-face cache and namespace naming links disagree')
        direct = naming(link_id, 'edge_recipe_data', decorated)
        secondary = naming(namespace_link_id, 'edge_recipe_data')
        if decorated and len(direct['progenitor_recipe_routes']) != 2:
            raise ValueError('Captured single linked-edge context requires two explicit progenitor roles')
        return {'context_object_id': identity, 'context_class_guid': EDGE_CONTEXT,
                'stored_cache_field_bytes_hex': payload[2:50].hex(),
                'cache_scope': 'Six stored float64-sized fields; evaluated source geometry not established',
                'namespace_context_object_id': namespace_id,
                'stored_context_index_field': struct.unpack_from('<I', context, 2)[0],
                'namespace_text': context_namespace, 'entity_guid_text': context_entity,
                'cache_naming_route': direct, 'namespace_naming_route': secondary,
                'same_naming_link': namespace_link_id == link_id,
                'association': 'Explicit cache and namespace references to typed naming links; recipe identities do not establish persistent edge or vertex identities'}

    contexts, unresolved = [], []
    for record in records:
        if not record.is_primary or record.class_guid != TOPOLOGY or record.object_id not in candidates:
            continue
        try:
            if primary.get(record.object_id) is not record:
                raise ValueError('Context variant descriptor identity ambiguous')
            payload = data[record.body:record.end]
            if (len(payload) < 183 or payload[:3] != bytes(3) or payload[3] not in (0, 1)
                    or struct.unpack_from('<I', payload, 15)[0] != 1):
                raise ValueError('Unobserved context variant descriptor prefix')
            namespace, cursor = text_uuid(payload, 19)
            entity, cursor = text_uuid(payload, cursor)
            if cursor != 171 or payload[171:179] != struct.pack('<Q', 2):
                raise ValueError('Unobserved context variant association framing')
            count = struct.unpack_from('<I', payload, 179)[0]
            if count not in (0, 1, 4) or len(payload) != 265+11*count:
                raise ValueError('Unobserved counted context descriptor extent/count')
            context_ids = [reference(payload, 183+11*i) for i in range(count)]
            if len(set(context_ids)) != count:
                raise ValueError('Repeated context identity in captured distinct context list')
            if count == 1:
                candidate = primary.get(context_ids[0])
                if candidate is None or candidate.class_guid != EDGE_CONTEXT or candidate.end-candidate.body != 75:
                    raise ValueError('Geometry-only context cache has no supported explicit naming route; context semantics unresolved')
            if payload[3] != (1 if count == 1 else 0):
                raise ValueError('Unobserved context count/descriptor flag combination')
            cursor = 183+11*count
            if struct.unpack_from('<I', payload, cursor)[0] != 1:
                raise ValueError('Unobserved context variant anchor count')
            anchor_id = reference(payload, cursor+4)
            typed(anchor_id, ANCHOR)
            matched = anchors.get(anchor_id, [])
            if len(matched) != 1:
                raise ValueError('Context variant historical anchor unresolved or ambiguous')
            anchor = matched[0]
            cursor += 15
            if (payload[cursor+14:cursor+18] != b'\1\1\0\0'
                    or payload[cursor+26:cursor+30] != b'\1\1\0\0'
                    or payload[cursor+41:cursor+44] != b'\1\0\0' or payload[cursor+55] != 0):
                raise ValueError('Unobserved context variant trailer markers')
            owner = reference(payload, cursor+56)
            if owner not in primary:
                raise ValueError('Context variant owner missing or ambiguous')
            helper_id, support_id = reference(payload, cursor+30), reference(payload, cursor+44)
            _, helper = typed(helper_id, HELPER)
            if helper not in (bytes(10), bytes.fromhex('0001000000000000000000000000')):
                raise ValueError('Unobserved context variant helper framing')
            _, support = typed(support_id, SUPPORT)
            if len(support) < 39 or support[:6] != bytes(6) or any(v not in (0, 1) for v in support[6:8]):
                raise ValueError('Unobserved context variant support prefix')
            support_count = struct.unpack_from('<I', support, 8)[0]
            if support_count not in (0, 1, 2) or len(support) != 39+19*support_count or support[-8:] != bytes(8):
                raise ValueError('Unobserved context variant support count/extent')
            if support[6:8] != (b'\1\1' if support_count else bytes(2)):
                raise ValueError('Unobserved support count/stored flag combination')
            sources = [reference(support, 12+19*i) for i in range(support_count)]
            if any(identity not in primary for identity in sources) or reference(support, 12+19*support_count) != record.object_id:
                raise ValueError('Context variant support source/reciprocal owner unresolved')
            parsed_recipe = recipe(reference(payload, 4), 'edge_recipe_data' if count == 1 else 'bounded_face_recipe_data')
            routes = [linked_context(identity, namespace, entity, count == 1) for identity in context_ids]
            contexts.append({'descriptor_object_id': record.object_id, 'owner_object_id': owner,
                             'stored_descriptor_flag_at_3': payload[3], 'descriptor_recipe': parsed_recipe,
                             'namespace_text': namespace, 'entity_guid_text': entity,
                             'stored_context_count': count, 'context_record_object_ids': context_ids,
                             'context_recipe_routes': routes,
                             'context_status': 'Explicit counted empty context list' if not count else 'Explicit typed naming and namespace recipe routes',
                             'helper_object_id': helper_id, 'support_object_id': support_id,
                             'stored_helper_bytes_hex': helper.hex(), 'stored_support_bytes_hex': support.hex(),
                             'stored_descriptor_trailer_hex': payload[cursor:].hex(),
                             'support_source_record_object_ids': sources,
                             'support_contains_historical_source_owner': anchor['source_owner_object_id'] in sources,
                             'support_status': 'Counted explicit native references and reciprocal descriptor; source roles and stored8-byte cache fields unresolved',
                             'body_anchor_object_id': anchor_id, 'native_body_object_id': anchor['native_body_object_id'],
                             'source_owner_object_id': anchor['source_owner_object_id'], 'scope': SCOPE})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'descriptor_object_id': record.object_id, 'class_guid': record.class_guid,
                               'record_offset': record.start, 'reason': str(error)})
    return {'contexts': contexts, 'unresolved': unresolved, 'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    """Focused saved-fixture comparisons and malformed native association guards."""
    import hashlib
    import json
    from pathlib import Path
    from fusion_archive import read_members
    from fusion_metadata import design_records
    from decode_basics import named_features

    root = Path(root)
    filenames = [
        'holeplacements-04adf73afe93/sketch_point.f3d',
        'holeplacements-04adf73afe93/sketch_points.f3d',
        'constructionmodes-521ce7cdfdbe/axis_perpendicular_at_point.f3d',
        'sketchprojections-67c0c4531b8f/body_edge.f3d',
        'tappedholes-409e96788503/modeled_full.f3d',
        'tappedholes-409e96788503/cosmetic_full.f3d',
        'tappedholes-409e96788503/cosmetic_partial.f3d',
        'remainingbodyinputs-7b3357274e85/mirror_boss_faces.f3d',
    ]
    controls = [
        'edgemodes-52695761f185/chamfer_multiple.f3d',
        'pipeedgecontrasts-5bd287323ae7/line_full.f3d',
        'holeplacements-04adf73afe93/center_edge.f3d',
    ]
    report = {'scope': SCOPE, 'integration': {
        'reader': 'decode_selection_context_variants(data,records,body_selections=None,prior_summary=None)',
        'merge': 'Merge contexts by descriptor_object_id into selection_context_recipes; clear only those successful descriptor IDs. Preserve default successful dictionaries and all geometry-only context failures.',
        'expected_outputs': 'samples[].expected_summary contains the complete additional helper output for exact equality checks.',
        'validator': 'decode_selection_context_variants.validate_fixtures(root,zstd_library=None)'},
        'framing': {
            'descriptor': 'Fixed namespace pair and association2, u32contextcount0/1/4, that many explicit11-byte context references, anchorcount1 and anchor reference,67-byte trailer; total265+11*count.',
            'support': 'Typed6CCF prefix, stored flag bytes6/7, u32count0/1/2, count repeated19-byte entries (native reference plus opaque8-byte cache), reciprocal descriptor reference, opaque8-byte cache, zero8 trailer; total39+19*count. Counted source entries are not assigned action/geometry roles.',
            'context75': 'Typed50AEE raw48-byte cache, zero byte50, C46D namespace-context reference51, markers0001 at62, naming-link reference64. Namespace context must reproduce both descriptor UUIDs and association2.',
            'bounded_face': 'Four contexts explicitly join through namespace contexts to the same4B31 links, each of which names a typed edge recipe. No geometric ordering, closed boundary or face/ASM identity inferred.',
            'projected_edge': 'Cache naming link319 contains named StrongRefMetaType start/end vertex progenitor links; each links to a typed vertex recipe. Namespace context327 references a separate link325 and edge recipe326; link identity is not collapsed.',
            'empty_context': 'Five descriptors explicitly encode an empty context list; historical body/owner references remain available, without inventing a namespace-context record.'},
        'limitations': [
            '46 remaining failures have only geometry/cache contexts:39 typed50AEE55,6 typed994C28,1 typedB0B103. This helper intentionally leaves them unresolved.',
            'Stored numeric recipe components are parsed using the counted grammar without design-object ID guesses. Exact source geometry, transforms, persistent topology, ASM entity mapping and regeneration remain unresolved.',
            'API examples document modeling provenance; four edge-recipe routes are not assumed to match API face boundary order. In construction and hole examples the descriptor owner is an actual native Sketch, not the eventual axis/hole feature.',
            'Projection helper already exposed progenitor link IDs; this stage adds typed vertex-recipe routes and descriptor/context namespace/body joins, without changing projected output geometry.'],
        'samples': [], 'retained_unresolved_controls': [], 'comparisons': [], 'malformed_guards': []}
    loaded = {}

    def load(filename):
        members = read_members(root/filename, zstd_library)
        name = next(n for n in members if n.endswith('FusionDesignSegmentType1/BulkStream.dat'))
        data = members[name]
        records, _ = design_records(data, members[name.replace('BulkStream.dat', 'MetaStream.dat')])
        return data, records

    def check(label, actual, expected):
        assert actual == expected, (label, actual, expected)
        report['comparisons'].append({'label': label, 'actual': actual, 'expected': expected, 'passed': True})

    for filename in filenames:
        data, records = load(filename)
        loaded[filename] = data, records
        parsed = decode_selection_context_variants(data, records)
        check(filename+' additional summary count', len(parsed['contexts']), 2 if filename.endswith('mirror_boss_faces.f3d') else 1)
        check(filename+' additional unresolved', parsed['unresolved'], [])
        sample = next(s for s in json.loads((root/Path(filename).parent/'ground_truth.json').read_text())['samples'] if s['file'] == Path(filename).name)
        features = {f['object_id']: f for f in named_features(data, records)}
        for item in parsed['contexts']:
            owner = features.get(item['owner_object_id'], {})
            if filename.startswith('sketchprojections-'):
                check('API projection target sketch name', owner.get('name'), sample['settings']['target_sketch_name'])
                check('API projection input type', sample['settings']['source_type'], 'adsk::fusion::BRepEdge')
                roles = item['context_recipe_routes'][0]['cache_naming_route']['progenitor_recipe_routes']
                check('Typed endpoint recipe roles', sorted(r['stored_role'] for r in roles), ['EdgeEndVertexProgenitor', 'EdgeStartVertexProgenitor'])
                check('Projection cache/namespace naming links remain distinct', item['context_recipe_routes'][0]['same_naming_link'], False)
            elif filename.startswith('remainingbodyinputs-'):
                check('API mirror owner feature name', owner.get('name'), sample['feature_identity']['name'])
                check('API mirror source collection type', sorted(set(s['entity_type'] for s in sample['actual_inputs'])), ['adsk::fusion::BRepFace'])
                if item['descriptor_object_id'] == 415:
                    check('Support/historical-source counterexample', item['support_contains_historical_source_owner'], False)
                    report['counterexample'] = {'file': filename, 'descriptor_object_id': 415,
                        'support_source_record_object_ids': item['support_source_record_object_ids'],
                        'historical_anchor_source_owner_object_id': item['source_owner_object_id'],
                        'conclusion': 'Populated support sources can omit the historical anchor source owner; explicit native relationships are preserved separately and are not merged into one source identity.'}
            elif filename.startswith('tappedholes-'):
                check(filename+' native owner kind matching API thread controls', owner.get('kind'), 'Thread')
                assert any(p['created_by'] == sample['settings']['thread_name'] for p in sample['parameters'])
            else:
                check(filename+' native descriptor owner kind', owner.get('kind'), 'Sketch')
                check(filename+' typed edge recipe routes count', len(item['context_recipe_routes']), 4)
            check(filename+' historical source owner resolves', item['source_owner_object_id'] in {r.object_id for r in records if r.is_primary}, True)
        report['samples'].append({'file': filename, 'sha256': hashlib.sha256((root/filename).read_bytes()).hexdigest(),
                                  'API_observation': sample, 'expected_summary': parsed})

    for filename in controls:
        data, records = load(filename)
        parsed = decode_selection_context_variants(data, records)
        check(filename+' geometry-only contexts stay unresolved', len(parsed['contexts']), 0)
        assert parsed['unresolved']
        report['retained_unresolved_controls'].append({'file': filename, 'expected_summary': parsed})

    def malformed(filename, descriptor_id, target_id, offset, replacement, label):
        data, records = loaded[filename]
        by_id = {r.object_id: r for r in records if r.is_primary}
        target = by_id[target_id]
        changed = bytearray(data)
        changed[target.body+offset:target.body+offset+len(replacement)] = replacement
        result = decode_selection_context_variants(bytes(changed), records, prior_summary={'unresolved': [{'descriptor_object_id': descriptor_id}]})
        assert not result['contexts'] and len(result['unresolved']) == 1, label
        report['malformed_guards'].append({'label': label, 'rejected': True, 'reason': result['unresolved'][0]['reason']})

    construction = 'constructionmodes-521ce7cdfdbe/axis_perpendicular_at_point.f3d'
    projection = 'sketchprojections-67c0c4531b8f/body_edge.f3d'
    malformed(construction, 302, 302, 179, struct.pack('<I', 3), 'Unobserved context count/extent')
    malformed(construction, 302, 302, 299, struct.pack('<Q', 999999), 'Missing final native owner')
    malformed(construction, 302, 303, 32, struct.pack('<Q', 286), 'Nonreciprocal support descriptor')
    malformed(construction, 302, 315, 14, b'1\0', 'Namespace context UUID disagrees with descriptor')
    malformed(construction, 302, 315, 171, struct.pack('<Q', 317), 'Bounded-face cache/namespace naming-link disagreement')
    malformed(projection, 311, 319, 55, struct.pack('<Q', 320), 'Endpoint progenitor reference wrong typed class')
    report['validation'] = {'additional_descriptors': 9, 'linked_context_routes': 13, 'explicit_vertex_progenitor_routes': 2,
                            'focused_success_files': len(filenames), 'retained_unresolved_control_files': len(controls),
                            'comparisons_passed': len(report['comparisons']), 'malformed_guards_passed': len(report['malformed_guards']),
                            'new_API_calls': 0}
    return report
