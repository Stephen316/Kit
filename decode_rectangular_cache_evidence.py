"""Body-input rectangular element keys joined to named stored BODY caches.

Native selectors, result anchors and same-blob stored IDs fix BODY identities.
The complete controller-key/source-prefix bijection precedes every rigid fit.
No Cantor coordinates, API element IDs or result-list order choose a cache.
"""
import math
import struct

from asm_records import inspect_asm
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections
from decode_brep import decode_topology
from decode_circular_placement_evidence import _face_names, _vertices, _fit
from decode_extrude import optional_reference
from decode_rectangular_pattern_modes import FEATURE, CONTROL
from decode_sketch import attributes, reference

SCOPE = ('Observed zero-suppression rectangular BODY-input controller-key/source-prefix cache '
         'correspondences and measured relative rigid matrices; logical grid/API element mapping, '
         'serialized transforms, current/final lifecycle and regeneration remain unresolved')
ANCHOR = 'D26351F0-5940-4D23-AA20-2C35475A6D9E'
ELEMENT = 'AD719C1A-11AF-4537-BB41-030A9091D36B'
COLLECTION = '8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF'


def decode_rectangular_cache_evidence(data, records, features, member, members, body_blob_bindings):
    """Return separate decoded/unresolved/scope evidence without changing settings."""
    result = dict(decoded=[], unresolved=[], scope=SCOPE)
    candidates = [f for f in features if f.get('class_guid') == FEATURE]
    if not candidates:
        return result
    grouped = {}
    for rec in records:
        if rec.is_primary:
            grouped.setdefault(rec.object_id, []).append(rec)

    def typed(identity, guid):
        matches = grouped.get(identity, [])
        if len(matches) != 1 or matches[0].class_guid != guid:
            raise ValueError('Rectangular cache typed native identity missing, duplicate or wrong class')
        rec = matches[0]
        return rec, data[rec.body:rec.end]

    selections, joined = None, None
    for feature in candidates:
        fid = feature['object_id']
        try:
            _, body = typed(fid, FEATURE)
            if len(body) < 24 or body[0] != 0 or body[1] not in (0, 1):
                raise ValueError('Unobserved rectangular cache feature header')
            props, cursor = attributes(body, 2) if body[1] else ({}, 2)
            if props:
                raise ValueError('Unobserved rectangular cache feature attributes')
            control_id, collection_id = reference(body, cursor), reference(body, cursor+11)
            feature_header_end = cursor+22
            _, control = typed(control_id, CONTROL)
            if len(control) < 150:
                raise ValueError('Rectangular cache controller is shorter than observed framing')
            _, mode_cursor = optional_reference(control, 114)
            compute, entity_type = struct.unpack_from('<II', control, mode_cursor+12)
            # This addition is body-only. Existing Feature patterns are not
            # attempted and do not receive a new unsupported diagnostic.
            if entity_type == 1:
                continue
            if (entity_type != 2 or compute not in (0, 1, 2)
                    or control[:5] != bytes.fromhex('0102000000')
                    or control[16:20] != bytes(4) or control[31:44] != bytes(9)+b'\xff'*4
                    or any(flag not in (0, 1) for flag in control[90:92])
                    or control[mode_cursor:mode_cursor+12] != bytes(12)
                    or control[mode_cursor+20:mode_cursor+24] != b'\xff'*4
                    or control[mode_cursor+24] not in (0, 1)):
                raise ValueError('Unobserved rectangular BODY cache controller mode/header')
            quantity_ids = [reference(control, 5), reference(control, 20)]
            quantities = []
            for identity, role in zip(quantity_ids, ('countU', 'CountV')):
                params = [p for p in feature.get('parameters', [])
                    if p['binding_object_id'] == identity and p['role'] == role]
                if len(params) != 1:
                    raise ValueError('Rectangular cache quantity binding/role is missing or ambiguous')
                value = params[0]['raw_float64']
                if (not isinstance(value, (int, float)) or isinstance(value, bool)
                        or not math.isfinite(value) or int(value) != value or not 1 <= value <= 1024):
                    raise ValueError('Rectangular cache quantity is not a bounded positive integer')
                quantities.append(int(value))
            total = math.prod(quantities)
            if not 2 <= total <= 1024 or reference(control, 92) != quantity_ids[1]:
                raise ValueError('Rectangular cache quantity product/repeated binding disagrees')
            cursor = mode_cursor+25
            pair_count = struct.unpack_from('<I', control, cursor)[0]
            if pair_count != total-1:
                raise ValueError('Rectangular cache controller pair count disagrees with quantity product')
            pairs = [list(struct.unpack_from('<QQ', control, cursor+4+16*i)) for i in range(pair_count)]
            if (any(not 2 <= p[0] <= 0xffffffff or p[1] <= 0 for p in pairs)
                    or len({p[0] for p in pairs}) != pair_count or len({p[1] for p in pairs}) != pair_count):
                raise ValueError('Rectangular controller element/naming keys are invalid or duplicated')
            cursor += 4+16*pair_count
            if struct.unpack_from('<I', control, cursor)[0] != total:
                raise ValueError('Rectangular cache element-reference count disagrees')
            element_ids = [reference(control, cursor+4+11*i) for i in range(total)]
            elements = {}
            for eid in element_ids:
                _, element = typed(eid, ELEMENT)
                if len(element) != 17 or element[:2] != bytes(2) or reference(element, 6) != control_id:
                    raise ValueError('Rectangular cache element/controller ownership disagrees')
                key = struct.unpack_from('<I', element, 2)[0]
                if key in elements:
                    raise ValueError('Rectangular cache repeats a native element key')
                elements[key] = eid
            if len(set(element_ids)) != total or set(elements) != {1} | {p[0] for p in pairs}:
                raise ValueError('Rectangular native element/key-pair coverage is not a bijection')
            cursor += 4+11*total
            if reference(control, cursor) != quantity_ids[0] or reference(control, cursor+11) != fid:
                raise ValueError('Rectangular cache repeated quantity/controller owner disagrees')
            proxy_id = reference(control, cursor+22)
            cursor += 33
            if len(control) != cursor+4 or struct.unpack_from('<I', control, cursor)[0] != 0:
                raise ValueError('Rectangular cache evidence supports explicit zero suppression only')
            if selections is None:
                selections = decode_body_selections(data, records)
            proxies = [p for p in selections['selection_proxies'] if p['selection_record_object_id'] == proxy_id]
            if len(proxies) != 1 or proxies[0]['owner_object_id'] != fid:
                raise ValueError('Rectangular explicit source BODY proxy ownership unresolved')
            proxy = proxies[0]
            sources = proxy['native_body_object_ids']
            descriptors = proxy['descriptor_object_ids']
            if len(sources) != len(descriptors) or len(set(sources)) != len(sources):
                raise ValueError('Rectangular source BODY/descriptor identities are ambiguous')
            _, collection = typed(collection_id, COLLECTION)
            count = struct.unpack_from('<I', collection, 6)[0]
            if (not 1 <= count <= 1024 or count != len(sources) or collection[:6] != bytes(6)
                    or len(collection) != 74+26*count
                    or [reference(collection, 10+26*i) for i in range(count)] != descriptors
                    or any(struct.unpack_from('<I', collection, 21+26*i)[0] != 1 for i in range(count))
                    or reference(collection, 10+26*count) != fid or reference(collection, len(collection)-11) != fid):
                raise ValueError('Rectangular source collection/proxy/count/owner copies disagree')
            source_descriptors = []
            for descriptor_id in descriptors:
                _, descriptor = typed(descriptor_id, '9716F783-676D-42E0-93F9-EBF273E7C035')
                if reference(descriptor, len(descriptor)-11) != fid:
                    raise ValueError('Rectangular source BODY descriptor owner disagrees')
                found = [d for d in selections['body_descriptors'] if d['object_id'] == descriptor_id]
                if len(found) != 1:
                    raise ValueError('Rectangular source descriptor lacks one typed native BODY route')
                source_descriptors.append(found[0])
            for i in range(count):
                typed(reference(collection, 25+26*i), 'C46D3EEB-40E1-43FA-83DC-9CB204335417')
            if body[feature_header_end:feature_header_end+4] != bytes(4):
                raise ValueError('Rectangular cache owned result-list prefix disagrees')
            result_count = struct.unpack_from('<I', body, feature_header_end+4)[0]
            if result_count != (total-1)*count:
                raise ValueError('Rectangular cache owned result count does not cover every source/active key')
            anchor_ids = [reference(body, feature_header_end+8+11*i) for i in range(result_count)]
            if len(set(anchor_ids)) != result_count:
                raise ValueError('Rectangular cache result anchor list is duplicated')
            results = []
            for aid in anchor_ids:
                _, anchor_body = typed(aid, ANCHOR)
                anchors = [a for a in selections['body_anchors'] if a['object_id'] == aid]
                if (len(anchor_body) != 102 or reference(anchor_body, 91) != fid or len(anchors) != 1
                        or anchors[0]['source_owner_object_id'] != fid):
                    raise ValueError('Rectangular cache owned result anchor/BODY/feature route disagrees')
                results.append(anchors[0])
            native_ids = sources+[a['native_body_object_id'] for a in results]
            if len(set(native_ids)) != len(native_ids):
                raise ValueError('Rectangular source/result native BODY identities overlap or repeat')
            if joined is None:
                joined = decode_body_asm_identifiers(data, records, member, members, body_blob_bindings)
            bindings = {nid: [(m, b) for m in joined['decoded'] for b in m['bindings']
                if b['native_body_object_id'] == nid] for nid in native_ids}
            if any(len(values) != 1 for values in bindings.values()):
                raise ValueError('Rectangular native BODY lacks a unique typed stored-ID cache join')
            mapping_ids = {bindings[nid][0][0]['mapping_record_object_id'] for nid in native_ids}
            blob_members = {bindings[nid][0][0]['history_blob_member'] for nid in native_ids}
            if len(mapping_ids) != 1 or len(blob_members) != 1:
                raise ValueError('Rectangular source/result BODY caches leave one explicit same-asset mapping')
            mapping = bindings[sources[0]][0][0]
            blob_member = mapping['history_blob_member']
            blob = members[blob_member]
            parsed = inspect_asm(blob)
            topology = decode_topology(parsed)
            if topology['unresolved']:
                raise ValueError('Rectangular mapped cache topology has unresolved fields')
            nodes = {n['index']: n for n in topology['nodes']}
            graphs = {g['body_index']: g for g in topology['body_graphs']}
            bodies = {}
            binding_fields = ('native_body_object_id', 'stored_handle', 'asm_body_index', 'asm_stored_entity_id',
                'asm_body_record_offset', 'asm_identifier_token_offset', 'association_status', 'identifier_scope')
            for nid in native_ids:
                entry = bindings[nid][0][1]
                graph = graphs.get(entry['asm_body_index'])
                if graph is None:
                    raise ValueError('Rectangular keyed BODY lacks one complete typed cache graph')
                names = _face_names(blob, parsed, graph)
                components = {v['components'] for v in names.values()}
                if len(components) != 1:
                    raise ValueError('Rectangular BODY complete face naming components disagree')
                vertices = _vertices(graph, nodes, names)
                if any(not math.isfinite(v) for p in vertices.values() for v in p['raw_position']):
                    raise ValueError('Rectangular identity-fixed vertex coordinates are not finite')
                name_proof = []
                for face_id, name in names.items():
                    name_proof.append(dict(face_record_index=face_id, name_key=list(name['name_key']),
                        stored_reference_components_int32=list(name['components']),
                        owner_attribute_indices=name['attribute_indices'],
                        original_attribute_records=[dict(record_index=a, record_offset=parsed['records'][a]['offset'],
                            record_end_offset=parsed['records'][a]['end_offset'],
                            original_payload_hex=blob[parsed['records'][a]['offset']:parsed['records'][a]['end_offset']].hex())
                            for a in name['attribute_indices']]))
                bodies[nid] = dict(binding={k: entry[k] for k in binding_fields},
                    names=names, components=next(iter(components)), vertices=vertices,
                    complete_face_naming_proof=name_proof)
            seeds = {}
            for nid in sources:
                components = bodies[nid]['components']
                if len(components) != 1 or components[0] in seeds:
                    raise ValueError('Rectangular source prefix is missing or ambiguous')
                seeds[components[0]] = nid
            by_naming_key = {key: element for element, key in pairs}
            groups, common_keys = {}, set()
            for anchor in results:
                nid = anchor['native_body_object_id']
                components = bodies[nid]['components']
                if len(components) != 3 or components[0] not in seeds or components[2] not in by_naming_key:
                    raise ValueError('Rectangular result full naming tuple has no explicit source/controller key')
                source_key, common_key, naming_key = components
                common_keys.add(common_key)
                if (naming_key, source_key) in groups:
                    raise ValueError('Rectangular result naming key/source prefix pair is ambiguous')
                groups[naming_key, source_key] = anchor
            expected = {(key, source_key) for _, key in pairs for source_key in seeds}
            if len(common_keys) != 1 or set(groups) != expected:
                raise ValueError('Rectangular controller naming-key/source-prefix groups are not a complete bijection')
            for (_, source_key), anchor in groups.items():
                source, target = bodies[seeds[source_key]], bodies[anchor['native_body_object_id']]
                if ({v['name_key'] for v in source['names'].values()} != {v['name_key'] for v in target['names'].values()}
                        or set(source['vertices']) != set(target['vertices'])):
                    raise ValueError('Rectangular result inherited face/vertex identity signatures disagree with source')
            # Every BODY and vertex identity is now fixed. Geometry fitting is
            # deliberately below the complete product/bijection proof.
            source_proofs = [dict(source_native_body_object_id=nid, source_descriptor=descriptor,
                source_body_binding=bodies[nid]['binding'],
                stored_source_naming_prefix=list(bodies[nid]['components']),
                complete_face_naming_proof=bodies[nid]['complete_face_naming_proof'])
                for nid, descriptor in zip(sources, source_descriptors)]
            evidence = dict(feature_object_id=fid, control_record_object_id=control_id,
                input_selection_record_object_id=proxy_id, input_entity_collection_object_id=collection_id,
                pattern_entity_type='Bodies', stored_entity_type_code=2, stored_compute_option_code=compute,
                stored_symmetry_flags=[bool(v) for v in control[90:92]],
                stored_instance_key_pairs=pairs, element_record_object_ids=element_ids,
                element_record_keys=[struct.unpack_from('<I', typed(eid, ELEMENT)[1], 2)[0] for eid in element_ids],
                stored_suppressed_element_keys=[], source_native_body_object_ids=sources,
                source_cache_bodies=source_proofs, owned_result_anchor_object_ids=anchor_ids,
                mapping_record_object_id=mapping['mapping_record_object_id'], mapping_owner_object_id=mapping['owner_object_id'],
                history_blob_member=blob_member, uninterpreted_common_feature_naming_component=next(iter(common_keys)),
                complete_controller_source_group_bijection=True, element_cache_groups=[],
                matrix_source='Measured relative rigid fit after all complete face-name/typed vertex identities are fixed; no serialized per-element transform claimed',
                coordinate_scope='One explicitly mapped initial ASM cache frame with identity BODY transforms; no world/current/final placement claim',
                native_key_scope='Literal native element key paired with an opaque naming key; no Cantor coordinate or API ID interpretation',
                API_element_identity=None, logical_grid_identity=None, current_placement=None,
                cache_application='Evidence only; no matrices applied to the already placed stored caches', scope=SCOPE)
            for element_key, naming_key in pairs:
                cache_group = dict(element_object_id=elements[element_key], stored_element_key=element_key,
                    stored_naming_key=naming_key, cache_bodies=[])
                for source_key, seed_id in seeds.items():
                    anchor = groups[naming_key, source_key]
                    nid = anchor['native_body_object_id']
                    source, target = bodies[seed_id], bodies[nid]
                    cache_group['cache_bodies'].append(dict(source_native_body_object_id=seed_id,
                        result_anchor_object_id=anchor['object_id'], result_body_anchor=anchor,
                        result_native_body_object_id=nid, result_body_binding=target['binding'],
                        stored_face_naming_components=list(target['components']),
                        complete_result_face_naming_proof=target['complete_face_naming_proof'],
                        measured_relative_rigid_fit=_fit(source['vertices'], target['vertices'])))
                evidence['element_cache_groups'].append(cache_group)
            result['decoded'].append(evidence)
        except (ValueError, KeyError, IndexError, TypeError, UnicodeError, struct.error) as error:
            result['unresolved'].append(dict(feature_object_id=fid, reason=str(error)))
    return result
