import collections
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from ExampleRecords import documents
from RecordFailures import failures
import convert.formats.Fusion.EntityCodec.Frame.ReadNamedMut as Named
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType

USED = collections.Counter()


def main():
    source = Named.NamedShape
    original = Named.ReadNamedMut

    def reader(cursor, catalog):
        def shape(type_name, element_name, named):
            schema = catalog.Classes.get(type_name.upper())
            if type_name not in named and not element_name and schema is not None and schema.IsValue:
                USED[(type_name[:8], schema.SchemaVersion)] += 1
                return WireType('object', ClassGuid=type_name.upper())
            return source(type_name, element_name, named)
        Named.NamedShape = shape
        try:
            return original(cursor, catalog)
        finally:
            Named.NamedShape = source

    import convert.formats.Fusion.EntityCodec.Frame.ReadFrameMut as Frame
    Frame.ReadNamedMut = reader
    for name, data in documents():
        found = failures(data)
        print(name[-24:], sum(found.values()), dict(found) if found else '')
    print(dict(USED))


if __name__ == '__main__':
    main()
