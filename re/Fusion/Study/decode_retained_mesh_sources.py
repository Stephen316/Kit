"""Typed stored mesh retained outside current counted collection membership.

No generic mesh ownership exception, lifecycle reconstruction or hidden-body
classification is made. The selected-source wrapper additionally validates an
explicit owned mesh selection; the neutral record factory makes no such claim.
"""
import math
import lzma
import struct

from decode_mesh_contents import MESH, _require
from decode_mesh_geometry_variants import decode_mesh_asset, triangle_properties
from decode_mesh_selections import decode_mesh_selection
from decode_parameters import read_string
from decode_placement import transform_point
from decode_sketch import reference


def decode_retained_mesh_source(data, records, mesh_id, selection, member, members):
    _require(selection['mesh_object_id'] == mesh_id and decode_mesh_selection(data, records,
        selection['proxy_object_id'], selection['owner_feature_object_id']) == selection,
        'Retained source selection does not match independently validated native mesh route')
    result = decode_retained_mesh_record(data, records, mesh_id, member, members)
    result['collection_scope'] = 'Retained selected-mesh owner reference with explicit current counted members excluding source; not reciprocal source membership or lifecycle reconstruction'
    result['source_identity_scope'] = 'Feature-owned typed proxy/descriptor and explicit BaseMeshFeature membership; geometry never chooses identity'
    return result


