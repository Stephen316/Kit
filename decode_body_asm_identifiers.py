"""Observed native mapping handles joined to typed ASM BODY stored entity IDs.

The key is scoped to the explicitly referenced same-asset history blob. It is
neither an ASM record index nor a global identity. Only the initial geometry
root table is accepted; history and trailing snapshots are not resolved. This
association does not establish current visibility, lifecycle or component owner.
"""

import struct

from asm_records import AsmReader, inspect_asm
from decode_body_properties import BODY, COLLECTION
from decode_parameters import read_string
from decode_sketch import reference

MAPPING = '74CA4562-59F8-4C97-8AD1-F8297C21F9AA'


def _validated_initial_geometry(parsed, raw):
    """Bound a complete initial section without accepting unsupported history."""
    if parsed['complete_token_stream']:
        return parsed, None
    if raw is None or not parsed.get('unresolved_reason'):
        raise ValueError('ASM identifier association requires a complete token stream or validated initial section')
    records = parsed['records']
    marker = next((r for r in records if r['record_kind'] == 'marker'), None)
    if (marker is None or marker['name'] != 'Begin-of-ASM-History-Data'
            or marker['section'] != 'geometry' or marker['index'] < parsed['header']['stored_entity_count']
            or parsed['last_complete_offset'] <= marker['end_offset']
            or not marker['end_offset'] < parsed['last_complete_offset'] <= len(raw)):
        raise ValueError('ASM incomplete stream lacks a proven closed initial geometry/history boundary')
    reader = AsmReader(raw)
    if reader.take(15) != b'ASM BinaryFile8':
        raise ValueError('ASM initial section signature disagrees')
    for _ in range(4):
        reader.number('q')
    header_tokens = [reader.token() for _ in range(6)]
    if [t['tag'] for t in header_tokens] != [7, 7, 7, 6, 6, 6] or not records or records[0]['offset'] != reader.cursor:
        raise ValueError('ASM initial geometry header/record boundary is not contiguous')
    previous_end = reader.cursor
    for record in records[:marker['index']]:
        if (record['record_kind'] != 'entity' or record['section'] != 'geometry'
                or record['offset'] != previous_end or not record['offset'] < record['end_offset'] <= marker['offset']
                or raw[record['end_offset'] - 1] != 17
                or any(not record['offset'] < t['offset'] < record['end_offset'] for t in record['tokens'])):
            raise ValueError('ASM initial geometry entities are not a contiguous complete prefix')
        previous_end = record['end_offset']
    if previous_end != marker['offset']:
        raise ValueError('ASM initial geometry does not end exactly at its history marker')
    reader.cursor = marker['offset']
    names = []
    for _ in range(32):
        token = reader.token()
        if token['kind'] not in ('entity_name_prefix', 'entity_name'):
            break
        names.append(token['value'])
        if token['kind'] == 'entity_name':
            break
    if token['kind'] != 'entity_name' or '-'.join(names) != 'Begin-of-ASM-History-Data' or reader.cursor != marker['end_offset']:
        raise ValueError('ASM initial geometry/history marker bytes disagree')
    # Revisit only the failed suffix until the first token error. This does not
    # recover it; it proves that the recorded failure occurs after the boundary.
    reader.cursor = parsed['last_complete_offset']
    failure = None
    try:
        token_count = 0
        while reader.cursor < len(raw):
            reader.token()
            token_count += 1
            if token_count > 1000000:
                raise ValueError('ASM incomplete suffix exceeds the token bound')
    except (ValueError, UnicodeError, struct.error) as error:
        failure = str(error)
    if failure != parsed['unresolved_reason'] or reader.cursor <= marker['end_offset']:
        raise ValueError('ASM incomplete-stream failure cannot be localized strictly after initial geometry')
    evidence = {'initial_geometry_complete': True, 'whole_token_stream_complete': False,
                'initial_geometry_record_count': marker['index'], 'history_marker_record_index': marker['index'],
                'history_marker_offset': marker['offset'], 'initial_geometry_end_offset': marker['offset'],
                'history_marker_end_offset': marker['end_offset'], 'last_complete_later_record_end_offset': parsed['last_complete_offset'],
                'unsupported_suffix_failure_cursor': reader.cursor, 'unsupported_later_history_reason': failure,
                'scope': 'Contiguous complete initial geometry only; whole stream and later history remain unsupported'}
    # decode_topology's completeness gate applies to this explicitly bounded
    # input only. Never mutate or relabel the original whole-stream summary.
    bounded = {**parsed, 'records': records[:marker['index'] + 1], 'complete_token_stream': True,
               'scope': evidence['scope']}
    return bounded, evidence


