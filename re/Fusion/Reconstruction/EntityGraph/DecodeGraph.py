import collections
import hashlib
import json
import math
import lzma
import runpy
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parents[1]
TOOLS = runpy.run_path(str(BASE / 'ReflectedFeatures.py'))
WIRE = runpy.run_path(str(Path(__file__).with_name('WireValues.py')))
CURVES = runpy.run_path(str(Path(__file__).with_name('CurveValues.py')))
RECIPES = runpy.run_path(str(Path(__file__).with_name('RecipeValues.py')))
PROGENITORS = runpy.run_path(str(Path(__file__).with_name('ProgenitorValues.py')))
ROOT = TOOLS['ROOT_ENTITY']
SCHEMA_PATH = BASE.parents[0] / 'LocalOracle' / 'Reflection' / 'Versions.json'
FORMATS = {'bool': 'B', 'unsigned char': 'B', 'unsigned short': 'H', 'unsigned int': 'I', 'unsigned long long': 'Q', 'int': 'i', 'float': 'f', 'double': 'd'}
INTRINSICS = {'IntrinsicMetaTypebool': 'B', 'IntrinsicMetaTypeuint8': 'B', 'IntrinsicMetaTypeuint16': 'H', 'IntrinsicMetaTypeuint32': 'I', 'IntrinsicMetaTypeuint64': 'Q', 'IntrinsicMetaTypeint32': 'i', 'IntrinsicMetaTypefloat': 'f', 'IntrinsicMetaTypedouble': 'd'}


def split_type(value):
    if '<' not in value:
        return value, []
    base, tail = value.split('<', 1)
    if not tail.endswith('>'):
        raise ValueError('Malformed template type ' + value)
    pieces, start, depth = [], 0, 0
    for index, char in enumerate(tail[:-1]):
        depth += (char == '<') - (char == '>')
        if char == ',' and depth == 0:
            pieces.append(tail[start:index].strip())
            start = index + 1
    pieces.append(tail[start:-1].strip())
    return base, pieces


