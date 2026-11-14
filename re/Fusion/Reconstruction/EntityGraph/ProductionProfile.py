import collections
import hashlib
import json
import lzma
import runpy
from pathlib import Path


BASE = Path(__file__).resolve().parent
GRAPH = runpy.run_path(str(BASE / 'DecodeGraph.py'))
ROOT = GRAPH['ROOT']
INTRINSICS = {
    'IntrinsicMetaTypebool': 'bool',
    'IntrinsicMetaTypeuint8': 'u8',
    'IntrinsicMetaTypeuint16': 'u16',
    'IntrinsicMetaTypeuint32': 'u32',
    'IntrinsicMetaTypeuint64': 'u64',
    'IntrinsicMetaTypeint32': 'i32',
    'IntrinsicMetaTypefloat': 'f32',
    'IntrinsicMetaTypedouble': 'f64',
    'IntrinsicMetaTypeIString': 'utf16',
    'IntrinsicMetaTypeHString': 'ascii',
    'IntrinsicMetaTypeUuid': 'utf16',
}
CPP_INTRINSICS = {
    'bool': 'bool', 'unsigned char': 'u8', 'unsigned short': 'u16',
    'unsigned int': 'u32', 'unsigned long long': 'u64', 'int': 'i32',
    'float': 'f32', 'double': 'f64',
    'Na::DesignCapture::EDcDependencyType': 'u32',
}


def wire(kind, **fields):
    return {'KindValue': kind, **fields}


def field(name, value, saved=True):
    return {'FieldName': name, 'ValueType': value, 'IsSaved': saved}


def structure(members):
    return wire('struct', Members=[field(name, value) for name, value in members])


def point(dimensions=3):
    return structure([(name, wire('f64')) for name in ('x', 'y', 'z')[:dimensions]])


def sketch_tag():
    return structure([
        ('version', wire('i32', AllowedInts=[3])),
        ('tagId', wire('u64')),
        ('secondaryTagId', wire('u64', AllowedInts=[0])),
        ('direction', wire('u32', AllowedInts=[0, 1])),
        ('splitSequenceId', wire('u32', AllowedInts=[1])),
        ('splitTotalNumber', wire('u32', AllowedInts=[1])),
        ('objectOffset20', wire('u64', AllowedInts=[0])),
    ])


def callbacks():
    return {
        'ColorValueMetaType': structure([(name, wire('f32')) for name in ('red', 'green', 'blue', 'alpha')]),
        'AcGePoint2dValueMetaType': point(2),
        'AcGePoint3dValueMetaType': point(),
        'AcGeVector3dValueMetaType': point(),
        'AcGeMatrix3dValueMetaType': wire('matrix', HasMatrixRows=False),
        'AcGeLine3dValueMetaType': structure([('pointOnLine', point()), ('parametricDirection', point())]),
        'AcGePlaneValueMetaType': structure([
            ('normalReversed', wire('bool')), ('origin', point()),
            ('uAxis', point()), ('vAxis', point()),
        ]),
        'AcGeCircArc3dValueMetaType': structure([
            ('center', point()), ('normal', point()), ('refVec', point()),
            ('radius', wire('f64')), ('startAngle', wire('f64')), ('endAngle', wire('f64')),
        ]),
        'sketch_tag_idValueMetaType': sketch_tag(),
        'profile_edge_tag_dataValueMetaType': structure([
            ('version', wire('i32', AllowedInts=[0])),
            ('sketchTags', wire('sequence', Arguments=[sketch_tag()])),
            ('objectOffset20Set', wire('set', Arguments=[wire('unsupported')])),
            ('objectOffset38Set', wire('set', Arguments=[wire('unsupported')])),
        ]),
    }


