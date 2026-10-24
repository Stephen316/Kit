"""Scoped Ruled sheet-boundary names and endpoint incidence; no tool changes."""
import math
import struct
import uuid

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
from decode_asm_subtypes import decode_asm_subtypes
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections, HELPER, SUPPORT
from decode_brep import decode_topology
from decode_one_face_edge_sources import _replay_recipe
from decode_parameters import read_string
from decode_patch_continuity import PATCH
from decode_recipe_components import decode_counted_recipe
from decode_selection import native_proxy_references
from decode_selection_context_recipes import TOPOLOGY
from decode_sketch import reference

RULED = 'BB4EDD5D-0BE0-4E13-B667-365B7C99C972'
PROXY = '2CA5A1CD-C99B-4C9B-91AF-57989148E841'
EDGE_CONTEXT = '50AEE8B4-9456-4DD7-847D-6F6C909BBB9D'
SCOPE = ('Observed156-byte Ruled direct-edge/one-face and two endpoint edge-incidence operands. '
         'Profile and auxiliary native selectors name the same cached sheet edge; API handle identity, '
         'direction/traversal, opaque qualifiers, current/persistent topology and historical lifecycle unresolved.')


def decode_ruled_edge_operands(recipe):
    """Decode only the complete captured156-byte operation; no owner inference."""
    raw = bytes.fromhex(recipe['payload_hex'])
    if recipe['payload_kind'] != 'edge_recipe_data' or len(raw) != 156:
        raise ValueError('Only the observed156-byte one-face endpoint-edge operation is supported')
    if (len(recipe['name_table']) != 4 or [e['table_index'] for e in recipe['name_table']] != list(range(4))
            or any(len(e['terms']) != 1 or e['terms'][0]['stored_index'] != 0
                   or e['terms'][0]['stored_reference_component_count'] != 1 for e in recipe['name_table'])):
        raise ValueError('Ruled operation requires four complete captured counted names')
    expected = [0, -1, 1, 1, -1, 2]
    endpoints = []
    for ordinal, other_name in enumerate((2, 3)):
        start = 24+64*ordinal
        expected.extend([-1, 1, 1, -1, 2])
        nested = []
        for offset, name in ((start+20, 0), (start+40, other_name)):
            fields = [name, -1, 0, 0, -1]
            expected.extend(fields)
            nested.append(dict(name_table_index=name, stored_secondary_index=-1,
                stored_face_count=0, stored_endpoint_count=0, stored_terminal_int32=-1,
                relative_offset=offset, payload_hex=raw[offset:offset+20].hex()))
        expected.append(0)
        endpoints.append(dict(operand_ordinal=ordinal, relative_offset=start,
            stored_direct_vertex_name_index=-1, stored_face_count=1, face_name_index=1,
            stored_face_secondary_index=-1, stored_edge_count=2, nested_edges=nested,
            stored_terminal_int32=0, payload_hex=raw[start:start+64].hex()))
    expected.append(-1)
    if struct.pack('<39i', *expected) != raw:
        raise ValueError('Ruled endpoint operation full framing/qualifier replay differs')
    return dict(stored_direct_edge_name_index=0, stored_secondary_index=-1,
        stored_face_count=1, face_name_index=1, stored_face_secondary_index=-1,
        stored_endpoint_count=2, endpoint_operands=endpoints,
        stored_final_qualifier_int32=-1, qualifier_semantics=None,
        payload_hex=raw.hex(), exact_full_operation_payload_replay=True)