class GraphCodec:
    def __init__(self, archive):
        self.schema = {item['identifier'].upper(): item for item in json.loads(SCHEMA_PATH.read_bytes())['metatypes']}
        self.classes = {item['identifier'].upper(): item for item in archive['classes'].values()}
        self.type_map = {}
        for entry in json.loads((BASE / 'BinaryClasses.json').read_bytes())['classes']:
            entity = self.schema.get(entry['identifier'].upper())
            if entity and entity['category'] == 'value' and entry['class'].endswith('ValueMetaType'):
                self.type_map[entry['class'][:-13]] = {'name': entity['name'], 'identifier': entity['identifier'], 'category': {'name': 'value'}}
        for entity in self.schema.values():
            for lookup in (entity.get('member_set_lookups') or []):
                for group in lookup.get('member_sets') or []:
                    for member in group.get('members') or []:
                        cpp = TOOLS['demangle'](member['debug_type_name'])
                        if member['metatype']['name'] != 'PrivatePointer':
                            self.type_map[cpp] = member['metatype']

    def read_frame(self, reader, primary):
        result = {'rootId': reader.field('Entity.rootId', 'ASCII', reader.text)}
        if not primary:
            return result
        result['hasSubjects'] = reader.field('Entity.hasEntitySubjects', 'bool', reader.boolean)
        result['subjects'] = []
        if result['hasSubjects']:
            for _ in range(reader.field('Entity.subjectCount', 'u32', reader.count)):
                result['subjects'].append({'subject': WIRE['read_ref'](reader), 'indexInObserverVec': reader.number('i')})
        result['hasNamedMetadata'] = reader.field('Entity.hasNameValuePair', 'bool', reader.boolean)
        result['namedMetadata'] = []
        if result['hasNamedMetadata']:
            for _ in range(reader.field('Entity.nameValuePairCount', 'u32', reader.count)):
                name = reader.field('NameValueMap.name', 'ASCII', reader.text)
                kind = reader.field('NameValueMap.metatypeIdentifier', 'ASCII', reader.text)
                metatype = self.named_type(kind)
                value = reader.field('NameValueMap.' + name, kind, lambda: self.read_kind(reader, metatype, ''))
                result['namedMetadata'].append({'name': name, 'metatype': kind, 'value': value})
        return result

    def emit_frame(self, value, primary):
        output = bytearray(TOOLS['encode_text'](value['rootId']))
        if not primary:
            return bytes(output)
        output.extend(struct.pack('<B', value['hasSubjects']))
        if value['hasSubjects']:
            output.extend(struct.pack('<I', len(value['subjects'])))
            for item in value['subjects']:
                output.extend(WIRE['emit_ref'](item['subject']) + struct.pack('<i', item['indexInObserverVec']))
        output.extend(struct.pack('<B', value['hasNamedMetadata']))
        if value['hasNamedMetadata']:
            output.extend(struct.pack('<I', len(value['namedMetadata'])))
            for item in value['namedMetadata']:
                output.extend(TOOLS['encode_text'](item['name']) + TOOLS['encode_text'](item['metatype']))
                output.extend(self.emit_kind(item['value'], self.named_type(item['metatype']), ''))
        return bytes(output)

    def named_type(self, kind):
        if kind in INTRINSICS or kind in ('IntrinsicMetaTypeIString', 'IntrinsicMetaTypeHString', 'IntrinsicMetaTypeUuid', 'StrongRefMetaType', 'PassiveRefMetaType'):
            return {'name': kind}
        if kind.upper() in self.schema:
            entity = self.schema[kind.upper()]
            return {'name': entity['name'], 'identifier': entity['identifier'], 'category': {'name': entity['category']}}
        raise ValueError('Unsupported named metadata metatype ' + kind)

    def own_set(self, identity):
        entity = self.schema[identity.upper()]
        version = self.classes.get(identity.upper(), {}).get('schemaVersion', entity['metatype_current_version'])
        match = next((item for item in (entity.get('member_set_lookups') or []) if item['lookup_version'] == version), None)
        if not match or match['lookup_status'] != 'initialized':
            raise ValueError('No initialized exact member set for ' + entity['name'] + ' v' + str(version))
        return match['member_sets'][0]

    def groups(self, identity, stops=()):
        groups, seen = [], set()
        while identity and identity.upper() != ROOT and identity.upper() not in stops:
            identity = identity.upper()
            if identity in seen:
                raise ValueError('Recursive schema inheritance')
            seen.add(identity)
            entity = self.schema[identity]
            if identity in self.classes and self.classes[identity]['baseIdentifier'].upper() != (entity['base_identifier'] or '').upper():
                raise ValueError('Archive inheritance differs from reflection')
            groups.append(self.own_set(identity))
            identity = entity['base_identifier']
        return groups

    def members(self, group):
        return sorted((item for item in group['members'] if item['option_mask'] & 1), key=lambda item: item['name'])

    def read_cpp(self, reader, cpp):
        base, args = split_type(cpp)
        if base in ('Ns::StrongRef', 'Ns::PassiveRef'):
            return WIRE['read_ref'](reader)
        if base in ('std::__1::vector', 'std::__1::list', 'std::__1::set'):
            return [self.read_cpp(reader, args[0]) for _ in range(reader.count())]
        if base in ('std::__1::map', 'std::__1::unordered_map'):
            return [{'key': self.read_cpp(reader, args[0]), 'value': self.read_cpp(reader, args[1])} for _ in range(reader.count())]
        if base == 'std::__1::pair':
            return {'first': self.read_cpp(reader, args[0]), 'second': self.read_cpp(reader, args[1])}
        if base == 'std::__1::basic_string':
            if args[0] not in ('char', 'wchar_t'):
                raise ValueError('Unsupported string character type ' + args[0])
            return reader.text(args[0] == 'wchar_t')
        if cpp == 'Na::DesignCapture::EDcDependencyType':
            return reader.number('I')
        if cpp in FORMATS:
            return reader.boolean() if cpp == 'bool' else reader.number(FORMATS[cpp])
        if cpp in self.type_map and self.type_map[cpp]['name'] != 'PrivatePointer':
            return self.read_kind(reader, self.type_map[cpp], cpp)
        raise ValueError('Unsupported nested C++ type ' + cpp)

    def emit_cpp(self, value, cpp):
        base, args = split_type(cpp)
        if base in ('Ns::StrongRef', 'Ns::PassiveRef'):
            return WIRE['emit_ref'](value)
        if base in ('std::__1::vector', 'std::__1::list', 'std::__1::set'):
            return struct.pack('<I', len(value)) + b''.join(self.emit_cpp(item, args[0]) for item in value)
        if base in ('std::__1::map', 'std::__1::unordered_map'):
            return struct.pack('<I', len(value)) + b''.join(self.emit_cpp(item['key'], args[0]) + self.emit_cpp(item['value'], args[1]) for item in value)
        if base == 'std::__1::pair':
            return self.emit_cpp(value['first'], args[0]) + self.emit_cpp(value['second'], args[1])
        if base == 'std::__1::basic_string':
            return TOOLS['encode_text'](value, args[0] == 'wchar_t')
        if cpp == 'Na::DesignCapture::EDcDependencyType':
            return struct.pack('<I', value)
        if cpp in FORMATS:
            return struct.pack('<' + FORMATS[cpp], value)
        if cpp in self.type_map and self.type_map[cpp]['name'] != 'PrivatePointer':
            return self.emit_kind(value, self.type_map[cpp], cpp)
        raise ValueError('Unsupported nested C++ type ' + cpp)

    def read_kind(self, reader, metatype, cpp):
        kind = metatype['name']
        if kind == 'ProgenitorAuxDataValueMetaType':
            return PROGENITORS['read_progenitor_aux'](reader)
        if kind == 'RECIPEValueMetaType':
            return RECIPES['read_recipe'](reader)
        if kind in ('AcGeLineSeg3dValueMetaType', 'AcGeEllipArc3dValueMetaType', 'AcGeNurbCurve3dValueMetaType'):
            return CURVES['read_curve'](reader, kind)
        if kind == 'ColorValueMetaType':
            return {key: reader.number('f') for key in ('red', 'green', 'blue', 'alpha')}
        if kind == 'sketch_tag_idValueMetaType':
            return WIRE['read_sketch_tag'](reader)
        if kind == 'profile_edge_tag_dataValueMetaType':
            return WIRE['read_profile_tag'](reader)
        if kind in INTRINSICS:
            return reader.boolean() if kind == 'IntrinsicMetaTypebool' else reader.number(INTRINSICS[kind])
        if kind in ('IntrinsicMetaTypeIString', 'IntrinsicMetaTypeHString', 'IntrinsicMetaTypeUuid'):
            return reader.text(kind != 'IntrinsicMetaTypeHString')
        if kind in ('PassiveRefMetaType', 'StrongRefMetaType'):
            return WIRE['read_ref'](reader)
        if kind in ('List', 'Vector', 'Set', 'Map', 'HashMap'):
            return self.read_cpp(reader, cpp)
        if kind in ('AcGePoint2dValueMetaType', 'AcGePoint3dValueMetaType', 'AcGeVector3dValueMetaType'):
            keys = ('x', 'y') if '2d' in kind else ('x', 'y', 'z')
            return {key: reader.number('d') for key in keys}
        if kind in ('AcGeMatrix3dValueMetaType', 'AcGeLine3dValueMetaType', 'AcGePlaneValueMetaType', 'AcGeCircArc3dValueMetaType'):
            return WIRE['read_geometry'](reader, kind)
        if kind == 'PrivatePointer':
            count = reader.count()
            if count > 1:
                raise ValueError('Invalid private pointer count')
            return None if not count else self.read_cpp(reader, cpp)
        if metatype['category']['name'] == 'value':
            groups = self.groups(metatype['identifier'])
            if not any(self.members(group) for group in groups):
                raise ValueError('Custom value callback requires wire evidence: ' + kind)
            return self.read_groups(reader, groups)
        raise ValueError('Unsupported metatype ' + kind + ': ' + cpp)

    def emit_kind(self, value, metatype, cpp):
        kind = metatype['name']
        if kind == 'ProgenitorAuxDataValueMetaType':
            return PROGENITORS['emit_progenitor_aux'](value)
        if kind == 'RECIPEValueMetaType':
            return RECIPES['emit_recipe'](value)
        if kind in ('AcGeLineSeg3dValueMetaType', 'AcGeEllipArc3dValueMetaType', 'AcGeNurbCurve3dValueMetaType'):
            return CURVES['emit_curve'](value, kind)
        if kind == 'ColorValueMetaType':
            return b''.join(struct.pack('<f', value[key]) for key in ('red', 'green', 'blue', 'alpha'))
        if kind == 'sketch_tag_idValueMetaType':
            return WIRE['emit_sketch_tag'](value)
        if kind == 'profile_edge_tag_dataValueMetaType':
            return WIRE['emit_profile_tag'](value)
        if kind in INTRINSICS:
            return struct.pack('<' + INTRINSICS[kind], value)
        if kind in ('IntrinsicMetaTypeIString', 'IntrinsicMetaTypeHString', 'IntrinsicMetaTypeUuid'):
            return TOOLS['encode_text'](value, kind != 'IntrinsicMetaTypeHString')
        if kind in ('PassiveRefMetaType', 'StrongRefMetaType'):
            return WIRE['emit_ref'](value)
        if kind in ('List', 'Vector', 'Set', 'Map', 'HashMap'):
            return self.emit_cpp(value, cpp)
        if kind in ('AcGePoint2dValueMetaType', 'AcGePoint3dValueMetaType', 'AcGeVector3dValueMetaType'):
            keys = ('x', 'y') if '2d' in kind else ('x', 'y', 'z')
            return b''.join(struct.pack('<d', value[key]) for key in keys)
        if kind in ('AcGeMatrix3dValueMetaType', 'AcGeLine3dValueMetaType', 'AcGePlaneValueMetaType', 'AcGeCircArc3dValueMetaType'):
            return WIRE['emit_geometry'](value, kind)
        if kind == 'PrivatePointer':
            return struct.pack('<I', value is not None) + (self.emit_cpp(value, cpp) if value is not None else b'')
        if metatype['category']['name'] == 'value':
            return self.emit_groups(value, self.groups(metatype['identifier']))
        raise ValueError('Unsupported metatype ' + kind)

    def read_groups(self, reader, groups):
        values = []
        for group in groups:
            identity = group['metatype_identifier']
            fields = {}
            for member in self.members(group):
                qualified = self.schema[identity.upper()]['name'] + '.' + member['name']
                cpp = TOOLS['demangle'](member['debug_type_name'])
                fields[member['name']] = reader.field(qualified, cpp, lambda: self.read_kind(reader, member['metatype'], cpp))
            values.append({'identifier': identity, 'fields': fields})
        return values

    def emit_groups(self, values, groups):
        if len(values) != len(groups):
            raise ValueError('Schema group mismatch')
        output = bytearray()
        for value, group in zip(values, groups):
            members = self.members(group)
            if value['identifier'].upper() != group['metatype_identifier'].upper() or set(value['fields']) != {item['name'] for item in members}:
                raise ValueError('Schema field mismatch')
            for member in members:
                output.extend(self.emit_kind(value['fields'][member['name']], member['metatype'], TOOLS['demangle'](member['debug_type_name'])))
        return bytes(output)


