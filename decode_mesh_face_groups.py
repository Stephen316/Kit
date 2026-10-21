"""Observed GenerateFaceGroups controls and ordered triangle group cache.

Temporary group IDs are stored cache values, not persistent native identities.
The owning mesh and asset are established by typed references before reading
its buffer5. No grouping algorithm or general buffer semantics are inferred.
"""
import lzma
import math
import struct
import uuid

from decode_mesh_contents import _backward_differences, _require
from decode_mesh_geometry_variants import decode_mesh_asset, decode_mesh_contents_variants
from decode_mesh_selections import decode_mesh_selection
from decode_parameters import decode_stream, read_string
from decode_sketch import reference

FACE_GROUPS = 'CA2AE956-FD81-4EBD-A601-F93A0F335722'
FLOAT_BINDING = 'D91D429C-1BB5-4640-B49F-69AF14F463E9'
PARAMETER = '7A6A3D31-BE74-4E19-9115-20642944C2E4'
SCOPE = ('Observed Fast20/80-degree minimum-size0.02 and Accurate boundary-tolerance0.001cm '
         'GenerateFaceGroups controls, owned current mesh/asset route and eight ordered cached triangle '
         'temporary group IDs. Additional asset lifecycle, persistent group identity, other buffer semantics '
         'and procedural grouping/regeneration remain unresolved.')


def _group_cache(mesh):
    geometry = mesh['geometry']
    _require(geometry['node_count'] == 6 and geometry['triangle_count'] == 8,
             'Unobserved FaceGroups cached mesh dimensions')
    block = geometry['buffers'][5]
    raw = bytes.fromhex(block['uncompressed_payload_hex'])
    _require(len(geometry['buffers']) == 6 and block['buffer_ordinal'] == 5
             and block['descriptor_hex'] == '82a15401a16401'
             and 'decompression_scope' not in block and block['uncompressed_size'] == len(raw) == 32,
             'Unobserved FaceGroups Int32 buffer5 descriptor/complete extent')
    differences = list(struct.unpack('<8i', raw))
    groups = _backward_differences(differences)
    _require(groups in (list(range(1,9)), [1]*8), 'Unobserved FaceGroups temporary-ID cache pattern')
    replay = [groups[i+1]-groups[i] for i in range(7)]+[groups[-1]]
    _require(replay == differences and struct.pack('<8i', *replay) == raw,
             'FaceGroups temporary-ID byte replay disagrees')
    return dict(asset_object_id=mesh['asset_object_id'], asset_member=mesh['asset_member'],
        asset_fusion_uuid=mesh['asset_fusion_uuid'], buffer_ordinal=5,
        buffer_asset_offset=block['asset_offset'], stored_descriptor_hex=block['descriptor_hex'],
        stored_payload_hex=raw.hex(), stored_int32_forward_differences=differences,
        decoded_triangle_face_group_temporary_ids=groups, distinct_temporary_id_count=len(set(groups)),
        triangle_order='Stored triangle_node_indices triples; equality with actual API order corroborated in focused captures',
        encoding='SignedInt32 forward differences and final absolute value, integrated backward',
        identity_scope='Temporary group labels only; no persistent native face/group identity or lifecycle')


