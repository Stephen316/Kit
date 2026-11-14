import argparse
import copy
import hashlib
import json
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directories', action='store_true')
    arguments = parser.parse_args()
    source = BASE / 'Generated' / 'AuthoredParameter.f3d'
    identity = hashlib.sha256(source.read_bytes()).hexdigest()
    if identity != '91fda6a666e843a525a2fb7b6cee3aedf34cd0dff92040a091dc41d4f6391487':
        raise ValueError('Only the frozen independently authored diagnostic candidate is allowed')
    destination = BASE / ('StoredFolders' if arguments.directories else 'StoredOnly')
    destination.mkdir(exist_ok=True)
    output = destination / 'AuthoredParameter.f3d'
    members = []
    with zipfile.ZipFile(source) as archive, zipfile.ZipFile(output, 'w') as generated:
        if arguments.directories:
            folders = sorted({name[:index + 1] for name in archive.namelist() for index, value in enumerate(name) if value == '/'}, key=lambda value: (value.count('/'), value))
            for name in folders:
                info = zipfile.ZipInfo(name, date_time=(2026, 11, 12, 0, 0, 0))
                info.external_attr = (0o40755 << 16) | 0x10
                generated.writestr(info, b'')
        for original in archive.infolist():
            data = archive.read(original)
            info = copy.copy(original)
            info.compress_type = zipfile.ZIP_STORED
            generated.writestr(info, data)
            members.append({'name': info.filename, 'method': info.compress_type, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    report = {'purpose': 'Diagnostic packaging of the frozen independently authored candidate; not a source-file authoring interface', 'sourceCandidateSha256': identity, 'candidate': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'methodCounts': {'0': len(members) + (len(folders) if arguments.directories else 0)}, 'memberPayloadsChanged': False, 'directoryEntriesAdded': arguments.directories, 'members': members}
    (destination / 'Generation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
