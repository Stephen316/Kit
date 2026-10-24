"""Extend recipe operands joined to literal naming versions and initial ASM cache.

This does not materialize history or identify the geometry before Extend.
"""
import math
import struct
import uuid

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names, _terms_key
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

EXTEND = 'D2BCAE08-CF42-4316-865F-8ED1DFD548E4'
PROXY = '2CA5A1CD-C99B-4C9B-91AF-57989148E841'
EDGE_CONTEXT = '50AEE8B4-9456-4DD7-847D-6F6C909BBB9D'
SCOPE = ('Observed complete156-byte Extend edge/face/endpoint operands and literal journal-paired '
         'naming-version correspondence to an explicitly mapped initial ASM cache. No history '
         'materialization, before-feature geometry, current/persistent/API source identity or traversal claim.')


def decode_extend_edge_operands(recipe):
    """Replay the complete observed156-byte grammar, preserving inline order."""
    raw = bytes.fromhex(recipe['payload_hex'])
    table = recipe['name_table']
    if (recipe['payload_kind'] != 'edge_recipe_data' or len(raw) != 156
            or len(table) != 4 or [e['table_index'] for e in table] != list(range(4))
            or any(len(e['terms']) != 1 or e['terms'][0]['stored_index'] != 0
                   or e['terms'][0]['stored_reference_component_count'] != 1 for e in table)):
        raise ValueError('Extend operation requires the captured156-byte four-name family')
    words = struct.unpack('<39i', raw)
    if words[:6] != (0, -1, 1, 1, -1, 2) or words[-1] != -1:
        raise ValueError('Extend outer edge/face/count/opaque qualifier differs')
    rebuilt = list(words[:6]); endpoints = []
    for ordinal, adjacent in enumerate((2, 3)):
        start = 6+16*ordinal
        if words[start:start+5] != (-1, 1, 1, -1, 2) or words[start+15] != 0:
            raise ValueError('Extend vertex operand header/terminal differs')
        rebuilt.extend(words[start:start+5]); nested = []
        for j in range(2):
            at = start+5+5*j; fields = words[at:at+5]
            if fields[1:] != (-1, 0, 0, -1):
                raise ValueError('Extend inline edge framing differs')
            nested.append(dict(name_table_index=fields[0], stored_secondary_index=-1,
                stored_face_count=0, stored_endpoint_count=0, stored_terminal_int32=-1,
                relative_offset=4*at, payload_hex=raw[4*at:4*(at+5)].hex()))
            rebuilt.extend(fields)
        order = [n['name_table_index'] for n in nested]
        if order not in ([0, adjacent], [adjacent, 0]):
            raise ValueError('Extend endpoint does not contain direct edge and its distinct adjacent edge')
        rebuilt.append(0)
        endpoints.append(dict(operand_ordinal=ordinal, relative_offset=4*start,
            stored_direct_vertex_name_index=-1, stored_face_count=1, face_name_index=1,
            stored_face_secondary_index=-1, stored_edge_count=2, nested_edges=nested,
            stored_inline_edge_name_order=order, adjacent_edge_name_index=adjacent,
            stored_terminal_int32=0, payload_hex=raw[4*start:4*(start+16)].hex()))
    rebuilt.append(-1)
    if struct.pack('<39i', *rebuilt) != raw:
        raise ValueError('Extend complete operation replay differs')
    return dict(stored_direct_edge_name_index=0, stored_secondary_index=-1,
        stored_face_count=1, face_name_index=1, stored_face_secondary_index=-1,
        stored_endpoint_count=2, endpoint_operands=endpoints,
        stored_final_qualifier_int32=-1, qualifier_semantics=None,
        payload_hex=raw.hex(), exact_full_operation_payload_replay=True)


