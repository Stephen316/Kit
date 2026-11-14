import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))

import convert.formats.Fusion.EntityCodec.Values.ReadValueMut as Values
import convert.formats.Fusion.EntityCodec.Values.ReadFieldsMut as Fields
from ExampleRecords import documents
from RecordFailures import failures

STACK = []
SEEN = collections.Counter()


def main():
    atom = Values.ReadAtomMut
    original = Fields.ReadFieldsMut

    def fields(cursor, specs, catalog, depth, reader):
        result = []
        for spec in specs:
            if not spec.IsSaved:
                continue
            STACK.append(spec.FieldName)
            start = cursor.Offset
            try:
                result.append(Fields.NamedValue(spec.FieldName, reader(cursor, spec.ValueType, catalog, depth + 1)))
            except ValueError as error:
                SEEN[(' > '.join(STACK[-3:]), spec.ValueType.KindValue, str(error)[:50], cursor.DataValue[start:start + 12].hex())] += 1
                STACK.pop()
                raise
            STACK.pop()
        return tuple(result)

    Fields.ReadFieldsMut = fields
    import convert.formats.Fusion.EntityCodec.Values.ReadGroupsMut as Groups
    import convert.formats.Fusion.EntityCodec.Tags.ReadSketchMut as Sketch
    Groups.ReadFieldsMut = fields
    Sketch.ReadFieldsMut = fields
    for name, data in documents():
        failures(data)
    for key, count in SEEN.most_common(20):
        print(count, json.dumps(key))


if __name__ == '__main__':
    main()
