"""Owned editable SketchText inputs for the observed planar Emboss captures.

Text object IDs are explicit native identities, never inferred from glyph curves.
The consumed-source option preserves txt_tag_base without interpreting its meaning.
"""
import struct
import uuid

from decode_emboss import decode_emboss
from decode_parameters import read_string
from decode_profiles import PROFILE_DESCRIPTOR_GUID, PROFILE_LOOP_GUID, read_loops
from decode_selection import native_proxy_references
from decode_sketch import attributes, reference
from decode_sketch_texts import TEXT, OPAQUE_LAYOUT, decode_sketch_texts
from decode_sketch_text_controls import decode_rectangle_text_controls

TEXT_DESCRIPTOR = '92F9A5F4-09AA-4B1B-9EE6-DF574D1D183C'
TEXT_LEAF = '90055C05-546C-4EE7-B3C9-3DD922AD0C9C'
SECOND_OPAQUE_LAYOUT = bytes.fromhex(
    '0000000000000000000000f03f000000000000000000000000000000000000000000000c400000000000000000000000000000f03f0000000000000000000000000000f03f00000000000000000000000000000000000000000000f03f0000000000000000000000000000000000000000000000000000000000000000000000000000f03f00000000010000000000000000000000000000803f0000803f0000000000')


def decode_consumed_sketch_texts(data, records, features):
    """Only opt-in sources containing txt_tag_base; merge successes by object ID.

    Ordinary rectangle/path output is deliberately absent. Existing readers own
    those records. Unsupported consumed sources remain in this helper's unresolved.
    """
    selected = set()
    for record in records:
        if record.is_primary and record.class_guid == TEXT:
            try:
                props, _ = attributes(data[record.body:record.end], 2)
                if 'txt_tag_base' in props:
                    selected.add(record.object_id)
            except (ValueError, IndexError, UnicodeError, struct.error):
                continue

    def controls(prefix, flags, tail):
        return decode_rectangle_text_controls(prefix, flags, tail,
                    allowed_layouts=(OPAQUE_LAYOUT, SECOND_OPAQUE_LAYOUT))

    result = decode_sketch_texts(data, records, features, controls_decoder=controls,
                               allow_text_tag_base=True)
    return {'texts': [text for text in result['texts'] if 'opaque_tag_base' in text],
            'unresolved': [item for item in result['unresolved'] if item['object_id'] in selected],
            'scope': 'Only consumed rectangle Text sources with optional opaque txt_tag_base; two exact opaque layout byte strings admitted without matrix interpretation'}


