import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.setrecursionlimit(20000)

from ExampleRecords import documents
from SweepOne import failure
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


def main():
    deep = len(sys.argv) > 1
    for name, data in documents():
        start = time.monotonic()
        try:
            model = ReadDocument(data)
            status = 'read'
            if deep:
                status = 'round' if ReadDocument(EmitParsed(model)) == model else 'model'
        except Exception as error:
            row = failure(error)
            status = f"{row['message'][:70]} @ {row['where']}"
        print(name[-24:], round(time.monotonic() - start, 1), status)


if __name__ == '__main__':
    main()
