"""Observed direct named-VERTEX cache associations, not full recipe evaluation.

Only the captured96-byte vertex operation branch is admitted. Its direct name
and two incident edge names establish cache correspondence. Auxiliary FACE and
terminal procedure fields remain separate; no current/final identity is claimed.
"""
import math
import struct
import uuid

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import ANCHOR, HELPER, SUPPORT, decode_body_selections
from decode_brep import decode_topology
from decode_brep_recipes import RECIPE_GUID
from decode_parameters import read_string
from decode_recipe_components import decode_counted_recipe
from decode_selection_context_recipes import TOPOLOGY
from decode_sketch import reference

POINT_CONTEXT = '994C518A-A831-400A-B7C7-16DAC55F4F1C'
BACKEND = '69EE2FA7-BCC7-449E-9CA9-976CEFDFED44'
FEATURE_CLASSES = {'ConstructionPoint': '5F40832C-61AA-4A05-95B1-EFA0BA483138',
                   'Scale': 'D45FD6C4-161B-4240-BFAC-83A7C2C97A0C'}
OPERATION_PREFIX = (0, 1, 1, -1, 2, 2, -1, 0, 0, -1, 3, -1, 0, 0, -1, 1, 0, 4)
SCOPE = 'Observed96-byte direct named vertex branch: typed descriptor/body/blob route and exact complete naming groups select cached VERTEX with two reciprocal incident EDGEs; auxiliary procedure, lifecycle and persistent identity unresolved'


