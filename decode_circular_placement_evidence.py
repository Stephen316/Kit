"""Circular element naming-key/cache joins and measured relative rigid fits.

No per-element matrix is claimed to be serialized. Correspondences use native
controller keys, reciprocal face naming attributes and typed vertex incidence,
never nearest coordinates, bounds, angles or result-list order.
"""

from itertools import combinations
import math
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import encode_generic_tag_payload
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections
from decode_brep import decode_topology
from decode_circular_patterns import FEATURE, CONTROL, ELEMENT, COLLECTION
from decode_sketch import reference


def _face_names(blob, parsed, graph):
    """Complete reciprocal attribute audit on every face of this bounded BODY."""
    records = parsed['records']
    limit = next((r['index'] for r in records if r['record_kind'] == 'marker'), len(records))
    result = {}
    for face_id in graph['face_indices']:
        face = records[face_id]
        current, previous, visited, terms = face['tokens'][0]['value'], -1, [], []
        while current != -1:
            if not isinstance(current, int) or not 0 <= current < limit or current in visited or len(visited) >= 16:
                raise ValueError('Circular face naming attribute chain leaves its bounded initial owner')
            visited.append(current); attr = records[current]; t = attr['tokens']
            if attr['name'] != 'ATTRIB_CUSTOM-attrib' or len(t) not in (17, 19):
                raise ValueError('Unobserved attribute prevents complete circular face-kind naming coverage')
            if ([v['kind'] for v in t[:5]] != ['pointer', 'integer', 'pointer', 'pointer', 'pointer']
                    or t[0]['value'] != -1 or t[1]['value'] != -1 or t[3]['value'] != previous or t[4]['value'] != face_id):
                raise ValueError('Circular face naming attribute owner/next/previous links disagree')
            def integer(i):
                if t[i]['kind'] != 'integer' or not isinstance(t[i]['value'], int) or isinstance(t[i]['value'], bool):
                    raise ValueError('Circular naming field lacks typed integer')
                return t[i]['value']
            if ([t[i]['kind'] for i in (5, 9, 12)] != ['string']*3
                    or t[5]['value'] != 'generic_tag_attrib_def'
                    or t[9]['value'] != 'generic_tag_attrib_def '
                    or [integer(i) for i in (6, 7, 8, 10)] != [3, 3, -1, 1]):
                raise ValueError('Unobserved counted circular face naming schema')
            name = t[12]['value']; count = integer(14)
            if (not isinstance(name, str) or not 1 <= len(name) <= 32 or not name.lstrip('-').isdigit()
                    or integer(11) != len(name.encode('ascii')) or count not in (1, 3)
                    or len(t) != 16+count or integer(15+count) != 0 or not 0 <= integer(13) <= 0xffffffff):
                raise ValueError('Circular face name/component count or terminator disagrees')
            components = [integer(15+i) for i in range(count)]
            if any(not 1 <= value <= 0x7fffffff for value in components):
                raise ValueError('Unobserved circular naming component range')
            term = {'name': name, 'stored_index': integer(13), 'stored_reference_components_int32': components}
            replay = {'definition_name': t[5]['value'], 'stored_definition_schema_fields': [3, 3, -1],
                      'stored_namespace_text': t[9]['value'], 'terms': [term]}
            if encode_generic_tag_payload(replay) != blob[t[5]['offset']:attr['end_offset']-1]:
                raise ValueError('Circular counted naming payload does not replay exact source bytes')
            terms.append((name, term['stored_index'], tuple(components)))
            previous, current = current, t[2]['value']
        if not terms or len(set(terms)) != 1:
            raise ValueError('Circular face lacks one unambiguous complete naming tuple')
        name, index, components = terms[0]
        result[face_id] = {'name_key': (name, index), 'components': components, 'attribute_indices': visited}
    if len(result) != 6 or len({v['name_key'] for v in result.values()}) != 6:
        raise ValueError('Only observed six uniquely named face BODYs are supported')
    return result