def decode_mesh_face_groups(data, records, features, member, members, mesh_contents=None):
    """Return decoded/unresolved/scope; success rows feature_object_id/kind/name/settings."""
    records = list(records)
    result = dict(decoded=[], unresolved=[], scope=SCOPE)
    targets = [r for r in records if r.is_primary and r.class_guid == FACE_GROUPS]
    if not targets:
        return result
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    def typed(identity, guid):
        rows = grouped.get(identity, [])
        _require(len(rows) == 1 and rows[0].class_guid == guid,
                 'FaceGroups typed reference missing/ambiguous/wrong class')
        r = rows[0]
        return r, data[r.body:r.end]
    named = {f['object_id']:f for f in features}
    parameters, _ = decode_stream(data, records)
    meshes = mesh_contents if mesh_contents is not None else decode_mesh_contents_variants(data, records, member, members)
    for record in targets:
        try:
            typed(record.object_id, FACE_GROUPS)
            owner, feature = record.object_id, named.get(record.object_id)
            _require(feature is not None and feature['class_guid'] == FACE_GROUPS
                     and feature['record_offset'] == record.start and feature.get('native_kind_label') == 'GenerateFaceGroups',
                     'FaceGroups discovery class/offset/label disagrees')
            body = data[record.body:record.end]
            _require(body[:2] == bytes(2) and body[61:65] == bytes(4) and body[76] == 0,
                     'Unobserved FaceGroups prefix/separators')
            method = struct.unpack_from('<I', body, 35)[0]
            _require(method in (0,1), 'Unobserved FaceGroups method')
            binding_ids = {role:reference(body,offset) for role,offset in
                (('Angle Threshold',2),('Boundary Tolerance',13),('Minimum Face Group Size',24))}
            _require(len(set(binding_ids.values())) == 3, 'FaceGroups scalar roles share a binding')
            scalars = {}
            for role, binding_id in binding_ids.items():
                _, payload = typed(binding_id, FLOAT_BINDING)
                _require(len(payload) == 85 and payload[:6] == bytes.fromhex('010100000001')
                         and all(reference(payload,i) == owner for i in (5,48,74)),
                         'FaceGroups scalar binding owner/framing mismatch: '+role)
                parameter_id = reference(payload,29)
                parameter, _ = typed(parameter_id,PARAMETER)
                value = struct.unpack_from('<d',payload,21)[0]
                parsed = [p for p in parameters if p['role'] == role
                          and p.get('declared_binding_object_id') == binding_id
                          and parameter.body <= p['role_offset'] < parameter.end]
                attached = [p for p in feature['parameters'] if p['role'] == role
                            and p.get('binding_object_id') == binding_id]
                _require(len(parsed) == len(attached) == 1 and math.isfinite(value)
                         and parsed[0]['raw_float64'] == attached[0]['raw_float64'] == value
                         and attached[0].get('parameter_object_id') == parameter_id,
                         'FaceGroups parameter/binding/value copies disagree: '+role)
                units = {'Angle Threshold':'deg','Boundary Tolerance':'mm','Minimum Face Group Size':''}[role]
                _require(parsed[0]['display_units'] == units, 'Unobserved FaceGroups units: '+role)
                scalars[role] = dict(binding_object_id=binding_id, parameter_object_id=parameter_id,
                    parameter_name=parsed[0]['parameter_name'], stored_value=value, display_units=units,
                    is_active=(role != 'Boundary Tolerance' if method == 0 else role == 'Boundary Tolerance'))
            values = {key:value['stored_value'] for key,value in scalars.items()}
            expected_angles = (math.radians(20),math.radians(80)) if method == 0 else (math.radians(25),)
            _require(values['Angle Threshold'] in expected_angles and values['Boundary Tolerance'] == 0.001
                     and values['Minimum Face Group Size'] == 0.02, 'Unobserved FaceGroups active/inactive scalar combination')
            asset_id, additional_id = reference(body,39), reference(body,50)
            _require(asset_id != additional_id, 'FaceGroups stored asset slots alias')
            selection_id = reference(body,65)
            selection = decode_mesh_selection(data,records,selection_id,owner)
            nil, cursor = read_string(body,77)
            _require(nil == str(uuid.UUID(int=0)) and cursor == 153 and body[153:156] == bytes(3)
                     and struct.unpack_from('<I',body,156)[0] == 5, 'FaceGroups namespace/dependency framing disagrees')
            repeated = [reference(body,160+i*11) for i in range(5)]
            _require(repeated == [selection_id,selection['descriptor_object_id']]+list(binding_ids.values())
                     and body[215:219] == b'\xff'*4, 'FaceGroups repeated dependencies disagree')
            label, cursor = read_string(body,219)
            index = struct.unpack_from('<Q',body,cursor)[0]
            name, tail = read_string(body,cursor+8)
            _require(label == 'GenerateFaceGroups' and index == feature['stored_index']
                     and name == feature['name'] and len(body)-tail == 66,
                     'FaceGroups counted metadata/footer disagrees')
            matching = [m for m in meshes['decoded'] if m['mesh_object_id'] == selection['mesh_object_id']]
            _require(len(matching) == 1 and matching[0]['asset_object_id'] == asset_id,
                     'FaceGroups selected mesh current asset route unresolved')
            mesh = matching[0]
            current = decode_mesh_asset(data,records,asset_id,member,members)
            additional = decode_mesh_asset(data,records,additional_id,member,members)
            _require(current['asset_member'] == mesh['asset_member'], 'FaceGroups current same-asset filename disagrees')
            settings = dict(method={0:'Fast',1:'Accurate'}[method], stored_method_code=method,
                scalar_bindings=scalars, angle_threshold_radians=values['Angle Threshold'] if method == 0 else None,
                minimum_face_group_size=values['Minimum Face Group Size'] if method == 0 else None,
                boundary_tolerance_cm=values['Boundary Tolerance'] if method == 1 else None,
                inactive_control_scope='Native values retained but inactive controls are not promoted to active API settings',
                input_selection=selection, native_mesh_object_id=mesh['mesh_object_id'], mesh_name=mesh['name'],
                component_object_id=mesh['component_object_id'], current_mesh_native_feature_owner_object_id=mesh['feature_object_id'],
                current_mesh_native_owner_class_guid=mesh['native_feature_class_guid'],
                owner_scope='Typed selection/current asset agree; independent BaseMesh owner retained, not reassigned to GenerateFaceGroups',
                current_mesh_asset=current, additional_stored_asset=additional, additional_asset_temporal_role=None,
                asset_scope='Explicit assets39/50; first independently agrees with current native mesh. Additional slot has no general temporal role',
                triangle_face_groups=_group_cache(mesh), repeated_dependency_object_ids=repeated,
                stored_shared_footer_hex=body[tail:].hex(),
                regeneration_scope='Stored controls and cache only; grouping algorithm and regeneration unresolved')
            result['decoded'].append(dict(feature_object_id=owner,kind='MeshGenerateFaceGroups',name=name,settings=settings))
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error, TypeError, lzma.LZMAError) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=FACE_GROUPS,reason=str(error)))
    return result
