"""Observed FullRound and Rule fillet controls with explicit source provenance.

Face roles follow swapped API holdouts and typed native lists. Bounded-face
recipes stay opaque; context and point caches do not establish persistent faces.
"""
import math
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import RECIPE_GUID, decode_recipe
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import numbers, reference

FILLET = 'A07D5F17-68CB-464D-9935-BF68E98A865F'
SET = '4A557CE2-375C-4F69-AA76-2403109F1493'
FULL_AGGREGATE = 'A9D2884D-E7D1-4E8F-8961-B7D90BAC64F1'
RULE_AGGREGATE = 'DFE2F969-631C-4978-9345-B58392AD6B9A'
FULL_LEAF = '128CC0A6-678F-4785-88C1-58D60802EFCE'
FULL_FACE = '4C687846-AC85-4C6F-BA18-0CF629FEA74C'
RULE_LEAF = '5E1EC0D0-0361-40E8-8883-063DDFEC3226'
SELECTOR = '84845197-E802-48EA-AB39-FC7B0E6F4102'
SUPPORT = '6CCF41D5-40BE-48ED-A834-18F3EAED6C57'
SCOPE = 'Captured single-set FullRound and Rule AllEdges/BetweenFaces constant/asymmetric controls and typed sources; exact persistent face/edge identity, fillet geometry and regeneration unresolved'


