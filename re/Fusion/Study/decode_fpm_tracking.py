"""Framed historical FPM literals, owner caches and native numeric correspondence.

FPM_tracked_attrib_def values are not promoted to typed native references. A
same-asset descriptor with an equal positive ID corroborates stored tracking
provenance; historical state and selected-source identity remain unqualified.
"""
import math
import struct
import uuid

from asm_records import inspect_asm
from decode_body_asm_identifiers import MAPPING, _body_identifiers
from decode_body_properties import BODY, COLLECTION
from decode_body_selections import ANCHOR, HELPER, SUPPORT, decode_body_selections
from decode_parameters import read_string
from decode_pipe_recipe_incidence import decode_pipe_edge_recipe_operands
from decode_recipe_components import decode_counted_recipe
from decode_selection_context_recipes import TOPOLOGY
from decode_sketch import reference

DEFINITION = 'FPM_tracked_attrib_def'
SCOPE = 'Observed reciprocal trailing FPM attribute/edge cache, geometry-ordinal journal mentions and same-asset positive literal/native descriptor numeric correspondence; historical state and exact selected-source identity unresolved'


def _integer(token, tag, low=None, high=None):
    value = token['value']
    if (token['tag'] != tag or not isinstance(value, int) or isinstance(value, bool)
            or low is not None and value < low or high is not None and value > high):
        raise ValueError('FPM typed integer/pointer kind or range disagrees')
    return value


def encode_fpm_attribute(attribute):
    """Exact full attribute payload replay, including reciprocal header pointers."""
    output = b''
    for tag, value in attribute['stored_token_fields']:
        if tag == 7:
            raw = value.encode('ascii')
            output += bytes([7, len(raw)])+raw
        else:
            output += bytes([tag])+struct.pack('<q', value)
    return output


