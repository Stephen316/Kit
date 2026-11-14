import io
import sys
import zipfile
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
target.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(io.BytesIO(source.read_bytes())) as archive:
    for info in archive.infolist():
        if info.filename.endswith('.f3d'):
            (target / Path(info.filename).name).write_bytes(archive.read(info.filename))
            print(info.filename, info.file_size)
