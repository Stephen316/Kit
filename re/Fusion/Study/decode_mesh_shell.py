"""Observed MeshShell scalar control and typed mesh/asset provenance, not an algorithm."""
import math
import struct
import uuid

from decode_mesh_geometry_variants import decode_mesh_asset, decode_mesh_contents_variants
from decode_mesh_selections import decode_mesh_selection
from decode_parameters import decode_stream, read_string
from decode_sketch import reference

SHELL = '1514CDB8-BB81-4895-A953-7B12F4504F99'
FLOAT_BINDING = 'D91D429C-1BB5-4640-B49F-69AF14F463E9'
PARAMETER = '7A6A3D31-BE74-4E19-9115-20642944C2E4'
SCOPE = ('Observed Thickness0.1/0.2cm owned parameter, typed input mesh and current/additional '
         'asset routes. Stored arrays/counts are cache evidence; shelling algorithm, general values, additional '
         'asset lifecycle and regeneration remain unresolved')


def decode_mesh_shell(data, records, features, member, members, mesh_contents=None):
    """Return decoded/unresolved/scope; rows have feature_object_id/kind/name/settings."""
    records = list(records)
    candidates = [r for r in records if r.is_primary and r.class_guid == SHELL]
    result = dict(decoded=[],unresolved=[],scope=SCOPE)
    if not candidates:
        return result
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        matches = grouped.get(identity,[])
        if len(matches) != 1 or matches[0].class_guid != guid:
            raise ValueError('MeshShell typed reference missing/ambiguous/wrong class')
        record = matches[0]
        return record,data[record.body:record.end]
    named = {f['object_id']:f for f in features}
    parameters,_ = decode_stream(data,records)
    meshes = mesh_contents if mesh_contents is not None else decode_mesh_contents_variants(data,records,member,members)
    for record in candidates:
        try:
            typed(record.object_id,SHELL)
            owner,feature = record.object_id,named.get(record.object_id)
            if feature is None or feature['class_guid'] != SHELL or feature['record_offset'] != record.start:
                raise ValueError('MeshShell feature metadata absent/stale')
            body = data[record.body:record.end]
            if body[:2] != bytes(2) or body[35:39] != bytes(4) or body[50] != 0:
                raise ValueError('Unobserved MeshShell prefix/separators')
            binding_id = reference(body,2)
            current_id,additional_id = reference(body,13),reference(body,24)
            if current_id == additional_id:
                raise ValueError('MeshShell two stored assets unexpectedly alias')
            selection_id = reference(body,39)
            selection = decode_mesh_selection(data,records,selection_id,owner)
            nil,cursor = read_string(body,51)
            if (nil != str(uuid.UUID(int=0)) or cursor != 127 or body[cursor:cursor+3] != bytes(3)
                    or struct.unpack_from('<I',body,130)[0] != 3):
                raise ValueError('MeshShell nil UUID/repeated dependency framing mismatch')
            repeated = [reference(body,134+11*i) for i in range(3)]
            if repeated != [selection_id,selection['descriptor_object_id'],binding_id]:
                raise ValueError('MeshShell repeated selection/parameter references disagree')
            if body[167:171] != b'\xff'*4:
                raise ValueError('MeshShell label marker mismatch')
            label,cursor = read_string(body,171)
            index = struct.unpack_from('<Q',body,cursor)[0]
            name,tail = read_string(body,cursor+8)
            if label != 'MeshShell' or index != feature['stored_index'] or name != feature.get('name') or len(body)-tail != 66:
                raise ValueError('MeshShell counted label/index/name/footer framing mismatch')
            _,payload = typed(binding_id,FLOAT_BINDING)
            if (len(payload) != 85 or payload[:6] != bytes.fromhex('010100000001')
                    or any(reference(payload,offset) != owner for offset in (5,48,74))):
                raise ValueError('MeshShell scalar binding owner/framing mismatch')
            parameter_id = reference(payload,29)
            parameter,_ = typed(parameter_id,PARAMETER)
            value = struct.unpack_from('<d',payload,21)[0]
            parsed = [p for p in parameters if p['role'] == 'Thickness' and p.get('declared_binding_object_id') == binding_id
                      and parameter.body <= p['role_offset'] < parameter.end]
            attached = [p for p in feature['parameters'] if p['role'] == 'Thickness' and p.get('binding_object_id') == binding_id]
            if (len(parsed) != 1 or len(attached) != 1 or not math.isfinite(value)
                    or parsed[0]['raw_float64'] != value or attached[0]['raw_float64'] != value
                    or attached[0].get('parameter_object_id') != parameter_id):
                raise ValueError('MeshShell role/parameter/binding numeric copies disagree')
            if value not in (0.1,0.2) or parsed[0]['display_units'] != 'mm':
                raise ValueError('Uncaptured MeshShell value or units')
            matches = [m for m in meshes['decoded'] if m['mesh_object_id'] == selection['mesh_object_id']]
            if len(matches) != 1 or matches[0]['asset_object_id'] != current_id:
                raise ValueError('MeshShell selected mesh lacks one qualified current asset route')
            mesh = matches[0]
            current_asset = decode_mesh_asset(data,records,current_id,member,members)
            additional_asset = decode_mesh_asset(data,records,additional_id,member,members)
            if current_asset['asset_member'] != mesh['asset_member']:
                raise ValueError('MeshShell current asset same-asset filename route disagrees')
            geometry = mesh['geometry']
            counts = (geometry['node_count'],geometry['triangle_count'])
            allowed_counts = ((2745,5481),(2745,5482)) if value == 0.1 else ((1556,3103),)
            if counts not in allowed_counts:
                raise ValueError('Uncaptured MeshShell current cache counts')
            settings = dict(thickness_cm=value,scalar_binding=dict(role='Thickness',binding_object_id=binding_id,
                    parameter_object_id=parameter_id,parameter_name=parsed[0]['parameter_name'],
                    stored_value=value,display_units='mm',value_representation='float64'),
                input_selection=selection,native_mesh_object_id=selection['mesh_object_id'],mesh_name=mesh['name'],
                component_object_id=mesh['component_object_id'],mesh_collection_object_id=mesh['mesh_collection_object_id'],
                current_mesh_native_feature_owner_object_id=mesh['feature_object_id'],
                current_mesh_native_owner_class_guid=mesh['native_feature_class_guid'],mesh_shell_owns_current_mesh=None,
                owner_scope='Typed selected mesh/current asset and independently decoded native owner; Shell feature is not promoted to current mesh owner or API baseOrFormFeature',
                stored_current_asset_field_relative_offset=13,current_mesh_asset=current_asset,
                stored_additional_asset_field_relative_offset=24,additional_stored_asset=additional_asset,
                additional_asset_temporal_role=None,
                asset_scope='Current asset independently agrees with selected native mesh; additional typed asset exact buffers retained without historical/source lifecycle assignment',
                current_cache_node_count=geometry['node_count'],current_cache_triangle_count=geometry['triangle_count'],
                current_cache_is_closed=geometry['derived_closed_oriented_edge_incidence'],
                algorithm_status='Not reconstructed; thickness and current geometry are separately decoded stored controls/caches',
                repeated_dependency_object_ids=repeated)
            result['decoded'].append(dict(feature_object_id=owner,kind='MeshShell',name=name,settings=settings))
        except (ValueError,KeyError,IndexError,UnicodeError,struct.error,TypeError) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=SHELL,reason=str(error)))
    return result
