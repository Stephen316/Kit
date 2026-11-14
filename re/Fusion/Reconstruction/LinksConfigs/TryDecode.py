import json
import sys
import traceback
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

import convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas as SchemaModule
from convert.formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import ReadVocabulary

draft = Path(__file__).with_name('DraftClasses.json')
original = SchemaModule.ReadDocSchemas


def patched():
    extra = tuple(item.Value for item in ReadVocabulary(draft)) if draft.exists() else ()
    known = {schema.ClassGuid.upper() for schema in extra}
    return tuple(schema for schema in original() if schema.ClassGuid.upper() not in known) + extra


SchemaModule.ReadDocSchemas = patched
import convert.formats.Fusion.DocumentCodec.ReadDocument as ReadModule

ReadModule.ReadDocSchemas = patched
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
import convert.formats.Fusion.EntityCodec.DecodeEntities
DecodeModule = sys.modules["convert.formats.Fusion.EntityCodec.DecodeEntities"]
import convert.formats.Fusion.MetaCursor as CursorModule

last_cursor = {}
original_init = CursorModule.MetaCursor.__init__


def tracking_init(self, data):
    original_init(self, data)
    last_cursor['cursor'] = self


CursorModule.MetaCursor.__init__ = tracking_init
original_read = DecodeModule.ReadEntity


def traced(record, scope, catalog):
    try:
        return original_read(record, scope, catalog)
    except Exception as error:
        cursor = last_cursor.get('cursor')
        offset = getattr(cursor, 'Offset', None)
        payload = record.Payload
        print('  record', record.ObjectId, 'type', record.TypeCode, 'primary', record.IsPrimary, 'len', len(payload), 'offset', offset, 'error', error)
        if offset is not None:
            print('  context', payload[max(0, offset - 24):offset].hex(' '), '|', payload[offset:offset + 48].hex(' '))
        raise


DecodeModule.ReadEntity = traced

for name in sys.argv[1:]:
    try:
        model = ReadModule.ReadDocument(Path(name).read_bytes())
        output = EmitParsed(model)
        again = ReadModule.ReadDocument(output)
        print(Path(name).name, 'OK', again == model)
    except Exception as error:
        frames = traceback.extract_tb(error.__traceback__)
        where = ' <- '.join(f'{Path(f.filename).stem}:{f.lineno}' for f in frames[-5:])
        print(Path(name).name, 'FAIL', type(error).__name__, error, '|', where)
