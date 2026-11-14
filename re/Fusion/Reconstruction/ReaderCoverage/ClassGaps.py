import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Records.DocumentCatalog import DocumentCatalog
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

names = {item['identifier'].upper(): item['class'] for item in json.loads((ROOT / 're/Fusion/Reconstruction/BinaryClasses.json').read_text()).get('classes', [])}
catalog = DocumentCatalog(ReadDocSchemas())


def census(paths):
    gaps = collections.defaultdict(list)
    for name in paths:
        try:
            container = ReadContainer(Path(name).read_bytes())
        except Exception as error:
            print('container', name, error)
            continue
        for stream, slot in zip(container.Streams, container.Asset.Segments, strict=True):
            meta = ReadMetaWire(stream.Metadata, Segment=slot.Segment)
            for row in meta.Classes:
                versions = [schema.SchemaVersion for schema in catalog.Classes.get(row.ClassGuid.upper(), ())]
                if row.SchemaVersion not in versions:
                    key = (row.ClassGuid.upper(), row.SchemaVersion, names.get(row.ClassGuid.upper()), tuple(versions), slot.Segment.name)
                    gaps[key].append((Path(name).name, len(row.OwnerIds)))
    return gaps


if __name__ == '__main__':
    paths = sys.argv[1:]
    if len(paths) == 1 and paths[0].endswith('.json'):
        report = json.loads(Path(paths[0]).read_text())
        paths = [str(ROOT / row['file']) for row in report['rows'] if 'Unqualified' in row.get('error', '') and row['file'].endswith('.f3d')]
    for key, rows in sorted(census(paths).items(), key=lambda item: -len(item[1])):
        print(key, len(rows), rows[:6])
