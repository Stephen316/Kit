import json
import io
import re
import sys
import zipfile
from pathlib import Path

private_pairs = Path(__file__).resolve().parents[2] / 'LocalOracle/LinksConfigs/tmp/PrivatePairs.json'
patterns = [rb'/Users/', rb'C:/Users/', rb'urn:adsk', re.escape(Path.home().name.encode()), rb'@[a-z0-9-]+\.[a-z]', rb'wipprod', rb'a\.[A-Za-z0-9]{20,}', rb'b\.[A-Za-z0-9]{20,}']
if private_pairs.exists():
    patterns += [re.escape(pair[0].encode()) for pair in json.loads(private_pairs.read_text())]


def utf16(pattern):
    out = b''
    index = 0
    while index < len(pattern):
        if pattern[index:index + 1] == b'\\':
            out += pattern[index:index + 2]
            index += 2
            continue
        char = pattern[index:index + 1]
        out += re.escape(char) + b'\\x00' if char.isalnum() or char in b':/@.' else char
        index += 1
    return out


def members(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist():
            payload = archive.read(info.filename)
            yield info.filename, payload
            if info.filename.endswith('.f3d'):
                for name, inner in members(payload):
                    yield info.filename + '!' + name, inner


for name in sys.argv[1:]:
    data = Path(name).read_bytes()
    hits = {}
    for member, payload in members(data) if zipfile.is_zipfile(io.BytesIO(data)) else [('raw', data)]:
        for pattern in patterns:
            for variant, label in ((pattern, 'a'), (utf16(pattern), 'w')):
                try:
                    found = re.findall(variant, payload)
                except re.error:
                    continue
                if found:
                    hits.setdefault(member.split('/')[-1][:40], set()).add(label + ':' + pattern.decode())
    print(Path(name).name, 'CLEAN' if not hits else hits)
