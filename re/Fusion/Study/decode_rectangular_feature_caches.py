"""Singleton Extrude Feature-input rectangular stored-cache correspondence.

The existing rectangular parser qualifies controls and owned selectors. The
shared rectangular cache reader alone joins controller keys, complete names and
vertex incidence, then measures the rigid fit. No Circular mode coercion occurs.
"""
from decode_body_selections import decode_body_selections
from decode_rectangular_pattern_modes import decode_rectangular_pattern_modes, FEATURE
from decode_rectangular_cache_evidence import decode_rectangular_cache_evidence
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
            raise ValueError('Rectangular Feature cache source native identity missing, duplicate or wrong class')
        return values[0]

    rec = unique(feature['object_id'], FEATURE)
    settings = decode_rectangular_pattern_modes(data, records, data[rec.body:rec.end], feature,
        native_origin_entities(data, records), features=features)
    if (settings['pattern_entity_type_code'] != 1 or settings['input_count'] != 1
            or settings['input_selection_record_object_id'] != input_proxy_id
            or settings['input_entity_collection_object_id'] != collection_id):
        raise ValueError('Only observed singleton Features rectangular cache sources supported')
    proxy = unique(input_proxy_id, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    collection = unique(collection_id, '8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF')
    selections = decode_body_selections(data, records)
    selected = settings['input_descriptors']
    source_ids, body_ids, proofs = [], [], []
    for item in selected:
        descriptor = unique(item['descriptor_object_id'], '5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
        association = unique(item['association_record_object_id'], 'C46D3EEB-40E1-43FA-83DC-9CB204335417')
        leaf = unique(item['terminal_object_id'], '90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
        source_id = item['source_feature_object_id']; source = unique(source_id, EXTRUDE)
        anchors = [a for a in selections['body_anchors'] if a['source_owner_object_id'] == source_id]
        if len(anchors) != 1:
            raise ValueError('Rectangular source Extrude must own exactly one independently typed BODY anchor')
        anchor = anchors[0]
        anchor_record = unique(anchor['object_id'], 'D26351F0-5940-4D23-AA20-2C35475A6D9E')
        body = unique(anchor['native_body_object_id'], 'D3937028-C20C-4E65-B010-94AD418A5C20')
        source_ids.append(source_id); body_ids.append(body.object_id)
        proofs.append({'input_descriptor': item, 'source_body_anchor': anchor,
            'native_records': [{'object_id': r.object_id, 'class_guid': r.class_guid,
                'record_offset': r.start, 'body_offset': r.body, 'end_offset': r.end,
                'payload_hex': data[r.body:r.end].hex()} for r in
                (proxy, collection, descriptor, association, leaf, source, anchor_record, body)]})
    return {'descriptor_object_ids': [s['descriptor_object_id'] for s in selected],
        'source_feature_object_ids': source_ids, 'source_native_body_object_ids': body_ids,
        'provenance': {'pattern_entity_type': 'Features', 'input_proxy_object_id': input_proxy_id,
            'input_collection_object_id': collection_id, 'sources': proofs,
            'exact_API_handle_identity': None, 'current_source_identity': None,
            'persistent_source_identity': None, 'qualified_historical_state': None,
            'logical_grid_identity': None,
            'scope': 'Explicit rectangular Feature selector leaf and uniquely source-owned Extrude anchor/native BODY; general multi-body feature contexts, API/current/history identity and logical-grid mapping unresolved'}}


def decode_rectangular_pattern_cache_evidence(data, records, features, member, members, body_blob_bindings):
    """Run the rectangular cache reader with a bounded Feature-source resolver."""
    return decode_rectangular_cache_evidence(data, records, features, member, members, body_blob_bindings,
        feature_source_resolver=lambda d,r,f,p,c: _feature_source(d,r,f,p,c,features=features))