def decode_ruled_edge_sources(data, records, features, member, members,
                             body_identifier_summary, body_selections=None):
    """Return one association per Ruled owner; all prior selectors stay intact."""
    result = dict(associations=[], unresolved=[], scope=SCOPE)
    candidates = [r for r in records if r.is_primary and r.class_guid == RULED]
    if not candidates:
        return result
    grouped, named = {}, {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    for feature in features:
        named.setdefault(feature['object_id'], []).append(feature)

    def typed(identity, guid=None):
        rows = grouped.get(identity, [])
        if len(rows) != 1 or guid is not None and rows[0].class_guid != guid:
            raise ValueError('Ruled source typed identity missing, ambiguous or wrong class')
        record = rows[0]
        return record, data[record.body:record.end]

    anchors = decode_body_selections(data, records)['body_anchors']
    mapped, cache = None, {}
    for candidate in candidates:
        owner = candidate.object_id
        try:
            record, body = typed(owner, RULED)
            if (member not in members or members[member] != data
                    or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat')):
                raise ValueError('Ruled source Design member/bytes scope differs')
            metadata = named.get(owner, [])
            if len(metadata) != 1 or metadata[0].get('class_guid') != RULED or metadata[0].get('record_offset') != record.start:
                raise ValueError('Ruled source feature metadata missing or ambiguous')
            if (len(body) < 103 or body[:7] != bytes.fromhex('00010000000000')
                    or body[7] not in (0, 1) or body[8] != 0 or body[50:54] != bytes(4)
                    or body[69:73] != bytes(4) or struct.unpack_from('<I', body, 35)[0] != 1
                    or struct.unpack_from('<I', body, 54)[0] != 1):
                raise ValueError('Ruled source input-role header differs')
            mode = struct.unpack_from('<I', body, 31)[0]
            if mode not in (0, 1, 2) or struct.unpack_from('<I', body, 73)[0] != (2 if mode == 2 else 1):
                raise ValueError('Ruled source auxiliary role count/mode differs')
            for slot in (9, 20):
                typed(reference(body, slot), 'D91D429C-1BB5-4640-B49F-69AF14F463E9')
            result_anchor_id = reference(body, 58)
            typed(result_anchor_id, 'D26351F0-5940-4D23-AA20-2C35475A6D9E')
            result_anchors = [a for a in anchors if a['object_id'] == result_anchor_id]
            if len(result_anchors) != 1 or result_anchors[0]['source_owner_object_id'] != owner:
                raise ValueError('Ruled source feature result-anchor owner differs')
            roles, recipes = [], []
            for role, slot in (('Profile', 39), ('Auxiliary', 77)):
                proxy_id = reference(body, slot)
                proxy_record, proxy = typed(proxy_id, PROXY)
                descriptors, properties = native_proxy_references(data, proxy_record)
                if (properties or len(descriptors) != 1 or len(proxy) != 105
                        or proxy[:6] != bytes(2)+struct.pack('<I', 1)
                        or proxy[17:23] != bytes(2)+struct.pack('<I', 1)
                        or proxy[34:52] != bytes(4)+struct.pack('<I', 8)+bytes(10)
                        or proxy[52:56] != b'\1\1\0\0' or proxy[64:68] != b'\1\1\0\0'
                        or proxy[79:82] != b'\1\0\0' or proxy[93] != 0
                        or reference(proxy, 94) != owner):
                    raise ValueError('Ruled source singleton proxy/owner framing differs')
                descriptor_id = descriptors[0]
                _, secondary = typed(reference(proxy, 23), '2DF7DA30-A4E4-4260-AFD1-D9C7154CB44B')
                proxy_helper_id, proxy_support_id = reference(proxy, 68), reference(proxy, 82)
                _, proxy_helper = typed(proxy_helper_id, HELPER)
                _, proxy_support = typed(proxy_support_id, SUPPORT)
                if (secondary != bytes.fromhex('0000010100')
                        or proxy_helper != bytes.fromhex('0001000000000000000000000000')
                        or len(proxy_support) != 58 or proxy_support[:12] != bytes(6)+b'\1\1'+struct.pack('<I', 1)
                        or reference(proxy_support, 12) != descriptor_id
                        or reference(proxy_support, 31) != proxy_id or proxy_support[-8:] != bytes(8)):
                    raise ValueError('Ruled source proxy/secondary/helper/support reciprocity differs')
                _, descriptor = typed(descriptor_id, TOPOLOGY)
                if (len(descriptor) != 276 or descriptor[:3] != bytes(3) or descriptor[3] not in (0, 1)
                        or struct.unpack_from('<I', descriptor, 15)[0] != 1
                        or descriptor[171:183] != struct.pack('<QI', 2, 1)
                        or struct.unpack_from('<I', descriptor, 194)[0] != 1
                        or descriptor[223:227] != b'\1\1\0\0' or descriptor[235:239] != b'\1\1\0\0'
                        or descriptor[250:253] != b'\1\0\0' or descriptor[264] != 0
                        or reference(descriptor, 265) != owner):
                    raise ValueError('Ruled source descriptor frame/trailer/owner differs')
                namespace, cursor = read_string(descriptor, 19)
                entity, cursor = read_string(descriptor, cursor)
                if len(namespace) != 36 or len(entity) != 36 or cursor != 171:
                    raise ValueError('Ruled source namespace extent differs')
                uuid.UUID(namespace); uuid.UUID(entity)
                context_id = reference(descriptor, 183)
                _, context = typed(context_id, EDGE_CONTEXT)
                if len(context) != 55 or context[:2] != bytes(2):
                    raise ValueError('Ruled source secondary cache outside captured55-byte framing')
                anchor_id = reference(descriptor, 198)
                selected = [a for a in anchors if a['object_id'] == anchor_id]
                if len(selected) != 1:
                    raise ValueError('Ruled source historical anchor missing or ambiguous')
                anchor = selected[0]
                source_owner = anchor['source_owner_object_id']
                typed(source_owner, PATCH)
                if source_owner == owner:
                    raise ValueError('Ruled source cannot be its own receiving feature')
                if body_selections is not None:
                    supplied = [a for a in body_selections['body_anchors'] if a['object_id'] == anchor_id]
                    if len(supplied) != 1 or any(supplied[0][k] != anchor[k] for k in ('native_body_object_id', 'source_owner_object_id')):
                        raise ValueError('Ruled source supplied historical anchor differs')
                helper_id, support_id = reference(descriptor, 239), reference(descriptor, 253)
                _, helper = typed(helper_id, HELPER)
                _, support = typed(support_id, SUPPORT)
                if (helper not in (bytes(10), bytes.fromhex('0001000000000000000000000000'))
                        or len(support) != 58 or support[:12] != bytes(6)+b'\1\1'+struct.pack('<I', 1)
                        or reference(support, 12) != source_owner or reference(support, 31) != descriptor_id
                        or support[-8:] != bytes(8)):
                    raise ValueError('Ruled source reciprocal support/helper framing differs')
                recipe_record, recipe_bytes = typed(reference(descriptor, 4), '7ACC2A03-0261-4879-A14A-A93D661A5BDC')
                recipe = decode_counted_recipe(data, recipe_record)
                operands = decode_ruled_edge_operands(recipe)
                if _replay_recipe(recipe) != recipe_bytes:
                    raise ValueError('Ruled source full counted recipe replay differs')
                recipes.append((recipe, recipe_bytes, operands))
                roles.append(dict(role=role, selection_record_object_id=proxy_id,
                    descriptor_object_id=descriptor_id, recipe_object_id=recipe_record.object_id,
                    body_anchor_object_id=anchor_id, native_body_object_id=anchor['native_body_object_id'],
                    historical_source_owner_object_id=source_owner, namespace_text=namespace, entity_guid_text=entity,
                    context_object_id=context_id, context_class_guid=EDGE_CONTEXT, context_payload_hex=context.hex(),
                    context_semantics=None, helper_object_id=helper_id, support_object_id=support_id,
                    support_payload_hex=support.hex(), proxy_support_object_id=proxy_support_id,
                    proxy_helper_object_id=proxy_helper_id, proxy_payload_hex=proxy.hex(),
                    proxy_support_payload_hex=proxy_support.hex(), feature_proxy_reference_offset=record.body+slot))
            if (roles[0]['selection_record_object_id'] == roles[1]['selection_record_object_id']
                    or roles[0]['descriptor_object_id'] == roles[1]['descriptor_object_id']
                    or roles[0]['recipe_object_id'] == roles[1]['recipe_object_id']
                    or recipes[0][1] != recipes[1][1]
                    or any(roles[0][k] != roles[1][k] for k in ('body_anchor_object_id', 'native_body_object_id', 'historical_source_owner_object_id'))):
                raise ValueError('Ruled profile/auxiliary selectors are not distinct identical-source recipe routes')
            position = 99 if mode == 2 else 88
            namespace, position = read_string(body, position)
            if namespace != str(uuid.UUID(int=0)) or body[position:position+3] != bytes(3):
                raise ValueError('Ruled source feature nil namespace/dependency prefix differs')
            count = struct.unpack_from('<I', body, position+3)[0]
            if count != (8 if mode == 2 else 6):
                raise ValueError('Ruled source feature repeated dependency count differs')
            dependency_ids = [reference(body, position+7+11*i) for i in range(count)]
            expected_ids = [reference(body, 20), reference(body, 9)]
            for role in roles:
                expected_ids.extend([role['selection_record_object_id'], role['descriptor_object_id']])
            if mode == 2:
                direction_id = reference(body, 88)
                _, direction = typed(direction_id, 'F2A7590D-6654-4674-B393-A2AEF4FEC48A')
                if (len(direction) != 202 or direction[:6] != bytes.fromhex('000008000000')
                        or struct.unpack_from('<I', direction, 99)[0] != 1
                        or reference(direction, 191) != owner):
                    raise ValueError('Ruled source retained direction selection owner differs')
                direction_descriptor_id = reference(direction, 103)
                _, direction_descriptor = typed(direction_descriptor_id, '5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
                if (len(direction_descriptor) != 263 or direction_descriptor[:2] != bytes(2)
                        or struct.unpack_from('<I', direction_descriptor, 13)[0] != 1
                        or reference(direction_descriptor, 252) != owner):
                    raise ValueError('Ruled source retained direction descriptor owner differs')
                expected_ids.extend([direction_id, direction_descriptor_id])
            if dependency_ids != expected_ids:
                raise ValueError('Ruled profile/auxiliary roles disagree with repeated feature dependencies')
            position += 7+11*count
            if struct.unpack_from('<I', body, position)[0] != 8:
                raise ValueError('Ruled source repeated feature metadata marker differs')
            label, position = read_string(body, position+4)
            index = struct.unpack_from('<Q', body, position)[0]
            name, position = read_string(body, position+8)
            if (label != 'SurfaceRuled' or index != metadata[0].get('stored_index')
                    or name != metadata[0].get('name') or len(body)-position != 66):
                raise ValueError('Ruled source repeated feature label/index/name/footer differs')
            if mapped is None:
                mapped = decode_body_asm_identifiers(data, records, member, members, body_identifier_summary)
            native_body = roles[0]['native_body_object_id']
            mappings = [(m, b) for m in mapped['decoded'] for b in m['bindings'] if b['native_body_object_id'] == native_body]
            if len(mappings) != 1:
                raise ValueError('Ruled source BODY has no unique validated same-asset mapping')
            mapping, binding = mappings[0]
            supplied = [b for m in body_identifier_summary['decoded'] if m['mapping_record_object_id'] == mapping['mapping_record_object_id']
                        for b in m['bindings'] if b['native_body_object_id'] == native_body]
            if len(supplied) != 1 or supplied[0]['asm_body_index'] != binding['asm_body_index']:
                raise ValueError('Ruled source supplied ASM BODY association differs')
            blob_member, body_id = mapping['history_blob_member'], binding['asm_body_index']
            if blob_member not in cache:
                blob = members[blob_member]; parsed = inspect_asm(blob)
                tags = decode_asm_generic_tags(blob, parsed=parsed, allow_fpm_tracking=True)
                topology = decode_topology(parsed, subtype_catalog=decode_asm_subtypes(blob, parsed=parsed))
                if tags['unresolved'] or topology['unresolved']:
                    raise ValueError('Ruled source requires complete initial names and reciprocal topology')
                cache[blob_member] = parsed, tags, topology
            parsed, tags, topology = cache[blob_member]
            recipe, _, operands = recipes[0]
            naming = match_recipe_tag_names(recipe, tags, parsed=parsed)
            entries = {e['name_table_index']: e for e in naming['name_entries']}
            if set(entries) != set(range(4)) or any(e['candidate_count'] != 1 for e in entries.values()):
                raise ValueError('Ruled source requires unique complete edge/face/adjacent-edge names')
            matched_names = [entries[i]['candidates'][0] for i in range(4)]
            if ([n['owner_kind'] for n in matched_names] != ['edge', 'face', 'edge', 'edge']
                    or any(n['body_graph_membership'] != [body_id] for n in matched_names)):
                raise ValueError('Ruled named operands are not typed members of the mapped source BODY')
            nodes = {n['index']: n for n in topology['nodes']}
            graphs = [g for g in topology['body_graphs'] if g['body_index'] == body_id]
            if len(graphs) != 1 or not graphs[0]['body_transform_is_identity']:
                raise ValueError('Ruled source BODY graph is missing/ambiguous/transformed')
            graph = graphs[0]; face_id = matched_names[1]['owner_record_index']
            edge_ids = [matched_names[i]['owner_record_index'] for i in (0, 2, 3)]
            if len(set(edge_ids)) != 3 or face_id not in graph['face_indices'] or any(e not in graph['edge_indices'] for e in edge_ids):
                raise ValueError('Ruled named source face/edges disagree with BODY membership')
            routes = []
            for edge_id in edge_ids:
                edge = nodes[edge_id]
                incident = [nodes[c] for g in topology['body_graphs'] for c in g['coedge_indices'] if nodes[c]['edge_index'] == edge_id]
                if len(incident) != 1:
                    raise ValueError('Ruled named edge lacks one boundary coedge')
                coedge = incident[0]; loop = nodes[coedge['loop_index']]
                if (loop['face_index'] != face_id or coedge['partner_index'] is not None
                        or edge['first_coedge_index'] != coedge['index'] or loop['index'] not in graph['loop_indices']
                        or nodes[coedge['next_coedge_index']]['previous_coedge_index'] != coedge['index']
                        or nodes[coedge['previous_coedge_index']]['next_coedge_index'] != coedge['index']):
                    raise ValueError('Ruled named edge/face/loop/coedge incidence is not reciprocal')
                routes.append(dict(edge_record_index=edge_id, coedge_record_index=coedge['index'],
                    loop_record_index=loop['index'], face_record_index=face_id))
            if len({r['loop_record_index'] for r in routes}) != 1:
                raise ValueError('Ruled endpoint edges do not share the captured source loop')
            edge = nodes[edge_ids[0]]; endpoint_vertices = []
            for ordinal, adjacent in enumerate(edge_ids[1:]):
                other = nodes[adjacent]
                common = {edge['start_vertex_index'], edge['end_vertex_index']} & {other['start_vertex_index'], other['end_vertex_index']}
                if len(common) != 1 or next(iter(common)) != edge['start_vertex_index' if ordinal == 0 else 'end_vertex_index']:
                    raise ValueError('Ruled named endpoint-edge intersections disagree with ordered edge vertices')
                vertex_id = next(iter(common)); vertex = nodes[vertex_id]; point = nodes[vertex['point_index']]
                if vertex_id not in graph['vertex_indices'] or point['kind'] != 'point':
                    raise ValueError('Ruled endpoint vertex/point is outside the mapped source BODY')
                endpoint_vertices.append(dict(operand_ordinal=ordinal, adjacent_edge_name_index=ordinal+2,
                    adjacent_edge_record_index=adjacent, vertex_record_index=vertex_id,
                    point_record_index=point['index'], raw_point=point['raw_origin']))
            curve = nodes[edge['curve_index']]
            if edge['start_vertex_index'] == edge['end_vertex_index'] or edge['is_reversed'] is not False or curve['kind'] != 'straight-curve':
                raise ValueError('Ruled selected cache is outside the captured non-reversed straight boundary')
            values = curve['raw_origin']+curve['direction']+[edge['start_parameter'], edge['end_parameter']]
            values += [x for e in endpoint_vertices for x in e['raw_point']]
            if any(not math.isfinite(x) for x in values) or not edge['end_parameter'] > edge['start_parameter']:
                raise ValueError('Ruled cached source coordinates/domain are not finite/positive')
            result['associations'].append(dict(owner_object_id=owner, descriptor_roles=roles,
                same_recipe_bytes=True, same_cached_edge=True, recipe=recipe,
                repeated_dependency_object_ids=dependency_ids,
                direction_selection_semantics=None,
                full_counted_recipe_payload_hex=recipes[0][1].hex(), exact_full_counted_recipe_replay=True,
                operation_operands=operands, naming_correspondence=naming,
                historical_source_owner_object_id=roles[0]['historical_source_owner_object_id'],
                body_anchor_object_id=roles[0]['body_anchor_object_id'], native_body_object_id=native_body,
                mapping_record_object_id=mapping['mapping_record_object_id'], history_blob_member=blob_member,
                explicit_asm_body_index=body_id, endpoint_incidence=endpoint_vertices,
                cached_source=dict(kind='Edge', edge_record_index=edge['index'], face_record_index=face_id,
                    curve_record_index=curve['index'], geometry=dict(kind='Line', raw_origin=curve['raw_origin'],
                        direction=curve['direction']), raw_endpoint_points=[e['raw_point'] for e in endpoint_vertices],
                    parameter_domain=[edge['start_parameter'], edge['end_parameter']],
                    stored_edge_reversal=edge['is_reversed'], incidence_routes=routes),
                API_input_edge_count=None, API_handle_identity=None, direction_parameter_mapping=None,
                current_source_identity=None, persistent_source_identity=None, qualified_historical_state=None,
                coordinate_scope='Raw mapped initial ASM cache with identity BODY transform; no general header-unit/occurrence conversion', scope=SCOPE))
        except (ValueError, KeyError, IndexError, TypeError, UnicodeError, struct.error) as error:
            result['unresolved'].append(dict(owner_object_id=owner, reason=str(error)))
    return result