def decode_fpm_attributes(blob, *, parsed=None):
    """Catalog exact FPM attrs/owned caches; no native-source/state inference."""
    from decode_asm_history import decode_asm_history

    parsed = inspect_asm(blob) if parsed is None else parsed
    if not parsed['complete_token_stream']:
        raise ValueError('FPM requires a complete bounded ASM token stream')
    records = parsed['records']
    targets = [r for r in records if r['name'] == 'ATTRIB_CUSTOM-attrib' and len(r['tokens']) > 5
               and r['tokens'][5]['kind'] == 'string' and r['tokens'][5]['value'] == DEFINITION]
    if not targets:
        return {'attributes': [], 'unresolved': [], 'scope': SCOPE}
    history = decode_asm_history(blob, parsed=parsed)
    entities = [r for r in records if r['record_kind'] == 'entity' and r['section'] in ('geometry', 'trailing_states')]
    ordinals = {r['index']: index for index, r in enumerate(entities)}
    if [(row['geometry_entity_ordinal'], row['inspection_record_index']) for row in history['geometry_entities']] != list(enumerate(r['index'] for r in entities)):
        raise ValueError('FPM geometry pointer namespace disagrees with shared journal parser')

    def entity(ordinal, kind=None):
        if not isinstance(ordinal, int) or isinstance(ordinal, bool) or not 0 <= ordinal < len(entities):
            raise ValueError('FPM pointer leaves explicit geometry-entity ordinal table')
        rec = entities[ordinal]
        if kind is not None and rec['name'] != kind:
            raise ValueError('FPM pointer target has wrong typed geometry kind')
        return rec

    def pointer(rec, field, kind=None, nullable=False):
        value = _integer(rec['tokens'][field], 12)
        if nullable and value == -1:
            return None
        entity(value, kind)
        return value

    def vector(token, kind):
        value = token['value']
        if token['kind'] != kind or len(value) != 3 or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in value):
            raise ValueError('FPM cached vector kind/value unsupported')
        return value

    def owner_cache(edge, owner_ordinal):
        ts = edge['tokens']
        if (len(ts) != 11 or [t['tag'] for t in ts] != [12, 4, 12, 12, 6, 12, 6, 12, 12, 11, 7]
                or _integer(ts[1], 4) != -1 or _integer(ts[2], 12) != -1
                or ts[9]['value'] is not False or ts[10]['value'] != 'unknown'):
            raise ValueError('Only observed unreversed trailing FPM edge cache layout supported')
        start, end = (pointer(edge, field, 'vertex') for field in (3, 5))
        if start == end:
            raise ValueError('Only observed distinct-endpoint FPM line owner supported')
        first_coedge = pointer(edge, 7, 'coedge')
        if pointer(entity(first_coedge), 6, 'edge') != owner_ordinal:
            raise ValueError('FPM owner edge/first-coedge backreference not reciprocal')
        curve_ordinal = pointer(edge, 8, 'straight-curve')
        curve = entity(curve_ordinal)
        ct = curve['tokens']
        if (len(ct) != 7 or [t['tag'] for t in ct[:3]] != [12, 4, 12]
                or [_integer(ct[0], 12), _integer(ct[1], 4), _integer(ct[2], 12)] != [-1, -1, -1]
                or [t['tag'] for t in ct[5:]] != [11, 11] or [t['value'] for t in ct[5:]] != [False, False]):
            raise ValueError('Unobserved FPM historical straight-curve cache framing')
        origin, direction = vector(ct[3], 'position_vector'), vector(ct[4], 'direction_vector')
        if not math.isclose(sum(x*x for x in direction), 1., abs_tol=1e-10):
            raise ValueError('Only observed normalized FPM line-cache direction supported')
        parameter_domain = [ts[4]['value'], ts[6]['value']]
        if not all(math.isfinite(x) for x in parameter_domain) or not parameter_domain[1] > parameter_domain[0]:
            raise ValueError('FPM cached owner parameter domain invalid')
        endpoints = []
        for vertex_ordinal, parameter in zip((start, end), parameter_domain):
            vertex = entity(vertex_ordinal, 'vertex')
            vt = vertex['tokens']
            if (len(vt) != 6 or [t['tag'] for t in vt] != [12, 4, 12, 12, 4, 12]
                    or [_integer(vt[0], 12), _integer(vt[1], 4), _integer(vt[2], 12), _integer(vt[4], 4)] != [-1, -1, -1, 1]):
                raise ValueError('FPM cached endpoint vertex framing unsupported')
            pointer(vertex, 3, 'edge')
            point_ordinal = pointer(vertex, 5, 'point')
            point = entity(point_ordinal)
            pt = point['tokens']
            if (len(pt) != 4 or [t['tag'] for t in pt[:3]] != [12, 4, 12]
                    or [_integer(pt[0], 12), _integer(pt[1], 4), _integer(pt[2], 12)] != [-1, -1, -1]):
                raise ValueError('FPM cached endpoint point framing unsupported')
            position = vector(pt[3], 'position_vector')
            if not all(math.isclose(x, o+parameter*d, abs_tol=1e-9) for x, o, d in zip(position, origin, direction)):
                raise ValueError('FPM owner endpoint/curve parameter caches disagree')
            endpoints.append({'vertex_geometry_ordinal': vertex_ordinal, 'vertex_record_index': vertex['index'],
                'point_geometry_ordinal': point_ordinal, 'point_record_index': point['index'], 'raw_point': position})
        return {'edge_geometry_ordinal': owner_ordinal, 'edge_record_index': edge['index'],
            'first_coedge_geometry_ordinal': first_coedge, 'first_coedge_record_index': entity(first_coedge)['index'],
            'curve_geometry_ordinal': curve_ordinal, 'curve_record_index': curve['index'], 'primitive_kind': 'Line',
            'raw_origin': origin, 'direction': direction, 'parameter_domain': parameter_domain,
            'endpoint_caches': endpoints, 'is_reversed': False,
            'state_scope': 'Typed trailing attribute-owner cache only; source selection, historical state, BODY membership and world placement unqualified'}

    attributes, unresolved = [], []
    for rec in targets:
        try:
            ts = rec['tokens']
            if (rec['section'] != 'trailing_states' or rec['index'] not in ordinals or len(ts) != 8
                    or [t['tag'] for t in ts] != [12, 4, 12, 12, 12, 7, 4, 4]
                    or [_integer(ts[0], 12), _integer(ts[1], 4), _integer(ts[6], 4)] != [-1, -1, 1]):
                raise ValueError('Unobserved trailing FPM custom attribute framing')
            literal = _integer(ts[7], 4, 1, 0xffffffff)
            owner = pointer(rec, 4, 'edge')
            edge = entity(owner)
            current, previous, chain = pointer(edge, 0, nullable=True), None, []
            while current is not None:
                if current in chain or len(chain) >= 128:
                    raise ValueError('Cyclic/oversized FPM owner attribute chain')
                chain.append(current)
                attr = entity(current, 'ATTRIB_CUSTOM-attrib')
                at = attr['tokens']
                if (len(at) < 5 or [t['tag'] for t in at[:5]] != [12, 4, 12, 12, 12]
                        or [_integer(at[0], 12), _integer(at[1], 4)] != [-1, -1]
                        or pointer(attr, 4, 'edge') != owner or pointer(attr, 3, nullable=True) != previous):
                    raise ValueError('FPM owner/attribute chain is not reciprocal')
                previous, current = current, pointer(attr, 2, nullable=True)
            ordinal = ordinals[rec['index']]
            if ordinal not in chain:
                raise ValueError('FPM attribute absent from claimed owner chain')
            owner_geometry = owner_cache(edge, owner)
            fields = [[t['tag'], t['value']] for t in ts]
            attribute = {'attribute_record_index': rec['index'], 'attribute_geometry_ordinal': ordinal,
                'section': rec['section'], 'definition_name': DEFINITION, 'stored_schema_integer': 1,
                'stored_tracking_literal': literal, 'stored_token_fields': fields,
                'owner_edge_geometry_ordinal': owner, 'owner_edge_record_index': edge['index'],
                'owner_attribute_chain_geometry_ordinals': chain,
                'owner_attribute_chain_record_indices': [entity(i)['index'] for i in chain],
                'cached_attribute_owner_edge': owner_geometry,
                'payload_offset': ts[0]['offset'], 'payload_end_offset': rec['end_offset']-1,
                'payload_hex': blob[ts[0]['offset']:rec['end_offset']-1].hex(),
                'qualified_historical_state': None, 'exact_selected_source_identity': None,
                'identity_scope': 'Positive stored FPM literal and reciprocal trailing owner only; typed native reference and historical selected-source semantics are not established'}
            if encode_fpm_attribute(attribute).hex() != attribute['payload_hex']:
                raise ValueError('FPM full attribute payload byte replay disagrees')
            # Filled from the shared journal grammar; sides stay literal.
            attribute['attribute_journal_mentions'] = _journal_mentions(history, ordinal)
            attribute['owner_journal_mentions'] = _journal_mentions(history, owner)
            if not attribute['attribute_journal_mentions'] or not attribute['owner_journal_mentions']:
                raise ValueError('FPM owner/attribute lacks explicit journal slot mentions')
            attributes.append(attribute)
        except (ValueError, IndexError, KeyError, UnicodeError, struct.error) as error:
            unresolved.append({'attribute_record_index': rec['index'], 'reason': str(error)})
    return {'attributes': attributes, 'unresolved': unresolved,
        'pointer_namespace': 'Initial plus trailing geometry entity ordinals, excluding section markers and history entries; separate from global inspection indices and delta-state slots',
        'scope': SCOPE}


