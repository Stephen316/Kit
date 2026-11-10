"""PathPattern native element ordinals joined to independently named BODY caches.

Typed selectors, owned anchors and same-asset stored BODY IDs establish identities.
The complete literal active-pair/source-prefix product precedes every rigid fit.
Matrices are cache measurements, without analytic path or API element assignment.
"""
import math
import struct

from asm_records import inspect_asm
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections
from decode_brep import decode_topology
from decode_circular_placement_evidence import _face_names, _vertices, _fit
from decode_path_patterns import decode_path_pattern, parse_path_pattern_controls
from decode_path_pattern_composites import decode_path_pattern_composites
from decode_sketch import reference

FEATURE='B0B3D9E5-1C25-47BC-ABCD-E723F193DF1B'
CONTROL='BE1FB171-D98A-4A4D-99C2-3738627CF79C'
ANCHOR='D26351F0-5940-4D23-AA20-2C35475A6D9E'
ELEMENT='AD719C1A-11AF-4537-BB41-030A9091D36B'
COLLECTION='8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF'
SCOPE=('Observed BODY PathPattern native element ordinal/opaque naming-key and source-prefix cache '
       'correspondences, including literal nonseed suppression, with measured relative matrices; '
       'API element identity, analytic path traversal, serialized transforms, current/final lifecycle '
       'and regeneration remain unresolved')
FEATURE_SCOPE=('Observed singleton Feature PathPattern typed source and complete canonical generic/FPM '
       'FACE naming/cache correspondence with measured relative matrices; API element identity, '
       'analytic traversal, serialized transforms, current/final lifecycle and regeneration unresolved')


