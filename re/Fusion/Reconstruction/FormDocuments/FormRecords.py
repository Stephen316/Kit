import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

def classes():
    names = {}
    for path in (ROOT / 'src/convert/formats/Fusion/DocumentCodec/Vocabulary').glob('*.json'):
        data = json.loads(path.read_text())
        rows = data if isinstance(data, list) else data.get('Classes', data.get('classes', []))
        for row in rows:
            if isinstance(row, dict):
                guid = row.get('ClassGuid') or row.get('Guid') or row.get('guid')
                name = row.get('NameValue') or row.get('Name') or row.get('name')
                if guid and name:
                    names[guid.upper()] = name
    return names


def short(value, depth=0):
    text = repr(value)
    return text if len(text) < 220 else text[:220] + '...'


def main(path, segment_id, wanted):
    model = ReadDocument(Path(path).read_bytes())
    names = classes()
    want = set(wanted.split(',')) if wanted else None
    for segment in model.Segments:
        if segment.Metadata.Header.SegmentId != int(segment_id):
            continue
        for record in segment.Records:
            if not record.Groups:
                continue
            labels = [names.get(group.ClassGuid.upper(), group.ClassGuid) for group in record.Groups]
            if want and not want.intersection(labels):
                continue
            print('#%d type=%d primary=%s root=%s %s' % (record.ObjectId, record.TypeCode, record.IsPrimary, record.Frame.RootId, ' > '.join(labels)))
            if record.Frame.Metadata:
                for meta in record.Frame.Metadata:
                    print('   meta', meta.FieldName, meta.TypeName, meta.ElementName, short(meta.Value))
            for group, label in zip(record.Groups, labels):
                for field in group.Fields:
                    print('   %s.%s = %s' % (label, field.FieldName, short(field.Value)))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '')
