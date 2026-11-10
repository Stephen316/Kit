"""Observed MeshRemesh EdgeLength controls and typed selected/current mesh assets.

Requested lengths do not constitute a recreated algorithm or universal edge-size
bound. Additional stored assets remain temporally unqualified.
"""
import math
import struct
import uuid

from decode_mesh_geometry_variants import decode_mesh_asset, decode_mesh_contents_variants
from decode_mesh_selections import decode_mesh_selection
from decode_parameters import decode_stream, read_string
from decode_sketch import reference

REMESH = '828DDA62-2750-447D-8728-06C9B7C2B117'
FLOAT_BINDING = 'D91D429C-1BB5-4640-B49F-69AF14F463E9'
PARAMETER = '7A6A3D31-BE74-4E19-9115-20642944C2E4'
SCOPE = ('Observed Adaptive EdgeLength2/1.5cm and Uniform EdgeLength2cm controls, optional Adaptive '
         'Shape Preservation0.5, owned mesh selection and typed current/additional asset references. '
         'Preservation flags, additional asset lifecycle, general target attainment and procedural remeshing remain unresolved')


def decode_mesh_remesh(data, records, features, member, members, mesh_contents=None):
    """Return decoded/unresolved/scope; rows have feature_object_id/kind/name/settings."""
    records = list(records)
    candidates = [r for r in records if r.is_primary and r.class_guid == REMESH]
    result = dict(decoded=[], unresolved=[], scope=SCOPE)
    if not candidates:
        return result
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    def typed(identity, guid):
        rows = grouped.get(identity, [])
        if len(rows) != 1 or rows[0].class_guid != guid:
            raise ValueError('MeshRemesh typed reference missing/ambiguous/wrong class')
        record = rows[0]
        return record, data[record.body:record.end]
    named = {f['object_id']:f for f in features}
    parameters, _ = decode_stream(data, records)
    meshes = mesh_contents if mesh_contents is not None else decode_mesh_contents_variants(data, records, member, members)
    for record in candidates:
        try:
            typed(record.object_id, REMESH)
            owner, feature = record.object_id, named.get(record.object_id)
            if feature is None or feature['class_guid'] != REMESH or feature['record_offset'] != record.start:
                raise ValueError('MeshRemesh feature metadata absent/stale')
            body = data[record.body:record.end]
            if body[:4] != bytes(4):
                raise ValueError('Unobserved MeshRemesh native prefix/preservation literal')
            method = struct.unpack_from('<I', body, 4)[0]
            if method not in (0, 1) or body[8] != (1 if method == 0 else 0):
                raise ValueError('Unobserved MeshRemesh method/optional Adaptive binding layout')
            binding_ids = {}
            cursor = 8
            if method == 0:
                binding_ids['Shape Preservation'] = reference(body, cursor)
                cursor += 11
            else:
                cursor += 1
            if body[cursor] != 0:
                raise ValueError('MeshRemesh optional parameter separator mismatch')
            cursor += 1
            binding_ids['Target Edge Length'] = reference(body, cursor)
            cursor += 11
            target = struct.unpack_from('<I', body, cursor)[0]
            if target != 1:
                raise ValueError('Only captured MeshRemesh EdgeLength target is supported')
            cursor += 4
            asset_offset = cursor
            current_id, additional_id = reference(body, cursor), reference(body, cursor+11)
            cursor += 22
            if current_id == additional_id or body[cursor:cursor+4] != bytes(4):
                raise ValueError('MeshRemesh two asset references alias or separator differs')
            cursor += 4
            selection_id = reference(body, cursor)
            cursor += 11
            if body[cursor] != 0:
                raise ValueError('MeshRemesh selection/UUID separator mismatch')
            cursor += 1
            nil, cursor = read_string(body, cursor)
            if nil != str(uuid.UUID(int=0)) or body[cursor:cursor+3] != bytes(3):
                raise ValueError('MeshRemesh nil UUID/dependency separator mismatch')
            cursor += 3
            count = struct.unpack_from('<I', body, cursor)[0]
            cursor += 4
            if count != 2+len(binding_ids):
                raise ValueError('MeshRemesh repeated dependency count mismatch')
            repeated = [reference(body, cursor+11*i) for i in range(count)]
            cursor += 11*count
            selection = decode_mesh_selection(data, records, selection_id, owner)
            if repeated != [selection_id,selection['descriptor_object_id']]+list(binding_ids.values()):
                raise ValueError('MeshRemesh repeated selection/parameter dependencies disagree')
            if body[cursor:cursor+4] != b'\xff'*4:
                raise ValueError('MeshRemesh feature label marker mismatch')
            label, end = read_string(body, cursor+4)
            index = struct.unpack_from('<Q', body, end)[0]
            name, tail = read_string(body, end+8)
            if label != 'MeshRemesh' or index != feature['stored_index'] or name != feature.get('name') or len(body)-tail != 66:
                raise ValueError('MeshRemesh label/index/name/footer framing mismatch')
            if len(set(binding_ids.values())) != len(binding_ids):
                raise ValueError('MeshRemesh roles share a binding')
            scalar_rows = {}
            for role, identity in binding_ids.items():
                binding, payload = typed(identity, FLOAT_BINDING)
                if (len(payload) != 85 or payload[:6] != bytes.fromhex('010100000001')
                        or any(reference(payload, offset) != owner for offset in (5,48,74))):
                    raise ValueError('MeshRemesh scalar binding owner/framing mismatch: '+role)
                parameter_id = reference(payload, 29)
                parameter, _ = typed(parameter_id, PARAMETER)
                value = struct.unpack_from('<d', payload, 21)[0]
                parsed = [p for p in parameters if p['role'] == role and p.get('declared_binding_object_id') == identity
                          and parameter.body <= p['role_offset'] < parameter.end]
                attached = [p for p in feature['parameters'] if p['role'] == role and p.get('binding_object_id') == identity]
                if (len(parsed) != 1 or len(attached) != 1 or not math.isfinite(value)
                        or parsed[0]['raw_float64'] != value or attached[0]['raw_float64'] != value
                        or attached[0].get('parameter_object_id') != parameter_id):
                    raise ValueError('MeshRemesh role/parameter/binding numeric copies disagree: '+role)
                expected_units = '' if role == 'Shape Preservation' else 'mm'
                if parsed[0]['display_units'] != expected_units:
                    raise ValueError('Uncaptured MeshRemesh parameter units: '+role)
                scalar_rows[role] = dict(binding_object_id=identity,parameter_object_id=parameter_id,
                    parameter_name=parsed[0]['parameter_name'],stored_value=value,display_units=expected_units,
                    value_representation='float64',is_active=True)
            edge = scalar_rows['Target Edge Length']['stored_value']
            if (edge not in (1.5,2.0) or method == 1 and edge != 2.0
                    or method == 0 and scalar_rows['Shape Preservation']['stored_value'] != 0.5):
                raise ValueError('Uncaptured MeshRemesh parameter values/method combination')
            matches = [m for m in meshes['decoded'] if m['mesh_object_id'] == selection['mesh_object_id']]
            if len(matches) != 1 or matches[0]['asset_object_id'] != current_id:
                raise ValueError('MeshRemesh selected mesh lacks one qualified current asset route')
            mesh = matches[0]
            current_asset = decode_mesh_asset(data, records, current_id, member, members)
            additional_asset = decode_mesh_asset(data, records, additional_id, member, members)
            if current_asset['asset_member'] != mesh['asset_member']:
                raise ValueError('MeshRemesh current asset same-asset filename route disagrees')
            geometry = mesh['geometry']
            expected_counts = (16,28) if edge == 1.5 else (9,14)
            if (geometry['node_count'],geometry['triangle_count']) != expected_counts:
                raise ValueError('Uncaptured MeshRemesh current cached geometry counts')
            settings = dict(method={0:'Adaptive',1:'Uniform'}[method],target_type='EdgeLength',
                stored_method_code=method,stored_target_code=target,
                requested_edge_length_cm=edge,scalar_bindings=scalar_rows,
                shape_preservation=(scalar_rows['Shape Preservation']['stored_value'] if method == 0 else None),
                shape_preservation_status=('Explicit owned Adaptive parameter' if method == 0 else 'Optional parameter absent in captured Uniform layout'),
                preservation_literal_bytes_2_4_hex=body[2:4].hex(),
                preserve_sharp_edges=None,preserve_boundaries=None,
                preservation_scope='Both actual API getters are false in all captures; two stored zero bytes lack independent role/true contrasts',
                input_selection=selection,native_mesh_object_id=selection['mesh_object_id'],mesh_name=mesh['name'],
                component_object_id=mesh['component_object_id'],mesh_collection_object_id=mesh['mesh_collection_object_id'],
                current_mesh_native_feature_owner_object_id=mesh['feature_object_id'],
                current_mesh_native_owner_class_guid=mesh['native_feature_class_guid'],mesh_remesh_owns_current_mesh=None,
                owner_scope='Typed input selection/current asset and independently decoded mesh owner; Remesh is not promoted to current mesh owner or API baseOrFormFeature',
                stored_current_asset_field_relative_offset=asset_offset,current_mesh_asset=current_asset,
                stored_additional_asset_field_relative_offset=asset_offset+11,additional_stored_asset=additional_asset,
                additional_asset_temporal_role=None,
                asset_scope='Typed current asset independently agrees with selected native mesh. Additional asset buffers remain separate without a historical/source lifecycle assignment',
                current_cache_node_count=geometry['node_count'],current_cache_triangle_count=geometry['triangle_count'],
                requested_edge_length_target_attained=None,
                target_scope='Stored request and current arrays/counts only; no universal edge-length bound, remeshing algorithm or target attainment inferred',
                repeated_dependency_object_ids=repeated)
            result['decoded'].append(dict(feature_object_id=owner,kind='MeshRemesh',name=name,settings=settings))
        except (ValueError,KeyError,IndexError,UnicodeError,struct.error,TypeError) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=REMESH,reason=str(error)))
    return result
