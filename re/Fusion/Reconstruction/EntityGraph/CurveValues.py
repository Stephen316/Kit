import struct


def read_xyz(reader):
    return {key: reader.number('d') for key in ('x', 'y', 'z')}


def emit_xyz(value):
    return struct.pack('<ddd', value['x'], value['y'], value['z'])


def read_array(reader, points=False):
    count, capacity, growth = reader.count(), reader.count(), reader.count()
    if count > capacity:
        raise ValueError('Geometry array length exceeds physical allocation')
    return {'physicalLength': capacity, 'growLength': growth, 'values': [read_xyz(reader) if points else reader.number('d') for _ in range(count)]}


def emit_array(value, points=False):
    values = value['values']
    if len(values) > value['physicalLength']:
        raise ValueError('Geometry array length exceeds physical allocation')
    return struct.pack('<III', len(values), value['physicalLength'], value['growLength']) + b''.join(emit_xyz(item) if points else struct.pack('<d', item) for item in values)


def read_curve(reader, kind):
    if kind == 'AcGeLineSeg3dValueMetaType':
        return {'startPoint': read_xyz(reader), 'displacement': read_xyz(reader)}
    if kind == 'AcGeEllipArc3dValueMetaType':
        result = {key: read_xyz(reader) for key in ('center', 'majorAxis', 'minorAxis')}
        result.update({key: reader.number('d') for key in ('majorRadius', 'minorRadius', 'startAngle', 'endAngle')})
        return result
    if kind == 'AcGeNurbCurve3dValueMetaType':
        result = {'evalMode': reader.boolean(), 'isPeriodic': reader.boolean(), 'degree': reader.number('i'), 'knotTolerance': reader.number('d')}
        result['knots'] = read_array(reader)
        result['weights'] = read_array(reader)
        result['controlPoints'] = read_array(reader, True)
        result['interval'] = {'tolerance': reader.number('d'), 'boundedBelow': reader.boolean(), 'boundedAbove': reader.boolean(), 'lowerBound': reader.number('d'), 'upperBound': reader.number('d')}
        return result
    raise ValueError('Unsupported custom curve value ' + kind)


def emit_curve(value, kind):
    if kind == 'AcGeLineSeg3dValueMetaType':
        return emit_xyz(value['startPoint']) + emit_xyz(value['displacement'])
    if kind == 'AcGeEllipArc3dValueMetaType':
        return b''.join(emit_xyz(value[key]) for key in ('center', 'majorAxis', 'minorAxis')) + b''.join(struct.pack('<d', value[key]) for key in ('majorRadius', 'minorRadius', 'startAngle', 'endAngle'))
    if kind == 'AcGeNurbCurve3dValueMetaType':
        output = struct.pack('<BBid', value['evalMode'], value['isPeriodic'], value['degree'], value['knotTolerance'])
        output += emit_array(value['knots']) + emit_array(value['weights']) + emit_array(value['controlPoints'], True)
        interval = value['interval']
        return output + struct.pack('<dBBdd', interval['tolerance'], interval['boundedBelow'], interval['boundedAbove'], interval['lowerBound'], interval['upperBound'])
    raise ValueError('Unsupported custom curve value ' + kind)