def _vertices(graph, nodes, names):
    if graph['counts'].get('vertex') != 8 or graph['counts'].get('edge') != 12 or not graph['body_transform_is_identity']:
        raise ValueError('Only observed eight-vertex/twelve-edge identity-transform cache BODYs are supported')
    signatures = {vertex: set() for vertex in graph['vertex_indices']}
    for cid in graph['coedge_indices']:
        coedge = nodes[cid]; loop = nodes[coedge['loop_index']]; face_id = loop['face_index']
        if face_id not in names:
            raise ValueError('Circular vertex incidence reaches a face outside the named BODY')
        edge = nodes[coedge['edge_index']]
        for field in ('start_vertex_index', 'end_vertex_index'):
            if edge[field] not in signatures:
                raise ValueError('Circular coedge endpoint leaves its owned BODY vertex table')
            signatures[edge[field]].add(names[face_id]['name_key'])
    result = {}
    for vertex, labels in signatures.items():
        signature = tuple(sorted(labels))
        point = nodes[nodes[vertex]['point_index']]
        if len(signature) != 3 or signature in result or point['kind'] != 'point':
            raise ValueError('Circular vertex named-face incidence is missing or ambiguous')
        result[signature] = {'vertex_index': vertex, 'point_index': point['index'], 'raw_position': point['raw_origin']}
    return result


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def _fit(source, target):
    if set(source) != set(target):
        raise ValueError('Source and target named-face vertex signatures disagree')
    labels = sorted(source)
    src = [source[k]['raw_position'] for k in labels]; dst = [target[k]['raw_position'] for k in labels]
    basis = None
    for indices in combinations(range(1, len(labels)), 3):
        cols = [[src[i][j]-src[0][j] for j in range(3)] for i in indices]
        determinant = _dot(cols[0], _cross(cols[1], cols[2]))
        if abs(determinant) > 1e-12:
            basis = indices, cols, determinant; break
    if basis is None:
        raise ValueError('Named source vertex correspondence has no noncoplanar fit basis')
    indices, cols, determinant = basis
    inverse = [[v/determinant for v in row] for row in
               (_cross(cols[1], cols[2]), _cross(cols[2], cols[0]), _cross(cols[0], cols[1]))]
    target_cols = [[dst[i][j]-dst[0][j] for j in range(3)] for i in indices]
    rotation = [[sum(target_cols[k][i]*inverse[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    translation = [dst[0][i]-_dot(rotation[i], src[0]) for i in range(3)]
    if (max(abs(_dot(rotation[i], rotation[j])-float(i == j)) for i in range(3) for j in range(3)) > 1e-8
            or not math.isclose(_dot(rotation[0], _cross(rotation[1], rotation[2])), 1., abs_tol=1e-8)):
        raise ValueError('Named source/target caches do not define a proper rigid rotation')
    errors = [math.dist([_dot(row, point)+t for row, t in zip(rotation, translation)], expected) for point, expected in zip(src, dst)]
    if max(errors) > 1e-8:
        raise ValueError('Rigid fit fails the complete typed named-vertex correspondence')
    matrix = [v for row, t in zip(rotation, translation) for v in row+[t]]+[0., 0., 0., 1.]
    correspondence = [{'incident_face_name_keys': [list(k) for k in signature],
                       'source': source[signature], 'target': target[signature]} for signature in labels]
    return {'matrix': matrix, 'matched_vertex_count': len(labels), 'maximum_vertex_residual_raw': max(errors),
            'vertex_correspondence': correspondence,
            'basis_selection': 'First noncoplanar triple in sorted identity-signature order; coordinates fit the matrix only after all vertex identities are fixed'}


def decode_circular_placement_evidence(data, records, features, member, members, body_blob_bindings):
    """Return separately labeled cache evidence; never mutate existing placements."""
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {i: rs[0] for i, rs in grouped.items() if len(rs) == 1}
    def typed(identity, guid):
        rec = primary.get(identity)
        if rec is None or rec.class_guid != guid:
            raise ValueError('Circular evidence typed native owner/reference missing or ambiguous')
        return rec, data[rec.body:rec.end]
    selections = decode_body_selections(data, records)
    anchors = {a['object_id']: a for a in selections['body_anchors']}
    proxies = {p['selection_record_object_id']: p for p in selections['selection_proxies']}
    joined = decode_body_asm_identifiers(data, records, member, members, body_blob_bindings)
    bindings = {}
    for mapping in joined['decoded']:
        for entry in mapping['bindings']:
            bindings.setdefault(entry['native_body_object_id'], []).append((mapping, entry))
    decoded, unresolved = [], []
    for feature in features:
        if feature.get('class_guid') != FEATURE:
            continue
        try:
            fid = feature['object_id']; _, body = typed(fid, FEATURE)
            control_id = reference(body, 6); _, control = typed(control_id, CONTROL)
            if body[:6] != bytes.fromhex('000100000000') or control[:2] != bytes(2) or control[2] not in (0, 1):
                raise ValueError('Unobserved circular feature/controller prefix')
            compute, entity_type = struct.unpack_from('<II', control, 37)
            if entity_type != 2:
                raise ValueError('Circular naming/cache evidence currently supports explicit body inputs only')
            pair_count = struct.unpack_from('<I', control, 50)[0]
            if not 1 <= pair_count <= 1023:
                raise ValueError('Circular evidence pair count outside bounds')
            pairs = [struct.unpack_from('<QQ', control, 54+16*i) for i in range(pair_count)]
            cursor = 54+16*pair_count
            quantity = struct.unpack_from('<I', control, cursor)[0]
            if quantity != pair_count+1 or [p[0] for p in pairs] != list(range(2, quantity+1)) or len({p[1] for p in pairs}) != pair_count:
                raise ValueError('Circular evidence ordinal/key table is inconsistent or ambiguous')
            elements = {}
            for i in range(quantity):
                eid = reference(control, cursor+4+11*i); _, payload = typed(eid, ELEMENT)
                if len(payload) != 17 or payload[:2] != bytes(2) or reference(payload, 6) != control_id:
                    raise ValueError('Circular element/controller backlink disagrees')
                ordinal = struct.unpack_from('<I', payload, 2)[0]
                if ordinal in elements:
                    raise ValueError('Duplicate circular element ordinal')
                elements[ordinal] = eid
            cursor += 4+11*quantity
            if reference(control, cursor+11) != fid or set(elements) != set(range(1, quantity+1)):
                raise ValueError('Circular controller owner/element ordinal coverage disagrees')
            proxy_id = reference(control, cursor+22)
            proxy = proxies.get(proxy_id)
            if proxy is None or proxy['owner_object_id'] != fid:
                raise ValueError('Explicit circular body input proxy/owner unresolved')
            collection_id = reference(body, 17); _, collection = typed(collection_id, COLLECTION)
            count = struct.unpack_from('<I', collection, 6)[0]
            if (count != len(proxy['descriptor_object_ids']) or collection[:6] != bytes(6)
                    or len(collection) != 74+26*count
                    or [reference(collection, 10+26*i) for i in range(count)] != proxy['descriptor_object_ids']
                    or reference(collection, 10+26*count) != fid or reference(collection, len(collection)-11) != fid):
                raise ValueError('Circular input collection/proxy membership or ownership disagrees')
            cursor += 33; suppressed_count = struct.unpack_from('<I', control, cursor)[0]
            if len(control) != cursor+4+4*suppressed_count:
                raise ValueError('Circular suppression table framing disagrees')
            suppressed = list(struct.unpack_from('<'+'I'*suppressed_count, control, cursor+4))
            if len(set(suppressed)) != len(suppressed) or any(o not in elements or o == 1 for o in suppressed):
                raise ValueError('Circular suppression ordinals unsupported')
            result_count = struct.unpack_from('<I', body, 32)[0]
            if result_count != (quantity-1-len(suppressed))*count:
                raise ValueError('Circular owned body-result count disagrees with active elements/inputs')
            result_anchors = [reference(body, 36+11*i) for i in range(result_count)]
            results = []
            for aid in result_anchors:
                anchor = anchors.get(aid)
                if anchor is None or anchor['source_owner_object_id'] != fid:
                    raise ValueError('Circular result anchor/body/feature ownership disagrees')
                results.append((aid, anchor['native_body_object_id']))
            native_ids = proxy['native_body_object_ids']+[b for _, b in results]
            if len(set(native_ids)) != len(native_ids) or any(len(bindings.get(i, [])) != 1 for i in native_ids):
                raise ValueError('Circular source/result BODY cache join is missing or ambiguous')
            mapping_ids = {bindings[i][0][0]['mapping_record_object_id'] for i in native_ids}
            if len(mapping_ids) != 1:
                raise ValueError('Circular evidence requires all source/result caches in one explicit same-asset history blob')
            mapping = bindings[native_ids[0]][0][0]; blob_member = mapping['history_blob_member']; blob = members[blob_member]
            parsed = inspect_asm(blob); topology = decode_topology(parsed)
            graphs = {g['body_index']: g for g in topology['body_graphs']}; nodes = {n['index']: n for n in topology['nodes']}
            body_data = {}
            for nid in native_ids:
                entry = bindings[nid][0][1]; graph = graphs.get(entry['asm_body_index'])
                if graph is None:
                    raise ValueError('Circular keyed BODY lacks bounded typed topology')
                names = _face_names(blob, parsed, graph)
                components = {v['components'] for v in names.values()}
                if len(components) != 1:
                    raise ValueError('Circular BODY face naming components disagree')
                body_data[nid] = {'binding': entry, 'graph': graph, 'names': names,
                                  'components': next(iter(components)), 'vertices': _vertices(graph, nodes, names)}
            seeds = {}
            for nid in proxy['native_body_object_ids']:
                components = body_data[nid]['components']
                if len(components) != 1 or components[0] in seeds:
                    raise ValueError('Circular source face-naming component missing or ambiguous')
                seeds[components[0]] = nid
            grouped_results = {}; middle = set()
            for aid, nid in results:
                components = body_data[nid]['components']
                if len(components) != 3 or components[0] not in seeds:
                    raise ValueError('Circular result naming prefix lacks one explicit source BODY group')
                source_key, common_key, key = components; middle.add(common_key)
                pair = next((p for p in pairs if p[1] == key), None)
                if pair is None or pair[0] in suppressed or (key, source_key) in grouped_results:
                    raise ValueError('Circular generated naming key is missing, suppressed or ambiguous')
                grouped_results[key, source_key] = (aid, nid)
            if len(middle) != 1:
                raise ValueError('Circular generated naming groups have inconsistent common feature component')
            expected = {(key, seed) for ordinal, key in pairs if ordinal not in suppressed for seed in seeds}
            if set(grouped_results) != expected:
                raise ValueError('Circular active element/source naming groups are not an exact bijection')
            evidence = {'feature_object_id': fid, 'control_record_object_id': control_id,
                        'history_blob_member': blob_member, 'mapping_record_object_id': mapping['mapping_record_object_id'],
                        'source_native_body_object_ids': proxy['native_body_object_ids'],
                        'uninterpreted_common_feature_naming_component': next(iter(middle)),
                        'element_cache_groups': [], 'suppressed_elements_without_generated_cache_group': [],
                        'identity_scope': 'Exact bounded serialized controller-key/count3 face-naming correspondence within explicitly owned result BODYs; not a universal persistent topology naming rule',
                        'matrix_source': 'Measured relative rigid matrix from complete named-face/typed-vertex correspondence; no serialized per-element transform claimed',
                        'coordinate_scope': 'One mapped initial ASM cache frame; source/result BODY transforms absent or identity; no world/current/final placement claim',
                        'api_getter_status': 'Existing circular transform getter disagreement remains unresolved; these matrices do not correct or reinterpret the API getters',
                        'cache_application': 'Evidence only; not applied again to the already placed cache geometry'}
            for ordinal, key in pairs:
                if ordinal in suppressed:
                    evidence['suppressed_elements_without_generated_cache_group'].append({'element_object_id': elements[ordinal], 'stored_ordinal': ordinal, 'stored_naming_key': key})
                    continue
                group = {'element_object_id': elements[ordinal], 'stored_ordinal': ordinal, 'stored_naming_key': key, 'cache_bodies': []}
                for source_key, seed_id in seeds.items():
                    aid, nid = grouped_results[key, source_key]; source_body, target_body = body_data[seed_id], body_data[nid]
                    if {v['name_key'] for v in source_body['names'].values()} != {v['name_key'] for v in target_body['names'].values()}:
                        raise ValueError('Circular source/result inherited face names disagree')
                    fit = _fit(source_body['vertices'], target_body['vertices'])
                    group['cache_bodies'].append({'source_native_body_object_id': seed_id, 'result_anchor_object_id': aid,
                        'result_native_body_object_id': nid, 'asm_body_index': target_body['binding']['asm_body_index'],
                        'asm_body_stored_id': target_body['binding']['asm_stored_entity_id'],
                        'stored_face_naming_components': list(target_body['components']),
                        'source_face_attribute_indices': sorted(i for n in source_body['names'].values() for i in n['attribute_indices']),
                        'result_face_attribute_indices': sorted(i for n in target_body['names'].values() for i in n['attribute_indices']),
                        'measured_relative_rigid_fit': fit})
                evidence['element_cache_groups'].append(group)
            decoded.append(evidence)
        except (ValueError, KeyError, IndexError, TypeError, struct.error) as error:
            unresolved.append({'feature_object_id': feature['object_id'], 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved,
            'scope': 'Bounded circular body-pattern native naming/cache evidence and measured relative matrices; existing getter/placement warnings preserved'}
