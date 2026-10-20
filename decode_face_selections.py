"""Observed owned face descriptors, explicit body anchors and opaque recipes."""
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import decode_recipe
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import reference


def resolve_native_faces(data, records, selection_id, owner_id, body_selections=None):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Face selection typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    def counted(payload, offset):
        count = struct.unpack_from('<I', payload, offset)[0]
        if count > 1024 or offset+4+11*count > len(payload):
            raise ValueError('Unsupported face selection reference count')
        ids = [reference(payload, offset+4+11*i) for i in range(count)]
        if len(set(ids)) != count:
            raise ValueError('Duplicate face selection references')
        return ids, offset+4+11*count

    proxy, payload = typed(selection_id, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    if reference(payload, len(payload)-11) != owner_id:
        raise ValueError('Face selection proxy owner disagrees')
    descriptor_ids, props = native_proxy_references(data, proxy)
    summary = body_selections if body_selections is not None else decode_body_selections(data, records)
    anchors = {a['object_id']: a for a in summary['body_anchors']}
    faces = []
    for identity in descriptor_ids:
        _, descriptor = typed(identity, '5662F619-2281-4AD9-93DC-1FCFDA1062E7')
        if (descriptor[:4] != b'\0'*4 or struct.unpack_from('<I', descriptor, 15)[0] != 1
                or reference(descriptor, len(descriptor)-11) != owner_id):
            raise ValueError('Unsupported face descriptor prefix/owner')
        recipe_id = reference(descriptor, 4)
        namespace, cursor = read_string(descriptor, 19)
        entity_uuid, cursor = read_string(descriptor, cursor)
        if len(namespace) != 36 or len(entity_uuid) != 36:
            raise ValueError('Unsupported face descriptor UUID length')
        uuid.UUID(namespace)
        uuid.UUID(entity_uuid)
        if struct.unpack_from('<Q', descriptor, cursor)[0] != 2:
            raise ValueError('Unsupported face association prefix')
        contexts, cursor = counted(descriptor, cursor+8)
        if len(contexts) > 1:
            raise ValueError('Unobserved face context list')
        for context_id in contexts:
            typed(context_id, 'C46D3EEB-40E1-43FA-83DC-9CB204335417')
        anchor_ids, cursor = counted(descriptor, cursor)
        if len(anchor_ids) != 1 or len(descriptor)-cursor != 67 or anchor_ids[0] not in anchors:
            raise ValueError('Face native body anchor or trailer unresolved')
        anchor = anchors[anchor_ids[0]]
        recipe_record, _ = typed(recipe_id, '7ACC2A03-0261-4879-A14A-A93D661A5BDC')
        recipe = decode_recipe(data, recipe_record, primary)
        if recipe['payload_kind'] not in ('face_recipe_data', 'bounded_face_recipe_data'):
            raise ValueError('Unsupported face selection recipe kind')
        faces.append({'descriptor_object_id': identity, 'body_anchor_object_id': anchor_ids[0],
                      'native_body_object_id': anchor['native_body_object_id'],
                      'source_owner_object_id': anchor['source_owner_object_id'],
                      'namespace_text': namespace, 'entity_guid_text': entity_uuid,
                      'context_record_object_ids': contexts, 'recipe': recipe,
                      'identity_scope': 'Explicit native historical body anchor and owned face recipe; exact ASM face unresolved',
                      'context_scope': 'Context identities retained; no occurrence transform inferred'})
    return {'selection_record_object_id': selection_id, 'attributes': props, 'faces': faces}
