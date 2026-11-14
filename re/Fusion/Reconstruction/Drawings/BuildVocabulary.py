import hashlib
import io
import json
import lzma
import runpy
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
ENTITY = BASE.parent / 'EntityGraph'
CORPUS = runpy.run_path(str(ENTITY / 'CorpusProfiles.py'))
PROFILE = CORPUS['PROFILE']
GRAPH = PROFILE['GRAPH']
TARGET = ROOT / 'src/convert/formats/Fusion/DrawingCodec/Segments/DrawingClasses.json'
SEGMENTS = ('FusionDrawingDesignSegmentType', 'FusionDrawingACTSegmentType')
sys.path.insert(0, str(ROOT / 'src'))


class DrawingCodec(GRAPH['GraphCodec']):
    def __init__(self, archive, schema):
        super().__init__(archive)
        self.schema = {item['identifier'].upper(): item for item in schema['metatypes']}
        for entity in self.schema.values():
            for lookup in entity.get('member_set_lookups') or []:
                for group in lookup.get('member_sets') or []:
                    for member in group.get('members') or []:
                        cpp = GRAPH['TOOLS']['demangle'](member['debug_type_name'])
                        if member['metatype']['name'] != 'PrivatePointer':
                            self.type_map[cpp] = member['metatype']


class DrawingBuilder(CORPUS['CorpusBuilder']):
    def kind_wire(self, metatype, cpp):
        if metatype['name'] == 'PairMetaType':
            return self.cpp_wire(cpp)
        return super().kind_wire(metatype, cpp)


def segment_classes(path):
    from convert.formats.Fusion.MetaIndex import SegmentKind
    from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
    from compression import zstd
    data = Path(path).read_bytes()
    archive = zipfile.ZipFile(io.BytesIO(data))
    found = {}
    for kind in SEGMENTS:
        meta = archive.read('Documentation[Active]/' + kind + '1/MetaStream.dat')
        value = ReadMetaWire(meta, Segment=SegmentKind(kind))
        for row in value.Classes:
            entry = {'identifier': row.ClassGuid, 'baseIdentifier': row.BaseGuid, 'schemaVersion': row.SchemaVersion, 'namespace': row.ClassSpace}
            previous = found.get(row.ClassGuid.upper())
            if previous is not None and previous != entry:
                raise ValueError('Inconsistent drawing class row ' + row.ClassGuid)
            found[row.ClassGuid.upper()] = entry
    return found, hashlib.sha256(data).hexdigest()


def known_schemas():
    from convert.formats.Fusion.DocumentCodec.Records.DocumentCatalog import DocumentCatalog
    from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
    catalog = DocumentCatalog(ReadDocSchemas())
    return {(guid, schema.SchemaVersion) for guid, schemas in catalog.Classes.items() for schema in schemas}


def main(schema_path, samples):
    schema = json.loads(Path(schema_path).read_bytes())
    metadata, sources = {}, []
    for sample in samples:
        classes, digest = segment_classes(sample)
        for key, value in classes.items():
            if key in metadata and metadata[key] != value:
                raise ValueError('Sample class versions disagree for ' + key)
            metadata[key] = value
        sources.append(digest)
    builder = DrawingBuilder({})
    builder.custom.update(CORPUS['expanded_callbacks']())
    builder.metadata = metadata
    builder.codec = DrawingCodec({'classes': metadata}, schema)
    builder.needed = set(metadata)
    builder.members = []
    profile = builder.build()
    known = known_schemas()
    names = {key: value for key, value in builder.codec.schema.items()}
    output = []
    for entry in profile['Classes']:
        key = (entry['ClassGuid'].upper(), entry['SchemaVersion'])
        if key in known:
            continue
        reflected = names[entry['ClassGuid'].upper()]
        output.append({**entry, 'NameValue': reflected['name'].removesuffix('MetaType'), 'ClassSpace': reflected['addin'] or ''})
    output.sort(key=lambda item: (item['ClassGuid'].upper(), item['SchemaVersion']))
    TARGET.write_text(json.dumps(output, indent=1) + '\n')
    unsupported = [
        {'class': item['NameValue'], 'field': field['FieldName'], 'kind': field['ValueType']['KindValue']}
        for item in output for field in item['Members']
        if field['IsSaved'] and CORPUS['has_unsupported'](field['ValueType'])
    ]
    report = {
        'schema': 'KitFusionDrawingVocabulary/1',
        'reflection_sha256': hashlib.sha256(Path(schema_path).read_bytes()).hexdigest(),
        'sample_sha256': sources,
        'drawing_classes': len(metadata),
        'emitted_classes': [{'name': item['NameValue'], 'guid': item['ClassGuid'], 'version': item['SchemaVersion'], 'members': len(item['Members'])} for item in output],
        'unsupported_saved_fields': unsupported,
        'unsupported_cpp_types': sorted(builder.unsupported),
        'unresolved_references': [name for name, value in builder.references.items() if not value['ClassGuid']],
        'vocabulary_sha256': hashlib.sha256(TARGET.read_bytes()).hexdigest(),
    }
    (BASE / 'Vocabulary.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in report.items()}))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
