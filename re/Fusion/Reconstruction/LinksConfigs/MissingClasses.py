import json
import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Records.DocumentCatalog import DocumentCatalog
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

names = {}
for item in json.loads((repository / 're/Fusion/Reconstruction/BinaryClasses.json').read_text()).get('classes', []):
    names[item['identifier'].upper()] = item['class']
catalog = DocumentCatalog(ReadDocSchemas())
schemas = {s.ClassGuid.upper(): s for s in ReadDocSchemas()}

missing = {}
for name in sys.argv[1:]:
    container = ReadContainer(Path(name).read_bytes())
    for stream, slot in zip(container.Streams, container.Asset.Segments):
        meta = ReadMetaWire(stream.Metadata, Segment=slot.Segment)
        for row in meta.Classes:
            key = row.ClassGuid.upper()
            choices = catalog.Classes.get(key, ())
            versions = [c.SchemaVersion for c in choices]
            if row.SchemaVersion in versions and (slot.Segment.name == 'KDesign' or key in schemas):
                continue
            entry = missing.setdefault((slot.Segment.name, key, row.SchemaVersion), {'name': names.get(key), 'known_versions': versions, 'base': row.BaseGuid, 'files': [], 'owners': 0})
            entry['files'].append(Path(name).stem)
            entry['owners'] += len(row.OwnerIds)
for key, value in sorted(missing.items()):
    print(key[0], key[1], key[2], value['name'], 'known', value['known_versions'], 'owners', value['owners'], 'in', len(value['files']), value['files'][:3])
