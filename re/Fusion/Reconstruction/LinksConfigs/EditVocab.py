import json
import re
import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sources = {
    'design': repository / 'src/convert/formats/Fusion/DocumentCodec/Vocabulary/DesignClasses.json',
    'act': repository / 'src/convert/formats/Fusion/ContainerCodec/Assembly/ActClasses.json',
    'browser': repository / 'src/convert/formats/Fusion/ContainerCodec/Browser/BrowserClasses.json',
}


def mark_matrices(shape):
    if shape.get('KindValue') == 'matrix':
        shape['HasMatrixRows'] = True
    for argument in shape.get('Arguments', []):
        mark_matrices(argument)
    for member in shape.get('Members', []):
        mark_matrices(member['ValueType'])


def main():
    command = sys.argv[1]
    target = sources[sys.argv[2]]
    data = json.loads(target.read_text())
    if command == 'matrix':
        class_name, field_name = sys.argv[3], sys.argv[4]
        hits = 0
        for entry in data:
            if entry['NameValue'] == class_name:
                for member in entry['Members']:
                    if member['FieldName'] == field_name:
                        mark_matrices(member['ValueType'])
                        hits += 1
        if hits != 1:
            raise SystemExit(f'expected one field, found {hits}')
    elif command == 'add':
        additions = json.loads(Path(sys.argv[3]).read_text())
        names = {sys.argv[i] for i in range(4, len(sys.argv))}
        for entry in additions:
            if entry['NameValue'] in names:
                data = [item for item in data if item['ClassGuid'].upper() != entry['ClassGuid'].upper()]
                data.append(entry)
    text = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
    text = re.sub(r'"AllowedInts": \[([^\]]*)\]', lambda match: '"AllowedInts": [' + ', '.join(part.strip() for part in match.group(1).split(',')) + ']', text)
    target.write_text(text)
    print('updated', target.name)


main()
