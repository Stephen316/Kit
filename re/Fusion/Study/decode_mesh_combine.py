"""Observed MeshCombine operations with current-target/retained-tool provenance.

Geometry failures remain separate from typed native operation controls. Invariant
zero fields are not promoted to algorithm or keep/new-component semantics.
"""
import lzma
import struct
import uuid

from decode_mesh_contents import MESH, MESH_FEATURE, decode_mesh_contents
from decode_mesh_geometry_variants import decode_mesh_asset, decode_mesh_contents_variants, native_layout
from decode_mesh_selections import decode_mesh_selection
from decode_parameters import read_string
from decode_retained_mesh_sources import decode_retained_mesh_source
from decode_sketch import reference
from decode_timeline import feature_state

COMBINE = 'EE0E56E8-5894-4D65-BAF4-9DAAF811307F'
OPERATIONS = {0: 'Join', 1: 'Cut', 2: 'Intersect'}
TARGET_PREFIX = bytes.fromhex('00000100000000000000000101010000000000000000')
TOOL_PREFIX = bytes.fromhex('00000200000000000000000100010000000000000000')
SCOPE = ('Observed single-tool MeshCombine Join/Cut/Intersect controls and typed target/retained-tool/asset '
         'routes in the captured root family. Algorithm and keep/new-component flag encoding, retained-object '
         'lifecycle, unsupported compressed geometry and regeneration remain unresolved.')


