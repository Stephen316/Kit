import json
import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Records.DocumentCatalog import DocumentCatalog
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.EntityCodec.Vocabulary.PickSchema import PickSchema
from convert.formats.Fusion.EntityCodec.Vocabulary.SchemaJson import SchemaJson
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

vocabulary = repository / 'src/convert/formats/Fusion/DocumentCodec/Vocabulary/DesignClasses.json'
present = {(item['ClassGuid'].upper(), item['SchemaVersion']) for item in json.loads(vocabulary.read_text())}
container = ReadContainer(Path(sys.argv[1]).read_bytes())
catalog = DocumentCatalog(ReadDocSchemas())
rows = {}
for stream, slot in zip(container.Streams, container.Asset.Segments):
    meta = ReadMetaWire(stream.Metadata, Segment=slot.Segment)
    for entry in meta.Classes:
        rows[entry.ClassGuid.upper()] = entry
output = []
identity = sys.argv[2].upper()
while identity in rows:
    entry = rows[identity]
    known = (identity, entry.SchemaVersion) in present
    print(identity, entry.SchemaVersion, 'base', entry.BaseGuid, 'in DesignClasses' if known else 'absent')
    if not known and len(sys.argv) > 3:
        try:
            schema = PickSchema(identity, entry.SchemaVersion, catalog)
            output.append(schema)
        except ValueError as error:
            print('   unresolved', error)
    identity = entry.BaseGuid.upper()
def wire_json(value):
    data = {'KindValue': value.KindValue}
    if value.Arguments:
        data['Arguments'] = [wire_json(item) for item in value.Arguments]
    if value.Members:
        data['Members'] = [field_json(item) for item in value.Members]
    if value.ClassGuid:
        data['ClassGuid'] = value.ClassGuid
    if value.FixedCount:
        data['FixedCount'] = value.FixedCount
    if value.AllowedInts:
        data['AllowedInts'] = list(value.AllowedInts)
    if value.HasMatrixRows:
        data['HasMatrixRows'] = True
    return data


def field_json(value):
    return {'FieldName': value.FieldName, 'ValueType': wire_json(value.ValueType), 'IsSaved': value.IsSaved}


names = {}
for item in json.loads((repository / 're/Fusion/Reconstruction/BinaryClasses.json').read_text()).get('classes', []):
    names[item['identifier'].upper()] = item['class'].split('::')[-1]
if len(sys.argv) > 3:
    Path(sys.argv[3]).write_text(json.dumps([
        {
            'ClassGuid': item.ClassGuid,
            'BaseGuid': item.BaseGuid,
            'SchemaVersion': item.SchemaVersion,
            'Members': [field_json(field) for field in item.Members],
            'IsValue': item.IsValue,
            'NameValue': names.get(item.ClassGuid.upper(), item.ClassGuid),
            'ClassSpace': rows[item.ClassGuid.upper()].ClassSpace,
        }
        for item in output
    ], indent=2) + '\n')