def decode_retained_mesh_record(data, records, mesh_id, member, members):
    """Strict stored mesh/asset route, requiring absence from current counted members.

    This does not establish an operation selection or parent BaseFeature. Callers
    qualify their own input association independently.
    """
    source_mesh_id = mesh_id
    def typed(identity, guid):
        rows = [r for r in records if r.is_primary and r.object_id == identity]
        _require(len(rows) == 1 and rows[0].class_guid == guid, 'Retained mesh typed reference missing, ambiguous or wrong class')
        return rows[0], data[rows[0].body:rows[0].end]
    source_record, source_payload = typed(source_mesh_id, MESH)
    stored_index = struct.unpack_from('<Q', source_payload, 2)[0]
    _require(stored_index in (1, 2) and source_payload[:2] == bytes(2) and source_payload[10:23] == bytes.fromhex('00010001000000000000000000') and source_payload[151] == 0,
             'Only captured retained-source index1/2 packed-prefix and explicit matrix variant supported')
    matrix = list(struct.unpack_from('<16d', source_payload, 23))
    second_matrix = list(struct.unpack_from('<16d', source_payload, 152))
    scale = matrix[0]
    _require(matrix == second_matrix and all(math.isfinite(v) for v in matrix) and scale > 0 and
             matrix == [scale, 0., 0., 0., 0., scale, 0., 0., 0., 0., scale, 0., 0., 0., 0., 1.],
             'Only observed equal positive native uniform matrices supported')
    base_mesh_id = reference(source_payload, 489)
    _, base_mesh = typed(base_mesh_id, '99F6967E-ED35-4222-B906-5CCF0AC70B53')
    _require(base_mesh[:6] == bytes(2)+struct.pack('<I', 1) and reference(base_mesh, 6) == source_mesh_id,
             'Retained selected mesh/BaseMeshFeature membership does not reciprocate')
    property_id = reference(source_payload, 500)
    _, name_property = typed(property_id, 'E5B3F49A-D8D0-4EEF-BC2B-FCDDAEF9745E')
    _require(len(name_property) == 21 and name_property[:2] == bytes(2) and reference(name_property, 2) == source_mesh_id and name_property[13:] == bytes(8),
             'Retained selected mesh name-property backlink disagrees')
    typed(reference(source_payload, 511), 'CD57BC48-50EC-47DC-975A-FB6DEA72F4DA')
    asset_id = reference(source_payload, 522)
    try:
        asset = decode_mesh_asset(data, records, asset_id, member, members)
    except lzma.LZMAError as error:
        raise ValueError('Retained source mesh asset compressed payload invalid: '+str(error)) from error
    _require(source_payload[533] == 0, 'Unobserved Retained source asset/name separator')
    helper_id = reference(source_payload, 534)
    _, name_helper = typed(helper_id, '702b9cd2-537c-429e-8cc4-22beeeb98c37')
    _require(len(name_helper) == 114 and name_helper[:10] == bytes.fromhex('00000000000002000000'),
             'Unobserved retained source mesh name-helper framing')
    source_name, source_name_end = read_string(source_payload, 545)
    _require(source_payload[source_name_end:source_name_end+18] == struct.pack('<4f', 0, 0, 0, 1)+b'\1\1', 'Unobserved Retained source mesh name/material framing')
    inherited = [r for r in records if not r.is_primary and r.object_id == source_mesh_id and r.class_guid == 'CB844AB6-240D-4fc9-9C9F-3679DC896D6F']
    _require(len(inherited) == 1, 'Retained selected mesh retained owner fragment ambiguous')
    retained_owner_payload = data[inherited[0].body:inherited[0].end]
    _require(len(retained_owner_payload) == 11, 'Unobserved Retained source owner fragment')
    retained_collection_id = reference(retained_owner_payload, 0)
    typed(retained_collection_id, '443807AD-8025-41A3-8A50-5157579C3D78')
    collection_bases = [r for r in records if not r.is_primary and r.object_id == retained_collection_id and r.class_guid == 'A7AEA631-985B-4DD1-8CE2-DE2C-14B54081']
    _require(len(collection_bases) == 1, 'Retained source mesh collection base ambiguous')
    retained_collection = data[collection_bases[0].body:collection_bases[0].end]
    count = struct.unpack_from('<I', retained_collection, 1)[0]
    _require(retained_collection[:1] == bytes(1) and count in (0, 1, 2) and len(retained_collection) == 16+11*count,
             'Only captured zero/one/two-member retained-owner current mesh collection supported')
    counted_members = [reference(retained_collection, 5+11*i) for i in range(count)]
    _require(source_mesh_id not in counted_members, 'Retained source is actually in current counted members')
    for identity in counted_members:
        typed(identity, MESH)
        rows = [r for r in records if not r.is_primary and r.object_id == identity and r.class_guid == 'CB844AB6-240D-4fc9-9C9F-3679DC896D6F']
        _require(len(rows) == 1 and rows[0].end-rows[0].body == 11 and reference(data[rows[0].body:rows[0].end], 0) == retained_collection_id,
                 'Retained-owner counted member backlink disagrees')
    component_id = reference(retained_collection, len(retained_collection)-11)
    typed(component_id, 'E03784ED-5E19-4E14-B9F2-3B07017018CD')
    geometry = asset['geometry']
    component_points = [transform_point(matrix, p) for p in geometry['stored_node_coordinates_float32']]
    geometry['component_node_coordinates_cm'] = component_points
    geometry.update(triangle_properties(component_points, geometry['triangle_node_indices']))
    source_mesh = {'mesh_object_id': source_mesh_id, 'mesh_record_offset': source_record.start,
        'name': source_name, 'component_object_id': component_id, 'base_mesh_feature_object_id': base_mesh_id,
        'base_mesh_feature_class_guid': '99F6967E-ED35-4222-B906-5CCF0AC70B53',
        'retained_mesh_collection_object_id': retained_collection_id, 'stored_current_collection_member_count': count,
        'retained_owner_collection_member_ids': counted_members, 'retained_membership_status': 'NotInCountedMembers',
        'collection_scope': 'Stored mesh owner reference with explicit current counted members excluding source; not reciprocal source membership, operation selection or lifecycle reconstruction',
        'source_identity_scope': 'Explicit reciprocal stored mesh/BaseMeshFeature and same-asset route only; no operation selection or parent BaseFeature inferred',
        'stored_packed_prefix_hex': source_payload[:22].hex(), 'stored_mesh_index': stored_index, 'packed_prefix_scope': 'Literal captured variant; flag semantics unresolved',
        'stored_matrix_copies': [matrix, second_matrix], 'asset_coordinates_to_component_matrix': matrix,
        **asset, 'name_property_object_id': property_id, 'name_helper_object_id': helper_id}
    return source_mesh