def decode_mesh_combine(data, records, features, member, members, mesh_contents=None):
    result = {'decoded': [], 'unresolved': [], 'scope': SCOPE}
    candidates = [r for r in records if r.is_primary and r.class_guid == COMBINE]
    if not candidates:
        return result
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)

    def typed(identity, guid):
        rows = grouped.get(identity, [])
        if len(rows) != 1 or rows[0].class_guid != guid:
            raise ValueError('MeshCombine typed identity missing, ambiguous or wrong class')
        record = rows[0]
        return record, data[record.body:record.end]

    named = {}
    for feature in features:
        named.setdefault(feature['object_id'], []).append(feature)
    strict_meshes = mesh_contents if mesh_contents is not None else decode_mesh_contents_variants(data, records, member, members)
    for record in candidates:
        try:
            typed(record.object_id, COMBINE)
            rows = named.get(record.object_id, [])
            if len(rows) != 1 or rows[0]['class_guid'] != COMBINE or rows[0]['record_offset'] != record.start:
                raise ValueError('MeshCombine discovered feature metadata differs from primary record')
            feature = rows[0]
            body = data[record.body:record.end]
            if (len(body) < 300 or body[:2] != bytes(2) or body[6:11] != bytes(5)
                    or struct.unpack_from('<I', body, 11)[0] != 1
                    or body[48:52] != bytes(4) or body[63] != 0):
                raise ValueError('Unobserved MeshCombine singleton-tool/opaque-control framing')
            operation = struct.unpack_from('<I', body, 2)[0]
            if operation not in OPERATIONS:
                raise ValueError('Unobserved MeshCombine operation code')
            tool = decode_mesh_selection(data, records, reference(body, 15), record.object_id)
            target = decode_mesh_selection(data, records, reference(body, 52), record.object_id)
            if (tool['mesh_object_id'] == target['mesh_object_id']
                    or tool['proxy_object_id'] == target['proxy_object_id']):
                raise ValueError('MeshCombine target/tool selections unexpectedly alias')
            _, target_body = typed(target['mesh_object_id'], MESH)
            _, tool_body = typed(tool['mesh_object_id'], MESH)
            if target_body[:22] != TARGET_PREFIX or tool_body[:22] != TOOL_PREFIX:
                raise ValueError('MeshCombine selected native mesh prefixes outside captured target/tool family')
            native_ids = {r.object_id for r in records if r.is_primary and r.class_guid == MESH}
            if native_ids != {target['mesh_object_id'], tool['mesh_object_id']}:
                raise ValueError('MeshCombine outside observed two-native-mesh root family')
            nil, cursor = read_string(body, 64)
            if nil != str(uuid.UUID(int=0)) or body[cursor:cursor+3] != bytes(3):
                raise ValueError('MeshCombine dependency-table nil UUID/separator differs')
            count = struct.unpack_from('<I', body, cursor+3)[0]
            table_start = cursor+7
            expected = [target['proxy_object_id'], target['descriptor_object_id'],
                        tool['proxy_object_id'], tool['descriptor_object_id']]
            if count != 4 or [reference(body, table_start+11*i) for i in range(count)] != expected:
                raise ValueError('MeshCombine ordered dependency table does not repeat target/tool selections')
            cursor = table_start+44
            if body[cursor:cursor+4] != b'\xff'*4:
                raise ValueError('MeshCombine feature-label marker differs')
            label, cursor = read_string(body, cursor+4)
            index = struct.unpack_from('<Q', body, cursor)[0]
            name, end = read_string(body, cursor+8)
            if (label != 'MeshCombine' or index != feature['stored_index'] or name != feature.get('name')
                    or len(body)-end != 66):
                raise ValueError('MeshCombine label/index/name/shared-footer extent differs')
            state = feature_state(body)
            metadata = decode_mesh_contents(data, records, member, members,
                native_layout_decoder=native_layout, metadata_only=True)
            current = [r for r in metadata['decoded'] if r['mesh_object_id'] == target['mesh_object_id']]
            if len(current) != 1:
                raise ValueError('MeshCombine target lacks one strict current native mesh metadata route')
            current = current[0]
            source = decode_retained_mesh_source(data, records, tool['mesh_object_id'], tool, member, members)
            if (current['native_feature_class_guid'] != MESH_FEATURE
                    or current['feature_object_id'] == record.object_id
                    or current['collection_mesh_object_ids'] != [target['mesh_object_id']]):
                raise ValueError('MeshCombine current target owner/membership outside captured native BaseMesh family')
            if (source['mesh_object_id'] != tool['mesh_object_id']
                    or source['base_mesh_feature_class_guid'] != MESH_FEATURE
                    or source['base_mesh_feature_object_id'] in (record.object_id, current['feature_object_id'])
                    or source['component_object_id'] != current['component_object_id']
                    or source['retained_mesh_collection_object_id'] != current['mesh_collection_object_id']
                    or source['retained_owner_collection_member_ids'] != current['collection_mesh_object_ids']
                    or source['retained_membership_status'] != 'NotInCountedMembers'
                    or source['geometry']['node_count'] != 4 or source['geometry']['triangle_count'] != 4):
                raise ValueError('MeshCombine retained tool owner/nonmembership outside captured tetra family')
            current_asset_id = reference(body, 26)
            additional_asset_id = reference(body, 37)
            if current_asset_id != current['asset_object_id'] or current_asset_id == additional_asset_id:
                raise ValueError('MeshCombine stored current/additional asset references disagree')
            if source['asset_object_id'] in (current_asset_id, additional_asset_id):
                raise ValueError('MeshCombine target/additional/tool stored asset identities unexpectedly alias')
            additional = decode_mesh_asset(data, records, additional_asset_id, member, members)
            if (additional['geometry']['node_count'] != 4 or additional['geometry']['triangle_count'] != 4):
                raise ValueError('MeshCombine additional asset outside captured tetra source-cache family')
            geometry_errors = []
            try:
                current_geometry = decode_mesh_asset(data, records, current_asset_id, member, members)
            except (ValueError, IndexError, UnicodeError, struct.error, lzma.LZMAError) as error:
                current_geometry = None
                geometry_errors.append({'asset_object_id': current_asset_id, 'asset_member': current['asset_member'],
                    'reason': str(error), 'scope': 'Strict stored geometry failed; metadata and operation provenance do not suppress or repair the failure'})
            # Exact replay of common framing, without replacing source bytes.
            def ref(identity):
                return b'\1'+struct.pack('<Q', identity)+bytes(2)
            def text(value):
                return struct.pack('<I', len(value))+value.encode('utf-16le')
            replay = (bytes(2)+struct.pack('<I', operation)+bytes(5)+struct.pack('<I', 1)
                +ref(tool['proxy_object_id'])+ref(current_asset_id)+ref(additional_asset_id)+bytes(4)
                +ref(target['proxy_object_id'])+bytes(1)+text(nil)+bytes(3)+struct.pack('<I', 4)
                +b''.join(ref(i) for i in expected)+b'\xff'*4+text(label)+struct.pack('<Q', index)+text(name)+body[end:])
            if replay != body:
                raise ValueError('MeshCombine full feature payload replay disagrees')
            settings = {'operation': OPERATIONS[operation], 'stored_operation_code': operation,
                'stored_uninterpreted_uint32_at_6': struct.unpack_from('<I', body, 6)[0],
                'stored_uninterpreted_byte_at_10': body[10],
                'algorithm_type': None, 'is_keep_tool_bodies': None, 'is_new_component': None,
                'invariant_controls_scope': 'Only Legacy/False/False API readbacks were captured. Zero native fields remain literal; algorithm and flag mapping is not independently contrasted',
                'target_selection': target, 'tool_selections': [tool],
                'target_mesh_metadata': current, 'retained_tool_sources': [source],
                'mesh_combine_owns_native_mesh': None,
                'native_api_owner_scope': 'Reciprocal native BaseMeshFeature owner identities remain separate from MeshCombine input roles and actual API baseOrFormFeature null getters',
                'stored_current_asset_reference_offset': 26, 'stored_additional_asset_reference_offset': 37,
                'current_target_asset_geometry': current_geometry,
                'additional_stored_asset': additional, 'additional_asset_temporal_role': None,
                'asset_scope': 'Current target asset is independently bound by native Mesh pointer/UUID/file/header. Additional typed asset is explicit, but source/prior/result lifecycle is not assigned from this field or geometry equality',
                'geometry_unresolved': geometry_errors,
                'strict_current_mesh_diagnostics': [r for r in strict_meshes['unresolved'] if r['mesh_object_id'] in native_ids],
                'history_scope': 'Target remains a current counted collection member; selected tool has retained native records. No persistent mesh identity, deletion/visibility flag semantics or source-state replay inferred',
                'ordered_dependency_object_ids': expected,
                'layout': {'feature_body_offset': record.body, 'feature_body_end_offset': record.end,
                    'feature_body_hex': body.hex(), 'dependency_table_body_relative_offset': table_start,
                    'dependency_table_hex': body[table_start:table_start+44].hex(),
                    'shared_footer_hex': body[end:].hex(), 'shared_feature_state': state,
                    'exact_full_payload_replay': True}}
            result['decoded'].append({'feature_object_id': record.object_id, 'kind': 'MeshCombine',
                'name': name, 'settings': settings})
        except (ValueError, KeyError, IndexError, TypeError, UnicodeError, struct.error, lzma.LZMAError) as error:
            result['unresolved'].append({'feature_object_id': record.object_id, 'reason': str(error)})
    return result
