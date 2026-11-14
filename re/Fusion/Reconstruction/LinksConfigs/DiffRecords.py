import json
import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

names = {}
for item in json.loads((repository / 're/Fusion/Reconstruction/BinaryClasses.json').read_text()).get('classes', []):
    names[item['identifier'].upper()] = item['class'].split('::')[-1]


def classes(segment):
    table = {}
    for entry in segment.Metadata.Classes:
        for owner in entry.OwnerIds:
            table[owner] = entry.ClassGuid.upper()
    return table


def describe(path):
    model = ReadDocument(Path(path).read_bytes())
    result = {}
    for segment in model.Segments:
        owners = classes(segment)
        kind = segment.Metadata.Header.Segment.name
        for record in segment.Records:
            guid = owners.get(record.ObjectId, '?')
            result[(kind, record.ObjectId, record.IsPrimary)] = (names.get(guid, guid), record)
    return model, result


base_model, base = describe(sys.argv[1])
model, current = describe(sys.argv[2])
wanted = set(sys.argv[3:])
if wanted == {'changed'}:
    for key in sorted(current):
        if key in base and base[key][1] != current[key][1]:
            before, after = base[key][1], current[key][1]
            print(key, current[key][0])
            if before.Frame != after.Frame:
                print('   frame', str(before.Frame)[:300], '->', str(after.Frame)[:300])
            for old_group, new_group in zip(before.Groups, after.Groups):
                for old_field, new_field in zip(old_group.Fields, new_group.Fields):
                    if old_field != new_field:
                        print('   ', new_field.FieldName, ':', str(old_field.Value)[:200], '->', str(new_field.Value)[:400])
    raise SystemExit
for key in sorted(current):
    label, record = current[key]
    if key in base and base[key][0] == label and not wanted:
        continue
    if wanted and label not in wanted:
        continue
    print(key, label, 'new' if key not in base else 'changed' if base[key][1] != record else 'same')
    print('   frame', record.Frame)
    for group in record.Groups:
        print('   group', names.get(group.ClassGuid.upper(), group.ClassGuid))
        for field in group.Fields:
            print('      ', field)
