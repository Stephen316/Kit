"""Captured SplitFace metadata variants; metadata integers have no assigned meaning.

Common mode, selection, descriptor and owner checks remain in decode_split_face.
This opt-in supports only the saved, nonextended plane-intersection family.
"""
import struct

from decode_extrude import optional_reference
from decode_parameters import read_string
from decode_selection import known_construction_entities
from decode_split_face import FEATURE, decode_split_face

SCOPE = ('Observed SplitFace metadata 8/12 with nonextended SurfaceIntersection, '
         'one constructed plane and one owned historical face recipe; metadata meaning, '
         'exact selected/result faces, lifecycle and regeneration remain unresolved')


def split_face_table_metadata(body):
    """Locate the bounded repeated table without searching for label bytes."""
    if body[:2] != bytes(2):
        raise ValueError('SplitFace metadata variant requires empty attributes prefix')
    _, cursor = optional_reference(body, 2)
    sentinel, end = read_string(body, cursor+71)
    if sentinel != '00000000-0000-0000-0000-000000000000' or body[end:end+3] != bytes(3):
        raise ValueError('Unsupported SplitFace metadata table sentinel')
    count = struct.unpack_from('<I', body, end+3)[0]
    if not 1 <= count <= 6:
        raise ValueError('Unsupported SplitFace metadata reference count')
    offset = end+7+11*count
    value = struct.unpack_from('<I', body, offset)[0]
    label, label_end = read_string(body, offset+4)
    return {'value': value, 'offset': offset, 'label': label,
            'reference_count': count, 'reference_table_start_offset': end+7,
            'metadata_and_label_hex': body[offset:label_end].hex()}


def decode_split_face_metadata_variant(data, records, feature, features, known=None):
    candidates = [r for r in records if r.is_primary and r.object_id == feature['object_id']]
    if len(candidates) != 1 or candidates[0].class_guid != FEATURE or feature.get('class_guid') != FEATURE:
        raise ValueError('SplitFace metadata variant feature missing, ambiguous or wrong class')
    record = candidates[0]
    body = data[record.body:record.end]
    metadata = split_face_table_metadata(body)
    settings = decode_split_face(data, records, body, feature,
        known if known is not None else known_construction_entities(data, records, features),
        features, allowed_table_metadata=(8, 12))
    if (settings['split_type'] != 'SurfaceIntersection' or settings['stored_mode_fields'] != [1, 0]
            or settings['stored_extension_flag'] != 0 or settings['projection_direction'] is not None
            or settings['target_face_count'] != 1 or metadata['reference_count'] != 4
            or len(settings['ordered_selection_reference_ids']) != 4):
        raise ValueError('SplitFace metadata variant outside captured nonextended singleton plane-intersection family')
    tool = settings['tool']['entity']
    plane_sources = [f for f in features if f.get('kind') == 'ConstructionPlane'
        and f.get('object_id') == tool.get('feature_object_id') and f.get('plane_object_id') == tool.get('object_id')]
    if tool.get('kind') != 'ConstructionPlane' or len(plane_sources) != 1:
        raise ValueError('SplitFace metadata variant requires explicitly referenced constructed plane')
    target = settings['target_faces'][0]
    sources = [f for f in features if f.get('object_id') == target['source_owner_object_id']]
    if (len(sources) != 1 or sources[0].get('kind') != 'Extrude'
            or target['recipe']['payload_kind'] != 'bounded_face_recipe_data'):
        raise ValueError('SplitFace metadata variant requires historical Extrude-owned bounded face recipe')
    return {'feature_object_id': feature['object_id'], 'settings': settings,
        'stored_table_metadata': metadata['value'],
        'table_metadata_layout': {
            'body_relative_offset': metadata['offset'],
            'absolute_offset': record.body+metadata['offset'],
            'metadata_and_label_hex': metadata['metadata_and_label_hex'],
            'kind_label': metadata['label'],
            'ordered_reference_count': metadata['reference_count'],
            'reference_table_body_relative_offset': metadata['reference_table_start_offset'],
            'semantics': 'Literal observed uint32 only; no enum, flag, mode or lifecycle meaning assigned'},
        'source_feature_object_id': target['source_owner_object_id'],
        'scope': SCOPE}


def decode_split_face_metadata_variants(data, records, features):
    decoded, unresolved = [], []
    known = known_construction_entities(data, records, features)
    for feature in features:
        if feature.get('kind') != 'SplitFace' or feature.get('class_guid') != FEATURE:
            continue
        candidates = [r for r in records if r.is_primary and r.object_id == feature['object_id']]
        if len(candidates) != 1:
            continue
        body = data[candidates[0].body:candidates[0].end]
        try:
            metadata = split_face_table_metadata(body)
            if metadata['value'] == 4:
                continue  # The existing default reader owns the original family.
            decoded.append(decode_split_face_metadata_variant(data, records, feature, features, known))
        except (ValueError, KeyError, IndexError, TypeError, struct.error, UnicodeError) as error:
            unresolved.append({'feature_object_id': feature['object_id'], 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved, 'scope': SCOPE}