def read_graph(path):
    archive = TOOLS['read_archive'](Path(path))
    codec = GraphCodec(archive)
    values = []
    for record in archive['records']:
        reader = TOOLS['Reader'](record['payload'])
        stops = {item['class']['identifier'].upper() for item in archive['records'] if item['identity'] == record['identity'] and not item['primary'] and item is not record}
        groups = codec.groups(record['class']['identifier'], stops)
        value = {'frame': codec.read_frame(reader, record['primary']), 'groups': codec.read_groups(reader, groups)}
        if reader.offset != len(reader.data):
            raise ValueError('Unexplained bytes in entity ' + str(record['identity']))
        values.append({'identity': record['identity'], 'primary': record['primary'], 'classCode': record['classCode'], 'payloadBulkOffset': record['payloadBulkOffset'], 'value': value})
    return {'archive': archive, 'codec': codec, 'records': values}


def emit_record(codec, value, primary):
    groups = [codec.own_set(group['identifier']) for group in value['groups']]
    for current, following in zip(groups, groups[1:]):
        if codec.schema[current['metatype_identifier'].upper()]['base_identifier'].upper() != following['metatype_identifier'].upper():
            raise ValueError('Noncontiguous inheritance groups')
    return codec.emit_frame(value['frame'], primary) + codec.emit_groups(value['groups'], groups)


