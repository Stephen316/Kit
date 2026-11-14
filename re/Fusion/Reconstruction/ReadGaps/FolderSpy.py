import io
import re
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from PackageCensus import PART, ROOT, designs

HEX = re.compile(r'[0-9A-Fa-f]{8}-[0-9A-Fa-f-]{27}')
TIME = re.compile(r'\d{4}-\d\d-\d\dT[0-9:.]+Z?')
NAME = re.compile(r'\b[0-9a-f]{11}(_png)?\b')


def mask(text):
    return NAME.sub('NAME', TIME.sub('TIME', HEX.sub('UUID', text)))


def main():
    name = sys.argv[1]
    index = sys.argv[2]
    wanted = sys.argv[3:]
    for label, data in designs(name):
        if not label.endswith(f' zip {index}'):
            continue
        with zipfile.ZipFile(io.BytesIO(data)) as outer:
            for info in outer.infolist():
                if not PART.fullmatch(info.filename):
                    continue
                with zipfile.ZipFile(io.BytesIO(outer.read(info))) as inner:
                    seen = set()
                    for member in inner.infolist():
                        shape = mask(member.filename)
                        if shape in seen or not any(item in shape for item in wanted):
                            continue
                        seen.add(shape)
                        payload = inner.read(member)
                        if member.filename.endswith('.xml'):
                            print('==', shape, len(payload))
                            print(mask(payload.decode('utf-8', 'replace')))
                        else:
                            print('==', shape, len(payload), payload[:8])


if __name__ == '__main__':
    main()