def decode_named_vertex_selections(data, records, features, member, members, body_identifier_summary,
                                   body_selections=None, *, descriptor_ids=None):
    """Return separate associations/unresolved/scope; preserve all older warnings."""
    grouped = {}
    for record in records:
        if record.is_primary: grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: rows[0] for identity, rows in grouped.items() if len(rows) == 1}
    def typed(identity, guid=None):
        record = primary.get(identity)
        if record is None or guid is not None and record.class_guid != guid:
            raise ValueError('Named vertex typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]
    # Revalidate native anchors/mapping from actual native records, not annotations.
    body_summary = decode_body_selections(data, records)
    anchors = {a['object_id']: a for a in body_summary['body_anchors']}
    verified = decode_body_asm_identifiers(data, records, member, members, {'decoded': body_identifier_summary['decoded']})
    wanted = None if descriptor_ids is None else set(descriptor_ids)
    associations, unresolved = [], []
    for record in records:
        if not record.is_primary or record.class_guid != TOPOLOGY or wanted is not None and record.object_id not in wanted: continue
        payload = data[record.body:record.end]
        try:
            if len(payload) < 15: continue
            recipe_record, _ = typed(reference(payload, 4), RECIPE_GUID)
            recipe = decode_counted_recipe(data, recipe_record)
            raw = bytes.fromhex(recipe['payload_hex'])
            if wanted is None and (recipe['payload_kind'] != 'vertex_recipe_data' or len(raw) != 96): continue
            if recipe['payload_kind'] != 'vertex_recipe_data' or len(raw) != 96:
                raise ValueError('Only observed96-byte named vertex operation supported')
            fields = struct.unpack('<24i', raw)
            if tuple(fields[:18]) != OPERATION_PREFIX or any(v < 0 for v in fields[18:]):
                raise ValueError('Unsupported named vertex operation framing')
            if len(recipe['name_table']) != 4 or [n['table_index'] for n in recipe['name_table']] != list(range(4)):
                raise ValueError('Named vertex operation requires four complete name groups')
            if (len(payload) != 276 or payload[:4] != bytes(4) or struct.unpack_from('<I', payload, 15)[0] != 1
                    or payload[171:183] != struct.pack('<QI', 2, 1) or struct.unpack_from('<I', payload, 194)[0] != 1
                    or payload[223:227] != b'\1\1\0\0' or payload[235:239] != b'\1\1\0\0'
                    or payload[250:253] != b'\1\0\0' or payload[264] != 0):
                raise ValueError('Unsupported named vertex descriptor framing')
            namespace, cursor = read_string(payload, 19); entity, cursor = read_string(payload, cursor)
            if cursor != 171 or len(namespace) != 36 or len(entity) != 36:
                raise ValueError('Named vertex descriptor namespace extent disagrees')
            uuid.UUID(namespace); uuid.UUID(entity)
            owner_id = reference(payload, 265)
            feature_choices = [f for f in features if f['object_id'] == owner_id and f['kind'] in FEATURE_CLASSES]
            if len(feature_choices) != 1: raise ValueError('Named vertex descriptor owner feature unresolved')
            feature = feature_choices[0]; _, source = typed(owner_id, FEATURE_CLASSES[feature['kind']])
            backend_id = reference(source, 22 if feature['kind'] == 'ConstructionPoint' else 10)
            _, backend = typed(backend_id, BACKEND)
            if (len(backend) != 178 or backend[:23] != bytes(23) or struct.unpack_from('<I', backend, 75)[0] != 1
                    or struct.unpack_from('<I', backend, 47)[0] != (10 if feature['kind'] == 'ConstructionPoint' else 1)
                    or reference(backend, 79) != record.object_id or reference(backend, 167) != owner_id):
                raise ValueError('Named vertex backend/descriptor/feature ownership not reciprocal')
            context_id = reference(payload, 183); _, context = typed(context_id, POINT_CONTEXT)
            if len(context) != 28 or context[:2] != bytes(2) or context[-2:] != b'\1\0':
                raise ValueError('Unsupported named vertex point-context framing')
            context_point = list(struct.unpack_from('<3d', context, 2))
            if not all(math.isfinite(v) for v in context_point): raise ValueError('Nonfinite named vertex context')
            anchor_id = reference(payload, 198); _, anchor_bytes = typed(anchor_id, ANCHOR)
            anchor = anchors.get(anchor_id)
            if anchor is None or len(anchor_bytes) != 102 or reference(anchor_bytes, 80) != anchor['native_body_object_id'] or reference(anchor_bytes, 91) != anchor['source_owner_object_id']:
                raise ValueError('Named vertex historical anchor/native body correspondence disagrees')
            helper_id, support_id = reference(payload, 239), reference(payload, 253)
            _, helper = typed(helper_id, HELPER); _, support = typed(support_id, SUPPORT)
            if helper not in (bytes(10), bytes.fromhex('0001000000000000000000000000')):
                raise ValueError('Unsupported named vertex helper framing')
            if len(support) < 39 or support[:6] != bytes(6) or support[-8:] != bytes(8):
                raise ValueError('Unsupported named vertex support framing')
            count = struct.unpack_from('<I', support, 8)[0]
            if count not in (1, 2) or len(support) != 39+19*count or support[6:8] != b'\1\1':
                raise ValueError('Unsupported named vertex source support count')
            sources = [reference(support, 12+19*i) for i in range(count)]
            if (any(s not in primary for s in sources) or anchor['source_owner_object_id'] not in sources
                    or reference(support, 12+19*count) != record.object_id):
                raise ValueError('Named vertex support/descriptor/source ownership not reciprocal')
            mappings = [(m,b) for m in verified['decoded'] for b in m['bindings'] if b['native_body_object_id'] == anchor['native_body_object_id']]
            if len(mappings) != 1: raise ValueError('Named vertex source BODY lacks one validated same-asset mapping')
            mapping, binding = mappings[0]; blob_member = mapping['history_blob_member']; blob = members[blob_member]
            parsed = inspect_asm(blob); tags = decode_asm_generic_tags(blob, parsed, allow_fpm_tracking=True)
            matches = match_recipe_tag_names(recipe, tags, parsed=parsed)
            topology = decode_topology(parsed)
            if topology['unresolved']: raise ValueError('Named vertex source topology incomplete')
            nodes = {n['index']:n for n in topology['nodes']}
            graphs = [g for g in topology['body_graphs'] if g['body_index'] == binding['asm_body_index']]
            if len(graphs) != 1 or graphs[0]['body_transform_is_identity'] is not True:
                raise ValueError('Named vertex source BODY graph missing or transformed')
            graph = graphs[0]
            def candidate(index, kind):
                row = matches['name_entries'][index]
                if row['candidate_count'] != 1: raise ValueError('Named vertex complete term-group absent or ambiguous')
                found = row['candidates'][0]
                if found['owner_kind'] != kind or found['body_graph_membership'] != [graph['body_index']]:
                    raise ValueError('Named vertex candidate type/mapped BODY membership disagrees')
                return found
            selected = candidate(0, 'vertex'); vertex_id = selected['owner_record_index']; vertex = nodes[vertex_id]
            edge_matches = [candidate(index, 'edge') for index in (2, 3)]
            edge_ids = [c['owner_record_index'] for c in edge_matches]
            incident = [edge for edge in graph['edge_indices'] if vertex_id in (nodes[edge]['start_vertex_index'], nodes[edge]['end_vertex_index'])]
            if len(set(edge_ids)) != 2 or set(edge_ids) != set(incident) or vertex['first_edge_index'] not in edge_ids:
                raise ValueError('Named vertex complete two-edge incidence disagrees')
            point = nodes[vertex['point_index']]
            if point['kind'] != 'point': raise ValueError('Named vertex point is not typed point geometry')
            face = matches['name_entries'][1]
            face_status = 'Unresolved; auxiliary FACE naming absent/ambiguous in mapped cache'
            if face['candidate_count'] == 1:
                f = candidate(1, 'face')
                if not set(edge_ids) <= {t['edge_index'] for loop in graph['face_trim_loops'] if loop['face_index'] == f['owner_record_index'] for t in loop['trims']}:
                    raise ValueError('Named vertex auxiliary face does not contain named incident edges')
                face_status = 'Unique named FACE member in source BODY; full recipe role unresolved'
            associations.append({'descriptor_object_id': record.object_id, 'descriptor_owner_feature_object_id': owner_id,
                'feature_kind': feature['kind'], 'backend_object_id': backend_id, 'recipe_object_id': recipe['object_id'],
                'operation_evidence': {'payload_kind': recipe['payload_kind'], 'stored_direct_name_table_index': 0,
                    'stored_fixed_prefix_int32': list(fields[:18]), 'stored_opaque_tail_int32': list(fields[18:]),
                    'payload_hex': raw.hex(), 'procedure_status': 'Only observed direct-name0 branch and two-edge cache correspondence; full procedure/tail semantics unresolved'},
                'context_object_id': context_id, 'body_anchor_object_id': anchor_id, 'helper_object_id': helper_id,
                'support_object_id': support_id, 'support_source_record_object_ids': sources,
                'native_body_object_id': anchor['native_body_object_id'], 'source_owner_object_id': anchor['source_owner_object_id'],
                'mapping_record_object_id': mapping['mapping_record_object_id'], 'history_blob_member': blob_member,
                'asm_body_index': graph['body_index'], 'asm_stored_body_entity_id': binding['stored_handle'],
                'selected_name_terms': recipe['name_table'][0]['terms'], 'matched_vertex_attribute_record_index': selected['attribute_record_index'],
                'cached_vertex_record_index': vertex_id, 'cached_point_record_index': point['index'], 'cached_raw_point': point['raw_origin'],
                'incident_edge_matches': edge_matches, 'auxiliary_face_name_evidence': face, 'auxiliary_face_status': face_status,
                'point_context_cached_position': context_point,
                'point_context_agrees_after_identity_join': math.dist(context_point, point['raw_origin']) < 1e-9,
                'coordinate_scope': 'Raw mapped initial ASM cache; no occurrence/joint/world placement inferred',
                'identity_status': 'Unique direct complete naming group with typed mapped BODY and two-edge incidence; cached source correspondence only',
                'remaining_uncertainty': ['Full96-byte recipe operation/tail procedure', 'Auxiliary context/face role', 'Historical/current/final lifecycle and persistent topology identity']})
        except (ValueError, KeyError, IndexError, TypeError, UnicodeError, struct.error) as error:
            unresolved.append({'descriptor_object_id': record.object_id, 'reason': str(error)})
    return {'associations': associations, 'unresolved': unresolved, 'scope': SCOPE}