def decode_path_pattern_cache_evidence(data,records,features,member,members,body_blob_bindings,
                                      *,feature_source_resolver=None):
    """Return separate decoded/unresolved/scope evidence without modifying controls."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    candidates=[f for f in features if f.get('class_guid')==FEATURE]
    if not candidates:
        return result
    grouped={}
    for rec in records:
        if rec.is_primary:
            grouped.setdefault(rec.object_id,[]).append(rec)

    def typed(identity,guid):
        values=grouped.get(identity,[])
        if len(values)!=1 or values[0].class_guid!=guid:
            raise ValueError('PathPattern cache typed native identity missing, duplicate or wrong class')
        rec=values[0]
        return rec,data[rec.body:rec.end]

    selections,joined=None,None
    for feature in candidates:
        fid=feature['object_id']
        try:
            _,body=typed(fid,FEATURE)
            if body[:6]!=bytes.fromhex('000100000000'):
                raise ValueError('Unobserved PathPattern cache feature prefix')
            control_id,collection_id=reference(body,6),reference(body,17)
            _,control=typed(control_id,CONTROL)
            if len(control)<142:
                raise ValueError('PathPattern cache controller shorter than observed framing')
            compute,entity_type=struct.unpack_from('<II',control,125)
            if entity_type==1 and feature_source_resolver is None:
                continue
            if entity_type==2:
                try:
                    settings=decode_path_pattern(data,records,body,feature,features)
                except (ValueError,KeyError,IndexError,TypeError,struct.error) as single_error:
                    try:
                        settings=decode_path_pattern_composites(data,records,body,feature,features)
                    except (ValueError,KeyError,IndexError,TypeError,struct.error) as composite_error:
                        raise ValueError('PathPattern native controls/source unresolved: single '+str(single_error)
                            +'; composite '+str(composite_error)) from composite_error
            elif entity_type==1 and compute in (0,1):
                settings=parse_path_pattern_controls(data,records,control_id,feature,features,
                    allowed_type_codes=((0,1),(1,1)))
            else:
                raise ValueError('Unobserved PathPattern cache compute/entity family')
            quantity=settings['quantity']
            if (not math.isfinite(settings['distance_cm']) or not math.isfinite(settings['stored_start_fraction'])
                    or not 2<=quantity<=1024):
                raise ValueError('PathPattern cache count/distance/start must be bounded finite controls')
            pairs=settings['stored_instance_ordinal_pairs']
            suppressed=settings['suppressed_element_ids']
            if (len(pairs)!=quantity-1 or [p[0] for p in pairs]!=list(range(1,quantity))
                    or any(type(key) is not int or key<=0 for _,key in pairs)
                    or len({key for _,key in pairs})!=len(pairs)):
                raise ValueError('PathPattern element/opaque naming-key pairs invalid or duplicated')
            if 0 in suppressed:
                raise ValueError('PathPattern cache seed suppression remains unobserved')
            active_pairs=[p for p in pairs if p[0] not in suppressed]
            if not active_pairs:
                raise ValueError('PathPattern cache needs an observed nonseed active result group')
            element_ids=settings['element_record_object_ids']
            elements={}
            for eid in element_ids:
                _,payload=typed(eid,ELEMENT)
                if len(payload)!=17 or payload[:2]!=bytes(2) or reference(payload,6)!=control_id:
                    raise ValueError('PathPattern typed element extent/prefix/controller backlink disagrees')
                ordinal=struct.unpack_from('<I',payload,2)[0]
                if ordinal in elements:
                    raise ValueError('PathPattern native element ordinal duplicated')
                elements[ordinal]=eid
            if (len(set(element_ids))!=quantity or set(elements)!={0}|{p[0] for p in pairs}
                    or [struct.unpack_from('<I',typed(eid,ELEMENT)[1],2)[0] for eid in element_ids]!=list(range(quantity))):
                raise ValueError('PathPattern native element/pair coverage is not a complete bijection')
            proxy_id=settings['auxiliary_selection_record_object_id']
            if selections is None:
                selections = decode_body_selections(data, records)
            source_feature_ids, source_provenance = None, None
            if entity_type == 2:
                proxies = [p for p in selections['selection_proxies'] if p['selection_record_object_id'] == proxy_id]
                if len(proxies) != 1 or proxies[0]['owner_object_id'] != fid:
                    raise ValueError('PathPattern explicit source BODY proxy ownership unresolved')
                proxy = proxies[0]
                sources = proxy['native_body_object_ids']
                descriptors = proxy['descriptor_object_ids']
            else:
                resolved = feature_source_resolver(data, records, feature, proxy_id, collection_id)
                required = {'descriptor_object_ids', 'source_feature_object_ids',
                            'source_native_body_object_ids', 'provenance'}
                if not isinstance(resolved, dict) or set(resolved) != required:
                    raise ValueError('PathPattern feature-source resolver returned an unobserved schema')
                descriptors = resolved['descriptor_object_ids']
                source_feature_ids = resolved['source_feature_object_ids']
                sources = resolved['source_native_body_object_ids']
                source_provenance = resolved['provenance']
                if (any(not isinstance(values, list) or not 1 <= len(values) <= 1024
                        or any(type(value) is not int or value <= 0 for value in values)
                        or len(set(values)) != len(values)
                        for values in (descriptors, source_feature_ids, sources))
                        or len({len(descriptors), len(source_feature_ids), len(sources)}) != 1
                        or not isinstance(source_provenance, dict) or not source_provenance):
                    raise ValueError('PathPattern feature-source resolver count/identities/provenance invalid')
                from decode_selection import native_proxy_references
                proxy_record, proxy_body = typed(proxy_id, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
                proxy_descriptors, _ = native_proxy_references(data, proxy_record)
                if reference(proxy_body, len(proxy_body)-11) != fid or proxy_descriptors != descriptors:
                    raise ValueError('PathPattern feature-source proxy/descriptor ownership disagrees')
            if len(sources) != len(descriptors) or len(set(sources)) != len(sources):
                raise ValueError('PathPattern source BODY/descriptor identities are ambiguous')
            _, collection = typed(collection_id, COLLECTION)
            count = struct.unpack_from('<I', collection, 6)[0]
            if (not 1 <= count <= 1024 or count != len(sources) or collection[:6] != bytes(6)
                    or len(collection) != 74+26*count
                    or [reference(collection, 10+26*i) for i in range(count)] != descriptors
                    or any(struct.unpack_from('<I', collection, 21+26*i)[0] != 1 for i in range(count))
                    or reference(collection, 10+26*count) != fid or reference(collection, len(collection)-11) != fid):
                raise ValueError('PathPattern source collection/proxy/count/owner copies disagree')
            source_descriptors = []
            for index, descriptor_id in enumerate(descriptors):
                if entity_type == 2:
                    _, descriptor = typed(descriptor_id, '9716F783-676D-42E0-93F9-EBF273E7C035')
                    if reference(descriptor, len(descriptor)-11) != fid:
                        raise ValueError('PathPattern source BODY descriptor owner disagrees')
                    found = [d for d in selections['body_descriptors'] if d['object_id'] == descriptor_id]
                    if len(found) != 1:
                        raise ValueError('PathPattern source descriptor lacks one typed native BODY route')
                    source_descriptors.append(found[0])
                else:
                    _, descriptor = typed(descriptor_id, '5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
                    if len(descriptor) != 263 or reference(descriptor, 252) != fid:
                        raise ValueError('PathPattern source Feature descriptor owner/extent disagrees')
                    leaf_id = reference(descriptor, 2)
                    _, leaf = typed(leaf_id, '90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
                    source_id = source_feature_ids[index]
                    if (len(leaf) != 10 or leaf[:2] != bytes(2)
                            or struct.unpack_from('<Q', leaf, 2)[0] != source_id
                            or source_id == fid or len(grouped.get(source_id, [])) != 1):
                        raise ValueError('PathPattern feature source differs from explicit typed descriptor leaf')
                    owned = [a for a in selections['body_anchors'] if a['source_owner_object_id'] == source_id]
                    if len(owned) != 1 or owned[0]['native_body_object_id'] != sources[index]:
                        raise ValueError('PathPattern source Feature lacks exactly one selected owned BODY anchor')
                    typed(owned[0]['object_id'], ANCHOR)
                    source_descriptors.append(dict(descriptor_object_id=descriptor_id,
                        descriptor_class_guid='5A1BF548-241F-46FD-9FB5-E4B05126EB9D',
                        terminal_object_id=leaf_id, source_feature_object_id=source_id,
                        source_body_anchor=owned[0]))
            for i in range(count):
                typed(reference(collection, 25+26*i), 'C46D3EEB-40E1-43FA-83DC-9CB204335417')
            if body[28:32] != bytes(4):
                raise ValueError('PathPattern cache owned result-list prefix disagrees')
            result_count = struct.unpack_from('<I', body, 32)[0]
            if result_count != len(active_pairs)*count:
                raise ValueError('PathPattern cache owned result count does not cover every source/active key')
            anchor_ids = [reference(body, 36+11*i) for i in range(result_count)]
            if len(set(anchor_ids)) != result_count:
                raise ValueError('PathPattern cache result anchor list is duplicated')
            results = []
            for aid in anchor_ids:
                _, anchor_body = typed(aid, ANCHOR)
                anchors = [a for a in selections['body_anchors'] if a['object_id'] == aid]
                if (len(anchor_body) != 102 or reference(anchor_body, 91) != fid or len(anchors) != 1
                        or anchors[0]['source_owner_object_id'] != fid):
                    raise ValueError('PathPattern cache owned result anchor/BODY/feature route disagrees')
                results.append(anchors[0])
            native_ids = sources+[a['native_body_object_id'] for a in results]
            if len(set(native_ids)) != len(native_ids):
                raise ValueError('PathPattern source/result native BODY identities overlap or repeat')
            if joined is None:
                joined = decode_body_asm_identifiers(data, records, member, members, body_blob_bindings)
            bindings = {nid: [(m, b) for m in joined['decoded'] for b in m['bindings']
                if b['native_body_object_id'] == nid] for nid in native_ids}
            if any(len(values) != 1 for values in bindings.values()):
                raise ValueError('PathPattern native BODY lacks a unique typed stored-ID cache join')
            mapping_ids = {bindings[nid][0][0]['mapping_record_object_id'] for nid in native_ids}
            blob_members = {bindings[nid][0][0]['history_blob_member'] for nid in native_ids}
            if len(mapping_ids) != 1 or len(blob_members) != 1:
                raise ValueError('PathPattern source/result BODY caches leave one explicit same-asset mapping')
            mapping = bindings[sources[0]][0][0]
            blob_member = mapping['history_blob_member']
            blob = members[blob_member]
            parsed = inspect_asm(blob)
            topology = decode_topology(parsed)
            if topology['unresolved']:
                raise ValueError('PathPattern mapped cache topology has unresolved fields')
            nodes = {n['index']: n for n in topology['nodes']}
            graphs = {g['body_index']: g for g in topology['body_graphs']}
            bodies, feature_name_proofs = {}, []
            binding_fields = ('native_body_object_id', 'stored_handle', 'asm_body_index', 'asm_stored_entity_id',
                'asm_body_record_offset', 'asm_identifier_token_offset', 'association_status', 'identifier_scope')
            for nid in native_ids:
                entry = bindings[nid][0][1]
                graph = graphs.get(entry['asm_body_index'])
                if graph is None:
                    raise ValueError('PathPattern keyed BODY lacks one complete typed cache graph')
                if entity_type == 1:
                    # Reuse the already bounded canonical generic/FPM FACE
                    # chain reader. FPM literals never choose an identity.
                    from decode_circular_feature_caches import _face_names as canonical_face_names
                    named = canonical_face_names(blob, parsed, graph)
                    names = named['names']
                    feature_name_proofs.append(dict(native_body_object_id=nid,
                        asm_body_index=entry['asm_body_index'],
                        binding={k: entry[k] for k in binding_fields}, proof=named['proof']))
                else:
                    names = _face_names(blob, parsed, graph)
                components = {v['components'] for v in names.values()}
                if len(components) != 1:
                    raise ValueError('PathPattern BODY complete face naming components disagree')
                vertices = _vertices(graph, nodes, names)
                if any(not math.isfinite(v) for p in vertices.values() for v in p['raw_position']):
                    raise ValueError('PathPattern identity-fixed vertex coordinates are not finite')
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
                    raise ValueError('PathPattern source prefix is missing or ambiguous')
                seeds[components[0]] = nid
            by_naming_key = {key: element for element, key in active_pairs}
            groups, common_keys = {}, set()
            for anchor in results:
                nid = anchor['native_body_object_id']
                components = bodies[nid]['components']
                if len(components) != 3 or components[0] not in seeds or components[2] not in by_naming_key:
                    raise ValueError('PathPattern result full naming tuple has no explicit source/controller key')
                source_key, common_key, naming_key = components
                common_keys.add(common_key)
                if (naming_key, source_key) in groups:
                    raise ValueError('PathPattern result naming key/source prefix pair is ambiguous')
                groups[naming_key, source_key] = anchor
            expected = {(key, source_key) for _, key in active_pairs for source_key in seeds}
            if len(common_keys) != 1 or set(groups) != expected:
                raise ValueError('PathPattern controller naming-key/source-prefix groups are not a complete bijection')
            for (_, source_key), anchor in groups.items():
                source, target = bodies[seeds[source_key]], bodies[anchor['native_body_object_id']]
                if ({v['name_key'] for v in source['names'].values()} != {v['name_key'] for v in target['names'].values()}
                        or set(source['vertices']) != set(target['vertices'])):
                    raise ValueError('PathPattern result inherited face/vertex identity signatures disagree with source')
            # Every BODY and vertex identity is now fixed. Geometry fitting is
            # deliberately below the complete product/bijection proof.
            source_proofs = [dict(source_native_body_object_id=nid, source_descriptor=descriptor,
                source_body_binding=bodies[nid]['binding'],
                stored_source_naming_prefix=list(bodies[nid]['components']),
                complete_face_naming_proof=bodies[nid]['complete_face_naming_proof'])
                for nid, descriptor in zip(sources, source_descriptors)]
            if entity_type == 1:
                source_proofs = [dict(source_native_body_object_id=nid, source_feature_descriptor=descriptor,
                    source_body_binding=bodies[nid]['binding'],
                    stored_source_naming_prefix=list(bodies[nid]['components']),
                    complete_face_naming_proof=bodies[nid]['complete_face_naming_proof'])
                    for nid, descriptor in zip(sources, source_descriptors)]
            evidence = dict(feature_object_id=fid, control_record_object_id=control_id,
                input_selection_record_object_id=proxy_id, input_entity_collection_object_id=collection_id,
                pattern_entity_type='Bodies' if entity_type == 2 else 'Features',
                stored_entity_type_code=entity_type, stored_compute_option_code=compute,
                stored_control_flags=[bool(v) for v in control[61:64]],
                stored_instance_ordinal_pairs=pairs, active_instance_ordinal_pairs=active_pairs,
                element_record_object_ids=element_ids,
                element_record_ordinals=[struct.unpack_from('<I', typed(eid, ELEMENT)[1], 2)[0] for eid in element_ids],
                stored_suppressed_element_ordinals=suppressed,
                suppressed_cache_groups=[dict(stored_element_ordinal=ordinal, stored_naming_key=key,
                    element_object_id=elements[ordinal], result_cache_assignment=None)
                    for ordinal,key in pairs if ordinal in suppressed], source_native_body_object_ids=sources,
                source_cache_bodies=source_proofs, owned_result_anchor_object_ids=anchor_ids,
                mapping_record_object_id=mapping['mapping_record_object_id'], mapping_owner_object_id=mapping['owner_object_id'],
                history_blob_member=blob_member, uninterpreted_common_feature_naming_component=next(iter(common_keys)),
                complete_controller_source_group_bijection=True, element_cache_groups=[],
                matrix_source='Measured relative rigid fit after all complete face-name/typed vertex identities are fixed; no serialized per-element transform claimed',
                coordinate_scope='One explicitly mapped initial ASM cache frame with identity BODY transforms; no world/current/final placement claim',
                native_key_scope='Literal typed element ordinal paired with an opaque naming key; literal nonseed mask filters the pair table only, without API ID or visibility interpretation',
                API_element_identity=None, logical_grid_identity=None, current_placement=None,
                cache_application='Evidence only; no matrices applied to the already placed stored caches', scope=SCOPE)
            if entity_type == 1:
                evidence.update(source_feature_object_ids=source_feature_ids,
                    source_feature_input_provenance=source_provenance,
                    source_feature_face_naming_proofs=feature_name_proofs, scope=FEATURE_SCOPE)
            for element_key, naming_key in active_pairs:
                cache_group = dict(element_object_id=elements[element_key], stored_element_ordinal=element_key,
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
    if any(row.get('stored_entity_type_code') == 1 for row in result['decoded']):
        result['scope'] = ('Observed BODY/Feature PathPattern native naming/cache evidence and measured relative matrices; '
            'API element mapping, analytic traversal, serialized transforms, current/final lifecycle and regeneration unresolved')
    return result
