"""Explicit modeling topology context routes, without persistent-edge inference.

A 171-byte context terminates without an optional route. The observed181-byte
variant points through a typed4B31 link to a separately framed edge recipe.
Recipe framing and historical body ownership are reused from existing readers.
"""
import struct
import uuid

from decode_body_selections import ANCHOR, CONTEXT, decode_body_selections
from decode_brep_recipes import RECIPE_GUID, decode_recipe
from decode_parameters import read_string
from decode_sketch import reference

TOPOLOGY = '5662F619-2281-4AD9-93DC-1FCFDA1062E7'
CONTEXT_RECIPE_LINK = '4B31DA1B-FCD6-4527-BC3E-BE1FBAF867FE'
SCOPE = 'Explicit topology descriptor/context namespace and entity correspondence, optional typed secondary edge-recipe route, historical body provenance; no geometry, closure or persistent topology mapping'


def decode_selection_context_recipes(data, records, body_selections=None):
    """Stream summary after body selections; contexts/unresolved/scope, no mutation."""
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}
    summary = body_selections if body_selections is not None else decode_body_selections(data, records)
    anchors = {}
    for anchor in summary['body_anchors']:
        anchors.setdefault(anchor['object_id'], []).append(anchor)

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Topology context typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    def text_uuid(payload, cursor):
        text, cursor = read_string(payload, cursor)
        if len(text) != 36:
            raise ValueError('Unobserved topology context UUID length')
        uuid.UUID(text)
        return text, cursor

    contexts, unresolved = [], []
    for record in records:
        if not record.is_primary or record.class_guid != TOPOLOGY:
            continue
        try:
            if primary.get(record.object_id) is not record:
                raise ValueError('Topology descriptor identity ambiguous')
            descriptor = data[record.body:record.end]
            if (len(descriptor) != 276 or descriptor[:3] != bytes(3) or descriptor[3] not in (0, 1)
                    or struct.unpack_from('<I', descriptor, 15)[0] != 1):
                raise ValueError('Unobserved topology descriptor framing')
            owner = reference(descriptor, 265)
            if owner not in primary:
                raise ValueError('Topology descriptor owner unresolved')
            namespace, cursor = text_uuid(descriptor, 19)
            entity, cursor = text_uuid(descriptor, cursor)
            if cursor != 171 or descriptor[cursor:cursor+12] != struct.pack('<QI', 2, 1):
                raise ValueError('Unobserved topology context list framing')
            context_id = reference(descriptor, cursor+12)
            if struct.unpack_from('<I', descriptor, cursor+23)[0] != 1:
                raise ValueError('Unobserved topology historical body anchor count')
            anchor_id = reference(descriptor, cursor+27)
            typed(anchor_id, ANCHOR)
            selected_anchors = anchors.get(anchor_id, [])
            if len(selected_anchors) != 1:
                raise ValueError('Topology context historical body anchor unresolved or ambiguous')
            anchor = selected_anchors[0]
            recipe_record, _ = typed(reference(descriptor, 4), RECIPE_GUID)
            recipe = decode_recipe(data, recipe_record, primary)
            _, context = typed(context_id, CONTEXT)
            if (len(context) not in (171, 181) or context[:2] != bytes(2)
                    or context[6:10] != bytes(4)):
                raise ValueError('Unobserved topology context payload framing')
            context_namespace, position = text_uuid(context, 10)
            context_entity, position = text_uuid(context, position)
            if context_namespace != namespace or context_entity != entity or position != 162:
                raise ValueError('Topology descriptor/context namespace or entity disagrees')
            if context[position:position+8] != struct.pack('<Q', 2):
                raise ValueError('Unobserved topology context association field')
            route = None
            if len(context) == 171:
                if context[-1] != 0 or recipe['payload_kind'] not in ('face_recipe_data', 'bounded_face_recipe_data'):
                    raise ValueError('Unobserved absent topology context route/kind')
            else:
                link_id = reference(context, 170)
                _, link = typed(link_id, CONTEXT_RECIPE_LINK)
                if len(link) != 14 or link[:2] != bytes(2) or link[-1] != 0:
                    raise ValueError('Unobserved topology context recipe link framing')
                context_recipe_record, _ = typed(reference(link, 2), RECIPE_GUID)
                context_recipe = decode_recipe(data, context_recipe_record, primary)
                if recipe['payload_kind'] != 'edge_recipe_data' or context_recipe['payload_kind'] != 'edge_recipe_data':
                    raise ValueError('Topology secondary route requires captured edge recipe kinds')
                route = {'link_object_id': link_id, 'link_class_guid': CONTEXT_RECIPE_LINK,
                         'recipe': context_recipe,
                         'association': 'Explicit context reference -> typed link -> typed edge recipe; relationship to descriptor recipe topology unresolved'}
            contexts.append({'descriptor_object_id': record.object_id, 'owner_object_id': owner,
                             'stored_descriptor_flag_at_3': descriptor[3],
                             'descriptor_recipe': recipe, 'context_object_id': context_id,
                             'namespace_text': namespace, 'entity_guid_text': entity,
                             'stored_context_index_field': struct.unpack_from('<I', context, 2)[0],
                             'optional_context_recipe_route': route,
                             'body_anchor_object_id': anchor_id,
                             'native_body_object_id': anchor['native_body_object_id'],
                             'source_owner_object_id': anchor['source_owner_object_id'],
                             'scope': SCOPE})
        except (ValueError, IndexError, KeyError, UnicodeError, struct.error) as error:
            unresolved.append({'descriptor_object_id': record.object_id, 'class_guid': record.class_guid,
                               'record_offset': record.start, 'reason': str(error)})
    return {'contexts': contexts, 'unresolved': unresolved, 'scope': SCOPE}