def decode_special_fillets(data, records, features, body_selections=None):
    """Return decoded/unresolved/scope; merge successes by feature_object_id."""
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {i: values[0] for i, values in grouped.items() if len(values) == 1}
    bodies = body_selections if body_selections is not None else decode_body_selections(data, records)
    feature_groups = {}
    for feature in features:
        feature_groups.setdefault(feature['object_id'], []).append(feature)

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Special fillet typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    def bounded_recipe(identity):
        record, _ = typed(identity, RECIPE_GUID)
        recipe = decode_recipe(data, record, primary)
        if recipe['payload_kind'] != 'bounded_face_recipe_data':
            raise ValueError('Special fillet face source requires bounded-face recipe')
        return {'kind': 'BRepFaceRecipe', 'recipe': recipe,
                'identity_status': 'Explicit typed bounded-face recipe; persistent face/ASM identity and geometry unresolved'}

    def aggregate(identity, owner, guid, context_counts):
        _, payload = typed(identity, guid)
        context_count = struct.unpack_from("<I", payload, 177)[0]
        if (context_count not in context_counts or len(payload) != 263+11*context_count or payload[:2] != bytes(2)
                or struct.unpack_from('<I', payload, 13)[0] != 1
                or reference(payload, len(payload)-11) != owner):
            raise ValueError('Special fillet aggregate descriptor framing/owner disagrees')
        namespace, cursor = read_string(payload, 17)
        entity, cursor = read_string(payload, cursor)
        uuid.UUID(namespace); uuid.UUID(entity)
        if (len(namespace) != 36 or len(entity) != 36 or cursor != 169
                or payload[cursor:cursor+12] != struct.pack('<QI', 2, context_count)
                or struct.unpack_from('<I', payload, 181+11*context_count)[0] != 1):
            raise ValueError('Special fillet context/anchor count framing changed')
        context_ids = [reference(payload, 181+11*i) for i in range(context_count)]
        if len(set(context_ids)) != context_count:
            raise ValueError('Duplicate special fillet context records')
        contexts = []
        context_guid = 'C46D3EEB-40E1-43FA-83DC-9CB204335417' if guid == FULL_AGGREGATE else '50AEE8B4-9456-4DD7-847D-6F6C909BBB9D'
        for context_id in context_ids:
            _, context = typed(context_id, context_guid)
            if guid == FULL_AGGREGATE:
                cn, pos = read_string(context, 10)
                ce, pos = read_string(context, pos)
                if (len(context) != 171 or context[:2] != bytes(2) or context[6:10] != bytes(4)
                        or cn != namespace or ce != entity or context[pos:] != struct.pack('<QB', 2, 0)):
                    raise ValueError('FullRound context namespace/entity framing changed')
            elif len(context) != 55 or context[:2] != bytes(2) or context[-5:] != bytes.fromhex('0000000100'):
                raise ValueError('Rule fillet context cache framing changed')
            contexts.append({'object_id': context_id, 'class_guid': context_guid, 'raw_hex': context.hex()})
        anchor_id = reference(payload, 185+11*context_count)
        matches = [a for a in bodies['body_anchors'] if a['object_id'] == anchor_id]
        if len(matches) != 1:
            raise ValueError('Special fillet historical body anchor unresolved/ambiguous')
        anchor = matches[0]
        _, anchor_payload = typed(anchor_id, 'D26351F0-5940-4D23-AA20-2C35475A6D9E')
        typed(anchor['native_body_object_id'], 'D3937028-C20C-4E65-B010-94AD418A5C20')
        if (len(anchor_payload) != 102 or anchor_payload[:2] != bytes(2)
                or reference(anchor_payload, 80) != anchor['native_body_object_id']
                or reference(anchor_payload, 91) != anchor['source_owner_object_id']):
            raise ValueError('Special fillet typed historical anchor/body/owner copies disagree')
        support_id = reference(payload, len(payload)-23)
        _, support = typed(support_id, SUPPORT)
        if (len(support) != 77 or support[:12] != bytes.fromhex('000000000000010102000000')
                or reference(support, 31) != identity or reference(support, 50) != identity):
            raise ValueError('Special fillet aggregate support references are not reciprocal')
        provenance = {'descriptor_object_id': identity, 'terminal_object_id': reference(payload, 2),
                      'body_anchor_object_id': anchor_id, 'native_body_object_id': anchor['native_body_object_id'],
                      'historical_body_source_owner_object_id': anchor['source_owner_object_id'],
                      'body_name': anchor.get('body_properties', {}).get('name'),
                      'namespace_text': namespace, 'entity_guid_text': entity,
                      'support_record_object_id': support_id, 'support_source_owner_object_id': reference(support, 12),
                      'context_records': contexts,
                      'context_status': 'Opaque cached contexts retained separately from source-role lists; not input count or persistent topology identity'}
        return provenance

    decoded, unresolved = [], []
    for feature in features:
        if feature['class_guid'] != FILLET:
            continue
        owner = feature['object_id']
        try:
            _, payload = typed(owner, FILLET)
            if len(payload) < 21 or struct.unpack_from('<I', payload, 17)[0] == 0:
                continue  # Ordinary edge-set fillets stay with their existing reader.
            mode = struct.unpack_from('<I', payload, 17)[0]
            if (mode not in (1, 2) or payload[:6] != bytes.fromhex('000001000000')
                    or payload[21] not in (0, 1) or payload[22:33] != bytes.fromhex('0001000000000000000000')
                    or struct.unpack_from('<I', payload, 33)[0] != 1):
                raise ValueError('Unobserved special fillet mode/header/set count')
            set_id, proxy_id = reference(payload, 6), reference(payload, 37)
            _, definition = typed(set_id, SET)
            proxy_record, proxy = typed(proxy_id, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
            ids, props = native_proxy_references(data, proxy_record)
            if len(proxy) != 105 or props or len(ids) != 1 or reference(proxy, 94) != owner:
                raise ValueError('Special fillet single aggregate proxy/owner disagrees')
            namespace, cursor = read_string(payload, 48)
            if namespace != str(uuid.UUID(int=0)) or cursor != 124 or payload[124:127] != bytes(3):
                raise ValueError('Special fillet feature metadata namespace framing changed')
            bindings = []

            def parameter(identity, role, slot):
                matches = [p for p in feature['parameters'] if p['binding_object_id'] == identity]
                if len(matches) != 1 or matches[0]['role'] != role:
                    raise ValueError('Special fillet parameter binding/role unresolved or ambiguous')
                p = matches[0]; value = p['raw_float64']
                _, binding = typed(identity, 'D91D429C-1BB5-4640-B49F-69AF14F463E9')
                _, numeric = typed(p['parameter_object_id'], '7A6A3D31-BE74-4E19-9115-20642944C2E4')
                _, npos = read_string(numeric, 12, allow_text_controls=True)
                if (len(binding) != 85 or binding[:5] != bytes.fromhex('0101000000')
                        or reference(binding, 5) != owner or struct.unpack_from('<I', binding, 16)[0] != slot
                        or reference(binding, 29) != p['parameter_object_id'] or reference(binding, 48) != owner
                        or reference(binding, 74) != owner or reference(numeric, npos+4) != identity
                        or struct.unpack_from('<I', binding, 40)[0] != struct.unpack_from('<I', numeric, npos)[0]
                        or p.get('internal_units') != 'cm' or read_string(data, p['role_offset'])[0] != role
                        or not math.isfinite(value) or value <= 0
                        or numbers(binding, 21, 1)[0] != value
                        or data[p['value_offset']:p['value_offset']+8] != binding[21:29]
                        or p['declared_binding_object_id'] != identity):
                    raise ValueError('Special fillet parameter values/indices/reciprocal owners disagree')
                _, bookkeeping = typed(reference(binding, 62), SUPPORT)
                if len(bookkeeping) != 39 or reference(bookkeeping, 12) != identity:
                    raise ValueError('Special fillet parameter bookkeeping does not reciprocate binding')
                bindings.append(identity)
                return {'binding_object_id': identity, 'parameter_object_id': p['parameter_object_id'],
                        'name': p['parameter_name'], 'role': role, 'value_cm': value,
                        'display_unit': p['display_units'], 'expression_candidates': p['expression_candidates']}

            result = {'feature_object_id': owner, 'kind': 'Fillet', 'fillet_feature_type': mode,
                      'is_rolling_ball_corner': bool(payload[21]), 'definition_record_object_id': set_id,
                      'selection_record_object_id': proxy_id, 'scope': SCOPE}
            if mode == 2:
                if len(definition) != 58 or definition[:32] != bytes(32) or definition[43:] != bytes(15) or reference(definition, 32) != proxy_id:
                    raise ValueError('Unobserved single FullRound set layout')
                if feature['parameters'] or not result['is_rolling_ball_corner']:
                    raise ValueError('Unobserved FullRound parameter/corner combination')
                provenance = aggregate(ids[0], owner, FULL_AGGREGATE, (3,))
                if provenance['support_source_owner_object_id'] != provenance['historical_body_source_owner_object_id']:
                    raise ValueError('FullRound aggregate support/historical body source disagrees')
                _, leaf = typed(provenance['terminal_object_id'], FULL_LEAF)
                if (len(leaf) != 48 or leaf[:2] != bytes(2) or leaf[2] not in (0, 1)
                        or any(struct.unpack_from('<I', leaf, i)[0] != 1 for i in (3, 18, 33))):
                    raise ValueError('Unobserved FullRound source-role counts')
                source_ids = [reference(leaf, i) for i in (7, 22, 37)]
                if len(set(source_ids)) != 3:
                    raise ValueError('Duplicate FullRound source faces')
                sources = []
                for identity in source_ids:
                    _, source = typed(identity, FULL_FACE)
                    if len(source) != 53 or source[:2] != bytes(2):
                        raise ValueError('Unobserved FullRound source face payload')
                    values = numbers(source, 2, 5)
                    sources.append({'source_record_object_id': identity, **bounded_recipe(reference(source, 42)),
                                    'uninterpreted_parameter_pair': values[:2], 'stored_face_point_cache_cm': values[2:],
                                    'point_cache_status': 'Agrees with captured rectangular-face centroid/pointOnFace in swapped holdout; general point/centroid semantics unresolved'})
                result.update(mode='FullRound', historical_body=provenance,
                              face_sets=[{'are_automatic_side_faces': bool(leaf[2]),
                                          'side_one': [sources[0]], 'side_two': [sources[1]], 'center': sources[2]}])
            else:
                if len(definition) == 68:
                    if (definition[:8] != bytes(8) or definition[8] != 1 or definition[9:33] != bytes(24)
                            or reference(definition, 33) != proxy_id or definition[59:64] != bytes(5)):
                        raise ValueError('Unobserved constant Rule fillet set layout')
                    radius = parameter(reference(definition, 44), 'Radius', 0)
                    offset_one = offset_two = None
                    native_rule, native_topology = struct.unpack_from('<I', definition, 55)[0], struct.unpack_from('<I', definition, 64)[0]
                    if not result['is_rolling_ball_corner']:
                        raise ValueError('Uncaptured constant Rule corner-mode combination')
                elif len(definition) == 78:
                    if (definition[:12] != bytes.fromhex('000001000000000001000000') or definition[34:53] != bytes(19)
                            or reference(definition, 53) != proxy_id or definition[64] != 0 or definition[69:74] != bytes(5)):
                        raise ValueError('Unobserved asymmetric Rule fillet set layout')
                    offset_one = parameter(reference(definition, 12), 'EdgeOffset1', 0)
                    offset_two = parameter(reference(definition, 23), 'EdgeOffset2', 1)
                    radius = None
                    native_rule, native_topology = struct.unpack_from('<I', definition, 65)[0], struct.unpack_from('<I', definition, 74)[0]
                    if result['is_rolling_ball_corner'] or (native_rule, native_topology) != (2, 3):
                        raise ValueError('Uncaptured asymmetric Rule corner/rule/topology combination')
                else:
                    raise ValueError('Unobserved Rule fillet set size')
                if native_rule not in (1, 2) or native_topology not in (1, 2, 3) or (native_rule == 1 and native_topology != 3):
                    raise ValueError('Unobserved Rule type/topology controls')
                provenance = aggregate(ids[0], owner, RULE_AGGREGATE, (4, 8, 12) if native_rule == 2 else (1,))
                _, leaf = typed(provenance['terminal_object_id'], RULE_LEAF)
                if leaf[:2] != bytes(2):
                    raise ValueError('Unobserved Rule source-list prefix')
                sources = []; one = []; two = []
                if native_rule == 2:
                    if len(leaf) != 36 or leaf[:10] != bytes(10) or struct.unpack_from('<I', leaf, 21)[0] != 1:
                        raise ValueError('Unobserved AllEdges single-feature source lists')
                    _, selector = typed(reference(leaf, 10), SELECTOR)
                    if selector != bytes(2)+struct.pack('<II', 3-native_topology, 2):
                        raise ValueError('Rule AllEdges selector is not captured feature mode')
                    leaf_id = reference(leaf, 25)
                    _, terminal = typed(leaf_id, '90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
                    if len(terminal) != 10 or terminal[:2] != bytes(2):
                        raise ValueError('Unobserved AllEdges feature identity leaf')
                    source_id = struct.unpack_from('<Q', terminal, 2)[0]
                    _, _ = typed(source_id, 'DD405BC2-D673-44F0-8833-5CB2A1C186C7')
                    matches = feature_groups.get(source_id, [])
                    if len(matches) != 1 or matches[0]['kind'] != 'Extrude' or provenance['support_source_owner_object_id'] != source_id:
                        raise ValueError('Rule AllEdges source feature/support identity disagrees')
                    sources.append({'kind': 'ExtrudeFeature', 'feature_object_id': source_id, 'name': matches[0]['name'],
                                    'terminal_object_id': leaf_id,
                                    'association': 'Explicit feature-mode selector/typed native identity leaf and aggregate support agree'})
                else:
                    if (len(leaf) != 47 or struct.unpack_from('<I', leaf, 2)[0] != 1
                            or struct.unpack_from('<I', leaf, 17)[0] != 0 or struct.unpack_from('<I', leaf, 32)[0] != 1):
                        raise ValueError('Unobserved BetweenFaces single-face role lists')
                    _, selector = typed(reference(leaf, 21), SELECTOR)
                    if selector != bytes(10) or provenance['support_source_owner_object_id'] != provenance['historical_body_source_owner_object_id']:
                        raise ValueError('Rule BetweenFaces selector/source body owner disagrees')
                    first_id, last_id = reference(leaf, 6), reference(leaf, 36)
                    if first_id == last_id:
                        raise ValueError('Duplicate BetweenFaces recipe roles')
                    # Storage order is reversed: actual swapped-role captures and
                    # identical FullRound recipes corroborate last=one/first=two.
                    one, two = [bounded_recipe(last_id)], [bounded_recipe(first_id)]
                result.update(mode='Rule', historical_body=provenance, rule_type=0 if native_rule == 2 else 1,
                              rule_type_name='AllEdges' if native_rule == 2 else 'BetweenFacesOrFeatures',
                              stored_rule_type=native_rule, topology_type=3-native_topology,
                              topology_type_name={3: 'Both', 2: 'Rounds', 1: 'Fillets'}[native_topology],
                              stored_topology_type=native_topology, selector_stored_topology_type=struct.unpack_from('<I', selector, 2)[0],
                              selector_stored_source_mode=struct.unpack_from('<I', selector, 6)[0], is_constant_radius=radius is not None,
                              radius=radius, offset_one=offset_one, offset_two=offset_two,
                              sources=sources, source_one=one, source_two=two,
                              corner_scope='Captured rolling-ball property retained; asymmetric internal corner algorithm is not inferred from this flag')
            expected = [proxy_id, ids[0]]+bindings
            count = struct.unpack_from('<I', payload, 127)[0]
            if (count != len(expected) or [reference(payload, 131+11*i) for i in range(count)] != expected
                    or len(feature['parameters']) != len(bindings)):
                raise ValueError('Special fillet feature/source/parameter dependency table disagrees')
            result['source_role_status'] = 'Typed ordered source lists corroborated by actual role swaps; no face IDs chosen by coordinate proximity'
            decoded.append(result)
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'feature_object_id': owner, 'kind': 'Fillet', 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved, 'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    """Focused nine-capture API/role-swap/negative validator; no Fusion access."""
    import hashlib
    import json
    from pathlib import Path
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records
    from decode_sketch import same

    root = Path(root)
    report = {'scope': SCOPE, 'integration': {
        'function': 'decode_special_fillets(data,records,features,body_selections=None)',
        'stream_key': 'special_fillets', 'feature_settings': 'Merge successes by feature_object_id into tool_settings; ordinary edge-set fillets stay with existing reader.',
        'validator': 'decode_special_fillets.validate_fixtures(root,zstd_library=None)',
        'expected_outputs': 'samples[].expected_summary is complete main/helper equality target.'},
        'layout': {
            'feature': 'Single set reference@6; native feature type@17 Rule1/FullRound2; rolling-ball property@21; owned proxy@37 repeated in exact source/parameter dependency table@127.',
            'FullRound': 'Set58 bytes with proxy@32. A9D aggregate ->128CC leaf48: automatic byte2; single source lists@3/18/33, references@7/22/37 are sideOne/sideTwo/center. Each typed4C68 source53 stores opaque pair and face-point cache before its bounded-face recipe reference@42.',
            'Rule': 'Constant set68 has radius binding@44, native rule@55 and topology@64. Asymmetric78 has offsets@12/@23, native rule@65/topology@74. Native rule2/1 maps API AllEdges0/Between1; topology3/2/1 maps API Both0/Rounds1/Fillets2.',
            'selector': '8484 selector10 bytes repeats API topology u32@2; u32@6 is feature mode2 or face mode0. Repeated topology must agree with set control.',
            'AllEdges_source': '5E1E leaf36: two empty face groups and one typed90055 feature identity leaf; explicit native Extrude source must agree with aggregate support owner. Historical body anchor remains original seed owner, distinct from selected Boss feature.',
            'Between_roles': '5E1E leaf47: first recipe@6 is API source_two; final recipe@36 is API source_one; middle list empty. Reversal corroborated by actual swapped-role getters and byte-identical FullRound center/side recipes; no coordinate matching chooses identity.',
            'contexts': 'Full3 C46 contexts; Rule55-byte50AEE cache lists observed lengths12/8/4 for AllEdges Both/Rounds/Fillets,1 Between. They remain opaque and are not input counts or persistent selected edges.'},
        'limitations': ['Only captured one-set FullRound, one-Extrude AllEdges, or one-face-per-group Between constant/asymmetric layouts.',
            'Face point caches match rectangular-face centroid/pointOnFace in the swapped FullRound holdout; general centroid semantics and first opaque pair remain unresolved.',
            'Typed bounded-face recipes retain source provenance; persistent face/edge IDs, trimmed topology, context transforms and fillet regeneration unresolved.',
            'Rolling-ball property is decoded as stored; asymmetric internal corner construction is not inferred from that property.',
            'Actual result face/edge counts, volumes, health and warning are API observations only, not reconstructed geometry.'],
        'samples': [], 'role_swap_checks': [], 'malformed_checks': [], 'capture_errors': {}}
    fixtures = {}; api_count = native_count = 0
    for folder in ('specialfillets-d50f7a4f04e0', 'specialfillets-a279c7bccbd1'):
        truth = json.loads((root/folder/'ground_truth.json').read_text())
        assert (root/folder/'complete.txt').is_file() and not truth['errors']
        report['capture_errors'][folder] = truth['errors']
        for sample in truth['samples']:
            archive = root/folder/sample['file']; main = decode_basics(archive, zstd_library)
            stream = next(s for s in main['streams'] if s.get('special_fillets', {}).get('decoded'))
            members = read_members(archive, zstd_library); data = members[stream['member']]
            records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
            result = decode_special_fillets(data, records, stream['features'], stream['body_selections'])
            assert len(result['decoded']) == 1 and not result['unresolved'] and result == stream['special_fillets']
            row = result['decoded'][0]; api = {}; native = {'main_complete_summary_equality': True}

            def eq(label, a, b, is_api=True):
                good = same(a, b) if isinstance(a, list) and a and isinstance(a[0], (int, float)) else a == b
                assert good, (sample['file'], label, a, b)
                (api if is_api else native)[label] = True

            eq('fillet_feature_type', row['fillet_feature_type'], sample['settings']['fillet_feature_type'])
            eq('rolling_ball_corner', row['is_rolling_ball_corner'], sample['settings']['is_rolling_ball_corner'])
            if row['mode'] == 'FullRound':
                eq('face_set_count', len(row['face_sets']), len(sample['actual_face_sets']))
                actual = sample['actual_face_sets'][0]; face_set = row['face_sets'][0]
                eq('automatic_side_faces', face_set['are_automatic_side_faces'], actual['are_automatic_side_faces'])
                for role in ('side_one', 'side_two', 'center'):
                    items = face_set[role] if isinstance(face_set[role], list) else [face_set[role]]
                    expected = actual[role] if isinstance(actual[role], list) else [actual[role]]
                    eq(role+'.count', len(items), len(expected))
                    for index, (item, a) in enumerate(zip(items, expected)):
                        eq(role+'.'+str(index)+'.type', 'adsk::fusion::BRepFace', a['entity_type'])
                        eq(role+'.'+str(index)+'.body', row['historical_body']['body_name'], a['body_name'])
                        if 'centroid_cm' in a:
                            eq(role+'.'+str(index)+'.stored_point_matches_actual_centroid', item['stored_face_point_cache_cm'], a['centroid_cm'])
                            eq(role+'.'+str(index)+'.stored_point_matches_actual_pointOnFace', item['stored_face_point_cache_cm'], a['point_on_face_cm'])
            else:
                actual = sample['actual_rule']
                for field in ('rule_type', 'topology_type', 'is_constant_radius'):
                    eq(field, row[field], actual[field])
                eq('repeated_selector_topology', row['selector_stored_topology_type'], actual['topology_type'])
                for field in ('radius', 'offset_one', 'offset_two'):
                    if actual[field] is None:
                        eq(field+'.absent', row[field], None)
                    else:
                        p, a = row[field], actual[field]
                        for decoded_key, api_key in (('name', 'name'), ('role', 'role'), ('value_cm', 'value'), ('display_unit', 'unit')):
                            eq(field+'.'+decoded_key, p[decoded_key], a[api_key])
                for role in ('sources', 'source_one', 'source_two'):
                    eq(role+'.count', len(row[role]), len(actual[role]))
                    for i, (item, a) in enumerate(zip(row[role], actual[role])):
                        eq(role+'.'+str(i)+'.type', 'adsk::fusion::ExtrudeFeature' if item['kind'] == 'ExtrudeFeature' else 'adsk::fusion::BRepFace', a['entity_type'])
                        if item['kind'] == 'ExtrudeFeature':
                            eq(role+'.'+str(i)+'.name', item['name'], a['name'])
                            source_feature = next(f for f in stream['features'] if f['object_id'] == item['feature_object_id'])
                            eq(role+'.'+str(i)+'.timeline', source_feature['timeline_index'], a['timeline_index'])
                            eq(role+'.'+str(i)+'.body', [row['historical_body']['body_name']], a['body_names'])
                        else:
                            eq(role+'.'+str(i)+'.body', row['historical_body']['body_name'], a['body_name'])
                if row['sources']:
                    eq('source_feature_differs_from_historical_seed_owner', row['sources'][0]['feature_object_id'] != row['historical_body']['historical_body_source_owner_object_id'], True, False)
            feature = next(f for f in stream['features'] if f['object_id'] == row['feature_object_id'])
            eq('main_feature_tool_settings_equality', feature['tool_settings'], {k: v for k, v in row.items() if k not in ('feature_object_id', 'kind')}, False)
            report['samples'].append({'file': str(archive.relative_to(root)), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                'expected_summary': result, 'API_comparisons': api, 'native_structure_checks': native,
                'API_observations': {k: sample[k] for k in ('settings', 'result_bodies', 'actual_rule', 'actual_face_sets') if k in sample},
                'getter_errors': sample['getter_errors']})
            fixtures[sample['file']] = data, records, stream, row
            api_count += len(api); native_count += len(native)

    def recipe_bytes(fixture, item):
        data, records, _, _ = fixture
        record = next(r for r in records if r.is_primary and r.object_id == item['recipe']['object_id'])
        return data[record.body:record.end]

    original = fixtures['full_explicit.f3d']; swapped = fixtures['full_explicit_swapped.f3d']
    a, b = original[3]['face_sets'][0], swapped[3]['face_sets'][0]
    for first, last in (('side_one', 'side_two'), ('side_two', 'side_one'), ('center', 'center')):
        before = a[first][0] if isinstance(a[first], list) else a[first]
        after = b[last][0] if isinstance(b[last], list) else b[last]
        assert recipe_bytes(original, before) == recipe_bytes(swapped, after)
        report['role_swap_checks'].append({'name': 'FullRound '+first+' -> swapped '+last, 'byte_identical_recipe': True})
    original_rule = fixtures['rule_between_faces.f3d']; swapped_rule = fixtures['rule_between_faces_swapped.f3d']
    for first, last in (('source_one', 'source_two'), ('source_two', 'source_one')):
        assert recipe_bytes(original_rule, original_rule[3][first][0]) == recipe_bytes(swapped_rule, swapped_rule[3][last][0])
        report['role_swap_checks'].append({'name': 'Rule '+first+' -> swapped '+last, 'byte_identical_recipe': True})
    # Independent FullRound point caches establish side/center roles in these
    # controlled fixtures; identical serialized recipes corroborate Rule roles.
    for rule_role, full_role in (('source_one', 'center'), ('source_two', 'side_one')):
        full_source = a[full_role][0] if isinstance(a[full_role], list) else a[full_role]
        assert recipe_bytes(original_rule, original_rule[3][rule_role][0]) == recipe_bytes(original, full_source)
        report['role_swap_checks'].append({'name': 'Rule '+rule_role+' serialized recipe equals controlled FullRound '+full_role, 'byte_identical_recipe': True,
            'limitation': 'Controlled byte correspondence only; no general persistent face index/geometry semantics assigned'})

    def bad(label, filename, mutate):
        data, records, stream, row = fixtures[filename]; by = {r.object_id: r for r in records if r.is_primary}
        changed = bytearray(data); mutate(changed, by, row)
        out = decode_special_fillets(changed, records, stream['features'], stream['body_selections'])
        assert not out['decoded'] and out['unresolved'], label
        report['malformed_checks'].append({'name': label, 'rejected': True, 'reason': out['unresolved'][0]['reason']})

    bad('FullRound side group count2 unobserved', 'full_explicit.f3d', lambda d, by, r: struct.pack_into('<I', d, by[r['historical_body']['terminal_object_id']].body+3, 2))
    bad('selection proxy reciprocal owner changed', 'full_explicit.f3d', lambda d, by, r: struct.pack_into('<Q', d, by[r['selection_record_object_id']].body+95, r['historical_body']['historical_body_source_owner_object_id']))
    bad('Rule selector repeated topology disagrees', 'rule_all_both.f3d', lambda d, by, r: struct.pack_into('<I', d, by[392].body+2, 1))
    bad('Rule parameter owner does not reciprocate feature', 'rule_asymmetric.f3d', lambda d, by, r: struct.pack_into('<Q', d, by[r['offset_one']['binding_object_id']].body+6, r['historical_body']['historical_body_source_owner_object_id']))
    bad('AllEdges source leaf selects seed instead of supported Boss', 'rule_all_both.f3d', lambda d, by, r: struct.pack_into('<Q', d, by[r['sources'][0]['terminal_object_id']].body+2, r['historical_body']['historical_body_source_owner_object_id']))
    bad('historical anchor raw owner disagrees with decoded anchor', 'full_explicit.f3d', lambda d, by, r: struct.pack_into('<Q', d, by[r['historical_body']['body_anchor_object_id']].body+92, r['feature_object_id']))
    report['summary'] = {'successful_archives': len(fixtures), 'API_comparisons': api_count,
        'native_structure_and_main_checks': native_count, 'role_swap_and_recipe_checks': len(report['role_swap_checks']),
        'malformed_checks': len(report['malformed_checks']), 'getter_errors': sum(len(s['getter_errors']) for s in report['samples']), 'all_passed': True}
    return report


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--zstd-library', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if not args.validate:
        parser.error('--validate is required')
    report = validate_fixtures(args.root, args.zstd_library)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], indent=2))
