"""Observed MeshReverseNormal owned selections and literal stored asset links."""
import lzma
import struct
import uuid

from decode_mesh_contents import _require
from decode_mesh_geometry_variants import decode_mesh_asset, decode_mesh_contents_variants
from decode_mesh_selections import decode_mesh_selection
from decode_parameters import read_string
from decode_sketch import reference

REVERSE = '4AB7A6BD-C40C-4C44-B7CA-0D415B6E4412'
SCOPE = ('Observed MeshReverseNormal feature class/label and owned mesh selections, typed same-asset '
         'geometry references at slots2/13, repeated dependency rows and literal cross-feature asset links. '
         'Current native mesh agreement is explicit per slot, not assumed for earlier features. Source/result '
         'temporal role, full history replay, lifecycle, packed state flags and procedural regeneration unresolved.')


def decode_mesh_reverse_normals(data, records, features, member, members, mesh_contents=None):
    result = {'decoded': [], 'unresolved': [], 'scope': SCOPE}
    targets = [r for r in records if r.is_primary and r.class_guid == REVERSE]
    if not targets:
        return result
    if mesh_contents is None:
        mesh_contents = decode_mesh_contents_variants(data, records, member, members)
    features_by_id = {f['object_id']: f for f in features}
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    for record in targets:
        try:
            _require(len(grouped.get(record.object_id, [])) == 1, 'ReverseNormal feature native identity ambiguous')
            feature = features_by_id.get(record.object_id)
            _require(feature is not None and feature.get('class_guid') == REVERSE and feature.get('record_offset') == record.start and feature.get('native_kind_label') == 'MeshReverseNormals', 'ReverseNormal discovery identity/label/offset disagrees')
            body = data[record.body:record.end]
            _require(body[:2] == bytes(2) and body[24:28] == bytes(4) and body[39:40] == bytes(1), 'Unobserved ReverseNormal prefix/separators')
            asset_at_2 = reference(body, 2)
            asset_at_13 = reference(body, 13)
            _require(asset_at_2 != asset_at_13, 'ReverseNormal two stored asset identities are not distinct')
            proxy_id = reference(body, 28)
            selection = decode_mesh_selection(data, records, proxy_id, record.object_id)
            namespace, cursor = read_string(body, 40)
            _require(namespace == str(uuid.UUID(int=0)) and cursor == 116 and body[116:119] == bytes(3) and struct.unpack_from('<I', body, 119)[0] == 2 and reference(body, 123) == proxy_id and reference(body, 134) == selection['descriptor_object_id'] and body[145:149] == b'\xff'*4, 'ReverseNormal repeated source/dependency table disagrees')
            label, cursor = read_string(body, 149)
            _require(label == 'MeshReverseNormals', 'ReverseNormal stored metadata label disagrees')
            index = struct.unpack_from('<Q', body, cursor)[0]
            name, name_end = read_string(body, cursor+8)
            _require(index == feature.get('stored_index') and name == feature.get('name') and len(body) == name_end+66 and body[name_end:name_end+7] == bytes(7), 'ReverseNormal native name/index/shared footer framing disagrees')
            state_id = reference(body, name_end+7)
            state_records = grouped.get(state_id, [])
            _require(len(state_records) == 1 and state_records[0].class_guid == 'B7F34D7B-DAC4-41A5-B67D-D672537C3BFA', 'ReverseNormal typed feature state missing/ambiguous')
            state = data[state_records[0].body:state_records[0].end]
            _require(state == bytes.fromhex('0000000000000100000000000000'), 'Unobserved ReverseNormal stored state payload')
            meshes = [m for m in mesh_contents['decoded'] if m['mesh_object_id'] == selection['mesh_object_id']]
            _require(len(meshes) == 1, 'ReverseNormal selected native mesh/asset route unresolved')
            mesh = meshes[0]
            first = decode_mesh_asset(data, records, asset_at_2, member, members)
            second = decode_mesh_asset(data, records, asset_at_13, member, members)
            settings = {'operation': 'ReverseNormals', 'native_mesh_selection': selection,
                'qualified_selected_mesh_object_id': mesh['mesh_object_id'],
                'selected_mesh_component_object_id': mesh['component_object_id'],
                'selected_mesh_current_asset_object_id': mesh['asset_object_id'],
                'asset_at_slot_2': first, 'asset_at_slot_13': second,
                'slot_2_matches_current_native_mesh_asset': asset_at_2 == mesh['asset_object_id'],
                'slot_13_matches_current_native_mesh_asset': asset_at_13 == mesh['asset_object_id'],
                'stored_feature_index': index, 'stored_state_object_id': state_id,
                'stored_state_payload_hex': state.hex(),
                'stored_shared_footer_hex': body[name_end:].hex(),
                'asset_reference_scope': 'Literal explicit slots and current-mesh asset equality only. Earlier feature slot2 may equal a later feature slot13 while differing from final current mesh; no universal temporal names or replay assigned.',
                'geometry_scope': 'Stored mesh geometry/normals are independently qualified assets; no BRep conversion or procedural reversal/regeneration implemented'}
            result['decoded'].append({'feature_object_id': record.object_id, 'kind': 'MeshReverseNormal',
                'name': name, 'class_guid': REVERSE, 'settings': settings})
        except (ValueError, IndexError, KeyError, UnicodeError, struct.error, lzma.LZMAError) as error:
            result['unresolved'].append({'feature_object_id': record.object_id, 'reason': str(error)})
    for row in result['decoded']:
        settings = row['settings']
        settings['other_feature_slot_13_references_to_this_slot_2'] = [
            {'feature_object_id': other['feature_object_id'],
             'stored_feature_index': other['settings']['stored_feature_index'],
             'shared_asset_object_id': settings['asset_at_slot_2']['asset_object_id']}
            for other in result['decoded'] if other is not row
            and other['settings']['qualified_selected_mesh_object_id'] == settings['qualified_selected_mesh_object_id']
            and other['settings']['asset_at_slot_13']['asset_object_id'] == settings['asset_at_slot_2']['asset_object_id']]
    return result
