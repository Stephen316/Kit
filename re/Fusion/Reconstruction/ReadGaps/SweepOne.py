import dataclasses
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, os.environ.get('SWEEP_SRC', str(ROOT / 'src')))
sys.setrecursionlimit(20000)
MISSING = dataclasses.MISSING


def failure(error):
    frames = traceback.extract_tb(error.__traceback__)
    where = ' <- '.join(f'{Path(f.filename).stem}:{f.lineno}' for f in reversed(frames[-4:]))
    return {'class': type(error).__name__, 'message': str(error)[:200], 'where': where}


def feed(state, value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        state.update(b'(' + type(value).__name__.encode())
        for field in dataclasses.fields(value):
            item = getattr(value, field.name)
            if field.default is not MISSING and item == field.default:
                continue
            if field.default_factory is not MISSING and item == field.default_factory():
                continue
            state.update(b' ' + field.name.encode() + b'=')
            feed(state, item)
        state.update(b')')
    elif isinstance(value, (tuple, list)):
        state.update(b'[')
        for item in value:
            feed(state, item)
            state.update(b',')
        state.update(b']')
    elif hasattr(value, 'items') and hasattr(value, 'keys'):
        state.update(b'{')
        for key, item in value.items():
            feed(state, key)
            state.update(b':')
            feed(state, item)
            state.update(b',')
        state.update(b'}')
    elif isinstance(value, (set, frozenset)):
        state.update(b'<' + ','.join(sorted(repr(item) for item in value)).encode() + b'>')
    else:
        state.update(repr(value).encode())


def digest(value):
    state = hashlib.sha256()
    feed(state, value)
    return state.hexdigest()


class BodyView:
    def __init__(self, node):
        self.BodyNode = node


def material(model):
    from convert.adapters.Fusion.Projection.NativeMaterial import NativeMaterial
    from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
    from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
    row = {}
    try:
        from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import MaterialSpec
        spec = NativeMaterial(model)
        if not model.Bodies and spec == MaterialSpec():
            row['native'] = {'status': 'empty'}
        else:
            row['native'] = {'status': 'pass', 'digest': digest(spec)}
    except Exception as error:
        row['native'] = {'status': 'fail', **failure(error)}
    try:
        graph = BuildGraph(model)
    except Exception as error:
        row['graph'] = {'status': 'fail', **failure(error)}
        return row
    bodies = [node for node in graph.Nodes.values() if node.ClassName == 'Body']
    results = []
    for node in sorted(bodies, key=lambda item: (item.SegmentId, item.ObjectId)):
        try:
            record = ReadMaterial(graph, BodyView(node), model)
            results.append({'status': 'pass', 'digest': digest((record.EntityName, record.Density, record.ColorValue))})
        except Exception as error:
            results.append({'status': 'fail', **failure(error)})
    bad = [item for item in results if item['status'] != 'pass']
    row['graph'] = {
        'status': 'none' if not results else ('pass' if not bad else 'fail'),
        'bodies': len(results),
        'failed': len(bad),
        'digest': digest([item.get('digest') for item in results]),
    }
    if bad:
        row['graph'].update({key: bad[0][key] for key in ('class', 'message', 'where')})
    return row


def document(data, deep):
    from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
    from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
    row = {'kind': 'design'}
    start = time.monotonic()
    try:
        model = ReadDocument(data)
    except Exception as error:
        row.update({'read': 'fail', **failure(error), 'seconds': round(time.monotonic() - start, 2)})
        return row
    row.update({'read': 'pass', 'model': digest(model), 'seconds': round(time.monotonic() - start, 2)})
    if deep:
        try:
            again = ReadDocument(EmitParsed(model))
            row['round'] = 'pass' if again == model else 'model'
        except Exception as error:
            row['round'] = 'fail'
            row['round_error'] = failure(error)
    row['material'] = material(model)
    return row


def drawing(data, deep):
    from convert.formats.Fusion.DrawingCodec.EmitDrawing import EmitDrawing
    from convert.formats.Fusion.DrawingCodec.ReadDrawing import ReadDrawing
    row = {'kind': 'drawing'}
    try:
        model = ReadDrawing(data)
    except Exception as error:
        row.update({'read': 'fail', **failure(error)})
        return row
    row.update({'read': 'pass', 'model': digest(model)})
    if deep:
        try:
            row['round'] = 'pass' if ReadDrawing(EmitDrawing(model)) == model else 'model'
        except Exception as error:
            row['round'] = 'fail'
            row['round_error'] = failure(error)
    return row


def bundle(data, deep):
    from convert.formats.Fusion.BundleCodec.EmitBundle import EmitBundle
    from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
    row = {'kind': 'bundle'}
    try:
        model = ReadBundle(data)
    except Exception as error:
        row.update({'read': 'fail', **failure(error)})
        return row
    row['read'] = 'pass'
    if deep:
        try:
            row['round'] = 'pass' if ReadBundle(EmitBundle(model)) == model else 'model'
        except Exception as error:
            row['round'] = 'fail'
            row['round_error'] = failure(error)
    members = []
    for index, entry in enumerate(model.Documents):
        suffix = Path(entry.FileName).suffix.lower()
        if suffix == '.f3d':
            child = document(entry.DataValue, deep)
        elif suffix == '.f2d':
            child = drawing(entry.DataValue, deep)
        else:
            child = {'kind': 'other', 'read': 'skip'}
        child['member'] = index
        child['suffix'] = suffix
        members.append(child)
    row['members'] = members
    return row


def main():
    path = ROOT / sys.argv[1]
    deep = len(sys.argv) > 2 and sys.argv[2] == 'deep'
    data = path.read_bytes()
    row = {'file': sys.argv[1], 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    suffix = path.suffix.lower()
    if suffix == '.f3z':
        row.update(bundle(data, deep))
    elif suffix == '.f2d':
        row.update(drawing(data, deep))
    else:
        row.update(document(data, deep))
    sys.stdout.write(json.dumps(row) + '\n')


if __name__ == '__main__':
    main()