def _journal_mentions(history, ordinal):
    """Adapter for the shared literal journal parser; no transition inference."""
    mentions = []
    for state in history['journal_states']:
        for entry in state['entries']:
            for side in entry['pointer_sides']:
                if side['stored_geometry_entity_ordinal'] == ordinal:
                    mentions.append({'delta_state_slot': state['delta_state_slot'],
                        'journal_record_index': state['inspection_record_index'], 'entry_ordinal': entry['entry_ordinal'],
                        'pointer_side': side['pointer_side'], 'geometry_entity_ordinal': ordinal,
                        'inspection_record_index': side['inspection_record_index'], 'pointer_token_offset': side['token_offset']})
    return mentions


def qualify_fpm_recipe_view(blob, descriptor, attribute, *, parsed=None, alternative=None):
    """Require recipe incidence and FPM owner agreement in one bounded view.

    This qualifies a slot0/side0 cache correspondence. It does not select a
    chronological historical state or claim a general persistent source ID.
    """
    from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
    from materialize_asm_alternative import materialize_asm_alternative

    parsed = inspect_asm(blob) if parsed is None else parsed
    alternative = materialize_asm_alternative(blob, parsed=parsed) if alternative is None else alternative
    if (alternative['state_slot'] != 0 or alternative['pointer_side'] != 0
            or alternative['qualified_dangling_pointer_count'] != 0):
        raise ValueError('FPM recipe correspondence requires captured qualified slot0/side0 view')
    view = alternative['view_parsed']
    topology = alternative['topology']
    if topology['unresolved'] or len(topology['body_graphs']) != 1:
        raise ValueError('FPM alternative topology incomplete or ambiguous')
    graph = topology['body_graphs'][0]
    nodes = {row['index']: row for row in topology['nodes']}
    origins = {row['view_record_index']: row for row in alternative['origin_map']}
    by_ordinal = {row['geometry_entity_ordinal']: row for row in alternative['origin_map']}
    aliases = {row['side1_entity_ordinal']: row['side0_entity_ordinal'] for row in alternative['literal_pair_aliases']}
    geometry_entities = [r for r in parsed['records'] if r['record_kind'] == 'entity' and r['section'] in ('geometry', 'trailing_states')]
    initial_body_candidates = [i for i, rec in enumerate(geometry_entities)
        if rec['index'] == descriptor['explicit_initial_asm_body_record_index'] and rec['name'] == 'body' and rec['section'] == 'geometry']
    if len(initial_body_candidates) != 1:
        raise ValueError('FPM native mapped initial BODY does not have one explicit geometry ordinal')
    initial_body_ordinal = initial_body_candidates[0]
    expected_body_ordinal = aliases.get(initial_body_ordinal, initial_body_ordinal)
    if (origins[graph['body_index']]['geometry_entity_ordinal'] != expected_body_ordinal
            or nodes[graph['body_index']]['stored_entity_id'] != descriptor['stored_native_body_handle']):
        raise ValueError('FPM alternative BODY not the explicit kind-preserving pair alias of mapped native BODY')
    owner_origin = by_ordinal.get(attribute['owner_edge_geometry_ordinal'])
    attr_origin = by_ordinal.get(attribute['attribute_geometry_ordinal'])
    if (owner_origin is None or attr_origin is None or owner_origin['kind'] != 'edge'
            or attr_origin['kind'] != 'ATTRIB_CUSTOM-attrib'
            or owner_origin['inspection_record_index'] != attribute['owner_edge_record_index']
            or attr_origin['inspection_record_index'] != attribute['attribute_record_index']):
        raise ValueError('FPM owner/attribute are not explicit members of the qualified view')
    view_edge_id, view_attr_id = owner_origin['view_record_index'], attr_origin['view_record_index']
    view_edge = view['records'][view_edge_id]
    view_attr = view['records'][view_attr_id]
    if (view_edge['tokens'][0]['value'] != view_attr_id or view_attr['tokens'][4]['value'] != view_edge_id
            or view_attr['tokens'][5]['value'] != DEFINITION
            or view_attr['tokens'][7]['value'] != attribute['stored_tracking_literal']):
        raise ValueError('FPM qualified-view attribute/edge relation not reciprocal or literal changed')
    tags = decode_asm_generic_tags(blob, parsed=view, allow_fpm_tracking=True)
    recipe = {'object_id': descriptor['primary_recipe_object_id'], 'payload_kind': descriptor['primary_recipe_payload_kind'],
        'payload_hex': descriptor['primary_recipe_payload_hex'], 'name_table': descriptor['primary_recipe_name_table']}
    correspondence = match_recipe_tag_names(recipe, tags, parsed=view)
    raw = bytes.fromhex(recipe['payload_hex'])
    operands = decode_pipe_edge_recipe_operands(dict(recipe, payload_hex=(raw[:-4]+bytes(4)).hex()))
    names = {entry['name_table_index']: entry for entry in correspondence['name_entries']}

    def named_face(ref):
        row = names[ref['name_table_index']]
        if row['candidate_count'] != 1:
            raise ValueError('FPM alternative recipe face tag absent or ambiguous')
        candidate = row['candidates'][0]
        face_id = candidate['owner_record_index']
        if (candidate['owner_kind'] != 'face' or candidate['body_graph_membership'] != [graph['body_index']]
                or face_id not in graph['face_indices']):
            raise ValueError('FPM alternative recipe name is not a typed face of aliased native BODY')
        return {'name_table_index': ref['name_table_index'], 'face_origin': origins[face_id],
            'attribute_origin': origins[candidate['attribute_record_index']]}

    faces = [named_face(ref) for ref in operands['face_name_references']]
    required = {row['face_origin']['view_record_index'] for row in faces}
    edge_faces, vertex_faces, routes = {}, {}, {}
    for coedge_id in graph['coedge_indices']:
        coedge = nodes[coedge_id]
        loop = nodes[coedge['loop_index']]
        edge = nodes[coedge['edge_index']]
        edge_faces.setdefault(edge['index'], set()).add(loop['face_index'])
        for vertex in (edge['start_vertex_index'], edge['end_vertex_index']):
            vertex_faces.setdefault(vertex, set()).add(loop['face_index'])
        routes.setdefault(edge['index'], []).append({'face_origin': origins[loop['face_index']],
            'loop_origin': origins[loop['index']], 'coedge_origin': origins[coedge_id], 'edge_origin': origins[edge['index']]})
    matches = [edge for edge, incident in edge_faces.items() if incident == required]
    if matches != [view_edge_id]:
        raise ValueError('FPM owner does not agree with unique serialized named-face edge incidence in qualified view')
    edge = nodes[view_edge_id]
    endpoints = []
    for operand in operands['vertex_face_operands']:
        endpoint_faces = [named_face(ref) for ref in operand['face_name_references']]
        needed = {row['face_origin']['view_record_index'] for row in endpoint_faces}
        vertices = [vertex for vertex, incident in vertex_faces.items() if incident == needed]
        if len(vertices) != 1:
            raise ValueError('FPM alternative endpoint recipe does not identify one reciprocal vertex')
        endpoints.append({'operand_ordinal': operand['operand_ordinal'], 'named_face_operands': endpoint_faces,
            'vertex_origin': origins[vertices[0]]})
    if [row['vertex_origin']['view_record_index'] for row in endpoints] != [edge['start_vertex_index'], edge['end_vertex_index']]:
        raise ValueError('FPM alternative endpoint recipe order disagrees with qualified-view edge vertices')
    curve = nodes[edge['curve_index']]
    if curve['kind'] != 'straight-curve' or edge['is_reversed'] is not False:
        raise ValueError('Only captured unreversed qualified FPM Line owner supported')
    return {'state_slot': 0, 'pointer_side': 0, 'qualification': alternative['qualification'],
        'mapped_initial_body_geometry_ordinal': initial_body_ordinal, 'qualified_body_origin': origins[graph['body_index']],
        'native_body_pair_alias': next((pair for pair in alternative['literal_pair_aliases'] if pair['side1_entity_ordinal'] == initial_body_ordinal), None),
        'FPM_attribute_origin': attr_origin, 'FPM_owner_edge_origin': owner_origin,
        'recipe_object_id': recipe['object_id'], 'named_face_operands': faces,
        'endpoint_operand_associations': endpoints, 'reciprocal_incidence_routes': routes[view_edge_id],
        'recipe_and_FPM_owner_agree': True,
        'cached_view_edge': {'edge_origin': owner_origin, 'curve_origin': origins[edge['curve_index']],
            'primitive_kind': 'Line', 'raw_origin': curve['raw_origin'], 'direction': curve['direction'],
            'parameter_domain': [edge['start_parameter'], edge['end_parameter']],
            'endpoint_origins': [origins[edge['start_vertex_index']], origins[edge['end_vertex_index']]]},
        'scope': 'Exact recipe/tag/reciprocal incidence and FPM owner agree only in the qualified slot0/side0 alternate cache view; chronology, exact historical selected-source semantics and current/final state remain unassigned'}


