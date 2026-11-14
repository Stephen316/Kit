import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from PackageSpy import ROOT, ReadBundle

from convert.adapters.Fusion.Native.Graph.ReadNames import ReadNames
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Records.MakeDocProfile import MakeDocProfile
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSegment import ReadDocSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

MASK = re.compile(r'[0-9A-Fa-f]{8}-[0-9A-Fa-f-]{27}')


def walk(value, path, found, depth=0):
    if depth > 30:
        return
    if isinstance(value, str):
        if 'Image.' in value or value.endswith('.png'):
            found.append((path, MASK.sub('UUID', value)[:80]))
        return
    if isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            walk(item, path, found, depth + 1)
        return
    fields = getattr(value, '__dataclass_fields__', None)
    if fields:
        for name in fields:
            label = getattr(value, 'FieldName', None)
            walk(getattr(value, name), path + ('.' + label if label and name == 'Value' else ''), found, depth + 1)


def main():
    model = ReadBundle((ROOT / sys.argv[1]).read_bytes())
    entry = model.Documents[int(sys.argv[2])]
    container = ReadContainer(entry.DataValue)
    print('parts', sorted({MASK.sub('UUID', part.Name) for part in container.Parts if part.Name.startswith('Images')}))
    names = {schema.Value.ClassGuid.upper(): schema.NameValue.rsplit('::', 1)[-1] for schema in ReadNames()}
    schemas = ReadDocSchemas()
    metadata = tuple(ReadMetaWire(stream.Metadata, Segment=slot.Segment) for stream, slot in zip(container.Streams, container.Asset.Segments))
    for stream, meta in zip(container.Streams, metadata):
        segment = ReadDocSegment(stream, meta, MakeDocProfile(schemas, metadata, stream.SegmentId))
        for record in segment.Records:
            for group in record.Groups:
                if group.ClassGuid.upper().startswith('830A2A2B'):
                    print('   serializer', record.IsPrimary, 'opaque', getattr(group, 'Opaque', None) is not None, [(field.FieldName, MASK.sub('UUID', str(field.Value))[:60]) for field in group.Fields])
                found = []
                walk(group.Fields, '', found)
                for path, value in found:
                    print(stream.SegmentId, names.get(group.ClassGuid.upper(), group.ClassGuid[:8]), path, value)
                if found:
                    frame = record.Frame
                    print('   primary', record.IsPrimary, 'root', MASK.sub('UUID', str(getattr(frame, 'RootId', None))), 'lineage', [names.get(item.ClassGuid.upper(), item.ClassGuid[:8]) for item in record.Groups])


if __name__ == '__main__':
    main()
