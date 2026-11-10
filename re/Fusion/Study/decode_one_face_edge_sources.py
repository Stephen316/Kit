"""Exact named one-face circular boundary source in the captured BRep Patch family."""
import math
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
from decode_asm_subtypes import decode_asm_subtypes
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections, HELPER, SUPPORT
from decode_brep import decode_topology
from decode_patch_continuity import PATCH, decode_patch_continuity
from decode_recipe_components import decode_counted_recipe
from decode_selection_context_recipes import TOPOLOGY
from decode_sketch import reference

SCOPE = ('Observed28-byte BRep Patch direct-edge/one-face named operands through reciprocal '
         'source anchor, same-asset BODY identifier and circular boundary incidence. Secondary '
         'context, opaque final qualifier, current/API/persistent identity and historical lifecycle unresolved.')


def _replay_recipe(recipe):
    value = bytearray(bytes(2)+struct.pack('<III', *recipe['stored_header_fields'], len(recipe['name_table'])))
    for entry in recipe['name_table']:
        value.extend(struct.pack('<I', len(entry['terms'])))
        for term in entry['terms']:
            name = term['name'].encode('ascii')
            value.extend(struct.pack('<I', len(name))+name+struct.pack('<II',
                term['stored_index'], term['stored_reference_component_count']))
            value.extend(bytes.fromhex(term['stored_reference_component_bytes_hex']))
            value.extend(struct.pack('<I', term['stored_reference_terminator_uint32']))
    kind = recipe['payload_kind'].encode('ascii')
    return bytes(value)+bytes(4)+struct.pack('<I', len(kind))+kind+bytes.fromhex(recipe['payload_hex'])


