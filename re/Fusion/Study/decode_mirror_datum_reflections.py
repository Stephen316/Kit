"""Typed datum Mirror membership and a bounded orientation-reversing cache map.

The reflection matrix is computed from the selected native origin plane, not
read as a stored matrix. It is checked against independently owned output data.
Combine/stitch controls and general feature/history regeneration stay unknown.
"""

import math
import struct

from decode_dependencies import decode_dependencies
from decode_mirror_datum_outputs import decode_mirror_datum_outputs
from decode_remaining_body_inputs import MIRROR_DATUM, _access
from decode_selection import known_construction_entities
from decode_sketch import reference, same


def reflection_matrix(origin, normal):
    if (len(origin) != 3 or len(normal) != 3 or not all(math.isfinite(v) for v in origin+normal)
            or not math.isclose(sum(v*v for v in normal), 1., abs_tol=1e-10)):
        raise ValueError('Datum reflection requires a finite origin and unit normal')
    offset = sum(a*b for a, b in zip(origin, normal))
    matrix = []
    for row in range(3):
        matrix.extend(float(row == col)-2*normal[row]*normal[col] for col in range(3))
        matrix.append(2*offset*normal[row])
    return matrix+[0., 0., 0., 1.]


def decode_mirror_datum_reflections(data, records, features, assembly):
    """Return scoped provenance and computed/cache corroboration, without mutation."""
    primary, typed = _access(data, records)
    known = known_construction_entities(data, records, features)
    result = {'decoded': [], 'unresolved': [],
              'scope': 'Owned construction-plane Mirror inputs/outputs and same-component reflected cache frames; unavailable controls, occurrence solving and general regeneration remain unresolved'}
    for feature in features:
        if feature['class_guid'] != MIRROR_DATUM:
            continue
        try:
            record, body = typed(feature['object_id'], MIRROR_DATUM)
            if record.start != feature['record_offset']:
                raise ValueError('Datum reflection feature record identity disagrees')
            provenance = decode_mirror_datum_outputs(data, records, body, feature, known)
            source, output = provenance['source_plane'], provenance['output_plane']
            collection_id = source['scope_reference_object_id']
            if output['scope_reference_object_id'] != collection_id:
                raise ValueError('Datum Mirror source/output collections disagree')
            _, collection = typed(collection_id, 'A8635B5F-1E2C-45FD-8BA9-0173B0FEB75E')
            count = struct.unpack_from('<I', collection, 2)[0]
            if collection[:2] != bytes(2) or count != 2 or len(collection) != 51+22*count:
                raise ValueError('Unobserved datum Mirror two-plane collection framing')
            members = [reference(collection, 6+11*i) for i in range(count)]
            repeated = len(collection)-15-11*count
            if (len(set(members)) != count or struct.unpack_from('<I', collection, repeated)[0] != count
                    or [reference(collection, repeated+4+11*i) for i in range(count)] != members
                    or set(members) != {source['native_plane_object_id'], output['native_plane_object_id']}):
                raise ValueError('Datum Mirror repeated source/output plane membership disagrees')
            component_id = reference(collection, len(collection)-11)
            typed(component_id, 'E03784ED-5E19-4E14-B9F2-3B07017018CD')
            for plane in (source, output):
                _, chunk = typed(plane['native_plane_object_id'], plane['class_guid'])
                if reference(chunk, len(chunk)-11) != collection_id:
                    raise ValueError('Datum Mirror plane/collection backlink disagrees')
            selected = provenance['mirror_plane']['entity']
            origin_id = selected.get('origin_container_object_id')
            if selected['kind'] != 'ConstructionPlane' or origin_id is None:
                raise ValueError('Datum Mirror reflection requires a typed component origin plane')
            _, container = typed(origin_id, '2972A3B8-3627-49BC-8C3D-18707605EC44')
            origin_count = struct.unpack_from('<I', container, 4)[0]
            if (container[:4] != bytes(4) or origin_count != 7 or len(container) != 19+11*origin_count
                    or reference(container, len(container)-11) != component_id
                    or [reference(container, 8+11*i) for i in range(origin_count)].count(selected['object_id']) != 1):
                raise ValueError('Datum Mirror selected plane and datum collection component ownership disagree')
            # Re-read paired native dependencies into fresh minimal feature rows;
            # preexisting feature annotations cannot establish this scope proof.
            owners = [{'object_id': identity} for identity in (feature['object_id'], source['owner_feature_object_id'])]
            decode_dependencies(data, records, owners, assembly)
            if any(owner.get('component_object_id') != component_id or 'component_scope_object_id' not in owner for owner in owners):
                raise ValueError('Datum Mirror source/feature native dependency scopes disagree')
            matrix = reflection_matrix(selected['origin_cm'], selected['normal'])
            source_matrix = source['cached_plane_to_component_matrix']
            computed = [sum(matrix[4*r+k]*source_matrix[4*k+c] for k in range(4)) for r in range(4) for c in range(4)]
            cached = output['cached_plane_to_component_matrix']
            if not same(computed, cached):
                raise ValueError('Computed datum reflection does not match the owned output plane cache')
            result['decoded'].append({
                'feature_object_id': feature['object_id'], 'feature_class_guid': MIRROR_DATUM,
                'input_kind': 'ConstructionPlane', 'input_count': 1, 'component_object_id': component_id,
                'control_record_object_id': provenance['control_record_object_id'],
                'source_plane_object_id': source['native_plane_object_id'], 'output_plane_object_id': output['native_plane_object_id'],
                'mirror_plane_selection': provenance['mirror_plane'], 'source_output_provenance': provenance,
                'native_component_evidence': {'plane_collection_object_id': collection_id,
                    'repeated_plane_object_ids': members, 'uninterpreted_collection_middle_hex': collection[6+11*count:repeated].hex(),
                    'origin_container_object_id': origin_id,
                    'dependency_scopes': [{'feature_object_id': owner['object_id'], 'scope_object_id': owner['component_scope_object_id'],
                                           'component_object_id': owner['component_object_id']} for owner in owners]},
                'stored_input_kind_code': 4, 'stored_api_compute_corresponding_code': 2,
                'is_combine': None, 'stitch_tolerance_cm': None,
                'unresolved_controls': ['Combine and stitch-tolerance API getters unavailable; native control semantics unqualified',
                                        'General datum types, arbitrary construction-plane supports, lifecycle replay and assembly solving'],
                'computed_reflection_matrix': matrix, 'computed_output_plane_frame': computed,
                'stored_output_plane_frame': cached, 'maximum_frame_difference': max(abs(a-b) for a, b in zip(computed, cached)),
                'matrix_scope': 'Computed Householder reflection in the explicitly shared native component; determinant -1, not a proper rigid occurrence transform or stored native matrix',
                'output_scope': 'Owned oriented plane cache corroborates this bounded computation; no API resultFeatures or timeline output is invented'})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            result['unresolved'].append({'feature_object_id': feature['object_id'], 'reason': str(error)})
    return result