def resolve_emboss_text_profiles(data, records, selection_id, owner_id, features):
    """Five-argument Emboss resolver; caller must attach decoded sketch.texts first."""
    def typed(identity, guid):
        found = [r for r in records if r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(found) != 1:
            raise ValueError('Emboss text typed reference missing or ambiguous')
        return found[0], data[found[0].body:found[0].end]

    proxy, payload = typed(selection_id, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    if reference(payload, len(payload)-11) != owner_id:
        raise ValueError('Emboss text proxy owner disagrees')
    descriptor_ids, props = native_proxy_references(data, proxy)
    if props or not 1 <= len(descriptor_ids) <= 2 or len(set(descriptor_ids)) != len(descriptor_ids):
        raise ValueError('Unobserved Emboss text proxy input list')
    output = []
    for descriptor_id in descriptor_ids:
        candidates = [r for r in records if r.is_primary and r.object_id == descriptor_id
                      and r.class_guid in (TEXT_DESCRIPTOR, PROFILE_DESCRIPTOR_GUID)]
        if len(candidates) != 1:
            raise ValueError('Emboss input descriptor class missing or ambiguous')
        descriptor = candidates[0]
        payload = data[descriptor.body:descriptor.end]
        if (len(payload) != 197 or payload[:2] != b'\0\0'
                or struct.unpack_from('<I', payload, 13)[0] != 1
                or reference(payload, 186) != owner_id):
            raise ValueError('Unobserved Emboss input descriptor framing/owner')
        namespace, cursor = read_string(payload, 17)
        sketch_text, cursor = read_string(payload, cursor)
        uuid.UUID(namespace)
        if len(namespace) != 36 or not sketch_text.isascii() or not sketch_text.isdecimal():
            raise ValueError('Emboss explicit source sketch identity invalid')
        sketch_id = int(sketch_text)
        sketches = [f for f in features if f['kind'] == 'Sketch' and f['sketch_object_id'] == sketch_id]
        if len(sketches) != 1 or cursor != 103 or struct.unpack_from('<QI', payload, cursor) != (1, 1):
            raise ValueError('Emboss input sketch/context framing unresolved')
        sketch = sketches[0]
        context_id = reference(payload, cursor+12)
        _, context = typed(context_id, 'C46D3EEB-40E1-43FA-83DC-9CB204335417')
        # The context namespace must agree; other stored values remain raw.
        if context[:2] != b'\0\0':
            raise ValueError('Emboss source context prefix changed')
        context_namespace, _ = read_string(context, 10)
        if context_namespace != namespace:
            raise ValueError('Emboss descriptor/context namespace disagrees')
        leaf_id = reference(payload, 2)
        common = {'selection_record_object_id': selection_id, 'descriptor_object_id': descriptor_id,
                  'sketch_object_id': sketch_id, 'sketch_name': sketch['name']}
        if descriptor.class_guid == TEXT_DESCRIPTOR:
            _, leaf = typed(leaf_id, TEXT_LEAF)
            if len(leaf) != 10 or leaf[:2] != b'\0\0':
                raise ValueError('Unobserved native Text identity leaf')
            text_id = struct.unpack_from('<Q', leaf, 2)[0]
            _, source = typed(text_id, TEXT)
            texts = [t for t in sketch.get('texts', []) if t.get('object_id') == text_id
                     and t.get('sketch_object_id') == sketch_id and t.get('class_guid') == TEXT]
            if (len(texts) != 1 or reference(source, len(source)-11) != sketch_id
                    or 'opaque_tag_base' not in texts[0]):
                raise ValueError('Emboss native Text ID not linked to owning sketch.texts')
            text = texts[0]
            output.append(dict(common, kind='SketchText', terminal_object_id=leaf_id,
                               text_object_id=text_id, text_entity_tag=text['entity_tag'],
                               text=text['text'], font_name=text['font_name'], height_cm=text['height_cm'],
                               context_evidence={'object_id': context_id, 'raw_hex': context.hex(),
                                                 'namespace': namespace, 'status': 'Context values/transforms unresolved'},
                               descriptor_opaque_suffix_hex=payload[cursor+23:-11].hex(),
                               scope='Explicit native Text object identity linked to owned editable source; no glyph profile inference'))
        else:
            _, loops = typed(leaf_id, PROFILE_LOOP_GUID)
            # Only the captured single ordinary profile set inside the mixed proxy.
            output.append(dict(common, kind='Profile', loop_definition_object_id=leaf_id,
                               loops=read_loops(loops, descriptor_id, sketch),
                               scope='Explicit single profile-set loop membership; traversal and general trims unresolved'))
    return output


def decode_emboss_texts(data, records, body, feature, features):
    """Observed one/two Text or Text+Profile, planar control fixtures only."""
    result = decode_emboss(data, records, body, feature, features,
                           profile_resolver=resolve_emboss_text_profiles)
    profiles = result['profiles']
    kinds = tuple(p['kind'] for p in profiles)
    if (kinds not in (('SketchText',), ('SketchText', 'Profile'), ('SketchText', 'SketchText'))
            or len({p['sketch_object_id'] for p in profiles}) != 1
            or len({p.get('text_object_id') for p in profiles if p['kind'] == 'SketchText'})
               != sum(p['kind'] == 'SketchText' for p in profiles)
            or any(result[k] != 0 for k in ('horizontal_distance_cm', 'vertical_distance_cm', 'rotation_angle_radians'))
            or not result['is_tangent_chain']):
        raise ValueError('Unobserved editable Text Emboss input/control combination')
    result['profile_scope'] = 'Ordered explicit editable Text object identities and optional ordinary profile membership'
    result['geometry_status'] = 'Planar Text Emboss/Deboss controls and owned source identities; glyph generation, font rendering, exact target topology and regeneration unresolved'
    return result