def decode_one_face_edge_sources(data, records, features, member, members,
                                body_identifier_summary, body_selections=None):
    """Return associations/unresolved/scope; no prior diagnostics are altered."""
    result = dict(associations=[], unresolved=[], scope=SCOPE)
    grouped, named = {}, {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    for feature in features:
        named.setdefault(feature['object_id'], []).append(feature)

    def typed(identity, guid=None):
        rows = grouped.get(identity, [])
        if len(rows) != 1 or guid is not None and rows[0].class_guid != guid:
            raise ValueError('One-face edge typed identity missing, ambiguous or wrong class')
        record = rows[0]
        return record, data[record.body:record.end]

    candidates = []
    for record in records:
        if not record.is_primary or record.class_guid != TOPOLOGY or record.end-record.body != 276:
            continue
        descriptor = data[record.body:record.end]
        try:
            owner_rows = grouped.get(reference(descriptor, 265), [])
            if not any(r.class_guid == PATCH for r in owner_rows):
                continue
            recipe_record, _ = typed(reference(descriptor, 4), '7ACC2A03-0261-4879-A14A-A93D661A5BDC')
            recipe = decode_counted_recipe(data, recipe_record)
            if recipe['payload_kind'] == 'edge_recipe_data' and len(bytes.fromhex(recipe['payload_hex'])) == 28:
                candidates.append(record)
        except (ValueError, KeyError, IndexError, TypeError, UnicodeError, struct.error) as error:
            result['unresolved'].append(dict(descriptor_object_id=record.object_id, reason=str(error)))
    if not candidates:
        return result

    # This existing reader validates receiving Patch→control→selection proxy→
    # descriptor and source/result anchors. Unrelated Patch failures stay with it.
    patches = decode_patch_continuity(data, records, features)
    sources = {}
    for patch in patches['decoded']:
        for source in patch['settings'].get('boundary_sources', []):
            if source.get('kind') == 'BRepEdgeRecipe':
                sources.setdefault(source['descriptor_object_id'], []).append((patch, source))
    anchors = decode_body_selections(data, records)
    mapped, caches = None, {}
    for record in candidates:
        descriptor = data[record.body:record.end]
        if len(descriptor) != 276:
            continue
        try:
            recipe_record, _ = typed(reference(descriptor, 4), '7ACC2A03-0261-4879-A14A-A93D661A5BDC')
            recipe = decode_counted_recipe(data, recipe_record)
            if recipe['payload_kind'] != 'edge_recipe_data' or len(bytes.fromhex(recipe['payload_hex'])) != 28:
                continue
            owner_id = reference(descriptor, 265)
            typed(owner_id, PATCH)
            typed(record.object_id, TOPOLOGY)
            if (member not in members or members[member] != data
                    or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat')):
                raise ValueError('One-face edge native Design member/bytes scope differs')
            owner_record, _ = typed(owner_id, PATCH)
            feature_rows = named.get(owner_id, [])
            if (len(feature_rows) != 1 or feature_rows[0].get('class_guid') != PATCH
                    or feature_rows[0].get('record_offset') != owner_record.start):
                raise ValueError('One-face edge receiving Patch metadata missing or ambiguous')
            choices = sources.get(record.object_id, [])
            if len(choices) != 1 or choices[0][0]['feature_object_id'] != owner_id:
                raise ValueError('One-face edge descriptor is not one validated receiving Patch boundary')
            _, source = choices[0]
            raw = bytes.fromhex(recipe['payload_hex'])
            words = struct.unpack('<7i', raw)
            if words != (0, -1, 1, 1, -1, 0, -1):
                raise ValueError('One-face edge operation fields/opaque qualifier outside captured28-byte framing')
            if (len(recipe['name_table']) != 2 or [e['table_index'] for e in recipe['name_table']] != [0, 1]
                    or any(len(e['terms']) != 1 for e in recipe['name_table'])
                    or any(e['terms'][0]['stored_reference_component_count'] != 1 for e in recipe['name_table'])):
                raise ValueError('One-face edge complete two-name counted framing differs')
            if _replay_recipe(recipe) != data[recipe_record.body:recipe_record.end] or struct.pack('<7i', *words) != raw:
                raise ValueError('One-face edge full recipe/operation payload replay differs')
            source_id, native_body_id = source['source_owner_object_id'], source['native_body_object_id']
            typed(source_id, PATCH)
            if source_id == owner_id:
                raise ValueError('One-face edge historical source and receiving Patch are not distinct')
            matches = [a for a in anchors['body_anchors'] if a['object_id'] == source['body_anchor_object_id']]
            if len(matches) != 1 or matches[0]['native_body_object_id'] != native_body_id or matches[0]['source_owner_object_id'] != source_id:
                raise ValueError('One-face edge independent source anchor differs')
            if body_selections is not None:
                supplied = [a for a in body_selections['body_anchors'] if a['object_id'] == source['body_anchor_object_id']]
                if len(supplied) != 1 or any(supplied[0][k] != matches[0][k] for k in ('native_body_object_id', 'source_owner_object_id')):
                    raise ValueError('One-face edge supplied anchor identity differs from native source')
            helper_id, support_id = reference(descriptor, 239), reference(descriptor, 253)
            if (descriptor[223:227] != b'\1\1\0\0' or descriptor[235:239] != b'\1\1\0\0'
                    or descriptor[250:253] != b'\1\0\0' or descriptor[264] != 0):
                raise ValueError('One-face edge descriptor trailer markers differ')
            _, helper = typed(helper_id, HELPER)
            _, support = typed(support_id, SUPPORT)
            if (helper != bytes.fromhex('0001000000000000000000000000')
                    or len(support) != 58 or support[:12] != bytes(6)+b'\1\1'+struct.pack('<I', 1)
                    or reference(support, 12) != source_id or reference(support, 31) != record.object_id
                    or support[-8:] != bytes(8)):
                raise ValueError('One-face edge helper/source-support reciprocal frame differs')
            if mapped is None:
                mapped = decode_body_asm_identifiers(data, records, member, members, body_identifier_summary)
            mappings = [(m, b) for m in mapped['decoded'] for b in m['bindings'] if b['native_body_object_id'] == native_body_id]
            if len(mappings) != 1:
                raise ValueError('One-face edge source BODY has no unique validated same-asset ASM mapping')
            mapping, binding = mappings[0]
            supplied = [b for m in body_identifier_summary['decoded'] if m['mapping_record_object_id'] == mapping['mapping_record_object_id']
                        for b in m['bindings'] if b['native_body_object_id'] == native_body_id]
            if len(supplied) != 1 or supplied[0]['asm_body_index'] != binding['asm_body_index']:
                raise ValueError('One-face edge supplied source BODY cache association differs')
            blob_member = mapping['history_blob_member']
            if blob_member not in caches:
                blob = members[blob_member]
                parsed = inspect_asm(blob)
                tags = decode_asm_generic_tags(blob, parsed=parsed, allow_fpm_tracking=True)
                topology = decode_topology(parsed, subtype_catalog=decode_asm_subtypes(blob, parsed=parsed))
                if tags['unresolved'] or topology['unresolved']:
                    raise ValueError('One-face edge requires complete initial naming and reciprocal topology')
                caches[blob_member] = parsed, tags, topology
            parsed, tags, topology = caches[blob_member]
            naming = match_recipe_tag_names(recipe, tags, parsed=parsed)
            entries = {entry['name_table_index']: entry for entry in naming['name_entries']}
            if set(entries) != {0, 1} or any(entry['candidate_count'] != 1 for entry in entries.values()):
                raise ValueError('One-face edge complete named-edge/face correspondence missing or ambiguous')
            edge_name, face_name = entries[0]['candidates'][0], entries[1]['candidates'][0]
            body_id = binding['asm_body_index']
            if (edge_name['owner_kind'] != 'edge' or face_name['owner_kind'] != 'face'
                    or edge_name['body_graph_membership'] != [body_id] or face_name['body_graph_membership'] != [body_id]):
                raise ValueError('One-face edge named operands are not typed members of the mapped source BODY')
            nodes = {node['index']: node for node in topology['nodes']}
            graphs = [g for g in topology['body_graphs'] if g['body_index'] == body_id]
            if len(graphs) != 1 or not graphs[0]['body_transform_is_identity']:
                raise ValueError('One-face edge requires one identity-transform mapped source BODY graph')
            graph = graphs[0]
            edge_id, face_id = edge_name['owner_record_index'], face_name['owner_record_index']
            if edge_id not in graph['edge_indices'] or face_id not in graph['face_indices']:
                raise ValueError('One-face edge named operand membership differs from source graph')
            edge, face = nodes[edge_id], nodes[face_id]
            incident = [nodes[c] for g in topology['body_graphs'] for c in g['coedge_indices'] if nodes[c]['edge_index'] == edge_id]
            if len(incident) != 1:
                raise ValueError('One-face edge requires one reciprocal boundary coedge')
            coedge = incident[0]
            loop = nodes[coedge['loop_index']]
            if (loop['face_index'] != face_id or coedge['partner_index'] is not None
                    or edge['first_coedge_index'] != coedge['index'] or loop['index'] not in graph['loop_indices']
                    or nodes[coedge['next_coedge_index']]['previous_coedge_index'] != coedge['index']
                    or nodes[coedge['previous_coedge_index']]['next_coedge_index'] != coedge['index']):
                raise ValueError('One-face edge/face/loop/coedge boundary incidence is not reciprocal')
            if edge['start_vertex_index'] != edge['end_vertex_index'] or edge['is_reversed'] is not False:
                raise ValueError('One-face edge circular endpoint/reversal shape differs')
            vertex = nodes[edge['start_vertex_index']]
            point = nodes[vertex['point_index']]
            curve = nodes[edge['curve_index']]
            if (curve['kind'] != 'ellipse-curve' or curve['stored_axis_ratio'] != 1.
                    or point['kind'] != 'point' or not math.isclose(edge['end_parameter']-edge['start_parameter'], 2*math.pi, abs_tol=1e-12)):
                raise ValueError('One-face edge requires the captured closed circular cache/domain')
            normal, axis, radius = curve['normal'], curve['stored_reference_axis'], curve['raw_major_radius']
            values = curve['raw_origin']+normal+axis+point['raw_origin']+[radius, edge['start_parameter'], edge['end_parameter']]
            if (any(not math.isfinite(v) for v in values) or radius <= 0
                    or not math.isclose(sum(v*v for v in normal), 1., abs_tol=1e-12)
                    or not math.isclose(sum(v*v for v in axis), radius*radius, abs_tol=1e-12)
                    or not math.isclose(sum(a*b for a, b in zip(normal, axis)), 0., abs_tol=1e-12)):
                raise ValueError('One-face edge circle frame is not finite/orthogonal/unit-normal')
            result['associations'].append(dict(descriptor_object_id=record.object_id, owner_object_id=owner_id,
                historical_source_owner_object_id=source_id, body_anchor_object_id=source['body_anchor_object_id'],
                native_body_object_id=native_body_id, mapping_record_object_id=mapping['mapping_record_object_id'],
                history_blob_member=blob_member, explicit_asm_body_index=body_id,
                recipe_object_id=recipe_record.object_id, recipe_payload_kind=recipe['payload_kind'],
                recipe=recipe, exact_full_recipe_payload_replay=True,
                operation_operands=dict(stored_direct_edge_name_index=0, stored_secondary_index=-1,
                    stored_face_operand_count=1, stored_face_name_index=1, stored_face_secondary_index=-1,
                    stored_penultimate_int32=0, stored_final_qualifier_int32=-1,
                    qualifier_semantics=None, payload_hex=raw.hex(), exact_payload_replay=True),
                naming_correspondence=naming,
                cached_source=dict(kind='Edge', edge_record_index=edge_id, face_record_index=face_id,
                    coedge_record_index=coedge['index'], loop_record_index=loop['index'],
                    curve_record_index=curve['index'], vertex_record_index=vertex['index'],
                    point_record_index=point['index'], raw_endpoint_point=point['raw_origin'],
                    parameter_domain=[edge['start_parameter'], edge['end_parameter']], is_closed=True,
                    stored_edge_reversal=edge['is_reversed'], stored_coedge_reversal=coedge['is_reversed'],
                    geometry=dict(kind='Circle', raw_center=curve['raw_origin'], normal=curve['normal'],
                        raw_reference_axis=curve['stored_reference_axis'], raw_radius=curve['raw_major_radius'])),
                context_object_id=source['context_record_object_id'], context_class_guid=source['context_class_guid'],
                context_payload_hex=source['context_payload_hex'], context_status=source['context_scope'],
                helper_object_id=helper_id, support_object_id=support_id,
                support_payload_hex=support.hex(), current_source_identity=None,
                persistent_source_identity=None, API_handle_identity=None, qualified_historical_state=None,
                traversal_parameter_mapping=None, coordinate_scope='Raw mapped initial ASM cache; identity BODY transform only; no general assembly/header-unit inference', scope=SCOPE))
        except (ValueError, KeyError, IndexError, TypeError, UnicodeError, struct.error) as error:
            result['unresolved'].append(dict(descriptor_object_id=record.object_id, reason=str(error)))
    return result
