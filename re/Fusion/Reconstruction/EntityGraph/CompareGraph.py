import collections
import json
import math
import lzma
import runpy
import sys
import struct
from pathlib import Path

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
API = runpy.run_path(str(DIRECTORY / 'DecodeGraph.py'))


def matches(left, right):
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(matches(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(matches(a, b) for a, b in zip(left, right))
    if isinstance(left, float) and isinstance(right, (int, float)):
        return math.isclose(left, right, rel_tol=1e-14, abs_tol=1e-14)
    return left == right


class Comparison:
    def __init__(self, graph, native):
        self.codec = graph['codec']
        self.native = native
        self.roots = {item['identity']: item['value']['frame']['rootId'] for item in graph['records'] if item['primary'] and item['value']['frame']['rootId']}
        self.native_segment = native['properties']['segment']
        self.segment_offset = self.native_segment - graph['archive']['segmentId']

    def reference(self, value):
        if value is None:
            return {}
        root = self.roots.get(value['entityId'], '') if 'segmentId' not in value else ''
        return {'segId': value['segmentId'] + self.segment_offset if 'segmentId' in value else self.native_segment, 'entityId': -1 if root else value['entityId'], 'rootId': root}

    def cpp_value(self, value, cpp):
        base, args = API['split_type'](cpp)
        if base in ('Ns::StrongRef', 'Ns::PassiveRef'):
            return self.reference(value)
        if base in ('std::__1::vector', 'std::__1::list', 'std::__1::set'):
            return [self.cpp_value(item, args[0]) for item in value]
        if base in ('std::__1::map', 'std::__1::unordered_map'):
            return [[self.cpp_value(item['key'], args[0]), self.cpp_value(item['value'], args[1])] for item in value]
        if base == 'std::__1::pair':
            return [self.cpp_value(value['first'], args[0]), self.cpp_value(value['second'], args[1])]
        if cpp in self.codec.type_map:
            return self.kind_value(value, self.codec.type_map[cpp], cpp)
        return value

    def group_values(self, groups):
        result = {}
        for group in groups:
            schema = self.codec.own_set(group['identifier'])
            for member in self.codec.members(schema):
                name = member['script_id'] or member['name']
                result[name] = self.kind_value(group['fields'][member['name']], member['metatype'], API['TOOLS']['demangle'](member['debug_type_name']))
        return result

    def kind_value(self, value, metatype, cpp):
        kind = metatype['name']
        if kind == 'ColorValueMetaType':
            return {key[0]: value[key] for key in ('red', 'green', 'blue', 'alpha')}
        if kind in ('PassiveRefMetaType', 'StrongRefMetaType'):
            return self.reference(value)
        if kind in ('List', 'Vector', 'Set', 'Map', 'HashMap'):
            return self.cpp_value(value, cpp)
        if kind == 'PrivatePointer':
            return [] if value is None else [self.cpp_value(value, cpp)]
        if kind in ('sketch_tag_idValueMetaType', 'profile_edge_tag_dataValueMetaType'):
            raise ValueError('Native JSON callback omits custom recipe fields')
        if kind == 'AcGeMatrix3dValueMetaType':
            return [[float(i == j) for j in range(4)] for i in range(4)] if value['identity'] else value['rows']
        if kind == 'AcGePlaneValueMetaType':
            u, v = value['uAxis'], value['vAxis']
            normal = {'x': u['y'] * v['z'] - u['z'] * v['y'], 'y': u['z'] * v['x'] - u['x'] * v['z'], 'z': u['x'] * v['y'] - u['y'] * v['x']}
            scale = math.sqrt(sum(axis ** 2 for axis in normal.values())) * (-1 if value['normalReversed'] else 1)
            return {'pointOnPlane': value['origin'], 'normal': {key: axis / scale for key, axis in normal.items()}}
        if kind == 'AcGeLine3dValueMetaType':
            return {'startPoint': value['pointOnLine'], 'endPoint': {key: value['pointOnLine'][key] + value['parametricDirection'][key] for key in ('x', 'y', 'z')}}
        if kind in ('AcGePoint2dValueMetaType', 'AcGePoint3dValueMetaType', 'AcGeVector3dValueMetaType', 'AcGeCircArc3dValueMetaType'):
            return value
        if metatype.get('category', {}).get('name') == 'value':
            return self.group_values(value)
        return value


def inspect(path):
    graph = API['read_graph'](path)
    native_path = path.with_suffix('.entities.json')
    native = {item['identity']['entityId']: item for item in json.loads(native_path.read_bytes()) if 'properties' in item}
    results = []
    for record in graph['records']:
        entity = native.get(record['identity'])
        if entity is None:
            results.append({'entityId': record['identity'], 'primary': record['primary'], 'status': 'native_entity_unavailable', 'rootId': record['value']['frame']['rootId']})
            continue
        comparison = Comparison(graph, entity)
        fields = []
        for group in record['value']['groups']:
            for member in comparison.codec.members(comparison.codec.own_set(group['identifier'])):
                name = member['script_id'] or member['name']
                result = {'group': group['identifier'], 'member': member['name'], 'nativeProperty': name}
                try:
                    expected = entity['properties'][name]
                    decoded = comparison.kind_value(group['fields'][member['name']], member['metatype'], API['TOOLS']['demangle'](member['debug_type_name']))
                    if member['metatype']['name'] == 'HashMap':
                        decoded = sorted(decoded, key=lambda item: json.dumps(item[0], sort_keys=True))
                        expected = sorted(expected, key=lambda item: json.dumps(item[0], sort_keys=True))
                    if member['metatype']['name'] == 'IntrinsicMetaTypefloat':
                        expected = struct.unpack('<f', struct.pack('<f', expected))[0]
                    result['status'] = 'matched' if matches(decoded, expected) else 'different'
                    if result['status'] == 'different':
                        result.update({'decoded': decoded, 'native': expected})
                except (KeyError, ValueError) as error:
                    result.update({'status': 'unavailable', 'reason': str(error)})
                fields.append(result)
        for entry in record['value']['frame'].get('namedMetadata', []):
            name = entry['name']
            fields.append({'member': 'NameValueMap.' + name, 'status': 'matched' if matches(entry['value'], entity['properties'].get(name)) else 'different', 'nativeProperty': name})
        results.append({'entityId': record['identity'], 'primary': record['primary'], 'status': 'compared', 'fields': fields})
    counts = collections.Counter(field['status'] for record in results for field in record.get('fields', []))
    return {'archive': path.name, 'nativeGraphSha256': API['TOOLS']['digest'](native_path.read_bytes()), 'fieldComparisonCounts': dict(counts), 'nativeEntityUnavailable': sum(item['status'] == 'native_entity_unavailable' for item in results), 'records': results}


def json_finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        return {'capturedNonfinite': str(value)}
    if isinstance(value, list):
        return [json_finite(item) for item in value]
    if isinstance(value, dict):
        return {key: json_finite(item) for key, item in value.items()}
    return value


def main():
    directory = DIRECTORY.parents[1] / 'LocalOracle' / 'Features'
    samples = [inspect(directory / name) for name in ('circle_sketch.f3d', 'extrude_07mm.f3d', 'extrude_13mm.f3d')]
    output = {'schema': 'FusionEntityGraphNativeComparison/1', 'floatComparison': {'relativeTolerance': 1e-14, 'absoluteTolerance': 1e-14, 'reason': 'Native JSON renders fewer decimal digits than the binary double payload'}, 'referenceNormalization': 'Archive segment ids shifted by native Design segment minus archive Design segment; named roots resolved through primary frame rootId', 'samples': samples}
    raw = (json.dumps(json_finite(output), indent=2, allow_nan=False) + '\n').encode()
    compressed = lzma.compress(raw, preset=9)
    (DIRECTORY / 'NativeComparison.json.xz').write_bytes(compressed)
    summary = {key: value for key, value in output.items() if key != 'samples'}
    summary.update({'completeEvidence': 'NativeComparison.json.xz', 'uncompressedSha256': API['TOOLS']['digest'](raw), 'compressedSha256': API['TOOLS']['digest'](compressed)})
    summary['samples'] = [{key: value for key, value in sample.items() if key != 'records'} | {'differences': [record | {'fields': [field for field in record.get('fields', []) if field['status'] != 'matched']} for record in sample['records'] if any(field['status'] != 'matched' for field in record.get('fields', []))]} for sample in samples]
    (DIRECTORY / 'NativeComparison.json').write_text(json.dumps(json_finite(summary), indent=2, allow_nan=False) + '\n')
    for sample in samples:
        print(sample['archive'], sample['fieldComparisonCounts'])
        for record in sample['records']:
            for field in record.get('fields', []):
                if field['status'] != 'matched':
                    print(record['entityId'], field)


if __name__ == '__main__':
    main()
