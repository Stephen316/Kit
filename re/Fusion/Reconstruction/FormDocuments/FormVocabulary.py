import argparse
import hashlib
import json
import lzma
import runpy
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

REFLECTION = ROOT / 're/Fusion/LocalOracle/TSplineReflection/Versions.json'
CORPUS = runpy.run_path(str(ROOT / 're/Fusion/Reconstruction/EntityGraph/CorpusProfiles.py'))
PROFILE = CORPUS['PROFILE']
PROFILE['GRAPH']['GraphCodec'].__init__.__globals__['SCHEMA_PATH'] = REFLECTION
TARGET = ROOT / 'src/convert/formats/Fusion/DocumentCodec/Vocabulary/FormClasses.json'
SEGMENTS = ('FusionDesignSegmentType1', 'FusionACTSegmentType1', 'FusionBrowserSegmentType1')
PREFIX = 'FusionAssetName[Active]/'


def sources():
    names = []
    for folder in ('re/Fusion/LocalOracle/TSpline', 're/Fusion/LocalOracle/TSplineCodec'):
        names.extend(sorted((ROOT / folder).glob('*.f3d')))
    extra = BASE / 'Sources.json'
    if extra.is_file():
        names.extend(ROOT / item for item in json.loads(extra.read_text())['archives'])
    return names


def existing():
    catalog = {}
    raw = json.loads(lzma.decompress((ROOT / 'src/convert/formats/Fusion/EntityCodec/Vocabulary/NativeClasses.xz').read_bytes()))
    for entry in raw['Classes']:
        catalog[(entry['ClassGuid'].upper(), entry['SchemaVersion'])] = entry
    for relative in ('src/convert/formats/Fusion/DocumentCodec/Vocabulary/DesignClasses.json', 'src/convert/formats/Fusion/ContainerCodec/Assembly/ActClasses.json', 'src/convert/formats/Fusion/ContainerCodec/Browser/BrowserClasses.json'):
        for entry in json.loads((ROOT / relative).read_text()):
            catalog.setdefault((entry['ClassGuid'].upper(), entry['SchemaVersion']), {key: entry[key] for key in ('ClassGuid', 'BaseGuid', 'SchemaVersion', 'Members', 'IsValue')})
    from convert.formats.Fusion.DocumentCodec.Records.NativeAuxiliary import KAuxiliarySchemas
    for schema in KAuxiliarySchemas:
        catalog.setdefault((schema.ClassGuid.upper(), schema.SchemaVersion), {'auxiliary': schema.ClassGuid})
    return catalog


def segment_classes(path):
    result = {}
    with zipfile.ZipFile(path) as archive:
        for segment in SEGMENTS:
            meta = ReadMetaWire(archive.read(PREFIX + segment + '/MetaStream.dat'))
            result[segment] = {item.ClassGuid.upper(): dict(identifier=item.ClassGuid, baseIdentifier=item.BaseGuid, schemaVersion=item.SchemaVersion, namespace=item.ClassSpace) for item in meta.Classes}
    return result


