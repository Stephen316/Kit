import collections
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

RECORDS = json.loads((BASE / 'RoundTrip.json').read_text())['rows']


def classes():
    names = {}
    for path in (ROOT / 'src/convert/formats/Fusion/DocumentCodec/Vocabulary').glob('*.json'):
        for row in json.loads(path.read_text()):
            names[row['ClassGuid'].upper()] = row['NameValue']
    return names


def main():
    names = classes()
    shapes = collections.Counter()
    archives = 0
    for row in RECORDS:
        if row['status'] != 'pass':
            continue
        archives += 1
        model = ReadDocument((ROOT / row['file']).read_bytes())
        for segment in model.Segments:
            for record in segment.Records:
                for meta in record.Frame.Metadata or ():
                    owner = names.get(record.Groups[0].ClassGuid.upper(), record.Groups[0].ClassGuid) if record.Groups else ''
                    count = len(meta.Value.Items) if meta.TypeName == 'Vector' else None
                    shapes[(segment.Metadata.Header.SegmentId, owner, meta.FieldName, meta.TypeName, meta.ElementName, count)] += 1
    rows = [{'segment': key[0], 'class': key[1], 'field': key[2], 'type': key[3], 'element': key[4], 'items': key[5], 'records': value} for key, value in sorted(shapes.items(), key=str)]
    report = {'scope': 'Named metadata shapes in the Form archives that pass the production round trip', 'archives': archives, 'shapes': rows}
    (BASE / 'NamedVectors.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