def decode_extend_edge_sources(data, records, features, member, members,
                               body_identifier_summary, body_selections=None):
    result = dict(associations=[], unresolved=[], scope=SCOPE)
    candidates = [r for r in records if r.is_primary and r.class_guid == EXTEND]
    if not candidates:
        return result
    # Import only when the owning native family exists; absent families are cheap.
    from decode_asm_name_versions import decode_asm_name_versions
    grouped, metadata = {}, {}
    for r in records:
        if r.is_primary: grouped.setdefault(r.object_id, []).append(r)
    for f in features: metadata.setdefault(f['object_id'], []).append(f)

    def typed(identity, guid=None):
        rows = grouped.get(identity, [])
        if len(rows) != 1 or guid is not None and rows[0].class_guid != guid:
            raise ValueError('Extend source typed reference missing, ambiguous or wrong class')
        r = rows[0]
        return r, data[r.body:r.end]

    anchors = decode_body_selections(data, records)['body_anchors']
    mapped, cache = None, {}
    for candidate in candidates:
        owner = candidate.object_id
        try:
            rec, body = typed(owner, EXTEND)
            if (member not in members or members[member] != data
                    or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat')):
                raise ValueError('Extend native Design member/bytes scope differs')
            fs = metadata.get(owner, [])
            if (len(fs) != 1 or fs[0].get('class_guid') != EXTEND
                    or fs[0].get('record_offset') != rec.start):
                raise ValueError('Extend source feature metadata missing or ambiguous')
            if (len(body) < 160 or body[:2] != bytes(2)
                    or struct.unpack_from('<I', body, 2)[0] not in (0, 1)
                    or struct.unpack_from('<I', body, 6)[0] not in (0, 1, 2)
                    or body[21:33] != bytes(12) or struct.unpack_from('<I', body, 33)[0] != 1):
                raise ValueError('Extend feature common controls/count frame differs')
            binding_id = reference(body, 10)
            typed(binding_id, 'D91D429C-1BB5-4640-B49F-69AF14F463E9')
            proxy_id = reference(body, 37)
            proxy_rec, proxy = typed(proxy_id, PROXY)
            descriptors, properties = native_proxy_references(data, proxy_rec)
            count = len(descriptors); shift = 11*(count-1)
            if (count not in (1, 2) or len(set(descriptors)) != count or properties
                    or len(proxy) != 105+shift or proxy[:2] != bytes(2)
                    or struct.unpack_from('<I', proxy, 2)[0] != count
                    or [reference(proxy, 6+11*i) for i in range(count)] != descriptors
                    or proxy[17+shift:23+shift] != bytes(2)+struct.pack('<I', 1)
                    or proxy[34+shift:52+shift] != bytes(4)+struct.pack('<I', 8)+bytes(10)
                    or proxy[52+shift:56+shift] != b'\1\1\0\0'
                    or proxy[64+shift:68+shift] != b'\1\1\0\0'
                    or proxy[79+shift:82+shift] != b'\1\0\0'
                    or proxy[93+shift] != 0 or reference(proxy, 94+shift) != owner):
                raise ValueError('Extend proxy complete counted/header/owner framing differs')
            _, secondary = typed(reference(proxy, 23+shift), '2DF7DA30-A4E4-4260-AFD1-D9C7154CB44B')
            proxy_helper_id = reference(proxy, 68+shift)
            proxy_support_id = reference(proxy, 82+shift)
            _, helper = typed(proxy_helper_id, HELPER)
            _, support = typed(proxy_support_id, SUPPORT)
            if (secondary != bytes.fromhex('0000010100')
                    or helper != bytes.fromhex('0001000000000000000000000000')
                    or len(support) != 58+19*(count-1)
                    or support[:12] != bytes(6)+b'\1\1'+struct.pack('<I', count)
                    or [reference(support, 12+19*i) for i in range(count)] != descriptors
                    or reference(support, 12+19*count) != proxy_id or support[-8:] != bytes(8)):
                raise ValueError('Extend proxy secondary/helper/support complete framing differs')
            namespace, position = read_string(body, 48)
            if namespace != str(uuid.UUID(int=0)) or body[position:position+3] != bytes(3):
                raise ValueError('Extend nil namespace/dependency prefix differs')
            dep_count = struct.unpack_from('<I', body, position+3)[0]
            deps = [reference(body, position+7+11*i) for i in range(dep_count)] if dep_count <= 4 else []
            if dep_count != count+2 or deps != [binding_id, proxy_id]+descriptors:
                raise ValueError('Extend repeated feature dependency aliases differ')
            position += 7+11*dep_count
            marker = struct.unpack_from('<I', body, position)[0]
            label, position = read_string(body, position+4)
            index = struct.unpack_from('<Q', body, position)[0]
            name, position = read_string(body, position+8)
            if (marker not in (10, 13) or label != 'SurfaceExtend'
                    or index != fs[0].get('stored_index') or name != fs[0].get('name')
                    or len(body)-position != 66):
                raise ValueError('Extend repeated metadata/footer extent differs')
            descriptor_rows = []
            for ordinal, descriptor_id in enumerate(descriptors):
                _, descriptor = typed(descriptor_id, TOPOLOGY)
                if (len(descriptor) != 276 or descriptor[:3] != bytes(3) or descriptor[3] not in (0, 1)
                        or struct.unpack_from('<I', descriptor, 15)[0] != 1
                        or descriptor[171:183] != struct.pack('<QI', 2, 1)
                        or struct.unpack_from('<I', descriptor, 194)[0] != 1
                        or descriptor[223:227] != b'\1\1\0\0' or descriptor[235:239] != b'\1\1\0\0'
                        or descriptor[250:253] != b'\1\0\0' or descriptor[264] != 0
                        or reference(descriptor, 265) != owner):
                    raise ValueError('Extend descriptor complete marker/count/owner framing differs')
                ns, at = read_string(descriptor, 19); entity, at = read_string(descriptor, at)
                if at != 171 or len(ns) != 36 or len(entity) != 36:
                    raise ValueError('Extend descriptor namespace extent differs')
                uuid.UUID(ns); uuid.UUID(entity)
                context_id = reference(descriptor, 183)
                _, context = typed(context_id, EDGE_CONTEXT)
                if len(context) != 55 or context[:2] != bytes(2):
                    raise ValueError('Extend opaque secondary context framing differs')
                anchor_id = reference(descriptor, 198)
                found = [a for a in anchors if a['object_id'] == anchor_id]
                if len(found) != 1: raise ValueError('Extend source anchor missing or ambiguous')
                anchor = found[0]; source_owner = anchor['source_owner_object_id']
                typed(source_owner, PATCH)
                if source_owner == owner: raise ValueError('Extend source owner is receiving feature')
                if body_selections is not None:
                    supplied = [a for a in body_selections['body_anchors'] if a['object_id'] == anchor_id]
                    if len(supplied) != 1 or any(supplied[0][k] != anchor[k] for k in ('native_body_object_id', 'source_owner_object_id')):
                        raise ValueError('Extend supplied anchor evidence differs')
                helper_id, support_id = reference(descriptor, 239), reference(descriptor, 253)
                _, dh = typed(helper_id, HELPER); _, ds = typed(support_id, SUPPORT)
                if (dh not in (bytes(10), bytes.fromhex('0001000000000000000000000000'))
                        or len(ds) != 58 or ds[:12] != bytes(6)+b'\1\1'+struct.pack('<I', 1)
                        or reference(ds, 12) != source_owner or reference(ds, 31) != descriptor_id
                        or ds[-8:] != bytes(8)):
                    raise ValueError('Extend descriptor reciprocal support/helper framing differs')
                recipe_rec, recipe_bytes = typed(reference(descriptor, 4), '7ACC2A03-0261-4879-A14A-A93D661A5BDC')
                recipe = decode_counted_recipe(data, recipe_rec)
                operands = decode_extend_edge_operands(recipe)
                if _replay_recipe(recipe) != recipe_bytes:
                    raise ValueError('Extend complete counted recipe replay differs')
                if mapped is None:
                    mapped = decode_body_asm_identifiers(data, records, member, members, body_identifier_summary)
                matches = [(m, b) for m in mapped['decoded'] for b in m['bindings'] if b['native_body_object_id'] == anchor['native_body_object_id']]
                if len(matches) != 1: raise ValueError('Extend source lacks unique same-asset native BODY mapping')
                mapping, binding = matches[0]
                supplied = [b for m in body_identifier_summary['decoded'] if m['mapping_record_object_id'] == mapping['mapping_record_object_id']
                            for b in m['bindings'] if b['native_body_object_id'] == anchor['native_body_object_id']]
                if len(supplied) != 1 or supplied[0]['asm_body_index'] != binding['asm_body_index']:
                    raise ValueError('Extend supplied native BODY/ASM identity differs')
                blob_member, body_id = mapping['history_blob_member'], binding['asm_body_index']
                if blob_member not in cache:
                    blob = members[blob_member]; parsed = inspect_asm(blob)
                    tags = decode_asm_generic_tags(blob, parsed=parsed, allow_fpm_tracking=True)
                    topology = decode_topology(parsed, subtype_catalog=decode_asm_subtypes(blob, parsed=parsed))
                    versions = decode_asm_name_versions(blob, parsed=parsed)
                    if tags['unresolved'] or topology['unresolved'] or versions['unresolved']:
                        raise ValueError('Extend initial naming/topology/version evidence incomplete')
                    cache[blob_member] = parsed, tags, topology, versions
                parsed, tags, topology, versions = cache[blob_member]
                naming = match_recipe_tag_names(recipe, tags, parsed=parsed)
                entries = {e['name_table_index']:e for e in naming['name_entries']}
                if set(entries) != set(range(4)) or any(entries[i]['candidate_count'] != 1 for i in (0, 2, 3)):
                    raise ValueError('Extend direct/adjacent edge complete names are absent or ambiguous')
                edge_names = [entries[i]['candidates'][0] for i in (0, 2, 3)]
                if any(n['owner_kind'] != 'edge' or n['body_graph_membership'] != [body_id] for n in edge_names):
                    raise ValueError('Extend named edges are not unique typed members of mapped initial BODY')
                version_evidence = None
                if entries[1]['candidate_count'] == 1:
                    face_name = entries[1]['candidates'][0]
                    if face_name['owner_kind'] != 'face' or face_name['body_graph_membership'] != [body_id]:
                        raise ValueError('Extend initial named face is outside mapped BODY')
                    face_id = face_name['owner_record_index']
                elif entries[1]['candidate_count'] == 0:
                    wanted = _terms_key(recipe['name_table'][1]['terms'])
                    pairs = [v for v in versions['decoded'] if _terms_key(v['trailing_attribute']['terms']) == wanted]
                    if len(pairs) != 1 or pairs[0]['initial_body_record_index'] != body_id:
                        raise ValueError('Extend missing face name lacks unique literal paired version in mapped initial BODY')
                    version_evidence = pairs[0]; face_id = version_evidence['owner_face_record_index']
                else:
                    raise ValueError('Extend face complete-name candidates ambiguous')
                nodes = {n['index']:n for n in topology['nodes']}
                graphs = [g for g in topology['body_graphs'] if g['body_index'] == body_id]
                if len(graphs) != 1 or not graphs[0]['body_transform_is_identity']:
                    raise ValueError('Extend initial BODY graph missing/ambiguous/transformed')
                graph = graphs[0]; edge_ids = [n['owner_record_index'] for n in edge_names]
                if len(set(edge_ids)) != 3 or face_id not in graph['face_indices'] or any(e not in graph['edge_indices'] for e in edge_ids):
                    raise ValueError('Extend named operands disagree with initial BODY graph')
                routes = []; paired_face_loops = []
                for eid in edge_ids:
                    edge = nodes[eid]
                    found = [nodes[c] for g in topology['body_graphs'] for c in g['coedge_indices'] if nodes[c]['edge_index'] == eid]
                    ids = {c['index'] for c in found}
                    if len(found) not in (1, 2) or edge['first_coedge_index'] not in ids:
                        raise ValueError('Extend initial operand edge lacks bounded reciprocal coedges')
                    face_ids = []; matching_loops = []
                    for coedge in found:
                        loop = nodes[coedge['loop_index']]
                        partner = coedge['partner_index']
                        if (loop['index'] not in graph['loop_indices'] or loop['face_index'] not in graph['face_indices']
                                or nodes[coedge['next_coedge_index']]['previous_coedge_index'] != coedge['index']
                                or nodes[coedge['previous_coedge_index']]['next_coedge_index'] != coedge['index']
                                or (len(found) == 1 and partner is not None)
                                or (len(found) == 2 and (partner not in ids or partner == coedge['index']
                                    or nodes[partner]['partner_index'] != coedge['index']))):
                            raise ValueError('Extend initial edge/face/loop/coedge links are not reciprocal')
                        face_ids.append(loop['face_index'])
                        if loop['face_index'] == face_id: matching_loops.append(loop['index'])
                        routes.append(dict(edge_record_index=eid, coedge_record_index=coedge['index'],
                            loop_record_index=loop['index'], face_record_index=loop['face_index'],
                            partner_coedge_record_index=partner))
                    if len(matching_loops) != 1:
                        raise ValueError('Extend named edge lacks unique incidence to the literal named face owner')
                    paired_face_loops.extend(matching_loops)
                if len(set(paired_face_loops)) != 1:
                    raise ValueError('Extend named operand edges do not share the literal paired-face loop')
                edge = nodes[edge_ids[0]]; endpoints = []
                for endpoint, adjacent in zip(operands['endpoint_operands'], edge_ids[1:]):
                    other = nodes[adjacent]
                    common = {edge['start_vertex_index'],edge['end_vertex_index']} & {other['start_vertex_index'],other['end_vertex_index']}
                    if len(common) != 1: raise ValueError('Extend endpoint operand intersection is not unique')
                    vid = next(iter(common)); vertex = nodes[vid]; point = nodes[vertex['point_index']]
                    if vid not in graph['vertex_indices'] or point['kind'] != 'point':
                        raise ValueError('Extend operand vertex/point is outside initial BODY')
                    endpoints.append(dict(operand_ordinal=endpoint['operand_ordinal'],
                        stored_inline_edge_name_order=endpoint['stored_inline_edge_name_order'],
                        adjacent_edge_name_index=endpoint['adjacent_edge_name_index'],
                        adjacent_edge_record_index=adjacent, vertex_record_index=vid,
                        point_record_index=point['index'], raw_point=point['raw_origin']))
                if {e['vertex_record_index'] for e in endpoints} != {edge['start_vertex_index'],edge['end_vertex_index']} or len({e['vertex_record_index'] for e in endpoints}) != 2:
                    raise ValueError('Extend operand intersections do not cover distinct initial edge endpoints')
                curve = nodes[edge['curve_index']]
                if curve['kind'] != 'straight-curve' or type(edge['is_reversed']) is not bool:
                    raise ValueError('Extend operand cache outside captured straight-edge family')
                values = curve['raw_origin']+curve['direction']+[edge['start_parameter'],edge['end_parameter']]+[x for e in endpoints for x in e['raw_point']]
                if any(not math.isfinite(x) for x in values) or not edge['end_parameter'] > edge['start_parameter']:
                    raise ValueError('Extend initial cache coordinates/domain are not finite/positive')
                descriptor_rows.append(dict(operand_ordinal=ordinal, selection_record_object_id=proxy_id,
                    descriptor_object_id=descriptor_id, recipe_object_id=recipe_rec.object_id,
                    recipe=recipe, operation_operands=operands, full_counted_recipe_payload_hex=recipe_bytes.hex(),
                    exact_full_counted_recipe_replay=True, naming_correspondence=naming,
                    literal_face_name_version=version_evidence,
                    qualification='Literal paired naming-version to initial-cache operand correspondence' if version_evidence else 'Exact initial-cache operand naming correspondence',
                    historical_source_owner_object_id=source_owner, body_anchor_object_id=anchor_id,
                    native_body_object_id=anchor['native_body_object_id'], mapping_record_object_id=mapping['mapping_record_object_id'],
                    history_blob_member=blob_member, explicit_asm_body_index=body_id,
                    context_object_id=context_id, context_class_guid=EDGE_CONTEXT, context_payload_hex=context.hex(),
                    context_semantics=None, descriptor_support_object_id=support_id,
                    descriptor_payload_hex=descriptor.hex(), descriptor_support_payload_hex=ds.hex(),
                    endpoint_incidence=endpoints, stored_initial_operand_cache=dict(kind='Edge',
                        edge_record_index=edge['index'],face_record_index=face_id,curve_record_index=curve['index'],
                        geometry=dict(kind='Line',raw_origin=curve['raw_origin'],direction=curve['direction']),
                        raw_endpoint_points=[e['raw_point'] for e in endpoints],
                        stored_start_vertex_index=edge['start_vertex_index'],stored_end_vertex_index=edge['end_vertex_index'],
                        stored_edge_reversal=edge['is_reversed'],
                        boundary_in_initial_cache=sum(r['edge_record_index'] == edge['index'] for r in routes) == 1,
                        selected_edge_incident_face_indices=sorted({r['face_record_index'] for r in routes if r['edge_record_index'] == edge['index']}),
                        parameter_domain=[edge['start_parameter'],edge['end_parameter']],
                        incidence_routes=routes, scope='Mapped initial ASM cache only; not a qualified pre-Extend state'),
                    exact_selected_source_identity=None,API_handle_identity=None,current_source_identity=None,
                    persistent_source_identity=None,qualified_historical_state=None,traversal=None))
            result['associations'].append(dict(owner_object_id=owner, descriptor_operands=descriptor_rows,
                selection_record_object_id=proxy_id, repeated_dependency_object_ids=deps,
                proxy_payload_hex=proxy.hex(),proxy_helper_object_id=proxy_helper_id,
                proxy_support_object_id=proxy_support_id,proxy_support_payload_hex=support.hex(),
                feature_payload_hex=body.hex(),stored_metadata_marker=marker,
                coordinate_scope='Raw initial ASM cache; identity BODY transform only, no general occurrence/header-unit conversion',scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
            result['unresolved'].append(dict(owner_object_id=owner,reason=str(error)))
    return result