def close_generic(added, reflection):
    from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
    from convert.formats.Fusion.EntityCodec.Vocabulary.ReadCatalog import ReadCatalog
    from convert.formats.Fusion.EntityCodec.Vocabulary.ReadSchema import ReadSchema
    from convert.formats.Fusion.EntityCodec.Vocabulary.SchemaClasses import SchemaClasses
    from dataclasses import asdict
    root = '98542EB9-A4F2-4137-A808-DBB5B3CD6159'
    native = ReadCatalog().Classes
    from convert.formats.Fusion.DocumentCodec.Records.NativeAuxiliary import KAuxiliarySchemas
    have = {key[0] for key in added} | {schema.ClassGuid.upper() for schema in KAuxiliarySchemas}
    for relative in ('src/convert/formats/Fusion/DocumentCodec/Vocabulary/DesignClasses.json', 'src/convert/formats/Fusion/ContainerCodec/Assembly/ActClasses.json', 'src/convert/formats/Fusion/ContainerCodec/Browser/BrowserClasses.json'):
        have.update(entry['ClassGuid'].upper() for entry in json.loads((ROOT / relative).read_text()))
    pending = [identity for entry in added.values() for identity in SchemaClasses(ReadSchema({key: entry[key] for key in ('ClassGuid', 'BaseGuid', 'SchemaVersion', 'Members', 'IsValue')}))]
    raw = {(entry['ClassGuid'].upper(), entry['SchemaVersion']): entry for entry in json.loads(lzma.decompress((ROOT / 'src/convert/formats/Fusion/EntityCodec/Vocabulary/NativeClasses.xz').read_bytes()))['Classes']}
    result = []
    while pending:
        identity = pending.pop().upper()
        if identity in have or identity == root:
            continue
        versions = native.get(identity, ())
        if len(versions) != 1:
            raise ValueError('Generic Form closure needs exactly one qualified version of ' + identity)
        have.add(identity)
        entry = dict(raw[(identity, versions[0].SchemaVersion)])
        entity = reflection[identity]
        entry['NameValue'] = entity['name'].removesuffix('MetaType')
        entry['ClassSpace'] = entity['addin']
        result.append(entry)
        pending.extend(SchemaClasses(versions[0]))
    return sorted(result, key=lambda item: item['ClassGuid'].upper())


def normalize(schema):
    return json.loads(json.dumps(schema, sort_keys=True))


def main(check):
    known = existing()
    reflection = {item['identifier'].upper(): item for item in json.loads(REFLECTION.read_bytes())['metatypes']}
    added, verified, refined, rows = {}, set(), set(), []
    for path in sources():
        per = segment_classes(path)
        for segment, metadata in per.items():
            builder = CORPUS['CorpusBuilder']({})
            builder.custom.update(CORPUS['expanded_callbacks']())
            builder.metadata = metadata
            builder.codec.classes = metadata
            builder.needed = set(metadata)
            builder.members = []
            profile = builder.build()
            missing = []
            for schema in profile['Classes']:
                key = (schema['ClassGuid'].upper(), schema['SchemaVersion'])
                if key in known:
                    if normalize(known[key]) == normalize(schema):
                        verified.add(key)
                    else:
                        refined.add(key)
                    continue
                if any(other[0] == key[0] for other in known):
                    raise ValueError('Form archive uses another version of a qualified class ' + key[0])
                if key[0] not in metadata:
                    continue
                entity = reflection[key[0]]
                entry = dict(schema)
                entry['NameValue'] = entity['name'].removesuffix('MetaType')
                entry['ClassSpace'] = metadata[key[0]]['namespace']
                if key in added and normalize(added[key]) != normalize(entry):
                    raise ValueError('Context-dependent Form schema ' + key[0])
                added[key] = entry
                missing.append(entity['name'])
            rows.append({'archive': str(path.relative_to(ROOT)), 'segment': segment, 'classes': len(metadata), 'added': sorted(missing)})
    closure = close_generic(added, reflection)
    vocabulary = [added[key] for key in sorted(added)] + closure
    encoded = json.dumps(vocabulary, indent=2) + '\n'
    if check:
        if TARGET.read_text() != encoded:
            raise ValueError('FormClasses.json differs from the reflection derivation')
    else:
        TARGET.write_text(encoded)
    report = {
        'scope': 'Schema-only Form vocabulary derived from native reflection; no entity values or payload bytes',
        'reflection': str(REFLECTION.relative_to(ROOT)),
        'reflection_sha256': hashlib.sha256(REFLECTION.read_bytes()).hexdigest(),
        'target': str(TARGET.relative_to(ROOT)),
        'target_sha256': hashlib.sha256(encoded.encode()).hexdigest(),
        'added_classes': [{'name': entry['NameValue'], 'identifier': entry['ClassGuid'], 'version': entry['SchemaVersion'], 'base': entry['BaseGuid'], 'members': [field['FieldName'] for field in entry['Members']]} for entry in vocabulary],
        'existing_schemas_reverified': len(verified),
        'existing_schemas_refined_by_production': len(refined),
        'archives': rows,
    }
    (BASE / 'FormVocabulary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'added': len(vocabulary), 'reverified': len(verified), 'archives': len(rows) // 3}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    main(parser.parse_args().check)