def inspect(path):
    archive = TOOLS['read_archive'](path)
    codec = GraphCodec(archive)
    results = []
    for record in archive['records']:
        reader = TOOLS['Reader'](record['payload'])
        identity = record['class']['identifier']
        result = {'entityId': record['identity'], 'primary': record['primary'], 'class': codec.schema[identity.upper()]['name'], 'classIdentifier': identity, 'schemaVersion': record['class']['schemaVersion'], 'payloadBulkOffset': record['payloadBulkOffset'], 'payloadBytes': len(reader.data), 'payloadSha256': TOOLS['digest'](reader.data)}
        try:
            stops = {item['class']['identifier'].upper() for item in archive['records'] if item['identity'] == record['identity'] and not item['primary'] and item is not record}
            groups = codec.groups(identity, stops)
            value = {'frame': codec.read_frame(reader, record['primary']), 'groups': codec.read_groups(reader, groups)}
            if reader.offset != len(reader.data):
                raise ValueError('Trailing unexplained bytes: ' + str(len(reader.data) - reader.offset))
            encoded = codec.emit_frame(value['frame'], record['primary']) + codec.emit_groups(json.loads(json.dumps(value['groups'], allow_nan=False)), groups)
            if encoded != reader.data:
                raise ValueError('Typed reencoding is not byte identical')
            result.update({'status': 'reencoded', 'value': value, 'unexplainedBytes': 0})
        except (ValueError, KeyError, UnicodeError, struct.error, RecursionError) as error:
            result.update({'status': 'unresolved', 'error': str(error), 'consumedBytes': reader.offset, 'unexplainedBytes': len(reader.data) - reader.offset})
        result['fields'] = reader.evidence
        results.append(result)
    return {'archive': path.name, 'archiveSha256': TOOLS['digest'](path.read_bytes()), 'metadataSha256': archive['metadataSha256'], 'bulkSha256': archive['bulkSha256'], 'recordCount': len(results), 'statusCounts': dict(collections.Counter(item['status'] for item in results)), 'records': results}


