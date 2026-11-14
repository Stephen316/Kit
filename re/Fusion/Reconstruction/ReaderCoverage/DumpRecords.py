import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire


def spans(path, guid):
    container = ReadContainer(Path(path).read_bytes())
    for stream, slot in zip(container.Streams, container.Asset.Segments, strict=True):
        for span in ReadBulkSpans(stream.BulkData, stream.Metadata, Segment=slot.Segment):
            if span.ClassGuid.upper() == guid.upper():
                yield slot.Segment.name, span, stream.BulkData[span.PayloadOffset:span.EndOffset]


def hexdump(data, width=32):
    for offset in range(0, len(data), width):
        chunk = data[offset:offset + width]
        text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f'  {offset:5d} {chunk.hex(" ")}  {text}')


if __name__ == '__main__':
    guid = sys.argv[1]
    for path in sys.argv[2:]:
        print('==', Path(path).name)
        for segment, span, payload in spans(path, guid):
            print(segment, 'object', span.ObjectId, 'primary', span.IsPrimary, 'bytes', len(payload))
            hexdump(payload[:int(sys.argv[0] and 4096)])
