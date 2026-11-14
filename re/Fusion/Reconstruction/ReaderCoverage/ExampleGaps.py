import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.Records.DocumentCatalog import DocumentCatalog
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

SOURCES = ('re/Fusion/examples/.f3d/example2.f3d', 're/Fusion/examples/.f3z/example1.f3z', 're/Fusion/LocalOracle/Bundles/kit_production_example1.f3z')

registry = {item['identifier'].upper(): item for item in json.loads((ROOT / 're/Fusion/Reconstruction/BinaryClasses.json').read_text())['classes']}
catalog = DocumentCatalog(ReadDocSchemas())


def documents(name):
    data = (ROOT / name).read_bytes()
    if name.endswith('.f3z'):
        for index, entry in enumerate(ReadBundle(data).Documents):
            if entry.FileName.lower().endswith('.f3d'):
                yield f'{name} member {index}', entry.DataValue
    else:
        yield name, data


# saved class versions that the catalog lacks in the example documents written by an older Fusion
def main():
    gaps = collections.defaultdict(lambda: {'documents': 0, 'records': 0})
    failures = []
    for name in SOURCES:
        for label, data in documents(name):
            try:
                ReadDocument(data)
                failures.append({'document': label, 'error': None})
            except ValueError as error:
                failures.append({'document': label, 'error': str(error)})
            container = ReadContainer(data)
            for stream, slot in zip(container.Streams, container.Asset.Segments, strict=True):
                meta = ReadMetaWire(stream.Metadata, Segment=slot.Segment)
                for row in meta.Classes:
                    identity = row.ClassGuid.upper()
                    versions = sorted(schema.SchemaVersion for schema in catalog.Classes.get(identity, ()))
                    if row.SchemaVersion in versions:
                        continue
                    entry = registry.get(identity, {})
                    runtime = entry.get('runtimeSchema', {})
                    key = (identity, row.SchemaVersion, slot.Segment.name)
                    gap = gaps[key]
                    gap.update({
                        'class_guid': identity,
                        'class': entry.get('class'),
                        'segment': slot.Segment.name,
                        'saved_version': row.SchemaVersion,
                        'catalog_versions': versions,
                        'registered_in_2706': bool(entry),
                        'runtime_version_2706': runtime.get('version'),
                        'kind': 'older than catalog' if versions else 'absent from catalog',
                    })
                    gap['documents'] += 1
                    gap['records'] += len(row.OwnerIds)
    rows = sorted(gaps.values(), key=lambda item: (item['kind'], item['class'] or '', item['saved_version']))
    report = {
        'scope': 'Class versions declared in the metadata of the example documents saved by an older Fusion that the catalog does not hold',
        'documents': failures,
        'gap_count': len(rows),
        'kinds': dict(collections.Counter(row['kind'] for row in rows)),
        'gaps': rows,
    }
    Path(__file__).with_name('ExampleGaps.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({key: report[key] for key in ('gap_count', 'kinds')}, indent=1))
    for row in rows:
        print(row['kind'], row['class'], row['saved_version'], row['catalog_versions'], row['runtime_version_2706'], row['documents'], row['records'])


if __name__ == '__main__':
    main()