def main():
    directory = BASE.parents[0] / 'LocalOracle' / 'Features'
    results = [inspect(directory / name) for name in ('circle_sketch.f3d', 'extrude_07mm.f3d', 'extrude_13mm.f3d')]
    output = {'schema': 'FusionEntityGraphTypedCoverage/1', 'reflection': str(SCHEMA_PATH.relative_to(BASE.parents[2])), 'reflectionSha256': TOOLS['digest'](SCHEMA_PATH.read_bytes()), 'scope': 'Research only: candidate typed layouts, byte-identical complete records distinguished from unresolved records; not a complete writer or vendor-loadability claim', 'samples': results}
    raw = (json.dumps(output, indent=2, allow_nan=False) + '\n').encode()
    compressed = lzma.compress(raw, preset=9)
    Path(__file__).with_name('GraphPayloads.json').write_bytes(raw)
    Path(__file__).with_name('GraphPayloads.json.xz').write_bytes(compressed)
    summary = {'schema': 'FusionEntityGraphCoverageSummary/1', 'evidence': 'GraphPayloads.json.xz', 'uncompressedSha256': TOOLS['digest'](raw), 'compressedSha256': TOOLS['digest'](compressed), 'reflectionSha256': output['reflectionSha256'], 'recordCount': sum(sample['recordCount'] for sample in results), 'payloadBytes': sum(record['payloadBytes'] for sample in results for record in sample['records']), 'samples': [{key: sample[key] for key in ('archive', 'archiveSha256', 'metadataSha256', 'bulkSha256', 'recordCount', 'statusCounts')} for sample in results]}
    Path(__file__).with_name('GraphSummary.json').write_text(json.dumps(summary, indent=2) + '\n')
    for sample in results:
        print(sample['archive'], sample['statusCounts'])
        print(collections.Counter((item['class'], item.get('error')) for item in sample['records'] if item['status'] == 'unresolved'))


if __name__ == '__main__':
    main()
