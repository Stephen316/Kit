import collections
import io
import json
import re
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from Sweep import ROOT, tracked

PREFIX = 'FusionAssetName[Active]/Images.BlobParts/'
GUID = '830A2A2B-0AA9-4D6A-ACA1-F7A2B2A06573'


def designs(name):
    data = (ROOT / name).read_bytes()
    if name.lower().endswith('.f3z'):
        with zipfile.ZipFile(io.BytesIO(data)) as outer:
            for info in outer.infolist():
                if info.filename.lower().endswith('.f3d'):
                    yield outer.read(info)
    elif name.lower().endswith('.f3d'):
        yield data


def scan(name, hits, shapes, holders):
    for data in designs(name):
        try:
            outer = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile:
            continue
        with outer:
            for info in outer.infolist():
                if 'DesignSegment' in info.filename and info.filename.endswith('MetaStream.dat'):
                    meta = outer.read(info)
                    if any(needle in meta for needle in (GUID.encode(), GUID.lower().encode(), GUID.encode('utf-16-le'), GUID.lower().encode('utf-16-le'))):
                        holders[('ImageSerializer metadata', name)] += 1
            parts = [info for info in outer.infolist() if info.filename.startswith(PREFIX) and info.filename != PREFIX]
            if not parts:
                continue
            hits.append(name)
            streams = {info.filename.split('/')[1]: outer.read(info) for info in outer.infolist() if info.filename.endswith('BulkStream.dat')}
            for info in parts:
                leaf = info.filename[len(PREFIX):]
                payload = outer.read(info)
                shapes[(re.sub(r'\d+', 'N', leaf), payload[:8].hex())] += 1
                for segment, stream in streams.items():
                    for form, needle in (('utf8', leaf.encode()), ('utf16', leaf.encode('utf-16-le'))):
                        if needle in stream:
                            holders[(re.sub(r'\d+', 'N', segment), form)] += 1


def main():
    hits, shapes, holders = [], collections.Counter(), collections.Counter()
    for name in tracked():
        if name.lower().endswith('.f2d'):
            continue
        scan(name, hits, shapes, holders)
    report = {'files': sorted(set(hits)), 'shapes': {f'{k[0]} {k[1]}': v for k, v in shapes.items()}, 'holders': {f'{k[0]} {k[1]}': v for k, v in holders.items()}}
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
