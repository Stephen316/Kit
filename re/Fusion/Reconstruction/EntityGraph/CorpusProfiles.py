import collections
import hashlib
import json
import lzma
import runpy
from pathlib import Path


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
PROFILE = runpy.run_path(str(BASE / 'ProductionProfile.py'))
GRAPH = PROFILE['GRAPH']
wire = PROFILE['wire']
structure = PROFILE['structure']
point = PROFILE['point']


def expanded_callbacks():
    return {
        'AcGeMatrix3dValueMetaType': wire('matrix', HasMatrixRows=True),
        'AcGeLineSeg3dValueMetaType': structure([('startPoint', point()), ('displacement', point())]),
        'AcGeEllipArc3dValueMetaType': structure([
            ('center', point()), ('majorAxis', point()), ('minorAxis', point()),
            ('majorRadius', wire('f64')), ('minorRadius', wire('f64')),
            ('startAngle', wire('f64')), ('endAngle', wire('f64')),
        ]),
        'AcGeNurbCurve3dValueMetaType': structure([
            ('evalMode', wire('bool')), ('isPeriodic', wire('bool')),
            ('degree', wire('i32')), ('knotTolerance', wire('f64')),
            ('knots', wire('ge-array', Arguments=[wire('f64')])),
            ('weights', wire('ge-array', Arguments=[wire('f64')])),
            ('controlPoints', wire('ge-array', Arguments=[point()])),
            ('interval', structure([
                ('tolerance', wire('f64')), ('boundedBelow', wire('bool')),
                ('boundedAbove', wire('bool')), ('lowerBound', wire('f64')),
                ('upperBound', wire('f64')),
            ])),
        ]),
        'RECIPEValueMetaType': wire('recipe'),
        'sketch_tag_idValueMetaType': wire('sketch-tag'),
        'ProgenitorAuxDataValueMetaType': structure([('tag', wire('u32'))]),
        'profile_edge_tag_dataValueMetaType': structure([
            ('version', wire('i32', AllowedInts=[0])),
            ('sketchTags', wire('sequence', Arguments=[wire('sketch-tag')])),
            ('startAdjacentPrimaryTagIds', wire('set', Arguments=[wire('u64')])),
            ('endAdjacentPrimaryTagIds', wire('set', Arguments=[wire('u64')])),
        ]),
    }


def archive_classes(path):
    name = 'FusionAssetName[Active]/FusionDesignSegmentType1/MetaStream.dat'
    data = GRAPH['TOOLS']['archive_member'](path, name)
    reader = GRAPH['TOOLS']['Reader'](data)
    if reader.text() != 'FusionDesignSegmentType':
        raise ValueError('Not a Design segment')
    reader.number('I')
    reader.text(True)
    if (reader.number('I'), reader.number('I')) != (1234, 8):
        raise ValueError('Unsupported metadata header')
    reader.take(8)
    reader.text()
    reader.text()
    if (reader.number('I'), reader.number('I')) != (1, 0):
        raise ValueError('Unsupported metadata storage')
    classes = {}
    for _ in range(reader.count()):
        identity, base = reader.text(), reader.text()
        version, space = reader.number('I'), reader.text()
        reader.take(8 * reader.count())
        classes[identity.upper()] = dict(identifier=identity, baseIdentifier=base, schemaVersion=version, namespace=space)
    return classes, hashlib.sha256(data).hexdigest()


class CorpusBuilder(PROFILE['ProfileBuilder']):
    def class_schema(self, identity):
        if identity.upper() == 'BE7E2847-FBC4-4898-A6E7-632A559A7F89':
            if self.metadata.get(identity, {}).get('schemaVersion', 0) != 0:
                raise ValueError('Unsupported progenitor auxiliary schema version')
            return {'ClassGuid': identity, 'BaseGuid': '', 'SchemaVersion': 0, 'Members': [PROFILE['field']('tag', wire('u32'))], 'IsValue': True}
        return super().class_schema(identity)


def has_unsupported(shape):
    return shape['KindValue'] == 'unsupported' or any(has_unsupported(value) for value in shape.get('Arguments', [])) or any(has_unsupported(field['ValueType']) for field in shape.get('Members', []))


