"""Observed Move definitions, explicit parameter roles and cached rigid transforms."""
import math
import struct

from decode_extrude import optional_reference
from decode_placement import rigid_matrix
from decode_selection import resolve_native_selection
from decode_sketch import numbers, reference


FEATURE = '64E40C8E-E564-469C-8690-5C4E77C1B02C'
CONTROL = '84E6245F-1CDC-4FB8-8048-163A85FAD3F0'


def decode_move(data, records, body, feature, known, features):
    if feature['class_guid'] != FEATURE or body[:2] != b'\0\0':
        raise ValueError('Unsupported Move feature class/prefix')
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Move typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    backend_id = reference(body, 2)
    _, payload = typed(backend_id, CONTROL)
    if payload[:12] != b'\0'*12:
        raise ValueError('Unsupported Move backend prefix')
    cursor, header_slots = 12, []
    for _ in range(8):
        identity, cursor = optional_reference(payload, cursor)
        header_slots.append(identity)
    subtype, code = struct.unpack_from('<II', payload, cursor)
    if code not in (0, 1, 2, 5, 6) or (code != 0 and subtype != 0) or subtype not in (0, 1, 2) or payload[cursor+8] != 0:
        raise ValueError('Unsupported Move definition/subtype')
    matrix_offset = cursor+9
    matrix = rigid_matrix(numbers(payload, matrix_offset, 16))
    cursor = matrix_offset+128
    matrix_suffix = payload[cursor:cursor+6]
    if (len(matrix_suffix) != 6 or matrix_suffix[:2] != bytes(2)
            or matrix_suffix[3:] != bytes(3) or matrix_suffix[2] not in (0, 1)
            or (code != 6 and matrix_suffix[2] != 1)):
        raise ValueError('Unsupported Move matrix suffix')
    selected_point_id, cursor = optional_reference(payload, cursor+6)
    if reference(payload, cursor) != feature['object_id']:
        raise ValueError('Move backend feature owner disagrees')
    cursor += 11
    slots = []
    for _ in range(9):
        identity, cursor = optional_reference(payload, cursor)
        slots.append(identity)
    if (len(payload)-cursor != 53 or payload[cursor:cursor+4] != b'\1\1\0\0'
            or payload[cursor+12:cursor+16] != b'\1\1\0\0'
            or payload[cursor+27:cursor+30] != b'\1\0\0' or payload[cursor+41] != 0
            or reference(payload, cursor+42) != feature['object_id']):
        raise ValueError('Unsupported Move footer or reciprocal owner')
    helper_id, support_id = reference(payload, cursor+16), reference(payload, cursor+30)
    typed(helper_id, '5FBE538E-139B-46D4-BCAF-CC796D1E1F78')
    typed(support_id, '6CCF41D5-40BE-48ED-A834-18F3EAED6C57')
    cached_scalar = numbers(payload, cursor+4, 1)[0]
    bindings = {p['binding_object_id']: p for p in feature['parameters']}

    def parameter(identity, role):
        parameter = bindings.get(identity)
        if parameter is None or parameter['role'] != role or not math.isfinite(parameter['raw_float64']):
            raise ValueError('Move explicit parameter binding/role disagrees: '+role)
        return parameter['raw_float64']

    def linear_entity(identity):
        _, entity = typed(identity, 'F2A7590D-6654-4674-B393-A2AEF4FEC48A')
        if (len(entity) != 202 or entity[:6] != bytes.fromhex('000008000000')
                or struct.unpack_from('<I', entity, 99)[0] != 1
                or reference(entity, 191) != feature['object_id']):
            raise ValueError('Unsupported Move linear entity selection/owner')
        native = resolve_native_selection(data, records, identity, known)
        if native is not None:
            if native['entity']['kind'] != 'ConstructionAxis':
                raise ValueError('Move linear reference resolves outside observed axis layout')
            return native
        descriptor_id = reference(entity, 103)
        _, descriptor = typed(descriptor_id, '5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
        if len(descriptor) != 263 or descriptor[:2] != b'\0\0' or reference(descriptor, 252) != feature['object_id']:
            raise ValueError('Unsupported Move sketch-line descriptor')
        terminal_id = reference(descriptor, 2)
        _, terminal = typed(terminal_id, 'E2CEFD18-D755-4E09-8E7F-953A2F6D43F8')
        if len(terminal) != 26 or terminal[:10] != b'\0'*10:
            raise ValueError('Unsupported Move sketch-line terminal')
        sketch_id, tag = struct.unpack_from('<QQ', terminal, 10)
        matches = [(f, g) for f in features if f['kind'] == 'Sketch' and f['sketch_object_id'] == sketch_id
                   for g in f['geometry'] if g['kind'] == 'Line' and g['entity_tag'] == tag]
        if len(matches) != 1:
            raise ValueError('Move sketch-line identity unresolved or ambiguous')
        return {'selection_object_id': identity, 'descriptor_object_id': descriptor_id,
                'terminal_object_id': terminal_id, 'entity': {'kind': 'SketchLine', 'sketch_object_id': sketch_id,
                    'sketch_name': matches[0][0]['name'], 'object_id': matches[0][1]['object_id'], 'entity_tag': tag},
                'association': 'Explicit owned linear selection -> descriptor -> sketch ID and curve tag'}

    def construction_point(identity):
        _, selected = typed(identity, '69EE2FA7-BCC7-449E-9CA9-976CEFDFED44')
        if len(selected) != 178 or reference(selected, len(selected)-11) != feature['object_id']:
            raise ValueError('Unsupported Move point selection/owner')
        resolved = resolve_native_selection(data, records, identity, known)
        if resolved is None or resolved['entity']['kind'] != 'ConstructionPoint':
            raise ValueError('Move construction point identity unresolved')
        return resolved

    result = {'transform': matrix, 'matrix_order': 'row-major; column-vector multiplication',
              'translation_units': 'cm', 'transform_record_object_id': backend_id,
              'stored_definition_code': code, 'stored_translation_subtype': subtype,
              'helper_record_object_id': helper_id, 'support_record_object_id': support_id,
              'uninterpreted_cached_scalar': cached_scalar,
              'transform_scope': 'Stored rigid transform in native feature context; existing body caches already include the move',
              'geometry_status': 'Observed definitions, bindings and selected inputs; no body regeneration or general occurrence transform replay'}
    active_slots = set()
    if code in (0, 1, 5) and any(identity is not None for identity in header_slots):
        raise ValueError('Unobserved Move context header variant')
    if code != 6 and selected_point_id is not None:
        raise ValueError('Unexpected Move selected-point field')
    if code == 5:
        result['definition'] = 'FreeMove'
    elif code == 0 and subtype in (0, 1):
        result.update(definition='TranslateXYZ', is_design_space=subtype == 1,
                      x_distance_cm=parameter(slots[6], 'TranslateX'), y_distance_cm=parameter(slots[7], 'TranslateY'),
                      z_distance_cm=parameter(slots[8], 'TranslateZ'))
        active_slots = {6, 7, 8}
    elif code == 0 and subtype == 2:
        result.update(definition='TranslateAlongEntity', distance_cm=parameter(slots[4], 'TranslateDistance'),
                      linear_entity=linear_entity(slots[3]))
        active_slots = {3, 4}
    elif code == 1:
        result.update(definition='Rotate', angle_radians=parameter(slots[0], 'RotateAngle'), axis_entity=linear_entity(slots[1]))
        active_slots = {0, 1}
    elif code == 2:
        if any(header_slots[index] is None for index in (0, 1, 2, 7)) or any(header_slots[index] is not None for index in (3, 4, 5, 6)):
            raise ValueError('Unobserved point-to-point context header')
        resolved = []
        for index in (1, 2):
            _, selected = typed(header_slots[index], '7B6C3C2D-4096-4E6D-B225-699E8C2D9355')
            if len(selected) not in (204, 332) or reference(selected, len(selected)-11) != feature['object_id']:
                raise ValueError('Unsupported Move point relationship/owner')
            point_id = reference(selected, len(selected)-129)
            if reference(selected, len(selected)-99) != point_id:
                raise ValueError('Move point relationship repeated references disagree')
            resolved.append(construction_point(point_id))
        result.update(definition='PointToPoint', origin_point=resolved[0], target_point=resolved[1])
    elif code == 6:
        is_design_space = bool(matrix_suffix[2])
        if (is_design_space != (header_slots[0] is not None)
                or any(identity is not None for identity in header_slots[1:])):
            raise ValueError('Unobserved point-to-position context header')
        result.update(definition='PointToPosition', point=construction_point(selected_point_id),
                      x_distance_cm=parameter(slots[6], 'PositionX'), y_distance_cm=parameter(slots[7], 'PositionY'),
                      z_distance_cm=parameter(slots[8], 'PositionZ'), is_design_space=is_design_space,
                      coordinate_status='Observed point-to-position coordinate flag and optional frame presence agree with paired API controls')
        active_slots = {6, 7, 8}
    if any(identity is not None for index, identity in enumerate(slots) if index not in active_slots):
        raise ValueError('Unexpected active Move parameter/entity slots')
    for index, identity in enumerate(header_slots):
        if identity is None:
            continue
        if index in (0, 7):
            _, frame = typed(identity, '2E3AC990-483D-4A55-8662-C064B976A957')
            if len(frame) != 68 or reference(frame, 40) != feature['object_id']:
                raise ValueError('Move point context frame owner disagrees')
    result['stored_header_reference_slots'] = header_slots
    return result
