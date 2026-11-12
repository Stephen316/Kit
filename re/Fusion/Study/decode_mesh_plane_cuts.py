"""Observed native MeshPlaneCut controls and explicit mesh/plane/asset routes."""
import lzma
import struct

from decode_mesh_contents import ASSET, _require
from decode_mesh_geometry_variants import PLANE_CUT, decode_mesh_asset, decode_mesh_contents_variants
from decode_mesh_selections import decode_mesh_selection
from decode_parameters import read_string
from decode_placement import IDENTITY, cross
from decode_sketch import attributes, numbers, reference

PLANE_PROXY = '2CA5A1CD-C99B-4C9B-91AF-57989148E841'
PLANE_DESCRIPTOR = '5A1BF548-241F-46FD-9FB5-E4B05126EB9D'
PLANE_GEOMETRY = '8D424E29-DE23-4B1F-A3AD-84C52A497D1A'
PLANE_FEATURE = 'D869265F-F339-4751-A066-91D30F81FF08'
SCOPE = ('Observed Trim/SplitBody and NoFill/MinimalFill native controls, owned mesh proxy/descriptor identity, '
         'typed selected offset-plane geometry and same-asset naming/geometry routes. Flip remains unresolved '
         'because all captured API values are false; current mesh selection is not lifecycle replay, and '
         'stored additional asset temporal role, mesh regeneration and unofficial API stability remain unclaimed.')


