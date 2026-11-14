import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))

import convert.formats.Fusion.EntityCodec.Frame.ReadNamedMut as Module
from ExampleRecords import documents
from RecordFailures import failures
from Sweep import tracked


def main():
    names = collections.Counter()
    check = Module.NamedShape

    def spy(type_name, element_name, named):
        try:
            return check(type_name, element_name, named)
        except ValueError:
            names[(type_name, element_name)] += 1
            raise

    Module.NamedShape = spy
    for name, data in documents():
        failures(data)
    known = collections.Counter()

    def count(type_name, element_name, named):
        known[(type_name, element_name)] += 1
        return check(type_name, element_name, named)

    Module.NamedShape = count
    if len(sys.argv) > 1:
        from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
        for name in tracked():
            if name.endswith('.f3d'):
                try:
                    ReadDocument((ROOT / name).read_bytes())
                except Exception:
                    pass
    print(json.dumps({'unsupported': [[*key, value] for key, value in names.items()], 'supported_in_corpus': [[*key, value] for key, value in known.most_common()]}, indent=1))


if __name__ == '__main__':
    main()
