import re
import sys
import zipfile
from pathlib import Path

pattern = re.compile(rb'\x01(.{8})\x24\x00\x00\x00([0-9A-Fa-f-]{36})([\x00\x01])', re.S)
for name in sys.argv[1:]:
    try:
        archive = zipfile.ZipFile(name)
    except zipfile.BadZipFile:
        continue
    hits = 0
    for info in archive.infolist():
        if not info.filename.endswith('BulkStream.dat'):
            continue
        data = archive.read(info)
        for match in pattern.finditer(data):
            hits += 1
            if hits <= 4:
                start = match.start()
                print(Path(name).name, info.filename.split('/')[-2], start, int.from_bytes(match.group(1), 'little'), match.group(2).decode(), data[match.end() - 1:match.end() + 24].hex(' '))
    if hits:
        print(Path(name).name, 'inline hits', hits)