class ProfileBuilder:
    def __init__(self, metadata=None):
        inventory = json.loads(lzma.decompress((BASE / 'GraphInventory.json.xz').read_bytes())) if metadata is None else None
        self.metadata = metadata if metadata is not None else {
            identity.upper(): {
                'identifier': identity,
                'baseIdentifier': item['base'] or '',
                'schemaVersion': item['version'],
            }
            for identity, item in inventory['classes'].items()
        }
        self.codec = GRAPH['GraphCodec']({'classes': self.metadata})
        self.cpp_classes = collections.defaultdict(set)
        for item in json.loads((BASE.parent / 'BinaryClasses.json').read_bytes())['classes']:
            self.cpp_classes[item['class']].add(item['identifier'])
        self.custom = callbacks()
        self.members = []
        self.references = {}
        self.unsupported = set()
        self.needed = set(self.metadata)

    def reference(self, cpp):
        base, args = GRAPH['split_type'](cpp)
        if base not in ('Ns::StrongRef', 'Ns::PassiveRef') or len(args) != 1:
            raise ValueError('Malformed reference type ' + cpp)
        identifiers = self.cpp_classes.get(args[0], set())
        normalized = {value.upper() for value in identifiers}
        if len(normalized) > 1:
            raise ValueError('Ambiguous reference class ' + args[0])
        identity = sorted(identifiers)[0] if identifiers else ''
        self.references[args[0]] = {
            'ClassGuid': identity,
            'resolution': 'binary-class-identifier' if identity else 'unresolved-interface',
        }
        return wire('ref', ClassGuid=identity)

    def cpp_wire(self, cpp):
        base, args = GRAPH['split_type'](cpp)
        if base in ('Ns::StrongRef', 'Ns::PassiveRef'):
            return self.reference(cpp)
        if base in ('std::__1::vector', 'std::__1::list', 'std::__1::set'):
            return wire('set' if base.endswith('::set') else 'sequence', Arguments=[self.cpp_wire(args[0])])
        if base in ('std::__1::map', 'std::__1::unordered_map', 'std::__1::pair'):
            kind = 'pair' if base.endswith('::pair') else 'map'
            return wire(kind, Arguments=[self.cpp_wire(arg) for arg in args[:2]])
        if base == 'std::__1::basic_string' and args[0] in ('char', 'wchar_t'):
            return wire('ascii' if args[0] == 'char' else 'utf16')
        if cpp in CPP_INTRINSICS:
            return wire(CPP_INTRINSICS[cpp])
        metatype = self.codec.type_map.get(cpp)
        if metatype and metatype['name'] != 'PrivatePointer':
            return self.kind_wire(metatype, cpp)
        self.unsupported.add(cpp)
        return wire('unsupported')

    def kind_wire(self, metatype, cpp):
        name = metatype['name']
        if name in INTRINSICS:
            return wire(INTRINSICS[name])
        if name in self.custom:
            return self.custom[name]
        if name in ('PassiveRefMetaType', 'StrongRefMetaType'):
            return self.reference(cpp)
        if name in ('List', 'Vector', 'Set', 'Map', 'HashMap'):
            return self.cpp_wire(cpp)
        if name == 'PrivatePointer':
            return wire('optional', Arguments=[self.cpp_wire(cpp)])
        if metatype.get('category', {}).get('name') == 'value':
            identity = metatype['identifier']
            try:
                groups = self.codec.groups(identity)
            except ValueError:
                self.unsupported.add(cpp)
                return wire('unsupported')
            if not any(self.codec.members(group) for group in groups):
                self.unsupported.add(cpp)
                return wire('unsupported')
            self.needed.add(identity.upper())
            return wire('object', ClassGuid=identity)
        self.unsupported.add(cpp)
        return wire('unsupported')

    def class_schema(self, identity):
        entity = self.codec.schema[identity]
        base = entity['base_identifier'] or ''
        if base:
            self.needed.add(base.upper())
        version = self.metadata.get(identity, {}).get('schemaVersion', entity['metatype_current_version'])
        own = [] if identity == ROOT else self.codec.own_set(identity)['members']
        fields = []
        for member in sorted(own, key=lambda item: item['name']):
            cpp = GRAPH['TOOLS']['demangle'](member['debug_type_name'])
            saved = bool(member['option_mask'] & 1)
            value = self.kind_wire(member['metatype'], cpp)
            fields.append(field(member['name'], value, saved))
            self.members.append({
                'ClassGuid': entity['identifier'], 'FieldName': member['name'],
                'CppType': cpp, 'Metatype': member['metatype']['name'],
                'OptionMask': member['option_mask'], 'IsSaved': saved,
            })
        return {
            'ClassGuid': entity['identifier'], 'BaseGuid': base,
            'SchemaVersion': version, 'Members': fields,
            'IsValue': entity['category'] == 'value',
        }

    def build(self):
        classes = {}
        while remaining := self.needed - classes.keys():
            for identity in sorted(remaining):
                classes[identity] = self.class_schema(identity)
        return {'RootGuid': ROOT, 'Classes': [classes[key] for key in sorted(classes)], 'ExternalTargets': []}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    builder = ProfileBuilder()
    profile = builder.build()
    raw = (json.dumps(profile, indent=2, allow_nan=False) + '\n').encode()
    packed = lzma.compress(raw, preset=9)
    target = BASE / 'DesignProfile.json.xz'
    target.write_bytes(packed)
    sources = [
        BASE / 'GraphInventory.json.xz', GRAPH['SCHEMA_PATH'],
        BASE.parent / 'BinaryClasses.json',
        BASE.parent / 'DocumentAuthoring/Variants/RecipeConstructors.json',
    ]
    report = {
        'schema': 'FusionProductionSchemaProfile/1',
        'fixture': target.name,
        'uncompressedSha256': digest(raw), 'compressedSha256': digest(packed),
        'scope': 'Schema-only qualified current Design declarations; no source entity values, instance identities, payload bytes, offsets, or donor blocks',
        'sources': [{'path': str(path.relative_to(BASE.parents[2])), 'sha256': digest(path.read_bytes())} for path in sources],
        'classCount': len(profile['Classes']),
        'valueClassCount': sum(item['IsValue'] for item in profile['Classes']),
        'memberCount': len(builder.members),
        'savedMemberCount': sum(item['IsSaved'] for item in builder.members),
        'referenceTypes': dict(sorted(builder.references.items())),
        'unsupportedCppTypes': sorted(builder.unsupported),
        'callbackKinds': sorted(builder.custom),
        'qualification': {
            'matrix': 'Identity matrix only; HasMatrixRows remains false',
            'sketchTag': 'Constructor-proven version3, secondaryTagId0, direction0or1, split1of1, objectOffset20zero',
            'profileTag': 'Version0, typed sketch tags, two empty callback sets; nonempty sets rejected',
            'unknownNestedType': 'Unsupported descriptor may only occur beneath an empty collection or absent optional',
            'externalReferences': 'No instance targets in fixture; archive integration must bind explicit segment/object/class identities',
            'unresolvedReferenceInterface': 'No inferred inheritance or invented GUID; unconstrained but target identity must resolve',
        },
        'members': builder.members,
    }
    report_raw = (json.dumps(report, indent=2, allow_nan=False) + '\n').encode()
    (BASE / 'DesignProfileEvidence.json.xz').write_bytes(lzma.compress(report_raw, preset=9))
    summary = {key: value for key, value in report.items() if key not in ('members', 'referenceTypes')}
    summary.update({
        'referenceTypeCount': len(builder.references),
        'unresolvedReferenceTypes': [name for name, item in sorted(builder.references.items()) if not item['ClassGuid']],
        'evidence': 'DesignProfileEvidence.json.xz',
        'evidenceSha256': digest((BASE / 'DesignProfileEvidence.json.xz').read_bytes()),
    })
    (BASE / 'DesignProfileSummary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: summary[key] for key in ('classCount', 'memberCount', 'savedMemberCount', 'referenceTypeCount', 'unresolvedReferenceTypes', 'unsupportedCppTypes')}))


if __name__ == '__main__':
    main()