def _auxiliary_face(face, nodes, graphs):
    node = nodes.get(face['index'])
    if (node is None or node['kind'] != 'face' or node['stored_entity_id'] != -1
            or node['pattern_index'] is not None or node['next_face_index'] is not None
            or node['shell_index'] is not None or node['subshell_index'] is not None or node['is_double_sided']
            or any(face['index'] in g['face_indices'] for g in graphs.values())):
        raise ValueError('Unsupported detached auxiliary planar FACE layout/ownership')
    surface = nodes.get(node['surface_index'])
    loop = nodes.get(node['first_loop_index'])
    if (surface is None or surface['kind'] != 'plane-surface' or loop is None or loop['kind'] != 'loop'
            or loop['face_index'] != face['index'] or loop['next_loop_index'] is not None):
        raise ValueError('Auxiliary planar FACE/surface/loop ownership is unresolved or not reciprocal')
    coedge = nodes.get(loop['first_coedge_index'])
    if (coedge is None or coedge['kind'] != 'coedge' or coedge['loop_index'] != loop['index']
            or coedge['next_coedge_index'] != coedge['index'] or coedge['previous_coedge_index'] != coedge['index']
            or coedge['partner_index'] is not None or coedge['pcurve_index'] is not None):
        raise ValueError('Unsupported auxiliary planar FACE single-coedge ring')
    edge = nodes.get(coedge['edge_index'])
    if (edge is None or edge['kind'] != 'edge' or edge['first_coedge_index'] != coedge['index']
            or edge['start_vertex_index'] is None or edge['start_vertex_index'] != edge['end_vertex_index']):
        raise ValueError('Auxiliary planar FACE edge/coedge ownership is not reciprocal')
    vertex = nodes.get(edge['start_vertex_index'])
    point = nodes.get(vertex['point_index']) if vertex is not None else None
    curve = nodes.get(edge['curve_index'])
    if (vertex is None or vertex['kind'] != 'vertex' or vertex['first_edge_index'] != edge['index']
            or point is None or point['kind'] != 'point' or curve is None or curve['kind'] != 'ellipse-curve'):
        raise ValueError('Auxiliary planar FACE closed ellipse endpoint/curve geometry unresolved')
    return {'asm_record_index': face['index'], 'kind': 'face', 'stored_entity_id': -1,
            'loop_index': loop['index'], 'coedge_index': coedge['index'], 'edge_index': edge['index'],
            'endpoint_vertex_index': vertex['index'], 'endpoint_point_index': point['index'],
            'surface_index': surface['index'], 'surface_kind': 'plane-surface', 'curve_index': curve['index'],
            'raw_plane_origin': surface['raw_origin'], 'raw_plane_normal': surface['normal'],
            'ownership_status': 'Detached initial-geometry planar FACE; native entity and BODY ownership unresolved',
            'coordinate_scope': 'Stored raw ASM cache only; no source-plane identity or lifecycle inferred',
            'body_graph_membership': []}


