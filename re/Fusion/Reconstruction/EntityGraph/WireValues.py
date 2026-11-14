import struct


def read_ref(reader):
    if not reader.boolean():
        return None
    result = {'entityId': reader.number('Q')}
    if reader.boolean():
        raise ValueError('Cross-asset references remain unsupported')
    if reader.boolean():
        result['segmentId'] = reader.number('I')
    return result


def emit_ref(value):
    if value is None:
        return b'\0'
    if not set(value) <= {'entityId', 'segmentId'} or 'entityId' not in value:
        raise ValueError('Unexpected reference fields')
    output = struct.pack('<BQB', 1, value['entityId'], 0)
    return output + (b'\1' + struct.pack('<I', value['segmentId']) if 'segmentId' in value else b'\0')


def read_xyz(reader):
    return {key: reader.number('d') for key in ('x', 'y', 'z')}


def emit_xyz(value):
    return struct.pack('<ddd', value['x'], value['y'], value['z'])


def read_geometry(reader, kind):
    if kind == 'AcGeMatrix3dValueMetaType':
        if reader.boolean():
            return {'identity': True}
        return {'identity': False, 'rows': [[reader.number('d') for _ in range(4)] for _ in range(4)]}
    if kind == 'AcGeLine3dValueMetaType':
        return {'pointOnLine': read_xyz(reader), 'parametricDirection': read_xyz(reader)}
    if kind == 'AcGePlaneValueMetaType':
        return {'normalReversed': reader.boolean(), 'origin': read_xyz(reader), 'uAxis': read_xyz(reader), 'vAxis': read_xyz(reader)}
    if kind == 'AcGeCircArc3dValueMetaType':
        return {'center': read_xyz(reader), 'normal': read_xyz(reader), 'refVec': read_xyz(reader), 'radius': reader.number('d'), 'startAngle': reader.number('d'), 'endAngle': reader.number('d')}
    raise ValueError('Unknown geometry value ' + kind)


def emit_geometry(value, kind):
    if kind == 'AcGeMatrix3dValueMetaType':
        return b'\1' if value['identity'] else b'\0' + b''.join(struct.pack('<d', item) for row in value['rows'] for item in row)
    if kind == 'AcGeLine3dValueMetaType':
        return emit_xyz(value['pointOnLine']) + emit_xyz(value['parametricDirection'])
    if kind == 'AcGePlaneValueMetaType':
        return struct.pack('<B', value['normalReversed']) + b''.join(emit_xyz(value[key]) for key in ('origin', 'uAxis', 'vAxis'))
    if kind == 'AcGeCircArc3dValueMetaType':
        return b''.join(emit_xyz(value[key]) for key in ('center', 'normal', 'refVec')) + b''.join(struct.pack('<d', value[key]) for key in ('radius', 'startAngle', 'endAngle'))
    raise ValueError('Unknown geometry value ' + kind)


def read_sketch_tag(reader):
    return {'version': reader.number('i'), 'tagId': reader.number('Q'), 'secondaryTagId': reader.number('Q'), 'direction': reader.number('I'), 'splitSequenceId': reader.number('I'), 'splitTotalNumber': reader.number('I'), 'objectOffset20': reader.number('Q')}


def emit_sketch_tag(value):
    return struct.pack('<iQQIIIQ', value['version'], value['tagId'], value['secondaryTagId'], value['direction'], value['splitSequenceId'], value['splitTotalNumber'], value['objectOffset20'])


def read_profile_tag(reader):
    version = reader.number('i')
    tags = [read_sketch_tag(reader) for _ in range(reader.count())]
    first = [reader.number('Q') for _ in range(reader.count())]
    second = [reader.number('Q') for _ in range(reader.count())]
    return {'version': version, 'sketchTags': tags, 'objectOffset20Set': first, 'objectOffset38Set': second}


def emit_profile_tag(value):
    output = struct.pack('<iI', value['version'], len(value['sketchTags']))
    output += b''.join(emit_sketch_tag(tag) for tag in value['sketchTags'])
    for key in ('objectOffset20Set', 'objectOffset38Set'):
        output += struct.pack('<I', len(value[key])) + b''.join(struct.pack('<Q', item) for item in value[key])
    return output
