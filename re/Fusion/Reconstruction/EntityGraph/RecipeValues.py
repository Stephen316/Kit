import struct


def read_count(reader):
    count = reader.number('i')
    if count < 0 or count > 1000000:
        raise ValueError('Invalid recipe count ' + str(count))
    return count


def read_tag(reader, version):
    return {'primaryId': list(reader.take(read_count(reader))), 'secondaryId': reader.number('i'), 'operationIds': [reader.number('i') for _ in range(read_count(reader))], 'approachId': reader.number('i') if version >= 3 else None}


def read_tag_table(reader, version):
    return [[read_tag(reader, version) for _ in range(read_count(reader))] for _ in range(read_count(reader))]


def emit_count(count):
    if type(count) is not int or count < 0 or count > 1000000:
        raise ValueError('Invalid recipe count ' + str(count))
    return struct.pack('<i', count)


def emit_tag(value, version):
    primary = bytes(value['primaryId'])
    operations = value['operationIds']
    return emit_count(len(primary)) + primary + struct.pack('<i', value['secondaryId']) + emit_count(len(operations)) + b''.join(struct.pack('<i', item) for item in operations) + (struct.pack('<i', value['approachId']) if version >= 3 else b'')


def emit_tag_table(value, version):
    return emit_count(len(value)) + b''.join(emit_count(len(group)) + b''.join(emit_tag(tag, version) for tag in group) for group in value)


def read_payload(reader, kind, depth=0):
    if depth > 64:
        raise ValueError('Recipe nesting limit exceeded')
    value = {'primaryTagIndex': reader.number('i')}
    if kind == 'base_recipe_data':
        return value
    if kind in ('body_recipe_data', 'face_recipe_data', 'bounded_face_recipe_data', 'edge_recipe_data'):
        value['lwdTagIndex'] = reader.number('i')
    if kind in ('body_recipe_data', 'face_recipe_data'):
        return value
    if kind == 'bounded_face_recipe_data':
        value['edges'] = [read_payload(reader, 'edge_recipe_data', depth + 1) for _ in range(read_count(reader))]
        return value
    if kind == 'edge_recipe_data':
        value['adjacentFaces'] = [read_payload(reader, 'face_recipe_data', depth + 1) for _ in range(read_count(reader))]
        value['adjacentVertices'] = [read_payload(reader, 'vertex_recipe_data', depth + 1) for _ in range(read_count(reader))]
        value['referenceFaceIndex'] = reader.number('i')
        return value
    if kind == 'vertex_recipe_data':
        value['adjacentFaces'] = [read_payload(reader, 'face_recipe_data', depth + 1) for _ in range(read_count(reader))]
        value['adjacentEdges'] = [read_payload(reader, 'edge_recipe_data', depth + 1) for _ in range(read_count(reader))]
        value['uvOrders'] = [{'key': reader.number('i'), 'value': {key: reader.number('i') for key in ('faceVertexCount', 'uOrder', 'uLowerOrder', 'uUpperOrder', 'vOrder', 'vLowerOrder', 'vUpperOrder')}} for _ in range(read_count(reader))]
        return value
    raise ValueError('Unknown recipe payload type ' + kind)


def emit_payload(value, kind, depth=0):
    if depth > 64:
        raise ValueError('Recipe nesting limit exceeded')
    output = struct.pack('<i', value['primaryTagIndex'])
    if kind == 'base_recipe_data':
        return output
    if kind in ('body_recipe_data', 'face_recipe_data', 'bounded_face_recipe_data', 'edge_recipe_data'):
        output += struct.pack('<i', value['lwdTagIndex'])
    if kind in ('body_recipe_data', 'face_recipe_data'):
        return output
    if kind == 'bounded_face_recipe_data':
        return output + emit_count(len(value['edges'])) + b''.join(emit_payload(item, 'edge_recipe_data', depth + 1) for item in value['edges'])
    if kind == 'edge_recipe_data':
        for key, child in (('adjacentFaces', 'face_recipe_data'), ('adjacentVertices', 'vertex_recipe_data')):
            output += emit_count(len(value[key])) + b''.join(emit_payload(item, child, depth + 1) for item in value[key])
        return output + struct.pack('<i', value['referenceFaceIndex'])
    if kind == 'vertex_recipe_data':
        for key, child in (('adjacentFaces', 'face_recipe_data'), ('adjacentEdges', 'edge_recipe_data')):
            output += emit_count(len(value[key])) + b''.join(emit_payload(item, child, depth + 1) for item in value[key])
        output += emit_count(len(value['uvOrders']))
        for item in value['uvOrders']:
            output += struct.pack('<i', item['key'])
            output += b''.join(struct.pack('<i', item['value'][key]) for key in ('faceVertexCount', 'uOrder', 'uLowerOrder', 'uUpperOrder', 'vOrder', 'vLowerOrder', 'vUpperOrder'))
        return output
    raise ValueError('Unknown recipe payload type ' + kind)


def read_recipe(reader):
    version = reader.number('i')
    if version != 3:
        raise ValueError('Unqualified ASM recipe version ' + str(version))
    value = {'version': version, 'tags': read_tag_table(reader, version), 'lwdTags': read_tag_table(reader, version)}
    value['type'] = reader.take(read_count(reader)).decode('ascii')
    value['payload'] = read_payload(reader, value['type'])
    return value


def emit_recipe(value):
    if value['version'] != 3:
        raise ValueError('Unqualified ASM recipe version ' + str(value['version']))
    kind = value['type'].encode('ascii')
    return struct.pack('<i', value['version']) + emit_tag_table(value['tags'], value['version']) + emit_tag_table(value['lwdTags'], value['version']) + emit_count(len(kind)) + kind + emit_payload(value['payload'], value['type'])
