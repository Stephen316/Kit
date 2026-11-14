import argparse
import hashlib
import json
import lzma
from pathlib import Path


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
SOURCE = BASE / 'CorpusProfiles.json.xz'
CLASS_KEYS = {'ClassGuid', 'BaseGuid', 'SchemaVersion', 'Members', 'IsValue'}
FIELD_KEYS = {'FieldName', 'ValueType', 'IsSaved'}
WIRE_KEYS = {
    'KindValue', 'Arguments', 'Members', 'ClassGuid', 'FixedCount',
    'AllowedInts', 'HasMatrixRows',
}


def check_fields(fields):
    for field in fields:
        if set(field) != FIELD_KEYS:
            raise ValueError('Field declaration contains non-schema properties')
        check_wire(field['ValueType'])


def check_wire(shape):
    if 'KindValue' not in shape or set(shape) - WIRE_KEYS:
        raise ValueError('Wire declaration contains non-schema properties')
    for argument in shape.get('Arguments', []):
        check_wire(argument)
    check_fields(shape.get('Members', []))


def make_catalog(source):
    classes = sorted(
        source['Classes'].values(),
        key=lambda item: (item['ClassGuid'].upper(), item['SchemaVersion']),
    )
    for entry in classes:
        if set(entry) != CLASS_KEYS:
            raise ValueError('Class declaration contains non-schema properties')
        check_fields(entry['Members'])
    named = source['NamedTypes']
    for entry in named:
        if set(entry) != {'TypeName', 'ValueType'}:
            raise ValueError('Named declaration contains non-schema properties')
        check_wire(entry['ValueType'])
    return {'Classes': classes, 'NamedTypes': named}


def make_sources(source):
    return {
        'Profiles': {
            name: {'MetadataHash': item['MetadataHash']}
            for name, item in sorted(source['Profiles'].items())
        },
    }


def serialize(value):
    raw = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    return raw, lzma.compress(raw, preset=9)


def promote(check_only=False):
    source = json.loads(lzma.decompress(SOURCE.read_bytes()))
    artifacts = (
        (
            ROOT / 'src/convert/formats/Fusion/EntityCodec/Vocabulary/NativeClasses.xz',
            make_catalog(source),
        ),
        (
            ROOT / 'tests/convert/formats/FusionCodec/Corpus/CorpusSources.xz',
            make_sources(source),
        ),
    )
    report = []
    for path, value in artifacts:
        raw, packed = serialize(value)
        if check_only:
            if not path.is_file() or path.read_bytes() != packed:
                raise ValueError('Promoted schema artifact differs: ' + str(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(packed)
        report.append({
            'path': str(path.relative_to(ROOT)),
            'bytes': len(packed),
            'sha256': hashlib.sha256(packed).hexdigest(),
            'uncompressedSha256': hashlib.sha256(raw).hexdigest(),
        })
    print(json.dumps({
        'source': str(SOURCE.relative_to(ROOT)),
        'sourceSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'checkOnly': check_only,
        'classVersionPairs': len(artifacts[0][1]['Classes']),
        'namedTypes': len(artifacts[0][1]['NamedTypes']),
        'sourceArchives': len(artifacts[1][1]['Profiles']),
        'artifacts': report,
    }, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    promote(parser.parse_args().check)
