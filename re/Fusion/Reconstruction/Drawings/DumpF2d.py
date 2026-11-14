import hashlib
import io
import json
import struct
import sys
import zipfile
from pathlib import Path


def members(data):
    archive = zipfile.ZipFile(io.BytesIO(data))
    rows = []
    for info in archive.infolist():
        offset = info.header_offset
        name_size, extra_size = struct.unpack_from('<HH', data, offset + 26)
        local = struct.unpack_from('<I5H3I2H', data, offset)
        start = offset + 30 + name_size + extra_size
        rows.append({
            'name': info.filename,
            'method': info.compress_type,
            'size': info.file_size,
            'packed': info.compress_size,
            'date': info.date_time,
            'create_system': info.create_system,
            'create_version': info.create_version,
            'extract_version': info.extract_version,
            'flags': info.flag_bits,
            'attr': hex(info.external_attr),
            'internal_attr': info.internal_attr,
            'extra': info.extra.hex(),
            'local_extra': data[offset + 30 + name_size:start].hex(),
            'offset': offset,
            'local_fields': local[1:],
            'sha256': hashlib.sha256(archive.read(info)).hexdigest() if not info.is_dir() else None,
        })
    return archive, rows


def main(path):
    data = Path(path).read_bytes()
    archive, rows = members(data)
    print(json.dumps({'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'comment': archive.comment.hex()}, indent=1))
    for row in rows:
        print(json.dumps(row))
    end = data.rfind(b'PK\x05\x06')
    print('eocd', data[end:].hex())


if __name__ == '__main__':
    main(sys.argv[1])
