"""Stored BaseMesh source provenance independent of current-mesh classification."""
import struct

from decode_mesh_contents import MESH, MESH_FEATURE
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_retained_mesh_sources import decode_retained_mesh_record
from decode_sketch import reference

SCOPE = ('Partial reciprocal BaseMeshFeature/stored mesh and same-asset provenance. Current accepted '
         'mesh routes remain separate from retained records absent from current counted members; '
         'parent BaseFeature, API handle assignment, visibility, qualified historical state and lifecycle unresolved.')


def decode_base_mesh_sources(data, records, features, member, members, *,
                             definitions=None, mesh_contents=None):
    """Return partial/unresolved/scope; never refine feature kinds or old warnings."""
    from decode_base_mesh_feature_definitions import decode_base_mesh_feature_definitions
    result = dict(partial=[], unresolved=[], scope=SCOPE)
    fresh = decode_base_mesh_feature_definitions(data, records, features)
    definitions_match = definitions is None or definitions == fresh
    # Independently validate any caller-provided current route, including its
    # native ownership, collection membership and same-asset buffer identities.
    current = decode_mesh_contents_variants(data, records, member, members)
    current_matches = mesh_contents is None or mesh_contents == current
    primary = {}
    for record in records:
        if record.is_primary:
            primary.setdefault(record.object_id, []).append(record)

    def typed(identity, guid):
        rows = primary.get(identity, [])
        if len(rows) != 1 or rows[0].class_guid != guid:
            raise ValueError('BaseMesh source typed identity missing, ambiguous or wrong class')
        record = rows[0]
        return record, data[record.body:record.end]

    for definition in fresh['partial']:
        identity = definition['feature_object_id']
        try:
            if not definitions_match:
                raise ValueError('BaseMesh source supplied definitions differ from independently decoded source')
            if not current_matches:
                raise ValueError('BaseMesh source supplied current mesh summary differs from native source')
            ids = definition['stored_mesh_object_ids']
            if len(ids) != 1:
                raise ValueError('BaseMesh source requires one explicitly stored mesh')
            mesh_id = ids[0]
            feature_record, feature = typed(identity, MESH_FEATURE)
            mesh_record, mesh = typed(mesh_id, MESH)
            if feature[:6] != bytes(2)+struct.pack('<I', 1) or reference(feature, 6) != mesh_id:
                raise ValueError('BaseMesh source feature singleton mesh reference differs')
            candidates = [row for row in current['decoded'] if row['mesh_object_id'] == mesh_id]
            row = dict(feature_object_id=identity, mesh_object_id=mesh_id,
                feature_mesh_reference_offset=feature_record.body+6,
                native_mesh_record_offset=mesh_record.start,
                parent_base_feature_object_id=None, API_handle_assignment=None,
                visibility=None, qualified_historical_state=None, lifecycle=None, scope=SCOPE)
            if candidates:
                if len(candidates) != 1 or candidates[0]['feature_object_id'] != identity:
                    raise ValueError('BaseMesh source accepted current route owner missing or ambiguous')
                accepted = candidates[0]
                owner_offset = accepted['asset_reference_field_offset']-33
                if reference(data, owner_offset) != identity:
                    raise ValueError('BaseMesh source current mesh feature backlink differs')
                row.update(relationship_kind='CurrentAcceptedMeshRoute',
                    source_membership_status='CurrentCountedMember',
                    native_mesh_owner_reference_offset=owner_offset,
                    current_mesh_route={key: accepted[key] for key in (
                        'mesh_object_id', 'feature_object_id', 'component_object_id',
                        'mesh_collection_object_id', 'collection_mesh_object_ids',
                        'asset_object_id', 'asset_member', 'asset_fusion_uuid', 'name')},
                    retained_stored_mesh=None,
                    geometry_scope='Existing accepted mesh_contents row only; geometry is not duplicated or used to choose identity')
            else:
                retained = decode_retained_mesh_record(data, records, mesh_id, member, members)
                if retained['base_mesh_feature_object_id'] != identity:
                    raise ValueError('BaseMesh retained mesh feature backlink differs')
                row.update(relationship_kind='RetainedStoredMeshRoute',
                    source_membership_status=retained['retained_membership_status'],
                    native_mesh_owner_reference_offset=mesh_record.body+489,
                    current_mesh_route=None, retained_stored_mesh=retained,
                    geometry_scope='Literal retained stored asset with its serialized mesh-to-component matrix; current/world placement and temporal state unassigned')
            result['partial'].append(row)
        except (ValueError, KeyError, IndexError, TypeError, struct.error) as error:
            result['unresolved'].append(dict(feature_object_id=identity, reason=str(error)))
    return result
