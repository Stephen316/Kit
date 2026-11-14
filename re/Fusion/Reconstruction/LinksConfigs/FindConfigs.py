import io
import sys
import zipfile
from pathlib import Path

roots = [Path(item) for item in sys.argv[1:]]
found = 0
for root in roots:
    for path in sorted(root.rglob('*')):
        if path.suffix.lower() not in ('.f3d', '.f3z') or not path.is_file():
            continue
        try:
            data = path.read_bytes()
            outer = zipfile.ZipFile(io.BytesIO(data))
            docs = [(path.name, outer)]
            if path.suffix.lower() == '.f3z':
                docs = [(name, zipfile.ZipFile(io.BytesIO(outer.read(name)))) for name in outer.namelist() if name.endswith('.f3d')]
            for label, archive in docs:
                for info in archive.infolist():
                    if info.filename.endswith(('.dsgcfg', '.dsgcfgrule')) and info.file_size > 2:
                        found += 1
                        print(path, label, info.filename, info.file_size)
                    if info.filename.endswith('RedirectionsStream.dat'):
                        print('REDIRECT', path, label, info.file_size)
        except Exception as error:
            print('ERR', path, error)
print('found', found)
