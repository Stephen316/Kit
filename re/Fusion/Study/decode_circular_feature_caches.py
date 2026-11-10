"""Feature-input circular cache evidence after typed selector and complete naming proof.

The shared body reader remains the sole controller/key/vertex-fit implementation.
FPM literals are retained as framed opaque metadata, never used as identities.
"""
from decode_asm_recipe_tags import decode_asm_generic_tags, encode_generic_tag_payload
from decode_body_selections import decode_body_selections
from decode_circular_patterns import decode_circular_pattern, FEATURE
from decode_circular_placement_evidence import decode_circular_placement_evidence
from decode_selection import native_origin_entities

EXTRUDE = 'DD405BC2-D673-44F0-8833-5CB2A1C186C7'


def _feature_source(data, records, feature, input_proxy_id, collection_id, *, features):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    def unique(identity, guid=None):
        values = grouped.get(identity, [])
        if len(values) != 1 or (guid is not None and values[0].class_guid != guid):
            raise ValueError('Circular feature cache source native identity missing, duplicate or wrong class')
        return values[0]
    rec = unique(feature['object_id'], FEATURE)
    # Reuse the existing complete collection/descriptor/leaf parser, preserving
    # Features mode and its ordinary controls rather than coercing to Bodies.
    settings = decode_circular_pattern(data, records, data[rec.body:rec.end], feature,
        native_origin_entities(data, records), features=features)
    if (settings['pattern_entity_type_code'] != 1 or settings['input_count'] != 1
            or settings['input_selection_record_object_id'] != input_proxy_id
            or settings['input_entity_collection_object_id'] != collection_id):
        raise ValueError('Only observed singleton Features circular cache sources supported')
    selections = decode_body_selections(data, records)
    selected = settings['input_descriptors']
    source_ids, body_ids, proofs = [], [], []
    for item in selected:
        descriptor = unique(item['descriptor_object_id'], '5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
        leaf = unique(item['terminal_object_id'], '90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
        source_id = item['source_feature_object_id']; source = unique(source_id, EXTRUDE)
        anchors = [a for a in selections['body_anchors'] if a['source_owner_object_id'] == source_id]
        if len(anchors) != 1:
            raise ValueError('Circular source Extrude must own exactly one independently typed BODY anchor')
        anchor = anchors[0]; unique(anchor['object_id'], 'D26351F0-5940-4D23-AA20-2C35475A6D9E')
        # Anchor reader already validates the actual native BODY class/backlink.
        source_ids.append(source_id); body_ids.append(anchor['native_body_object_id'])
        proofs.append({'input_descriptor': item, 'source_body_anchor': anchor,
            'native_records': [{'object_id': r.object_id, 'class_guid': r.class_guid,
                'record_offset': r.start, 'body_offset': r.body, 'end_offset': r.end,
                'payload_hex': data[r.body:r.end].hex()} for r in
                (descriptor, leaf, source, unique(anchor['object_id']), unique(anchor['native_body_object_id']))]})
    return {'descriptor_object_ids': [s['descriptor_object_id'] for s in selected],
        'source_feature_object_ids': source_ids, 'source_native_body_object_ids': body_ids,
        'provenance': {'pattern_entity_type': 'Features', 'input_proxy_object_id': input_proxy_id,
            'input_collection_object_id': collection_id, 'sources': proofs,
            'exact_API_handle_identity': None, 'current_source_identity': None,
            'persistent_source_identity': None, 'qualified_historical_state': None,
            'scope': 'Explicit feature selector leaf and uniquely source-owned Extrude anchor/native BODY; current visibility, general multi-body feature contexts and persistent identity unresolved'}}


def _face_names(blob, parsed, graph):
    tags = decode_asm_generic_tags(blob, parsed, allow_fpm_tracking=True)
    face_ids = set(graph['face_indices']); records = parsed['records']
    result, proof = {}, []
    for face_id in graph['face_indices']:
        face_tags = [t for t in tags['tags'] if t['owner_kind'] == 'face' and t['owner_record_index'] == face_id]
        face = records[face_id]; chain = []; previous = -1; current = face['tokens'][0]['value']
        while current != -1:
            if type(current) is not int or not 0 <= current < len(records) or current in chain or len(chain) >= 16:
                raise ValueError('Circular canonical FACE attribute chain missing or cyclic')
            attr = records[current]; t = attr['tokens']
            if (attr['section'] != 'geometry' or attr['name'] != 'ATTRIB_CUSTOM-attrib'
                    or [v['kind'] for v in t[:5]] != ['pointer','integer','pointer','pointer','pointer']
                    or t[0]['value'] != -1 or t[1]['value'] != -1
                    or t[3]['value'] != previous or t[4]['value'] != face_id):
                raise ValueError('Circular canonical FACE attribute owner/previous header disagrees')
            chain.append(current); previous, current = current, t[2]['value']
        if not face_tags or any(t['owner_attribute_chain'] != chain for t in face_tags):
            raise ValueError('Circular complete generic naming owner chain unresolved')
        accepted = {t['attribute_record_index']: t for t in face_tags}
        ignored = [t for t in tags['ignored_validated_other_definition_attributes']
            if t['owner_kind'] == 'face' and t['owner_record_index'] == face_id]
        if any(t['definition_name'] != 'FPM_tracked_attrib_def' for t in ignored):
            raise ValueError('Unobserved circular FACE non-naming definition')
        if set(chain) != set(accepted) | {t['attribute_record_index'] for t in ignored}:
            raise ValueError('Circular canonical FACE chain contains an unvalidated attribute')
        tuples = set()
        for tag in face_tags:
            if len(tag['terms']) != 1 or encode_generic_tag_payload(tag) != blob[tag['payload_offset']:tag['payload_end_offset']]:
                raise ValueError('Circular singleton complete name payload/replay disagrees')
            term = tag['terms'][0]; components = tuple(term['stored_reference_components_int32'])
            if (not term['name'].lstrip('-').isdigit() or len(components) not in (1,3)
                    or any(type(v) is not int or not 1 <= v <= 0x7fffffff for v in components)):
                raise ValueError('Circular complete face naming tuple outside observed grammar')
            tuples.add((term['name'],term['stored_index'],components))
        if len(tuples) != 1:
            raise ValueError('Circular complete FACE naming tuple ambiguous')
        name,index,components = tuples.pop()
        result[face_id] = {'name_key': (name,index), 'components': components,
            'attribute_indices': [i for i in chain if i in accepted]}
        proof.append({'face_record_index': face_id, 'owner_attribute_chain': chain,
            'generic_tags': face_tags, 'opaque_FPM_attributes': [dict(t,
                payload_hex=blob[records[t['attribute_record_index']]['offset']:records[t['attribute_record_index']]['end_offset']].hex()) for t in ignored]})
    if len(result) != 6 or len({v['name_key'] for v in result.values()}) != 6 or set(result) != face_ids:
        raise ValueError('Only six uniquely completely named circular cache FACEs supported')
    return {'names': result, 'proof': {'body_record_index': graph['body_index'], 'faces': proof,
        'FPM_literal_identity': None,
        'scope': 'Canonical generic payload replay plus complete reciprocal FACE chains; FPM schema/literals remain opaque metadata and select no identities'}}


def decode_circular_cache_evidence(data, records, features, member, members, body_blob_bindings):
    """Shared circular reader with explicitly bounded Feature-input resolvers."""
    return decode_circular_placement_evidence(data, records, features, member, members, body_blob_bindings,
        feature_source_resolver=lambda d,r,f,p,c: _feature_source(d,r,f,p,c,features=features),
        face_name_resolver=_face_names)