def _body_identifiers(parsed, raw=None):
    parsed, prefix_evidence = _validated_initial_geometry(parsed, raw)
    records = parsed['records']
    limit = next((r['index'] for r in records if r['record_kind'] == 'marker'), len(records))
    count = parsed['header']['stored_entity_count']
    if not 2 <= count <= limit or records[0]['name'] != 'asmheader':
        raise ValueError('Unsupported ASM initial root table framing')
    declared = records[1:count]
    if any(r['name'] not in ('body', 'edge', 'face') or r['section'] != 'geometry' for r in declared):
        raise ValueError('Unsupported ASM mixed declared root kind or section')
    roots = [r for r in declared if r['name'] == 'body']
    auxiliary = [r for r in declared if r['name'] != 'body']
    if not roots or [r['index'] for r in records[:limit] if r['name'] == 'body'] != [r['index'] for r in roots]:
        raise ValueError('ASM initial BODY table is not exactly the declared root table')

    def pointer(token, expected=None):
        value = token['value']
        if token['kind'] != 'pointer' or not isinstance(value, int) or isinstance(value, bool):
            raise ValueError('ASM BODY link lacks a typed pointer')
        if value == -1:
            return None
        if not 0 <= value < limit:
            raise ValueError('ASM BODY pointer leaves the initial geometry table')
        if expected is not None and records[value]['name'] != expected:
            raise ValueError('ASM BODY pointer target has the wrong entity kind')
        return records[value]

    result = {}
    for body in roots:
        tokens = body['tokens']
        if len(tokens) != 6 or [t['kind'] for t in tokens] != ['pointer', 'integer', 'pointer', 'pointer', 'pointer', 'pointer']:
            raise ValueError('Unsupported typed ASM BODY identifier layout')
        identity = tokens[1]['value']
        if not isinstance(identity, int) or isinstance(identity, bool) or identity < -1 or identity in result:
            raise ValueError('ASM BODY stored entity IDs are invalid or ambiguous')
        pointer(tokens[0])
        pointer(tokens[2], 'pattern')
        lump = pointer(tokens[3], 'lump')
        pointer(tokens[4], 'wire')
        pointer(tokens[5], 'transform')
        # Check the BODY/lump chain independently of all coordinate comparisons.
        visited = set()
        while lump is not None:
            lt = lump['tokens']
            if len(lt) != 6 or [t['kind'] for t in lt] != ['pointer', 'integer', 'pointer', 'pointer', 'pointer', 'pointer']:
                raise ValueError('Unsupported typed ASM lump layout')
            lump_owner = pointer(lt[5], 'body')
            if lump['index'] in visited or lump_owner is None or lump_owner['index'] != body['index']:
                raise ValueError('ASM BODY/lump ownership is not reciprocal')
            visited.add(lump['index'])
            lump = pointer(lt[3], 'lump')
        if identity == -1:
            auxiliary.append(body)
        else:
            result[identity] = body
    evidence = []
    topology = None
    if auxiliary or prefix_evidence:
        # The observed extra edge is a detached initial-geometry root, not an
        # edge of either keyed body. Verify its own reciprocal vertex links and
        # require actual initial body graphs, without assigning an owning body.
        from decode_brep import decode_topology
        topology = decode_topology(parsed)
        nodes = {n['index']: n for n in topology['nodes']}
        graphs = {g['body_index']: g for g in topology['body_graphs']}
        for body in roots:
            node = nodes.get(body['index'])
            if node is None or node['kind'] != 'body' or body['index'] not in graphs:
                label = 'Auxiliary unnumbered BODY' if body['tokens'][1]['value'] == -1 else 'Mixed-root keyed BODY'
                raise ValueError(label + ' lacks a decoded initial geometry body graph: ' + str(body['index']))
        for edge in auxiliary:
            if edge['name'] == 'body':
                graph = graphs[edge['index']]
                evidence.append({'asm_record_index': edge['index'], 'kind': 'body', 'stored_entity_id': -1,
                                 'body_graph_index': edge['index'], 'topology_counts': graph['counts'],
                                 'transform_index': graph['transform_index'],
                                 'body_transform_is_identity': graph['body_transform_is_identity'],
                                 'ownership_status': 'Unnumbered declared initial BODY; no native body identity assigned',
                                 'lifecycle_status': 'Auxiliary stored geometry; source/result/current lifecycle unresolved'})
                continue
            if edge['name'] == 'face':
                evidence.append(_auxiliary_face(edge, nodes, graphs))
                continue
            tokens = edge['tokens']
            if (len(tokens) != 11 or [t['kind'] for t in tokens] != [
                    'pointer', 'integer', 'pointer', 'pointer', 'double', 'pointer', 'double',
                    'pointer', 'pointer', 'boolean_token', 'string']
                    or tokens[1]['value'] != -1 or tokens[2]['value'] != -1 or tokens[7]['value'] != -1):
                raise ValueError('Unsupported mixed-root detached edge layout')
            edge_node = nodes.get(edge['index'])
            if edge_node is None or edge_node['kind'] != 'edge':
                raise ValueError('Mixed-root edge lacks decoded initial geometry')
            if any(edge['index'] in g['edge_indices'] for g in graphs.values()):
                raise ValueError('Mixed-root edge is not the observed detached auxiliary variant')
            pointer(tokens[0])
            vertex_ids, point_ids = [], []
            for offset in (3, 5):
                vertex = pointer(tokens[offset], 'vertex')
                if vertex is None:
                    raise ValueError('Mixed-root auxiliary edge has no endpoint vertex')
                vt = vertex['tokens']
                if (len(vt) != 6 or [t['kind'] for t in vt] != [
                        'pointer', 'integer', 'pointer', 'pointer', 'integer', 'pointer']
                        or vt[1]['value'] != -1 or vt[2]['value'] != -1):
                    raise ValueError('Unsupported mixed-root auxiliary vertex layout')
                owner = pointer(vt[3], 'edge')
                point = pointer(vt[5], 'point')
                if owner is None or owner['index'] != edge['index']:
                    raise ValueError('Mixed-root auxiliary edge/vertex ownership is not reciprocal')
                point_node = nodes.get(point['index']) if point is not None else None
                if point_node is None or point_node['kind'] != 'point' or vertex['index'] not in nodes:
                    raise ValueError('Mixed-root endpoint point geometry is unresolved')
                vertex_ids.append(vertex['index'])
                point_ids.append(point['index'])
            curve = pointer(tokens[8])
            curve_node = nodes.get(curve['index']) if curve is not None else None
            if curve_node is None or curve_node['kind'] not in ('straight-curve', 'ellipse-curve'):
                raise ValueError('Mixed-root auxiliary curve is not a decoded observed Line/Ellipse primitive')
            evidence.append({'asm_record_index': edge['index'], 'kind': 'edge', 'stored_entity_id': -1,
                             'endpoint_vertex_indices': vertex_ids, 'endpoint_point_indices': point_ids,
                             'curve_index': curve['index'], 'curve_kind': curve['name'],
                             'ownership_status': 'Detached initial-geometry auxiliary edge; no native body/edge identity association inferred',
                             'body_graph_membership': []})
    if prefix_evidence is not None:
        prefix_evidence['validated_initial_geometry_body_graphs'] = topology['body_graphs']
    return result, evidence, prefix_evidence


