import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import TrialGrammar  # noqa: E402,F401
from convert.formats.Fusion.MaterialCodec.Package.ReadPackage import ReadPackage  # noqa: E402
from convert.formats.Fusion.MaterialCodec.Records import DecodeAsset as AssetModule  # noqa: E402
from convert.formats.Fusion.MaterialCodec.Schema.SelectFields import SelectFields  # noqa: E402
from convert.formats.Fusion.MaterialCodec.Values.DecodeLinks import DecodeLinks  # noqa: E402
from convert.formats.Fusion.MaterialCodec.Values import DecodeValue as ValueModule  # noqa: E402

WATCH = set(sys.argv[2].split(','))


def tracing(reader, fields, definition):
    values = []
    for field in SelectFields(fields, definition):
        start = reader.Offset
        if field.FieldName in WATCH:
            print('   BYTES', field.FieldName, reader.Payload[start:start + 160].hex(' '))
        try:
            value = ValueModule.DecodeValue(reader, field)
            links = DecodeLinks(reader, field.ConnectMode)
        except Exception as error:
            print('   FAIL', field.FieldName, field.ValueKind, field.UnitName, field.IsMultiple, field.ConnectMode, error)
            raise
        values.append((field.FieldName, value, links))
    reader.RequireEnd()
    return tuple(AssetModule.PropertyValue(name, value, links) for name, value, links in values)


original = AssetModule.DecodeFields


def chooser(reader, fields, definition):
    names = {field.FieldName for field in fields}
    if names & WATCH:
        print('  asset fields', definition, [(f.FieldName, f.ValueKind) for f in SelectFields(fields, definition)][:80])
        return tracing(reader, fields, definition)
    return original(reader, fields, definition)


AssetModule.PropertyValue = __import__('convert.formats.Fusion.MaterialCodec.Models.PropertyValue', fromlist=['PropertyValue']).PropertyValue
AssetModule.DecodeFields = chooser
path = Path(sys.argv[1])
with ZipFile(path) as outer:
    name = next(item for item in outer.namelist() if item.endswith('.protein'))
    ReadPackage(outer.read(name))
print('decoded')
