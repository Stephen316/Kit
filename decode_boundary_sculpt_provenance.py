"""Same-asset Boundary Fill source selections joined to positive sculpt tags.

This is a bounded numeric source-provenance correspondence. An ASM face keeps
its own entity ordinal and owning snapshot BODY; selected native source IDs do
not become persistent face identities or the snapshot BODY's identity.
"""

import copy
import struct

from decode_body_asm_identifiers import MAPPING
from decode_body_properties import BODY, COLLECTION
from decode_boundary_fill import BOUNDARY_FILL_GUID, decode_boundary_fill
from decode_boundary_fill_results import decode_boundary_fill_results
from decode_parameters import read_string
from decode_sculpt_tool_attributes import decode_sculpt_tool_attributes
from decode_selection import known_construction_entities
from decode_sketch import reference

SCOPE = ('Observed positive SCULPT face source tags and independently typed native Boundary Fill tool selections, '
         'scoped through explicit same-asset history-blob filename/collection ownership; '
         'no persistent face identity, owning native BODY assignment, exclusive feature causality or lifecycle inferred')
PLANE = '8D424E29-DE23-4B1F-A3AD-84C52A497D1A'


def decode_boundary_sculpt_provenance(data, records, member, members, features, body_bindings):
    """Return decoded/unresolved_attributes/unresolved/scope, without mutation.

    Call after ordinary Boundary Fill/construction geometry and body-binding
    recovery. ``member`` is this Design BulkStream's exact archive member.
    Each decoded entry has a feature ID, history blob proof and attributes.
    Repeated matches to distinct features remain non-exclusive correspondences.
    """
    result = {'decoded': [], 'unresolved_attributes': [], 'unresolved': [], 'scope': SCOPE}
    grouped = {}
    for r in records:
        if r.is_primary:
            grouped.setdefault(r.object_id, []).append(r)
    primary = {i: rs[0] for i, rs in grouped.items() if len(rs) == 1}
    candidates = [r for r in records if r.is_primary and r.class_guid == BOUNDARY_FILL_GUID]
    if not candidates:
        return result

    def typed(identity, guid):
        r = primary.get(identity)
        if r is None or r.class_guid != guid:
            raise ValueError('Boundary sculpt native reference missing, ambiguous or wrong class')
        return r, data[r.body:r.end]

    if (member not in members or members[member] != data or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat')
            or member.count('/FusionDesignSegmentType1/') != 1):
        result['unresolved'].append({'reason': 'Boundary sculpt Design member/bytes/asset framing disagrees'})
        return result
    asset = member.rsplit('/FusionDesignSegmentType1/', 1)[0]
    body_results = decode_boundary_fill_results(data, records)
    by_feature = {item['feature_object_id']: item for item in body_results['decoded']}
    known = known_construction_entities(data, records, features)
    mappings, sculpt = {}, {}

    def mapping_for(collection_id):
        if collection_id in mappings:
            return mappings[collection_id]
        chosen = [m for m in body_bindings.get('decoded', []) if m['owner_object_id'] == collection_id and m['body_count']]
        if len(chosen) != 1:
            raise ValueError('Boundary sculpt tool collection has no unique populated history mapping')
        m = chosen[0]
        native, payload = typed(m['mapping_record_object_id'], MAPPING)
        typed(collection_id, COLLECTION)
        if payload[:2] != bytes(2) or len(payload) < 6:
            raise ValueError('Unsupported Boundary sculpt history mapping prefix')
        count = struct.unpack_from('<I', payload, 2)[0]
        cursor = 6+16*count
        if not 1 <= count <= 100000 or cursor+16 > len(payload):
            raise ValueError('Boundary sculpt history mapping count exceeds bounds')
        entries = [struct.unpack_from('<QQ', payload, 6+16*i) for i in range(count)]
        if len({h for h, _ in entries}) != count or len({b for _, b in entries}) != count:
            raise ValueError('Boundary sculpt history mapping entries are not unique')
        if reference(payload, cursor) != collection_id or payload[cursor+11] != 0:
            raise ValueError('Boundary sculpt history mapping owner/separator disagrees')
        filename, end = read_string(payload, cursor+12)
        if (end != len(payload) or not filename.startswith('BREP.') or not filename.endswith('.smbh')
                or '/' in filename or '\\' in filename):
            raise ValueError('Unsupported Boundary sculpt history filename')
        blob_member = asset+'/Breps.BlobParts/'+filename
        if (m['body_count'] != count or m['history_blob_member'] != blob_member
                or [(b['stored_handle'], b['native_body_object_id']) for b in m['bindings']] != entries
                or blob_member not in members):
            raise ValueError('Boundary sculpt supplied mapping differs from explicit same-asset filename/entries')
        for _, identity in entries:
            typed(identity, BODY)
        proof = {'mapping_record_object_id': native.object_id, 'mapping_record_offset': native.start,
                 'mapping_owner_collection_object_id': collection_id,
                 'mapping_collection_reference_offset': native.body+cursor,
                 'mapping_filename_offset': native.body+cursor+12, 'stored_history_filename': filename,
                 'history_blob_member': blob_member, 'native_design_member': member,
                 'asset_member_prefix': asset,
                 'association': 'Raw typed mapping owner and filename match the decoded mapping and exact same-asset archive member',
                 'body_mapping_scope': 'Mapping establishes blob/collection context only; its entries do not identify SCULPT face owners'}
        if blob_member not in sculpt:
            sculpt[blob_member] = decode_sculpt_tool_attributes(members[blob_member])
        mappings[collection_id] = proof
        return proof

    for r in candidates:
        try:
            typed(r.object_id, BOUNDARY_FILL_GUID)
            native_result = by_feature.get(r.object_id)
            if native_result is None:
                raise ValueError('Boundary sculpt requires independently decoded owned native tool/result references')
            controls = decode_boundary_fill(data, records, data[r.body:r.end],
                {'object_id': r.object_id, 'class_guid': r.class_guid}, known)
            tools = {}
            collections, collection_links = set(), []
            for b in native_result['historical_body_tools']:
                native, payload = typed(b['native_body_object_id'], BODY)
                collection = reference(payload, len(payload)-11)
                typed(collection, COLLECTION)
                collections.add(collection)
                collection_links.append({'native_body_object_id': native.object_id,
                    'retained_collection_object_id': collection, 'native_collection_reference_offset': native.end-11,
                    'scope': 'Literal retained native collection link; historical inputs need not remain in active collection lists'})
                tools.setdefault(('SCULPT_TOOL_BODY', native.object_id), []).append({
                    'kind': 'Body', 'native_body_object_id': native.object_id,
                    'selection_record_object_id': b['selection_record_object_id'],
                    'descriptor_object_id': b['descriptor_object_id'], 'body_anchor_object_id': b['body_anchor_object_id'],
                    'source_owner_object_id': b['source_owner_object_id'],
                    'native_chain': 'BoundaryFill counted body-tool proxy -> owned typed descriptor -> typed body anchor -> typed native BODY'})
            if len(collections) != 1:
                raise ValueError('Boundary sculpt historical tools do not identify one shared mapping collection')
            proof = mapping_for(next(iter(collections)))
            for t in controls['tools']:
                if t['kind'] != 'ConstructionPlane':
                    continue
                selection = t['selection']
                if selection is None:
                    result['unresolved'].append({'feature_object_id': r.object_id,
                        'plane_selection_record_object_id': t['selection_record_object_id'],
                        'reason': 'Boundary sculpt plane source lacks a validated typed terminal chain'})
                    continue
                plane_id = selection['entity']['object_id']
                typed(plane_id, PLANE)
                if 'terminal_object_id' not in selection:
                    raise ValueError('Boundary sculpt only admits observed plane terminal selection grammar')
                tools.setdefault(('SCULPT_WORKPLANE_TOOL', plane_id), []).append({
                    'kind': 'ConstructionPlane', 'native_plane_object_id': plane_id,
                    'selection_record_object_id': t['selection_record_object_id'],
                    'descriptor_object_id': t['descriptor_object_id'], 'terminal_object_id': selection['terminal_object_id'],
                    'plane_feature_object_id': selection['entity']['feature_object_id'],
                    'name': selection['entity']['name'],
                    'native_chain': 'BoundaryFill counted plane-tool proxy -> owned typed plane descriptor -> typed native-plane terminal -> typed ConstructionPlane'})
            blob_member = proof['history_blob_member']
            associated = []
            for a in sculpt[blob_member]['attributes']:
                value = a['stored_signed_int64']
                matches = tools.get((a['attribute_name'], value), []) if value > 0 else []
                if not matches:
                    item = {'feature_object_id': r.object_id, 'history_blob_member': blob_member,
                        'attribute_record_index': a['attribute_record_index'],
                        'geometry_entity_ordinal': a['geometry_entity_ordinal'],
                        'attribute_name': a['attribute_name'], 'stored_signed_int64': value,
                        'reason': 'No positive exact match to a validated source-tool selection'}
                    if value < 0 and a['attribute_name'] == 'SCULPT_WORKPLANE_TOOL':
                        item['magnitude_only_candidates'] = copy.deepcopy(tools.get((a['attribute_name'], -value), []))
                        item['reason'] = 'Negative workplane literal: magnitude candidates retained; sign/polarity/source interpretation unresolved'
                    result['unresolved_attributes'].append(item)
                    continue
                associated.append({'attribute_record_index': a['attribute_record_index'],
                    'geometry_entity_ordinal': a['geometry_entity_ordinal'], 'section': a['section'],
                    'attribute_name': a['attribute_name'], 'stored_signed_int64': value,
                    'value_token_offset': a['value_token_offset'],
                    'face_owner_record_index': a['face_owner_record_index'],
                    'face_owner_entity_ordinal': a['face_owner_entity_ordinal'],
                    'snapshot_topology': copy.deepcopy(a['snapshot_topology']),
                    'owner_attribute_chain_record_indices': list(a['owner_attribute_chain_record_indices']),
                    'journal_mentions': copy.deepcopy(a['journal_mentions']),
                    'source_tools': copy.deepcopy(matches),
                    'association': 'Positive exact tag value equals an independently validated selected native source-tool ID in this same-asset history context',
                    'scope': 'Observed face source provenance; snapshot owner identity, persistent face identity, selected-cell side and current/final state remain separate'})
            result['decoded'].append({'feature_object_id': r.object_id, 'history_blob_member': blob_member,
                'blob_context': copy.deepcopy(proof), 'historical_tool_collection_links': collection_links,
                'attributes': associated, 'positive_attribute_count': len(associated),
                'feature_attribution_scope': 'Source selections correspond to these tags; this is not exclusive attribution that the feature generated each recorded face',
                'scope': SCOPE})
        except (ValueError, KeyError, IndexError, TypeError, UnicodeError, struct.error) as error:
            result['unresolved'].append({'feature_object_id': r.object_id, 'reason': str(error)})
    return result
