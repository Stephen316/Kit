import json
import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.DocumentCodec.Records.DocumentCatalog import DocumentCatalog
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas

names = {}
for item in json.loads((repository / 're/Fusion/Reconstruction/BinaryClasses.json').read_text()).get('classes', []):
    names[item['class'].split('::')[-1].lower()] = item['identifier'].upper()
    names[item['identifier'].upper()] = item['identifier'].upper()
catalog = DocumentCatalog(ReadDocSchemas())


def shape(value):
    text = value.KindValue
    if getattr(value, 'ClassGuid', ''):
        text += '<' + value.ClassGuid[:8] + '>'
    if getattr(value, 'Arguments', ()):
        text += '[' + ','.join(shape(a) for a in value.Arguments) + ']'
    if getattr(value, 'Members', ()):
        text += '{' + ','.join(m.FieldName + ':' + shape(m.ValueType) for m in value.Members) + '}'
    return text


for query in sys.argv[1:]:
    key = names.get(query.lower(), query.upper())
    for schema in catalog.Classes.get(key, ()):
        print(query, key, 'v', schema.SchemaVersion, 'base', schema.BaseGuid, 'value' if schema.IsValue else 'entity')
        for member in schema.Members:
            print('   ', member.FieldName, shape(member.ValueType), 'saved' if member.IsSaved else 'unsaved')