def decode_body_asm_identifiers(data, records, member, members, body_blob_bindings):
    """Return nonmutating patches for already decoded native body/blob mappings.

    Call after body-binding variant recovery, before placement decoding. Clear
    old ordinal candidates for every populated mapping, including rejected ones;
    use only successful ``asm_body_index`` fields for subsequent placements.
    """
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Native body/ASM association reference missing, ambiguous or wrong class')
        return record

    decoded, unresolved, invalidate = [], [], []
    parsed_blobs = {}
    asset = member.rsplit('/FusionDesignSegmentType1/', 1)[0]
    for mapping in body_blob_bindings.get('decoded', []):
        if mapping.get('body_count') == 0:
            continue  # Empty tables have neither bodies nor an ASM blob.
        mapping_id = mapping['mapping_record_object_id']
        invalidate.append(mapping_id)
        try:
            native = typed(mapping_id, MAPPING)
            payload = data[native.body:native.end]
            if payload[:2] != bytes(2) or len(payload) < 6:
                raise ValueError('Unsupported native body/ASM mapping prefix')
            count = struct.unpack_from('<I', payload, 2)[0]
            cursor = 6 + 16 * count
            if not 1 <= count <= 100000 or cursor + 16 > len(payload):
                raise ValueError('Native body/ASM mapping count exceeds bounds')
            entries = [struct.unpack_from('<QQ', payload, 6 + 16 * i) for i in range(count)]
            if len({h for h, _ in entries}) != count or len({b for _, b in entries}) != count:
                raise ValueError('Native body/ASM mapping identifiers are ambiguous')
            owner = reference(payload, cursor)
            typed(owner, COLLECTION)
            if payload[cursor + 11] != 0:
                raise ValueError('Unsupported native body/ASM filename separator')
            filename, end = read_string(payload, cursor + 12)
            if (end != len(payload) or not filename.startswith('BREP.') or not filename.endswith('.smbh')
                    or '/' in filename or '\\' in filename):
                raise ValueError('Unsupported native body/ASM filename')
            blob_member = asset + '/Breps.BlobParts/' + filename
            if (mapping['owner_object_id'] != owner or mapping['body_count'] != count
                    or mapping['history_blob_member'] != blob_member
                    or [(b['stored_handle'], b['native_body_object_id']) for b in mapping['bindings']] != entries):
                raise ValueError('Decoded native mapping disagrees with its stored references')
            for _, identity in entries:
                typed(identity, BODY)
            if blob_member not in members:
                raise ValueError('Explicit same-asset ASM history blob is unavailable')
            if blob_member not in parsed_blobs:
                parsed_blobs[blob_member] = _body_identifiers(inspect_asm(members[blob_member]), members[blob_member])
            roots, auxiliary, prefix_evidence = parsed_blobs[blob_member]
            if set(roots) != {h for h, _ in entries}:
                raise ValueError('Native handles and initial ASM BODY stored IDs are not a bijection')
            patches = []
            for entry, (handle, identity) in zip(mapping['bindings'], entries):
                body = roots[handle]
                old = entry.get('candidate_asm_body_index')
                patches.append({
                    'native_body_object_id': identity, 'stored_handle': handle,
                    'asm_body_index': body['index'], 'asm_stored_entity_id': handle,
                    'asm_body_record_offset': body['offset'],
                    'asm_identifier_token_offset': body['tokens'][1]['offset'],
                    'association_status': 'Observed explicit same-blob native handle / typed ASM BODY stored-entity-ID association',
                    'identifier_scope': 'Identifier local to the explicitly referenced history blob; not an ASM record index',
                    'lifecycle_status': 'Initial stored geometry root; current visibility and historical/final lifecycle unresolved',
                    'previous_ordinal_candidate': old,
                    'ordinal_candidate_conflict': old is not None and old != body['index'],
                })
            output = {'mapping_record_object_id': mapping_id, 'owner_object_id': owner,
                      'history_blob_member': blob_member, 'body_count': count, 'bindings': patches}
            if auxiliary:
                output['auxiliary_declared_roots'] = auxiliary
                output['root_table_status'] = ('Mixed initial BODY and bounded detached-edge roots; BODY association uses stored IDs only'
                                               if all(a['kind'] == 'edge' for a in auxiliary) else
                                               'Mixed initial BODY and bounded unassociated auxiliary roots; BODY association uses stored IDs only')
            if prefix_evidence is not None:
                output['initial_geometry_validation'] = prefix_evidence
            decoded.append(output)
        except (ValueError, IndexError, KeyError, TypeError, UnicodeError, struct.error) as error:
            unresolved.append({'mapping_record_object_id': mapping_id, 'reason': str(error),
                               'ordinal_candidates_must_be_discarded': True})
    return {'decoded': decoded, 'unresolved': unresolved,
            'invalidate_ordinal_candidates_for_mapping_ids': invalidate,
            'scope': 'Observed typed per-blob BODY identifier association; no component ownership, final-body or solved placement inference'}
