import json
import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import KMinClassCode
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

names = {}
for item in json.loads((repository / 're/Fusion/Reconstruction/BinaryClasses.json').read_text()).get('classes', []):
    names[item['identifier'].upper()] = item['class']


def hexdump(data, width=32):
    lines = []
    for start in range(0, len(data), width):
        chunk = data[start:start + width]
        text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f'    {start:5d} {chunk.hex(" ")} {text}')
    return '\n'.join(lines)


def records(path, wanted):
    container = ReadContainer(Path(path).read_bytes())
    for stream, slot in zip(container.Streams, container.Asset.Segments):
        meta = ReadMetaWire(stream.Metadata, Segment=slot.Segment)
        registry = dict(enumerate(meta.Classes, KMinClassCode))
        for span in ReadBulkSpans(stream.BulkData, stream.Metadata, Segment=slot.Segment):
            entry = registry[span.TypeCode]
            label = names.get(entry.ClassGuid.upper(), entry.ClassGuid)
            if wanted and not any(w.lower() in label.lower() or w.upper() == entry.ClassGuid.upper() for w in wanted):
                continue
            yield slot.Segment.name, span.ObjectId, span.IsPrimary, label, stream.BulkData[span.PayloadOffset:span.EndOffset]


if __name__ == '__main__':
    path = sys.argv[1]
    wanted = sys.argv[2:]
    for segment, identity, primary, label, payload in records(path, wanted):
        print(segment, identity, 'primary' if primary else 'continued', label, len(payload))
        print(hexdump(payload))