def decode_fpm_selection_tracking(data, records, features, member, members, body_identifier_summary, body_selections=None):
    """Same-asset positive FPM/native descriptor numeric correspondences only.

    Tracks are keyed numerically_matching_descriptor_object_id. No track is a
    qualified selected-source edge and no tool/context failure may be cleared.
    """
    grouped = {}
    for rec in records:
        if rec.is_primary:
            grouped.setdefault(rec.object_id, []).append(rec)
    primary = {identity: rows[0] for identity, rows in grouped.items() if len(rows) == 1}
    body_summary = body_selections if body_selections is not None else decode_body_selections(data, records)
    anchors = {}
    for anchor in body_summary['body_anchors']:
        anchors.setdefault(anchor['object_id'], []).append(anchor)
    feature_map = {f['object_id']: f for f in features}

    def typed(identity, guid=None):
        rec = primary.get(identity)
        if rec is None or guid is not None and rec.class_guid != guid:
            raise ValueError('FPM native correspondence missing/ambiguous or wrong typed class')
        return rec, data[rec.body:rec.end]

    def text_uuid(payload, position):
        value, end = read_string(payload, position)
        if len(value) != 36:
            raise ValueError('FPM native descriptor UUID extent unsupported')
        uuid.UUID(value)
        return value, end

    def mapping_blob(mapping):
        _, payload = typed(mapping['mapping_record_object_id'], MAPPING)
        if payload[:2] != bytes(2):
            raise ValueError('FPM native body mapping prefix disagrees')
        count = struct.unpack_from('<I', payload, 2)[0]
        cursor = 6+16*count
        if not 1 <= count <= 1024 or cursor+16 > len(payload):
            raise ValueError('FPM native body mapping count/extent unsupported')
        pairs = [struct.unpack_from('<QQ', payload, 6+16*i) for i in range(count)]
        supplied = [(binding['stored_handle'], binding['native_body_object_id']) for binding in mapping['bindings']]
        if (sorted(pairs) != sorted(supplied) or len(set(pairs)) != count
                or len({handle for handle, _ in pairs}) != count or len({identity for _, identity in pairs}) != count):
            raise ValueError('FPM native body mapping handle/body table not bijective')
        owner = reference(payload, cursor)
        typed(owner, COLLECTION)
        if owner != mapping['owner_object_id'] or mapping['body_count'] != count or payload[cursor+11] != 0:
            raise ValueError('FPM native body mapping owner/count/separator disagrees')
        filename, end = read_string(payload, cursor+12)
        if (end != len(payload) or not filename.startswith('BREP.') or not filename.endswith('.smbh')
                or '/' in filename or '\\' in filename):
            raise ValueError('FPM native body mapping filename unsupported')
        blob_member = member.rsplit('/FusionDesignSegmentType1/', 1)[0]+'/Breps.BlobParts/'+filename
        if blob_member != mapping['history_blob_member'] or blob_member not in members:
            raise ValueError('FPM native mapping explicitly referenced same-asset blob disagrees')
        blob = members[blob_member]
        parsed = inspect_asm(blob)
        roots, _, _ = _body_identifiers(parsed, blob)
        if set(roots) != {handle for handle, _ in pairs}:
            raise ValueError('FPM native handle set does not match typed initial ASM BODY IDs')
        for binding in mapping['bindings']:
            typed(binding['native_body_object_id'], BODY)
            if roots[binding['stored_handle']]['index'] != binding['asm_body_index']:
                raise ValueError('FPM supplied typed initial ASM BODY index disagrees')
        return blob_member, blob, parsed

    def native_descriptor(identity, mapping, blob_member):
        _, payload = typed(identity, TOPOLOGY)
        if (len(payload) != 276 or payload[:3] != bytes(3) or payload[3] not in (0, 1)
                or struct.unpack_from('<I', payload, 15)[0] != 1
                or payload[171:183] != struct.pack('<QI', 2, 1)
                or struct.unpack_from('<I', payload, 194)[0] != 1):
            raise ValueError('FPM numeric descriptor correspondence has unobserved framing')
        namespace, cursor = text_uuid(payload, 19)
        entity, cursor = text_uuid(payload, cursor)
        if cursor != 171:
            raise ValueError('FPM native descriptor namespace pair extent disagrees')
        owner = reference(payload, 265)
        typed(owner)
        if owner not in feature_map or feature_map[owner]['kind'] not in ('Fillet', 'Chamfer'):
            raise ValueError('Only captured Fillet/Chamfer FPM descriptor owners supported')
        anchor_id = reference(payload, 198)
        _, anchor_payload = typed(anchor_id, ANCHOR)
        choices = anchors.get(anchor_id, [])
        if len(choices) != 1:
            raise ValueError('FPM native descriptor historical body anchor unresolved')
        anchor = choices[0]
        if (len(anchor_payload) != 102 or reference(anchor_payload, 80) != anchor['native_body_object_id']
                or reference(anchor_payload, 91) != anchor['source_owner_object_id']):
            raise ValueError('FPM native descriptor anchor body/source owner disagrees')
        bindings = [b for b in mapping['bindings'] if b['native_body_object_id'] == anchor['native_body_object_id']]
        if len(bindings) != 1:
            raise ValueError('FPM descriptor body does not belong to the explicitly referenced same blob mapping')
        helper_id, support_id = reference(payload, 239), reference(payload, 253)
        _, helper = typed(helper_id, HELPER)
        _, support = typed(support_id, SUPPORT)
        if (payload[223:227] != b'\1\1\0\0' or payload[235:239] != b'\1\1\0\0'
                or payload[250:253] != b'\1\0\0' or payload[264] != 0
                or helper != bytes.fromhex('0001000000000000000000000000')):
            raise ValueError('FPM native descriptor helper/trailer framing disagrees')
        if (len(support) != 58 or support[:12] != bytes.fromhex('000000000000010101000000')
                or reference(support, 12) != anchor['source_owner_object_id']
                or reference(support, 31) != identity or support[-8:] != bytes(8)):
            raise ValueError('FPM native descriptor support source/owner not reciprocal')
        context_id = reference(payload, 183)
        _, context = typed(context_id, '50AEE8B4-9456-4DD7-847D-6F6C909BBB9D')
        if len(context) != 55 or context[:2] != bytes(2):
            raise ValueError('Only captured FPM descriptor secondary55-byte cache supported')
        recipe_id = reference(payload, 4)
        recipe_rec, _ = typed(recipe_id, '7ACC2A03-0261-4879-A14A-A93D661A5BDC')
        recipe = decode_counted_recipe(data, recipe_rec)
        raw = bytes.fromhex(recipe['payload_hex'])
        if recipe['payload_kind'] != 'edge_recipe_data' or len(raw) != 116 or raw[-4:] != struct.pack('<i', -1):
            raise ValueError('Only captured FPM native116-byte edge recipe with opaque-minus-one qualifier supported')
        normalized = dict(recipe, payload_hex=(raw[:-4]+bytes(4)).hex())
        operands = decode_pipe_edge_recipe_operands(normalized)
        return {'numerically_matching_descriptor_object_id': identity, 'descriptor_class_guid': TOPOLOGY,
            'descriptor_owner_object_id': owner, 'descriptor_owner_kind': feature_map[owner]['kind'],
            'primary_recipe_object_id': recipe_id, 'primary_recipe_payload_kind': recipe['payload_kind'],
            'primary_recipe_payload_hex': raw.hex(),
            'primary_recipe_face_name_indices': [r['name_table_index'] for r in operands['face_name_references']],
            'primary_recipe_name_table': recipe['name_table'], 'stored_recipe_final_int32': -1,
            'namespace_text': namespace, 'entity_guid_text': entity, 'context_object_id': context_id,
            'context_status': 'Secondary geometry-only cache remains unresolved',
            'body_anchor_object_id': anchor_id, 'native_body_object_id': anchor['native_body_object_id'],
            'historical_source_owner_object_id': anchor['source_owner_object_id'],
            'mapping_record_object_id': mapping['mapping_record_object_id'], 'history_blob_member': blob_member,
            'stored_native_body_handle': bindings[0]['stored_handle'], 'explicit_initial_asm_body_record_index': bindings[0]['asm_body_index'],
            'helper_object_id': helper_id, 'support_object_id': support_id,
            'mapping_scope': 'Explicit native BODY maps to typed initial ASM BODY in this blob; FPM trailing owner BODY membership or historical state not established'}

    tracks, unresolved = [], []
    for mapping in body_identifier_summary['decoded']:
        try:
            blob_member, blob, parsed = mapping_blob(mapping)
            catalog = decode_fpm_attributes(blob, parsed=parsed)
            if catalog['unresolved']:
                raise ValueError('Incomplete FPM attribute coverage prevents unique literal correspondence')
            by_literal = {}
            for attribute in catalog['attributes']:
                by_literal.setdefault(attribute['stored_tracking_literal'], []).append(attribute)
            alternative, alternative_error = None, None
            if by_literal:
                try:
                    from materialize_asm_alternative import materialize_asm_alternative
                    alternative = materialize_asm_alternative(blob, parsed=parsed)
                except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
                    alternative_error = str(error)
            for literal, candidates in by_literal.items():
                try:
                    if len(candidates) != 1:
                        raise ValueError('Ambiguous FPM literal has multiple trailing owner candidates')
                    descriptor = native_descriptor(literal, mapping, blob_member)
                    track = {'stored_tracking_literal': literal,
                        'numeric_descriptor_correspondence': descriptor, 'FPM_attribute': candidates[0],
                        'correspondence_status': 'ExactPositiveStoredFPMAndTypedNativeDescriptorNumericCorrespondence',
                        'qualified_historical_state': None, 'exact_selected_source_identity': None,
                        'source_curve_geometry': None,
                        'identity_scope': 'Equal positive literal is a numeric correspondence, not a serialized typed native reference. Descriptor/frame/body/blob and reciprocal FPM owner/journal provenance are independently explicit; historical selected-source meaning remains unqualified.',
                        'scope': SCOPE}
                    track['alternative_view_correspondence'] = None
                    track['alternative_view_unresolved_reason'] = alternative_error
                    if alternative is not None:
                        try:
                            track['alternative_view_correspondence'] = qualify_fpm_recipe_view(
                                blob, descriptor, candidates[0], parsed=parsed, alternative=alternative)
                        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
                            track['alternative_view_unresolved_reason'] = str(error)
                    tracks.append(track)
                except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
                    unresolved.append({'history_blob_member': blob_member, 'stored_tracking_literal': literal,
                        'FPM_attribute_record_indices': [a['attribute_record_index'] for a in candidates], 'reason': str(error)})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'mapping_record_object_id': mapping['mapping_record_object_id'], 'reason': str(error)})
    return {'tracks': tracks, 'unresolved': unresolved, 'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    """Nine tracked literals across seven saved EdgeMode files and two controls."""
    import copy
    import json
    from pathlib import Path
    from decode_basics import decode_basics
    from decode_selection_recipe_incidence import decode_selection_recipe_incidence
    from fusion_archive import read_members
    from fusion_metadata import design_records

    root = Path(root)
    files = [('edgemodes-52695761f185/chamfer_multiple.f3d', [286, 298]),
             ('edgemodes-52695761f185/fillet_curvature.f3d', [287]),
             ('edgemodes-87edbf67527b/chamfer_angle.f3d', [286]),
             ('edgemodes-87edbf67527b/chamfer_angle_flipped.f3d', [286]),
             ('edgemodes-87edbf67527b/fillet_multiple.f3d', [287, 301]),
             ('edgemodes-87edbf67527b/fillet_asymmetric.f3d', [287]),
             ('edgemodes-87edbf67527b/fillet_chord.f3d', [287])]
    controls = ['revolveaxes-14700158dba9/brep_edge_offset_x.f3d', 'pipeedgecontrasts-5bd287323ae7/circle_full.f3d']
    report = {'scope': SCOPE, 'interfaces': {
        'catalog': 'decode_fpm_attributes(blob,*,parsed=None)',
        'replay': 'encode_fpm_attribute(attribute)',
        'native_tracking': 'decode_fpm_selection_tracking(data,records,features,member,members,body_identifier_summary,body_selections=None)',
        'qualified_candidate': 'qualify_fpm_recipe_view(blob,descriptor,attribute,*,parsed=None,alternative=None)',
        'dependencies': 'decode_asm_history supplies explicit geometry ordinals/journal slots. materialize_asm_alternative supplies a separately qualified slot0/side0 cache view and origin map. decode_asm_generic_tags opt-in FPM framing preserves its strict default.',
        'expected_outputs': 'samples[].expected_summary and controls[].expected_summary contain complete native-tracking outputs',
        'integration': 'Separate FPM tracking summary only. Keep exact_selected_source_identity, qualified_historical_state and source_curve_geometry null. Nested alternative_view_correspondence qualifies recipe/FPM agreement only within the explicit alternate cache view. Preserve all initial-cache/secondary-context/tool failures.'},
        'grammar': {
            'FPM_attribute': 'Exactly8 typed tokens: pointer-1,integer-1,nextattribute pointer,previousattribute pointer,edge-owner pointer,string FPM_tracked_attrib_def,integer1,positive uint32-range integer literal. Full byte payload replays exactly.',
            'owner': 'Geometry ordinal namespace spans initial+trailing entity records, excluding all markers/history records. Attribute owner pointer and owner first-attribute/next/previous chain are reciprocal. Observed edge/vertex/point/straight-curve cache signatures are typed and finite; first-coedge refers back to the owner edge.',
            'journal': 'Only literal table mentions and sides0/1 are exposed from the shared bounded parser. Chronological transition-side interpretation is not assigned.',
            'native_correspondence': 'An equal positive literal must identify one actual native topology descriptor with a framed edge recipe, feature owner, reciprocal support, historical anchor and native BODY mapped explicitly to typed initial ASM BODY in this same asset blob. The literal itself is not represented as a serialized typed native reference.',
            'qualified_alternative': 'Only independently qualified slot0/side0 alternate view is admitted. Explicit pair alias connects the native mapped BODY to the viewed BODY. Exact generic-tag name tuples select one reciprocal edge and ordered endpoint vertices; that edge must also be the explicitly origin-mapped FPM attribute owner. No coordinates or root ordinals select the candidate.'},
        'limitations': [
            'The alternate-view materializer has a narrow captured three-state schema; it is not universal history replay and its slot0/side0 view is not labeled chronologically before/after/current/final.',
            'Even when recipe and FPM agree uniquely within that view, general exact historical selected-source identity remains unclaimed. Numeric FPM/descriptor equality alone cannot establish it.',
            'The original initial-cache edge association failures remain meaningful: Chamfer removes the selected edge and Fillet caches can include unsupported topology. A successful alternate-view candidate does not clear those failures.',
            'Actual selected edge geometry getters were not captured in these old EdgeMode fixtures. API settings/edge-set counts and generator seed shape corroborate scope, not persistent identity. All geometry here is explicitly stored cache geometry.',
            'Only observed trailing Line-owner FPM attributes and Fillet/Chamfer276-byte single-cache descriptors with116-byte edge recipes are admitted; circles, faces, other custom definitions and other native owner families remain unsupported.'],
        'samples': [], 'controls': [], 'comparisons': [], 'malformed_guards': []}
    saved = {}

    def check(label, actual, expected):
        assert actual == expected, (label, actual, expected)
        report['comparisons'].append({'label': label, 'actual': actual, 'expected': expected, 'passed': True})

    def load(filename):
        members = read_members(root/filename, zstd_library)
        stream = decode_basics(root/filename, zstd_library)['streams'][0]
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        return data, records, stream, members

    def decode(loaded, *, data=None, members=None, mapping=None):
        original_data, records, stream, original_members = loaded
        return decode_fpm_selection_tracking(data if data is not None else original_data, records, stream['features'],
            stream['member'], members if members is not None else original_members,
            mapping if mapping is not None else stream['body_asm_identifiers'], stream['body_selections'])

    for filename, expected_literals in files:
        loaded = load(filename)
        data, records, stream, members = loaded
        output = decode(loaded)
        check(filename+' no tracking framing errors', output['unresolved'], [])
        check(filename+' exact positive native descriptor numeric correspondences', [t['stored_tracking_literal'] for t in output['tracks']], expected_literals)
        actual = next(s for s in json.loads((root/filename).parent.joinpath('ground_truth.json').read_text())['samples'] if s['file'] == Path(filename).name)
        check(filename+' captured API edge-set count agrees number of distinct framed descriptors', len(output['tracks']), len(actual['settings']['edge_sets']))
        for track in output['tracks']:
            literal = track['stored_tracking_literal']
            attribute = track['FPM_attribute']
            candidate = track['alternative_view_correspondence']
            check(filename+f' literal{literal} exact FPM byte replay', encode_fpm_attribute(attribute).hex(), attribute['payload_hex'])
            check(filename+f' literal{literal} owner/attribute namespace indices remain distinct', attribute['attribute_geometry_ordinal'] != attribute['attribute_record_index'], True)
            check(filename+f' literal{literal} raw owner and tag both have journal mentions', bool(attribute['attribute_journal_mentions']) and bool(attribute['owner_journal_mentions']), True)
            check(filename+f' literal{literal} historical state remains unassigned', track['qualified_historical_state'], None)
            check(filename+f' literal{literal} exact selected source identity remains unassigned', track['exact_selected_source_identity'], None)
            check(filename+f' literal{literal} no global source geometry promoted', track['source_curve_geometry'], None)
            check(filename+f' literal{literal} alternative has no qualification error', track['alternative_view_unresolved_reason'], None)
            check(filename+f' literal{literal} named recipe agrees with FPM owner in qualified view', candidate['recipe_and_FPM_owner_agree'], True)
            check(filename+f' literal{literal} qualified candidate preserves actual original owner ordinal', candidate['FPM_owner_edge_origin']['geometry_entity_ordinal'], attribute['owner_edge_geometry_ordinal'])
            check(filename+f' literal{literal} native mapped BODY has explicit pair alias', candidate['native_body_pair_alias']['side1_entity_ordinal'], candidate['mapped_initial_body_geometry_ordinal'])
        initial = decode_selection_recipe_incidence(data, records, stream['features'], stream['member'], members,
            stream['body_asm_identifiers'], stream['body_selections'], descriptor_ids=expected_literals)
        check(filename+' initial-cache source failures remain valid', initial['associations'], [])
        report['samples'].append({'file': filename, 'expected_summary': output,
            'expected_initial_cache_incidence': initial,
            'API_observation': {'edge_sets': actual['settings']['edge_sets'],
                'scope': 'Actual edge-set getters; no selected source edge geometry getter was captured. No API data enters the decoder.'}})
        saved[Path(filename).name] = loaded, output

    plain = saved['chamfer_angle.f3d'][1]['tracks'][0]
    flipped = saved['chamfer_angle_flipped.f3d'][1]['tracks'][0]
    check('Chamfer flip does not change positive FPM tracking literal', plain['stored_tracking_literal'], flipped['stored_tracking_literal'])
    check('Chamfer flip does not change stored trailing owner Line origin', plain['FPM_attribute']['cached_attribute_owner_edge']['raw_origin'], flipped['FPM_attribute']['cached_attribute_owner_edge']['raw_origin'])
    for filename in controls:
        output = decode(load(filename))
        check(filename+' unrelated source has no FPM tracks', output['tracks'], [])
        check(filename+' no false FPM failure on attribute-free source', output['unresolved'], [])
        report['controls'].append({'file': filename, 'expected_summary': output})

    loaded, output = saved['chamfer_angle.f3d']
    data, records, stream, members = loaded
    track = output['tracks'][0]
    native = track['numeric_descriptor_correspondence']
    attribute = track['FPM_attribute']
    blob_member = native['history_blob_member']
    blob = members[blob_member]
    parsed = inspect_asm(blob)
    attr_rec = parsed['records'][attribute['attribute_record_index']]
    owner_rec = parsed['records'][attribute['owner_edge_record_index']]
    for label, token, value in [('FPM schema integer mismatch', attr_rec['tokens'][6], 2),
                                ('FPM nonpositive tracking literal', attr_rec['tokens'][7], 0),
                                ('FPM owner points to wrong geometry type', attr_rec['tokens'][4], 0),
                                ('FPM owner first-coedge points to a vertex', owner_rec['tokens'][7], owner_rec['tokens'][3]['value'])]:
        changed = bytearray(blob)
        struct.pack_into('<q', changed, token['offset']+1, value)
        rejected = decode_fpm_attributes(bytes(changed))
        assert rejected['unresolved'] and not rejected['attributes'], label
        report['malformed_guards'].append({'label': label, 'rejected': True, 'reason': rejected['unresolved'][0]['reason']})

    changed = bytearray(blob)
    struct.pack_into('<q', changed, attr_rec['tokens'][7]['offset']+1, native['descriptor_owner_object_id'])
    modified_members = dict(members)
    modified_members[blob_member] = bytes(changed)
    rejected = decode(loaded, members=modified_members)
    assert not rejected['tracks'] and rejected['unresolved']
    report['malformed_guards'].append({'label': 'Positive FPM literal matches wrong native class', 'rejected': True, 'reason': rejected['unresolved'][0]['reason']})

    primary = {r.object_id: r for r in records if r.is_primary}
    recipe_rec = primary[native['primary_recipe_object_id']]
    raw = bytes.fromhex(native['primary_recipe_payload_hex'])
    start = data.find(raw, recipe_rec.body, recipe_rec.end)
    assert start >= 0
    changed = bytearray(data)
    changed[start+32:start+72], changed[start+72:start+112] = raw[72:112], raw[32:72]
    rejected = decode(loaded, data=bytes(changed))
    assert len(rejected['tracks']) == 1 and rejected['tracks'][0]['alternative_view_correspondence'] is None
    report['malformed_guards'].append({'label': 'Numeric FPM match retained but swapped endpoint recipe cannot qualify alternate candidate', 'rejected': True,
        'reason': rejected['tracks'][0]['alternative_view_unresolved_reason']})
    mapping = copy.deepcopy(stream['body_asm_identifiers'])
    mapping['decoded'][0]['history_blob_member'] = 'UnrelatedAsset/Breps.BlobParts/BREP.fake.smbh'
    rejected = decode(loaded, mapping=mapping)
    assert not rejected['tracks'] and rejected['unresolved']
    report['malformed_guards'].append({'label': 'Cross-asset FPM/native mapping', 'rejected': True, 'reason': rejected['unresolved'][0]['reason']})
    track_count = sum(len(s['expected_summary']['tracks']) for s in report['samples'])
    report['validation'] = {'saved_files': len(files), 'unrelated_controls': len(controls),
        'framed_FPM_attributes': track_count, 'exact_attribute_payload_replays': track_count, 'positive_numeric_descriptor_correspondences': track_count,
        'qualified_alternative_recipe_and_FPM_candidates': track_count, 'comparisons_passed': len(report['comparisons']),
        'malformed_guards_passed': len(report['malformed_guards']), 'historical_state_or_exact_selected_source_claims': 0,
        'initial_context_or_tool_failures_cleared': 0, 'new_API_calls': 0}
    return report
