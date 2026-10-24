"""Resolve observed owned sketch-profile proxies without deriving trimmed contours."""
import struct
import uuid

from decode_parameters import read_string
from decode_profiles import PROFILE_DESCRIPTOR_GUID, PROFILE_LOOP_GUID, read_loops
from decode_selection import native_proxy_references
from decode_sketch import reference


def resolve_sketch_profiles(data, records, selection_id, owner_id, features):
    def typed(identity, guid):
        matches = [r for r in records if r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(matches) != 1:
            raise ValueError('Sketch profile typed reference missing or ambiguous')
        record = matches[0]
        return record, data[record.body:record.end]

    def owned(payload):
        if reference(payload, len(payload)-11) != owner_id:
            raise ValueError('Sketch profile selection owner disagrees')

    proxy, payload = typed(selection_id, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    owned(payload)
    descriptor_ids, props = native_proxy_references(data, proxy)
    if props:
        raise ValueError('Unobserved sketch profile selection attributes')
    profiles = []
    for descriptor_id in descriptor_ids:
        descriptor, payload = typed(descriptor_id, PROFILE_DESCRIPTOR_GUID)
        owned(payload)
        if payload[:2] != b'\0\0' or struct.unpack_from('<I', payload, 13)[0] != 1:
            raise ValueError('Unsupported sketch profile descriptor')
        namespace, cursor = read_string(payload, 17)
        sketch_text, cursor = read_string(payload, cursor)
        if len(namespace) != 36 or not sketch_text.isascii() or not sketch_text.isdecimal():
            raise ValueError('Unsupported explicit profile sketch identity')
        uuid.UUID(namespace)
        sketch_id = int(sketch_text)
        sketches = [f for f in features if f['kind'] == 'Sketch' and f['sketch_object_id'] == sketch_id]
        if len(sketches) != 1:
            raise ValueError('Profile sketch unresolved or ambiguous')
        definition_id = reference(payload, 2)
        _, definition = typed(definition_id, PROFILE_LOOP_GUID)
        if len(definition) < 17 or definition[:2] != b'\0\0' or reference(definition, 2) != descriptor_id:
            raise ValueError('Profile-set definition owner disagrees')
        set_count = struct.unpack_from('<I', definition, 13)[0]
        if not 1 <= set_count <= 1024:
            raise ValueError('Unsupported profile-set count')
        position = 17
        for set_index in range(set_count):
            start = position
            loop_count = struct.unpack_from('<I', definition, position)[0]
            if not 1 <= loop_count <= 1024:
                raise ValueError('Unsupported profile-set loop count')
            position += 4
            for _ in range(loop_count):
                curve_count = struct.unpack_from('<I', definition, position)[0]
                if not 1 <= curve_count <= 100000 or position+4+40*curve_count+1 > len(definition):
                    raise ValueError('Truncated or unsupported profile-set curves')
                position += 4+40*curve_count+1
            if definition[position:position+4] != b'\0'*4:
                raise ValueError('Unsupported profile-set suffix')
            position += 4
            framed = definition[:13]+struct.pack('<I', 1)+definition[start:position]
            loops = read_loops(framed, descriptor_id, sketches[0])
            item = {'selection_record_object_id': selection_id, 'descriptor_object_id': descriptor.object_id,
                         'loop_definition_object_id': definition_id, 'sketch_object_id': sketch_id,
                         'sketch_name': sketches[0]['name'], 'loops': loops,
                         'scope': 'Explicit sketch-curve membership and outer/inner loop flags; traversal and general trims unresolved'}
            if set_count > 1:
                item['profile_set_index'] = set_index
                item['source_profile_set_count'] = set_count
            profiles.append(item)
        if position != len(definition):
            raise ValueError('Unparsed profile-set bytes')
    return profiles