def decode_mesh_plane_cuts(data, records, features, member, members, mesh_contents=None):
    if mesh_contents is None:
        mesh_contents = decode_mesh_contents_variants(data, records, member, members)
    result = {'decoded': [], 'unresolved': [], 'scope': SCOPE}
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    def typed(identity, guid):
        rows = grouped.get(identity, [])
        _require(len(rows) == 1 and rows[0].class_guid == guid, 'PlaneCut typed identity missing, ambiguous or wrong class')
        return rows[0], data[rows[0].body:rows[0].end]
    feature_rows = {f['object_id']: f for f in features}
    for record in records:
        if not record.is_primary or record.class_guid != PLANE_CUT:
            continue
        try:
            typed(record.object_id, PLANE_CUT)
            feature = feature_rows.get(record.object_id)
            _require(feature is not None and feature.get('class_guid') == PLANE_CUT and feature.get('native_kind_label') == 'MeshPlaneCut', 'PlaneCut feature discovery identity/label missing')
            body = data[record.body:record.end]
            _require(body[:2] == bytes(2) and len(body) > 200, 'Unobserved PlaneCut prefix/extent')
            mode, raw_flags = struct.unpack_from('<II', body, 2)
            _require(mode in (0, 1) and raw_flags == 16 and numbers(body, 10, 16) == IDENTITY, 'Unobserved PlaneCut mode/flags/frame')
            fill = struct.unpack_from('<I', body, 138)[0]
            _require(fill in (0, 1) and body[142] == 0 and (mode, fill) in ((0, 0), (0, 1), (1, 1)), 'Unobserved PlaneCut fill/boolean combination')
            source_selection = decode_mesh_selection(data, records, reference(body, 143), record.object_id)
            cursor = 154
            if mode == 1:
                result_selection = decode_mesh_selection(data, records, reference(body, cursor), record.object_id)
                cursor += 11
            else:
                _require(body[cursor] == 0, 'Unobserved nullable PlaneCut result proxy')
                cursor += 1; result_selection = None
            plane_proxy_id = reference(body, cursor); cursor += 11
            current_asset_id = reference(body, cursor); cursor += 11
            additional_asset_id = reference(body, cursor); cursor += 11
            typed(current_asset_id, ASSET); typed(additional_asset_id, ASSET)
            _require(body[cursor:cursor+4] == bytes(4) and reference(body, cursor+4) == source_selection['proxy_object_id'], 'PlaneCut repeated source proxy framing disagrees')
            _, proxy = typed(plane_proxy_id, PLANE_PROXY)
            _require(len(proxy) == 105 and proxy[:6] == bytes(2)+struct.pack('<I', 1) and struct.unpack_from('<I', proxy, 19)[0] == 1 and reference(proxy, 94) == record.object_id, 'Unobserved owned PlaneCut plane proxy')
            secondary_id = reference(proxy, 23)
            _, secondary = typed(secondary_id, '2DF7DA30-A4E4-4260-AFD1-D9C7154CB44B')
            _require(secondary == bytes.fromhex('0000010100'), 'Unobserved PlaneCut plane secondary payload')
            descriptor_id = reference(proxy, 6)
            _, descriptor = typed(descriptor_id, PLANE_DESCRIPTOR)
            _require(len(descriptor) == 252 and descriptor[:2] == bytes(2) and struct.unpack_from('<I', descriptor, 13)[0] == 1 and reference(descriptor, 241) == record.object_id, 'Unobserved PlaneCut selected-plane descriptor')
            namespace, string_end = read_string(descriptor, 17)
            entity_guid, string_end = read_string(descriptor, string_end)
            _require(string_end == 169 and descriptor[169:185] == struct.pack('<QII', 2, 0, 0), 'Unobserved selected-plane namespace/context framing')
            leaf_id = reference(descriptor, 2)
            _, leaf = typed(leaf_id, '90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
            _require(len(leaf) == 10 and leaf[:2] == bytes(2), 'Unobserved selected-plane identity leaf')
            plane_id = struct.unpack_from('<Q', leaf, 2)[0]
            plane_record, plane = typed(plane_id, PLANE_GEOMETRY)
            _require(plane[:2] == b'\0\1', 'Unobserved PlaneCut selected-plane geometry prefix')
            props, p = attributes(plane, 2)
            _require(props == {'EntityGenesis': 0} and struct.unpack_from('<I', plane, p)[0] == 1 and plane[p+20] == 0, 'Only captured explicit offset-plane geometry is supported')
            values = numbers(plane, p+21, 9)
            origin, x_axis, y_axis = values[:3], values[3:6], values[6:]
            _require(x_axis == [1., 0., 0.] and y_axis == [0., 1., 0.] and origin == [0., 0., 1.], 'Unobserved PlaneCut selected-plane placement')
            _, p_end = read_string(plane, p+109)
            plane_feature_id = reference(plane, p_end+20)
            _, plane_feature = typed(plane_feature_id, PLANE_FEATURE)
            _require(reference(plane_feature, 19) == plane_id, 'Selected plane geometry/feature backlink disagrees')
            plane_name, _ = read_string(plane, p_end+33)
            selected_plane = {'proxy_object_id': plane_proxy_id, 'descriptor_object_id': descriptor_id,
                'leaf_object_id': leaf_id, 'plane_geometry_object_id': plane_id,
                'plane_geometry_record_offset': plane_record.start, 'plane_feature_object_id': plane_feature_id,
                'namespace_text': namespace, 'entity_guid_text': entity_guid, 'name': plane_name,
                'origin_cm': origin, 'x_axis': x_axis, 'y_axis': y_axis, 'normal': cross(x_axis, y_axis),
                'proof': 'Owned plane proxy/descriptor, typed numeric identity leaf, explicit native plane geometry and reciprocal WorkPlane feature backlink',
                'api_scope': 'Compared to actual input.cutPlane and ConstructionPlane.geometry; no feature.cutPlane getter exists'}
            native_mesh_id = source_selection['mesh_object_id']
            current_rows = [r for r in mesh_contents['decoded'] if r['mesh_object_id'] == native_mesh_id]
            _require(len(current_rows) == 1 and current_rows[0]['asset_object_id'] == current_asset_id, 'PlaneCut current-asset field does not match qualified native mesh asset route')
            current = decode_mesh_asset(data, records, current_asset_id, member, members)
            additional = decode_mesh_asset(data, records, additional_asset_id, member, members)
            result_row = None
            if result_selection is not None:
                rows = [r for r in mesh_contents['decoded'] if r['mesh_object_id'] == result_selection['mesh_object_id']]
                _require(len(rows) == 1 and rows[0]['feature_object_id'] == record.object_id and rows[0]['native_feature_owner_selection'] == result_selection, 'PlaneCut explicit additional result mesh route incomplete')
                result_row = {'mesh_object_id': rows[0]['mesh_object_id'], 'asset_object_id': rows[0]['asset_object_id'],
                              'asset_member': rows[0]['asset_member'], 'native_feature_owner_selection': result_selection}
            settings = {'mesh_plane_cut_type': 'Trim' if mode == 0 else 'SplitBody',
                'stored_mesh_plane_cut_type_code': mode, 'mesh_plane_cut_fill_type': 'NoFill' if fill == 0 else 'MinimalFill',
                'stored_mesh_plane_cut_fill_type_code': fill, 'stored_uninterpreted_flags_at_6': raw_flags,
                'stored_uninterpreted_boolean_at_142': False,
                'is_flip': None, 'is_flip_status': 'All actual captured API values false; native flip encoding not independently established',
                'stored_feature_matrix': IDENTITY, 'source_mesh_selection': source_selection,
                'selected_plane': selected_plane, 'qualified_current_mesh_object_id': native_mesh_id,
                'current_native_mesh_asset': current, 'additional_stored_asset': additional,
                'additional_asset_scope': 'Explicit additional asset field with typed same-asset UUID/file proof. Captured API source geometry agrees, but temporal/lifecycle role is not assigned solely from this slot.',
                'explicit_additional_result_mesh': result_row,
                'geometry_scope': 'Stored triangular meshes and native selections only; no PlaneCut regeneration, history replay or BRep conversion'}
            result['decoded'].append({'feature_object_id': record.object_id, 'kind': 'MeshPlaneCut',
                'name': feature.get('name'), 'class_guid': PLANE_CUT, 'settings': settings})
        except (ValueError, IndexError, UnicodeError, struct.error, lzma.LZMAError) as error:
            result['unresolved'].append({'feature_object_id': record.object_id, 'reason': str(error)})
    return result
