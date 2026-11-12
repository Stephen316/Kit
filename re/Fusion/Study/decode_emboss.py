"""Observed planar Emboss/deboss controls and explicit profile/target inputs."""
import math
import struct

from decode_face_selections import resolve_native_faces
from decode_profile_selections import resolve_sketch_profiles
from decode_sketch import reference


EMBOSS = 'C3A9ECCE-7D25-4432-A645-3A0D9687F22A'


def decode_emboss(data, records, body, feature, features, *, profile_resolver=resolve_sketch_profiles):
    if (feature['class_guid'] != EMBOSS or len(body) < 145 or body[:4] != b'\0'*4 or body[4] not in (0, 1)
            or struct.unpack_from('<I', body, 38)[0] != 1 or body[46:50] != b'\0'*4):
        raise ValueError('Unsupported Emboss class/control prefix')
    bindings = {p['binding_object_id']: p for p in feature['parameters']}
    values, ids = {}, {}
    for offset, role, key in [(5, 'Depth', 'depth_cm'), (27, 'Horizontal Distance', 'horizontal_distance_cm'),
                              (58, 'Rotation Angle', 'rotation_angle_radians'), (80, 'Vertical Distance', 'vertical_distance_cm')]:
        identity = reference(body, offset)
        parameter = bindings.get(identity)
        if parameter is None or parameter['role'] != role or not math.isfinite(parameter['raw_float64']):
            raise ValueError('Emboss explicit parameter binding/role disagrees')
        values[key], ids[role] = parameter['raw_float64'], identity
    if values['depth_cm'] == 0:
        raise ValueError('Unobserved zero-depth Emboss')

    def counted(cursor):
        count = struct.unpack_from('<I', body, cursor)[0]
        if not 1 <= count <= 1024 or cursor+4+11*count > len(body):
            raise ValueError('Unsupported Emboss input selection count')
        identities = [reference(body, cursor+4+11*i) for i in range(count)]
        if len(set(identities)) != count:
            raise ValueError('Duplicate Emboss selections')
        return identities, cursor+4+11*count

    profile_ids, cursor = counted(91)
    if body[cursor:cursor+12] != b'\0'*12:
        raise ValueError('Unsupported Emboss input list separator')
    face_ids, cursor = counted(cursor+12)
    if len(face_ids) != 1 or reference(body, 69) != face_ids[0]:
        raise ValueError('Only observed repeated single-target Emboss face selection supported')
    profiles = [p for identity in profile_ids for p in profile_resolver(data, records, identity, feature['object_id'], features)]
    if not profiles:
        raise ValueError('Emboss profile membership unresolved')
    faces = [resolve_native_faces(data, records, identity, feature['object_id']) for identity in face_ids]
    controller_id = reference(body, 16)
    controllers = [r for r in records if r.is_primary and r.object_id == controller_id
                   and r.class_guid == '9B5B035F-5B40-4B8B-946C-34A536CC1CA0']
    if len(controllers) != 1:
        raise ValueError('Emboss result controller missing or ambiguous')
    controller = data[controllers[0].body:controllers[0].end]
    if (len(controller) != 81 or reference(controller, 2) != feature['object_id']
            or reference(controller, 70) != feature['object_id']):
        raise ValueError('Emboss controller reciprocal owners disagree')
    return dict(values, mode='Emboss' if values['depth_cm'] > 0 else 'Deboss',
                is_tangent_chain=bool(body[4]), parameter_bindings=ids,
                profiles=profiles, profile_count=len(profiles), input_faces=faces,
                result_controller_object_id=controller_id,
                uninterpreted_reference_count_field=struct.unpack_from('<I', body, 42)[0],
                uninterpreted_stored_value=struct.unpack_from('<Q', body, 50)[0],
                input_definition_end_offset=cursor,
                profile_scope='Observed individual profile sets and explicit loop/curve membership; general trimmed contours unresolved',
                target_scope='Owned face recipes and native body anchors; exact persistent face-to-ASM mapping unresolved',
                geometry_status='Planar-target control fixtures only; wrapped/spherical/cylindrical geometry, text inputs and regeneration unverified')
