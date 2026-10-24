"""Feature PathPattern cache evidence with the original typed dual-anchor route.

The full native PathPattern input reader qualifies each source. The shared Path
cache core alone proves key/naming/vertex correspondences before measuring fits.
"""
import copy

from decode_assembly import decode_assembly
from decode_body_selections import decode_body_selections
from decode_path_pattern_inputs import decode_path_pattern_inputs, FEATURE
from decode_path_pattern_cache_evidence import decode_path_pattern_cache_evidence as _decode_cache
from decode_placement import decode_placement
from decode_sketch import decode_sketches

EXTRUDE = 'DD405BC2-D673-44F0-8833-5CB2A1C186C7'


def _feature_source(data, records, feature, input_proxy_id, collection_id, *, features):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)

    def unique(identity, guid=None):
        values = grouped.get(identity, [])
        if len(values) != 1 or (guid is not None and values[0].class_guid != guid):
            raise ValueError('Feature Path cache native identity missing, duplicate or wrong class')
        return values[0]

    unique(feature['object_id'], FEATURE)
    # Reparse fresh sketch/placement/assembly fragments on a private metadata
    # copy. No invented empty assembly or trusted caller control dictionary.
    fresh = copy.deepcopy(features)
    decode_sketches(data, records, fresh)
    decode_placement(data, records, fresh)
    assembly = decode_assembly(data, records, fresh)
    selections = decode_body_selections(data, records)
    decoded = decode_path_pattern_inputs(data, records, fresh, assembly, body_selections=selections)
    rows = [r for r in decoded['decoded'] if r['feature_object_id'] == feature['object_id']]
    errors = [r for r in decoded['unresolved'] if r['feature_object_id'] == feature['object_id']]
    if len(rows) != 1 or errors:
        raise ValueError('Feature Path cache full native input proof unresolved: '+str(errors))
    settings = rows[0]['settings']
    if (settings.get('pattern_entity_type') != 'Features' or settings['stored_entity_type_code'] != 1
            or settings['input_entity_count'] != 1 or settings['auxiliary_selection_record_object_id'] != input_proxy_id
            or settings['input_entity_collection_object_id'] != collection_id):
        raise ValueError('Only observed singleton Extrude Feature Path cache inputs supported')
    proxy = unique(input_proxy_id, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    collection = unique(collection_id, '8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF')
    selected = settings['input_descriptors']; source_ids, body_ids, proofs = [], [], []
    for item in selected:
        descriptor = unique(item['descriptor_object_id'], '5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
        leaf = unique(item['terminal_object_id'], '90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
        association = unique(item['association_record_object_id'], 'C46D3EEB-40E1-43FA-83DC-9CB204335417')
        bridge = unique(item['association_bridge_object_id'], 'CB4F4CC2-9D6F-48BA-9B1F-20C1992C9C9C')
        second_leaf = unique(item['association_terminal_object_id'], '90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
        source_id = item['source_feature_object_id']; source = unique(source_id, EXTRUDE)
        anchors = [a for a in selections['body_anchors'] if a['source_owner_object_id'] == source_id]
        if (len(anchors) != 1 or anchors[0]['object_id'] != item['source_body_anchor_object_id']
                or anchors[0]['native_body_object_id'] != item['source_native_body_object_id']):
            raise ValueError('Feature Path descriptor/association anchor is not the unique source-owned BODY anchor')
        anchor = anchors[0]
        anchor_record = unique(anchor['object_id'], 'D26351F0-5940-4D23-AA20-2C35475A6D9E')
        body = unique(anchor['native_body_object_id'], 'D3937028-C20C-4E65-B010-94AD418A5C20')
        source_ids.append(source_id); body_ids.append(body.object_id)
        proofs.append(dict(input_descriptor=item, source_body_anchor=anchor,
            native_records=[dict(object_id=r.object_id,class_guid=r.class_guid,
                record_offset=r.start,body_offset=r.body,end_offset=r.end,
                payload_hex=data[r.body:r.end].hex()) for r in
                (proxy,collection,descriptor,leaf,association,bridge,second_leaf,source,anchor_record,body)]))
    return dict(descriptor_object_ids=[s['descriptor_object_id'] for s in selected],
        source_feature_object_ids=source_ids, source_native_body_object_ids=body_ids,
        provenance=dict(pattern_entity_type='Features',input_proxy_object_id=input_proxy_id,
            input_collection_object_id=collection_id,sources=proofs,
            full_path_input_settings=settings,fresh_assembly_scope=assembly['scope'],
            fresh_assembly_unresolved=assembly['unresolved'],
            exact_API_handle_identity=None,current_source_identity=None,persistent_source_identity=None,
            qualified_historical_state=None,path_traversal=None,
            scope='Explicit Feature leaf plus matching descriptor/association bridge anchor, unique source-owned Extrude BODY, and freshly parsed native Path input/sketch/assembly context; API/current/history identity and traversal unresolved'))


def decode_path_pattern_cache_evidence(data, records, features, member, members, body_blob_bindings):
    """Run Path-specific key/cache proof with its bounded Feature-source reader."""
    return _decode_cache(data,records,features,member,members,body_blob_bindings,
        feature_source_resolver=lambda d,r,f,p,c: _feature_source(d,r,f,p,c,features=features))
