import copy
import hashlib
import json
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    source = BASE / 'OrderedAct' / 'AuthoredParameter.f3d'
    identity = hashlib.sha256(source.read_bytes()).hexdigest()
    if identity != 'cda56e7247dcfdbb2271063c1498d324a6000f8186058d921cb45b0981565db0':
        raise ValueError('Only the frozen independently authored diagnostic candidate is allowed')
    destination = BASE / 'BrepFolder'
    destination.mkdir(exist_ok=True)
    output = destination / 'AuthoredParameter.f3d'
    folder = 'FusionAssetName[Active]/Breps.BlobParts/'
    members = []
    with zipfile.ZipFile(source) as archive, zipfile.ZipFile(output, 'w') as generated:
        info = zipfile.ZipInfo(folder, date_time=(2026, 11, 12, 0, 0, 0))
        info.external_attr = (0o40755 << 16) | 0x10
        generated.writestr(info, b'')
        for original in archive.infolist():
            data = archive.read(original)
            generated.writestr(copy.copy(original), data)
            members.append({'name': original.filename, 'method': original.compress_type, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    report = {'purpose': 'Add empty BRep blob folder to ordered independently authored candidate', 'sourceCandidateSha256': identity, 'candidate': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'memberPayloadsChanged': False, 'addedDirectories': [folder], 'members': members}
    (destination / 'Generation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