def main():
    source = BASE.parent / 'CorpusInventory.json'
    inventory = json.loads(source.read_bytes())
    builder = CorpusBuilder({})
    builder.custom.update(expanded_callbacks())
    catalog, profiles, failures = {}, {}, []
    named = [{'TypeName': 'BE7E2847-FBC4-4898-A6E7-632A559A7F89', 'ValueType': structure([('tag', wire('u32'))])}]
    named += [{'TypeName': name, 'ValueType': wire(kind)} for name, kind in (
        ('StrongRefMetaType', 'ref'), ('PassiveRefMetaType', 'ref'),
        ('IntrinsicMetaTypeHString', 'ascii'), ('IntrinsicMetaTypeIString', 'utf16'),
        ('IntrinsicMetaTypeUuid', 'utf16'),
    )]
    for index, entry in enumerate(inventory['files']):
        try:
            metadata, metadata_digest = archive_classes(ROOT / entry['path'])
            builder.metadata = metadata
            builder.codec.classes = metadata
            builder.needed = set(metadata)
            builder.members = []
            profile = builder.build()
            keys = []
            for schema in profile['Classes']:
                key = schema['ClassGuid'].upper() + '@' + str(schema['SchemaVersion'])
                if key in catalog and catalog[key] != schema:
                    raise ValueError('Context-dependent schema for ' + key)
                catalog[key] = schema
                keys.append(key)
            profiles[entry['path']] = {'Classes': keys, 'MetadataHash': metadata_digest}
        except (ValueError, KeyError) as error:
            failures.append({'path': entry['path'], 'error': str(error)})
        if index % 100 == 0:
            print(json.dumps({'processed': index + 1, 'profiles': len(profiles), 'failures': len(failures)}), flush=True)
    output = {'schema': 'FusionCorpusSchemaProfiles/1', 'RootGuid': GRAPH['ROOT'], 'Classes': catalog, 'Profiles': profiles, 'NamedTypes': named}
    raw = (json.dumps(output, indent=2, allow_nan=False) + '\n').encode()
    packed = lzma.compress(raw, preset=9)
    (BASE / 'CorpusProfiles.json.xz').write_bytes(packed)
    summary = {
        'schema': 'FusionCorpusSchemaProfileSummary/1',
        'scope': 'Schema-only production descriptors selected by each archive metadata; no decoded record values or entity identities',
        'fixture': 'CorpusProfiles.json.xz', 'uncompressedSha256': hashlib.sha256(raw).hexdigest(),
        'compressedSha256': hashlib.sha256(packed).hexdigest(), 'archiveCount': len(profiles),
        'classVersionPairs': len(catalog), 'uniqueClasses': len({value['ClassGuid'].upper() for value in catalog.values()}),
        'inventorySha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'reflectionSha256': hashlib.sha256(GRAPH['SCHEMA_PATH'].read_bytes()).hexdigest(),
        'sketchSplitEvidence': [{'path': name, 'sha256': hashlib.sha256((BASE / name).read_bytes()).hexdigest()} for name in ('SketchSplitSemantics.json', 'SketchSplitSamples.json')],
        'unsupportedCppTypes': sorted(builder.unsupported),
        'unsupportedPersistedFields': [{'class': builder.codec.schema[value['ClassGuid'].upper()]['name'], 'classGuid': value['ClassGuid'], 'version': value['SchemaVersion'], 'field': field['FieldName'], 'outerKind': field['ValueType']['KindValue']} for value in catalog.values() for field in value['Members'] if field['IsSaved'] and has_unsupported(field['ValueType'])],
        'unresolvedReferenceTypes': [name for name, value in builder.references.items() if not value['ClassGuid']],
        'archiveFailures': failures,
        'newQualifications': ['Nonidentity matrix bool+16f64; the static evidence that first supported it was removed', 'Line segment, ellipse, NURB and geometry arrays use the callback order that frames every corpus record', 'ASM recipes restrict the versioned union to observed version3', 'Named progenitor auxiliary value is exactly four bytes, read as tag:uint32', 'Profile tag sets are read as start/end adjacent primary tag identities; this naming is not confirmed by a black-box experiment', 'Sketch split uint32 fields are one-based ordinal and total count; every corpus split pair satisfies 1 <= ordinal <= total', 'Sketch direction admits 0, 1 and UINT32_MAX, all observed in the corpus'],
        'retainedGuards': ['Sketch tags retain version3/secondary0/topologyRoleFlags0 restrictions pending additional semantics', 'Sketch split pairs reject zero ordinal/count or ordinal greater than total, without a corpus-derived maximum', 'Reference target class constraints remain enabled', 'Unknown nested types reject nonempty values'],
        'runtimeVerification': 'Not run locally; all production decode/reencode verification belongs to remote compatibility CI',
    }
    (BASE / 'CorpusProfileSummary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: summary[key] for key in ('archiveCount', 'classVersionPairs', 'uniqueClasses', 'archiveFailures', 'unresolvedReferenceTypes')}), flush=True)


if __name__ == '__main__':
    main()
